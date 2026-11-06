# Runbook: CJAP on the DGX Spark, with a video avatar (alternative version)

> **For:** you, as `sv`, over `ssh isl.spark`, plus owner steps that need your sudo password (🔑). **Design:** [`CJAP_SPARK_AVATAR_ARCHITECTURE.md`](AVATAR_ARCHITECTURE.md).
> **What you get:** everything the base runbook gives (CJAP on the Spark, Reachy Mini Lite, Whisper, the local voice) **plus a lip-synced face of Justice Panganiban** from Ditto on the Spark's GPU, shown by CJAP's own `/face-avatar` page on a display laptop next to the robot, with the voice from the monitor's speakers.
> **How to use:** **Part 1** is the base runbook, unchanged. **Part 2** (steps X0–X9) adds the avatar: run its blocks in order and compare with **✅ Expect**. Fixes are only in step X11. A block that is only `sudo -v` asks for your password before the next block.
> **The code** is on CJAP branch **`spark/video-avatar`** (`spark/local-speech` plus one commit), in the bundle `cjap-spark/cjap-spark-video-avatar.bundle` until it is pushed.
> **Licences:** Ditto's face-analysis models are non-commercial (InsightFace) or unclear upstream; the Wav2Lip fallback is non-commercial. Fine for building and testing; check with counsel before a public exhibit (architecture §9).

| Step | What | Where | Time |
|---|---|---|---|
| Part 1 | Base runbook steps 0–9 (CJAP, robot, voice) through Gate E | sv + robot | 2–3 h |
| X0 | Check (read only) | sv | 2 min |
| X1 | 🔑 The avatar branch, dashboard unit, tests | laptop + sv | 5 min |
| X2 | Keys and config | sv | 3 min |
| X3 | Build `sv/cjap-avatar:1` (TensorRT, plugin, Ditto, LiveKit) | sv | 30–60 min |
| X4 | Ditto models and TensorRT engines | sv | 20–40 min |
| X5 | The portrait | laptop + sv | 5 min |
| X6 | Gate X1: the plumbing with the `still` engine | sv + display laptop | 15 min |
| X7 | Gate X2: Ditto speed (alone and with the voice running) | sv + laptop | 15 min |
| X8 | Gate X3: live with Ditto | robot + display laptop | 20 min |
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
```
✅ Expect: `mode: office` or `robot`; `avatar-ports-free`; `udp-free`; `sv/cjap-tts:1`; ≥ 40 GB available.

You also need:
- a **display laptop or mini-PC** with Chrome or Edge, **on the same LAN as the Spark** (192.168.1.x), with internet (the page loads LiveKit's browser library from a CDN), and an HDMI monitor with speakers;
- the **portrait photo** (front-facing, even light, face ≥ 512 px, the subject's consent) in `~/Downloads` on your laptop.

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
git fetch ~/cjap-spark-video-avatar.bundle spark/video-avatar:spark/video-avatar
git checkout spark/video-avatar
git log --oneline -2
```
✅ Expect: `git status` prints nothing (no local edits); `… is okay`; `Switched to branch 'spark/video-avatar'`; the log starts with `Spark: a local video avatar in place of HeyGen LiveAvatar`.

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
- `… passed` with **no** `failed`; the server-contract test shows as `skipped` if CJAP's venv has no FastAPI (it ran in the branch's own checks).

---

## X2. Keys and config

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

---

## X3. Build `sv/cjap-avatar:1`

