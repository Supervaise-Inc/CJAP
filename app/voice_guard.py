"""Panganiban's voice or nothing (2026-09-16).

Every TTS call site used to FAIL OPEN to the OpenAI ``tts-1`` / ``echo`` voice —
per sentence, with nothing but a log line. On 2026-09-16 the ElevenLabs
account's character quota ran out (131,000/131,000) and the result was heard in
the room: cached lines played in Panganiban's cloned voice, freshly composed
sentences came out as an American stranger, and the voice switched back and
forth *inside one answer*. Nothing on the robot, on /console or in the room
said why.

This module is the single place that decides whether a substitute voice may be
used, and the single place that records that his voice is failing so the
operator can see it.

The rule: **only a clone of Panganiban speaks.** There are now two of them —
Fish Audio (model "CJAP") and ElevenLabs — and either is acceptable because
both are the same person. The OpenAI voice is not, and a call site that can
reach neither clone stays silent rather than putting a stranger in front of an
audience. See speech_engines.tts_cloned_wav for the chain and
main_voice_robot._say_apology for how a silenced turn degrades.

Three states, not two:

* **ok** — the primary clone is speaking.
* **degraded** (``standby`` set) — the primary failed and the OTHER clone is
  speaking. The room still hears Panganiban, so this is amber, not red; but the
  two clones are not identical and someone who knows the voice will notice.
* **down** (``ok`` false, no ``standby``) — neither clone can speak. Lines are
  being suppressed, and the operator needs to know now.

Two deliberate non-behaviours:

* This is **not** a circuit breaker. A failure never stops the *next* call from
  trying the primary again — `blocked()` only answers "may I substitute for the
  failure that just happened?". A transient blip therefore self-heals on the
  next sentence, and a topped-up key recovers with no restart.
* The latch only clears on a **real** synthesis by the primary engine
  (`synth_ok()` is called from the cache-MISS branch of each engine wrapper). A
  clip-cache hit needs no network and proves nothing about the API, so it must
  never clear the banner.

State is published to tmpfs for the dashboard, which runs as a separate service
under the system python3 and reads the JSON directly (ui_common._read_json)
rather than importing this module. The robot also ships the same state to the
lease authority in its 1 Hz floor report, so /console can show the banner for
BOTH machines.

Escape hatch: ``CJ_ALLOW_VOICE_SUBSTITUTION=1`` restores the old fail-open
behaviour for an operator who decides a wrong voice beats silence. Off by
default, and the banner says when it is on.
"""
from __future__ import annotations

import json
import os
import socket
import threading
import time

# tmpfs only: the dashboard polls this and an SD-card write per failed
# sentence would be wear for nothing.
STATE_PATH = os.environ.get("CJ_VOICE_GUARD_PATH", "/dev/shm/cj_voice_guard.json")

# Why a clone failed, in the words the operator needs. voice.speak (ElevenLabs)
# and voice.fish both raise with exactly these reasons; anything else reads as
# "error". Deliberately vendor-neutral — the engine is named separately.
REASON_TEXT = {
    "quota": "its quota or credit is used up",
    "network": "the robot cannot reach it",
    "error": "it rejected the request",
}
ENGINE_LABEL = {"fish": "Fish Audio", "elevenlabs": "ElevenLabs"}

_lock = threading.Lock()
_state = {
    "ok": True,          # True until a real failure; only a real primary synth clears it
    "engine": None,      # the engine that FAILED
    "reason": None,      # quota | network | error
    "detail": "",
    "where": "",         # answer | filler | line | say-text
    "since": None,       # wall clock of the first failure in this outage
    "ts": None,          # wall clock of the most recent failure
    "failures": 0,       # failures in this outage
    "suppressed": 0,     # utterances kept silent rather than voiced by a stranger
    "standby": None,     # the OTHER clone, carrying speech while the primary is down
    "standby_lines": 0,  # utterances the standby clone has spoken
    "recovered_at": None,
    # Which clone last put audio in the room, and when. Not diagnostics: this
    # is the operator's answer to "is it actually speaking as Fish?" — the
    # engine NAMED in the config and the engine actually SPEAKING can differ
    # for a whole session (2026-09-16, user: "making sure that it is fish audio").
    "last_engine": None,
    "last_engine_ts": None,
}


