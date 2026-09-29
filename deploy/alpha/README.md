# deploy/alpha: everything alpha runs that is not in the app code

These files were captured from **alpha** (`reachy-cjap`, Reachy Mini Wireless,
ReachyMiniOS v0.2.3, Debian 13, Python 3.13.5) on **2026-09-29**, when the
machine was handed over. At that point alpha was running commit `d465215`
(knowledge base v2), which is on both `master` and `feat/operator-console`.

Before this folder existed, a fresh machine could not reproduce alpha from git:
the tuning, the audio routing, the service files and the filler clips all lived
only on the Pi. This folder is a **snapshot for restoring**, not the live copy.
The machine reads its files from the paths in the table below. Edit those, then
re-capture them here.

## What is here and where it goes

| In this folder | Goes to on the robot | What it is |
|---|---|---|
| `systemd/supervaise.service` | `/etc/systemd/system/` | The voice robot (`app/main_voice_robot.py --wake`) |
| `systemd/supervaise.service.d/wakeword.conf` | `/etc/systemd/system/supervaise.service.d/` | **~250 lines of tuning** (48 `Environment=` settings plus comments): name pronunciation (`CJ_NAME_PIN_*`), echo-cancellation feed (`CJ_AEC_REF_*`, delay 444 ms), rear-facing beams (`CJ_LISTEN_DIRECTION=back`), `MALLOC_ARENA_MAX=2`. Root-owned. |
| `systemd/pi-dashboard.service` | `/etc/systemd/system/` | The port-8080 dashboard and `/console` (the floor-lease authority) |
| `systemd/audio-hub.service` | `/etc/systemd/system/` | Prefers a USB-hub mic and speaker (`scripts/audio_hub.py`) |
| `systemd/bt-keepalive.service` + `.d/interval.conf` | `/etc/systemd/system/` | Keeps a Bluetooth speaker awake (pulse every 150 s) |
| `systemd/wifi-fallback.service` | `/etc/systemd/system/` | Setup hotspot `ReachyMini-Setup` when no known Wi-Fi is found |
| `systemd/speaker-watchdog.service` | `/etc/systemd/system/` | **Keep disabled.** It moves audio onto any paired Bluetooth speaker. |
| `systemd/user@.service.d/99-reachy-rtprio.conf` | `/etc/systemd/system/user@.service.d/` | Real-time audio priority limits |
| `home/bin/*` | `~/bin/` | `audio-out` (output route: internal / dac / bluetooth), `audio-volume`, `aplay-dual`, `xvf-ctl` (mic-array chip), `verify.sh`, `verify-mic.sh`, snapshot helpers. The dashboard calls several of these. |
| `home/tools/*` | `~/tools/` | `aec_ref_calib.py`: **run at the venue** if a USB speaker (DAC) is used, to set `CJ_AEC_REF_DELAY_DAC_MS`. Also `barge_in_sweep.py` and pronunciation A/B tools. |
| `home/audio-ui.py`, `home/bt-keepalive.sh`, `home/speaker-watchdog.sh`, `home/verify_boot.sh`, `home/switch_voice.sh` | `~/` | Called by the dashboard or by the services above |
| `home/gen_fillers.py`, `home/gen_voice_wavs_eleven.py` | `~/` | How the filler clips were generated |
| `home/.asoundrc`, `home/.asoundrc.route` | `~/` | ALSA routing. `audio-out` rewrites `.asoundrc.route`. `.asoundrc.inroute` is created by `audio-hub` only when a USB mic is present. |
| `home/fillers/`, `home/fillers_ack/`, `home/fillers_bail/` | `~/` | Pre-recorded "thinking", acknowledgement and fallback lines in the **ElevenLabs** clone voice. They cannot be regenerated identically. |
| `home/videos/` | `~/videos/` | The clips for the dashboard's video card |
| `home/speaker_id/3dspeaker_…onnx` | `~/speaker_id/` | Public speaker-embedding model used by the voice lock. **No enrolled voiceprints are included.** |
| `dashboard-assets/` | `dashboard/assets/` | Cached avatar portrait and metadata. Copy `liveavatar.json.example` to `liveavatar.json` and add the key. |
| `state/console_state.json` | `~/.cj_console_state.json` | Console state at handover: alpha plays Panganiban, mode `direct`, profile `kiosk`, wake threshold 0.5 |

