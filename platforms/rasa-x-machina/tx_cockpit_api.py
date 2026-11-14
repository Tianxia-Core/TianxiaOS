#!/usr/bin/env python3
# ffp: TX-COCKPIT-API io-edge python
"""
tx_cockpit_api.py -- same-origin status API for the Tianxia cockpit PWA.

The cockpit is served by tx-ui (python -m http.server) on :8081 while the model
gateway lives on :8790. Cross-origin fetches from the PWA would need CORS on the
gateway; instead this process owns the cockpit origin and aggregates every
panel's data server-side, so the PWA only ever makes same-origin requests.

Endpoints (all GET, all read-only):
  /api/status   mesh reachability, memory, model count, RF/ADS-B counters
  /api/spectrum newest wideband sweep -> normalized bins for the spectrum panel
  /api/adsb     ADS-B label distribution + recent aircraft
  /api/models   gateway model ids

Security: read-only, binds the mesh IP (not 0.0.0.0), and never shells out with
user input. Static file serving is delegated to the same directory tx-ui already
publishes.

ADDRESSING: the mesh IP is NOT hardcoded, because Tailscale re-keys. This
service used to bind 10.0.99.2; after the tailnet moved to 100.x that address
stopped being local, the process bound a phantom address, and every request
timed out while the unit still reported "active". The host is therefore
resolved at start-up: use the configured address if it is bindable, else the
current tailnet address, else loopback.
"""
from __future__ import annotations

import fcntl
import glob
import json
import logging
import os
import re
import shutil
import socket
import struct
import subprocess
import time
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE = os.environ.get("TX_BASE_DIR", "/var/lib/tianxia")
UI_DIR = os.environ.get("TX_COCKPIT_UI", os.path.join(BASE, "ui"))
# Intent-generated GUIs (tx_genui.py) live in a SHARED dir, not /tmp: this
# service runs with PrivateTmp=yes, so a /tmp dir is invisible to it even
# though the generator wrote it there. The dir is TTL-GC'd by tx_genui.py.
GUI_DIR = os.environ.get("TX_COCKPIT_GUI_DIR", os.path.join(BASE, "gui"))
GUI_TTL_S = float(os.environ.get("TX_COCKPIT_GUI_TTL_S", "3600"))
GUI_NAME_RE = re.compile(r"^[0-9a-f]{8,64}$")
RF_DIR = os.path.join(BASE, "log", "rf")


def _tailscale_binary() -> str:
    """The tailscale CLI, found by absolute path.

    The unit's PATH carries no tailscale, so a plain lookup silently found
    nothing and the mesh list stayed frozen at its hardcoded 10.0.99.x set --
    every node showed "down" in the cockpit panel forever.
    """
    for cand in sorted(glob.glob("/nix/store/*tailscale*/bin/tailscale")):
        if os.access(cand, os.X_OK):
            return cand
    return shutil.which("tailscale") or ""


