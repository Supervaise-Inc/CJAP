#!/bin/bash
# speaker-watchdog - keep robot audio on a Bluetooth speaker whenever one is
# connected, otherwise on the internal XMOS speaker, so the robot is never mute.
#
# Priority (first usable wins): Sony ULT FIELD 1, then Marshall EMBERTON.
# "Usable" = bluetoothctl says Connected AND BlueALSA exposes its A2DP PCM
# (a speaker can be "connected" with no audio endpoint yet -> would be mute).
# Route mechanics live in ~/bin/audio-out (rewrites ~/.asoundrc.route; only
# newly opened playback streams follow a switch, i.e. the next utterance).
# To force the internal speaker while a BT speaker is on, stop this service
# first: sudo systemctl stop speaker-watchdog
# 2026-08-26: generalised from Sony-only to both paired speakers + PCM check.
# 2026-09-02: leaves a working manual route alone (laptop, dual speaker+laptop).
set -u
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"

SONY_MAC="50:1B:6A:8B:16:F2"       # Sony ULT FIELD 1
MARSHALL_MAC="04:21:44:84:1F:C1"   # Marshall EMBERTON
C41_MAC="66:EA:C5:C3:E5:6B"        # C41 speaker (2026-09-02) — first in priority
# Same per-robot override file audio-out uses (other speakers' MACs).
[ -f "$HOME/bin/audio-out.local" ] && . "$HOME/bin/audio-out.local"
# Priority: Sony, Marshall, then ANY other paired device advertising the
# Audio Sink UUID (2026-08-31, user: "any bluetooth speaker"). The laptop and
# non-audio devices are excluded by the UUID filter. Names for the extras are
# their MACs — audio-out accepts a raw MAC since the same date.
base_speakers=("$C41_MAC|c41" "$SONY_MAC|sony" "$MARSHALL_MAC|marshall")   # priority order
build_speakers() {
    SPEAKERS=("${base_speakers[@]}")
    while read -r _ mac _; do
        [ "$mac" = "$SONY_MAC" ] || [ "$mac" = "$MARSHALL_MAC" ] || [ "$mac" = "$C41_MAC" ] && continue
        info=$(bluetoothctl info "$mac" 2>/dev/null)
        echo "$info" | grep -q "Audio Sink" || continue
        # laptops/phones also advertise Audio Sink — only real audio devices
        echo "$info" | grep -qE "Icon: audio-(card|headset|headphones)" || continue
        SPEAKERS+=("$mac|$mac")
    done < <(bluetoothctl devices Paired 2>/dev/null)
}
build_speakers

ROUTE="$HOME/.asoundrc.route"
AUDIO_OUT="$HOME/bin/audio-out"
INTERVAL=15

connected()   { bluetoothctl info "$1" 2>/dev/null | grep -q "Connected: yes"; }
has_pcm()     { bluealsa-aplay -L 2>/dev/null | grep -q "DEV=$1,PROFILE=a2dp"; }
# 2026-09-05: the route may name the USB DAC ("dac") instead of a MAC — usable
# while PipeWire still has its sink; treated like a working manual route.
usable_out()  { if [ "$1" = dac ]; then "$AUDIO_OUT" dac-present >/dev/null 2>&1; else connected "$1" && has_pcm "$1"; fi; }
# 2026-09-02: the route file carries "# Primary:" / "# Secondary:" headers
# (audio-out dual output); older files without them fall back to the awk scan.
routed_mac() {
    local p; p=$(sed -n 's/^# Primary: //p' "$ROUTE" 2>/dev/null)
    [ -z "$p" ] && p=$(awk -F'"' '/type bluealsa/ {bt=1} bt && /device/ {print $2; exit}' "$ROUTE" 2>/dev/null)
    [ "$p" = internal ] && p=""
    echo "$p"
}
routed_second() { local s; s=$(sed -n 's/^# Secondary: //p' "$ROUTE" 2>/dev/null); [ "$s" = none ] && s=""; echo "$s"; }

