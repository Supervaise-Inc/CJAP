# Read me first

This is **Bundle Folder**, everything needed to give a Reachy Mini robot the September 2026 knowledge
model in one drag-and-drop. It has two parts:

- **`cjap-bundle/`** — the payload. This is what goes to the Pi. **Do not rename it, and do not move
  anything out of it onto its own.** The folder you are reading this from has a space in its name
  ("Bundle Folder"), which is fine for dragging onto a USB stick or a Windows desktop — but a space in a
  file path breaks `rsync`, `scp`, and the systemd service paths the moment it reaches the robot's Linux
  system. `cjap-bundle/` has no space in its name for exactly that reason. Copy `cjap-bundle/`, not
  `Bundle Folder` itself.
- **`install/`** — a copy of the robot's install script, its Python package list, and its systemd
  service files, for reference. You do not need to touch this for a routine data refresh (see step 3);
  it is here so the whole picture — code, service files, and data — travels together in one folder.

**Nothing about how the robot behaves changes by copying this folder.** The robot's answer engine is
selected by a setting called `CJ_PIPELINE`, and it stays at its current setting (`legacy`) no matter
what is copied here, until a separate, later sign-off (internally: "CE-11 through CE-14") says the new
engine is ready. Copying this folder updates the robot's *knowledge* — its corpus, its search indexes —
not its behavior.

## Step 1 — what this is for

A refresh of the robot's knowledge model: the columns, book chapters, speeches and biography chapters it
draws on, the search indexes built from them, and the language-understanding model that powers the
search. It does **not** include anything that would change how the robot currently answers a question.

## Step 2 — check the robot has room, BEFORE you copy anything

SSH into the robot and run:

```bash
df -h /home/pollen
```

Look at the **Avail** column for the filesystem that contains `/home/pollen`. You need **at least
1.5 GB free** — the payload itself (`cjap-bundle/`) is **516 MB**, and the rest of that 1.5 GB is
headroom for the transfer itself plus the copy it will replace. If the robot has less than that free,
**stop here** and free up space (or ask for help) before doing anything else. This step could not be
checked in advance — the robot was not reachable from the machine that built this folder (no network
route to it from here) and nothing in the project records the robot's actual storage capacity — so it is
the first thing to do here, not an afterthought.

## Step 3 — copy `cjap-bundle/` to the robot

From a machine that has this folder, with the robot's hostname or IP address in place of
`<hostname>`:

```bash
rsync -a --info=progress2 "cjap-bundle/" pollen@<hostname>.local:~/data_bundle_incoming/
```

(Quote the source path if your copy of this folder ever ends up with a space anywhere in *its* name too
— quoting costs nothing and avoids a surprise.) This copies to a temporary location on the robot first,
not directly over the live data, so an interrupted copy never leaves the robot half-updated.

## Step 4 — verify the copy, then make it live

On the robot, after the copy finishes:

```bash
cd ~/data_bundle_incoming
sha256sum -c checksums.sha256
```

Every line must say `OK`. If even one line says anything else (`FAILED`, `No such file or directory`),
**do not proceed** — the copy is incomplete or corrupted. Re-run the `rsync` command from step 3 (it
only re-sends what is missing or broken); if it still fails, delete `~/data_bundle_incoming` on the
robot and start over from step 3, and check `df -h` again — a failure here is usually the robot running
out of space partway through.

Once every line says `OK`:

```bash
rm -rf ~/Supervaise-Reachy-Mini-Project-main/deploy/pi/bundle
mv ~/data_bundle_incoming ~/Supervaise-Reachy-Mini-Project-main/deploy/pi/bundle
sudo systemctl restart supervaise
```

## Step 5 — if something goes wrong, roll back

Two safety nets exist:

- The stage-then-swap copy in steps 3–4 means a failed transfer never overwrites the working copy — the
  robot keeps running on what it had until you explicitly run the `mv` command above.
- The old code and data this replaces are preserved under the git tag
  **`pi-snapshot-pre-kbv2-2026-09-27`**. Restoring it is a git operation for whoever manages the robot's
  software, not something to attempt from this note alone — ask them if you need to go back further
  than "undo the last `mv`".

## Step 6 — switching the robot's answer engine later (do not do this yet)

The `install/` files reference a setting called `CJ_PIPELINE`. Leave it alone. When (and only when) you
are told the CE-11 → CE-14 sign-off has passed, switching the robot to the new engine means adding one
line to `app/.env` on the robot:

```bash
echo 'CJ_PIPELINE=retrieval' >> ~/Supervaise-Reachy-Mini-Project-main/app/.env
sudo systemctl restart supervaise
```

To switch back, delete that line (or change it to `CJ_PIPELINE=legacy`) and restart the service again.
Until you are told otherwise, the robot should stay on `legacy` — that is what it does automatically if
this line is never added at all.
