#!/bin/bash
# Install the USB-hub audio preference on this robot (2026-09-15). Idempotent.
#   1. ~/.asoundrc: the voice app's capture goes through pcm.audio_in_route
#      (fallback: the robot's XMOS beam), with ~/.asoundrc.inroute included
#      beside ~/.asoundrc.route. A dated backup is kept.
#   2. audio-hub.service (scripts/audio_hub.py) installed, enabled, started.
# Needs ~/bin/audio-out with the `dac` route (2026-09-05 or later).
# supervaise.service must be restarted once afterwards, so the running app
# picks up the capture-route reload (main_voice_robot._input_route_sync).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"

if ! grep -q "dac|usb|usb-dac" "$HOME/bin/audio-out" 2>/dev/null; then
    echo "error: ~/bin/audio-out has no dac route - copy the current one from the other robot first" >&2
    exit 1
fi
python3 "$REPO/scripts/audio_hub.py" --patch-asoundrc
arecord -L | grep -q "^reachymini_audio_src_plug" || { echo "error: capture pcm missing after the patch" >&2; exit 1; }
sudo install -m 644 "$REPO/scripts/audio-hub.service" /etc/systemd/system/audio-hub.service
sudo systemctl daemon-reload
sudo systemctl enable --now audio-hub.service
sudo systemctl restart audio-hub.service
sleep 3
systemctl --no-pager --lines=6 status audio-hub.service || true
