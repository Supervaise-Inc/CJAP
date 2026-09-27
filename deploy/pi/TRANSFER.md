# Moving CJAP to another Reachy Mini

Two things move: the **public repo** (code, models, clips, units, tuning —
branch `pi/deployment-snapshots`) and one **encrypted private bundle** (API
keys, certs, HeyGen key, voice print, optionally the clip cache) that the
repo must never contain. Total hands-on time ≈ 20 min; `install.sh` runs
10–15 min unattended on a CM4.

Repo: `https://github.com/Supervaise-Inc/CJAP.git` (the old
`KennChristian/Neto` URL redirects there).

## 0. Prerequisites on the NEW robot

- Stock Reachy Mini image (Debian 13, user `pollen`, `/venvs/mini_daemon`
  with `reachy_mini` 1.9.x, `reachy-mini-daemon` running).
- XMOS mic firmware ≥ 2.1.0 (needed for direction-of-arrival). Check:
  `/venvs/mini_daemon/bin/python /venvs/mini_daemon/lib/python3.12/site-packages/reachy_mini/media/audio_control_utils.py VERSION`
  → `VERSION: [0, 2, 1, x]` is fine.
- Internet on the new robot (WiFi via the Reachy setup flow, or Ethernet).
- Note its address: `hostname -I` / `<hostname>.local`.

## 1. On the OLD robot (reference) — push code, pack secrets

```bash
snapshot-push.sh                       # live system -> repo branch snapshot/<ts> + pi/deployment-snapshots
export-private.sh --with-cache         # asks for a passphrase; writes ~/backups/private-<host>-<ts>.tar.gz.enc
#   drop --with-cache for a ~10 KB bundle (keys only); with it, ~400 MB and the
#   ~150 canned/event answers play instantly on the new robot with no ElevenLabs spend
scp "$(ls -t ~/backups/private-*.tar.gz.enc | head -1)" pollen@<new-robot>.local:~/   # newest bundle only
```

## 2. On the NEW robot — install

Clone the current release TAG, not the `pi/deployment-snapshots` branch — tags are immutable, so a
robot installed from one never moves under it (`deploy/pi/install.sh`'s own top comment names the
current tag; check there if a newer release has since shipped).

```bash
git clone -b release/kb-v2-2026-09-27 https://github.com/Supervaise-Inc/CJAP.git \
    ~/Supervaise-Reachy-Mini-Project-main
cd ~/Supervaise-Reachy-Mini-Project-main
bash deploy/pi/install.sh              # apt, venv (exact pins), models, clips, dotfiles,
                                       # PipeWire realtime fix, dashboard + cert, units, hotspot
~/bin/import-private.sh "$(ls -t ~/private-*.tar.gz.enc | head -1)"   # same passphrase; restores .env,
                                                # voice/config.py, certs, liveavatar.json, enrolled.npz, (.voice_cache)
# optional: keep the old robot's name/URLs (only if the old robot is OFF or renamed —
# two "reachy-cjap" on one LAN makes mDNS call the second one reachy-cjap-2.local)
sudo hostnamectl set-hostname reachy-cjap && sudo sed -i 's/^127\.0\.1\.1.*/127.0.1.1\treachy-cjap/' /etc/hosts
sudo reboot                                     # once — the PipeWire realtime limits need a fresh session
```

## 3. After the reboot — verify

```bash
verify.sh          # 24 checks: services, keys, models, clips, PipeWire fix, XMOS fw, DoA, venv, 3 APIs, journal
```
All PASS → say **"Hi Cee-Jap"** and ask a question. Then open
`http://<hostname>.local:8080/maintain?key=cjap` and check the Providers
chips are green and the wake meter moves when you talk.

## 4. Things that are robot-specific (re-do by hand)

