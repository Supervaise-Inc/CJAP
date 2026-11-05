"""GStreamer sentence player (2026-11-05, opt-in: CJ_SENTENCE_PLAYER=gst).

An alternative to `_SentenceOut` (PortAudio, the default) in main_voice_robot.py
with the SAME interface: enabled(), play(wav, listener, trim), close(), abort().
It exists so the two players can be compared on the robot for the paper, and
because the Reachy Mini media stack is GStreamer based.

One pipeline stays PLAYING for the whole answer and every sentence is pushed
into it, so a sentence boundary pays no process spawn and no PCM re-open:

    appsrc ! audioconvert ! audioresample ! alsasink device=audio_out_route

The ALSA pcm `audio_out_route` is the same one aplay and the PortAudio player
use, so ~/bin/audio-out (internal / Bluetooth / USB DAC) still decides where
the sound goes. CJ_GST_SINK replaces the sink element text, for example
`pipewiresink` or `autoaudiosink`.

Not supported: the dual route (audio_out_route2 mirror). open() raises, and the
caller falls back to aplay for that sentence, exactly as it does for any device
trouble.

Nothing here imports gi at module load: `available()` probes it, so the module
imports on a machine with no GStreamer (the test suite injects a fake).
"""
import os
import threading
import time

import numpy as np

_SINK_DEFAULT = "alsasink device=audio_out_route"


def _env_num(name, default):
    try:
        return float(os.environ.get(name, "").strip() or default)
    except ValueError:
        return float(default)


def _load_gst():
    """The Gst module, initialised, or None when python-gi / GStreamer is absent."""
    try:
        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst
        Gst.init(None)
        return Gst
    except Exception:
        return None


def available(gst=None):
    """True when python-gi, GStreamer and the elements this player needs exist."""
    Gst = gst or _load_gst()
    if Gst is None:
        return False
    try:
        return all(Gst.ElementFactory.find(n) is not None
                   for n in ("appsrc", "audioconvert", "audioresample", "alsasink"))
    except Exception:
        return False


def pipeline_description(rate, sink=None, max_bytes=None, buffer_s=0.15):
    """The gst-launch text for one output stream (public so a test or an
    operator can run the same thing by hand with `gst-launch-1.0`)."""
    sink = sink or os.environ.get("CJ_GST_SINK", _SINK_DEFAULT)
    if max_bytes is None:
        max_bytes = int(rate * 2 * 0.3)         # 0.3 s of S16 mono: the back-pressure window
    caps = f"audio/x-raw,format=S16LE,layout=interleaved,channels=1,rate={int(rate)}"
    desc = (f'appsrc name=src is-live=true format=time do-timestamp=true block=true '
            f'max-bytes={int(max_bytes)} caps="{caps}" '
            f'! audioconvert ! audioresample ! {sink} name=sink')
    if sink.startswith("alsasink"):
        # ALSA buffer, same 0.15 s as the PortAudio player; sync=false plays
        # buffers as they arrive instead of waiting on a clock
        desc += f" sync=false buffer-time={int(buffer_s * 1_000_000)} latency-time=20000"
    return desc


