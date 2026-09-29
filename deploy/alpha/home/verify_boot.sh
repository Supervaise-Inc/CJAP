#!/bin/bash
# Post-reboot check for the Panganiban exhibit. Read-only. Run on either robot:
#   bash ~/verify_boot.sh
echo "=== COLD BOOT CHECK — $(hostname) — $(date '+%F %H:%M:%S') ==="
echo "uptime:        $(uptime -p)"
echo "system state:  $(systemctl is-system-running 2>&1)"
echo "failed units:  $(systemctl --failed --no-legend | wc -l)"
systemctl --failed --no-legend | sed 's/^/   /' | head -5
for U in supervaise.service pi-dashboard.service wifi-fallback.service; do
  echo "$U: active=$(systemctl is-active $U) enabled=$(systemctl is-enabled $U) restarts=$(systemctl show $U -p NRestarts --value)"
done
echo "speaker-watchdog: active=$(systemctl is-active speaker-watchdog.service 2>&1) enabled=$(systemctl is-enabled speaker-watchdog.service 2>&1)  <- must be disabled"
cd "$HOME/Supervaise-Reachy-Mini-Project-main" 2>/dev/null && \
  echo "commit: $(git rev-parse --short HEAD)  dirty: $(git status --porcelain | wc -l)"
P=$(systemctl show supervaise.service -p MainPID --value)
echo "env applied: $(tr '\0' '\n' < /proc/$P/environ 2>/dev/null | grep -cE 'MALLOC_ARENA_MAX=2|CJ_STOP_DEBUG_WAV=0|CJ_NAME_PIN_SPEED')/3"
echo "tracebacks this boot: $(journalctl -u supervaise.service -b --no-pager -o cat | grep -ciE 'traceback|exception')"
echo "--- app init ---"
journalctl -u supervaise.service -b --no-pager -o cat | grep -E 'persona. loaded|persona. ACTIVE|= slot|mic. using|gestures.*connected' | head -5
echo "--- mic mute (tmpfs: cleared by a reboot) ---"
test -f /dev/shm/cj_muted && echo "MUTED" || echo "NOT muted — the robot will listen; touch /dev/shm/cj_muted to silence it"
