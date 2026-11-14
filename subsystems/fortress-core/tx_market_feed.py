#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-MARKET-FEED glue python
"""
TIANXIA // MARKET FEED  v1.0.0
=============================
Free upstream price feeds for the RGU portfolio. Zero auth, zero cost.
Hydrates the `rgu_market_data` SQLite table with real, current ticks
that the substrate LLM observes via `/api/rgu/market` and
`/stream/rgu-market`.

Sources (all public, no key required):
  - CoinGecko  : https://api.coingecko.com/api/v3/coins/markets
  - Coinbase   : https://api.coinbase.com/v2/prices/BTC-USD/spot
  - Kraken     : https://api.kraken.com/0/public/Ticker?pair=XBTUSD

If a request fails (rate-limit, offline, dns), the script logs and moves
on. The bridge never blocks on this.

Usage:
  $ tx_market_feed.py refresh
  $ tx_market_feed.py refresh --symbols btc,eth,sol
  $ tx_market_feed.py install-cron        # writes bin/tx_market_cron.sh
  $ tx_market_feed.py probe               # one-shot GET /api/rgu/market via bridge
"""
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tx_net_guard import _check_allowlist, is_allowlisted, safe_fetch  # noqa: E402,F401
import argparse
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tx_observability import get_logger, audit_event  # noqa: E402,F401

log = get_logger(__name__)

log.info("%s module ready", __name__)

import json
import os
import sys
import time
import urllib.request
import urllib.error
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))
DB = BASE / "db" / "portfolio.sqlite3"

# SSRF Protection: External API allowlist
ALLOWED_EXTERNAL_HOSTS = {
    "api.coingecko.com",
    "api.coinbase.com",
    "api.exchange.coinbase.com",
    "api.kraken.com",
}

def _validate_external_url(url: str) -> str:
    """Validate external API URL against allowlist to prevent SSRF."""
    parsed = urlparse(url)
    # Only allow https scheme
    if parsed.scheme != "https":
        raise ValueError(f"Invalid scheme (must be https): {parsed.scheme}")
    # Only allow allowed hosts
    if parsed.hostname not in ALLOWED_EXTERNAL_HOSTS:
        raise ValueError(f"External host not allowed: {parsed.hostname}")
    # Only allow https port
    if parsed.port and parsed.port != 443:
        raise ValueError(f"External port not allowed: {parsed.port}")
    # Basic path safety
    if ".." in parsed.path or "//" in parsed.path:
        raise ValueError(f"Suspicious path: {parsed.path}")
    return url

BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))
DB = BASE / "db" / "portfolio.sqlite3"

# Symbol map (ticker -> CoinGecko coin id). Extend as needed.
COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "USDC": "usd-coin", "USDT": "tether", "DAI": "dai",
    "MATIC": "matic-network", "AVAX": "avalanche-2", "DOT": "polkadot",
    "LINK": "chainlink", "UNI": "uniswap", "AAVE": "aave",
    "ATOM": "cosmos", "NEAR": "near", "SUI": "sui",
    "APT": "aptos", "ARB": "arbitrum", "OP": "optimism",
    "TIA": "celestia", "INJ": "injective-protocol",
    "SEI": "sei-network", "PYTH": "pyth-network", "JTO": "jito-governance-token",
    "JUP": "jupiter-exchange-solana", "RNDR": "render-token",
    "FET": "fetch-ai", "TAO": "bittensor", "AKT": "akash-network",
}

