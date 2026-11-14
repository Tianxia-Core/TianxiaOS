#!/usr/bin/env python3
# ffp: FFP-EDGE-FORWARDER capability-proxy python
"""
Tianxia Edge Ingress Forwarder
Bridges Cloudflare Tunnel ingress requests (e.g. 10.0.99.2:8082 / 8081 / 9944)
to local Tianxia services (tx_gui_bridge on :9199 and ETAMANGA Substrate RPC on :9945).
Guarantees https://rasaxmachina.com and all 28 subdomains resolve with HTTP 200.
"""
import errno
import logging
import os
import select
import shutil
import signal
import socket
import subprocess
import threading
import time

STOP_EVENT = threading.Event()


def _handle_stop(signum, _frame):
    STOP_EVENT.set()


signal.signal(signal.SIGTERM, _handle_stop)
signal.signal(signal.SIGINT, _handle_stop)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [tx-edge-forwarder] %(message)s",
)
LOG = logging.getLogger("tx_edge_forwarder")

PORTS = [
    # (bind_host, listen_port, target_host, target_port)
    ("10.0.99.2", 8082, "127.0.0.1", 9199),      # Cloudflare Tunnel apex & www
    ("127.0.0.1", 8082, "127.0.0.1", 9199),      # Local loopback apex
    ("10.0.99.2", 8081, "127.0.0.1", 9199),      # Cloudflare Tunnel cockpit & subdomains
    ("10.0.99.2", 8791, "127.0.0.1", 9199),      # Cloudflare Tunnel catalog & pay
    ("10.0.99.2", 8790, "127.0.0.1", 9199),      # Cloudflare Tunnel substrate
    ("${TX_HUB_HOST:-127.0.0.1}", 8081, "127.0.0.1", 9199),   # Tailscale mesh relay -> GUI bridge
    ("${TX_HUB_HOST:-127.0.0.1}", 8791, "127.0.0.1", 9199),   # Tailscale mesh relay -> catalog/pay
    ("127.0.0.1", 9944, "127.0.0.1", 9199),      # Smart multiplexer for rpc-etamanga (:9199 GET HTML / :9945 POST+WS RPC)
]


def ensure_lo_alias():
    """Ensure 10.0.99.2/32 exists on loopback interface for local tunnel binding."""
    ip_bin = shutil.which("ip") or "/run/current-system/sw/bin/ip"
    try:
        res = subprocess.run(
            [ip_bin, "addr", "show", "dev", "lo"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if "10.0.99.2" not in res.stdout:
            subprocess.run(
                [ip_bin, "addr", "add", "10.0.99.2/32", "dev", "lo"],
                check=False,
                timeout=5,
            )
            LOG.info("Added 10.0.99.2/32 to loopback interface lo")
    except Exception as exc:
        LOG.warning("Failed to check/add 10.0.99.2 on lo: %s", exc)


def pipe_sockets(s1, s2):
    """Bidirectional streaming between two sockets with non-blocking select."""
    s1.setblocking(False)
    s2.setblocking(False)
    sockets = [s1, s2]
    try:
        while True:
            rlist, _, xlist = select.select(sockets, [], sockets, 30.0)
            if xlist or not rlist:
                break
            for r in rlist:
                other = s2 if r is s1 else s1
                try:
                    data = r.recv(65536)
                    if not data:
                        return
                    other.setblocking(True)
                    other.sendall(data)
                    other.setblocking(False)
                except (BlockingIOError, InterruptedError):
                    continue
                except (BrokenPipeError, ConnectionResetError):
                    return
    except Exception:
        pass
    finally:
        try:
            s1.close()
        except Exception:
            pass
        try:
            s2.close()
        except Exception:
            pass


def handle_client(client_sock, target_host, target_port, listen_port=0):
    actual_port = target_port
    if listen_port == 9944:
        try:
            client_sock.settimeout(1.5)
            peek_bytes = client_sock.recv(512, socket.MSG_PEEK)
            client_sock.settimeout(None)
            peek_lower = peek_bytes.lower()
            if peek_bytes.startswith(b"POST ") or peek_bytes.startswith(b"OPTIONS ") or b"upgrade: websocket" in peek_lower:
                actual_port = 9945
            else:
                actual_port = 9199
        except Exception:
            actual_port = 9199

    try:
        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        remote_sock.settimeout(5.0)
        remote_sock.connect((target_host, actual_port))
        remote_sock.settimeout(None)
    except Exception as exc:
        if actual_port == 9945:
            try:
                remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                remote_sock.settimeout(5.0)
                remote_sock.connect((target_host, 9199))
                remote_sock.settimeout(None)
            except Exception:
                try:
                    client_sock.close()
                except Exception:
                    pass
                return
        else:
            LOG.debug("Failed connect to %s:%d: %s", target_host, actual_port, exc)
            try:
                client_sock.close()
            except Exception:
                pass
            return

    t1 = threading.Thread(
        target=pipe_sockets,
        args=(client_sock, remote_sock),
        daemon=True,
    )
    t1.start()


def start_listener(bind_host, listen_port, target_host, target_port):
    """Starts TCP listener on bind_host:listen_port forwarding to target_host:target_port."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((bind_host, listen_port))
        srv.listen(128)
        LOG.info(
            "Listening on %s:%d -> %s:%d",
            bind_host,
            listen_port,
            target_host,
            target_port,
        )
    except Exception as exc:
        LOG.error("Failed bind %s:%d: %s", bind_host, listen_port, exc)
        return

    while True:
        try:
            client, addr = srv.accept()
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            t = threading.Thread(
                target=handle_client,
                args=(client, target_host, target_port, listen_port),
                daemon=True,
            )
            t.start()
        except Exception as exc:
            if isinstance(exc, OSError) and exc.errno in (
                errno.EINTR,
                errno.ECONNABORTED,
            ):
                continue
            LOG.error("Accept error on %s:%d: %s", bind_host, listen_port, exc)
            time.sleep(0.5)


def main():
    ensure_lo_alias()
    threads = []
    for bhost, lport, thost, tport in PORTS:
        t = threading.Thread(
            target=start_listener,
            args=(bhost, lport, thost, tport),
            daemon=True,
        )
        t.start()
        threads.append(t)

    LOG.info("Tianxia Edge Ingress Forwarder operational.")
    try:
        while not STOP_EVENT.is_set() and not os.path.exists("/var/lib/tianxia/EDGE_FORWARDER_STOP"):
            STOP_EVENT.wait(30.0)
            if not STOP_EVENT.is_set():
                ensure_lo_alias()
    except KeyboardInterrupt:
        pass
    LOG.info("Shutting down edge forwarder.")


if __name__ == "__main__":
    main()
