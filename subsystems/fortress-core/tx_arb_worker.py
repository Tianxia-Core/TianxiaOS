#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-ARB-WORKER glue python
"""
TIANXIA // AUTO-ARBITRAGE LLM WORKER  v1.0.0
===========================================
The substrate's arbitrage loop. Observes cross-venue spreads via the
bridge, opens paper allocations against `arb_spread_x_usd`, monitors
the spread until it closes or the TTL elapses, and records realized
PnL via /api/rgu/portfolio/upsert action=close.

This is DRY-RUN by default. The LLM is the executor; the founder
decides when to fund a real exchange account. The substrate never
holds money.

Usage:
  $ tx_arb_worker.py once             # one cycle (good for cron)
  $ tx_arb_worker.py loop --interval 60 --max-open 5
  $ tx_arb_worker.py status           # show open positions
  $ tx_arb_worker.py close-all        # close all open positions
"""
import argparse
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tx_observability import get_logger, audit_event  # noqa: E402,F401

log = get_logger(__name__)

log.info("%s module ready", __name__)

from tx_auth import require_auth, verify_jwt, has_permission  # noqa: E402,F401
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))
HOST = os.environ.get("TX_BRIDGE_HOST", "127.0.0.1")
PORT = os.environ.get("TX_BRIDGE_PORT", "9199")
TOKEN_FILE = BASE / "secrets" / "substrate_auth.token"

# SSRF Protection: Allowed paths and URL validation
ALLOWED_PATHS = {
    "/api/rgu/market/cross-venue",
    "/api/rgu/portfolio",
    "/api/rgu/portfolio/upsert",
    "/api/health",
    "/api/status.json",
}
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}
ALLOWED_PORTS = {"9199", "9191"}  # bridge + timesfm

def _validate_url(url: str) -> str:
    """Validate URL against allowlist to prevent SSRF."""
    parsed = urlparse(url)
    # Only allow http scheme
    if parsed.scheme != "http":
        raise ValueError(f"Invalid scheme: {parsed.scheme}")
    # Only allow allowed hosts
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Host not allowed: {parsed.hostname}")
    # Only allow allowed ports
    if parsed.port and str(parsed.port) not in ALLOWED_PORTS:
        raise ValueError(f"Port not allowed: {parsed.port}")
    # Only allow allowed paths
    if parsed.path not in ALLOWED_PATHS:
        raise ValueError(f"Path not allowed: {parsed.path}")
    # Reject any query params that look suspicious (basic check)
    query = parsed.query
    if ".." in query or "|" in query or ";" in query:
        raise ValueError(f"Suspicious query params: {query}")
    return url

def token():
    return TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else ""


def http_get(path):
    url = f"http://{HOST}:{PORT}{path}"
    _validate_url(url)  # SSRF protection
    req = urllib.request.Request(url,
                                 headers={"Authorization": "Bearer " + token()})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def http_post(path, body):
    url = f"http://{HOST}:{PORT}{path}"
    _validate_url(url)  # SSRF protection
    req = urllib.request.Request(url,
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + token()},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


# ---------------------------------------------------------------------------
# Cycle
# ---------------------------------------------------------------------------
def fetch_spreads():
    return http_get("/api/rgu/market/cross-venue?lookback=600")


def open_positions():
    """Return the list of OPEN allocations across all templates.
    The bridge's /api/rgu/portfolio returns:
      {"summary": {...}, "open": {"ok":..., "allocations": [...]}, "all": {...}}
    """
    d = http_get("/api/rgu/portfolio")
    return (d.get("open") or {}).get("allocations", []) or []


def has_arb_open():
    return any(a.get("template_id") == ARB_TEMPLATE and a.get("status") == "open"
               for a in open_positions())


def open_arb(symbol, buy_price, sell_price, spread_bps):
    return http_post("/api/rgu/portfolio/upsert", {
        "action": "open",
        "template_id": ARB_TEMPLATE,
        "principal_usd": PRINCIPAL_USD,
        "notes": f"auto-arb {symbol} {buy_price:.4f}->{sell_price:.4f} Δ {spread_bps:.2f}bps t={int(time.time())}",
    })


