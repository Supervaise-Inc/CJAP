#!/bin/bash
# Is the voice app capturing from the microphone it should? (verify.sh helper, 2026-09-15)
#   exit 0  capturing from the routed mic (XMOS hw via dsnoop, or the USB mic via PipeWire),
#           or the mic is CLOSED because this robot does not hold the floor (by design)
#   exit 1  otherwise
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"
pid=$(systemctl show -p MainPID --value supervaise.service)
[ -n "$pid" ] && [ "$pid" != 0 ] || { echo "supervaise not running"; exit 1; }
last=$(journalctl -u supervaise -b --no-pager 2>/dev/null | grep -F '[mic] ' | grep -E 'OPEN|CLOSED' | tail -1)
case "$last" in
  *CLOSED*) echo "mic closed: this robot does not hold the floor (ok)"; exit 0 ;;
  "")       echo "mic never opened this boot: this robot has not held the floor (ok)"; exit 0 ;;
esac
if [ -f ~/.asoundrc.inroute ]; then
    src=$(sed -n 's/^ *device "\(.*\)"/\1/p' ~/.asoundrc.inroute)
    pactl -f json list source-outputs 2>/dev/null | python3 -c "
import sys, json, subprocess
outs = json.load(sys.stdin)
srcs = {s['index']: s['name'] for s in json.loads(subprocess.run(['pactl','-f','json','list','sources'], capture_output=True, text=True).stdout or '[]')}
ok = any(str(o.get('properties', {}).get('application.process.id')) == '$pid' and srcs.get(o.get('source')) == '$src' for o in outs)
print('USB mic via PipeWire: ' + ('capturing' if ok else 'NOT capturing') + ' from $src')
sys.exit(0 if ok else 1)"
    exit $?
fi
# XMOS: the dsnoop owner is one of the app's threads (owner_pid is a TID, not the main pid)
owner=$(sed -n 's/^owner_pid *: *//p' /proc/asound/Audio/pcm0c/sub0/status 2>/dev/null)
tgid=$(sed -n 's/^Tgid:\s*//p' /proc/"$owner"/status 2>/dev/null)
if [ -n "$owner" ] && [ "$tgid" = "$pid" ]; then echo "XMOS array held by supervaise (tid $owner)"; exit 0; fi
echo "XMOS capture owner is '${owner:-nobody}' (tgid ${tgid:-?}), supervaise is $pid"; exit 1