AUDIO_VOLUME="$HOME/bin/audio-volume"
prev_pcms=""   # 2026-09-01: BlueALSA forgets a PCM's volume when the speaker drops,
               # so the stored /maintain level is re-applied whenever a new A2DP PCM appears

echo "speaker-watchdog: start (priority: ${SPEAKERS[*]})"
while true; do
    build_speakers   # pick up newly paired speakers without a restart
    pcms=$(bluealsa-aplay -L 2>/dev/null | grep -o 'DEV=[0-9A-F:]*,PROFILE=a2dp' | sort | tr '\n' ' ')
    if [ "$pcms" != "$prev_pcms" ]; then
        if [ -n "$pcms" ] && [ -x "$AUDIO_VOLUME" ]; then
            echo "speaker-watchdog: A2DP endpoint change ($pcms) -> $("$AUDIO_VOLUME" apply 2>/dev/null)"
        fi
        prev_pcms="$pcms"
    fi
    want_mac=""; want_name=""
    for entry in "${SPEAKERS[@]}"; do
        mac="${entry%%|*}"; name="${entry#*|}"
        if connected "$mac" && has_pcm "$mac"; then
            want_mac="$mac"; want_name="$name"; break
        fi
    done

    if [ -z "$want_mac" ]; then
        # nothing usable: try to (re)connect in priority order, one per pass
        for entry in "${SPEAKERS[@]}"; do
            mac="${entry%%|*}"
            connected "$mac" && continue
            if bluetoothctl connect "$mac" >/dev/null 2>&1; then
                sleep 2   # let BlueALSA register the A2DP endpoint
                break
            fi
        done
        for entry in "${SPEAKERS[@]}"; do
            mac="${entry%%|*}"; name="${entry#*|}"
            if connected "$mac" && has_pcm "$mac"; then
                want_mac="$mac"; want_name="$name"; break
            fi
        done
    fi

    cur="$(routed_mac)"; sec="$(routed_second)"
    if [ -n "$want_mac" ]; then
        if [ "$cur" != "$want_mac" ]; then
            if [ -n "$cur" ] && usable_out "$cur"; then
                # 2026-09-02: a manually chosen Bluetooth output that still works
                # (the laptop, another speaker, a dual route) is left alone - the
                # job here is "never mute", not "always Sony".
                :
            elif [ -n "$sec" ] && [ "$sec" != internal ] && [ "$sec" != "$want_mac" ] && usable_out "$sec"; then
                echo "speaker-watchdog: $want_name ($want_mac) usable -> routing audio to it (+ keeping second output $sec)"
                "$AUDIO_OUT" dual "$want_mac" "$sec" >/dev/null 2>&1 || echo "speaker-watchdog: audio-out dual $want_name $sec failed"
            else
                echo "speaker-watchdog: $want_name ($want_mac) usable -> routing audio to it"
                "$AUDIO_OUT" "$want_name" >/dev/null 2>&1 || echo "speaker-watchdog: audio-out $want_name failed"
            fi
        elif [ -n "$sec" ] && [ "$sec" != internal ] && ! usable_out "$sec"; then
            echo "speaker-watchdog: second output $sec gone -> dropping it"
            "$AUDIO_OUT" ensure >/dev/null 2>&1
        fi
    elif [ -n "$cur" ]; then
        if usable_out "$cur"; then
            :   # e.g. laptop-only route, still working: leave it (2026-09-02)
        elif [ -n "$sec" ] && [ "$sec" != internal ] && usable_out "$sec"; then
            echo "speaker-watchdog: $cur gone -> second output $sec"
            "$AUDIO_OUT" "$sec" >/dev/null 2>&1 || echo "speaker-watchdog: audio-out $sec failed"
        else
            echo "speaker-watchdog: no usable Bluetooth speaker (was $cur) -> internal speaker"
            "$AUDIO_OUT" internal >/dev/null 2>&1 || echo "speaker-watchdog: audio-out internal failed"
        fi
    fi
    sleep "$INTERVAL"
done