| What | Why | How |
|---|---|---|
| Bluetooth speakers | pairings live in the OS, and `audio-out sony/marshall` are pinned to the reference speakers' MACs | pair from `/maintain` → Bluetooth card; then `audio-out sony`. Different speakers: put the MACs in `~/bin/audio-out.local` (survives `install.sh` re-runs; `~/bin/audio-out` itself is regenerated) |
| WiFi networks | NetworkManager profiles are not exported | Reachy setup flow or `/maintain` → WiFi card; the `ReachySetup` fallback hotspot is created by install.sh |
| Voice lock enrolment | `enrolled.npz` is restored by the bundle; re-enrol if a different person will host | `/maintain` → Enroll |
| Speaker turn direction (DoA) | head yaw sign is assumed | stand to the robot's LEFT, say "Cee-Jap"; if it turns right: `printf '[Service]\nEnvironment=CJ_DOA_FLIP=1\n' \| sudo tee /etc/systemd/system/supervaise.service.d/local.conf && sudo systemctl daemon-reload && sudo systemctl restart supervaise`. Any robot-specific tuning goes in that `local.conf` — `install.sh` re-runs rewrite `wakeword.conf` but never `local.conf` |
| XMOS chip tuning | AEC/NS values are chip-runtime and reset on power cycle (both robots run stock values) | nothing to do |
| Event mode | the flag file `data/entities/event_mode.on` is runtime state, not in the repo — a new robot starts with event mode OFF | turn it on from `/event` or `/maintain` before the event |

## 5. Rollback / restore points