def label(engine) -> str:
    return ENGINE_LABEL.get(engine, engine or "the voice service")


def substitution_allowed() -> bool:
    """True when a NON-clone voice may stand in. Only the operator's explicit
    override, or a build that is not using a cloned voice at all (nothing to
    protect: the OpenAI voice IS the configured voice then)."""
    if os.environ.get("CJ_ALLOW_VOICE_SUBSTITUTION", "").strip().lower() in {
            "1", "true", "yes", "on"}:
        return True
    return _backend() != "elevenlabs"


def _backend() -> str:
    """CJ_TTS_BACKEND still selects cloned-voice mode as a whole; the ORDER of
    the clones inside that mode is CJ_TTS_ORDER (see speech_engines)."""
    try:
        import speech_engines
        return str(getattr(speech_engines, "TTS_BACKEND", "openai")).strip().lower()
    except Exception:
        return os.environ.get("CJ_TTS_BACKEND", "openai").strip().lower()


def primary_engine() -> str | None:
    """The first configured clone — the one whose success means "healthy"."""
    try:
        import speech_engines
        order = speech_engines.engine_order()
        return order[0] if order else None
    except Exception:
        return None


def reason_of(exc) -> str:
    """SynthError / FishError carry .reason (quota | network | error); anything
    else is an error. Never reads the message, which is where a key could hide."""
    r = getattr(exc, "reason", None)
    return r if r in REASON_TEXT else "error"


def _begin_outage_locked(now):
    if _state["ok"]:
        _state["since"] = now
        _state["failures"] = 0
        _state["suppressed"] = 0
        _state["standby_lines"] = 0


def blocked(exc, where: str = "", engine=None) -> bool:
    """Record that NO clone could speak, and answer the caller's only question:
    must this utterance stay silent?

    Always call this from the ``except`` around the last clone attempt —
    recording the failure is what puts the banner up, and it happens whether or
    not substitution is allowed."""
    reason = reason_of(exc)
    detail = f"{type(exc).__name__}: {str(exc)[:120]}"
    allow = substitution_allowed()
    now = time.time()
    with _lock:
        _begin_outage_locked(now)
        _state.update(ok=False, engine=engine or _state.get("engine"), reason=reason,
                      detail=detail, where=where or "", ts=now, standby=None,
                      recovered_at=None)
        _state["failures"] += 1
        if not allow:
            _state["suppressed"] += 1
        snapshot = dict(_state)
    _publish(snapshot)
    return not allow


def degraded(exc, engine: str, where: str = "", failed=None) -> None:
    """The primary failed but the OTHER CLONE OF THE SAME PERSON spoke instead.
    Not the same event as `blocked`: the room still hears Panganiban, so this is
    a warning to fix the primary, not an emergency."""
    reason = reason_of(exc)
    detail = f"{type(exc).__name__}: {str(exc)[:120]}"
    now = time.time()
    with _lock:
        _begin_outage_locked(now)
        _state.update(ok=False, engine=failed or _state.get("engine"), reason=reason,
                      detail=detail, where=where or "", ts=now, standby=engine,
                      recovered_at=None)
        _state["failures"] += 1
        _state["standby_lines"] += 1
        snapshot = dict(_state)
    _publish(snapshot)


def spoke(engine: str) -> None:
    """Record which clone produced the audio just handed to the player. Cheap
    (tmpfs) and called per sentence, like the speaking feed beside it."""
    with _lock:
        if _state["last_engine"] == engine:
            _state["last_engine_ts"] = time.time()
            return          # same engine as last sentence: no republish needed
        _state.update(last_engine=engine, last_engine_ts=time.time())
        snapshot = dict(_state)
    _publish(snapshot)


def synth_ok(engine: str, where: str = "") -> None:
    """A REAL synthesis succeeded. Clears the guard only when it was the PRIMARY
    engine: the standby succeeding is the degraded state, not recovery. Called
    from the cache-MISS branch of each engine wrapper, because a cache hit needs
    no network and so proves nothing."""
    if engine != primary_engine():
        return
    with _lock:
        if _state["ok"]:
            return
        was = dict(_state)
        _state.update(ok=True, engine=None, reason=None, detail="", where=where or "",
                      ts=time.time(), standby=None, recovered_at=time.time(),
                      failures=0, suppressed=0, standby_lines=0)
        snapshot = dict(_state)
    print(f"[voice-guard] {label(engine)} RECOVERED after {was['failures']} failure(s), "
          f"{was['suppressed']} utterance(s) kept silent, "
          f"{was['standby_lines']} spoken by the standby", flush=True)
    _publish(snapshot)


