"""WiFi control on /maintain and / — every nmcli call goes through sudo (the
service has no login session; polkit refuses scan/activate otherwise), saved
networks are matched by SSID not profile name, a new password replaces a saved
one, hidden networks are explicit, and a failed join puts the robot back on the
previous network.

2026-09-14: "connected" is no longer nmcli's exit code. The fake now models an
UPLINK (full / portal / limited / none), an autoconnect priority per profile,
and two profiles sharing one SSID — the three things the old fake could not
express, and therefore the three things nothing tested. A join is verified in
stages and a captive portal reads as connected-with-no-internet, not connected.
"""
from __future__ import annotations

import os
import socket
import pathlib
import sys

# Import the dashboard from the REPO, not through ~/pi_dashboard. That symlink
# happens to point here on alpha, but on beta it was a stale DIRECTORY holding
# an older copy until 2026-09-14 — so these tests were validating code that was
# not the code being deployed, and passing. Same shape as the breath-motion
# fixture: a test must not depend on the state of the machine it runs on.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dashboard"))
import ui_server as srv  # noqa: E402


class FakeNM:
    """Minimal nmcli: profiles {name: ssid}, active profile, scan list, which
    SSIDs accept which password, what each network's uplink does, and the
    autoconnect priority / mode of each profile."""

    def __init__(self):
        self.profiles = {"Home": "Home", "ReachySetup": "CJAP Reachy", "Event": "Event Hall"}
        self.psk = {"Home": "oldpw"}
        self.priority = {"Home": 0, "Event": 0, "ReachySetup": 0}
        self.mode = {"ReachySetup": "ap"}          # everything else is infrastructure
        self.active = "Home"
        self.scan = [("Event Hall", "80", "WPA2"), ("Home", "70", "WPA2"), ("Cafe:Wifi", "40", "")]
        self.accept = {"Event Hall": "eventpw", "Home": "oldpw", "Cafe:Wifi": None,
                       "Ghost": "ghostpw"}
        # what the uplink of each SSID does once you are on it
        self.uplink = {"Home": "full", "Event Hall": "full", "Cafe:Wifi": "portal",
                       "Ghost": "full", "CJAP Reachy": "none"}
        self.ip_for = {}                            # ssid -> address; default 192.168.1.50
        self.calls = []

    # ── helpers ──────────────────────────────────────────────────────────
    def _ssid(self):
        return self.profiles.get(self.active) if self.active else None

    def _ip(self):
        s = self._ssid()
        if not s:
            return None
        return self.ip_for.get(s, "192.168.1.50")

    def connectivity(self):
        s = self._ssid()
        if not s or self._ip() is None:
            return "none"
        return self.uplink.get(s, "full")

    def __call__(self, cmd, timeout=10):
        assert cmd[:3] == ["sudo", "-n", "nmcli"], cmd
        a = cmd[3:]
        if a[:1] == ["--wait"]:                     # bounded activation wait
            a = a[2:]
        self.calls.append(a)
        esc = lambda s: s.replace(":", chr(92) + ":")

        if a[:5] == ["-t", "-f", "NAME,TYPE", "connection", "show"]:
            return 0, "\n".join(f"{esc(n)}:802-11-wireless" for n in self.profiles) + "\nlo:loopback"
        if a[:2] == ["-g", "802-11-wireless.ssid"]:
            return 0, esc(self.profiles[a[4]])
        if a[:2] == ["-g", "802-11-wireless.mode"]:
            return 0, self.mode.get(a[4], "infrastructure")
        if a[:2] == ["-g", "connection.autoconnect-priority"]:
            return 0, str(self.priority.get(a[4], 0))
        if a[:3] == ["-s", "-g", "802-11-wireless-security.psk"]:
            return 0, self.psk.get(a[5]) or ""
        if a[:5] == ["-t", "-f", "NAME,TYPE,DEVICE", "connection", "show"]:
            act = esc(self.active) if self.active else None
            return 0, (f"{act}:802-11-wireless:wlan0\n" if act else "") + "lo:loopback:lo"
        if a[:5] == ["-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "dev", "wifi"]:
            return 0, "\n".join(
                f"{esc(s)}:{sig}:{sec}:{'*' if self._ssid() == s else ' '}"
                for s, sig, sec in self.scan)
        if a[:5] == ["-t", "-f", "DEVICE,STATE,CONNECTION", "device", "status"]:
            state = "connected" if self.active else "disconnected"
            return 0, f"wlan0:{state}:{esc(self.active) if self.active else '--'}\nlo:unmanaged:--"
        if a[:2] == ["-g", "IP4.ADDRESS"]:
            ip = self._ip()
            return 0, f"{ip}/24" if ip else ""
        if a[:3] == ["-t", "-f", "GENERAL.CONNECTION,IP4.ADDRESS"]:
            ip = self._ip()
            return 0, (f"GENERAL.CONNECTION:{esc(self.active) if self.active else '--'}\n"
                       + (f"IP4.ADDRESS[1]:{ip}/24" if ip else ""))
        if a[:4] == ["-t", "-f", "CONNECTIVITY", "general"] or a[:3] == ["networking",
                                                                        "connectivity", "check"]:
            return 0, self.connectivity()
        if a[:2] == ["connection", "modify"]:
            name, rest = a[2], a[3:]
            for k, v in zip(rest[::2], rest[1::2]):
                if k == "wifi-sec.psk":
                    self.psk[name] = v
            return 0, ""
        if a[:3] == ["connection", "up", "id"]:
            name = a[3]
            ssid = self.profiles[name]
            if self.psk.get(name) == self.accept.get(ssid):
                self.active = name
                return 0, "Connection successfully activated"
            self.active = None
            return 4, "Error: Connection activation failed: Secrets were required"
        if a[:3] == ["dev", "wifi", "connect"]:
            ssid = a[3]
            pw = a[a.index("password") + 1] if "password" in a else None
            hidden = "hidden" in a
            if ssid not in [x[0] for x in self.scan] and not hidden:
                return 10, f"Error: No network with SSID '{ssid}' found."
            self.profiles[ssid] = ssid          # nmcli makes the profile first
            self.psk[ssid] = pw
            if ssid in self.accept and self.accept[ssid] == pw:
                self.active = ssid
                return 0, f"Device 'wlan0' successfully activated with '{ssid}'."
            self.active = None
            return 4, "Error: Connection activation failed: (7) Secrets were required"
        if a[:3] == ["connection", "delete", "id"]:
            self.profiles.pop(a[3], None)
            self.psk.pop(a[3], None)
            return 0, ""
        if a[:2] == ["connection", "down"]:
            self.active = None
            return 0, ""
        raise AssertionError(f"unexpected nmcli {a}")


def _wire(monkeypatch, dns=True):
    nm = FakeNM()
    monkeypatch.setattr(srv, "run", nm)
    # wifi_verify resolves a host; never touch real DNS from a test
    if dns:
        monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [("AF_INET", None)])
    else:
        def _boom(*a, **k):
            raise socket.gaierror("Name or service not known")
        monkeypatch.setattr(socket, "getaddrinfo", _boom)
    srv._wifi_profiles_cache.update(ts=0.0, data=None)
    return nm


