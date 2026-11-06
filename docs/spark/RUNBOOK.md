# Runbook: CJAP on the DGX Spark with a Reachy Mini Lite (user `sv`)

> **For:** you, as `sv`, over `ssh isl.spark` from your Windows laptop, plus a few **owner steps** that need your sudo password (marked 🔑). **Design:** [`CJAP_SPARK_ARCHITECTURE.md`](ARCHITECTURE.md).
> **Starts from** the box as probed on **2026-11-05**: Qwen on vLLM (split `qwen=50`), nginx/LiteLLM/whisper-api up, no CJAP, no Reachy, no sound card.
> **What you get:** CJAP (branch **`spark/local-speech`**) running on the Spark as `supervaise`, its dashboard on **:8180**, the Reachy Mini Lite on USB-C, speech-to-text on the Spark's whisper-api, Panganiban's voice from a **Qwen3-TTS clone** on the GPU, and `sv-robot on|off` to switch between robot mode and the office LLM API.
> **How to use:** run the blocks of **steps 0–9 in order**, top to bottom, each block as a whole, and compare with **✅ Expect**. A block that is only `sudo -v` asks for your password **before** the next block, so the prompt can't swallow pasted lines; type the password, then paste the next block. When the output doesn't match, stop and look up the named row in **step 11**. The fixes are there and nowhere else. Steps 10–12 are tables.
> **Outages:** step 8 (`sv-robot on`) stops Qwen: teammates' `qwen38` calls fail until step 9 (`sv-robot off`). Nothing else touches the chat engines.
> **The code** is on the CJAP branch `spark/local-speech`, four commits on top of `merge/master-single-robot` @ `1d986be`. Until someone with push rights publishes it, it travels as a git bundle (`cjap-spark/cjap-spark-local-speech.bundle` next to this runbook).

| Step | What | Where | Time |
|---|---|---|---|
| 0 | Check the box (read only) | sv | 2 min |
| 1 | CJAP + the Spark branch | laptop + sv | 5 min |
| 2 | 🔑 Packages, USB rules, groups, units | sv (sudo) | 10 min |
| 3 | Python venv, Gate P (tests) | sv | 10–20 min |
| 4 | Plug in the Lite, audio files, Gate A (speaker + mic) | sv + robot | 15 min |
| 5 | Reachy daemon, Gate R (motion) | sv + robot | 5 min |
| 6 | Keys, Gate W (Whisper) | sv | 10 min |
| 7 | The voice: image, model, reference clip from the real recording, Gate T (speed), Gate V (listen) | sv + laptop | 45–70 min |
| 8 | Robot mode, the console, Gate E (live turns), Gate L (latency) | sv + robot + laptop | 30 min |
| 9 | Back to office mode, Gate O | sv | 5 min |
| 10 | Daily use | | |
| 11 | Incidents | | |
| 12 | Teardown | | |

---

## 0. Check the box

On the **laptop** (PowerShell), open a tmux session on the Spark. `-L cjap` gives this runbook its own tmux server, so it can be restarted in step 2 without touching anyone else's sessions:
```powershell
ssh isl.spark -t "tmux -L cjap new -As cjap"
```
On the **Spark** (read only):
```bash
docker ps --format '{{.Names}} {{.Status}}'
free -g | sed -n 2p
df -h / | tail -1
ls -d ~/Supervaise-Reachy-Mini-Project-main 2>&1
ss -tln | grep -E ':(8010|8091|8180|8543) ' || echo ports-free
docker image ls sv/whisper:1 --format '{{.Repository}}:{{.Tag}}'
ls ~/models
id
```
✅ Expect:
- `sv-llm-vllm-1 Up … (healthy)`, `sv-llm-whisper-api-1 Up … (healthy)`, plus `litellm`, `nginx`, `postgres` up;
- a `Mem:` line with **≥ 40** in the last (available) column;
- `/` with ≥ 100G free;
- `… No such file or directory` for the CJAP folder (not installed yet);
- `ports-free`;
- `sv/whisper:1`;
- your model folders (no `Qwen3-TTS…` yet);
- `uid=1001(sv)` with groups `sudo`, `docker` (no `dialout` yet: step 2 adds it).

