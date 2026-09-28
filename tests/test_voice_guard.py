"""The cloned voice or nothing (2026-09-16): app/voice_guard.py + the banners.

User: "there was voice switching when the robot answers" — the ElevenLabs
account hit 131,000/131,000 characters, every uncached sentence 401'd, and each
call site quietly fell back to the OpenAI `echo` voice. Cached lines still
played in Panganiban's cloned voice, so the voice switched back and forth
*inside one answer*, and nothing on the robot, on /console or in the room said
why.

The answer has two halves: app/voice_guard.py refuses the stranger, and
voice/fish.py adds a SECOND clone of the same person (Fish Audio model "CJAP")
so there is something acceptable to fall to. Fish is the primary since the
user's "prioritize fish.audio voice" the same day.

What is asserted:
  * substitution by a NON-clone is refused by default, allowed only by the
    operator's explicit override, and moot when no cloned voice is configured;
  * engine_order() honours CJ_TTS_ORDER, skips engines with no credentials, and
    puts Fish first by default;
  * falling from one clone to the OTHER is `degraded`, not `blocked` — the room
    still hears Panganiban, so it is amber, not red;
  * a failure is recorded whether or not substitution is allowed — recording is
    what raises the banner;
  * only a REAL synthesis BY THE PRIMARY clears the guard (a clip-cache hit
    proves nothing about the API, and the standby succeeding is the degraded
    state, not recovery);
  * the tmpfs state file the dashboards read is written atomically and carries
    a message an operator can act on;
  * a robot's floor report carries the state, the console turns it into the
    right level of warning, and a robot whose build predates the field reads as
    "unknown", never as "bad".

Run:  app/.venv/bin/python -m pytest tests/test_voice_guard.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dashboard"))
sys.path.insert(0, str(ROOT / "app"))

import console as cs          # noqa: E402
import voice_guard as vg      # noqa: E402


class SynthError(Exception):
    """Stands in for voice.speak.SynthError: the only thing the guard reads off
    an exception is .reason (never the message, which is where a key could
    hide)."""

    def __init__(self, reason, detail=""):
        super().__init__(detail or reason)
        self.reason = reason


@pytest.fixture(autouse=True)
def clean(tmp_path, monkeypatch):
    """Every test starts with an untripped guard, its own state file, a cloned
    voice configured, a known engine order and no operator override."""
    monkeypatch.setattr(vg, "STATE_PATH", str(tmp_path / "cj_voice_guard.json"))
    monkeypatch.setattr(vg, "_backend", lambda: "elevenlabs")
    monkeypatch.setattr(vg, "primary_engine", lambda: "fish")
    monkeypatch.delenv("CJ_ALLOW_VOICE_SUBSTITUTION", raising=False)
    vg.reset()
    yield
    vg.reset()


# ────────────────────────────────────────────────────────────────────────────
# 1. the rule: the cloned voice or nothing
# ────────────────────────────────────────────────────────────────────────────
def test_substitution_is_refused_by_default():
    assert vg.substitution_allowed() is False
    assert vg.blocked(SynthError("quota", "key credit cap exhausted (401)"),
                      where="answer") is True


def test_operator_override_restores_the_old_fail_open(monkeypatch):
    monkeypatch.setenv("CJ_ALLOW_VOICE_SUBSTITUTION", "1")
    assert vg.substitution_allowed() is True
    assert vg.blocked(SynthError("quota"), where="answer") is False


@pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
def test_override_accepts_the_usual_truthy_spellings(monkeypatch, value):
    monkeypatch.setenv("CJ_ALLOW_VOICE_SUBSTITUTION", value)
    assert vg.substitution_allowed() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
def test_override_is_off_for_anything_else(monkeypatch, value):
    monkeypatch.setenv("CJ_ALLOW_VOICE_SUBSTITUTION", value)
    assert vg.substitution_allowed() is False


def test_nothing_to_protect_when_the_cloned_voice_is_not_the_backend(monkeypatch):
    # A build running the OpenAI voice deliberately: the "substitute" IS the
    # configured voice, so the guard must not silence it.
    monkeypatch.setattr(vg, "_backend", lambda: "openai")
    assert vg.substitution_allowed() is True
    assert vg.blocked(SynthError("quota"), where="answer") is False


# ────────────────────────────────────────────────────────────────────────────
# 2. recording — what puts the banner up
# ────────────────────────────────────────────────────────────────────────────
def test_a_failure_is_recorded_even_when_substitution_is_allowed(monkeypatch):
    monkeypatch.setenv("CJ_ALLOW_VOICE_SUBSTITUTION", "1")
    vg.blocked(SynthError("quota"), where="answer")
    s = vg.state()
    assert s["ok"] is False and s["failures"] == 1
    # allowed => the line was voiced by a stranger, not suppressed
    assert s["suppressed"] == 0
    assert "spoken in a DIFFERENT voice" in s["message"]
    assert "CJ_ALLOW_VOICE_SUBSTITUTION is ON" in s["message"]


def test_suppressed_counts_only_lines_actually_kept_silent():
    for _ in range(3):
        vg.blocked(SynthError("quota"), where="answer")
    s = vg.state()
    assert s["failures"] == 3 and s["suppressed"] == 3
    assert "SILENT" in s["message"]


@pytest.mark.parametrize("reason,needle", [
    ("quota", "its quota or credit is used up"),
    ("network", "the robot cannot reach it"),
    ("error", "it rejected the request"),
])
def test_the_message_names_the_cause(reason, needle):
    vg.blocked(SynthError(reason), where="answer")
    assert needle in vg.state()["message"]


def test_the_message_names_the_engine_that_failed():
    vg.blocked(SynthError("quota"), where="answer", engine="fish")
    assert "Fish Audio" in vg.state()["message"]
    vg.reset()
    vg.blocked(SynthError("quota"), where="answer", engine="elevenlabs")
    assert "ElevenLabs" in vg.state()["message"]


def test_an_unknown_exception_reads_as_error():
    vg.blocked(ValueError("something else went wrong"), where="answer")
    assert vg.state()["reason"] == "error"


def test_the_detail_never_carries_more_than_a_short_summary():
    vg.blocked(SynthError("error", "x" * 500), where="answer")
    assert len(vg.state()["detail"]) <= 140


def test_the_operator_is_told_duet_still_works():
    vg.blocked(SynthError("quota"), where="answer")
    assert "DUET" in vg.state()["message"]


# ────────────────────────────────────────────────────────────────────────────
# 2b. degraded — the OTHER clone of the same person took over
# ────────────────────────────────────────────────────────────────────────────
def test_the_other_clone_speaking_is_degraded_not_blocked():
    vg.degraded(SynthError("quota"), "elevenlabs", where="answer", failed="fish")
    s = vg.state()
    assert s["ok"] is False and s["standby"] == "elevenlabs"
    assert s["suppressed"] == 0 and s["standby_lines"] == 1
    assert "ElevenLabs clone of the same voice is speaking instead" in s["message"]
    # the room still hears him, so the operator is not told to switch to DUET
    assert "DUET" not in s["message"]


def test_degraded_names_both_engines():
    vg.degraded(SynthError("quota"), "elevenlabs", where="answer", failed="fish")
    m = vg.state()["message"]
    assert "Fish Audio" in m and "ElevenLabs" in m


def test_a_later_total_failure_clears_the_standby():
    vg.degraded(SynthError("quota"), "elevenlabs", where="answer", failed="fish")
    vg.blocked(SynthError("quota"), where="answer", engine="fish")
    s = vg.state()
    assert s["standby"] is None and s["suppressed"] == 1
    assert "kept SILENT" in s["message"]


# ────────────────────────────────────────────────────────────────────────────
# 3. recovery — only a real synthesis clears it
# ────────────────────────────────────────────────────────────────────────────
def test_a_real_primary_synthesis_clears_the_guard():
    vg.blocked(SynthError("quota"), where="answer")
    assert vg.state()["ok"] is False
    vg.synth_ok("fish")           # the primary, per the fixture
    s = vg.state()
    assert s["ok"] is True and s["message"] == ""


def test_the_standby_succeeding_is_not_recovery():
    """ElevenLabs rendering a sentence while Fish is down means the answer was
    spoken — not that the primary is back. Clearing here would drop the banner
    while every sentence still costs a fallback."""
    vg.degraded(SynthError("quota"), "elevenlabs", where="answer", failed="fish")
    vg.synth_ok("elevenlabs")     # the standby, not the primary
    assert vg.state()["ok"] is False


def test_recovery_resets_the_counters_for_the_next_outage():
    for _ in range(2):
        vg.blocked(SynthError("quota"), where="answer")
    vg.synth_ok("fish")
    vg.blocked(SynthError("network"), where="answer")
    s = vg.state()
    assert s["failures"] == 1 and s["suppressed"] == 1 and s["reason"] == "network"


def test_recovery_clears_the_standby_counters_too():
    vg.degraded(SynthError("quota"), "elevenlabs", where="answer", failed="fish")
    vg.synth_ok("fish")
    s = vg.state()
    assert s["ok"] is True and s["standby"] is None and s["standby_lines"] == 0


def test_the_guard_is_not_a_circuit_breaker():
    """A failure must never stop the NEXT call from trying ElevenLabs again:
    that is what lets a blip self-heal and a topped-up key recover with no
    restart. The guard exposes no "skip the attempt" state at all."""
    vg.blocked(SynthError("network"), where="answer")
    assert not hasattr(vg, "should_skip")
    # the only question it answers is about a failure that ALREADY happened
    assert vg.substitution_allowed() is False


# ────────────────────────────────────────────────────────────────────────────
# 4. the file the dashboards read
# ────────────────────────────────────────────────────────────────────────────
def test_state_file_is_written_for_the_dashboard():
    vg.blocked(SynthError("quota", "key credit cap exhausted (401)"), where="answer")
    d = json.loads(Path(vg.STATE_PATH).read_text())
    assert d["ok"] is False and d["reason"] == "quota"
    assert d["suppressed"] == 1
    assert d["substitution_allowed"] is False
    assert "DUET" in d["message"]


def test_state_file_leaves_no_temp_file_behind():
    vg.blocked(SynthError("quota"), where="answer")
    assert not Path(vg.STATE_PATH + ".tmp").exists()


def test_recovery_is_published_too():
    vg.blocked(SynthError("quota"), where="answer")
    vg.ok("synth")
    assert json.loads(Path(vg.STATE_PATH).read_text())["ok"] is True


def test_an_unwritable_state_path_still_blocks(monkeypatch):
    """A guard that cannot write its state must still refuse the wrong voice."""
    monkeypatch.setattr(vg, "STATE_PATH", "/nonexistent-dir/guard.json")
    assert vg.blocked(SynthError("quota"), where="answer") is True
    assert vg.state()["ok"] is False


def test_report_is_the_compact_form_for_the_floor_poll():
    vg.blocked(SynthError("quota"), where="answer")
    r = vg.report()
    assert set(r) == {"ok", "reason", "engine", "last_engine", "last_engine_ts",
                      "suppressed", "failures", "substitution_allowed",
                      "standby", "standby_lines", "since"}
    assert r["ok"] is False and r["reason"] == "quota"


# ────────────────────────────────────────────────────────────────────────────
# 5. the console banner, from a robot's floor report
# ────────────────────────────────────────────────────────────────────────────
class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s
        return self.t


def make_console(tmp_path, clock):
    src = cs.ConfigSources(modes_dir=str(ROOT / "config" / "modes"),
                           dropin_path=str(tmp_path / "absent.conf"),
                           dotenv_path=str(tmp_path / "absent.env"),
                           robots_path=str(ROOT / "config" / "robots.json"))
    return cs.Console(src, clock=clock, wall=clock,
                      state_path=str(tmp_path / "state.json"),
                      journal_path=str(tmp_path / "journal.jsonl"),
                      log=lambda *a, **k: None, restore=False)


def voice_warnings(console, now):
    st, d = cs.api(console, "GET", "/api/state", authed=True, now=now)
    assert st == 200
    return [w for w in d["warnings"] if w.get("kind") == "voice"]


def report(console, robot, now, voice):
    body = {"robot": robot}
    if voice is not None:
        body["voice"] = voice
    st, d = cs.api(console, "POST", "/api/lease", body=body, authed=True, now=now)
    assert st == 200, d
    return d


def test_a_failing_voice_raises_a_bad_console_banner(tmp_path):
    clock = Clock()
    c = make_console(tmp_path, clock)
    report(c, "alpha", clock(), {"ok": False, "reason": "quota", "suppressed": 4,
                                 "failures": 4, "substitution_allowed": False})
    w = voice_warnings(c, clock())
    assert len(w) == 1 and w[0]["level"] == "bad" and w[0]["robot"] == "alpha"
    assert "4 line(s) kept SILENT" in w[0]["msg"]
    assert "DUET" in w[0]["msg"]


def test_the_override_gets_its_own_louder_wording(tmp_path):
    clock = Clock()
    c = make_console(tmp_path, clock)
    report(c, "alpha", clock(), {"ok": False, "reason": "quota", "suppressed": 0,
                                 "failures": 9, "substitution_allowed": True})
    msg = voice_warnings(c, clock())[0]["msg"]
    assert "DIFFERENT VOICE" in msg and "CJ_ALLOW_VOICE_SUBSTITUTION" in msg


def test_a_healthy_voice_raises_nothing(tmp_path):
    clock = Clock()
    c = make_console(tmp_path, clock)
    report(c, "alpha", clock(), {"ok": True, "reason": None, "suppressed": 0,
                                 "failures": 0, "substitution_allowed": False})
    assert voice_warnings(c, clock()) == []


def test_an_older_build_without_the_field_reads_as_unknown_not_bad(tmp_path):
    """beta ran a build from before 2026-09-16 for a while; a missing field must
    never be rendered as a failing voice."""
    clock = Clock()
    c = make_console(tmp_path, clock)
    report(c, "alpha", clock(), None)
    assert voice_warnings(c, clock()) == []


def test_a_stale_report_does_not_keep_the_banner_up(tmp_path):
    """A robot that has stopped reporting is "unknown", and gets its own
    not-reporting warning — this one must not also assert its voice is bad."""
    clock = Clock()
    c = make_console(tmp_path, clock)
    report(c, "alpha", clock(), {"ok": False, "reason": "quota", "suppressed": 1,
                                 "failures": 1, "substitution_allowed": False})
    clock.advance(cs.OBS_FRESH_S + 5)
    assert voice_warnings(c, clock()) == []


def test_each_robot_is_named_separately(tmp_path):
    clock = Clock()
    c = make_console(tmp_path, clock)
    report(c, "beta", clock(), {"ok": False, "reason": "network", "engine": "fish",
                                "suppressed": 2, "failures": 2,
                                "substitution_allowed": False})
    w = voice_warnings(c, clock())
    assert len(w) == 1 and w[0]["robot"] == "beta"
    assert "Fish Audio" in w[0]["msg"] and "the robot cannot reach it" in w[0]["msg"]


def test_a_garbage_voice_field_is_ignored(tmp_path):
    clock = Clock()
    c = make_console(tmp_path, clock)
    report(c, "alpha", clock(), "not-a-dict")
    assert voice_warnings(c, clock()) == []


# ────────────────────────────────────────────────────────────────────────────
# 6. the chain itself — speech_engines.engine_order / tts_cloned_wav
# ────────────────────────────────────────────────────────────────────────────
import speech_engines as se  # noqa: E402


class FishError(Exception):
    def __init__(self, reason, detail=""):
        super().__init__(detail or reason)
        self.reason = reason


@pytest.fixture
def engines(monkeypatch, tmp_path):
    """Both clones configured, neither reachable: the test says what each one
    does. Returns the call log so order is assertable."""
    # voice/config.py refuses to import without these; the tests never reach
    # the network (see the _synth_with stub below), so placeholders are right.
    monkeypatch.setenv("ELEVEN_API_KEY", "test-key")
    monkeypatch.setenv("ELEVEN_VOICE_ID", "testvoiceid0")
    monkeypatch.setenv("FISH_API_KEY", "test-fish-key")
    monkeypatch.setenv("FISH_MODEL_ID", "testfishmodel")
    monkeypatch.setattr(se, "_engine_cooloff", {})
    monkeypatch.setattr(se, "_engine_reason", {})
    monkeypatch.setattr(vg, "primary_engine", lambda: se.engine_order()[0])
    calls = []
    behaviour = {}

    def fake(engine, text, out_dir, speed, eleven_kw):
        calls.append(engine)
        b = behaviour.get(engine)
        if isinstance(b, Exception):
            raise b
        return f"/dev/shm/{engine}.wav"

    monkeypatch.setattr(se, "_synth_with", fake)
    return type("E", (), {"calls": calls, "behaviour": behaviour})()


def test_engine_order_puts_fish_first_by_default(engines, monkeypatch):
    monkeypatch.delenv("CJ_TTS_ORDER", raising=False)
    assert se.engine_order() == ["fish", "elevenlabs"]


def test_engine_order_is_configurable(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "elevenlabs,fish")
    assert se.engine_order() == ["elevenlabs", "fish"]
    monkeypatch.setenv("CJ_TTS_ORDER", "elevenlabs")
    assert se.engine_order() == ["elevenlabs"]


def test_an_engine_with_no_credentials_is_not_broken_just_absent(engines, monkeypatch):
    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    assert se.engine_order() == ["fish"]


def test_the_primary_speaks_when_it_can(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    wav, engine = se.tts_cloned_wav("hello", where="answer")
    assert engine == "fish" and engines.calls == ["fish"]
    assert vg.state()["ok"] is True


def test_the_other_clone_takes_over_and_that_is_degraded(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    engines.behaviour["fish"] = FishError("quota", "http 402")
    wav, engine = se.tts_cloned_wav("hello", where="answer")
    assert engine == "elevenlabs" and engines.calls == ["fish", "elevenlabs"]
    s = vg.state()
    assert s["ok"] is False and s["standby"] == "elevenlabs" and s["engine"] == "fish"
    assert s["suppressed"] == 0          # nothing was silenced: he still spoke


def test_no_clone_at_all_raises_voice_unavailable(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    engines.behaviour["fish"] = FishError("quota")
    engines.behaviour["elevenlabs"] = SynthError("quota")
    with pytest.raises(se.VoiceUnavailable):
        se.tts_cloned_wav("hello", where="answer")
    assert vg.state()["suppressed"] == 1


def test_the_override_hands_the_caller_back_its_openai_path(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    monkeypatch.setenv("CJ_ALLOW_VOICE_SUBSTITUTION", "1")
    engines.behaviour["fish"] = FishError("quota")
    engines.behaviour["elevenlabs"] = SynthError("quota")
    assert se.tts_cloned_wav("hello", where="answer") == (None, None)


def test_a_quota_failure_cools_the_engine_off(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    engines.behaviour["fish"] = FishError("quota")
    se.tts_cloned_wav("one", where="answer")
    assert se.engine_cooloff_left("fish") > 0
    se.tts_cloned_wav("two", where="answer")
    # fish was tried once, not twice: no dead round-trip per sentence
    assert engines.calls == ["fish", "elevenlabs", "elevenlabs"]


def test_a_blip_is_never_cooled_off(engines, monkeypatch):
    """network/error really do self-heal — cooling them off would turn the
    guard into the circuit breaker it promises not to be."""
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    engines.behaviour["fish"] = FishError("network")
    se.tts_cloned_wav("one", where="answer")
    assert se.engine_cooloff_left("fish") == 0
    se.tts_cloned_wav("two", where="answer")
    assert engines.calls == ["fish", "elevenlabs", "fish", "elevenlabs"]


def test_a_cooled_off_primary_still_reports_the_real_reason(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    engines.behaviour["fish"] = FishError("quota")
    se.tts_cloned_wav("one", where="answer")
    vg.reset()
    se.tts_cloned_wav("two", where="answer")   # fish skipped, nothing raised
    assert vg.state()["reason"] == "quota"
    assert "quota or credit is used up" in vg.state()["message"]


def test_cooloff_never_silences_everything(engines, monkeypatch):
    """If the cool-off would skip every clone, it must be ignored — silence
    caused by bookkeeping rather than by a real failure would be a bug."""
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    engines.behaviour["fish"] = FishError("quota")
    engines.behaviour["elevenlabs"] = SynthError("quota")
    with pytest.raises(se.VoiceUnavailable):
        se.tts_cloned_wav("one", where="answer")
    assert se.engine_cooloff_left("fish") > 0
    assert se.engine_cooloff_left("elevenlabs") > 0
    engines.calls.clear()
    engines.behaviour.clear()                  # both healthy again
    wav, engine = se.tts_cloned_wav("two", where="answer")
    assert engine == "fish" and engines.calls == ["fish"]


def test_a_recovered_engine_leaves_its_cooloff_behind(engines, monkeypatch):
    monkeypatch.setenv("CJ_TTS_ORDER", "fish,elevenlabs")
    engines.behaviour["fish"] = FishError("quota")
    se.tts_cloned_wav("one", where="answer")
    engines.behaviour.clear()
    se._engine_cooloff.clear()                 # cool-off elapsed
    wav, engine = se.tts_cloned_wav("two", where="answer")
    assert engine == "fish" and se.engine_cooloff_left("fish") == 0


# ────────────────────────────────────────────────────────────────────────────
# 7. the /maintain engine card — ui_common.voice_engines / voice_engine_set
# ────────────────────────────────────────────────────────────────────────────
import ui_common as ui  # noqa: E402


@pytest.fixture
def card(monkeypatch):
    """The card's three inputs stubbed: ElevenLabs quota, Fish credit, and the
    robot's guard file. _env_set and _restart_app are ALWAYS stubbed — the real
    ones write app/.env and restart the live voice service."""
    env = {"CJ_TTS_ORDER": "fish,elevenlabs", "ELEVEN_API_KEY": "k",
           "FISH_API_KEY": "k", "FISH_MODEL_ID": "m"}
    written, restarts = {}, []
    monkeypatch.setattr(ui, "_env_value", lambda n: env.get(n))
    def _set(pairs):   # the real one returns only the keys that actually CHANGED
        changed = {k: v for k, v in pairs.items() if env.get(k) != v}
        written.update(changed)
        env.update(changed)
        return changed
    monkeypatch.setattr(ui, "_env_set", _set)
    monkeypatch.setattr(ui, "_restart_app", lambda: restarts.append(1))
    monkeypatch.setattr(ui, "_eleven_quota", lambda: {"tier": "pro", "character_count": 400,
                                                      "character_limit": 600000})
    monkeypatch.setattr(ui, "_fish_status", lambda: {"configured": True, "model_id": "m",
                                                     "key_hint": "…y01E", "credit": 50.0,
                                                     "model_name": "CJAP", "state": "trained",
                                                     "error": None})
    monkeypatch.setattr(ui, "voice_guard", lambda: None)
    return type("C", (), {"env": env, "written": written, "restarts": restarts})()


def test_the_card_reports_the_configured_order_and_both_engines(card):
    d = ui.voice_engines()
    assert d["order"] == ["fish", "elevenlabs"] and d["primary"] == "fish"
    assert d["engines"]["fish"]["ready"] is True
    assert "CJAP" in d["engines"]["fish"]["detail"]
    assert d["engines"]["elevenlabs"]["ready"] is True
    assert "599,600 chars left" in d["engines"]["elevenlabs"]["detail"]


def test_fish_with_no_credit_is_configured_but_not_ready(card, monkeypatch):
    monkeypatch.setattr(ui, "_fish_status", lambda: {"configured": True, "model_id": "m",
                                                     "key_hint": "", "credit": 0.0,
                                                     "model_name": "CJAP", "state": "trained",
                                                     "error": None})
    e = ui.voice_engines()["engines"]["fish"]
    assert e["configured"] is True and e["ready"] is False


def test_the_card_shows_what_actually_spoke(card, monkeypatch):
    """The whole point of the card: the engine NAMED in the config and the one
    actually SPEAKING can differ for a whole session."""
    monkeypatch.setattr(ui, "voice_guard", lambda: {"ok": False, "last_engine": "elevenlabs",
                                                    "last_engine_ts": 1.0, "standby": "elevenlabs"})
    d = ui.voice_engines()
    assert d["primary"] == "fish" and d["last_engine"] == "elevenlabs"   # the UI flags this


def test_setting_the_order_writes_it_and_restarts(card):
    ok, out = ui.voice_engine_set({"order": "elevenlabs,fish"})
    assert ok and card.written == {"CJ_TTS_ORDER": "elevenlabs,fish"}
    assert card.restarts == [1]
    assert "ElevenLabs, then Fish Audio" in out


def test_setting_the_same_order_changes_nothing_and_does_not_restart(card):
    ok, out = ui.voice_engine_set({"order": "fish,elevenlabs"})
    assert ok and "no change" in out and card.restarts == []


def test_an_unknown_order_is_refused(card):
    ok, out = ui.voice_engine_set({"order": "openai"})
    assert not ok and "pick one of" in out
    assert card.written == {} and card.restarts == []


def test_an_engine_without_credentials_cannot_be_selected(card, monkeypatch):
    monkeypatch.setattr(ui, "_fish_status", lambda: {"configured": False, "model_id": "",
                                                     "key_hint": "", "credit": None,
                                                     "model_name": None, "state": None,
                                                     "error": "no FISH_API_KEY"})
    ok, out = ui.voice_engine_set({"order": "fish,elevenlabs"})
    assert not ok and "no credentials" in out
    assert card.restarts == []


def test_choosing_a_primary_that_is_not_ready_warns_but_is_allowed(card, monkeypatch):
    """An operator may well set this up BEFORE topping up — but it must not
    look like it worked."""
    monkeypatch.setattr(ui, "_fish_status", lambda: {"configured": True, "model_id": "m",
                                                     "key_hint": "", "credit": 0.0,
                                                     "model_name": "CJAP", "state": "trained",
                                                     "error": None})
    card.env["CJ_TTS_ORDER"] = "elevenlabs,fish"
    ok, out = ui.voice_engine_set({"order": "fish,elevenlabs"})
    assert ok and "not ready" in out
    assert "fall through to ElevenLabs" in out


def test_a_lone_unready_engine_warns_that_nothing_will_be_spoken(card, monkeypatch):
    monkeypatch.setattr(ui, "_fish_status", lambda: {"configured": True, "model_id": "m",
                                                     "key_hint": "", "credit": 0.0,
                                                     "model_name": "CJAP", "state": "trained",
                                                     "error": None})
    ok, out = ui.voice_engine_set({"order": "fish"})
    assert ok and "nothing will be spoken" in out


# ────────────────────────────────────────────────────────────────────────────
# 8. boot — tmpfs outlives a service restart
# ────────────────────────────────────────────────────────────────────────────
def test_boot_clears_a_banner_left_by_the_previous_run():
    """2026-09-16: /maintain still read "Fish Audio is failing" eleven minutes
    after the credit was topped up and the app restarted, because /dev/shm
    survives a service restart and nothing had spoken since to overwrite it."""
    vg.blocked(SynthError("quota"), where="answer", engine="fish")
    assert json.loads(Path(vg.STATE_PATH).read_text())["ok"] is False
    vg.boot()
    d = json.loads(Path(vg.STATE_PATH).read_text())
    assert d["ok"] is True and d["message"] == ""
    assert d["suppressed"] == 0 and d["standby"] is None and d["last_engine"] is None


def test_boot_publishes_even_with_no_previous_file(tmp_path, monkeypatch):
    monkeypatch.setattr(vg, "STATE_PATH", str(tmp_path / "fresh.json"))
    vg.boot()
    assert json.loads(Path(vg.STATE_PATH).read_text())["ok"] is True


def test_boot_never_raises_on_an_unwritable_path(monkeypatch):
    monkeypatch.setattr(vg, "STATE_PATH", "/nonexistent-dir/guard.json")
    vg.boot()          # must not raise: it runs on the robot's startup path
    assert vg.state()["ok"] is True