One image for building the engines and running: CUDA 13.0 devel, TensorRT 10.14.1, the GridSample3D plugin compiled for the GB10 (sm_121), Ditto (pinned, two patches), LiveTalking (for the fallback only), LiveKit's Python SDK, the server.
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose build cjap-avatar 2>&1 | tail -5
I=sv/cjap-avatar:1
docker run --rm --gpus all $I python -c "import tensorrt as t; print('trt', t.__version__)"
docker run --rm $I ls -l /opt/libgrid_sample_3d_plugin.so
docker run --rm $I grep -i -E '^(torch|tensorrt|livekit|numpy)' versions.txt
```
✅ Expect:
- the build ends with `naming to docker.io/sv/cjap-avatar:1` (30–60 min the first time);
- `trt 10.14.1.48…`;
- the plugin file, a few hundred KB;
- among them `torch==2.11.0…`, `tensorrt…10.14.1…`, `livekit==1.2.1`, `numpy==2.…`.

An `apt` error about `libnvinfer…` versions → step X11, *TensorRT apt version*. A CMake/nvcc error → *Plugin build*.

---

## X4. Ditto models and TensorRT engines

The published ONNX models and configs (about 2 GB), then the TensorRT engines built for this GPU (the published engines are x86 and TensorRT 8.6):
```bash
cd ~/models
I=sv/cjap-avatar:1
R="--rm -u 1001:1001 -e HF_HUB_OFFLINE=0 -v $PWD:/models"
M=digital-avatar/ditto-talkinghead
docker run $R $I hf download $M --include "ditto_onnx/*" --local-dir /models/ditto
docker run $R $I hf download $M --include "ditto_cfg/*" --local-dir /models/ditto
ls ~/models/ditto/ditto_onnx | head -20
ls ~/models/ditto/ditto_cfg
```
✅ Expect: ONNX files (`appearance_extractor…`, `lmdm…`, `warp_network…`, `hubert.onnx`, …) and `libgrid_sample_3d_plugin.so` (the x86 one); in `ditto_cfg`, `v0.4_hubert_cfg_trt_online.pkl` among others.

Swap in the arm64 plugin and build the engines (the GPU does this; 10–30 min):
```bash
cd ~/models/ditto/ditto_onnx
mv libgrid_sample_3d_plugin.so libgrid_sample_3d_plugin.so.x86
cd ~/models
I=sv/cjap-avatar:1
G="--rm -u 1001:1001 --gpus all -v $PWD:/models"
docker run $G $I cp /opt/libgrid_sample_3d_plugin.so /models/ditto/ditto_onnx/
O=/models/ditto
C="python scripts/cvt_onnx_to_trt.py"
docker run $G -w /opt/ditto $I $C --onnx_dir $O/ditto_onnx --trt_dir $O/ditto_trt_spark | tail -15
ls -l ~/models/ditto/ditto_trt_spark
```
✅ Expect: the converter prints one `polygraphy convert …` line per model and ends without `Error`; `ditto_trt_spark` holds one `.engine` file per model (12). A warp-network error about `GridSample3D` → step X11, *Engine conversion*.

---

## X5. The portrait

On the **laptop** (PowerShell; use your file's name):
```powershell
scp ~/Downloads/portrait.jpg isl.spark:robot/avatar/source.jpg
```
On the **Spark**: a square 720×720 crop around the face:
```bash
I=sv/cjap-avatar:1
cd ~/robot/avatar
R="--rm -u 1001:1001 -v $PWD:/avatar"
docker run $R $I python prepare_photo.py /avatar/source.jpg /avatar/portrait.jpg 720
```
✅ Expect: `… -> /avatar/portrait.jpg 720x720 (face …)`. A `WARNING: the face region is under 512 px` means a larger photo would look sharper.

Check the crop on the **laptop**:
```powershell
scp isl.spark:robot/avatar/portrait.jpg ~/Downloads/portrait_check.jpg
```
✅ Expect: the face centred, the whole head and some shoulder visible, eyes open, mouth closed.

---

## X6. Gate X1: the plumbing with the `still` engine

Before Ditto, prove the path with the `still` engine (the photo, our audio passed through, no lip motion): the dashboard's session calls, LiveKit across the LAN, the control socket, the lag loop and the voice mode.

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
✅ Expect: `robot mode ON.` (as in the base runbook); `/health` with `"ok":true`, `"engine":"still"`, `"size":[720,720]`; `sv-avatar-livekit-1` and `sv-avatar-cjap-avatar-1` both `Up`.

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

## X7. Gate X2: Ditto speed

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

Ditto alone, 30 s:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose run --rm --no-deps cjap-avatar python avatar_bench.py ditto /avatar/bench.wav 30 | tail -7
```
✅ Expect: `ditto: loaded in …`; **`engine fps ≥ 25`** (aim ≥ 28); `start lag per clip (s):` values around 1.1–1.4; `speaking frames: … mean … ms each` under 40 ms; `worst frame gap` under 0.2 s.

