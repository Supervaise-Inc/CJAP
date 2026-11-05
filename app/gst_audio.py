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

Review fixes (research 02_gstreamer_review.md, B1-B4):
  B1  appsrc is block=false and the writer paces itself on current-level-bytes,
      so no push ever waits while holding the lock: a stop word's abort() is
      never stuck behind a full queue, and a stalled device (Bluetooth drop,
      USB unplug) is noticed after CJ_GST_STALL_S (2 s) instead of hanging.
  B2  the keep-alive pushes silence only when the appsrc queue is EMPTY and never
      more than one chunk, so it cannot delay the next sentence by the queue
      length. CJ_GST_KEEPALIVE=0 turns it off (worth testing on non-Bluetooth).
  B3  the bus is polled; an ERROR, or any failed push, tears the pipeline down so
      audio_out_route is released before the caller falls back to aplay.
  B4  libasound's config cache is refreshed right before a pipeline is opened,
      so a ~/bin/audio-out route switch is followed (as _SentenceOut does).

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
_QUEUE_S = 0.1          # appsrc queue: two 50 ms chunks (was 0.3 s)


def _env_num(name, default):
    try:
        return float(os.environ.get(name, "").strip() or default)
    except ValueError:
        return float(default)


def _env_on(name, default=True):
    v = os.environ.get(name, "").strip().lower()
    if not v:
        return default
    return v not in {"0", "false", "no", "off"}