SYMBOLS_DEFAULT = ["BTC", "ETH", "SOL", "USDC", "AVAX", "LINK",
                   "MATIC", "ATOM", "NEAR", "SUI", "APT", "ARB",
                   "INJ", "TIA", "JTO", "JUP", "FET", "TAO", "AKT",
                   "AAVE", "UNI", "OP", "SEI", "PYTH", "RNDR",
                   "DOT", "DOGE", "ADA", "XRP"]


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
def fetch_coingecko(symbols):
    """Free public CoinGecko markets endpoint. No auth. ~10-30 calls/min budget."""
    ids = [COINGECKO_IDS[s] for s in symbols if s in COINGECKO_IDS]
    if not ids: return []
    url = ("https://api.coingecko.com/api/v3/coins/markets"
           "?vs_currency=usd&ids=" + ",".join(ids)
           + "&order=market_cap_desc&per_page=" + str(len(ids))
           + "&page=1&sparkline=false"
           + "&price_change_percentage=1h,24h")
    try:
        _validate_external_url(url)  # SSRF protection
        req = urllib.request.Request(url, headers={
            "User-Agent": "Tianxia/1.0 (internal-edition)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"coingecko: {e}", file=sys.stderr)
        return []
    out = []
    for c in data:
        sym = c.get("symbol", "").upper()
        price = c.get("current_price")
        ch24 = c.get("price_change_percentage_24h")
        ch1h = c.get("price_change_percentage_1h_in_currency")
        vol = c.get("total_volume")
        out.append({
            "symbol": f"{sym}-USD",
            "price_usd": price,
            "volume_24h_usd": vol,
            "ch_24h": ch24, "ch_1h": ch1h,
            "spread_bps": None, "bid": None, "ask": None,
            "source": "coingecko",
            "ts": time.time(),
            "meta": {"id": c.get("id"), "mcap": c.get("market_cap"),
                     "rank": c.get("market_cap_rank"),
                     "ath": c.get("ath"), "atl": c.get("atl"),
                     "supply_circ": c.get("circulating_supply"),
                     "supply_max": c.get("max_supply"),
                     "ch_24h": ch24, "ch_1h": ch1h},
        })
    return out


# Kraken symbol -> Kraken pair name. MATIC was rebranded to POL on Kraken.
KRAKEN_PAIRS = {
    "BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD",
    "AVAX": "AVAXUSD", "LINK": "LINKUSD", "MATIC": "POLUSD",
    "DOT": "DOTUSD", "ATOM": "ATOMUSD", "NEAR": "NEARUSD",
    "SUI": "SUIUSD", "APT": "APTUSD", "ARB": "ARBUSD",
    "OP": "OPUSD", "TIA": "TIAUSD", "INJ": "INJUSD",
    "JTO": None,  # not on Kraken
    "JUP": None,
    "FET": None,
    "TAO": None,
    "AKT": None,
    "AAVE": "AAVEUSD", "UNI": "UNIUSD",
    "DOGE": "DOGEUSD", "ADA": "ADAUSD", "XRP": "XRPUSD",
    "USDC": "USDCUSD", "USDT": None,  # USDT not on Kraken
}


def fetch_kraken(symbols):
    """Free public Kraken REST Ticker. No auth. Returns bid/ask/price/volume."""
    pairs = [KRAKEN_PAIRS[s] for s in symbols if KRAKEN_PAIRS.get(s)]
    if not pairs:
        return []
    url = "https://api.kraken.com/0/public/Ticker?pair=" + ",".join(pairs)
    try:
        _validate_external_url(url)  # SSRF protection
        req = urllib.request.Request(url, headers={"User-Agent": "Tianxia/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print(f"kraken: {e}", file=sys.stderr)
        return []
    if data.get("error"):
        return []
    out = []
    for kraken_pair, d in (data.get("result") or {}).items():
        # Kraken returns the WS name (e.g. "XXBTZUSD" for XBT/USD, "XETHZUSD" for ETH/USD).
        # We just match by the Kraken "wsname" or altname (d contains it, but we
        # also get the info from AssetPairs). Since we only have a flat symbol
        # list, match by stripping the leading X/Z heuristically.
        sym = None
        for k, v in KRAKEN_PAIRS.items():
            # Kraken may return XXBTZUSD for XBTUSD — try multiple normalisations
            n = kraken_pair.lstrip("XZ").replace("USD", "").replace("USDC", "").strip()
            if k in ("BTC",) and kraken_pair in ("XBTUSD", "XXBTZUSD"):
                sym = k; break
            if k in ("ETH",) and kraken_pair in ("ETHUSD", "XETHZUSD"):
                sym = k; break
            if v == kraken_pair:
                sym = k; break
        if not sym:
            continue
        try:
            ask = float(d["a"][0])
            bid = float(d["b"][0])
            last = float(d["c"][0])
            vol_24h = float(d["v"][1])  # today
            spread_bps = round((ask - bid) / bid * 10000, 2) if bid > 0 else None
            out.append({
                "symbol": f"{sym}-USD",
                "price_usd": last,
                "bid": bid, "ask": ask, "spread_bps": spread_bps,
                "volume_24h_usd": vol_24h,
                "source": "kraken",
                "ts": time.time(),
                "meta": {"kraken_pair": kraken_pair,
                         "high_24h": float(d["h"][0]), "low_24h": float(d["l"][0]),
                         "open_24h": float(d["o"])},
            })
        except (KeyError, ValueError, IndexError):
            pass
    return out


def fetch_coinbase(symbols):
    """Free public Coinbase Exchange ticker (bid/ask/volume). No auth.
    https://api.exchange.coinbase.com/products/<SYM>-USD/ticker"""
    out = []
    for s in symbols:
        try:
            url = f"https://api.exchange.coinbase.com/products/{s}-USD/ticker"
            _validate_external_url(url)  # SSRF protection
            req = urllib.request.Request(url, headers={
                "User-Agent": "Tianxia/1.0 (internal-edition)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=5) as r:
                d = json.loads(r.read())
            bid = float(d.get("bid", 0)) or None
            ask = float(d.get("ask", 0)) or None
            price = float(d.get("price", 0)) or None
            vol = float(d.get("volume", 0)) or None
            spread_bps = None
            if bid and ask and bid > 0:
                spread_bps = round((ask - bid) / bid * 10000, 2)
            out.append({
                "symbol": f"{s}-USD",
                "price_usd": price,
                "bid": bid, "ask": ask, "spread_bps": spread_bps,
                "volume_24h_usd": vol,
                "source": "coinbase",
                "ts": time.time(),
                "meta": {},
            })
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
            pass
    return out


# ---------------------------------------------------------------------------
# Persist
# ---------------------------------------------------------------------------
def persist(ticks, per_venue_snapshots=None):
    """Persist ticks.

    `ticks` is the canonical per-symbol view (one row per symbol in
    `rgu_market_data`). The `source` field on the canonical row is the
    union of contributing venues.

    `per_venue_snapshots` is an optional list of per-venue rows used to
    populate `rgu_market_snapshots` — one row per (symbol, venue). If
    omitted, we fall back to one snapshot per canonical tick (which
    means the cross-venue spread function only sees a single venue per
    symbol — not useful for arbitrage). The `tx refresh` flow builds
    `per_venue_snapshots` from the raw fetches BEFORE merging.
    """
    if not ticks:
        return 0
    conn = sqlite3.connect(str(DB))
    cur = conn.execute("PRAGMA table_info(rgu_market_data)")
    cols = {row[1] for row in cur.fetchall()}
    if "ch_24h" not in cols:
        conn.execute("ALTER TABLE rgu_market_data ADD COLUMN ch_24h REAL")
    if "ch_1h" not in cols:
        conn.execute("ALTER TABLE rgu_market_data ADD COLUMN ch_1h REAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS rgu_market_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, symbol TEXT, source TEXT,
        price_usd REAL, bid REAL, ask REAL, spread_bps REAL,
        volume_24h_usd REAL, meta_json TEXT)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_snap_symbol_ts
        ON rgu_market_snapshots(symbol, ts)""")
    n = 0
    for t in ticks:
        conn.execute("""INSERT OR REPLACE INTO rgu_market_data
            (symbol, price_usd, bid, ask, spread_bps, volume_24h_usd,
             source, ts, meta_json, ch_24h, ch_1h)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (t["symbol"], t.get("price_usd"),
             t.get("bid"), t.get("ask"), t.get("spread_bps"),
             t.get("volume_24h_usd"),
             t.get("source", "llm"),
             t.get("ts") or time.time(),
             json.dumps(t.get("meta", {})),
             t.get("ch_24h"), t.get("ch_1h")))
        n += 1
    if per_venue_snapshots:
        for t in per_venue_snapshots:
            conn.execute("""INSERT INTO rgu_market_snapshots
                (ts, symbol, source, price_usd, bid, ask, spread_bps,
                 volume_24h_usd, meta_json)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (t.get("ts") or time.time(), t["symbol"], t.get("source", "llm"),
                 t.get("price_usd"), t.get("bid"), t.get("ask"),
                 t.get("spread_bps"), t.get("volume_24h_usd"),
                 json.dumps(t.get("meta", {}))))
    conn.commit()
    conn.close()
    return n


def cross_venue_spread(symbol=None, lookback_s=300):
    """Find the widest cross-venue spread in the snapshot ledger.
    Returns a list of (symbol, venue_a, bid_a, venue_b, ask_b, spread_bps)."""
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    since = time.time() - lookback_s
    q = """SELECT symbol, source, bid, ask, ts FROM rgu_market_snapshots
          WHERE ts > ? AND bid IS NOT NULL AND ask IS NOT NULL"""
    args = [since]
    if symbol:
        q += " AND symbol=?"; args.append(symbol)
    cur.execute(q, args)
    rows = cur.fetchall()
    conn.close()
    # group by symbol
    by_sym = {}
    for s, src, bid, ask, ts in rows:
        by_sym.setdefault(s, []).append((src, bid, ask, ts))
    out = []
    for s, venues in by_sym.items():
        # take latest per venue
        latest = {}
        for src, bid, ask, ts in venues:
            if src not in latest or ts > latest[src][3]:
                latest[src] = (src, bid, ask, ts)
        if len(latest) < 2:
            continue
        # find max spread (lowest bid venue vs highest ask venue)
        venues = list(latest.values())
        lo = min(venues, key=lambda v: v[1])
        hi = max(venues, key=lambda v: v[2])
        if lo[0] == hi[0]:
            continue
        spread_bps = (hi[2] - lo[1]) / lo[1] * 10000
        if spread_bps > 0:
            out.append({"symbol": s,
                        "buy_at": {"venue": lo[0], "price": lo[1]},
                        "sell_at": {"venue": hi[0], "price": hi[2]},
                        "spread_bps": round(spread_bps, 2)})
    out.sort(key=lambda r: r["spread_bps"], reverse=True)
    return out


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------
def cmd_refresh(args):
    symbols = args.symbols.split(",") if args.symbols else SYMBOLS_DEFAULT
    print(f"refreshing {len(symbols)} symbols from coingecko + coinbase + kraken…", file=sys.stderr)
    cg = fetch_coingecko(symbols)
    print(f"  coingecko: {len(cg)} ticks (24h change)", file=sys.stderr)
    cb = []
    if not args.no_coinbase:
        cb = fetch_coinbase([s for s in symbols if s in COINGECKO_IDS])
        print(f"  coinbase:  {len(cb)} ticks (bid/ask)", file=sys.stderr)
    kr = []
    if not args.no_kraken:
        kr = fetch_kraken(symbols)
        print(f"  kraken:    {len(kr)} ticks (bid/ask)", file=sys.stderr)
    # Per-venue snapshots — one row per (symbol, source). This is what
    # cross_venue_spread() reads.
    per_venue = list(cg)
    for t in cb: t2 = dict(t); per_venue.append(t2)
    for t in kr: t2 = dict(t); per_venue.append(t2)
    # Merge: prefer CoinGecko's ch_24h/ch_1h, prefer the freshest bid/ask.
    by_sym = {}
    for t in cg:
        by_sym[t["symbol"]] = dict(t)
    for t in cb:
        s = t["symbol"]
        if s in by_sym:
            for k in ("bid", "ask", "spread_bps", "price_usd"):
                if t.get(k) is not None:
                    by_sym[s][k] = t[k]
            by_sym[s]["source"] = "coingecko+coinbase"
        else:
            by_sym[s] = t
    for t in kr:
        s = t["symbol"]
        if s in by_sym:
            for k in ("bid", "ask", "spread_bps", "price_usd", "volume_24h_usd"):
                if t.get(k) is not None:
                    by_sym[s][k] = t[k]
            by_sym[s]["source"] = (by_sym[s].get("source", "") + "+kraken").lstrip("+")
        else:
            by_sym[s] = t
    merged = list(by_sym.values())
    n = persist(merged, per_venue_snapshots=per_venue)
    spreads = cross_venue_spread(lookback_s=600)
    if spreads:
        print("top cross-venue spreads (dry-run):", file=sys.stderr)
        for s in spreads[:5]:
            print(f"  {s['symbol']:12}  buy {s['buy_at']['venue']:>32} ${s['buy_at']['price']:.4f}"
                  f"  sell {s['sell_at']['venue']:>32} ${s['sell_at']['price']:.4f}"
                  f"  Δ {s['spread_bps']} bps", file=sys.stderr)
    print(json.dumps({"ok": True, "ticks_persisted": n,
                      "with_bid_ask": sum(1 for t in merged if t.get("bid")),
                      "with_24h": sum(1 for t in merged if t.get("ch_24h") is not None),
                      "snapshots_written": len(per_venue),
                      "top_spread_bps": spreads[0]["spread_bps"] if spreads else 0}))


def cmd_install_cron(_):
    sh = BASE / "bin" / "tx_market_cron.sh"
    sh.write_text(f"""#!/usr/bin/env bash
# Auto-installed by tx_market_feed.py — refresh market ticks + run arb worker every 5 minutes.
set -e
export TX_BASE_DIR="{BASE}"
echo "[$(date -Is)] refresh"
{sys.executable} "{Path(__file__).resolve()}" refresh >> "{BASE / 'logs' / 'market_feed.log'}" 2>&1
echo "[$(date -Is)] cross-venue (top 5)"
{sys.executable} "{Path(__file__).resolve()}" cross-venue --lookback 600 >> "{BASE / 'logs' / 'market_feed.log'}" 2>&1
echo "[$(date -Is)] arb-once (min 5bps)"
TX_ARB_MIN_BPS=5 {sys.executable} "{BASE / 'bin' / 'tx_arb_worker.py'}" once >> "{BASE / 'logs' / 'market_feed.log'}" 2>&1
""")
    sh.chmod(0o755)
    print(f"wrote {sh} (add '*/5 * * * * {sh}' to your cron)")


def cmd_probe(_):
    # call /api/rgu/market via the bridge, print the symbols we see
    try:
        req = urllib.request.Request(
            f"http://{os.environ.get('TX_BRIDGE_HOST','127.0.0.1')}:"
            f"{os.environ.get('TX_BRIDGE_PORT','9199')}/api/rgu/market",
            headers={"Authorization": "Bearer " + (BASE / "secrets" / "substrate_auth.token").read_text().strip()})
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read())
        print(json.dumps(d, default=str)[:1500])
    except Exception as e:
        print(f"probe failed: {e}", file=sys.stderr)


def cmd_cross_venue(args):
    spreads = cross_venue_spread(symbol=args.symbol or None,
                                 lookback_s=args.lookback)
    print(json.dumps({"ok": True, "count": len(spreads), "spreads": spreads}, indent=2, default=str))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("refresh")
    p.add_argument("--symbols", default="")
    p.add_argument("--no-coinbase", action="store_true")
    p.add_argument("--no-kraken", action="store_true")
    p2 = sub.add_parser("cross-venue")
    p2.add_argument("--symbol", default="")
    p2.add_argument("--lookback", type=int, default=600)
    sub.add_parser("install-cron")
    sub.add_parser("probe")
    args = ap.parse_args()
    {"refresh": cmd_refresh, "install-cron": cmd_install_cron,
     "probe": cmd_probe,
     "cross-venue": cmd_cross_venue}[args.cmd](args)


if __name__ == "__main__":
    main()
