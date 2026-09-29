#!/usr/bin/env python3
"""A web console for the Reachy Mini's audio devices.

Lists every ALSA capture and playback device, lets you mute/unmute each one,
and records from the selected microphone to a WAV file - with a live level
meter so you can see the mic is actually picking something up. Recordings play
back and download straight from the browser.

Standard library only. Device discovery uses `arecord -l` / `aplay -l`,
muting uses `amixer`, and recording pipes raw PCM out of `arecord` - the same
tools api-isolator.py relies on, so there is nothing new to install.

Each recording in the drawer has an "Isolate voice" button that sends the WAV
through the ElevenLabs Voice Isolator API and saves a background-noise-free
copy next to it (`*-isolated.wav`, via ffmpeg when present, else `.mp3`).
The API key is picked up from $ELEVEN_API_KEY or the Supervaise checkout's
app/.env / voice/config.py - the same credential the robot's voice uses.
Note this is offline cleanup, billed per minute of audio: it cannot sit in
the live mic path in front of the wake-word engine.

Usage:
    python3 audio-ui.py                    # serve on 0.0.0.0:8090
    python3 audio-ui.py --port 9000        # a different port
    python3 audio-ui.py --host 127.0.0.1   # robot-local only
    python3 audio-ui.py --list             # print devices and exit (headless)
    python3 audio-ui.py --outdir ~/audio   # where recordings are written
    python3 audio-ui.py --no-monitor       # never hold the mic open when idle

No display required, so plain `ssh` is enough - no `ssh -X`, no X server. Open
the printed URL from any device on the network, including a phone. Under VS
Code Remote-SSH the port is forwarded for you, so http://localhost:8090 on the
laptop reaches the robot with no extra setup. The robot already uses 8000,
8080 and 8443 for its own services, hence 8090.
"""

from __future__ import annotations

import argparse
import array
import io
import json
import math
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import wave
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Recording format. plughw + 48 kHz mono is what every Reachy mic handles.
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH = 2  # S16_LE
CHUNK = 4096

BARS = 64        # waveform history the browser draws
MON_BARS = 40    # shorter history for the small mic-check widget
MON_RETRY = 5.0  # seconds before re-opening a mic that refused monitoring
TICK = 0.045     # how often the sampler appends a level
PUSH = 0.08      # how often each SSE client is updated

# The delayed isolated view: a rolling window of mic audio is sent through the
# ElevenLabs isolator over and over while the ISO toggle is on. The API needs
# whole files (min 4.6 s input, ~3 s round trip), so this can only ever trail
# reality by several seconds - and it bills quota the entire time it is on.
ISO_WIN_S = 6.0  # seconds of audio per window (and the pace between sends)
ISO_PAD_S = 5.0  # left-pad a short buffer with silence to clear the API minimum


# ------------------------------------------------------------- backend -----


@dataclass
class Device:
    card: int
    index: int
    name: str
    detail: str
    kind: str                    # "input" | "output"
    control: str | None = None   # amixer simple control that has a switch
    enabled: bool = True         # mirrors the mixer switch, or UI-only
    pcm: str | None = None       # explicit PCM, for sources that are not a card

    @property
    def alsa(self) -> str:
        return self.pcm or f"plughw:{self.card},{self.index}"

    @property
    def hw(self) -> str:
        return self.pcm or f"hw:{self.card},{self.index}"

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.pcm}" if self.pcm else f"{self.kind}:{self.card}:{self.index}"

    @property
    def shared(self) -> bool:
        """True when other apps can hold this mic at the same time we do."""
        return self.pcm is not None

    def as_json(self) -> dict:
        return {"key": self.key, "name": self.name, "detail": self.detail,
                "kind": self.kind, "hw": self.hw, "alsa": self.alsa,
                "control": self.control, "enabled": self.enabled,
                "shared": self.shared}


_CARD_RE = re.compile(
    r"^card (\d+): (\S+) \[([^\]]*)\], device (\d+): (.*?)(?: \[([^\]]*)\])?$"
)


def _run(cmd: list[str], timeout: float = 4.0) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


class Audio:
    """Everything that talks to ALSA."""

    def __init__(self) -> None:
        self.devices: list[Device] = []
        self.error: str | None = None

    # -- discovery ----------------------------------------------------------

    def refresh(self) -> None:
        if not shutil.which("arecord"):
            self.error = "alsa-utils not found - sudo apt install alsa-utils"
            self.devices = []
            return
        self.error = None
        shared = self._shared_source()
        found = ([shared] if shared else []) \
            + self._parse("arecord", "input") + self._parse("aplay", "output")
        for d in found:
            if d.shared:
                continue          # not a card, so it has no amixer switch
            d.control = self._pick_control(d)
            state = self._switch_state(d)
            d.enabled = True if state is None else state
        self.devices = found
        if not found:
            self.error = "No ALSA devices reported. Is the audio HAT/USB device attached?"

    def _shared_source(self) -> Device | None:
        """PipeWire's default mic, reachable as the `default` PCM.

        Opening `plughw:` is exclusive, so it fails whenever something else got
        there first - on this robot supervaise.service holds the mic from boot.
        Recording through PipeWire shares it instead of fighting for it.
        """
        if not shutil.which("pactl"):
            return None
        m = re.search(r"^Default Source:\s*(\S+)$", _run(["pactl", "info"]), re.M)
        if not m or m.group(1).endswith(".monitor"):
            return None           # a monitor is loopback of the speakers, not a mic
        pretty = re.sub(r"^alsa_input\.(usb-)?", "", m.group(1)).split(".")[0]
        pretty = re.sub(r"[_-]\d{6,}.*$", "", pretty).replace("_", " ").strip()
        return Device(card=-1, index=-1, kind="input", pcm="default",
                      name="Shared microphone",
                      detail=f"{pretty or 'PipeWire default'} - shared, works while another app records")

    def _parse(self, tool: str, kind: str) -> list[Device]:
        out = []
        for line in _run([tool, "-l"]).splitlines():
            m = _CARD_RE.match(line.strip())
            if not m:
                continue
            card, cid, cname, idx, dname, dsub = m.groups()
            out.append(Device(
                card=int(card),
                index=int(idx),
                name=(cname or cid).strip(),
                detail=(dsub or dname or "").strip(),
                kind=kind,
            ))
        return out

    # -- mute / unmute ------------------------------------------------------

    def _controls(self, card: int) -> list[str]:
        text = _run(["amixer", "-c", str(card), "scontrols"])
        return re.findall(r"Simple mixer control '([^']+)'", text)

    def _pick_control(self, d: Device) -> str | None:
        """First mixer control on the card that actually exposes an on/off switch."""
        wanted = ("mic", "capture", "input") if d.kind == "input" else ("master", "speaker", "pcm", "headphone")
        names = self._controls(d.card)
        names.sort(key=lambda n: 0 if any(w in n.lower() for w in wanted) else 1)
        for n in names:
            text = _run(["amixer", "-c", str(d.card), "sget", n])
            if "[on]" in text or "[off]" in text:
                return n
        return None

    def _switch_state(self, d: Device) -> bool | None:
        if not d.control:
            return None
        text = _run(["amixer", "-c", str(d.card), "sget", d.control])
        if "[off]" in text:
            return False
        if "[on]" in text:
            return True
        return None

    def set_enabled(self, d: Device, on: bool) -> str | None:
        """Flip the mixer switch. Returns an error string, or None on success."""
        d.enabled = on
        if not d.control:
            return None  # no hardware switch; the toggle only gates recording
        pairs = [("cap", "nocap"), ("unmute", "mute")]
        if d.kind == "output":
            pairs.reverse()
        for on_word, off_word in pairs:
            _run(["amixer", "-q", "-c", str(d.card), "sset",
                  d.control, on_word if on else off_word])
            state = self._switch_state(d)
            if state is not None and state == on:
                return None
        return f"Could not change '{d.control}' on card {d.card}"


def _tidy_alsa(msg: str) -> str:
    """Turn ALSA's `arecord: main:850: ...` noise into something actionable."""
    msg = re.sub(r"^\w+:\s*\w+:\d+:\s*", "", msg).strip()
    if "busy" in msg.lower():
        # The usual cause on this robot: its own audio service holds the mic.
        msg += " - another process already has this mic open"
    return msg


