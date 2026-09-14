# LL-013: A green test suite that was reading the machine instead of a fixture

* Date: 2026-09-14
* Severity: medium (one test was asserting against a broken state and passing)
* Related: [LL-003](LL-003-dotenv-override-false.md),
  `tests/test_breath_motion.py`, `tests/test_dashboard_ui.py`,
  `tests/test_wifi_control.py`, `tests/test_canned_answers.py`

## Symptom

`tests/test_breath_motion.py::test_envelope_is_disabled_at_zero_degrees` passed
for weeks and then failed the moment an unrelated feature created a file:

```
monkeypatch.setattr(mvr, "ENV_DEG", 0.0)
assert g.breath_offset(2.0) == _g().breath_offset(2.0)
E  assert 2.3508878776... == 2.3895627311...
```

## Cause

`_motion_val(key, default)` reads `/dev/shm/cj_motion.json` and falls back to
the module default **only when that file is absent**. The test monkeypatched
the module default — a value the code never consults while the file exists.

The file did not exist on this machine, so the test had always taken the
fallback path and passed. On 2026-09-14 the dashboard gained a startup mirror
that writes the versioned config into `/dev/shm`, the file appeared, and the
test started reading the machine's live tuning instead of its own fixture.

**The test was green because the config was missing.** Had anyone tuned the
motion sliders before running the suite, it would have failed then, for the
same reason, and looked like a regression in the code under test.

## The wider sweep

Prompted by the above, the whole suite was checked. Three empirical results:

| Check | Result |
|---|---|
| every file in isolation vs. the full suite | 253 = 253 — no order dependence manifests |
| full suite with all 44 live `CJ_*` service variables injected | 253 pass |
| assertion density | 475 asserts across 143 functions, mean 3.3, none empty |

So the suite is substantially better than the one failure suggested. 253
collected cases come from **143 distinct functions** — parametrisation accounts
for the rest, mostly `test_premise_gate` (9 → 76) and `test_floor_lease`
(43 → 86).

Four isolation defects were found. Two are fixed; three of the remaining are
logged here because they are latent rather than active.

**Fixed 2026-09-14:**

1. `test_breath_motion.py` — an autouse fixture now stubs `mvr._motion` to
   `{}`, so the tests assert on the code and never on the machine's tuning.
2. `test_dashboard_ui.py:18` and `test_wifi_control.py:19` imported the
   dashboard through `~/pi_dashboard`. That symlink points into the repo on
   alpha, but on beta it was a **stale directory holding an older copy** until
   2026-09-14 — so on that machine the tests were validating code that was not
   the code being deployed, and passing. They now import from
   `Path(__file__).parent.parent / "dashboard"`.

**Logged, not yet fixed:**

3. `test_canned_answers.py:9` sets `os.environ["CJ_CANNED_ENABLED"] = "1"` at
   import and never restores it; lines 156 and 159 toggle it again. It leaks
   into every test that runs afterwards in the same process. Nothing currently
   asserts the opposite, so it is latent.
4. `test_intro_rotation.py:71` sets `CJ_WAKE_LISTEN = "1"` with no restore.
   Same shape.
5. `test_canned_answers.py` runs roughly twenty `check()` calls at import time
   and collapses them into a single `assert FAIL == 0`. pytest reports one
   test; a failure names none of the twenty.

## The general lesson

A test that reads live state does not fail — it *drifts*, and it is green
exactly when the machine happens to agree with it. The breath case is the
sharp version: it was green **because** the thing it depended on was missing.

Two rules follow, and they are cheap:

* A test must never read `/dev/shm`, `$HOME`, the systemd environment, or a
  path that resolves through a symlink into a deployed tree. Point at the repo,
  or at a fixture.
* When code reads a live file with a fallback, the test must stub the *reader*,
  not the fallback. Monkeypatching a default proves nothing while the file that
  shadows it exists.