## Not included, on purpose

| Missing | Why | How to get it back |
|---|---|---|
| `app/.env` | API keys | Copy `app/.env.example` and fill in `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ELEVEN_API_KEY`, `FISH_API_KEY`. The other values in it are alpha's. |
| `dashboard/assets/liveavatar.json` | API key | From `dashboard-assets/liveavatar.json.example`. The custom avatar needs the key of the account that owns it, and production mode (`sandbox: false`). |
| `dashboard/certs/` | TLS private key | Self-signed, so generate a new pair |
| `~/.voice_cache/` (521 MB) | Regenerable cache of synthesised sentences | Fills itself as the robot speaks |
| `data/prerendered/**/*.wav` | Kept out of git by design | `scripts/render_duet.py` and `scripts/render_intro.py` (ElevenLabs) |
| `~/wake_real_20260901/`, `~/speaker_id/enrolled.npz` | Recordings and voiceprints of real people | Re-record and re-enrol on site |
| `~/backups/`, `~/CJAP/`, `~/gitwork/` | Old checkpoints and clones of other repositories | Not needed |

## Restoring onto a fresh Reachy Mini

```bash
cd ~ && git clone -b master https://github.com/Supervaise-Inc/CJAP.git Supervaise-Reachy-Mini-Project-main
cd Supervaise-Reachy-Mini-Project-main
python3 -m venv app/.venv && app/.venv/bin/pip install -r app/requirements.txt
cp app/.env.example app/.env        # then add the four keys
ln -s ~/Supervaise-Reachy-Mini-Project-main/dashboard ~/pi_dashboard

A=deploy/alpha
sudo cp $A/systemd/*.service /etc/systemd/system/
sudo mkdir -p /etc/systemd/system/{supervaise,bt-keepalive}.service.d /etc/systemd/system/user@.service.d
sudo cp $A/systemd/supervaise.service.d/wakeword.conf /etc/systemd/system/supervaise.service.d/
sudo cp $A/systemd/bt-keepalive.service.d/interval.conf /etc/systemd/system/bt-keepalive.service.d/
sudo cp $A/systemd/user@.service.d/99-reachy-rtprio.conf /etc/systemd/system/user@.service.d/
mkdir -p ~/bin ~/tools ~/speaker_id
cp $A/home/bin/* ~/bin/ && cp -r $A/home/tools/* ~/tools/
cp -r $A/home/{fillers,fillers_ack,fillers_bail,videos} ~/
cp $A/home/{audio-ui.py,bt-keepalive.sh,speaker-watchdog.sh,verify_boot.sh,switch_voice.sh,.asoundrc,.asoundrc.route} ~/
cp $A/home/speaker_id/*.onnx ~/speaker_id/
cp $A/dashboard-assets/{portrait.jpg,portrait.json,liveavatar_avatar.json} dashboard/assets/

sudo systemctl daemon-reload
sudo systemctl enable --now supervaise pi-dashboard audio-hub bt-keepalive wifi-fallback
sudo systemctl disable --now speaker-watchdog     # keep it off
app/.venv/bin/python -m pytest tests/             # 396 passing at handover
```

Then open `http://<robot>:8080/console`. The floor must be granted to `alpha`
for the microphone to open (it fails closed), and the mode must be `direct`
for visitors to ask questions. The operating procedure is in
[`docs/EVENT_RUNBOOK.md`](../../docs/EVENT_RUNBOOK.md) and
[`docs/PRE_EVENT_CHECKLIST.md`](../../docs/PRE_EVENT_CHECKLIST.md).

**A second robot (beta)** uses the same files. Its role comes from
`CJ_ROBOT_ROLE` or, failing that, the hostname (`app/floor_lease.py`), and it
must reach alpha's console. Beta was not updated to knowledge base v2 at
handover.

## Written notes

`docs/handover-notes/` holds the Word documents kept in alpha's home folder
(event runbook, system reference, audit report, avatar, display and Wi-Fi
notes, improvements) and `PROJECT_NOTES.txt`. They are dated working notes.
Where they disagree with the code or with `CLAUDE.md`, the code wins.
