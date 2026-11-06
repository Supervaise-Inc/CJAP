# Runbook: CJAP on the DGX Spark, with a video avatar (alternative version)

> **For:** you, as `sv`, over `ssh isl.spark`, plus owner steps that need your sudo password (🔑). **Design:** [`CJAP_SPARK_AVATAR_ARCHITECTURE.md`](AVATAR_ARCHITECTURE.md).
> **What you get:** everything the base runbook gives (CJAP on the Spark, Reachy Mini Lite, Whisper, the local voice) **plus a lip-synced face of Justice Panganiban** from **AVTR-1** on the Spark's GPU, shown by CJAP's own `/face-avatar` page on a display laptop next to the robot, with the voice from the monitor's speakers. The face also listens: it reacts while the visitor talks.
> **How to use:** **Part 1** is the base runbook, unchanged. **Part 2** (steps X0–X9) adds the avatar: run its blocks in order and compare with **✅ Expect**. Fixes are only in step X11. A block that is only `sudo -v` asks for your password before the next block.
> **The code** is on CJAP branch **`spark/video-avatar`** (`spark/local-speech` plus the avatar commits), also in the bundle `cjap-spark/cjap-spark-video-avatar.bundle`.
> **Licences:** AVTR-1's renderer is **noncommercial only** (PolyForm Noncommercial); its face-analysis models (InsightFace) are non-commercial research only; the Wav2Lip fallback is non-commercial. Fine for building and testing; check with counsel before a public exhibit (architecture §9).

| Step | What | Where | Time |
|---|---|---|---|
| Part 1 | Base runbook steps 0–9 (CJAP, robot, voice) through Gate E | sv + robot | 2–3 h |
| X0 | Check (read only), and a HuggingFace account | sv + browser | 5 min |
| X1 | 🔑 The avatar branch, dashboard unit, tests | laptop + sv | 5 min |
| X2 | Keys, config and the HuggingFace token | sv | 3 min |
| X3 | Build `sv/cjap-avatar:1` (TensorRT, plugin, AVTR-1, LiveKit) | sv | 30–60 min |
| X4 | AVTR-1 weights and TensorRT engines | sv | 30–60 min |
| X5 | The portrait | laptop + sv | 5 min |
| X6 | Gate X1: the plumbing with the `still` engine | sv + display laptop | 15 min |
| X7 | Gate X2: AVTR-1 speed (alone and with the voice running) | sv + laptop | 15 min |
| X8 | Gate X3: live with AVTR-1 | robot + display laptop | 20 min |
| X9 | Back to office mode | sv | 3 min |
| X10 | Daily use | | |
| X11 | Incidents, and the Wav2Lip fallback | | |
| X12 | Teardown | | |

---

## Part 1. The base runbook

Run [`CJAP_SPARK_RUNBOOK.md`](RUNBOOK.md) **steps 0–9** first, as written. They give the Spark CJAP, the robot, Whisper and the voice. **Gate E** there must pass: the robot answers in the clone voice. Leave the robot plugged in.

---

## X0. Check

On the **Spark** (tmux `-L cjap` session, read only):
```bash
sv-robot status
ss -tln | grep -E ':(7880|7881|8092) ' || echo avatar-ports-free
ss -uln | grep ':7882 ' || echo udp-free
docker image ls sv/cjap-tts:1 --format '{{.Repository}}:{{.Tag}}'
free -g | sed -n 2p
df -h ~ | tail -1
ls -l ~/.asoundrc
id -nG | tr ' ' '\n' | grep -x audio
```
✅ Expect: `mode: office` or `robot`; `avatar-ports-free`; `udp-free`; `sv/cjap-tts:1`; ≥ 40 GB memory available; ≥ 30 GB disk free; `~/.asoundrc` present (base runbook step 2); `audio`.