# ── the original contract, still true ────────────────────────────────────────

def test_nm_split_handles_escaped_colons():
    assert srv._nm_split("Cafe\\:Wifi:40:WPA2:*") == ["Cafe:Wifi", "40", "WPA2", "*"]
    assert srv._nm_split("a\\\\b:c") == ["a\\b", "c"]


def test_scan_and_status_use_sudo_and_ssids(monkeypatch):
    nm = _wire(monkeypatch)
    nets = srv.wifi_scan(rescan=True)
    assert [n["ssid"] for n in nets] == ["Event Hall", "Home", "Cafe:Wifi"]
    assert nets[1]["in_use"] and nets[2]["security"] == "open"
    assert ["-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "dev", "wifi", "list",
            "--rescan", "yes"] in nm.calls
    saved, current = srv.wifi_status()
    assert saved == ["CJAP Reachy", "Event Hall", "Home"] and current == "Home"


def test_join_saved_network_by_profile_name(monkeypatch):
    nm = _wire(monkeypatch)
    nm.accept["Event Hall"] = None
    nm.psk["Event"] = None
    ok, msg = srv.wifi_connect("Event Hall")
    assert ok and 'now on "Event Hall"' in msg and nm.active == "Event"
    assert ["connection", "up", "id", "Event"] in nm.calls
    assert not any(a[:3] == ["dev", "wifi", "connect"] for a in nm.calls)


def test_new_password_replaces_saved_one(monkeypatch):
    nm = _wire(monkeypatch)
    nm.active = "Event"; nm.psk["Event"] = "eventpw"
    nm.accept["Home"] = "newpw"                          # the router password changed
    ok, msg = srv.wifi_connect("Home", "newpw")
    assert ok and nm.psk["Home"] == "newpw" and nm.active == "Home"
    assert any(a[:3] == ["connection", "modify", "Home"] and "newpw" in a for a in nm.calls)


def test_failed_join_restores_previous_and_drops_half_profile(monkeypatch):
    nm = _wire(monkeypatch)
    ok, msg = srv.wifi_connect("Cafe:Wifi", "wrongpw")
    assert not ok and "back on 'Home'" in msg and nm.active == "Home"
    assert "Cafe:Wifi" not in nm.profiles


def test_unknown_ssid_refused_unless_hidden(monkeypatch):
    nm = _wire(monkeypatch)
    ok, msg = srv.wifi_connect("Ghost", "ghostpw")
    assert not ok and "not in the last scan" in msg and nm.active == "Home"
    ok, msg = srv.wifi_connect("Ghost", "ghostpw", hidden=True)
    assert ok and nm.active == "Ghost"


def test_bad_ssid():
    assert srv.wifi_connect("")[0] is False
    assert srv.wifi_connect("x" * 33)[0] is False


# ── verified connection: the 2026-09-14 contract ─────────────────────────────

