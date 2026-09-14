#!/bin/bash
# ReachyMini setup-hotspot fallback (2026-08-13).
#
# If the Pi has no active WiFi for ~60s (boot at a new venue, router gone),
# start its own access point so a phone can connect and open the dashboard
# to add the venue WiFi:
#
#     network  CJAP Reachy   password  reachymini
#     dashboard at  http://10.42.0.1:8080  (WiFi card -> add network)
#
# While the hotspot is up, every ~5 min it drops for 45s to let
# NetworkManager rejoin any known network that appeared (self-healing when
# the robot returns home). The dashboard's connect endpoint also tears the
# hotspot down itself when the user submits a network.
#
# Runs as root via wifi-fallback.service. Override the AP name/password with
# CJ_SETUP_SSID / CJ_SETUP_PW in the unit's Environment.

SSID="${CJ_SETUP_SSID:-CJAP Reachy}"
PW="${CJ_SETUP_PW:-reachymini}"
CON="ReachySetup"
CHECK_S="${CJ_SETUP_CHECK_S:-20}"
# 3 x 20s = 60s without WiFi -> hotspot. On the SECOND robot of a two-robot
# kit raise this (CJ_SETUP_MISSES=30 = 10 min): when the venue router dies both
# machines start counting, and whoever raises an AP first stops the other from
# joining it. The authority should always win that race, because its hotspot is
# the fallback LAN the other robot needs to reach the lease. (2026-09-12)
MISSES_BEFORE_AP="${CJ_SETUP_MISSES:-3}"
RECOVER_EVERY="${CJ_SETUP_RECOVER_EVERY:-15}"   # every 15 AP loops (~5 min) probe for known WiFi
RECOVER_WAIT="${CJ_SETUP_RECOVER_WAIT:-45}"

# Association only. A router with a dead uplink, a captive portal, or simply
# the wrong network all satisfy this — which is why the hotspot never rescued
# the one failure that actually strands the machine (2026-09-14 audit).
active_wifi() {
    nmcli -t -f NAME,TYPE connection show --active 2>/dev/null |
        awk -F: '$2 ~ /wireless/ {print $1; exit}'
}

# full | portal | limited | none | unknown — NetworkManager's own verdict.
wifi_connectivity() {
    nmcli -t -f CONNECTIVITY general 2>/dev/null | tail -1
}

# Associated WITHOUT internet, for REQUIRE_INTERNET_POLLS consecutive polls, is
# treated as no-wifi and raises the setup hotspot.
#
# OFF by default, deliberately. The venue kit is a travel router whose WAN may
# legitimately be down while the LAN it provides is exactly what the two robots
# need: the floor lease, the console and duet mode all work with no internet at
# all, and raising an AP there would break a working installation to fix
# nothing. Turn it on (CJ_SETUP_REQUIRE_INTERNET=1) for a kiosk that is useless
# without the composer, where being unreachable is worse than being offline.
REQUIRE_INTERNET="${CJ_SETUP_REQUIRE_INTERNET:-0}"
REQUIRE_INTERNET_POLLS="${CJ_SETUP_REQUIRE_INTERNET_POLLS:-30}"   # 30 x 20 s = 10 min
no_net_polls=0

ensure_profile() {
    nmcli -t -f NAME connection show | grep -qx "$CON" && return
    nmcli connection add type wifi ifname wlan0 con-name "$CON" \
        autoconnect no ssid "$SSID" \
        802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared \
        wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PW"
}

misses=0
ap_loops=0
while true; do
    aw="$(active_wifi)"
    if [ "$aw" = "$CON" ]; then
        ap_loops=$((ap_loops + 1))
        if [ "$ap_loops" -ge "$RECOVER_EVERY" ]; then
            ap_loops=0
            echo "probing for known wifi (hotspot down ${RECOVER_WAIT}s)"
            nmcli connection down "$CON"
            sleep "$RECOVER_WAIT"
            if [ -z "$(active_wifi)" ]; then
                echo "no known wifi found - hotspot back up"
                nmcli connection up "$CON"
            else
                echo "rejoined wifi: $(active_wifi)"
            fi
        fi
    elif [ -n "$aw" ]; then
        ap_loops=0
        if [ "$REQUIRE_INTERNET" = "1" ]; then
            conn="$(wifi_connectivity)"
            if [ "$conn" = "full" ]; then
                no_net_polls=0
                misses=0
            else
                no_net_polls=$((no_net_polls + 1))
                if [ "$no_net_polls" -ge "$REQUIRE_INTERNET_POLLS" ]; then
                    no_net_polls=0
                    misses=0
                    echo "on '$aw' but connectivity=$conn for $((CHECK_S * REQUIRE_INTERNET_POLLS))s - starting setup hotspot $SSID"
                    ensure_profile
                    nmcli connection up "$CON"      # takes wlan0 from '$aw'
                else
                    misses=0
                fi
            fi
        else
            misses=0
        fi
    else
        misses=$((misses + 1))
        if [ "$misses" -ge "$MISSES_BEFORE_AP" ]; then
            misses=0
            ap_loops=0
            echo "no wifi for $((CHECK_S * MISSES_BEFORE_AP))s - starting setup hotspot $SSID"
            ensure_profile
            nmcli connection up "$CON"
        fi
    fi
    sleep "$CHECK_S"
done