# legacy name, kept because the 2026-09-16 first cut called it ok()
def ok(where: str = "") -> None:
    synth_ok(primary_engine() or "", where)


def state() -> dict:
    """The current picture, with the fields the banner needs derived here so
    the two dashboards cannot word it differently."""
    with _lock:
        s = dict(_state)
    s["substitution_allowed"] = substitution_allowed()
    s["backend"] = _backend()
    s["primary"] = primary_engine()
    s["machine"] = _machine()
    s["message"] = message(s)
    return s


def message(s: dict | None = None) -> str:
    """One operator-facing sentence. Empty when nothing is wrong."""
    s = s if s is not None else state()
    if s.get("ok"):
        return ""
    who = label(s.get("engine"))
    why = REASON_TEXT.get(s.get("reason"), REASON_TEXT["error"])
    if s.get("standby"):
        return (f"Panganiban's primary voice ({who}) is failing — {why}. "
                f"The {label(s['standby'])} clone of the same voice is speaking instead "
                f"({s['standby_lines']} line(s) so far), so the room still hears him — but "
                f"the two clones are not identical. Fix the primary when you can.")
    if s.get("substitution_allowed"):
        return (f"Panganiban's voice is failing ({who} — {why}) and no clone could stand in. "
                f"CJ_ALLOW_VOICE_SUBSTITUTION is ON, so answers are being spoken in a "
                f"DIFFERENT voice ({s['failures']} so far). Turn it off, or fix the voice, "
                f"before anyone hears this.")
    return (f"Panganiban's voice is unavailable ({who} — {why}) and no clone could stand in. "
            f"{s['suppressed']} utterance(s) have been kept SILENT rather than spoken in "
            f"another voice. Top up the voice service, or switch to DUET, which plays "
            f"pre-rendered audio and needs neither quota nor network.")


def _machine() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return ""


def _publish(snapshot: dict) -> None:
    """Atomic tmpfs write for the dashboards. Fails open — a guard that cannot
    write its state must still block the wrong voice."""
    try:
        snapshot = dict(snapshot)
        snapshot["substitution_allowed"] = substitution_allowed()
        snapshot["backend"] = _backend()
        snapshot["primary"] = primary_engine()
        snapshot["machine"] = _machine()
        snapshot["message"] = message(snapshot)
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(snapshot, f)
        os.replace(tmp, STATE_PATH)
    except OSError:
        pass


def report() -> dict:
    """The compact form that rides in the robot's 1 Hz floor report, so the
    lease authority can raise the banner for the machine that is failing —
    including the one the operator is not looking at."""
    s = state()
    return {"ok": bool(s["ok"]), "reason": s["reason"], "engine": s["engine"],
            "last_engine": s["last_engine"], "last_engine_ts": s["last_engine_ts"],
            "suppressed": int(s["suppressed"]), "failures": int(s["failures"]),
            "substitution_allowed": bool(s["substitution_allowed"]),
            "standby": s["standby"], "standby_lines": int(s["standby_lines"]),
            "since": s["since"]}


def boot() -> None:
    """Clear the published state at app start.

    STATE_PATH is on tmpfs, which survives a SERVICE restart and only clears on
    reboot — so without this a resolved outage leaves its banner up for ever:
    seen 2026-09-16, when /maintain still read "Fish Audio is failing" eleven
    minutes after the credit was topped up and the app restarted, because
    nothing had spoken since to overwrite the file. A fresh process has, by
    definition, no outage in progress; the first failure after boot republishes
    within one sentence."""
    reset()
    _publish(dict(_state))
    print("[voice-guard] armed — "
          f"primary {label(primary_engine())}, "
          f"substitute voice {'ALLOWED' if substitution_allowed() else 'refused'}",
          flush=True)


def reset() -> None:
    """Tests only (and boot())."""
    with _lock:
        _state.update(ok=True, engine=None, reason=None, detail="", where="",
                      since=None, ts=None, failures=0, suppressed=0, standby=None,
                      standby_lines=0, recovered_at=None, last_engine=None,
                      last_engine_ts=None)