Ditto while the voice bench runs three times alongside:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark
( for i in 1 2 3; do python3 tts/tts_bench.py > /dev/null; done ) &
cd avatar
docker compose run --rm --no-deps cjap-avatar python avatar_bench.py ditto /avatar/bench.wav 30 | tail -7
wait
```
✅ Expect: **`engine fps ≥ 25`** again.

**Look and listen:** join the video and its audio, and watch it on the laptop:
```bash
cd ~/robot/avatar/bench
B=bench_ditto
ffmpeg -y -loglevel error -i $B.mp4 -i $B.wav -c:v libx264 -c:a aac -shortest ditto_check.mp4
ls -l ditto_check.mp4
```
```powershell
scp isl.spark:robot/avatar/bench/ditto_check.mp4 ~/Downloads/
```
✅ Expect (your judgement): the face is recognisably the portrait; the lips match the words; between sentences the head idles and blinks; no flicker or tearing.

Under 25 fps → step X11, *Ditto too slow* (settings first, then the Wav2Lip fallback). Bad quality → *Ditto looks wrong*.

---

## X8. Gate X3: live with Ditto

Make the avatar part of robot mode (so `sv-robot on` starts it), and start it now:
```bash
touch ~/robot/avatar/enabled
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose up -d
H=127.0.0.1:8092/health
for i in $(seq 60); do curl -s $H | grep -q '"ok":true' && break; sleep 5; done
curl -s $H; echo
```
✅ Expect: `"ok":true`, `"engine":"ditto"`, `"size":[720,720]` (loading takes 1–3 min: engines plus the photo's registration).

On the **display laptop**: reload `/face-avatar`, click once; then on `/maintain` press **Voice: avatar** (again: a reload resets it). In the room, with the robot:
1. **"Hi Cee-Jap" … "What is the rule of law?"** ✅ The face speaks the answer from the monitor, the lips match, the robot is silent and moving.
2. **"Tell me about your mentor."** (follow-up) ✅ The same.
3. Between answers: ✅ the face idles and blinks (or shows the still portrait once the page parks).
4. During an answer, press **Interrupt** on `/maintain`. ✅ The voice stops at once; the mouth settles within about a second.
5. During another answer, say **"Cee-Jap"** (the stop phrase). ✅ It stops. If instead answers stop by themselves → step X11, *Self-interrupt*.

```bash
curl -s 127.0.0.1:8092/health; echo
journalctl -u supervaise --since "-10 min" --no-pager | grep -E '[[](trace|avatar)' | tail -8
```
✅ Expect: `"engine_fps"` about 25 (the publish rate), `"error": null`; `[trace]` lines for your questions. The page's status line shows the measured start lag (about 1.1–1.5 s with Ditto).

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
| Faster or calmer | `AVATAR_DITTO_STEPS` (10 → 8 is faster), `AVATAR_DITTO_OVERLAP` (70 → 75 halves the start lag, costs speed) in `deploy/spark/avatar/docker-compose.yml`, then `docker compose up -d` |
| Test the plumbing only | `AVATAR_ENGINE=still docker compose up -d` in `deploy/spark/avatar` |

---

## X11. Incidents, and the Wav2Lip fallback

| Row | Symptom | Cause and fix |
|---|---|---|
| **TensorRT apt version** | X3 build: `Version '10.14.1.48-1+cuda13.0' for 'libnvinfer10' was not found` | The CUDA repo names it differently. `docker run --rm nvidia/cuda:13.0.2-devel-ubuntu24.04 bash -c "apt-get update -qq; apt-cache madison libnvinfer-dev"` lists the versions; pick the `10.14.1…cuda13.0` string and build with `docker compose build --build-arg TRT_DEB=<that string> cjap-avatar` |
| **Plugin build** | CMake or nvcc errors in the `gs3d` step | Read the first error. `NvInfer.h: No such file` → the TensorRT headers didn't install (row above). `sm_121` unknown → the CUDA image is older than 13.0 |
| **Engine conversion** | X4: `Plugin not found GridSample3D` or `Network must have at least one output` for `warp_network` | The x86 plugin was still in `ditto_onnx` (check `ls -l ~/models/ditto/ditto_onnx/*.so*`: the arm64 one is the newer file). Re-run the `cp` and converter lines |
| **cuda bindings** | `ImportError` around `cuda.bindings` | `docker run --rm sv/cjap-avatar:1 grep -n 'from cuda' /opt/ditto/core/utils/tensorrt_utils.py` must show `from cuda.bindings import driver as cuda, runtime as cudart, nvrtc`. If cuda-python changed layout again, rebuild with `cuda-python` pinned to the version in `versions.txt` that worked |
| **LiveKit not reached** | X1: the page says `LiveKit connect failed`, or stays on the portrait | The laptop must be on 192.168.1.x (`ipconfig` on it). On the Spark: `ss -tln \| grep 7880`, `ss -uln \| grep 7882`, `docker logs sv-avatar-livekit-1 --tail 20`. A VPN or a guest Wi-Fi on the laptop blocks it |
| **Voice from the robot** | Both the robot and the monitor speak | `/maintain` voice mode isn't **avatar** (it's per page load: set it after opening `/face-avatar`) |
| **No sound on the monitor** | The face moves, silence | Click once on the page (autoplay); the laptop's output device is the monitor; the page's audio isn't muted (voice mode avatar) |
| **Self-interrupt** | Answers stop by themselves while the face speaks | The robot's mic hears the monitor and takes its voice for the stop phrase. Turn the monitor's speakers away and lower them; if it persists, `cjap-env-set CJ_STOP_WORD_ENABLED 0` then `sudo systemctl restart supervaise` (the Interrupt button on `/maintain` still works) |
| **Session refused** | The page: `a LiveAvatar session is already live on another page` | CJAP allows one avatar page at a time. Close the other tab (or wait 25 s after closing it) |
| **Avatar not valid on /maintain** | `invalid API key` / `avatar not found` | `liveavatar.json` and `avatar.env` disagree: redo X2 (it rewrites both, and the LiveKit secret), then in `deploy/spark/avatar` `docker compose up -d --force-recreate` and `sudo systemctl restart pi-dashboard` |
| **Ditto looks wrong** | Distorted face, odd crop, wandering head | A frontal, evenly lit photo with the whole head (X5). The crop: `prepare_photo.py` prints what it found. Calmer head motion: in `engines/ditto.py`'s `setup(...)` add `overall_ctrl_info` deltas or `use_d_keys=("exp",)` (expression only, head still), then rebuild the image |
| **Ditto too slow** | Gate X2 below 25 fps | In order: (1) `nvidia-smi`: nothing else heavy on the GPU (Qwen stopped?); (2) `AVATAR_DITTO_STEPS: "8"`, then `"6"`, re-run the bench; (3) a 512×512 portrait (`prepare_photo.py … 512`); (4) the Wav2Lip fallback below, **internal tests only** |
| **Avatar unhealthy** | `/health` `"ok": false` with an `error` | `docker logs sv-avatar-cjap-avatar-1 --tail 50`: a Ditto worker error (`worker_exception`) needs `docker compose restart cjap-avatar`; repeating → the TensorRT engines (X4) or the photo (X5) |
| **Face lags the voice** | Lips late vs sound in the browser | Rare with one stream. `docker logs sv-avatar-cjap-avatar-1` for `behind schedule`: the engine is under 25 fps (row above) |

### Only if Gate X2 fails: the Wav2Lip fallback (internal tests only)

**Not for a public exhibit:** Wav2Lip is licensed for non-commercial research only, and the 256 weights LiveTalking distributes have no licence. It lip-syncs only the mouth over an 8 s base clip of the portrait, which Ditto makes once (offline; speed doesn't matter for that).

1. On the laptop, download `wav2lip256.pth` from LiveTalking's model folder (`https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ`) to `~/Downloads`, then: `scp ~/Downloads/wav2lip256.pth isl.spark:models/wav2lip/` (after `ssh isl.spark mkdir -p models/wav2lip`).
2. On the Spark, in `~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar`:
   - the base clip: `docker compose run --rm --no-deps cjap-avatar python make_base_video.py /avatar/base 8`
   - its face crops (downloads the S3FD face detector on first use): `docker compose run --rm --no-deps cjap-avatar python prepare_wav2lip.py /avatar/base /avatar/wav2lip`
   - the speed check: `docker compose run --rm --no-deps cjap-avatar python avatar_bench.py wav2lip /avatar/bench.wav 30` (read the `speaking frames … ms each` line: under 40 ms)
   - use it: `AVATAR_ENGINE=wav2lip docker compose up -d`, and in `docker-compose.yml` change `${AVATAR_ENGINE:-ditto}` to `${AVATAR_ENGINE:-wav2lip}` so `sv-robot on` keeps it.
3. Back to Ditto: `AVATAR_ENGINE=ditto docker compose up -d` and the default back to `ditto`.

---

## X12. Teardown

The base setup stays; this removes only the avatar:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main/deploy/spark/avatar
docker compose down
docker image rm sv/cjap-avatar:1 livekit/livekit-server:v1.13.11
rm -f ~/robot/avatar/enabled
rm -f ~/Supervaise-Reachy-Mini-Project-main/dashboard/assets/liveavatar.json
```
Optional, the data (the portrait is a person's likeness): `~/robot/avatar`, `~/models/ditto`, `~/models/wav2lip`. To return to the base branch: `git checkout spark/local-speech`, then base runbook step 2's unit install (the dashboard unit without `CJ_LIVEAVATAR_URL`) and `install -m 755 deploy/spark/bin/sv-robot ~/bin/`.