**Also, once:** the 2026-11-05 probe printed the vLLM `--api-key` through `docker inspect`. Rotate it when convenient (it's independent of this runbook).

---

## 1. CJAP + the Spark branch

On the **laptop** (PowerShell, one line at a time):
```powershell
cd ~/Downloads/SV/DGXSpark
scp cjap-spark/cjap-spark-local-speech.bundle isl.spark:
```
✅ Expect: one line, `cjap-spark-local-speech.bundle 100% …`.

On the **Spark**:
```bash
cd ~
R=https://github.com/Supervaise-Inc/CJAP.git
B=merge/master-single-robot
D=Supervaise-Reachy-Mini-Project-main
git clone --filter=blob:none --single-branch -b $B $R $D
cd ~/$D
git bundle verify ~/cjap-spark-local-speech.bundle
git fetch ~/cjap-spark-local-speech.bundle spark/local-speech:spark/local-speech
git checkout spark/local-speech
git log --oneline -3
```
✅ Expect:
- the clone finishes (about 120 MB, the knowledge base and audio clips included);
- `The bundle requires this ref: 1d986be…` and `… is okay`;
- `Switched to branch 'spark/local-speech'`;
- the log starts with `Spark: …` (one or two commits) then `1d986be Filler: no new clip once the answer is coming…`.

The folder name `Supervaise-Reachy-Mini-Project-main` is deliberate: CJAP's dashboard and alpha's scripts use that path.

If the branch has already been pushed to GitHub: instead of the bundle lines, `git fetch origin spark/local-speech:spark/local-speech` (step 11, *Branch on GitHub*).

---

## 2. 🔑 Packages, USB rules, groups, units

**Owner step: needs your sudo password.** All of it runs once.

```bash
sudo -v
```

```bash
cd ~/Supervaise-Reachy-Mini-Project-main
sudo apt-get update
sudo apt-get install -y libportaudio2 pulseaudio-utils alsa-utils ffmpeg
sudo apt-get install -y libasound2-plugins
sudo apt-get install -y build-essential pkg-config python3-dev
sudo apt-get install -y libgirepository1.0-dev libgirepository-2.0-dev
sudo apt-get install -y libcairo2-dev
sudo apt-get install -y gir1.2-glib-2.0 gir1.2-gstreamer-1.0
sudo apt-get install -y gir1.2-gst-plugins-base-1.0 gstreamer1.0-alsa
```
What they are for: PortAudio (CJAP's `sounddevice`), `pactl` (audio routing), `ffmpeg` (the dashboard), the ALSA `pulse` plugin (`~/.asoundrc` plays through PipeWire); a compiler and the GObject headers so `pip` can build **PyGObject**, which the Reachy SDK imports even with media off; the GStreamer typelibs the SDK, the daemon and CJAP's GStreamer player load.

```bash
cd ~/Supervaise-Reachy-Mini-Project-main
S=deploy/spark
sudo install -m 644 $S/udev/99-reachy-mini.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb --subsystem-match=tty
sudo usermod -aG dialout,plugdev,audio sv
sudo loginctl enable-linger sv
sudo systemctl restart user@1001.service
sudo install -m 644 $S/systemd/*.service /etc/systemd/system/
W=/etc/systemd/system/supervaise.service.d
sudo mkdir -p $W
sudo install -m 644 $S/systemd/supervaise.service.d/wakeword.conf $W/
sudo systemctl daemon-reload
systemctl list-unit-files 'supervaise*' 'reachy-daemon*' 'pi-dashboard*' 'cjap-*'
```
✅ Expect:
- `apt-get` ends without `E:` lines;
- four units listed, each `disabled` or `static` (none starts at boot: `sv-robot on` starts them).

The `user@1001` restart gives sv's PipeWire the new `audio` group (it runs under that user manager, not under your SSH session). It doesn't end tmux or SSH sessions.

Now **start a fresh shell** so the new groups apply. A tmux server keeps the groups it started with, so end this runbook's own server (only `-L cjap`, nobody else's):
```bash
tmux -L cjap kill-server
```
That closes this window and drops you back to the laptop. Reconnect (PowerShell):
```powershell
ssh isl.spark -t "tmux -L cjap new -As cjap"
```
Then on the Spark:
```bash
id
loginctl show-user sv -p Linger
```
✅ Expect: `id` lists `dialout`, `plugdev` and `audio`; `Linger=yes`. Groups missing → step 11, *Groups not applied*.

---

## 3. Python venv, Gate P

`uv` installs per user (no sudo), into `~/.local/bin`.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=$HOME/.local/bin:$PATH
uv --version
```
✅ Expect: `uv 0.…`.

```bash
cd ~/Supervaise-Reachy-Mini-Project-main
export PATH=$HOME/.local/bin:$PATH
uv venv app/.venv --python /usr/bin/python3.12
P=app/.venv/bin/python
uv pip install --python $P --no-deps openwakeword==0.6.0
uv pip install --python $P -r deploy/spark/requirements-spark.txt
$P -c "import openwakeword.utils as u; u.download_models([])"
$P -c "import reachy_mini, gi, sounddevice, sherpa_onnx; print('imports ok')"
uv pip show --python $P reachy-mini | head -2
```
✅ Expect:
- `Creating virtual environment at: app/.venv`;
- the big install ends with `Installed N packages` (PyGObject builds from source: a minute or two);
- the model download prints nothing or a few progress lines;
- `imports ok`;
- `Name: reachy-mini`, `Version: 1.14.0`.

Install fails on **PyGObject** → step 11, *PyGObject build*. On **openwakeword** → *openwakeword*.

**Gate P: CJAP's own tests.**
```bash
cd ~/Supervaise-Reachy-Mini-Project-main
CJ_TTS_ORDER=spark app/.venv/bin/python -m pytest tests/ -q 2>&1 | tail -4
```
✅ Expect: `… passed` and **no** `failed` (alpha had 396 at the 09-29 handover; this branch adds 12 in `test_spark_voice.py`). Any failure → step 11, *Tests fail*.

---

## 4. Plug in the Lite, audio files, Gate A

Connect the Reachy Mini Lite: its **power supply** to the wall and its **USB-C** cable to a USB port on the Spark. Wait 10 s.

```bash
lsusb | grep -i -E '38fb|1a86'
ls -l /dev/ttyACM0
grep -iE 'reachy|audio' /proc/asound/cards
```
✅ Expect:
- two lines: `ID 38fb:1001 Pollen Robotics Reachy Mini Audio` and `ID 1a86:55d3 …` (the motor bus);
- `crw-rw---- 1 root dialout … /dev/ttyACM0`;
- a card named `Audio` (`USB-Audio - Reachy Mini Audio`) next to the existing `NVIDIA` card.

Nothing from `lsusb` → step 11, *Lite not seen*.

**The files CJAP expects in the home folder** (from `deploy/alpha`, paths changed for `sv`):
```bash
cd ~/Supervaise-Reachy-Mini-Project-main
A=deploy/alpha/home
S=deploy/spark
mkdir -p ~/bin ~/tools ~/speaker_id ~/robot/voices/panganiban ~/robot/run
cp -b $S/home/.asoundrc $S/home/.asoundrc.route ~/
chmod 700 ~/robot/voices
cp -r $A/fillers $A/fillers_ack $A/fillers_bail ~/
cp $A/speaker_id/*.onnx ~/speaker_id/
cp -r $A/tools/. ~/tools/
for f in xvf-ctl audio-out audio-volume aplay-dual verify-mic.sh; do cp $A/bin/$f ~/bin/; done
E='s#/home/pollen#/home/sv#g; s#python3.13#python3.12#g; s#/run/user/1000#/run/user/1001#g'
for f in xvf-ctl audio-out audio-volume aplay-dual verify-mic.sh; do sed -i "$E" ~/bin/$f; done
install -m 755 $S/bin/sv-robot $S/bin/whisper-keepalive $S/bin/cjap-env-set ~/bin/
for f in xvf-ctl audio-out audio-volume aplay-dual verify-mic.sh; do chmod 755 ~/bin/$f; done
ln -sfn ~/Supervaise-Reachy-Mini-Project-main/dashboard ~/pi_dashboard
grep -l pollen ~/bin/* ~/.asoundrc || echo no-pollen-paths
ls ~/fillers | wc -l
```
✅ Expect: `no-pollen-paths`; `40`. (`cp -b` kept any earlier `~/.asoundrc` as `~/.asoundrc~`.)

**Gate A: the robot's speaker and microphone.** Route playback to the robot's card, play a filler, record 4 s from the robot's microphone, play it back. **When the filler has played, speak a sentence near the robot** (the next 4 s are recorded):
```bash
export XDG_RUNTIME_DIR=/run/user/1001
~/bin/audio-out internal
pactl get-default-sink
aplay -D audio_out_route ~/fillers/01.wav
arecord -D reachymini_audio_src_plug -f S16_LE -r 16000 -c 1 -d 4 /dev/shm/cj_mic_test.wav
aplay -D audio_out_route /dev/shm/cj_mic_test.wav
~/bin/xvf-ctl read AUDIO_MGR_OP_L
```
✅ Expect:
- `pactl get-default-sink` names an `alsa_output.usb-Pollen_Robotics_Reachy_Mini_Audio…` sink;
- you **hear** the filler ("Ah — a fine question…") **from the robot**;
- you hear your own sentence back, clearly;
- `xvf-ctl` prints one JSON line containing `AUDIO_MGR_OP_L` and two numbers (alpha: `[8, 0]`).

No sound → step 11, *No sound from the robot*. `Device or resource busy` → *Card busy*. Silent recording → *Silent microphone*. `xvf-ctl` permission error → *XVF access denied*.

---

## 5. Reachy daemon, Gate R

The daemon runs as `reachy-daemon.service` (motors only, `--no-media`, **127.0.0.1:8010**; 8000 is taken on this host).
```bash
sudo -v
```

```bash
sudo systemctl start reachy-daemon
sleep 15
ss -tln | grep 8010
curl -s http://127.0.0.1:8010/api/daemon/status; echo
journalctl -u reachy-daemon --since "-2 min" --no-pager | tail -5
```
✅ Expect: `127.0.0.1:8010` listening; a JSON status that includes `"ready": true` (and the backend running); the journal ends without `Error`/`Traceback`. The robot's head may move to its "awake" pose.

**Gate R: motion through the SDK, the way CJAP connects.**
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/app
.venv/bin/python - <<'EOF'
from reachy_mini import ReachyMini
m = ReachyMini(port=8010, connection_mode="localhost_only", media_backend="no_media")
m.enable_motors()
m.goto_target(antennas=[0.6, -0.6], duration=1.0)
m.goto_target(antennas=[0.0, 0.0], duration=1.0)
print("motion ok")
EOF
sudo systemctl stop reachy-daemon
```
✅ Expect: the antennas swing out and back; `motion ok`. Anything else → step 11, *Daemon not ready* or *SDK connect fails*.

---

## 6. Keys, Gate W

CJAP reads its keys from `app/.env` (mode 600). `cjap-env-set NAME` asks for the value without echoing it.
```bash
cd ~/Supervaise-Reachy-Mini-Project-main
cp -n app/.env.example app/.env
chmod 600 app/.env
cjap-env-set ANTHROPIC_API_KEY
```
Paste the Anthropic key at the prompt. ✅ Expect: `ANTHROPIC_API_KEY set in …/app/.env`.

A **whisper-only** LiteLLM key for the robot (it can't use the chat models):
```bash
sv-keys --one cjap-whisper --models whisper --rpm 120 --parallel 2
```
✅ Expect: the new key printed once. Copy it, then:
```bash
cjap-env-set OPENAI_API_KEY
```
Paste the whisper key at the prompt. Then the non-secret settings:
```bash
cjap-env-set OPENAI_BASE_URL http://127.0.0.1:18080/v1
cjap-env-set OPENAI_STT_MODEL whisper
cjap-env-set CJ_TTS_ORDER spark
cjap-env-set CJ_QWEN_TTS_URL http://127.0.0.1:8091
cjap-env-set --show
```
✅ Expect: the `--show` list includes `ANTHROPIC_API_KEY=(set)`, `OPENAI_API_KEY=(set)`, `OPENAI_BASE_URL=(set)`, `CJ_TTS_ORDER=(set)`; `ELEVEN_API_KEY=(empty)` and `FISH_API_KEY=(empty)` stay empty on purpose.

**Gate W: CJAP's own STT function against the Spark's Whisper.** Three runs of the same filler clip; the first may wait for the GPU worker to load.
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/app
set -a; . ./.env; set +a
.venv/bin/python - <<'EOF'
import os, time, speech_engines as s
for i in range(3):
    t = time.monotonic()
    txt = s.transcribe_openai(os.path.expanduser("~/fillers/07.wav"), language="en")
    print(f"{time.monotonic() - t:5.2f} s  {txt!r}")
EOF
```
✅ Expect:
- three lines, each the sentence *"I should like to answer this properly, so let me consult my record first."* (small wording differences are fine), **without** `{` or `"text"`;
- the first up to ~60 s (cold worker), the **second and third ≤ 1.5 s**.

`401` → step 11, *Whisper 401*. `503` or a timeout → *Whisper busy or cold*.

---

## 7. The voice

### 7.1 Build `sv/cjap-tts:1`

The image is built on `sv/whisper:1` and must keep its torch build. Pin it from the image itself:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/tts
docker run --rm sv/whisper:1 pip freeze | grep -E '^(torch|torchaudio|triton)==' > constraints.txt
cat constraints.txt
cd ../compose
docker compose build cjap-tts 2>&1 | tail -5
docker run --rm sv/cjap-tts:1 cat /opt/cjap-tts/versions.txt > /dev/shm/tts_versions.txt
grep -E '^(torch|faster-qwen3-tts|transformers)==' /dev/shm/tts_versions.txt
```
✅ Expect:
- `constraints.txt`: three lines, `torch==2.11.0+cu130`, `torchaudio==2.11.0…`, `triton==3.6.0`;
- the build ends with `Built` / `naming to docker.io/sv/cjap-tts:1` (5–15 min);
- `faster-qwen3-tts==0.5.4`, `torch==2.11.0+cu130`, `transformers==5.…`.

A pip error about torch → step 11, *TTS build: torch conflict*.

### 7.2 The model (4.5 GB)
```bash
cd ~/models
M=Qwen/Qwen3-TTS-12Hz-1.7B-Base
N=${M#*/}
I=sv/cjap-tts:1
R="--rm -u 1001:1001 -e HF_HUB_OFFLINE=0"
docker run $R -v $PWD:/models $I hf download $M --local-dir /models/$N
du -sh ~/models/$N
```
✅ Expect: the download completes; `4.3G` to `4.6G`.

### 7.3 The reference clip, from the real recording

The clone is made from 10–15 s of **Justice Panganiban's own voice**: a stretch of `Recording_four.aac`, the 3 min 16 s recording the Fish Audio "CJAP" model was trained on. Get the file from whoever made that model (Fish account `dev0`) and put it in `~/Downloads` on the laptop.

On the **laptop** (PowerShell):
```powershell
scp ~/Downloads/Recording_four.aac isl.spark:robot/voices/
```
✅ Expect: one line, `Recording_four.aac 100% …`.

On the **Spark**: the script transcribes the recording with the Spark's own Whisper (it never leaves the box), picks the cleanest continuous 10–15 s, cuts it to 24 kHz mono and transcribes the cut again:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main
P=app/.venv/bin/python
V=$HOME/robot/voices
$P deploy/spark/tts/ref_from_recording.py $V/Recording_four.aac $V/panganiban
```
✅ Expect:
- `transcribing the whole recording …` (a minute or two);
- up to five numbered candidates, `start-end s (duration, confidence): text`;
- `ref.wav: …` and `ref.txt: …` with the chosen stretch and its text.