def test_verify_passes_every_stage_when_the_uplink_works(monkeypatch):
    _wire(monkeypatch)
    v = srv.wifi_verify()
    assert v["ok"] and [s["stage"] for s in v["stages"]] == list(srv.WIFI_STAGES)
    assert all(s["ok"] for s in v["stages"])
    assert v["ssid"] == "Home" and v["ip"] == "192.168.1.50" and v["connectivity"] == "full"
    assert "internet reachable" in v["plain"]


def test_captive_portal_is_not_connected(monkeypatch):
    """The venue case. Associated, has an IP, DNS answers — and no internet."""
    nm = _wire(monkeypatch)
    nm.uplink["Home"] = "portal"
    v = srv.wifi_verify()
    assert not v["ok"]
    assert dict((s["stage"], s["ok"]) for s in v["stages"]) == {
        "interface": True, "associated": True, "ip": True, "dns": True, "internet": False}
    assert "captive portal" in v["plain"] and "no internet" in v["plain"]


def test_associated_but_no_uplink_reports_no_internet(monkeypatch):
    nm = _wire(monkeypatch)
    nm.uplink["Home"] = "limited"
    v = srv.wifi_verify()
    assert not v["ok"] and "no internet" in v["plain"]


def test_no_ip_is_reported_as_a_dhcp_failure(monkeypatch):
    nm = _wire(monkeypatch)
    nm.ip_for["Home"] = None
    v = srv.wifi_verify()
    assert not v["ok"] and "never gave us an IP" in v["plain"]
    assert [s["stage"] for s in v["stages"]][-1] == "ip"


def test_dns_failure_stops_before_the_internet_stage(monkeypatch):
    _wire(monkeypatch, dns=False)
    v = srv.wifi_verify()
    assert not v["ok"] and "name lookup fails" in v["plain"]
    assert [s["stage"] for s in v["stages"]][-1] == "dns"


def test_connect_reports_failure_when_the_network_has_no_internet(monkeypatch):
    """nmcli exits 0, so the OLD code said 'now on Event Hall'. It must not."""
    nm = _wire(monkeypatch)
    nm.accept["Event Hall"] = None
    nm.psk["Event"] = None
    nm.uplink["Event Hall"] = "portal"
    ok, msg = srv.wifi_connect("Event Hall")
    assert not ok, "a network with no internet must not report success"
    assert "captive portal" in msg and "still joined" in msg
    assert nm.active == "Event", "and it must not be torn down — the operator may sign in"


# ── the credential that used to be destroyed ─────────────────────────────────

def test_wrong_password_for_a_saved_network_keeps_the_working_one(monkeypatch):
    """One typo while re-entering the password for the network you are ON used
    to overwrite the good secret, fail, and then fail the restore too."""
    nm = _wire(monkeypatch)
    assert nm.psk["Home"] == "oldpw" and nm.active == "Home"
    ok, msg = srv.wifi_connect("Home", "typo")
    assert not ok and "wrong password" in msg
    assert nm.psk["Home"] == "oldpw", "the working password must survive a failed attempt"
    assert nm.active == "Home", "and the robot must come back to the network it was on"


# ── duplicate profiles for one SSID ──────────────────────────────────────────

def test_duplicate_profiles_pick_the_highest_priority(monkeypatch):
    """Verified live on alpha: GlobeAtHome (prio 0) and GlobeAtHome_F98D0
    (prio 5) both carry one SSID, and listing order picked the stale one."""
    nm = _wire(monkeypatch)
    nm.profiles["Home_old"] = "Home"
    nm.priority["Home_old"] = 0
    nm.priority["Home"] = 5
    nm.psk["Home_old"] = "stale"
    srv._wifi_profiles_cache.update(ts=0.0, data=None)
    assert srv._profile_for("Home") == "Home"


def test_an_access_point_profile_is_never_joined(monkeypatch):
    nm = _wire(monkeypatch)
    nm.profiles["HotspotAlias"] = "Home"     # an AP profile carrying a real SSID
    nm.mode["HotspotAlias"] = "ap"
    nm.priority["HotspotAlias"] = 99
    srv._wifi_profiles_cache.update(ts=0.0, data=None)
    assert srv._profile_for("Home") == "Home"


# ── plain words, not raw nmcli ───────────────────────────────────────────────

def test_failures_are_explained_in_words():
    assert srv._explain(4, "Error: Connection activation failed: Secrets were required") \
        == "wrong password"
    assert "not found" in srv._explain(10, "Error: No network with SSID 'x' found.")
    assert "timed out" in srv._explain(-2, "timed out")
    assert "not allowed" in srv._explain(1, "sudo: a password is required")


def test_wifi_info_reports_the_uplink(monkeypatch):
    nm = _wire(monkeypatch)
    monkeypatch.setattr(srv, "run", lambda cmd, timeout=10: (0, "") if cmd[0] == "iwconfig"
                        else nm(cmd, timeout))
    info = srv.wifi_info()
    assert info["essid"] == "Home" and info["ip"] == "192.168.1.50"
    assert info["connectivity"] == "full" and info["online"] is True
    nm.uplink["Home"] = "portal"
    assert srv.wifi_info()["online"] is False