def _alsa_config_refresh():
    """Drop libasound's per-process config cache so the next PCM open re-reads
    ~/.asoundrc and the route file it includes (same job as the function of the
    same name in main_voice_robot.py). Fails open."""
    try:
        import ctypes
        ctypes.CDLL("libasound.so.2").snd_config_update_free_global()
    except Exception as e:
        print(f"[audio] alsa config refresh skipped: {e}")


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
        max_bytes = int(rate * 2 * _QUEUE_S)    # S16 mono: the queue the writer paces against
    caps = f"audio/x-raw,format=S16LE,layout=interleaved,channels=1,rate={int(rate)}"
    # block=false: push-buffer never waits (B1); the writer paces on current-level-bytes
    desc = (f'appsrc name=src is-live=true format=time do-timestamp=true block=false '
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
                 dual_route=None, bt_route=None, alsa_refresh=None, gst=None):
        """load_wav(path) -> (rate, int16 mono array); trim_edges(a, rate) -> a.
        ref_feed: the Bluetooth AEC reference object (sync/warm/push/abort), or
        None. dry_run / dual_route / bt_route: callables returning a bool.
        alsa_refresh: called right before a pipeline is opened (B4); defaults to
        the libasound refresh in this module."""
        self._gst = gst or _load_gst()
        if self._gst is None:
            raise RuntimeError("GStreamer (python-gi) is not available")
        self._load_wav, self._trim = load_wav, trim_edges
        self._ref = ref_feed
        self._dry = dry_run or (lambda: False)
        self._dual = dual_route or (lambda: False)
        self._bt = bt_route or (lambda: False)
        self._alsa_refresh = alsa_refresh or _alsa_config_refresh
        self.pipeline = self.src = None
        self.rate = None
        self.lock = threading.Lock()        # guards ONLY the pipeline/src swap and one short push
        self._alive = None
        self._last_write = 0.0
        self._busy = False
        self._opening = threading.Lock()    # one open at a time, never held with self.lock
        self.stats = {"open_s": None, "latency_s": None, "sentences": 0,
                      "first_push_s": None, "errors": 0}

    @staticmethod
    def enabled():
        return os.environ.get("CJ_SENTENCE_PLAYER", "stream").strip().lower() != "aplay"

    # ── pipeline lifecycle ────────────────────────────────────────────────
    def _open(self, rate):
        """The running (pipeline, src) for this rate, opening one if needed."""
        with self.lock:
            if self.pipeline is not None and self.rate == rate:
                return self.pipeline, self.src
        with self._opening:
            with self.lock:
                if self.pipeline is not None and self.rate == rate:
                    return self.pipeline, self.src
            self.close()
            if self._dual():
                raise RuntimeError("dual route is not supported by the GStreamer player")
            Gst = self._gst
            t0 = time.monotonic()
            self._alsa_refresh()            # B4: follow ~/bin/audio-out switches; nothing open now
            desc = pipeline_description(rate, buffer_s=_env_num("CJ_SENT_OUT_LATENCY_S", 0.15))
            pipe = Gst.parse_launch(desc)
            src = pipe.get_by_name("src")
            ret = pipe.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                pipe.set_state(Gst.State.NULL)
                raise RuntimeError(f"GStreamer pipeline would not start: {desc}")
            with self.lock:
                self.pipeline, self.src, self.rate = pipe, src, rate
            # a fresh Bluetooth stream swallows its first 100-300 ms (see _SentenceOut)
            prime = _env_num("CJ_SENT_PRIME_S", 0.25 if self._bt() else 0.0)
            if prime > 0:
                self._push(pipe, src, np.zeros(int(rate * prime), dtype=np.int16))
            if self._ref is not None and self._ref.sync():
                self._ref.warm(rate)
            self.stats["open_s"] = round(time.monotonic() - t0, 4)
            self.stats["latency_s"] = self._query_latency(pipe)
            self._last_write = time.monotonic()
            print(f"[audio] GStreamer player open @ {rate} Hz "
                  f"(open {self.stats['open_s'] * 1000:.0f} ms, "
                  f"pipeline latency {self.stats['latency_s']}) — sentences play gapless")
            self._alive = threading.Thread(target=self._watch, args=(pipe, src, rate), daemon=True)
            self._alive.start()
            return pipe, src

    def _query_latency(self, pipe):
        """Pipeline latency in seconds (live min), or None if it cannot be read."""
        try:
            q = self._gst.Query.new_latency()
            if pipe.query(q):
                _live, lo, _hi = q.parse_latency()
                return round(lo / 1e9, 4)
        except Exception:
            pass
        return None

    # ── writing (B1) ──────────────────────────────────────────────────────
    @staticmethod
    def _level(src):
        try:
            return int(src.get_property("current-level-bytes"))
        except Exception:
            return 0

    def _push(self, pipe, src, samples):
        """Write int16 samples. Never blocks inside GStreamer and never waits
        while holding self.lock: the writer sleeps here, lock-free, until the
        appsrc queue has room. A queue that does not drain within
        CJ_GST_STALL_S means the device is stuck: tear down and raise, so the
        caller falls back to aplay. Raises when the pipeline was replaced or
        aborted underneath us."""
        Gst = self._gst
        cap = int(self.rate * 2 * _QUEUE_S) if self.rate else 0
        stall = _env_num("CJ_GST_STALL_S", 2.0)
        t0 = time.monotonic()
        while self._level(src) > cap:
            if self.pipeline is not pipe:
                raise RuntimeError("GStreamer pipeline was released")
            if time.monotonic() - t0 > stall:
                self._fail(pipe, f"queue did not drain for {stall:.1f} s (device stuck?)")
                raise RuntimeError("GStreamer output stalled")
            time.sleep(0.005)
        with self.lock:                      # one short non-blocking push
            if self.pipeline is not pipe:
                raise RuntimeError("GStreamer pipeline was released")
            ret = src.emit("push-buffer", Gst.Buffer.new_wrapped(samples.tobytes()))
        if ret not in (Gst.FlowReturn.OK, Gst.FlowReturn.FLUSHING):
            self._fail(pipe, f"push returned {ret}")
            raise RuntimeError(f"GStreamer push failed: {ret}")

    def _fail(self, pipe, why):
        """B3: a dead or stuck pipeline must not keep holding audio_out_route."""
        self.stats["errors"] += 1
        print(f"[audio] GStreamer player error: {why} — releasing the device")
        self._release(abort=True, only=pipe)

    def _watch(self, pipe, src, rate):
        """Keep-alive silence (B2) and bus polling (B3), off the writer's path."""
        Gst = self._gst
        zeros = np.zeros(int(rate * self.CHUNK_S), dtype=np.int16)
        chunk_bytes = len(zeros) * 2
        keep = _env_on("CJ_GST_KEEPALIVE", True)
        bus = pipe.get_bus()
        while self.pipeline is pipe:
            try:
                msg = bus.timed_pop_filtered(0, Gst.MessageType.ERROR)
            except Exception:
                msg = None
            if msg is not None:
                self._fail(pipe, f"bus error {getattr(msg, 'type', '')}")
                return
            # silence only into an EMPTY queue, and never more than one chunk:
            # the next sentence then waits at most one chunk, not the queue length
            if (keep and not self._busy and self._level(src) < chunk_bytes
                    and time.monotonic() - self._last_write > self.CHUNK_S):
                try:
                    self._push(pipe, src, zeros)
                    self._last_write = time.monotonic()
                except Exception:
                    return
            time.sleep(self.CHUNK_S / 2)

    # ── teardown ──────────────────────────────────────────────────────────
    def _release(self, abort, only=None):
        with self.lock:                      # swap only; no waiting inside
            pipe, src = self.pipeline, self.src
            if only is not None and pipe is not only:
                return
            self.pipeline = self.src = None
        if pipe is None:
            return
        Gst = self._gst
        try:
            if not abort:
                # let the tail drain: EOS goes through the pipeline, then stop
                src.emit("end-of-stream")
                pipe.get_bus().timed_pop_filtered(int(1.5 * 1e9),
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
        pipe, src = self._open(rate)
        feed = self._ref is not None and self._ref.sync()
        n = int(rate * self.CHUNK_S)
        self._busy = True
        try:
            for k in range(0, len(a), n):
                if listener.fired:
                    self.abort()
                    return True
                if self.pipeline is not pipe:    # aborted from another thread
                    return True
                try:
                    self._push(pipe, src, a[k:k + n])
                except RuntimeError:
                    if self.pipeline is not pipe and self.stats["errors"] == 0:
                        return True              # released by an abort, not a failure
                    raise
                self._last_write = time.monotonic()
                if feed:
                    self._ref.push(a[k:k + n], rate, self._last_write)
                if self.stats["first_push_s"] is None:
                    self.stats["first_push_s"] = round(time.monotonic(), 4)
            self.stats["sentences"] += 1
            return False
        finally:
            self._busy = False
