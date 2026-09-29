#!/home/pollen/Supervaise-Reachy-Mini-Project-main/app/.venv/bin/python
"""AEC reference-feed calibration (2026-09-01, Bluetooth self-hearing fix).

Measures, with the CURRENT audio route (run `audio-out status`):
  lag_ref  : chirp written to pcm cj_ref_feed (PipeWire -> XMOS) -> seen on the
             XVF3800's AEC reference tap (AUDIO_MGR_OP_R = 12,0)
  lag_echo : chirp written to pcm audio_out_route (the speaker in use) -> heard
             on raw mic 0 (AUDIO_MGR_OP_R = 3,0)
and prints the CJ_AEC_REF_DELAY_MS to put in the supervaise drop-in so the
echo lands ~80 ms after the reference (the chip's AEC tail is 3072 samples =
192 ms; SYS_DELAY clamps at 256 samples, so the host must delay).

Usage:  aec_ref_calib.py [--repeats 3] [--margin-ms 80]
Restores AUDIO_MGR_OP_R = 8,0 on exit. Needs the mic meter on /maintain OFF.
"""
import argparse, json, os, subprocess, sys, threading, time
import numpy as np
import sounddevice as sd

RATE = 16000
XVF = os.path.expanduser("~/bin/xvf-ctl")


def xvf(*a):
    r = subprocess.run([XVF, *a], capture_output=True, text=True, timeout=10)
    line = [l for l in r.stdout.splitlines() if l.startswith("{")]
    return json.loads(line[-1]) if line else {"ok": False, "error": r.stderr[-200:]}


def chirp(dur=0.6, f0=300, f1=3000, amp=0.25):
    t = np.arange(int(RATE * dur)) / RATE
    k = (f1 - f0) / dur
    x = np.sin(2 * np.pi * (f0 * t + 0.5 * k * t * t)) * amp
    x *= np.hanning(len(x)) ** 0.3
    return (x * 32767).astype(np.int16)


class Rec:
    """2-ch capture of reachymini_audio_src with the wall-clock of sample 0."""
    def __init__(self):
        self.buf, self.t0, self.lock = [], None, threading.Lock()
        self.st = sd.InputStream(device="reachymini_audio_src", samplerate=RATE, channels=2,
                                 dtype="int16", blocksize=256, callback=self._cb)
        self.st.start()

    def _cb(self, indata, frames, tinfo, status):
        now = time.monotonic()
        with self.lock:
            if self.t0 is None:
                self.t0 = now - frames / RATE
            self.buf.append(indata.copy())

    def stop(self):
        self.st.stop(); self.st.close()
        return np.concatenate(self.buf) if self.buf else np.zeros((0, 2), np.int16)


def lag_of(sig, ref, t0_rec, t_write):
    """Seconds from t_write to the chirp's arrival in `sig` (cross-correlation peak)."""
    s = sig.astype(np.float64); s -= s.mean()
    r = ref.astype(np.float64)
    n = len(s) + len(r)
    c = np.fft.irfft(np.fft.rfft(s, n) * np.conj(np.fft.rfft(r, n)), n)[:len(s)]
    i = int(np.argmax(c))
    snr = float(c[i] / (np.sqrt(np.mean(c * c)) + 1e-9))
    return t0_rec + i / RATE - t_write, snr


def measure(device, op, label, ref, repeats):
    r = xvf("write", "AUDIO_MGR_OP_R", *map(str, op))
    if not r.get("ok"):
        sys.exit(f"cannot set AUDIO_MGR_OP_R: {r}")
    time.sleep(0.3)
    out = []
    for k in range(repeats):
        rec = Rec()
        time.sleep(0.6)
        st = sd.OutputStream(device=device, samplerate=RATE, channels=1, dtype="int16",
                             blocksize=800, latency=0.15)
        st.start()
        t_write = time.monotonic()
        st.write(ref)
        st.write(np.zeros(RATE // 2, np.int16))
        st.stop(); st.close()
        time.sleep(1.2)
        a = rec.stop()
        if not len(a):
            print(f"  {label}: no audio captured"); continue
        lag, snr = lag_of(a[:, 1], ref, rec.t0, t_write)
        print(f"  {label} #{k + 1}: {lag * 1000:7.1f} ms   (peak/rms {snr:.0f}, R rms {20 * np.log10(np.sqrt(np.mean(a[:, 1].astype(float) ** 2)) / 32768 + 1e-9):.0f} dBFS)")
        if snr > 8:
            out.append(lag)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--margin-ms", type=float, default=80)
    a = ap.parse_args()
    route = subprocess.run([os.path.expanduser("~/bin/audio-out"), "status"], capture_output=True, text=True).stdout
    print("route:", " ".join(route.split("\n")[1:2]).strip() or route[:80])
    ref = chirp()
    try:
        print("1) reference path: cj_ref_feed -> XVF3800 reference tap (12,0)")
        lr = measure("cj_ref_feed", (12, 0), "lag_ref", ref, a.repeats)
        print("2) echo path: audio_out_route -> raw mic 0 (3,0)")
        le = measure("audio_out_route", (3, 0), "lag_echo", ref, a.repeats)
    finally:
        xvf("write", "AUDIO_MGR_OP_R", "8", "0")
    if not lr or not le:
        sys.exit("not enough clean measurements — is the speaker on and the mic meter off?")
    lag_ref, lag_echo = float(np.median(lr)), float(np.median(le))
    delay = max(0.0, (lag_echo - lag_ref) * 1000 - a.margin_ms)
    print(f"\nlag_ref {lag_ref * 1000:.0f} ms   lag_echo {lag_echo * 1000:.0f} ms   "
          f"echo - ref = {(lag_echo - lag_ref) * 1000:.0f} ms (AEC tail 192 ms)")
    print(f"=> CJ_AEC_REF_DELAY_MS={delay:.0f}   (echo then lands ~{a.margin_ms:.0f} ms after the reference)")
    if (lag_echo - lag_ref) * 1000 < 20:
        print("   (route is probably the internal speaker: no feed needed there)")


if __name__ == "__main__":
    main()