def rms_of(buf: bytes) -> float:
    """Normalised 0..1 loudness of a little-endian S16 buffer."""
    usable = len(buf) // 2 * 2
    if usable == 0:
        return 0.0
    a = array.array("h")
    a.frombytes(buf[:usable])
    if sys.byteorder == "big":
        a.byteswap()
    step = max(1, len(a) // 512)  # subsample; this runs ~12x a second on a Pi
    total = count = 0
    for i in range(0, len(a), step):
        total += a[i] * a[i]
        count += 1
    return math.sqrt(total / max(count, 1)) / 32768.0


# ----------------------------------------------- ElevenLabs isolation -----

# Where the robot already keeps its ElevenLabs credential, in the order the
# voice stack itself resolves it: environment, then app/.env (written by
# switch_voice.sh), then the gitignored voice/config.py literal.
_SUPERVAISE = Path.home() / "Supervaise-Reachy-Mini-Project-main"
_KEY_SOURCES = (
    (_SUPERVAISE / "app" / ".env", r"^ELEVEN_API_KEY=(.+)$"),
    (_SUPERVAISE / "voice" / "config.py", r'^ELEVEN_API_KEY = "([^"]+)"'),
)
ISOLATE_URL = "https://api.elevenlabs.io/v1/audio-isolation"


def eleven_key() -> str | None:
    key = os.environ.get("ELEVEN_API_KEY", "").strip()
    if key:
        return key
    for path, pattern in _KEY_SOURCES:
        try:
            text = path.read_text()
        except OSError:
            continue
        m = re.search(pattern, text, re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return None


def isolate_voice(data: bytes, filename: str, key: str) -> bytes:
    """One round trip through the Voice Isolator. Returns MP3 bytes.

    The API takes a whole file and answers with the cleaned audio, so the
    call blocks for a few seconds. Billed at 1000 characters of TTS quota
    per minute of input audio.
    """
    boundary = "----reachy" + secrets.token_hex(12)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="audio"; filename="{filename}"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(ISOLATE_URL, data=body, headers={
        "xi-api-key": key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read(500).decode(errors="replace")
        try:  # the API wraps errors as {"detail": {"status": ..., "message": ...}}
            detail = json.loads(detail)["detail"]["message"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        raise RuntimeError(f"ElevenLabs HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ElevenLabs unreachable: {exc.reason}") from exc


def mp3_to_wav(mp3: bytes, out: Path) -> bool:
    """Transcode to the console's native 48 kHz mono S16 WAV. False if no ffmpeg."""
    if not shutil.which("ffmpeg"):
        return False
    p = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", "pipe:0",
         "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS), "-sample_fmt", "s16",
         str(out)],
        input=mp3, capture_output=True, timeout=120,
    )
    if p.returncode != 0:
        out.unlink(missing_ok=True)
        raise RuntimeError("ffmpeg failed: "
                           + (p.stderr.decode(errors="replace").strip() or "unknown error"))
    return True


WAVE_PEAKS = 160                 # bars in a recording's static waveform
_peak_cache: dict[str, tuple[float, list[float]]] = {}


def waveform_peaks(path: Path, n: int = WAVE_PEAKS) -> list[float]:
    """n peak amplitudes (0..1) across a recording, for the drawer's waveform.

    Deliberately NOT normalised per file: raw and isolated copies share the
    same absolute scale, so the noise floor the isolator removed is visible
    as the difference between the two drawings.
    """
    mtime = path.stat().st_mtime
    cached = _peak_cache.get(str(path))
    if cached and cached[0] == mtime:
        return cached[1]

    a = array.array("h")
    if path.suffix == ".wav":
        with wave.open(str(path), "rb") as w:
            nch, sw = w.getnchannels(), w.getsampwidth()
            raw = w.readframes(w.getnframes())
        if sw == 2:
            a.frombytes(raw[: len(raw) // 2 * 2])
            if sys.byteorder == "big":
                a.byteswap()
            if nch > 1:
                a = a[::nch]
    elif shutil.which("ffmpeg"):     # the no-ffmpeg isolate fallback keeps MP3
        p = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", str(path),
             "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1"],
            capture_output=True, timeout=60)
        if p.returncode == 0:
            a.frombytes(p.stdout[: len(p.stdout) // 2 * 2])
            if sys.byteorder == "big":
                a.byteswap()

    peaks = _peaks(a, n)
    _peak_cache[str(path)] = (mtime, peaks)
    return peaks


def _peaks(a: array.array, n: int) -> list[float]:
    """n bucketed peak amplitudes (0..1) of S16 samples."""
    peaks = []
    total = len(a)
    for i in range(n):
        lo = total * i // n
        hi = max(lo + 1, total * (i + 1) // n)
        step = max(1, (hi - lo) // 256)  # subsample inside the bucket; Pi CPU
        m = 0
        for j in range(lo, min(hi, total), step):
            v = a[j]
            if v < 0:
                v = -v
            if v > m:
                m = v
        peaks.append(m / 32768.0)
    return peaks


def _pcm_to_wav(pcm: bytes) -> bytes:
    """Wrap raw capture PCM as a WAV file the isolation API will accept."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPLE_WIDTH)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return buf.getvalue()


def mp3_peaks(mp3: bytes, n: int) -> list[float]:
    """Peaks of the API's MP3 answer, decoded through ffmpeg without a temp file."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not installed - needed to decode the API's MP3")
    p = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "mp3", "-i", "pipe:0",
         "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1"],
        input=mp3, capture_output=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed: "
                           + (p.stderr.decode(errors="replace").strip()[-120:] or "?"))
    a = array.array("h")
    a.frombytes(p.stdout[: len(p.stdout) // 2 * 2])
    if sys.byteorder == "big":
        a.byteswap()
    return _peaks(a, n)


class _Capture:
    """Pipes raw PCM out of `arecord` and tracks the live level.

    Subclasses decide what to do with the bytes: Recorder writes them to a WAV,
    Monitor throws them away and keeps only the level.
    """

    def __init__(self, device: Device) -> None:
        self.device = device
        self.level = 0.0
        # The last ISO_WIN_S seconds of raw PCM, for the delayed isolated view.
        # ~0.6 MB when full, so it is kept regardless of the ISO toggle.
        self.recent: deque[bytes] = deque(
            maxlen=int(SAMPLE_RATE * SAMPLE_WIDTH * ISO_WIN_S / CHUNK) + 1)
        self.error: str | None = None
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- hooks --------------------------------------------------------------

    def _opened(self) -> None:
        """arecord is up and no data has arrived yet."""

    def _consume(self, data: bytes) -> None:
        """One raw PCM chunk, already reflected in self.level."""

    def _closed(self) -> None:
        """The pump has finished; flush whatever needs flushing."""

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> bool:
        cmd = ["arecord", "-D", self.device.alsa, "-f", "S16_LE",
               "-r", str(SAMPLE_RATE), "-c", str(CHANNELS), "-t", "raw", "-q", "-"]
        try:
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE, bufsize=CHUNK)
        except OSError as exc:
            self.error = str(exc)
            return False
        try:
            self._opened()
        except OSError as exc:               # e.g. the WAV path is not writable
            self.error = str(exc)
            self._proc.terminate()
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        return True

    def _pump(self) -> None:
        assert self._proc and self._proc.stdout
        try:
            while not self._stop.is_set():
                data = self._proc.stdout.read(CHUNK)
                if not data:
                    break
                self.level = rms_of(data)
                self.recent.append(data)
                self._consume(data)
        except (OSError, ValueError):
            pass
        finally:
            self.level = 0.0
            # arecord failing (busy device, bad rate) shows up on stderr. Wait
            # for it to actually exit first: straight after an empty read it may
            # not be reaped yet, and poll() would report None - losing the reason.
            if self._proc:
                try:
                    self._proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
                if self._proc.poll() not in (None, 0):
                    err = (self._proc.stderr.read() or b"").decode(errors="replace")
                    first = next((l for l in err.splitlines() if l.strip()), "")
                    if first and not self._stop.is_set():
                        self.error = _tidy_alsa(first)

    def stop(self) -> None:
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._thread:
            self._thread.join(timeout=2)
        self._closed()


class Monitor(_Capture):
    """Listens without saving, so the mic-check widget can show live signal."""


class Recorder(_Capture):
    """A capture that also writes what it hears into a WAV file."""

    def __init__(self, device: Device, outdir: Path) -> None:
        super().__init__(device)
        self.outdir = outdir
        self.path: Path | None = None
        self.peak = 0.0
        self.started = 0.0
        self._wav: wave.Wave_write | None = None

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started if self.started else 0.0

    def _opened(self) -> None:
        self.outdir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.path = self.outdir / f"reachy-{stamp}.wav"
        self._wav = wave.open(str(self.path), "wb")
        self._wav.setnchannels(CHANNELS)
        self._wav.setsampwidth(SAMPLE_WIDTH)
        self._wav.setframerate(SAMPLE_RATE)
        self.started = time.monotonic()

    def _consume(self, data: bytes) -> None:
        self._wav.writeframes(data)
        self.peak = max(self.peak, self.level)

    def _closed(self) -> None:
        if self._wav:
            try:
                self._wav.close()
            except Exception:
                pass
            self._wav = None
        self.started = 0.0

    def stop(self) -> Path | None:
        super().stop()
        return self.path


# --------------------------------------------------------------- state -----


class Console:
    """Shared application state. Every HTTP thread touches this, so it locks."""

    def __init__(self, audio: Audio, outdir: Path, monitor: bool = True) -> None:
        self.audio = audio
        self.outdir = outdir
        self.rec: Recorder | None = None
        self.mon: Monitor | None = None
        self.mon_on = monitor
        self.mon_error: str | None = None
        self.mon_levels = deque([0.0] * MON_BARS, maxlen=MON_BARS)
        self.isolating: set[str] = set()   # recordings mid-flight to ElevenLabs
        self.iso_on = False           # the delayed isolated view (ISO toggle)
        self.iso_levels = [0.0] * MON_BARS
        self.iso_state = "off"
        self.iso_bad = False
        self.iso_ts = 0.0             # when the last cleaned window came back
        self._mon_next = 0.0          # backoff clock for re-opening a busy mic
        self.selected: str | None = None
        self.status = ""
        self.status_bad = False
        self.rev = 0                      # bumped when the device list changes
        self.levels = deque([0.0] * BARS, maxlen=BARS)
        self.lock = threading.RLock()
        self._stop = threading.Event()
        self.refresh(initial=True)
        threading.Thread(target=self._sample_loop, daemon=True).start()
        threading.Thread(target=self._iso_loop, daemon=True).start()

    # -- background sampler -------------------------------------------------

    def _sample_loop(self) -> None:
        """Keeps the waveform history moving whether or not a browser is open."""
        while not self._stop.wait(TICK):
            with self.lock:
                rec = self.rec
                live = bool(rec and rec.running)
                self.levels.append(rec.level if live
                                   else self.levels[-1] * 0.82)  # settle back to flat
                if rec and (not live or rec.error):
                    self._reap(rec)
                    live = False
                self._tend_monitor(live)
                if live:
                    mlvl = rec.level
                elif self.mon and self.mon.running:
                    mlvl = self.mon.level
                else:
                    mlvl = self.mon_levels[-1] * 0.7
                self.mon_levels.append(mlvl)

    def _tend_monitor(self, recording: bool) -> None:
        """Keep a Monitor open on the selected mic whenever we are not recording.

        This is what makes the mic-check widget move without committing to a
        take. It yields the device the instant a real recording starts, since
        `plughw:` will not open twice. A mic that refuses to open is retried on
        a timer rather than every tick, or a busy device would have us spawning
        arecord 20 times a second.
        """
        dev = self.device(self.selected)
        want = dev if (self.mon_on and not recording and dev and dev.enabled) else None

        mon = self.mon
        if mon and (want is None or mon.device.key != want.key):
            mon.stop()
            self.mon = None
        elif mon and not mon.running:               # it died on its own
            self.mon_error = mon.error or self.mon_error
            mon.stop()
            self.mon = None
            self._mon_next = time.monotonic() + MON_RETRY

        if want is not None and self.mon is None and time.monotonic() >= self._mon_next:
            fresh = Monitor(want)
            if fresh.start():
                self.mon, self.mon_error = fresh, None
            else:
                self.mon_error = fresh.error or "Could not open this mic for monitoring"
                self._mon_next = time.monotonic() + MON_RETRY

    def _iso_loop(self) -> None:
        """The delayed isolated view: while the ISO toggle is on, keep sending
        the newest window of mic audio through the Voice Isolator and keep the
        peaks of whatever comes back.

        The API is a whole-file call, so this is inherently seconds behind the
        raw mic-check waveform - that is a property of the service, not a bug.
        One window is in flight at a time, paced to ISO_WIN_S between sends,
        which costs about a minute of isolator quota per minute switched on.
        """
        while not self._stop.wait(0.3):
            with self.lock:
                on = self.iso_on
                cap = self.rec if (self.rec and self.rec.running) else self.mon
                if cap and not cap.running:
                    cap = None
            if not on:
                continue
            try:
                pcm = b"".join(cap.recent) if cap else b""
            except RuntimeError:      # pump thread appended mid-join; next tick
                continue
            if len(pcm) < SAMPLE_RATE * SAMPLE_WIDTH:      # under a second
                with self.lock:
                    self.iso_state, self.iso_bad = "listening…", False
                continue
            key = eleven_key()
            if not key:
                with self.lock:
                    self.iso_state, self.iso_bad = "no ElevenLabs key", True
                self._stop.wait(3)
                continue
            need = int(SAMPLE_RATE * ISO_PAD_S) * SAMPLE_WIDTH - len(pcm)
            if need > 0:              # silence in front, newest audio stays right
                pcm = b"\x00" * need + pcm
            t0 = time.monotonic()
            try:
                mp3 = isolate_voice(_pcm_to_wav(pcm), "monitor.wav", key)
                peaks = mp3_peaks(mp3, MON_BARS)
                dt = time.monotonic() - t0
                with self.lock:
                    if self.iso_on:   # switched off mid-flight: show nothing
                        self.iso_levels = peaks
                        self.iso_ts = time.time()
                        self.iso_state = f"window cleaned in {dt:.1f} s"
                        self.iso_bad = False
            except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                with self.lock:
                    self.iso_state, self.iso_bad = str(exc)[:90], True
                self._stop.wait(3)    # a failing API must not be hammered
            spent = time.monotonic() - t0
            if spent < ISO_WIN_S:     # pace: at most one window per ISO_WIN_S
                self._stop.wait(ISO_WIN_S - spent)

    def toggle_isolive(self) -> None:
        with self.lock:
            self.iso_on = not self.iso_on
            self.iso_bad = False
            self.iso_ts = 0.0
            self.iso_levels = [0.0] * MON_BARS
            self.iso_state = "starting…" if self.iso_on else "off"
            self._set_status(
                "Isolated view on - mic audio goes to ElevenLabs every few seconds"
                if self.iso_on else "Isolated view off")

    def toggle_monitor(self) -> None:
        with self.lock:
            self.mon_on = not self.mon_on
            self._mon_next = 0.0
            self.mon_error = None
            if not self.mon_on and self.mon:
                self.mon.stop()
                self.mon = None
            self._set_status("Mic check " + ("on" if self.mon_on else "off - mic released"))

    def _reap(self, rec: Recorder) -> None:
        """Retire a recorder that stopped on its own and say why it stopped."""
        path = rec.stop()
        self.rec = None
        if rec.error:
            self._set_status(rec.error, bad=True)
            # A recorder that never got a frame leaves a header-only WAV behind;
            # binning it keeps the Recordings folder honest.
            if path and path.exists() and path.stat().st_size <= 64:
                path.unlink(missing_ok=True)
        elif path:
            size = path.stat().st_size / 1e6 if path.exists() else 0
            self._set_status(f"Saved {path.name} ({size:.1f} MB)")
        self.rev += 1

    def shutdown(self) -> None:
        self._stop.set()
        with self.lock:
            if self.rec and self.rec.running:
                self.rec.stop()
            if self.mon:
                self.mon.stop()
                self.mon = None

    # -- state --------------------------------------------------------------

    def _set_status(self, text: str, bad: bool = False) -> None:
        self.status, self.status_bad = text, bad

    def device(self, key: str | None) -> Device | None:
        return next((d for d in self.audio.devices if d.key == key), None)

    def refresh(self, initial: bool = False) -> None:
        with self.lock:
            self.audio.refresh()
            inputs = [d for d in self.audio.devices if d.kind == "input"]
            if self.selected not in {d.key for d in inputs}:
                self.selected = inputs[0].key if inputs else None
            self.rev += 1
            if not initial:
                self._set_status(f"Found {len(self.audio.devices)} devices")

    def select(self, key: str) -> None:
        with self.lock:
            d = self.device(key)
            if not d or d.kind != "input":
                self._set_status("Not a capture device", bad=True)
                return
            self.selected = d.key
            self._mon_next = 0.0
            self._set_status(f"Source: {d.alsa}")

    def toggle_device(self, key: str) -> None:
        with self.lock:
            d = self.device(key)
            if not d:
                self._set_status("Unknown device", bad=True)
                return
            err = self.audio.set_enabled(d, not d.enabled)
            if err:
                self._set_status(err, bad=True)
            elif d.control is None:
                self._set_status(f"{d.name}: no hardware switch - toggle gates recording only")
            else:
                self._set_status(f"{d.name} {'unmuted' if d.enabled else 'muted'} ({d.control})")
            self.rev += 1

    def toggle_record(self) -> None:
        with self.lock:
            if self.rec and self.rec.running:
                path = self.rec.stop()
                size = path.stat().st_size / 1e6 if path and path.exists() else 0
                self._set_status(f"Saved {path.name} ({size:.1f} MB)" if path else "Stopped")
                self.rec = None
                self.rev += 1
                return
            dev = self.device(self.selected)
            if not dev:
                self._set_status("No capture device selected", bad=True)
                return
            if not dev.enabled:
                self._set_status(f"{dev.name} is muted - toggle it on first", bad=True)
                return
            if self.mon:
                self.mon.stop()      # synchronously: plughw will not open twice
                self.mon = None
            rec = Recorder(dev, self.outdir)
            if not rec.start():
                self._set_status(rec.error or "Could not start arecord", bad=True)
                return
            self.rec = rec
            self.levels = deque([0.0] * BARS, maxlen=BARS)
            self._set_status(f"Recording from {dev.alsa}")

    def isolate(self, name: str) -> None:
        """Run one recording through the ElevenLabs Voice Isolator.

        Blocks the calling HTTP thread for the API round trip (seconds); the
        lock is only held for bookkeeping, so the sampler and other requests
        keep flowing while we wait on the network.
        """
        if "/" in name or "\\" in name:
            return
        src = self.outdir / name
        with self.lock:
            if name in self.isolating:
                return
            if not src.is_file():
                self._set_status(f"{name} not found", bad=True)
                return
            if "-isolated" in src.stem:
                self._set_status(f"{name} is already an isolated copy", bad=True)
                return
            key = eleven_key()
            if not key:
                self._set_status(
                    "No ElevenLabs key - set $ELEVEN_API_KEY or run switch_voice.sh",
                    bad=True)
                return
            self.isolating.add(name)
            self._set_status(f"Isolating voice from {name} - takes a few seconds")
            self.rev += 1
        try:
            mp3 = isolate_voice(src.read_bytes(), name, key)
            out = src.with_name(src.stem + "-isolated.wav")
            if not mp3_to_wav(mp3, out):
                out = out.with_suffix(".mp3")   # no ffmpeg: keep the API's MP3
                out.write_bytes(mp3)
            size = out.stat().st_size / 1e6
            with self.lock:
                self._set_status(f"Saved {out.name} ({size:.1f} MB)")
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            with self.lock:
                self._set_status(f"Isolation failed: {exc}", bad=True)
        finally:
            with self.lock:
                self.isolating.discard(name)
                self.rev += 1

    # -- payloads -----------------------------------------------------------

    def snapshot(self) -> dict:
        """The small, hot object pushed to browsers many times a second."""
        with self.lock:
            rec = self.rec
            live = bool(rec and rec.running)
            dev = self.device(self.selected)
            return {
                "rev": self.rev,
                "recording": live,
                "level": round(rec.level, 5) if live else 0.0,
                "peak": round(rec.peak, 5) if rec else 0.0,
                "elapsed": round(rec.elapsed, 2) if live else 0.0,
                "levels": [round(v, 4) for v in self.levels],
                "status": self.status,
                "statusBad": self.status_bad,
                "selected": self.selected,
                "liveName": dev.name if dev else "No microphone selected",
                "liveAlsa": dev.alsa if dev else "-",
                "monOn": self.mon_on,
                "monLive": live or bool(self.mon and self.mon.running),
                "monLevel": round(rec.level, 5) if live else (
                    round(self.mon.level, 5) if self.mon and self.mon.running else 0.0),
                "monLevels": [round(v, 4) for v in self.mon_levels],
                "monError": self.mon_error,
                "isoOn": self.iso_on,
                "isoLevels": [round(v, 4) for v in self.iso_levels],
                "isoState": self.iso_state,
                "isoBad": self.iso_bad,
                "isoAge": round(time.time() - self.iso_ts, 1) if self.iso_ts else None,
            }

    def devices_payload(self) -> dict:
        with self.lock:
            return {
                "rev": self.rev,
                "error": self.audio.error,
                "selected": self.selected,
                "outdir": str(self.outdir).replace(str(Path.home()), "~"),
                "devices": [d.as_json() for d in self.audio.devices],
            }

    def recordings(self) -> list[dict]:
        if not self.outdir.is_dir():
            return []
        with self.lock:
            busy = set(self.isolating)
        files = [p for pat in ("*.wav", "*.mp3") for p in self.outdir.glob(pat)]
        out = []
        for p in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True):
            st = p.stat()
            out.append({"name": p.name, "size": st.st_size, "mtime": st.st_mtime,
                        "url": "/rec/" + p.name,
                        "isolated": "-isolated" in p.stem,
                        "isolating": p.name in busy})
        return out


# ---------------------------------------------------------------- page -----

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reachy Mini - Audio Console</title>
<style>
:root{
  --card:#FCEDE8; --panel:#FFFFFF; --ink:#17110F; --muted:#8C7A73; --hair:#EFE1DB;
  --dark:#171210; --dark-soft:#2A211D; --violet:#8B5CF6; --pink:#D9469F;
  --amber:#F97316; --rec:#F0453A; --good:#2FBF71; --warn:#F5A524; --off:#E2D6D0;
  --accent:linear-gradient(90deg,#8B5CF6,#D9469F,#F97316);
  --sans:"Inter","Poppins","Nunito Sans",Ubuntu,"DejaVu Sans",system-ui,sans-serif;
  --mono:"JetBrains Mono","Roboto Mono","Ubuntu Mono","DejaVu Sans Mono",monospace;
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%}
body{
  font-family:var(--sans); color:var(--ink); -webkit-font-smoothing:antialiased;
  background:linear-gradient(115deg,#7A2BE0 0%,#A93CCF 34%,#E0559A 67%,#F4713F 100%);
  background-attachment:fixed; padding:24px;
}
.mono{font-family:var(--mono)}
.shell{max-width:1180px;margin:0 auto}
.card{background:var(--card);border-radius:30px;overflow:hidden;
      box-shadow:0 24px 60px rgba(23,17,15,.24)}

/* ---- header ---- */
header{display:flex;align-items:center;justify-content:space-between;padding:34px 38px 0}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:42px;height:42px;border-radius:13px;background:var(--dark);
      display:grid;place-items:center;color:#fff;flex:none}
.brand b{display:block;font-size:15px;line-height:1.2}
.brand span{display:block;font-size:12px;color:var(--muted)}
.tools{display:flex;gap:12px}
.icon{width:40px;height:40px;border-radius:50%;background:#fff;border:1px solid var(--hair);
      display:grid;place-items:center;cursor:pointer;color:var(--ink);transition:transform .12s}
.icon:hover{transform:translateY(-1px)}
.icon:active{transform:translateY(0)}

/* ---- hero + live ---- */
.top{display:grid;grid-template-columns:1fr 478px;gap:32px;padding:26px 38px 30px;align-items:start}
h1{font-size:38px;line-height:1.14;margin:0 0 16px;letter-spacing:-.02em}
.grad{background:var(--accent);-webkit-background-clip:text;background-clip:text;color:transparent}
.lede{font-size:13.5px;color:var(--muted);margin:0 0 24px;line-height:1.6}
.actions{display:flex;gap:14px;flex-wrap:wrap}
button{font-family:inherit}
.rec-btn{display:inline-flex;align-items:center;gap:12px;height:48px;padding:0 26px;
  border:0;border-radius:24px;background:var(--accent);color:#fff;font-size:13px;
  font-weight:700;cursor:pointer;transition:transform .12s,filter .12s}
.rec-btn:hover{filter:brightness(1.06)}
.rec-btn .dot{width:26px;height:26px;border-radius:50%;background:#fff;display:grid;place-items:center}
.rec-btn .dot::after{content:"";width:10px;height:10px;border-radius:50%;background:var(--rec)}
.rec-btn.live{background:var(--dark)}
.rec-btn.live .dot::after{border-radius:2px;background:var(--dark)}
.ghost{height:48px;padding:0 26px;border-radius:24px;background:#fff;border:1px solid var(--hair);
  font-size:13px;font-weight:700;color:var(--ink);cursor:pointer}
.ghost:hover{background:#fffdfc}
.meta{list-style:none;display:flex;gap:26px;flex-wrap:wrap;padding:0;margin:26px 0 0;
      font-size:11px;color:var(--muted)}
.meta li{display:flex;align-items:center;gap:8px;min-width:0}
.meta li:last-child{max-width:min(100%,360px);white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;display:inline-block;line-height:1.6}
.meta li:last-child::before{display:inline-block;vertical-align:middle;margin-right:8px}
.meta li::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--amber)}

/* ---- mic check widget ---- */
.signal{margin-top:22px;background:#fff;border:1px solid var(--hair);border-radius:20px;
  padding:13px 16px 11px;max-width:430px}
.signal-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}
.eyebrow2{font-size:9.5px;letter-spacing:.16em;color:var(--muted);font-weight:700}
.mon-btn{border:1px solid var(--hair);background:#fff;color:var(--muted);border-radius:11px;
  font-size:9.5px;font-weight:700;letter-spacing:.06em;padding:4px 11px;cursor:pointer}
.mon-btn[aria-pressed="true"]{background:#E8F7EF;border-color:#CBEBDA;color:#1E8F55}
.signal-btns{display:flex;gap:8px}
#btn-iso[aria-pressed="true"]{background:#F1EBFE;border-color:#DDD0FB;color:#6D3FD4}
#sigwave{display:block;width:100%;height:44px}
.iso-strip{margin-top:9px;border-top:1px dashed var(--hair);padding-top:8px}
#isowave{display:block;width:100%;height:44px;margin-top:4px}
.signal-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;
  margin-top:5px;font-size:10.5px;color:var(--muted)}
.sig-state{display:flex;align-items:center;gap:7px;min-width:0}
.sig-state i{width:7px;height:7px;border-radius:50%;background:#D9CBC5;flex:none}
.sig-state span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sig-state.hot i{background:var(--good)}
.sig-state.bad{color:var(--rec)}
.sig-state.bad i{background:var(--rec)}

.live{background:var(--dark);border-radius:26px;padding:28px;color:#fff}
.eyebrow{font-size:10px;letter-spacing:.18em;color:#8A7A74}
.live h2{font-size:16px;margin:12px 0 4px;font-weight:700}
.live .sub{font-size:11.5px;color:#8A7A74}
#wave{display:block;width:100%;height:150px;margin:18px 0 6px}
.live-foot{display:flex;align-items:center;justify-content:space-between;gap:16px}
.timer{font-size:27px;font-weight:700;color:#6E605B;letter-spacing:-.01em}
.timer.live{color:#fff}
.pill{display:inline-flex;align-items:center;gap:9px;height:30px;padding:0 15px;
  border-radius:15px;background:var(--dark-soft);font-size:10px;font-weight:700;
  letter-spacing:.08em;color:#8A7A74}
.pill i{width:8px;height:8px;border-radius:50%;background:#6E605B}
.pill.live{background:var(--rec);color:#fff}
.pill.live i{background:#fff;animation:pulse 1.1s ease-in-out infinite}
@keyframes pulse{50%{opacity:.35}}
.meter{height:4px;border-radius:2px;background:#332A26;margin-top:18px;overflow:hidden}
#meter-fill{height:100%;width:0;border-radius:2px;background:var(--good);transition:width .08s linear}
.meter-labels{display:flex;justify-content:space-between;margin-top:8px;font-size:10px;color:#8A7A74}

/* ---- device list ---- */
.devices{background:var(--panel);border-radius:0 0 30px 30px;padding:22px 38px 30px}
.devices-head{display:flex;align-items:baseline;gap:12px;margin-bottom:6px}
.devices-head h3{font-size:15px;margin:0}
.devices-head .sub{font-size:11.5px;color:var(--muted)}
.status{margin-left:auto;font-size:11.5px;color:var(--muted);text-align:right}
.status.bad{color:var(--rec)}
.row{display:flex;align-items:center;gap:14px;padding:11px 10px;border-bottom:1px solid var(--hair);
     border-radius:16px}
.row:last-child{border-bottom:0}
.row.chosen{background:#FBF2EF}
.row .glyph{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;flex:none}
.row .who{min-width:0;flex:1}
.row .who b{display:block;font-size:12.5px;font-weight:700}
.row .who span{display:block;font-size:10.5px;color:var(--muted);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row.muted .who b{color:#B3A49E}
.badge{font-size:9.5px;font-weight:700;letter-spacing:.06em;padding:5px 11px;border-radius:11px;flex:none}
.radio{width:20px;height:20px;border-radius:50%;border:2px solid #D9CBC5;background:none;
  cursor:pointer;flex:none;display:grid;place-items:center;padding:0}
.radio.on{border-color:var(--violet)}
.radio.on::after{content:"";width:8px;height:8px;border-radius:50%;background:var(--violet)}
.radio-label{font-size:10px;color:var(--muted);flex:none;width:44px}
.sw{width:48px;height:27px;border-radius:14px;border:0;background:var(--off);position:relative;
  cursor:pointer;flex:none;padding:0;transition:background .15s}
.sw.on{background:var(--accent)}
.sw::after{content:"";position:absolute;top:3px;left:3px;width:21px;height:21px;border-radius:50%;
  background:#fff;transition:transform .15s}
.sw.on::after{transform:translateX(21px)}
.err{color:var(--rec);font-size:13px;padding:16px 0}

/* ---- recordings drawer ---- */
.drawer{position:fixed;inset:0;background:rgba(23,17,15,.55);display:grid;place-items:center;
  padding:24px;z-index:10}
.drawer[hidden]{display:none}   /* a display rule outranks the hidden attribute */
.drawer-box{background:var(--panel);border-radius:24px;width:min(620px,100%);max-height:80vh;
  overflow:auto;padding:28px}
.drawer-box h3{margin:0 0 4px;font-size:16px}
.drawer-box .sub{font-size:11.5px;color:var(--muted)}
.take{border-top:1px solid var(--hair);padding:14px 0}
.take-top{display:flex;align-items:baseline;gap:10px}
.take b{font-size:12.5px}
.take .when{font-size:10.5px;color:var(--muted);margin-left:auto}
.take audio{width:100%;margin-top:10px;height:34px}
.take-wave{display:block;width:100%;height:38px;margin-top:10px}
.take-foot{display:flex;align-items:center;gap:14px;margin-top:6px}
.iso-btn{border:1px solid var(--hair);background:#fff;color:var(--ink);border-radius:11px;
  font-size:10px;font-weight:700;letter-spacing:.04em;padding:5px 12px;cursor:pointer}
.iso-btn:hover{background:#fffdfc}
.iso-btn[disabled]{color:var(--muted);cursor:wait}
.badge-iso{font-size:9.5px;font-weight:700;letter-spacing:.06em;padding:4px 10px;
  border-radius:10px;background:#E8F7EF;color:#1E8F55;flex:none}
.close{margin-top:20px;width:100%;height:44px;border-radius:22px;border:1px solid var(--hair);
  background:#fff;font-size:12.5px;font-weight:700;cursor:pointer}

@media (max-width:900px){
  body{padding:12px}
  .top{grid-template-columns:1fr;padding:22px 22px 26px;gap:24px}
  header{padding:26px 22px 0}
  .devices{padding:20px 22px 26px}
  h1{font-size:30px}
  .radio-label{display:none}
  .row .badge{display:none}
}
</style>
</head>
<body>
<main class="shell">
  <section class="card">
    <header>
      <div class="brand">
        <div class="logo">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round">
            <rect x="9" y="2" width="6" height="11" rx="3" fill="currentColor" stroke="none"/>
            <path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/>
          </svg>
        </div>
        <div><b>Reachy Mini</b><span>audio console</span></div>
      </div>
      <div class="tools">
        <button class="icon" id="btn-refresh" title="Refresh devices" aria-label="Refresh devices">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-3-6.7"/>
            <path d="M21 4v5h-5"/></svg>
        </button>
        <button class="icon" id="btn-files" title="Recordings" aria-label="Recordings">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linejoin="round">
            <path d="M3 7V5.5A1.5 1.5 0 0 1 4.5 4h4L10 6h9.5A1.5 1.5 0 0 1 21 7.5V18a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18Z"/></svg>
        </button>
      </div>
    </header>

    <div class="top">
      <div class="hero">
        <h1><span class="grad">Audio devices</span><br>on your Reachy</h1>
        <p class="lede">
          Every ALSA capture and playback device the robot can see.<br>
          Mute one, pick a microphone, and record straight to WAV.
        </p>
        <div class="actions">
          <button class="rec-btn" id="btn-rec">
            <span class="dot"></span><span id="rec-label">Start recording</span>
          </button>
          <button class="ghost" id="btn-files2">Recordings</button>
        </div>
        <ul class="meta">
          <li>48 kHz mono</li><li>16-bit WAV</li><li id="meta-dir">-</li>
        </ul>

        <div class="signal">
          <div class="signal-head">
            <span class="eyebrow2">M I C &nbsp; C H E C K</span>
            <span class="signal-btns">
              <button class="mon-btn" id="btn-iso" aria-pressed="false"
                title="Delayed isolated view - sends the mic through ElevenLabs while on (uses quota)">ISO</button>
              <button class="mon-btn" id="btn-mon" aria-pressed="true">ON</button>
            </span>
          </div>
          <canvas id="sigwave"></canvas>
          <div class="signal-foot">
            <span class="sig-state" id="sig-state"><i></i><span id="sig-text">Starting</span></span>
            <span class="mono" id="sig-db">-&#8734; dBFS</span>
          </div>
          <div class="iso-strip" id="iso-strip" hidden>
            <span class="eyebrow2">I S O L A T E D &nbsp;&middot;&nbsp; D E L A Y E D</span>
            <canvas id="isowave"></canvas>
            <div class="signal-foot">
              <span class="sig-state" id="iso-state"><i></i><span id="iso-text">Off</span></span>
              <span class="mono" id="iso-age"></span>
            </div>
          </div>
        </div>
      </div>

      <div class="live">
        <span class="eyebrow">L I V E &nbsp; C A P T U R E</span>
        <h2 id="live-name">No microphone selected</h2>
        <div class="sub mono" id="live-alsa">-</div>
        <canvas id="wave"></canvas>
        <div class="live-foot">
          <div class="timer mono" id="timer">00:00:00</div>
          <div class="pill" id="pill"><i></i><span id="pill-label">IDLE</span></div>
        </div>
        <div class="meter"><div id="meter-fill"></div></div>
        <div class="meter-labels"><span>peak</span><span class="mono" id="dbfs">-&#8734; dBFS</span></div>
      </div>
    </div>

    <section class="devices">
      <div class="devices-head">
        <h3>Devices</h3>
        <span class="sub" id="counts"></span>
        <span class="status" id="status"></span>
      </div>
      <div id="list"></div>
    </section>
  </section>
</main>

<div class="drawer" id="drawer" hidden>
  <div class="drawer-box">
    <h3>Recordings</h3>
    <div class="sub" id="drawer-dir"></div>
    <div id="takes"></div>
    <button class="close" id="btn-close">Close</button>
  </div>
</div>

<script>
const GAIN = 3.4;            // display gain, matching the desktop build
const $ = (id) => document.getElementById(id);
let rev = -1, recording = false;
let levels = new Array(64).fill(0);

const esc = (s) => String(s).replace(/[&<>"]/g, c => (
  {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

// ---- waveform -------------------------------------------------------------
const cv = $("wave"), ctx = cv.getContext("2d");
const scv = $("sigwave"), sctx = scv.getContext("2d");
const icv = $("isowave"), ictx = icv.getContext("2d");

function fit(canvas, c2d){
  const r = canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(r.width * dpr);
  canvas.height = Math.round(r.height * dpr);
  c2d.setTransform(dpr, 0, 0, dpr, 0, 0);
}
function sizeCanvas(){ fit(cv, ctx); fit(scv, sctx); if (!$("iso-strip").hidden) fit(icv, ictx); }
window.addEventListener("resize", () => { sizeCanvas(); drawWave(); drawSignal(); drawIso(); });

function drawWave(){
  const w = cv.clientWidth, h = cv.clientHeight, mid = h / 2;
  ctx.clearRect(0, 0, w, h);

  // Amplitude is the only thing encoded: one mirrored bar per sample, and a
  // vertical ramp so louder peaks read hotter. Colour never means category.
  const ramp = ctx.createLinearGradient(0, 0, 0, h);
  ramp.addColorStop(0, "#F97316");
  ramp.addColorStop(.34, "#D9469F");
  ramp.addColorStop(.5, "#8B5CF6");
  ramp.addColorStop(.66, "#D9469F");
  ramp.addColorStop(1, "#F97316");

  const n = levels.length, gap = w / n, bw = Math.max(2, gap - 2);
  ctx.lineCap = "round";
  ctx.lineWidth = bw;
  ctx.strokeStyle = recording ? ramp : "#2A211D";
  for (let i = 0; i < n; i++){
    const amp = Math.max(1.5, Math.min(levels[i] * GAIN, 1) * (mid - 12));
    const x = gap * (i + .5);
    ctx.beginPath();
    ctx.moveTo(x, mid - amp);
    ctx.lineTo(x, mid + amp);
    ctx.stroke();
  }
  ctx.strokeStyle = "#332A26";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(w, mid); ctx.stroke();
}

// ---- mic check ------------------------------------------------------------
const SIGNAL = 0.005;        // ~-46 dBFS: above the noise floor of a live mic
let monLevels = new Array(40).fill(0), monHot = false;

function drawSignal(){
  const w = scv.clientWidth, h = scv.clientHeight, mid = h / 2;
  sctx.clearRect(0, 0, w, h);
  const n = monLevels.length, gap = w / n;
  sctx.lineCap = "round";
  sctx.lineWidth = Math.max(2, gap - 3);
  // One series, so one colour: green once the mic is actually hearing
  // something, flat grey while it is silent.
  sctx.strokeStyle = monHot ? "#2FBF71" : "#D9CBC5";
  for (let i = 0; i < n; i++){
    const amp = Math.max(1, Math.min(monLevels[i] * GAIN, 1) * (mid - 4));
    const x = gap * (i + .5);
    sctx.beginPath();
    sctx.moveTo(x, mid - amp);
    sctx.lineTo(x, mid + amp);
    sctx.stroke();
  }
}

// ---- delayed isolated view ------------------------------------------------
// Same widget style as the mic check, but the data is the last window of mic
// audio after a trip through ElevenLabs - so it trails reality by seconds.
let isoLevels = new Array(40).fill(0);

function drawIso(){
  if ($("iso-strip").hidden) return;
  const w = icv.clientWidth, h = icv.clientHeight, mid = h / 2;
  ictx.clearRect(0, 0, w, h);
  const n = isoLevels.length, gap = w / n;
  ictx.lineCap = "round";
  ictx.lineWidth = Math.max(2, gap - 3);
  ictx.strokeStyle = "#8B5CF6";   // violet: cleaned signal, vs the raw green
  for (let i = 0; i < n; i++){
    const amp = Math.max(1, Math.min(isoLevels[i] * GAIN, 1) * (mid - 4));
    const x = gap * (i + .5);
    ictx.beginPath();
    ictx.moveTo(x, mid - amp);
    ictx.lineTo(x, mid + amp);
    ictx.stroke();
  }
}

function applyIso(s){
  const strip = $("iso-strip"), btn = $("btn-iso");
  btn.setAttribute("aria-pressed", String(s.isoOn));
  btn.textContent = s.isoOn ? "ISO ON" : "ISO";
  if (strip.hidden === s.isoOn){
    strip.hidden = !s.isoOn;
    if (s.isoOn) fit(icv, ictx);    // it had no size while hidden
  }
  if (!s.isoOn) return;
  isoLevels = s.isoLevels;
  $("iso-text").textContent = s.isoState || "…";
  $("iso-text").title = s.isoState || "";
  $("iso-age").textContent = s.isoAge != null ? "as of " + Math.round(s.isoAge) + " s ago" : "";
  const box = $("iso-state");
  box.classList.toggle("bad", !!s.isoBad);
  box.classList.toggle("hot", !s.isoBad && s.isoAge != null);
  drawIso();
}

function applyMonitor(s){
  monLevels = s.monLevels;
  monHot = s.monLive && s.monLevel > SIGNAL;

  $("btn-mon").setAttribute("aria-pressed", String(s.monOn));
  $("btn-mon").textContent = s.monOn ? "ON" : "OFF";
  $("sig-db").textContent = s.monLevel > 0.0005
    ? (20 * Math.log10(s.monLevel)).toFixed(1) + " dBFS" : "-∞ dBFS";

  const box = $("sig-state");
  let text;
  if (s.monError){ text = s.monError; }
  else if (!s.monOn){ text = "Off - mic not held open"; }
  else if (!s.monLive){ text = "Opening the mic"; }
  else { text = monHot ? "Signal detected" : "Silent - no signal yet"; }
  $("sig-text").textContent = text;
  $("sig-text").title = text;
  box.classList.toggle("hot", monHot && !s.monError);
  box.classList.toggle("bad", !!s.monError);
  drawSignal();
}

// ---- live state -----------------------------------------------------------
const hms = (s) => [Math.floor(s / 3600), Math.floor(s % 3600 / 60), Math.floor(s % 60)]
  .map(v => String(v).padStart(2, "0")).join(":");

function applyState(s){
  levels = s.levels;
  recording = s.recording;

  $("live-name").textContent = s.liveName;
  $("live-alsa").textContent = s.liveAlsa;
  $("timer").textContent = hms(s.elapsed);
  $("timer").classList.toggle("live", recording);
  $("pill").classList.toggle("live", recording);
  $("pill-label").textContent = recording ? "REC" : "IDLE";
  $("btn-rec").classList.toggle("live", recording);
  $("rec-label").textContent = recording ? "Stop recording" : "Start recording";

  // Peak meter is a status readout, so it carries a number as well as a colour.
  const lvl = Math.min(s.level * GAIN, 1);
  const fill = $("meter-fill");
  fill.style.width = (lvl > .01 ? lvl * 100 : 0) + "%";
  fill.style.background = lvl > .92 ? "var(--rec)" : lvl > .7 ? "var(--warn)" : "var(--good)";
  $("dbfs").textContent = s.level > 0.0005
    ? (20 * Math.log10(s.level)).toFixed(1) + " dBFS" : "-∞ dBFS";

  const st = $("status");
  st.textContent = s.status;
  st.classList.toggle("bad", !!s.statusBad);

  if (s.rev !== rev){ rev = s.rev; loadDevices(); }
  applyMonitor(s);
  applyIso(s);
  drawWave();
}

// ---- devices --------------------------------------------------------------
const MIC = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="2" width="6" height="11" rx="3" fill="currentColor" stroke="none"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/></svg>';
const SPK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 9v6h4l5 4V5L8 9Z" fill="currentColor" stroke="none"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>';

async function loadDevices(){
  const d = await (await fetch("/api/devices")).json();
  $("meta-dir").textContent = d.outdir;
  $("meta-dir").title = d.outdir;
  $("drawer-dir").textContent = d.outdir;
  const list = $("list");

  if (d.error){
    list.innerHTML = '<div class="err">' + esc(d.error) + "</div>";
    $("counts").textContent = "";
    return;
  }
  const nIn = d.devices.filter(x => x.kind === "input").length;
  $("counts").textContent = nIn + " in / " + (d.devices.length - nIn) + " out";

  list.innerHTML = d.devices.map(x => {
    const isIn = x.kind === "input", chosen = isIn && x.key === d.selected;
    // A shared source reads as its own kind of thing: it is the one that keeps
    // working when the voice service already holds the mic.
    const tint = x.shared ? "var(--good)" : isIn ? "var(--violet)" : "var(--amber)";
    const wash = x.shared ? "#E8F7EF" : isIn ? "#F1EBFE" : "#FEF0E7";
    let sub = x.detail ? x.hw + "  ·  " + x.detail : x.hw;
    if (x.control) sub += "  ·  " + x.control;
    return '<div class="row' + (chosen ? " chosen" : "") + (x.enabled ? "" : " muted") +
      '" data-key="' + x.key + '" data-kind="' + x.kind + '">' +
      '<div class="glyph" style="background:' + wash + ';color:' +
        (x.enabled ? tint : "#C9BCB6") + '">' + (isIn ? MIC : SPK) + "</div>" +
      '<div class="who"><b>' + esc(x.name) + "</b><span>" + esc(sub) + "</span></div>" +
      '<span class="badge" style="background:' + wash + ";color:" + tint + '">' +
        (x.shared ? "SHARED" : isIn ? "INPUT" : "OUTPUT") + "</span>" +
      (isIn ? '<button class="radio' + (chosen ? " on" : "") + '" data-act="select" ' +
              'aria-label="Use as source" aria-pressed="' + chosen + '"></button>' +
              '<span class="radio-label">source</span>'
            : '<span style="width:20px"></span><span class="radio-label"></span>') +
      '<button class="sw' + (x.enabled ? " on" : "") + '" data-act="toggle" ' +
        'role="switch" aria-checked="' + x.enabled + '" aria-label="Mute or unmute"></button>' +
      "</div>";
  }).join("");
}

const post = (url, body) => fetch(url, {
  method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify(body || {})
});

$("list").addEventListener("click", (e) => {
  const row = e.target.closest(".row");
  if (!row) return;
  const key = row.dataset.key;
  const act = e.target.closest("[data-act]")?.dataset.act;
  if (act === "toggle") post("/api/toggle", {key});
  else if (act === "select" || row.dataset.kind === "input") post("/api/select", {key});
});

$("btn-rec").onclick = () => post("/api/record");
$("btn-refresh").onclick = () => post("/api/refresh");
$("btn-mon").onclick = () => post("/api/monitor");
$("btn-iso").onclick = () => post("/api/isolive");

// ---- recordings -----------------------------------------------------------
const kb = (n) => n > 1e6 ? (n / 1e6).toFixed(1) + " MB" : Math.round(n / 1e3) + " kB";

async function openDrawer(){
  const takes = await (await fetch("/api/recordings")).json();
  $("takes").innerHTML = takes.length ? takes.map(t =>
    '<div class="take"><div class="take-top"><b>' + esc(t.name) + "</b>" +
    (t.isolated ? '<span class="badge-iso">ISOLATED</span>' : "") +
    '<span class="when">' + kb(t.size) + "  ·  " +
    new Date(t.mtime * 1000).toLocaleString() + "</span></div>" +
    '<canvas class="take-wave" data-name="' + esc(t.name) + '" data-iso="' + t.isolated + '"></canvas>' +
    '<audio controls preload="none" src="' + t.url + '"></audio>' +
    '<div class="take-foot">' +
    // Isolated copies don't get a button: re-isolating cleaned audio just
    // spends quota. The API round trip takes seconds, hence the wait state.
    (t.isolated ? "" :
      '<button class="iso-btn" data-name="' + esc(t.name) + '"' +
      (t.isolating ? " disabled>Isolating&hellip;" : ">Isolate voice") + "</button>") +
    '<a href="' + t.url + '" download style="font-size:11px;color:var(--muted)">download</a>' +
    "</div></div>").join("") : '<div class="take sub">Nothing recorded yet.</div>';
  $("drawer").hidden = false;   // before drawing: a hidden canvas has no size
  drawTakeWaves();
}

// The static waveform under each take. Raw takes draw in grey and isolated
// copies in green (matching their badge); both share one absolute scale, so
// the background noise the isolator stripped shows as the visual difference.
async function drawTakeWaves(){
  for (const c of document.querySelectorAll(".take-wave")){
    try {
      const r = await fetch("/api/waveform?name=" + encodeURIComponent(c.dataset.name));
      if (!r.ok) continue;
      const peaks = (await r.json()).peaks || [];
      if (!document.body.contains(c)) continue;   // drawer re-rendered meanwhile
      const c2d = c.getContext("2d");
      fit(c, c2d);
      const w = c.clientWidth, h = c.clientHeight, mid = h / 2;
      c2d.clearRect(0, 0, w, h);
      const n = peaks.length, gap = w / n;
      c2d.lineCap = "round";
      c2d.lineWidth = Math.max(1.5, gap - 1.5);
      c2d.strokeStyle = c.dataset.iso === "true" ? "#2FBF71" : "#C9BCB6";
      for (let i = 0; i < n; i++){
        const amp = Math.max(1, Math.min(peaks[i] * GAIN, 1) * (mid - 2));
        const x = gap * (i + .5);
        c2d.beginPath();
        c2d.moveTo(x, mid - amp);
        c2d.lineTo(x, mid + amp);
        c2d.stroke();
      }
    } catch (e) {}   // one bad take must not stop the rest from drawing
  }
}
$("takes").addEventListener("click", async (e) => {
  const btn = e.target.closest(".iso-btn");
  if (!btn || btn.disabled) return;
  btn.disabled = true;
  btn.innerHTML = "Isolating&hellip;";
  try { await post("/api/isolate", {name: btn.dataset.name}); }
  finally { if (!$("drawer").hidden) openDrawer(); }
});
$("btn-files").onclick = openDrawer;
$("btn-files2").onclick = openDrawer;
$("btn-close").onclick = () => { $("drawer").hidden = true; };
$("drawer").addEventListener("click", (e) => {
  if (e.target === $("drawer")) $("drawer").hidden = true;
});

// ---- stream ---------------------------------------------------------------
function connect(){
  const es = new EventSource("/api/events");
  es.onmessage = (e) => applyState(JSON.parse(e.data));
  es.onerror = () => { es.close(); setTimeout(connect, 1500); };  // robot rebooted, wifi blipped
}
sizeCanvas();
drawWave();
drawSignal();
loadDevices();
connect();
</script>
</body>
</html>
"""


# -------------------------------------------------------------- server -----


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ReachyAudio/2.0"

    console: Console = None     # set on the server before serving
    verbose: bool = False

    def log_message(self, fmt, *args):
        if self.verbose:
            super().log_message(fmt, *args)

    # -- helpers ------------------------------------------------------------

    def _send(self, code: int, ctype: str, body: bytes, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, "application/json", json.dumps(obj).encode())

    def _body(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return {}

    # -- routes -------------------------------------------------------------

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        c = self.console
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", PAGE.encode(),
                       {"Cache-Control": "no-store"})
        elif path == "/api/state":
            self._json(c.snapshot())
        elif path == "/api/devices":
            self._json(c.devices_payload())
        elif path == "/api/recordings":
            self._json(c.recordings())
        elif path == "/api/events":
            self._events()
        elif path == "/api/waveform":
            q = parse_qs(urlparse(self.path).query)
            self._waveform(q.get("name", [""])[0])
        elif path.startswith("/rec/"):
            self._wav(path[len("/rec/"):])
        else:
            self._send(404, "text/plain", b"not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        c = self.console
        if path == "/api/refresh":
            c.refresh()
        elif path == "/api/record":
            c.toggle_record()
        elif path == "/api/monitor":
            c.toggle_monitor()
        elif path == "/api/isolive":
            c.toggle_isolive()
        elif path == "/api/select":
            c.select(self._body().get("key", ""))
        elif path == "/api/toggle":
            c.toggle_device(self._body().get("key", ""))
        elif path == "/api/isolate":
            c.isolate(self._body().get("name", ""))
        else:
            self._send(404, "text/plain", b"not found")
            return
        self._json(c.snapshot())

    # -- server-sent events -------------------------------------------------

    def _events(self) -> None:
        """One long-lived response per browser tab; the level meter rides on it."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        # No Content-Length and no chunked framing, so the body has to be
        # read-until-close or the browser buffers it forever waiting for chunks.
        self.send_header("Connection", "close")
        self.close_connection = True
        self.end_headers()
        try:
            while True:
                blob = json.dumps(self.console.snapshot()).encode()
                self.wfile.write(b"data: " + blob + b"\n\n")
                self.wfile.flush()
                time.sleep(PUSH)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # tab closed

    def _waveform(self, name: str) -> None:
        """Peak levels for one recording, drawn as the drawer's waveform."""
        if "/" in name or "\\" in name or not name.endswith((".wav", ".mp3")):
            self._json({"error": "bad name"}, 400)
            return
        path = self.console.outdir / name
        if not path.is_file():
            self._json({"error": "not found"}, 404)
            return
        try:
            peaks = waveform_peaks(path)
        except (OSError, wave.Error, subprocess.SubprocessError):
            peaks = [0.0] * WAVE_PEAKS   # draw a flat line rather than 500
        self._json({"peaks": [round(v, 4) for v in peaks]})

    # -- WAV playback -------------------------------------------------------

    def _wav(self, name: str) -> None:
        """Serve a recording, honouring Range so the browser can seek."""
        if "/" in name or "\\" in name or not name.endswith((".wav", ".mp3")):
            self._send(400, "text/plain", b"bad name")
            return
        ctype = "audio/mpeg" if name.endswith(".mp3") else "audio/wav"
        path = self.console.outdir / name
        if not path.is_file():
            self._send(404, "text/plain", b"not found")
            return
        size = path.stat().st_size
        start, end = 0, size - 1
        rng = self.headers.get("Range", "")
        partial = False
        if rng.startswith("bytes="):
            lo, _, hi = rng[6:].partition("-")
            try:
                if lo:
                    start = int(lo)
                    end = int(hi) if hi else end
                else:                       # suffix form: bytes=-N
                    start = max(0, size - int(hi))
                partial = 0 <= start <= end < size
            except ValueError:
                partial = False
        if not partial:
            start, end = 0, size - 1
        length = end - start + 1

        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with path.open("rb") as fh:
            fh.seek(start)
            left = length
            while left > 0:
                block = fh.read(min(64 * 1024, left))
                if not block:
                    break
                self.wfile.write(block)
                left -= len(block)


def _lan_ip() -> str | None:
    """Our address on the route out - the one other devices should dial."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


# ----------------------------------------------------------------- cli -----


def print_devices(audio: Audio) -> int:
    audio.refresh()
    if audio.error:
        print(audio.error, file=sys.stderr)
        return 1
    for kind in ("input", "output"):
        rows = [d for d in audio.devices if d.kind == kind]
        print(f"\n{kind.upper()}  ({len(rows)})")
        for d in rows:
            state = "on " if d.enabled else "off"
            ctl = d.control or "-"
            print(f"  [{state}] {d.hw:<12} {d.name:<34} switch={ctl}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="print devices and exit")
    ap.add_argument("--outdir", default="~/Recordings/reachy",
                    help="where WAV files are written (default: %(default)s)")
    ap.add_argument("--host", default="0.0.0.0",
                    help="interface to bind (default: %(default)s, i.e. the whole LAN)")
    ap.add_argument("--port", type=int, default=8090,
                    help="port (default: %(default)s; the robot already uses 8000/8080/8443)")
    ap.add_argument("--no-monitor", dest="monitor", action="store_false",
                    help="do not hold the mic open for the live mic-check widget")
    ap.add_argument("--verbose", action="store_true", help="log every request")
    args = ap.parse_args()

    audio = Audio()
    if args.list:
        return print_devices(audio)

    console = Console(audio, Path(args.outdir).expanduser(), monitor=args.monitor)
    Handler.console = console
    Handler.verbose = args.verbose

    try:
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        print(f"Cannot bind {args.host}:{args.port} - {exc}", file=sys.stderr)
        console.shutdown()
        return 1
    httpd.daemon_threads = True

    print("Reachy Mini audio console")
    print(f"  local     http://127.0.0.1:{args.port}")
    ip = _lan_ip()
    if args.host != "127.0.0.1" and ip:
        print(f"  network   http://{ip}:{args.port}")
        print(f"  mDNS      http://{socket.gethostname()}.local:{args.port}")
    print(f"  saving to {console.outdir}")
    print("Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        console.shutdown()
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
