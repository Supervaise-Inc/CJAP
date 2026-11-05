"""scripts/turn_timing.py: [trace] journal lines -> per-stage timing (2026-11-05).

What is asserted: a real-shaped journal line parses (timestamp prefix, "-" as
None, numbers with an s suffix, booleans); derived stages are computed only
when their inputs exist; non-streamed and non-trace lines are skipped; the
summary statistics are right; the endpoint silence is added to the perceived
time; and two reports compare side by side.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import turn_timing as tt  # noqa: E402

L1 = ("2026-11-05T10:12:01+0800 reachy-cjap python3[812]: [trace] path=streamed | stt_s=1.30s | "
      "compose_s=6.80s | first_audio_s=3.90s | on_air_s=5.20s | audio_s=14.10s | words=58 | "
      "topic=judicial_reform | interrupted=False")
L2 = ("2026-11-05T10:13:30+0800 reachy-cjap python3[812]: [trace] path=streamed | stt_s=1.10s | "
      "compose_s=5.00s | first_audio_s=3.10s | on_air_s=3.10s | audio_s=9.00s | words=40 | "
      "topic=elections_and_automated_voting | interrupted=False")
CANNED = ("2026-11-05T10:14:00+0800 reachy-cjap python3[812]: [trace] path=canned | stt_s=0.90s | "
          "compose_s=- | first_audio_s=- | on_air_s=- | topic=canned:greeting")
NOISE = "2026-11-05T10:14:01+0800 reachy-cjap python3[812]: [stream] first audio 5.2s after transcript"


def test_parse_line_reads_every_field():
    r = tt.parse_line(L1)
    assert r["when"].startswith("2026-11-05T10:12:01")
    assert r["path"] == "streamed" and r["stt_s"] == 1.30 and r["on_air_s"] == 5.20
    assert r["words"] == 58.0 and r["interrupted"] is False
    assert r["topic"] == "judicial_reform"


def test_dash_is_none_and_non_trace_lines_are_skipped():
    r = tt.parse_line(CANNED)
    assert r["compose_s"] is None and r["topic"] == "canned:greeting"
    assert tt.parse_line(NOISE) is None
    assert tt.parse_line("") is None


def test_derived_stages_need_their_inputs():
    d = tt.derive(tt.parse_line(L1))
    assert d["filler_wait_s"] == 1.30            # 5.20 - 3.90
    assert d["heard_to_sound_s"] == 6.50         # 1.30 + 5.20
    c = tt.derive(tt.parse_line(CANNED))
    assert "filler_wait_s" not in c and "heard_to_sound_s" not in c


def test_endpoint_silence_is_added_to_perceived_time():
    d = tt.derive(tt.parse_line(L1), endpoint_s=1.2)
    assert d["heard_to_sound_s"] == 7.70


def test_build_keeps_only_the_requested_path_and_summarises():
    rep = tt.build([L1, L2, CANNED, NOISE], label="alpha")
    assert rep["n"] == 2 and rep["lines_seen"] == 3
    s = rep["summary"]["on_air_s"]
    assert s["n"] == 2 and s["median"] == 4.15 and s["min"] == 3.10 and s["max"] == 5.20
    assert tt.build([L1, L2, CANNED], path="all")["n"] == 3
    assert "filler_wait_s" in rep["summary"]


def test_p90_interpolates():
    assert tt._pct([1, 2, 3, 4, 5], 0.9) == 4.6
    assert tt._pct([7], 0.9) == 7


def test_empty_input_reports_cleanly():
    rep = tt.build([NOISE])
    assert rep["n"] == 0 and "no turns" in tt.format_report(rep)


def test_compare_shows_delta_between_robots():
    a = tt.build([L1, L2], label="alpha")
    b = tt.build([L2, L2], label="beta")
    out = tt.compare(a, b)
    assert "alpha med" in out and "beta med" in out
    row = [l for l in out.splitlines() if l.startswith("on_air_s")][0]
    assert "-1.05" in row                          # 3.10 - 4.15


def test_cli_writes_json_and_csv(tmp_path, capsys):
    src = tmp_path / "t.txt"
    src.write_text("\n".join([L1, L2, NOISE]), encoding="utf-8")
    j, c = tmp_path / "r.json", tmp_path / "r.csv"
    assert tt.main([str(src), "--label", "alpha", "--json", str(j), "--csv", str(c)]) == 0
    assert "alpha: 2 turn(s)" in capsys.readouterr().out
    assert j.exists() and "on_air_s" in c.read_text(encoding="utf-8").splitlines()[0]
