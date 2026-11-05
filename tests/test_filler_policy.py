"""app/filler_policy.py: when and what the "thinking" filler plays (2026-11-05).

The answer used to sit behind a 2.6-5.2 s filler clip it could not cut. What is
asserted: short clips replace the long set when they exist; the first clip of a
turn is the shortest; CJ_FILLER_MAX_CLIP_S keeps short clips only when there are
any; recently heard clips are skipped; and no new clip starts once the first
composer token is in, but clips resume if the answer is still not on air after
the quiet limit.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import filler_policy as fp  # noqa: E402

DUR = {"a": 4.0, "b": 2.6, "c": 5.2, "s1": 1.0, "s2": 1.2}


def _dur(c):
    return DUR[c]


def _touch(d, names):
    d.mkdir(parents=True, exist_ok=True)
    for n in names:
        (d / n).write_bytes(b"")


def test_short_clips_replace_the_long_set_when_present(tmp_path):
    long_, short = tmp_path / "fillers", tmp_path / "short"
    _touch(long_, ["01.wav", "02.wav"])
    _touch(short, ["s1.wav", "s2.wav"])
    got = fp.load_clips(str(long_), env={"CJ_FILLER_SHORT_DIR": str(short)})
    assert [os.path.basename(c) for c in got] == ["s1.wav", "s2.wav"]


def test_long_set_is_used_when_there_are_no_short_clips(tmp_path):
    long_ = tmp_path / "fillers"
    _touch(long_, ["01.wav", "02.wav"])
    got = fp.load_clips(str(long_), env={"CJ_FILLER_SHORT_DIR": str(tmp_path / "none")})
    assert sorted(os.path.basename(c) for c in got) == ["01.wav", "02.wav"]


def test_first_clip_is_the_shortest():
    pool = fp.build_pool(["a", "b", "c"], recent=(), duration_fn=_dur, first=True,
                         max_clip_s=0, rng=random.Random(1))
    assert pool.pop() == "b"                      # pop() takes the last: shortest


def test_recent_clips_are_skipped_but_never_empty_the_pool():
    pool = fp.build_pool(["a", "b", "c"], recent={"a", "b"}, duration_fn=_dur, first=False,
                         max_clip_s=0, rng=random.Random(1))
    assert pool == ["c"]
    pool = fp.build_pool(["a", "b"], recent={"a", "b"}, duration_fn=_dur, first=False,
                         max_clip_s=0, rng=random.Random(1))
    assert sorted(pool) == ["a", "b"]


def test_max_clip_length_keeps_short_clips_when_any_exist():
    pool = fp.build_pool(["a", "b", "c", "s1"], recent=(), duration_fn=_dur, first=False,
                         max_clip_s=1.5, rng=random.Random(1))
    assert pool == ["s1"]
    pool = fp.build_pool(["a", "b", "c"], recent=(), duration_fn=_dur, first=True,
                         max_clip_s=1.5, rng=random.Random(1))
    assert sorted(pool) == ["a", "b", "c"] and pool[-1] == "b"   # nothing short: shortest first


def test_max_clip_length_reads_the_environment(monkeypatch):
    monkeypatch.setenv("CJ_FILLER_MAX_CLIP_S", "1.5")
    pool = fp.build_pool(["a", "s1", "s2"], recent=(), duration_fn=_dur, first=False,
                         rng=random.Random(1))
    assert sorted(pool) == ["s1", "s2"]


def test_no_quiet_before_the_first_token():
    assert fp.stay_quiet(None, now=100.0) is False


def test_quiet_after_the_first_token_then_clips_resume(monkeypatch):
    monkeypatch.delenv("CJ_FILLER_TOKEN_QUIET_MAX_S", raising=False)
    assert fp.stay_quiet(100.0, now=100.5) is True      # answer expected shortly
    assert fp.stay_quiet(100.0, now=102.4) is True
    assert fp.stay_quiet(100.0, now=102.6) is False     # still not on air: allow a clip


def test_quiet_limit_is_configurable(monkeypatch):
    monkeypatch.setenv("CJ_FILLER_TOKEN_QUIET_MAX_S", "5")
    assert fp.stay_quiet(100.0, now=104.0) is True
    monkeypatch.setenv("CJ_FILLER_TOKEN_QUIET_MAX_S", "0")
    assert fp.stay_quiet(100.0, now=100.0) is False


def test_bad_environment_values_fall_back(monkeypatch):
    monkeypatch.setenv("CJ_FILLER_TOKEN_QUIET_MAX_S", "soon")
    assert fp.stay_quiet(100.0, now=102.0) is True       # default 2.5 s