def close_arb(alloc_id, exit_value, notes):
    return http_post("/api/rgu/portfolio/upsert", {
        "action": "close",
        "alloc_id": alloc_id,
        "exit_value_usd": exit_value,
        "notes": notes,
    })


def find_arb_alloc_for_symbol(symbol):
    for a in open_positions():
        if (a.get("template_id") == ARB_TEMPLATE
                and a.get("status") == "open"
                and symbol in (a.get("notes") or "")):
            return a
    return None


def cycle():
    spreads = fetch_spreads().get("spreads", [])
    acted = 0
    # 1. close positions whose spread has collapsed (or TTL elapsed)
    for a in open_positions():
        if a.get("template_id") != ARB_TEMPLATE or a.get("status") != "open":
            continue
        notes = a.get("notes") or ""
        # extract symbol from notes (e.g. "auto-arb BTC-USD ...")
        sym = None
        for token in notes.split():
            if "-" in token and token[0].isalpha():
                sym = token
                break
        if not sym:
            continue
        # find current spread for this symbol
        current = next((s for s in spreads if s.get("symbol") == sym), None)
        if not current:
            # spread not found - keep position open
            continue
        current_bps = current.get("spread_bps", 0)
        # close if spread collapsed below min or TTL elapsed
        opened_at = a.get("opened_at", 0)
        age = time.time() - opened_at
        if current_bps < SPREAD_MIN_BPS or age > TTL_SECONDS:
            # estimate exit value (simplified: principal + spread PnL)
            principal = a.get("principal_usd", PRINCIPAL_USD)
            pnl = principal * (current_bps / 10000.0) * (age / 3600.0)
            exit_val = principal + pnl
            close_arb(a["alloc_id"], exit_val, f"spread collapsed {current_bps:.2f}bps age={age:.0f}s")
            acted += 1
    # 2. open new arb if slot available and spread exceeds min
    if not has_arb_open() and len(open_positions()) < MAX_OPEN:
        for s in spreads:
            sym = s.get("symbol")
            spread_bps = s.get("spread_bps", 0)
            if spread_bps >= SPREAD_MIN_BPS:
                buy_price = s.get("buy_price", 0)
                sell_price = s.get("sell_price", 0)
                if buy_price and sell_price:
                    open_arb(sym, buy_price, sell_price, spread_bps)
                    acted += 1
                    break
    return acted


def once():
    acted = cycle()
    print(json.dumps({"acted": acted, "open_positions": len(open_positions())}))


def loop(interval: int, max_open: int):
    global MAX_OPEN
    MAX_OPEN = max_open
    print(f"[ARB] loop started interval={interval}s max_open={max_open}")
    try:
        while True:
            try:
                acted = cycle()
                if acted:
                    print(f"[ARB] acted={acted} open={len(open_positions())}")
            except Exception as e:
                print(f"[ARB] cycle error: {e}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[ARB] stopped")


def status():
    print(json.dumps({"open_positions": len(open_positions()), "details": open_positions()}))


def close_all():
    for a in open_positions():
        if a.get("status") == "open":
            close_arb(a["alloc_id"], a.get("principal_usd", PRINCIPAL_USD), "manual close-all")
    print(json.dumps({"closed": "all"}))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("once", help="Run one arbitrage cycle")
    p_loop = sub.add_parser("loop", help="Run continuous loop")
    p_loop.add_argument("--interval", type=int, default=60, help="Seconds between cycles")
    p_loop.add_argument("--max-open", type=int, default=5, help="Max concurrent positions")
    sub.add_parser("status", help="Show open positions")
    sub.add_parser("close-all", help="Close all open positions")
    args = parser.parse_args()
    if args.cmd == "once":
        once()
    elif args.cmd == "loop":
        loop(args.interval, args.max_open)
    elif args.cmd == "status":
        status()
    elif args.cmd == "close-all":
        close_all()

if __name__ == "__main__":
    main()