class GstSentenceOut:
    CHUNK_S = 0.05

    def __init__(self, load_wav, trim_edges, ref_feed=None, dry_run=None,
                 dual_route=None, bt_route=None, gst=None):
        """load_wav(path) -> (rate, int16 mono array); trim_edges(a, rate) -> a.
        ref_feed: the Bluetooth AEC reference object (sync/warm/push/abort), or
        None. dry_run / dual_route / bt_route: callables returning a bool."""
        self._gst = gst or _load_gst()
        if self._gst is None:
            raise RuntimeError("GStreamer (python-gi) is not available")
        self._load_wav, self._trim = load_wav, trim_edges
        self._ref = ref_feed
        self._dry = dry_run or (lambda: False)
        self._dual = dual_route or (lambda: False)
        self._bt = bt_route or (lambda: False)
        self.pipeline = self.src = None
        self.rate = None
        self.lock = threading.Lock()
        self._alive = None
        self._last_write = 0.0
        self._busy = False
        self.stats = {"open_s": None, "latency_s": None, "sentences": 0, "first_push_s": None}

    @staticmethod
    def enabled():
        return os.environ.get("CJ_SENTENCE_PLAYER", "stream").strip().lower() != "aplay"

    # ── pipeline lifecycle ────────────────────────────────────────────────
    def _open(self, rate):
        if self.pipeline is not None and self.rate == rate:
            return self.src
        self.close()
        if self._dual():
            raise RuntimeError("dual route is not supported by the GStreamer player")
        Gst = self._gst
        t0 = time.monotonic()
        desc = pipeline_description(rate, buffer_s=_env_num("CJ_SENT_OUT_LATENCY_S", 0.15))
        pipe = Gst.parse_launch(desc)
        src = pipe.get_by_name("src")
        ret = pipe.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            pipe.set_state(Gst.State.NULL)
            raise RuntimeError(f"GStreamer pipeline would not start: {desc}")
        # a fresh Bluetooth stream swallows its first 100-300 ms (see _SentenceOut)
        prime = _env_num("CJ_SENT_PRIME_S", 0.25 if self._bt() else 0.0)
        self.pipeline, self.src, self.rate = pipe, src, rate
        if prime > 0:
            self._push(np.zeros(int(rate * prime), dtype=np.int16))
        if self._ref is not None and self._ref.sync():
            self._ref.warm(rate)
        self.stats["open_s"] = round(time.monotonic() - t0, 4)
        self.stats["latency_s"] = self._query_latency()
        self._last_write = time.monotonic()
        print(f"[audio] GStreamer player open @ {rate} Hz "
              f"(open {self.stats['open_s'] * 1000:.0f} ms, "
              f"pipeline latency {self.stats['latency_s']}) — sentences play gapless")
        self._alive = threading.Thread(target=self._keepalive, args=(pipe,), daemon=True)
        self._alive.start()
        return src

    def _query_latency(self):
        """Pipeline latency in seconds (live min), or None if it cannot be read."""
        try:
            Gst = self._gst
            q = Gst.Query.new_latency()
            if self.pipeline.query(q):
                _live, lo, _hi = q.parse_latency()
                return round(lo / 1e9, 4)
        except Exception:
            pass
        return None

    def _push(self, samples):
        """Write int16 samples; blocks while the 0.3 s window is full."""
        Gst = self._gst
        buf = Gst.Buffer.new_wrapped(samples.tobytes())
        ret = self.src.emit("push-buffer", buf)
        if ret not in (Gst.FlowReturn.OK, Gst.FlowReturn.FLUSHING):
            raise RuntimeError(f"GStreamer push failed: {ret}")

    def _keepalive(self, pipe):
        """Silence between sentences so the device never underruns (same job as
        _SentenceOut._keepalive; stands down while a sentence is being written)."""
        zeros = np.zeros(int(self.rate * self.CHUNK_S), dtype=np.int16)
        while self.pipeline is pipe:
            with self.lock:
                if (self.pipeline is pipe and not self._busy
                        and time.monotonic() - self._last_write > self.CHUNK_S):
                    try:
                        self._push(zeros)
                        self._last_write = time.monotonic()
                    except Exception:
                        pass
            time.sleep(self.CHUNK_S / 2)

    def _release(self, abort):
        with self.lock:
            pipe, src = self.pipeline, self.src
            self.pipeline = self.src = None
        if pipe is None:
            return
        Gst = self._gst
        try:
            if not abort:
                # let the tail drain: EOS goes through the pipeline, then stop
                src.emit("end-of-stream")
                bus = pipe.get_bus()
                bus.timed_pop_filtered(int(1.5 * 1e9),
                                       Gst.MessageType.EOS | Gst.MessageType.ERROR)
        except Exception:
            pass
        try:
            pipe.set_state(Gst.State.NULL)       # NULL drops whatever is still buffered
        except Exception:
            pass

    def close(self):    # answer finished: drain the last sentence, free the device
        self._release(abort=False)

    def abort(self):    # stop word / mute: drop what is buffered now
        self._release(abort=True)
        if self._ref is not None:
            self._ref.abort()

    # ── one sentence ──────────────────────────────────────────────────────
    def play(self, wav_path, listener, trim=True):
        """True if the listener cut it, False when written out. Raises on
        device trouble: the caller then falls back to aplay."""
        rate, a = self._load_wav(wav_path)
        if trim:
            a = self._trim(a, rate)
        if self._dry():   # console rehearsal: keep the timing, skip the speaker
            end = time.monotonic() + len(a) / float(rate)
            while time.monotonic() < end:
                if listener.fired:
                    return True
                time.sleep(0.05)
            return False
        self._open(rate)
        feed = self._ref is not None and self._ref.sync()
        n = int(rate * self.CHUNK_S)
        self._busy = True
        try:
            for k in range(0, len(a), n):
                if listener.fired:
                    self.abort()
                    return True
                with self.lock:
                    if self.pipeline is None:    # aborted from another thread
                        return True
                    self._push(a[k:k + n])
                    self._last_write = time.monotonic()
                if feed:
                    self._ref.push(a[k:k + n], rate, self._last_write)
                if self.stats["first_push_s"] is None:
                    self.stats["first_push_s"] = round(time.monotonic(), 4)
            self.stats["sentences"] += 1
            return False
        finally:
            self._busy = False