Every push makes a `snapshot/YYYY-MM-DD-HHMM` branch. To put a robot back:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main && git fetch && git checkout snapshot/2026-08-25-1813
bash deploy/pi/install.sh && sudo systemctl restart supervaise pi-dashboard
```

## 6. Keeping two robots in sync afterwards

Reference robot: `snapshot-push.sh` after changes. Other robot:
```bash
cd ~/Supervaise-Reachy-Mini-Project-main && git pull && bash deploy/pi/install.sh
sudo systemctl restart supervaise pi-dashboard
```
`install.sh` never overwrites `.env`, `voice/config.py`, `.asoundrc.route`,
certs or clips already present.

## 7. Refreshing the corpus/model data only (`deploy/pi/bundle/`)

Everything above moves a *whole robot* (code, models, clips, units — a fresh `git clone` of
`pi/deployment-snapshots`). Phase 7 (batch-04) added a second, smaller thing that moves on its own: the
**data bundle**, `deploy/pi/bundle/` — the corpus, the search indexes and the sentence encoder that the
new deterministic retrieval pipeline (`app/service.py` + `app/retrieval.py`) reads. Built by
`scripts/build_robot_bundle.py` on `deliverable/2026-09`; see its MANIFEST.md for exactly what is in it
and why, and `batch-04/BATCH-04_REPORT.md` for the full reasoning.

**Read this before using it (Phase 8 finding; closed by Phase 10 — kept for the record).**
`app/service.py` was committed on `deliverable/2026-09` but, at the time, existed on neither that branch
nor `pi/deployment-snapshots` in a place `install.sh` could reach: `install.sh` cloned
`pi/deployment-snapshots`, which had none of the five retrieval modules at all. Phase 8 added
`config.CJ_PIPELINE` (`legacy` | `retrieval`, default **`legacy`**) so the new path was reachable and
testable without flipping what's live, and §8 below documents the stopgap that existed in the meantime.
**Phase 10 closed the actual gap**: `install.sh` now clones the immutable tag `release/kb-v2-2026-09-27`
(see its top comment for the current one), cut from `deliverable/2026-09`, which carries all five
modules — a normal `install.sh` run today delivers them. §8's manual-`rsync` stopgap is no longer
needed for a *fresh* install; it may still help temporarily patching an *already-provisioned* robot
between releases. `legacy` still remains what a normal `install.sh` clone runs — Phase 10 shipped the
code, not a default-behaviour change.

Size: **516 MB, 1,315 files** (1,290 corpus document cards, the chunk store, the topic map and voice
files, the dense/sparse/centroid indexes, and a 419 MB sentence encoder). The Pi needs **at least 1.1 GB
free** (the bundle plus headroom for the transfer itself and the old copy it replaces) — check with
`df -h /home/pollen` before starting.

```bash
# from a machine with the deliverable/2026-09 checkout, after scripts/build_robot_bundle.py has run
rsync -a --info=progress2 deploy/pi/bundle/ pollen@<hostname>.local:~/data_bundle_incoming/
```

It lands at `~/data_bundle_incoming/` first, not directly over the live path, so a failed or partial
transfer never leaves the robot with a half-written bundle:

```bash
# on the Pi, after the rsync finishes
cd ~/data_bundle_incoming
sha256sum -c checksums.sha256                      # every line must say OK
# all OK:
rm -rf ~/Supervaise-Reachy-Mini-Project-main/deploy/pi/bundle
mv ~/data_bundle_incoming ~/Supervaise-Reachy-Mini-Project-main/deploy/pi/bundle
sudo systemctl restart supervaise
```

**If `sha256sum -c` reports anything but OK for every line:** do not move the bundle into place. Re-run
the `rsync` (plain `rsync -a` is resumable — it only re-sends the files that failed or are still
partial); if it fails again, delete `~/data_bundle_incoming` and re-transfer from scratch rather than
patching individual files, and check `df -h` first — a `FAILED open or read` line usually means the
transfer ran out of disk space partway through.

**Free space: not measured here.** This document was prepared from a development checkout with no
network path to the robot (`ping`/`ssh reachy-mini.local` both returned nothing — no route from this
environment), and nothing in the repo records the Pi's actual storage capacity or how much of it is
free. The "1.1 GB free" above is what the bundle needs, not a confirmation the robot has it — **run
`df -h /home/pollen` on the actual Pi before transferring**, and if free space is under that figure, say
so and stop rather than starting a transfer that will fail partway through.

## 8. `CJ_PIPELINE` — testing the retrieval stack on a robot without making it live

Phase 8 (batch-04) wired `main_voice_robot.py` to pick its turn-handling pipeline from
`config.CJ_PIPELINE`. **`legacy` is the default and stays the default** until CE-11 → CE-14 validate
the retrieval stack (see `docs/architecture/PIPELINES.md` and `batch-04/BATCH-04_REPORT.md`). Setting
`retrieval` makes the robot route, retrieve and compose entirely locally except for the one composer
call — but do not do this on a robot people are relying on until that gate clears.

**Getting the code there at all (the stopgap).** Because none of the five files above are on
`pi/deployment-snapshots` (see §7), `install.sh` cannot deliver them. Until they are merged onto that
branch through whatever release process this project settles on — not invented here — the only way to
test `CJ_PIPELINE=retrieval` on a robot is to copy the files directly, on top of an existing
`install.sh`-provisioned checkout, leaving its git state on `pi/deployment-snapshots` untouched:

```bash
# from a deliverable/2026-09 checkout — the five retrieval-stack modules plus the entry point
# and config.py that reference them (main_voice_robot.py, config.py); app/ files go to app/,
# config.py goes one level up, to the repo root
R="pollen@<hostname>.local:~/Supervaise-Reachy-Mini-Project-main"
rsync -a app/service.py app/retrieval.py app/embeddings.py app/sparse.py app/centering.py app/main_voice_robot.py "$R/app/"
rsync -a config.py "$R/"
```

This is a manual file patch over a git checkout — `git status` on the Pi afterward will show these six
files as locally modified against `pi/deployment-snapshots`. That is expected and reversible
(`git checkout -- <path>` restores the deployed version for any file); it is not how this should reach
production, only how it can be tried.

**Setting the flag.** Add one line to `app/.env` (created by `install.sh`, never overwritten by it) or
export it in the systemd unit's environment:

```bash
echo 'CJ_PIPELINE=retrieval' >> ~/Supervaise-Reachy-Mini-Project-main/app/.env
sudo systemctl restart supervaise
journalctl -u supervaise -n 20 --no-pager | grep '\[pipeline\]'   # confirms which one actually started
```

**Switching back:** delete that line (or set `CJ_PIPELINE=legacy`) and restart the service. `legacy` is
also what running with no `CJ_PIPELINE` set at all gives you — the flag fails safe to `legacy` on a typo
too (`config.py` logs a warning and falls back rather than starting in an unrecognised mode).
