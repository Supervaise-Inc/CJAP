# deploy/spark: CJAP on a DGX Spark with a Reachy Mini Lite

Branch `spark/local-speech` (2026-11-05), off `merge/master-single-robot` @ `1d986be`.
The same app as alpha, moved from the robot's Pi onto an NVIDIA DGX Spark
(`gx10-c1f6`, GB10, aarch64, Ubuntu 24.04, user `sv`), with a **Reachy Mini
Lite** on the Spark's USB-C. Speech moves onto the Spark:

| | alpha (Pi) | Spark |
|---|---|---|
| STT | OpenAI `gpt-4o-mini-transcribe` | the Spark's whisper-api (`whisper`, large-v3-turbo) through LiteLLM, same OpenAI client (`OPENAI_BASE_URL`) |
| Panganiban's voice | Fish Audio clone (`CJ_TTS_ORDER=fish`) | **Qwen3-TTS clone** on the Spark GPU, engine `spark` (`voice/qwen.py`, container `cjap-tts`), `CJ_TTS_ORDER=spark` |
| Claude | Haiku 4.5 + Sonnet 4.6 | unchanged |
| Reachy daemon | on the Pi, :8000 | `reachy-daemon.service` on the Spark, `--no-media --fastapi-port 8010` (8000 is taken on this host) |
| Dashboard / console | :8080 / :8443 | **:8180 / :8543** (`CJ_DASH_PORT`, `CJ_DASH_HTTPS_PORT`; 8080/8443 are taken) |
| Machine map | `config/robots.json` | `deploy/spark/robots.json` via `CJ_ROBOTS_JSON` (this host is alpha and the authority) |

The full plan and the step-by-step runbook are in the DGX Spark docs
(`CJAP_SPARK_ARCHITECTURE.md`, `CJAP_SPARK_RUNBOOK.md`, also under `docs/spark/`).

## Code changes on this branch (all default-off for alpha)

| File | Change |
|---|---|
| `voice/qwen.py` | New: client for `cjap-tts`, the same contract as `voice/fish.py` |
| `app/speech_engines.py` | Engine `spark` in `engine_order()` / `_synth_with()`, `tts_spark_wav()`; a JSON-wrapped transcript from LiteLLM is unwrapped |
| `app/voice_guard.py` | Label for `spark` |
| `voice/config.py` | ElevenLabs credentials required only while `CJ_TTS_ORDER` lists `elevenlabs` (default `fish,elevenlabs`: alpha unchanged) |
| `app/main_voice_robot.py` | `CJ_REACHY_PORT` (unset = SDK default, as before) |
| `app/floor_lease.py`, `dashboard/console.py` | `CJ_ROBOTS_JSON` (unset = `config/robots.json`) |
| `dashboard/ui_server.py` | `CJ_DASH_PORT`, `CJ_DASH_HTTPS_PORT` (unset = 8080 / 8443) |
| `tests/test_spark_voice.py` | Tests for all of the above |

## What is here and where it goes on the Spark

| In this folder | Goes to | What it is |
|---|---|---|
| `systemd/supervaise.service`, `reachy-daemon.service`, `pi-dashboard.service`, `cjap-whisper-keepalive.service` | `/etc/systemd/system/` | Not enabled at boot: `~/bin/sv-robot on` starts them |
| `systemd/supervaise.service.d/wakeword.conf` | `/etc/systemd/system/supervaise.service.d/` | alpha's 48 settings with Spark paths, STT on whisper, no Bluetooth AEC feed, plus the Spark block. `dashboard/console.py` reads this file, so Spark settings live here |
| `home/.asoundrc`, `home/.asoundrc.route` | `~/` | alpha's ALSA names over the Lite's USB card, PipeWire playback |
| `bin/sv-robot` | `~/bin/` | `on` / `off` / `status`: robot mode vs the office LLM split |
| `bin/whisper-keepalive`, `bin/cjap-env-set` | `~/bin/` | Keep whisper loaded; set `app/.env` lines without echoing secrets |
| `tts/` | built in place | `Dockerfile.tts` (`FROM sv/whisper:1`), `tts_server.py`, `make_ref.py` (reference clip from the filler clips). `constraints.txt` is written by the runbook from the base image |
| `compose/docker-compose.yml` | run in place | Project `sv-robot`, service `cjap-tts` on 127.0.0.1:8091 |
| `robots.json` | read in place | `CJ_ROBOTS_JSON` points here |

Also needed from `deploy/alpha/`: `home/bin/{xvf-ctl,audio-out,audio-volume,aplay-dual,verify-mic.sh}`
(paths changed `/home/pollen` → `/home/sv`, `python3.13` → `python3.12`, `/run/user/1000` → `/run/user/1001`),
`home/{fillers,fillers_ack,fillers_bail}`, `home/speaker_id/*.onnx`.

## Not used on the Spark

`audio-hub`, `bt-keepalive`, `wifi-fallback`, `speaker-watchdog`, the Bluetooth AEC reference
feed, LiveAvatar. The dashboard's service/reboot buttons use `sudo -n`; `sv` has no NOPASSWD rule,
so they report a failure (use `sv-robot` instead).