def _tailscale_peers() -> tuple[str, ...]:
    """Every tailnet IPv4 (self first, then peers), discovered live."""
    binary = _tailscale_binary()
    if not binary:
        return ()
    try:
        out = subprocess.run(
            [binary, "status", "--json"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        ).stdout
        data = json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        log.warning("tailscale status failed: %s", exc)
        return ()
    addrs: list[str] = []
    self_node = data.get("Self") or {}
    for node in [self_node] + list((data.get("Peer") or {}).values()):
        v4 = [a for a in (node.get("TailscaleIPs") or []) if ":" not in a]
        if v4 and v4[0] not in addrs:
            addrs.append(v4[0])
    return tuple(addrs)


_MESH_ENV = os.environ.get("TX_COCKPIT_MESH_NODES", "")
# Fallback when the tailscale CLI is unavailable: the MagicDNS NAMES, which
# survive a re-key (the old 10.0.99.x set is the dead WireGuard mesh).
_MESH_FALLBACK = ("latitude-tianxia.tail7a45a7.ts.net", "xps13-tianxia.tail7a45a7.ts.net",
                  "pixel8pro.tail7a45a7.ts.net", "poco-x5-pro-5g.tail7a45a7.ts.net",
                  "tianxia-relay.tail7a45a7.ts.net")
MESH_NODES = tuple(host.strip() for host in _MESH_ENV.split(",") if host.strip()) or _tailscale_peers() or _MESH_FALLBACK
TIMEOUT = float(os.environ.get("TX_COCKPIT_TIMEOUT", "6"))

log = logging.getLogger("tx_cockpit_api")


def _interface_addresses() -> dict[str, str]:
    """Every IPv4 address actually assigned to a local interface.

    Read straight from the kernel with stdlib only: the unit's PATH carries
    neither `ip` nor `tailscale`, and a plain bind() test is useless here
    because net.ipv4.ip_nonlocal_bind=1 lets the kernel bind an address that
    does not exist (which is exactly how a stale mesh IP kept a dead API
    listening on a phantom address).
    """
    addrs: dict[str, str] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        try:
            interfaces = socket.if_nameindex()
        except (OSError, PermissionError) as exc:
            log.debug("cannot enumerate interfaces: %s", exc)
            return addrs
        for _, name in interfaces:
            try:
                req = struct.pack("256s", name[:15].encode())
                raw = fcntl.ioctl(sock.fileno(), 0x8915, req)  # SIOCGIFADDR
            except OSError as exc:
                log.debug("SIOCGIFADDR failed for %s: %s", name, exc)
                continue
            addrs[name] = socket.inet_ntoa(raw[20:24])
    finally:
        sock.close()
    return addrs


def _local_addresses() -> set[str]:
    return set(_interface_addresses().values())


def _local_bindable(host: str) -> bool:
    """True when this host actually has the address."""
    if not host:
        return False
    return host in _local_addresses()


def _tailscale_ip() -> str:
    """The current tailnet IPv4. It CHANGES when Tailscale re-keys.

    Found from the interface table first (stdlib, no binaries -- the unit's
    PATH has neither `tailscale` nor `ip`), then via those binaries if they
    happen to be present.
    """
    for name, addr in sorted(_interface_addresses().items()):
        if name.startswith("tailscale"):
            return addr
    for cmd in (["tailscale", "ip", "-4"], ["ip", "-4", "addr", "show", "tailscale0"]):
        try:
            out = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5, check=False
            ).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            log.warning("could not run %s: %s", cmd[0], exc)
            continue
        if cmd[0] == "tailscale":
            for line in out.splitlines():
                line = line.strip()
                if line:
                    return line
        else:
            for match in re.finditer(r"inet (\d+\.\d+\.\d+\.\d+)", out):
                return match.group(1)
    return ""


def _resolve_host(host: str) -> str:
    """The bind address, corrected for a stale mesh IP."""
    if host in ("0.0.0.0", "127.0.0.1"):
        return host
    if host and _local_bindable(host):
        return host
    tail = _tailscale_ip()
    if tail and _local_bindable(tail):
        log.warning(
            "configured host %r is not a local address (stale mesh IP?); using %s",
            host,
            tail,
        )
        return tail
    log.warning(
        "configured host %r is not local and no usable tailnet address was found; "
        "falling back to 127.0.0.1",
        host,
    )
    return "127.0.0.1"


_CONFIGURED_HOST = os.environ.get("TX_COCKPIT_HOST", "")
HOST = _resolve_host(_CONFIGURED_HOST)
PORT = int(os.environ.get("TX_COCKPIT_PORT", "8081"))
_CONFIGURED_GATEWAY = os.environ.get("TX_GATEWAY_URL", "")
GATEWAY = _CONFIGURED_GATEWAY or ("http://%s:8790" % HOST)
if _CONFIGURED_GATEWAY:
    # The gateway usually runs on this same box. If its address went stale
    # with the mesh IP, re-point it at the address we actually resolved.
    parsed = urllib.parse.urlsplit(_CONFIGURED_GATEWAY)
    if parsed.hostname and not _local_bindable(parsed.hostname):
        GATEWAY = urllib.parse.urlunsplit(
            (parsed.scheme, "%s:%d" % (HOST, parsed.port or 8790),
             parsed.path, parsed.query, parsed.fragment)
        )
        log.warning("gateway host %r is stale; using %s", parsed.hostname, GATEWAY)


