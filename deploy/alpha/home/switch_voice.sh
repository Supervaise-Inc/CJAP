#!/bin/bash
# Switch the robot's answers to the ElevenLabs cloned voice.
# Run by the user:  bash ~/switch_voice.sh
# Extracts the two credentials from the main checkout's gitignored
# voice/config.py into app/.env (no key is stored in this script),
# sets the backend flag, restarts the service.
set -e
ENV=~/Supervaise-Reachy-Mini-Project-main/app/.env
SRC=~/Supervaise-Reachy-Mini-Project-main/voice/config.py

if grep -q '^CJ_TTS_BACKEND=' "$ENV" 2>/dev/null; then
  echo "already switched — $ENV has CJ_TTS_BACKEND set; nothing to do"
  exit 0
fi

# match ONLY the quoted-literal assignment lines (not the env-override lines)
awk -F'"' '/^ELEVEN_API_KEY = "/{print "ELEVEN_API_KEY="$2}
           /^ELEVEN_VOICE_ID = "/{print "ELEVEN_VOICE_ID="$2}' "$SRC" >> "$ENV"
echo 'CJ_TTS_BACKEND=elevenlabs' >> "$ENV"

grep -c '^ELEVEN_' "$ENV" | xargs -I{} echo "credential lines in .env: {}"
sudo systemctl restart supervaise
echo SWITCHED