In a **browser**, with a HuggingFace account (any; free):
1. Open `https://huggingface.co/avaturn-live/avtr-1` and accept the licence to get access (the weights are gated; access is granted at once).
2. Open `https://huggingface.co/settings/tokens` → **Create new token** → type **Read** → copy it (step X2 asks for it; don't paste it anywhere else).

You also need:
- a **display laptop or mini-PC** with Chrome or Edge, **on the same LAN as the Spark** (192.168.1.x), with internet (the page loads LiveKit's browser library from a CDN), and an HDMI monitor with speakers;
- the **portrait photo** (front-facing, even light, face ≥ 256 px, the subject's consent) in `~/Downloads` on your laptop.

---

## X1. 🔑 The avatar branch, dashboard unit, tests

On the **laptop** (PowerShell):
```powershell
cd ~/Downloads/SV/DGXSpark
scp cjap-spark/cjap-spark-video-avatar.bundle isl.spark:
```
✅ Expect: `cjap-spark-video-avatar.bundle 100% …`.

On the **Spark**:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main
git status --short | head -5
git bundle verify ~/cjap-spark-video-avatar.bundle
git fetch ~/cjap-spark-video-avatar.bundle +spark/video-avatar:spark/video-avatar
git checkout spark/video-avatar
git log --oneline -3
```
✅ Expect: `git status` prints nothing (no local edits); `… is okay`; `Switched to branch 'spark/video-avatar'`; the log starts with `Spark: AVTR-1 in place of Ditto for the video avatar`, then `Spark: a local video avatar in place of HeyGen LiveAvatar`.

```bash
sudo -v
```

```bash
cd ~/Supervaise-Reachy-Mini-Project-main
S=deploy/spark
sudo install -m 644 $S/systemd/pi-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
install -m 755 $S/bin/sv-robot ~/bin/
systemctl is-active pi-dashboard
P=app/.venv/bin/python
CJ_TTS_ORDER=spark $P -m pytest tests/test_spark_avatar.py tests/test_avatar_session.py -q | tail -3
```
✅ Expect:
- `inactive` (Part 1 ended in office mode; robot mode starts it with the new setting);
- `… passed` with **no** `failed`; tests that need FastAPI or soxr show as `skipped` if CJAP's venv lacks them (they ran in the branch's own checks).

---

## X2. Keys, config and the HuggingFace token

Random keys for LiveKit and for the avatar API, written straight into the two config files (mode 600) and into CJAP's avatar config:
```bash
mkdir -p ~/robot/avatar/bench
chmod 700 ~/robot/avatar
cd ~/robot/avatar
LKS=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
AK=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
AID=$(python3 -c 'import uuid; print(uuid.uuid4())')
install -m 600 /dev/null avatar.env
install -m 600 /dev/null livekit.yaml
cat > avatar.env <<EOF
AVATAR_API_KEY=$AK
AVATAR_ID=$AID
LIVEKIT_API_KEY=avatarkey
LIVEKIT_API_SECRET=$LKS
EOF
cat > livekit.yaml <<EOF
port: 7880
bind_addresses: ["0.0.0.0"]
rtc:
  tcp_port: 7881
  udp_port: 7882
  use_external_ip: false
  node_ip: 192.168.1.201
  ips:
    includes: [192.168.1.0/24]
keys:
  avatarkey: $LKS
logging:
  level: info
EOF
cd ~/Supervaise-Reachy-Mini-Project-main/dashboard
mkdir -p assets
install -m 600 /dev/null assets/liveavatar.json
cat > assets/liveavatar.json <<EOF
{"api_key": "$AK", "avatar_id": "$AID", "sandbox": false}
EOF
unset LKS AK
ls -l ~/robot/avatar assets/liveavatar.json
cut -c1-15 ~/robot/avatar/avatar.env
```
✅ Expect: `avatar.env`, `livekit.yaml` and `liveavatar.json` all `-rw-------` owned by `sv`; four lines `AVATAR_API_KEY=…`, `AVATAR_ID=…`, `LIVEKIT_API_KEY…`, `LIVEKIT_API_SEC…`.

The HuggingFace token from X0, at a hidden prompt (nothing shows while you paste; press Enter):
```bash
cd ~/robot/avatar
read -rsp 'HuggingFace read token: ' HFT; echo
install -m 600 /dev/null hf.token
echo "$HFT" > hf.token
unset HFT
ls -l hf.token
cut -c1-3 hf.token
```
✅ Expect: `-rw-------` … `hf.token` of about 38 bytes; `hf_`.

---

## X3. Build `sv/cjap-avatar:1`

One image for downloading the weights, building the engines and running: CUDA 13.0 devel, TensorRT 10.14.1, the GridSample3D plugin compiled for the GB10 (sm_121), AVTR-1 (pinned), ONNX Runtime with CUDA, LiveTalking (for the fallback only), LiveKit's Python SDK, the server.
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose build cjap-avatar 2>&1 | tail -5
I=sv/cjap-avatar:1
docker run --rm --gpus all $I python -c "import tensorrt as t; print('trt', t.__version__)"
docker run --rm --gpus all $I python -c "import onnxruntime as o; print(o.get_available_providers())"
docker run --rm --gpus all $I python -c "import avtr1_renderer; print('avtr1 ok')"
docker run --rm $I ls -l /opt/libgrid_sample_3d_plugin.so
docker run --rm $I grep -i -E '^(torch|tensorrt|onnxruntime|livekit|numpy|avtr)' versions.txt
```
✅ Expect:
- the build ends with `naming to docker.io/sv/cjap-avatar:1` (30–60 min the first time);
- `trt 10.14.1.48…`;
- a list that includes `'CUDAExecutionProvider'`;
- `avtr1 ok`;
- the plugin file, a few hundred KB;
- among them `torch==2.11.0…`, `tensorrt…10.14.1…`, `onnxruntime-gpu==1.31.1`, `livekit==1.2.1`, `numpy==2.…`, `avtr-1 eb1e5a89…`.

An `apt` error about `libnvinfer…` versions → step X11, *TensorRT apt version*. A CMake/nvcc error → *Plugin build*. No `CUDAExecutionProvider` → *ONNX Runtime without CUDA*.

---

## X4. AVTR-1 weights and TensorRT engines

First the arm64 plugin in its place (so the download keeps it and skips the published x86 one), then the weights (about 2 GB, from AVTR-1's gated repo and Ditto's public one):
```bash
mkdir -p ~/models/avtr1/main/renderer_runtime_artifacts
cd ~/models
I=sv/cjap-avatar:1
G="--rm -u 1001:1001 --gpus all -v $PWD:/models"
P=/models/avtr1/main/renderer_runtime_artifacts
docker run $G $I cp /opt/libgrid_sample_3d_plugin.so $P/
export HF_TOKEN=$(cat ~/robot/avatar/hf.token)
D=/opt/avtr1/scripts/download_artifacts.py
docker run $G -e HF_TOKEN -e HF_HUB_OFFLINE=0 $I python $D 2>&1 | tail -3
unset HF_TOKEN
du -sh ~/models/avtr1/main
ls -l ~/models/avtr1/main/renderer_runtime_artifacts
```
✅ Expect: `All artifacts ready.`; about `1.9G`; seven `.onnx` files (`appearance_extractor`, `motion_extractor`, `landmark106`, `landmark203`, `insightface_det`, `blaze_face`, `face_mesh`) and `libgrid_sample_3d_plugin.so` with the **same size as in X3** (1820592 bytes would be the x86 one). `GatedRepoError` or `401` → step X11, *Weights refused*.

Then the TensorRT engines, built for this GPU (the GPU does this; 15–45 min):
```bash
cd ~/models
I=sv/cjap-avatar:1
G="--rm -u 1001:1001 --gpus all -v $PWD:/models"
B=/opt/avtr1/scripts/build_engines.py
docker run $G $I python $B 2>&1 | tail -25
cd ~/models/avtr1/main
ls renderer_runtime_artifacts_cc speech2motion_runtime_artifacts_cc
ls -l avtr1_normalizer.safetensors
```
✅ Expect:
- the log ends with `All engines built.` (a warning `You are using the legacy TorchScript-based ONNX export` is expected);
- `renderer_runtime_artifacts_cc`: `decoder_b5_fp16.engine`, `modnet_b5_fp16.engine`, `stitch_network_b5_fp16.engine`, `warp_network_b5_fp16.engine`;
- `speech2motion_runtime_artifacts_cc`: `avtr1_decode_fp16.engine`, `avtr1_encode_fp16.engine`, `hubert_lbs_fp16.engine`;
- `avtr1_normalizer.safetensors`.

A warp error about `GridSample3D` → step X11, *Warp engine*. An error inside `torch.onnx.export` → *AVTR-1 export*.

---

## X5. The portrait

On the **laptop** (PowerShell; use your file's name):
```powershell
scp ~/Downloads/portrait.jpg isl.spark:robot/avatar/source.jpg
```
On the **Spark**: a 1280×720 PNG with the face centred (AVTR-1's frame):
```bash
I=sv/cjap-avatar:1
cd ~/robot/avatar
R="--rm -u 1001:1001 -v $PWD:/avatar"
docker run $R $I python prepare_photo.py /avatar/source.jpg /avatar/portrait.png
```
✅ Expect: `… -> /avatar/portrait.png 1280x720 (face …)`. A `padded with white` line is fine (the person is cut out and put on the background). A `WARNING: the face is under 256 px` means a larger photo would look sharper.

Check the crop on the **laptop**:
```powershell
scp isl.spark:robot/avatar/portrait.png ~/Downloads/portrait_check.png
```
✅ Expect: the face centred, the whole head and the shoulders visible, eyes open, mouth closed.

The background is `plain_white`. To change it, set `AVATAR_BG` in `deploy/spark/avatar/docker-compose.yml` to one of `aloe_window`, `beige_sofa`, `bright_loft`, `framed_art`, `jungle_window`, `lounge_chairs`, `minimal_office`, `plain_white`, `study_desk`, `sunlit_bedroom`, or to your own 1280×720 image copied to `~/robot/avatar/` (e.g. `/avatar/background.png`).

---

## X6. Gate X1: the plumbing with the `still` engine

Before AVTR-1, prove the path with the `still` engine (the photo, our audio passed through, no lip motion): the dashboard's session calls, LiveKit across the LAN, the control socket, the lag loop and the voice mode.

Turn robot mode on (as in base runbook step 8; the avatar isn't part of it yet):
```bash
sudo -v
```

```bash
sv-robot on
sudo systemctl restart pi-dashboard
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
AVATAR_ENGINE=still docker compose up -d
H=127.0.0.1:8092/health
for i in $(seq 30); do curl -s $H | grep -q '"ok":true' && break; sleep 2; done
curl -s $H; echo
docker compose ps --format '{{.Name}} {{.Status}}'
```
✅ Expect: `robot mode ON.` (as in the base runbook); `/health` with `"ok":true`, `"engine":"still"`, `"size":[1280,720]`; `sv-avatar-livekit-1` and `sv-avatar-cjap-avatar-1` both `Up`.

On the **display laptop** (on the LAN), in Chrome or Edge:
1. `http://192.168.1.201:8180/face-avatar?key=<your dashboard key>`, then **click once** on the page (browsers play sound only after a click). Press F11 on the monitor.
2. A second tab: `http://192.168.1.201:8180/maintain?key=<your dashboard key>` → the **LiveAvatar** card → ⟳: ✅ the avatar shows as **Panganiban (Spark)**, ACTIVE. Then press **Voice: avatar** (after the face page is open: the page ignores a voice command sent before it loaded).
3. Say **"Hi Cee-Jap"** to the robot and ask **"What is the rule of law?"**

✅ Expect:
- the page goes from the still portrait to the live stream (`session connected` in its status line), still showing the photo;
- **the answer is heard from the laptop's/monitor's speakers**, and **not** from the robot; the robot's head still moves;
- the page's status line shows `speaking — avatar start lag 0.xs (auto-sync)`;
- on the Spark: `curl -s 127.0.0.1:8092/health` shows `"speak_started"` above 0.

No live stream → step X11, *LiveKit not reached*. Sound from the robot too → *Voice from the robot*. The robot interrupts itself → *Self-interrupt*.

---

## X7. Gate X2: AVTR-1 speed

The engine alone first, then while the voice server is busy (as it is during an answer). Stop the plumbing test and make a test sentence with the clone voice:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose down
cd ~/robot/avatar
W='The rule of law means that no one is above the law, not even the President.'
W="$W Every citizen may seek justice from the courts."
T=$(python3 -c 'import json, sys; print(json.dumps({"text": sys.argv[1]}))' "$W")
curl -s -X POST 127.0.0.1:8091/v1/tts -H 'Content-Type: application/json' -d "$T" -o bench.wav
ls -l bench.wav
```
✅ Expect: `bench.wav` of about 400–500 KB (8–10 s).

AVTR-1 alone, 30 s (the first start registers the photo; loading takes 1–2 min):
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose run --rm --no-deps cjap-avatar python avatar_bench.py avtr1 /avatar/bench.wav 30 | tail -8
```
✅ Expect: `avtr1: loaded in …`; **`chunk time: median … ms, p95 … ms`** with **p95 under 200 ms** (aim: median under 170); **`engine fps ≥ 25`**; `start lag per clip (s):` values around 0.3–0.6; `speaking frames: … mean … ms each` under 40 ms; `worst frame gap` under 0.25 s (the engine works 5 frames at a time; the live server smooths this).

AVTR-1 while the voice bench runs three times alongside:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark
( for i in 1 2 3; do python3 tts/tts_bench.py > /dev/null; done ) &
cd avatar
docker compose run --rm --no-deps cjap-avatar python avatar_bench.py avtr1 /avatar/bench.wav 30 | tail -8
wait
```
✅ Expect: **p95 chunk time under 200 ms** and **`engine fps ≥ 25`** again.

**Look and listen:** join the video and its audio, and watch it on the laptop:
```bash
cd ~/robot/avatar/bench
B=bench_avtr1
ffmpeg -y -loglevel error -i $B.mp4 -i $B.wav -c:v libx264 -c:a aac -shortest avtr1_check.mp4
ls -l avtr1_check.mp4
```
```powershell
scp isl.spark:robot/avatar/bench/avtr1_check.mp4 ~/Downloads/
```
✅ Expect (your judgement): the face is recognisably the portrait, on the background; the lips match the words; between sentences the head idles and blinks; no flicker or tearing around the hair.

Over 200 ms or under 25 fps → step X11, *AVTR-1 too slow* (settings first, then the Wav2Lip fallback). Bad quality → *Face looks wrong*.

---

## X8. Gate X3: live with AVTR-1

Make the avatar part of robot mode (so `sv-robot on` starts it), and start it now:
```bash
touch ~/robot/avatar/enabled
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose up -d
H=127.0.0.1:8092/health
for i in $(seq 60); do curl -s $H | grep -q '"ok":true' && break; sleep 5; done
curl -s $H; echo
docker logs sv-avatar-cjap-avatar-1 2>&1 | grep -E 'listen|ready' | tail -3
```
✅ Expect: `"ok":true`, `"engine":"avtr1"`, `"size":[1280,720]` (loading takes 1–2 min: engines plus the photo's registration); the log shows `engine avtr1 1280x720 ready in …` and **no** `listen: … listening to silence` line (that line means the mic couldn't be shared: step X11, *Face doesn't listen*).

On the **display laptop**: reload `/face-avatar`, click once; then on `/maintain` press **Voice: avatar** (again: a reload resets it). In the room, with the robot:
1. **"Hi Cee-Jap" … "What is the rule of law?"** ✅ While you ask, the face reacts (small nods, attention); then it speaks the answer from the monitor, the lips match, the robot is silent and moving.
2. **"Tell me about your mentor."** (follow-up) ✅ The same.
3. Between answers: ✅ the face idles and blinks (or shows the still portrait once the page parks).
4. During an answer, press **Interrupt** on `/maintain`. ✅ The voice stops at once; the mouth settles within about half a second.
5. During another answer, say **"Cee-Jap"** (the stop phrase). ✅ It stops. If instead answers stop by themselves → step X11, *Self-interrupt*.

```bash
curl -s 127.0.0.1:8092/health; echo
journalctl -u supervaise --since "-10 min" --no-pager | grep -E '[[](trace|avatar)' | tail -8
```
✅ Expect: `"engine_fps"` about 25 (the publish rate), `"error": null`; `[trace]` lines for your questions. The page's status line shows the measured start lag (about 0.5–0.9 s with AVTR-1).

---

## X9. Back to office mode
```bash
sudo -v
```

```bash
sv-robot off
docker ps -a --format '{{.Names}} {{.Status}}' | grep -E 'sv-avatar|vllm'
```
✅ Expect: `robot mode OFF.`; both `sv-avatar-…` containers `Exited`; `sv-llm-vllm-1` coming back to `healthy` within ~5 min. From now on `sv-robot on` starts the avatar too (because `~/robot/avatar/enabled` exists).

---

## X10. Daily use

| Task | How |
|---|---|
| Robot + avatar on / off | `sv-robot on` · `sv-robot off` (the avatar starts with robot mode while `~/robot/avatar/enabled` exists; `rm` it to run without the face) |
| Show the face | display laptop: `http://192.168.1.201:8180/face-avatar?key=…`, click once, F11; `/maintain` → Voice: **avatar** |
| Avatar state | `curl -s 127.0.0.1:8092/health` · `docker logs sv-avatar-cjap-avatar-1 --tail 30` |
| New portrait | X5 again, then `docker compose restart cjap-avatar` in `deploy/spark/avatar` |
| New background | `AVATAR_BG` in `deploy/spark/avatar/docker-compose.yml` (X5 lists the names), then `docker compose up -d` |
| Faster, or calmer | `AVATAR_AVTR1_STEPS` (5 → 4 is faster), `AVATAR_CFG_SELF` / `AVATAR_CFG_OTHER` (2.0 → 1.5 is calmer speaking / listening) in `docker-compose.yml`, then `docker compose up -d` |
| No listening | `AVATAR_LISTEN_PCM: ""` in `docker-compose.yml`, then `docker compose up -d` |
| Test the plumbing only | `AVATAR_ENGINE=still docker compose up -d` in `deploy/spark/avatar` |

---

## X11. Incidents, and the Wav2Lip fallback

| Row | Symptom | Cause and fix |
|---|---|---|
| **TensorRT apt version** | X3 build: `Version '10.14.1.48-1+cuda13.0' for 'libnvinfer10' was not found` | The CUDA repo names it differently. `docker run --rm nvidia/cuda:13.0.2-devel-ubuntu24.04 bash -c "apt-get update -qq; apt-cache madison libnvinfer-dev"` lists the versions; pick the `10.14.1…cuda13.0` string and build with `docker compose build --build-arg TRT_DEB=<that string> cjap-avatar` |
| **Plugin build** | CMake or nvcc errors in the `gs3d` step | Read the first error. `NvInfer.h: No such file` → the TensorRT headers didn't install (row above). `sm_121` unknown → the CUDA image is older than 13.0 |
| **ONNX Runtime without CUDA** | X3 lists only `CPUExecutionProvider`, or X7 fails registering the photo | `docker run --rm --gpus all sv/cjap-avatar:1 python -c "import torch, onnxruntime as o; print(torch.cuda.is_available(), o.get_device())"`: `True GPU` is required. A missing `libcudnn`/`libcublas` in the log → the `onnxruntime-gpu[cuda,cudnn]` extras didn't install; rebuild with `docker compose build --no-cache cjap-avatar` |
| **Weights refused** | X4: `GatedRepoError`, `401` or `403` | The licence isn't accepted for the account that made the token (X0 step 1), or the token is wrong: redo X0's browser steps and X2's token block |
| **Warp engine** | X4: `Plugin not found GridSample3D`, or `warp` fails | The x86 plugin is in place: `ls -l ~/models/avtr1/main/renderer_runtime_artifacts/*.so` shows 1820592 bytes. Re-run X4's `cp` line, then `docker run $G $I python /opt/avtr1/scripts/build_renderer_engines.py warp` (with `I` and `G` as in X4) |
| **AVTR-1 export** | X4: the AVTR-1 step fails inside `torch.onnx.export` | torch 2.11's legacy exporter rejected AVTR-1's TorchScript model. The section *Only if X4's AVTR-1 export fails* below builds just those two engines with an older torch |
| **LiveKit not reached** | X1: the page says `LiveKit connect failed`, or stays on the portrait | The laptop must be on 192.168.1.x (`ipconfig` on it). On the Spark: `ss -tln \| grep 7880`, `ss -uln \| grep 7882`, `docker logs sv-avatar-livekit-1 --tail 20`. A VPN or a guest Wi-Fi on the laptop blocks it |
| **Voice from the robot** | Both the robot and the monitor speak | `/maintain` voice mode isn't **avatar** (it's per page load: set it after opening `/face-avatar`) |
| **No sound on the monitor** | The face moves, silence | Click once on the page (autoplay); the laptop's output device is the monitor; the page's audio isn't muted (voice mode avatar) |
| **Self-interrupt** | Answers stop by themselves while the face speaks | The robot's mic hears the monitor and takes its voice for the stop phrase. Turn the monitor's speakers away and lower them; if it persists, `cjap-env-set CJ_STOP_WORD_ENABLED 0` then `sudo systemctl restart supervaise` (the Interrupt button on `/maintain` still works) |
| **Face doesn't listen** | X8 log: `listen: arecord … ended …; listening to silence` | The container couldn't share the mic. The error text says why: `No such file or directory` for `/dev/snd` → the robot's USB isn't connected; `Permission denied` → `sv` isn't in `audio` (X0); `Unknown PCM` → `~/.asoundrc` isn't the base runbook's. The face still idles; CJAP is unaffected |
| **Face reacts to itself** | The face keeps "listening" right after it speaks | The monitor is loud at the robot. Lower and turn the speakers; or `AVATAR_LISTEN_GAIN: "0.5"` in `docker-compose.yml`, then `docker compose up -d` |
| **Session refused** | The page: `a LiveAvatar session is already live on another page` | CJAP allows one avatar page at a time. Close the other tab (or wait 25 s after closing it) |
| **Avatar not valid on /maintain** | `invalid API key` / `avatar not found` | `liveavatar.json` and `avatar.env` disagree: redo X2's first block (it rewrites both, and the LiveKit secret), then in `deploy/spark/avatar` `docker compose up -d --force-recreate` and `sudo systemctl restart pi-dashboard` |
| **Face looks wrong** | Distorted face, odd crop, halo around the hair, exaggerated mouth | A frontal, evenly lit photo with the whole head (X5); `prepare_photo.py` prints what it found. A halo: a background closer to the photo's own colours (`AVATAR_BG`). Exaggerated motion: `AVATAR_CFG_SELF: "1.5"` (speaking) or `AVATAR_CFG_OTHER: "1.5"` (listening), then `docker compose up -d` |
| **No face found** | X7 or X8: `RuntimeError: No face detected in source image.` | AVTR-1's detector didn't find the face in `portrait.png`: a larger, frontal photo, then X5 again |
| **AVTR-1 too slow** | Gate X2: p95 chunk time over 200 ms, or under 25 fps | In order: (1) `nvidia-smi`: nothing else heavy on the GPU (Qwen stopped?); (2) `AVATAR_AVTR1_STEPS: "4"`, then `"3"`, re-run the bench; (3) a 960×540 frame: X5 with `prepare_photo.py /avatar/source.jpg /avatar/portrait.png 960 540`, and `AVATAR_W: "960"`, `AVATAR_H: "540"` in `docker-compose.yml`; (4) the Wav2Lip fallback below, **internal tests only** |
| **Avatar unhealthy** | `/health` `"ok": false` with an `error` | `docker logs sv-avatar-cjap-avatar-1 --tail 50`: the first traceback says which engine; `docker compose restart cjap-avatar`; repeating → the TensorRT engines (X4) or the photo (X5) |
| **Face lags the voice** | Lips late vs sound in the browser | Rare with one stream. The engine is too slow (row above): `docker logs sv-avatar-cjap-avatar-1` for errors, `/health` `"engine_fps"` under 25 |

### Only if X4's AVTR-1 export fails: export with torch 2.8

Builds only the two AVTR-1 engines and its normalizer, with torch 2.8 in a throwaway folder (about 4 GB, deleted after). The renderer and HuBERT engines from X4 stay.
```bash
cd ~/models
I=sv/cjap-avatar:1
G="--rm -u 1001:1001 --gpus all -v $PWD:/models"
T=/models/torch28
U=https://download.pytorch.org/whl/cu129
docker run $G $I pip install -q --target $T torch==2.8.0 --index-url $U
A=/opt/avtr1/scripts/build_avtr1_engines.py
docker run $G -e PYTHONPATH=$T:/opt/avtr1/src $I python $A 2>&1 | tail -8
rm -rf ~/models/torch28
ls ~/models/avtr1/main/speech2motion_runtime_artifacts_cc
```
✅ Expect: the export ends without a traceback; `avtr1_decode_fp16.engine`, `avtr1_encode_fp16.engine`, `hubert_lbs_fp16.engine`. Then continue at X5.

### Only if Gate X2 fails: the Wav2Lip fallback (internal tests only)

**Not for a public exhibit:** Wav2Lip is licensed for non-commercial research only, and the 256 weights LiveTalking distributes have no licence. It lip-syncs only the mouth over an 8 s base clip of the portrait, which AVTR-1 makes once (offline; speed doesn't matter for that).

1. On the laptop, download `wav2lip256.pth` from LiveTalking's model folder (`https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ`) to `~/Downloads`, then: `scp ~/Downloads/wav2lip256.pth isl.spark:models/wav2lip/` (after `ssh isl.spark mkdir -p models/wav2lip`).
2. On the Spark, in `~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar`:
   - the base clip: `docker compose run --rm --no-deps cjap-avatar python make_base_video.py /avatar/base 8`
   - its face crops (downloads the S3FD face detector on first use): `docker compose run --rm --no-deps cjap-avatar python prepare_wav2lip.py /avatar/base /avatar/wav2lip`
   - the speed check: `docker compose run --rm --no-deps cjap-avatar python avatar_bench.py wav2lip /avatar/bench.wav 30` (read the `speaking frames … ms each` line: under 40 ms)
   - use it: `AVATAR_ENGINE=wav2lip docker compose up -d`, and in `docker-compose.yml` change `${AVATAR_ENGINE:-avtr1}` to `${AVATAR_ENGINE:-wav2lip}` so `sv-robot on` keeps it.
3. Back to AVTR-1: `AVATAR_ENGINE=avtr1 docker compose up -d` and the default back to `avtr1`.

---

## X12. Teardown

The base setup stays; this removes only the avatar:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose down
docker image rm sv/cjap-avatar:1 livekit/livekit-server:v1.13.11
rm -f ~/robot/avatar/enabled ~/robot/avatar/hf.token
rm -f ~/Supervaise-Reachy-Mini-Project-main/dashboard/assets/liveavatar.json
```
Optional, the data (the portrait is a person's likeness): `~/robot/avatar`, `~/models/avtr1`, `~/models/wav2lip`. Revoke the HuggingFace token at `https://huggingface.co/settings/tokens`. To return to the base branch: `git checkout spark/local-speech`, then base runbook step 2's unit install (the dashboard unit without `CJ_LIVEAVATAR_URL`) and `install -m 755 deploy/spark/bin/sv-robot ~/bin/`.
