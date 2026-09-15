"""Interrupt (MUTE_TRIGGER) freshness (2026-09-15).

An Interrupt pressed while nothing was playing or listening stayed on disk and
abandoned the next visitor's question 23 minutes later, right after the wake
word. A fresh press still cuts; a stale one is dropped.
"""
from __future__ import annotations

import os
import sys
import time

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
sys.path.insert(0, APP)
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
import main_voice_robot as mvr  # noqa: E402


def test_a_fresh_interrupt_counts_once_and_a_stale_one_is_dropped(monkeypatch, tmp_path):
    f = tmp_path / "cj_mute_trigger"
    monkeypatch.setattr(mvr, "MUTE_TRIGGER", str(f))
    monkeypatch.delenv("CJ_INTERRUPT_MAX_AGE_S", raising=False)
    assert mvr._interrupt_pending() is False                 # nothing pressed
    f.touch()
    assert mvr._interrupt_pending() is True and not f.exists()
    assert mvr._interrupt_pending() is False                 # consumed: counts once
    f.touch()
    old = time.time() - 1380                                  # beta, 2026-09-15: 23 minutes
    os.utime(f, (old, old))
    assert mvr._interrupt_pending() is False and not f.exists()


def test_no_reader_checks_the_trigger_without_its_age():
    src = open(os.path.join(APP, "main_voice_robot.py")).read()
    assert "os.path.exists(MUTE_TRIGGER)" not in src
    assert src.count("_interrupt_pending()") >= 3