**Listen and check the text.** Through the robot's speaker, then on the laptop's headphones:
```bash
aplay -D audio_out_route ~/robot/voices/panganiban/ref.wav
cat ~/robot/voices/panganiban/ref.txt
```
```powershell
scp isl.spark:robot/voices/panganiban/ref.wav ~/Downloads/ref_panganiban.wav
```
✅ Expect: one speaker, clear, no music or noise, no cough or laugh, a calm delivery; and `ref.txt` says **exactly** what you hear. Correct any misheard word with `nano ~/robot/voices/panganiban/ref.txt` (the clone copies the audio by aligning it to this text). If the stretch itself is poor, run the same `$P …` line again with `--pick 2` (or 3, 4, 5) at the end, or choose one by ear with `--start S --end E` in seconds.

No recording available → step 11, *No real recording*.

### 7.4 Start it, Gate T
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/compose
docker compose up -d cjap-tts
H=127.0.0.1:8091/health
for i in $(seq 36); do curl -s $H | grep -q '"ok":true' && break; sleep 10; done
curl -s 127.0.0.1:8091/health; echo
python3 ../tts/tts_bench.py
docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' sv-robot-cjap-tts-1
```
The `for` line waits up to 6 min for the model to load and warm up (2–5 min the first time).
✅ Expect:
- `/health`: `"ok": true`, `"model": "Qwen3-TTS-12Hz-1.7B-Base"`, a 12-character `ref` (the reference's hash), `warm_s` under ~120;
- ten bench lines, then **`median speed ≥ 1.25x`** and the **first (opener) line `synth ≤ 1.8 s`**;
- memory under ~10 GiB.

Waiting more than 6 min → step 11, *cjap-tts never ready*. Speed under 1.25× → *TTS too slow*.

### 7.5 Gate V: listen

Through the **robot's speaker**:
```bash
aplay -D audio_out_route /dev/shm/cj_tts_opener.wav
aplay -D audio_out_route /dev/shm/cj_tts_longest.wav
aplay -D audio_out_route ~/fillers/01.wav
```
And on the **laptop** (PowerShell), to listen on headphones:
```powershell
scp isl.spark:/dev/shm/cj_tts_longest.wav ~/Downloads/
```
✅ Expect (your judgement, ideally with a teammate):
- it sounds like **Justice Panganiban** in the reference clip (the filler you hear third is the ElevenLabs clone; close is fine, the clips will still play between answers);
- "Panganiban" and "Salonga" are acceptable;
- the longest sentence keeps the same voice from start to end (no drift).

Wrong voice or accent → step 11, *Voice doesn't match*.

---

## 8. Robot mode, the console, Gate E, Gate L

**🔑 Owner step, once: the dashboard access key** (replaces the default `cjap`). Both the dashboard and the robot read it from one root-only file: the robot's lease requests must carry the same key, or the console refuses them and the microphone never opens. Choose a key of letters and digits only.
```bash
sudo -v
```
Then the key, alone in its own block (type it at the prompt; it isn't shown):
```bash
read -rsp "new dashboard key: " K; echo
```
```bash
sudo mkdir -p /etc/cjap
sudo install -m 600 /dev/null /etc/cjap/dashboard.env
echo "CJ_DASH_KEY=$K" | sudo tee /etc/cjap/dashboard.env >/dev/null
unset K
sudo cut -c1-12 /etc/cjap/dashboard.env
sudo stat -c '%a %U' /etc/cjap/dashboard.env
```
✅ Expect: `CJ_DASH_KEY=`; `600 root`.

**Switch to robot mode.** This stops Qwen (teammates' `qwen38` calls fail until step 9).
```bash
sudo -v
```

```bash
sv-robot on
```
✅ Expect, in order:
- `saved split: {"pct": {"qwen": 50.0, …}` then `sv-split`'s own lines as it stops Qwen;
- `waiting for cjap-tts …` then `cjap-tts ready: {"ok":true,…}`;
- four `●` units each `Active: active (running)`;
- `robot mode ON.`

**Open the console** from the laptop through an SSH tunnel (the dashboard is not exposed to the internet). On the **laptop**, a second PowerShell window:
```powershell
ssh -N -L 8180:127.0.0.1:8180 isl.spark
```
Leave it open. In the laptop's browser: `http://localhost:8180/console?key=<your dashboard key>`
- **Floor:** `alpha`. **Mode:** `direct`. **Profile:** `kiosk`.
- **Wake threshold:** start at **0.15** (genuine "Hi Cee-Jap" calls scored 0.066–0.46 on alpha; the handover left 0.5, which misses most of them).
- `http://localhost:8180/maintain?key=…` shows mic, speaker route, last-turn timings and the voice-guard state.

Check the robot's journal:
```bash
journalctl -u supervaise -n 400 --no-pager | grep -E '[[](gestures|mic|wake|tts|voice)' | tail -12
```
✅ Expect: `[mic] using ReSpeaker array (reachymini_audio_src_plug)`, `[gestures] connected, motors on`, `[gestures] breathing …`, `[wake] armed …`; no `[gestures] disabled`, no `[tts] spark failed`.

Expected noise, not faults: a `[prewarm]` line about the OpenAI model check (it now goes to LiteLLM with a whisper-only key), `/maintain` showing the OpenAI key as invalid (it tests against api.openai.com), and `/maintain` buttons that restart services failing (they use `sudo -n`; use `sv-robot` instead).

**Gate E: live turns** (in the room with the robot):
1. Say **"Hi Cee-Jap"**. ✅ The head perks toward you.
2. Ask **"What is the rule of law?"** ✅ A filler or ack plays, then an answer in the **clone voice**, the head moving while it speaks.
3. Ask a follow-up within ~10 s (voice lock), e.g. **"Tell me about your mentor."** ✅ Answered without the wake word (it mentions Jovito Salonga).
4. While it answers, say **"Cee-Jap"** (the stop phrase). ✅ It stops within about a second.
5. **Voice guard.** Stop the voice server:
   ```bash
   cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/compose
   docker compose stop cjap-tts
   ```
   Ask a new question. ✅ The pre-recorded acknowledgement or filler may still play, but **no answer sentence is spoken in any other voice** (only sentences already in the cache can play), and `/maintain` shows the voice warning. Start it again and wait for it:
   ```bash
   cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/compose
   docker compose start cjap-tts
   H=127.0.0.1:8091/health
   for i in $(seq 36); do curl -s $H | grep -q '"ok":true' && break; sleep 10; done
   curl -s 127.0.0.1:8091/health; echo
   ```

```bash
journalctl -u supervaise --since "-10 min" --no-pager | grep -E '[[](stt|trace)[]]' | tail -8
```
✅ Expect: `[stt] heard: …` lines with your questions, and one `[trace] path=streamed | stt_s=… | first_audio_s=… | on_air_s=…` per answer.

**Gate L: latency over 20 turns.** Ask 20 varied questions (the six build-kit questions plus your own), then:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main
J="journalctl -u supervaise -o short-iso --no-pager"
$J -g '[[]trace[]]' --since today > ~/robot/spark_trace.txt
app/.venv/bin/python scripts/turn_timing.py ~/robot/spark_trace.txt --label spark --endpoint-s 1.2
```
✅ Expect: the per-stage table; **median `stt_s` ≤ 1.5 s**, **median `on_air_s` ≤ 5 s**. Compare with alpha's numbers if you have an alpha trace. Over → step 11, *Slow first answer*.

---

## 9. Back to office mode, Gate O
```bash
sudo -v
```

```bash
sv-robot off
sleep 120
docker ps -a --format '{{.Names}} {{.Status}}' | grep -E 'vllm|cjap'
sv-split | head -6
```
✅ Expect:
- `restoring split: qwen=50 lfm=0 embed=0 ctx=131072` and `robot mode OFF.`;
- `sv-llm-vllm-1 Up … (health: starting)` turning `(healthy)` within ~5 min; `sv-robot-cjap-tts-1` `Exited`;
- the split shows `qwen 50`.

Then send one chat request the way you normally do (any `qwen38` key). ✅ It answers.

Unplugging the robot is fine in office mode.

---

## 10. Daily use

| Task | Command |
|---|---|
| Robot on / off / state | `sv-robot on` · `sv-robot off` · `sv-robot status` |
| Console and maintenance | laptop: `ssh -N -L 8180:127.0.0.1:8180 isl.spark`, then `http://localhost:8180/console?key=…` and `/maintain?key=…` |
| Follow one turn | `journalctl -u supervaise -f \| grep -E '[[](wake\|stt\|stream\|tts\|trace)'` |
| Voice server state | `curl -s 127.0.0.1:8091/health` · `docker logs sv-robot-cjap-tts-1 --tail 30` |
| Restart CJAP only (not mid-answer) | `sudo systemctl restart supervaise` |
| Update the code | once the branch is on GitHub: `cd ~/Supervaise-Reachy-Mini-Project-main && git pull origin spark/local-speech`, then the tests (step 3), re-install the units if `deploy/spark/systemd` changed (step 2), and `sudo systemctl restart supervaise pi-dashboard` |
| Swap the reference voice | put `ref.wav` + `ref.txt` in `~/robot/voices/panganiban/`, then `docker compose restart cjap-tts` in `deploy/spark/compose`. The cache key includes the reference hash, so old clips are not reused |
| Use the 0.6B model | download `Qwen/Qwen3-TTS-12Hz-0.6B-Base` as in 7.2, set `TTS_MODEL: /models/Qwen3-TTS-12Hz-0.6B-Base` in `deploy/spark/compose/docker-compose.yml`, `docker compose up -d cjap-tts` |
| Visitor audio kept by Whisper | `ls ~/whisper/api/_sync \| wc -l`; after an event: `find ~/whisper/api/_sync -mindepth 1 -maxdepth 1 -mtime +0 -exec rm -rf {} +` |

---

## 11. Incidents

Look up the row named by the step. These are the only fixes; don't improvise on the box.

| Row | Symptom | Cause and fix |
|---|---|---|
| **Branch on GitHub** | The branch was pushed | Skip the bundle: `git fetch origin spark/local-speech:spark/local-speech` then `git checkout spark/local-speech` |
| **Groups not applied** | `id` lacks `dialout` after reconnecting | You reattached a tmux server started before step 2. Run `tmux -L cjap kill-server` (this runbook's server only; never a bare `tmux kill-server`, which ends everyone's sessions on the box), reconnect with `ssh isl.spark -t "tmux -L cjap new -As cjap"`. Still missing: `grep -E 'dialout|plugdev|audio' /etc/group` should list `sv`; if not, step 2's `usermod` line didn't run |
| **PyGObject build** | `uv pip install` fails on `PyGObject` / `pycairo` with a meson or pkg-config error | Step 2's apt lines didn't all run. Re-run them, then the install line. Still failing: send the last 30 lines of the error |
| **openwakeword** | `ModuleNotFoundError: tflite_runtime` at import | It was installed with its dependencies. `uv pip uninstall --python app/.venv/bin/python openwakeword`, then the `--no-deps` line again |
| **Tests fail** | `pytest` reports failures | Run the same command with `-x -q --tb=short` and read the first failure. `test_spark_voice.py` failing = the branch didn't check out cleanly (`git status`). Others: compare with the base, `git stash; git checkout 1d986be`, run the same test, `git checkout spark/local-speech; git stash pop`. A failure on both is not caused by this branch |
| **Lite not seen** | `lsusb` shows neither id | Power supply connected? Try another USB port and cable (a data cable, not charge-only). `journalctl -k --since "-5 min" \| tail -20` |
| **No sound from the robot** | `aplay` runs, silence | `pactl list sinks short`: if no `Reachy_Mini_Audio` sink, PipeWire can't open the card or isn't running for sv: `systemctl --user status pipewire wireplumber`; if it started before step 2, `sudo systemctl restart user@1001.service` (gives it the `audio` group). If the sink exists: `pactl set-default-sink <its name>`, `~/bin/audio-volume` (or `amixer -c Audio set PCM 100%`) |
| **Card busy** | `aplay`/`arecord`: `Device or resource busy` | Something else opened the card raw. `fuser -v /dev/snd/*`. If it is PipeWire holding capture, the `dsnoop` in `~/.asoundrc` can't open: `systemctl --user restart wireplumber` and retry; persisting → report it (a WirePlumber rule to leave the capture side alone is the fix) |
| **Silent microphone** | The recording is silence | XVF3800 firmware older than 2.1.3 records zeros on some Lites (Pollen issue #845): `~/bin/xvf-ctl read VERSION`. Update with Pollen's `dfu-util` procedure (owner step) |
| **XVF access denied** | `xvf-ctl`: `Access denied` / Errno 13 | udev rule not applied: unplug and replug the robot; check `ls -l /dev/bus/usb/*/*` shows `plugdev` for the device; re-login for the group |
| **Daemon not ready** | `/api/daemon/status` missing or `"ready": false` | `journalctl -u reachy-daemon -n 50`. "No serial port"/"several ports" → is `/dev/ttyACM0` the robot (`ls -l /dev/serial/by-id`)? If another device took `ttyACM0`, change `--serialport` in `/etc/systemd/system/reachy-daemon.service` to the `by-id` path (owner step), `daemon-reload`. Version below 1.14.0 reports `ready: false` on the Spark (#1278) |
| **SDK connect fails** | Gate R or `[gestures] disabled (…)` | The daemon isn't on 8010 or isn't running: `ss -tln \| grep 8010`. CJAP: `CJ_REACHY_PORT=8010` must be in the drop-in (`systemctl show supervaise -p Environment \| tr ' ' '\n' \| grep REACHY`). The SDK and daemon must be the same version (both in `app/.venv`) |
| **Whisper 401** | `AuthenticationError` | Wrong key in `OPENAI_API_KEY`, or the key lacks the `whisper` model. Make a new one (step 6) |
| **Whisper busy or cold** | 503 or a long first call | The worker loads on demand (30–60 s). Check `docker logs sv-llm-whisper-api-1 --tail 20` for `waiting for memory`: with Qwen still running and little free memory it waits. In robot mode the keepalive keeps it loaded: `systemctl status cjap-whisper-keepalive` |
| **TTS build: torch conflict** | pip wants another torch | `constraints.txt` empty or wrong: re-run its line in 7.1 and check its three lines; rebuild with `docker compose build --no-cache cjap-tts` |
| **cjap-tts never ready** | `/health` not ok after 6 min | `docker logs sv-robot-cjap-tts-1 --tail 50`. `No such file …/ref.wav` → step 7.3. `local_files_only` / missing files → step 7.2 not complete. CUDA / out of memory → `free -g` (is Qwen still running? `sv-split`) |
| **TTS too slow** | Median speed < 1.25× or opener > 1.8 s | Check nothing else uses the GPU (`nvidia-smi`). Then switch to the 0.6B model (step 10) and re-run the bench |
| **Voice doesn't match** | Wrong timbre or accent | First check `ref.txt` against `ref.wav` word for word (step 7.3). Then another stretch: the 7.3 line with `--pick 2` … `--pick 5`, then `docker compose restart cjap-tts` in `deploy/spark/compose` and the bench again. Last resort: `TTS_XVEC_ONLY: "1"` in the compose file (speaker embedding only, no transcript) |
| **No real recording** | `Recording_four.aac` can't be found | Use the ElevenLabs filler clips (already the clone voice, but with CJAP's speaker EQ and a "thinking" delivery): `F=$PWD/deploy/alpha/home/fillers`, `V=$HOME/robot/voices/panganiban`, then `docker run --rm --user 1001:1001 -v $F:/f:ro -v $V:/out sv/cjap-tts:1 python make_ref.py /f /out` from the checkout (clips 01 03 07; others: 06 11 15 20 26). Swap in the real recording later (step 10, *Swap the reference voice*) |
| **Robot deaf** | No reaction to "Hi Cee-Jap" | `journalctl -u supervaise -n 200 \| grep -i -E 'lease\|403'`: a 403 or "bad key" means the robot sends another key than the console expects; both read `/etc/cjap/dashboard.env`, so check it exists (`sudo ls -l /etc/cjap`) and restart both (`sudo systemctl restart pi-dashboard supervaise`). Then `/console`: floor `alpha`, mode `direct`? (the mic only opens while the floor is granted). `/maintain` wake meter: scores below the threshold → lower it. Mic muted on `/maintain`? |
| **Slow first answer** | `on_air_s` well above 5 s | Read the trace columns: `stt_s` high → Whisper cold (keepalive); `first_audio_s` high → TTS (0.6B model) or composer (`CJ_CONTEXT_BODY_DOCS=1` in `app/.env`) |
| **Dashboard won't start** | `pi-dashboard` fails, `Address already in use` | Something took 8180/8543: `ss -tln \| grep -E '8180\|8543'`. Pick free ports in `/etc/systemd/system/pi-dashboard.service` and `deploy/spark/robots.json` (`authority.port`) and `CJ_CONSOLE_URL` in the drop-in, then `daemon-reload` |
| **sv-split restore fails** | `sv-robot off` can't restore | `cat ~/robot/run/split-before.json`, then set it by hand: `sv-split qwen=50 lfm=0 embed=0` |

---

## 12. Teardown

Back to the box as it was before this runbook (the Whisper and LLM stacks are untouched):
```bash
sudo -v
```

```bash
sv-robot off
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/compose && docker compose down
docker image rm sv/cjap-tts:1
sudo rm /etc/systemd/system/{supervaise,reachy-daemon,pi-dashboard,cjap-whisper-keepalive}.service
sudo rm -r /etc/systemd/system/supervaise.service.d /etc/systemd/system/pi-dashboard.service.d
sudo rm /etc/udev/rules.d/99-reachy-mini.rules
sudo udevadm control --reload-rules
sudo rm -r /etc/cjap
sudo systemctl daemon-reload
sv-keys --revoke cjap-whisper
```
Optional, to also remove the data (`~/robot/voices` holds Justice Panganiban's recording): `~/Supervaise-Reachy-Mini-Project-main`, `~/robot`, `~/models/Qwen3-TTS-12Hz-1.7B-Base`, `~/fillers*`, `~/speaker_id`, `~/tools`, the copied `~/bin` scripts, `~/.asoundrc*` (restore `~/.asoundrc~` if `cp -b` made one), `~/.voice_cache`, `~/pi_dashboard`. Groups and linger can stay.