def _http_json(url: str, timeout: float = TIMEOUT):
    """GET a JSON document; returns None on any failure (never raises)."""
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
        log.debug("json fetch failed %s: %s", url, exc)
        return None


def mem_available_mb() -> int:
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except OSError as exc:
        log.debug("meminfo read failed: %s", exc)
    return -1


def tcp_up(host: str, port: int = 22, timeout: float = 1.5) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except OSError as exc:
        log.debug("probe %s failed: %s", host, exc)
        return False


def gateway_models():
    data = _http_json(GATEWAY + "/v1/models")
    if not data:
        return []
    return [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]


def newest_sweep() -> str:
    try:
        files = sorted(Path(RF_DIR).glob("wideband_*.csv"), key=lambda p: p.stat().st_mtime)
        return str(files[-1]) if files else ""
    except (OSError, ValueError) as exc:
        log.debug("sweep scan failed: %s", exc)
        return ""


def spectrum(limit: int = 48) -> dict:
    """Newest wideband sweep -> evenly sampled normalized bins (0..1).

    rtl_power CSV layout (8 comma-separated columns, spaces around negatives):
        date, time, freq_start, freq_stop, bin_width, steps, mean_rssi, peak_rssi
    Column 7 (peak_rssi) is the value to plot; the bin width in column 4 is not.
    """
    path = newest_sweep()
    if not path:
        return {"available": False, "bins": [], "source": ""}
    peaks: list[float] = []
    try:
        with open(path) as fh:
            for row in fh:
                parts = [p.strip() for p in row.strip().split(",")]
                if len(parts) >= 8:
                    peaks.append(float(parts[7]))
    except (OSError, ValueError, IndexError) as exc:
        log.debug("sweep parse failed: %s", exc)
        return {"available": False, "bins": [], "source": path}
    if not peaks:
        return {"available": False, "bins": [], "source": path}
    step = max(1, len(peaks) // limit)
    sampled = peaks[::step][:limit]
    lo, hi = min(sampled), max(sampled)
    span = (hi - lo) or 1.0
    bins = [round((v - lo) / span, 4) for v in sampled]
    top = max(range(len(sampled)), key=lambda i: sampled[i])
    return {
        "available": True,
        "bins": bins,
        "source": os.path.basename(path),
        "n_peak": hi,
        "n_floor": lo,
        "peak_index": top,
    }


def adsb(recent: int = 8) -> dict:
    """Label distribution + most recent frames from the MAHASARASVATI ledger."""
    path = os.path.join(RF_DIR, "adsb_frames.jsonl")
    counts: dict[str, int] = {}
    tail: list[dict] = []
    total = 0
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total += 1
                counts[row.get("label", "OTHER")] = counts.get(row.get("label", "OTHER"), 0) + 1
                tail.append(row)
                if len(tail) > recent:
                    tail.pop(0)
    except OSError as exc:
        log.debug("adsb ledger read failed: %s", exc)
        return {"available": False, "total": 0, "labels": {}, "recent": []}
    return {"available": True, "total": total, "labels": counts, "recent": tail}


def status() -> dict:
    models = gateway_models()
    nodes = [{"host": h, "up": tcp_up(h)} for h in MESH_NODES]
    rf = adsb()
    return {
        "mesh": {"nodes": nodes, "online": sum(1 for n in nodes if n["up"]), "total": len(nodes)},
        "memory": {"available_mb": mem_available_mb()},
        "models": {"count": len(models), "ids": models},
        "adsb": {"total": rf["total"], "labels": rf["labels"]},
        "spectrum": {"available": bool(spectrum(limit=4)["available"])},
    }


ROUTES = {
    "/api/status": status,
    "/api/spectrum": spectrum,
    "/api/adsb": adsb,
    "/api/models": lambda: {"models": gateway_models()},
}


class CockpitHandler(BaseHTTPRequestHandler):
    server_version = "tx-cockpit/1.0"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        log.debug("%s - %s", self.address_string(), fmt % args)

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError as exc:
            log.debug("client write failed: %s", exc)

    def _json(self, payload, code: int = 200) -> None:
        self._send(code, json.dumps(payload).encode("utf-8"), "application/json")

    def _serve_gui(self, name: str) -> None:
        """Serve an intent-generated GUI (tx_genui.py) by its content hash.

        The id is a content hash, so it is validated strictly: hex only, no
        path separators, and the resolved file must stay under the GUI dir.
        The TTL is enforced here as well as in the GC, so an expired GUI is
        never served even between GC runs.
        """
        if name.endswith(".html"):
            name = name[:-5]
        if not GUI_NAME_RE.match(name):
            self._json({"error": "bad gui id"}, code=400)
            return
        try:
            root = Path(GUI_DIR).resolve()
        except OSError as exc:
            log.error("gui dir unresolvable: %s", exc)
            self._json({"error": "gui dir missing"}, code=500)
            return
        target = (root / (name + ".html")).resolve()
        if not str(target).startswith(str(root)):
            self._json({"error": "forbidden"}, code=403)
            return
        if not target.is_file():
            self._json({"error": "not found"}, code=404)
            return
        age = time.time() - target.stat().st_mtime
        if GUI_TTL_S and age > GUI_TTL_S:
            self._json({"error": "expired", "age_s": round(age)}, code=410)
            return
        try:
            data = target.read_bytes()
        except OSError as exc:
            log.error("gui read failed: %s", exc)
            self._json({"error": str(exc)}, code=503)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0]
        if path in ROUTES:
            try:
                self._json(ROUTES[path]())
            except Exception as exc:  # noqa: BLE001 - never 500 the cockpit
                log.exception("route %s failed: %s", path, exc)
                self._json({"error": str(exc)}, code=503)
            return
        if path == "/api/mesh":
            nodes = [{"host": h, "up": tcp_up(h)} for h in MESH_NODES]
            self._json({"nodes": nodes,
                        "online": sum(1 for n in nodes if n["up"]),
                        "total": len(nodes)})
            return
        if path.startswith("/gui/"):
            self._serve_gui(path[len("/gui/"):])
            return
        # static
        rel = path.lstrip("/") or "index.html"
        target = (Path(UI_DIR) / rel).resolve()
        try:
            ui_root = Path(UI_DIR).resolve()
        except OSError as exc:
            log.error("ui root unresolvable: %s", exc)
            self._json({"error": "ui dir missing"}, code=500)
            return
        if not str(target).startswith(str(ui_root)):
            self._json({"error": "forbidden"}, code=403)
            return
        if not target.is_file():
            self._json({"error": "not found"}, code=404)
            return
        ctype = ("text/html" if target.suffix == ".html"
                 else "text/css" if target.suffix == ".css"
                 else "application/javascript" if target.suffix == ".js"
                 else "image/png" if target.suffix == ".png"
                 else "application/manifest+json" if target.suffix == ".webmanifest"
                 else "application/octet-stream")
        try:
            self._send(200, target.read_bytes(), ctype)
        except OSError as exc:
            log.warning("static read failed %s: %s", target, exc)
            self._json({"error": "read failed"}, code=500)


def halted() -> bool:
    """Bāgalamukhī containment: operator stop flags must halt the serve loop."""
    paused = os.path.exists(os.path.join(BASE, "AUTONOMY_PAUSED"))
    stopped = os.path.exists(os.path.join(BASE, "PROBE_STOP"))
    return paused or stopped


def serve(srv: ThreadingHTTPServer) -> None:
    """serve_forever with a kill-switch check so it stays containable."""
    while not halted():
        # handle_request with a timeout returns on each poll, letting us honour
        # the stop flags without waiting for a connection to arrive.
        try:
            srv.handle_request()
        except OSError as exc:
            log.debug("handle_request error: %s", exc)
            break
    log.warning("kill-switch engaged; cockpit api stopping")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )
    if not Path(UI_DIR).is_dir():
        log.error("ui dir missing: %s", UI_DIR)
        return 1
    server = ThreadingHTTPServer((HOST, PORT), CockpitHandler)
    server.timeout = 5  # poll interval for the containment loop
    log.info("cockpit api+static on http://%s:%d (ui=%s, gateway=%s)",
             HOST, PORT, UI_DIR, GATEWAY)
    try:
        serve(server)
    except KeyboardInterrupt:
        log.info("interrupted")
    except Exception as exc:  # noqa: BLE001 - top-level guard
        log.exception("server failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
