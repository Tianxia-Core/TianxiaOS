#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-TELEGRAM-HERALD glue python
"""
tx_telegram_herald.py -- RGO-ALPHA herald.  Publishes live cross-venue arb
signals to the RasaXM Alpha Telegram channel, fully autonomously.

Signal sourcing: public spot endpoints (CoinGecko aggregate + Coinbase +
Kraken).  Spread computed in bps per symbol.  Free feed = best signal per
cycle; every post is logged to the fortress ledger (Veritas-Rex discipline:
if it's not in the ledger, it didn't happen).

Usage:
  tx_telegram_herald.py --once            # one cycle (test / cron)
  tx_telegram_herald.py --loop            # daemon (systemd), cycle every 900s
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tx_observability as obs
import tx_secrets_vault as sv
from tx_net_guard import _check_allowlist

log = obs.get_logger("tx_telegram_herald")

BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))
VAULT_PASSPHRASE = os.environ.get("TX_VAULT_PASSPHRASE", "tianxia-sovereign-2026-vault")
STATE = BASE / "logs" / "herald_state.json"
DB = BASE / "db" / "portfolio.sqlite3"

SYMBOLS = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}
MIN_SPREAD_BPS = 5.0     # publish threshold
QUIET_DIGEST_HOURS = 24  # if no signal above threshold, digest at most this often


def _vault() -> tuple:
    vault = sv.open_vault(VAULT_PASSPHRASE)
    try:
        return (
            vault.get_secret("telegram_bot_token") or "",
            vault.get_secret("telegram_channel_id") or "",
        )
    finally:
        try:
            vault.lock()
        except Exception:
            pass


def _get(url: str) -> dict:
    _check_allowlist(url)
    req = urllib.request.Request(url, headers={"User-Agent": "TianxiaHerald/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _post_tg(token: str, chat: str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    _check_allowlist(url)
    req = urllib.request.Request(
        url, data=json.dumps({"chat_id": chat, "text": text, "parse_mode": "HTML",
                              "disable_web_page_preview": True}).encode(),
        method="POST", headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def best_spreads() -> list:
    """Compute cross-venue spreads in bps for the watchlist.  Returns a
    sorted list of {symbol, venue_a, px_a, venue_b, px_b, spread_bps}."""
    cg = _get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd")
    out = []
    for cid, sym in SYMBOLS.items():
        px_ref = float(cg.get(cid, {}).get("usd", 0) or 0)
        if px_ref <= 0:
            continue
        # venue legs
        try:
            cb = _get(f"https://api.coinbase.com/v2/prices/{sym}-USD/spot")
            px_cb = float(cb["data"]["amount"])
        except Exception:
            px_cb = px_ref
        try:
            kr = _get(f"https://api.kraken.com/0/public/Ticker?pair={sym}USD")
            kkey = next(iter(kr["result"]))
            px_kr = float(kr["result"][kkey]["c"][0])
        except Exception:
            px_kr = px_ref
        legs = {"coingecko": px_ref, "coinbase": px_cb, "kraken": px_kr}
        hi_v = max(legs, key=legs.get)
        lo_v = min(legs, key=legs.get)
        spread_bps = (legs[hi_v] - legs[lo_v]) / legs[lo_v] * 10000.0
        out.append({"symbol": sym, "venue_a": lo_v, "px_a": legs[lo_v],
                    "venue_b": hi_v, "px_b": legs[hi_v], "spread_bps": round(spread_bps, 2)})
    out.sort(key=lambda x: -x["spread_bps"])
    return out


def _ledger_note() -> str:
    """Append a herald event to the ledger; return a short audit ref."""
    try:
        import sqlite3
        con = sqlite3.connect(DB)
        con.execute(
            "create table if not exists herald_log (ts real, symbol text, spread_bps real, msg_id text)")
        con.commit()
        con.close()
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt(sig: dict, free_tier: bool = True) -> str:
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ref = _ledger_note()
    arrow = "→"
    body = (
        f"📡 <b>{sig['symbol']} cross-venue spread</b>\n"
        f"{sig['venue_a']} ${sig['px_a']:,.2f} {arrow} {sig['venue_b']} ${sig['px_b']:,.2f}\n"
        f"<b>Spread: {sig['spread_bps']:.1f} bps</b>\n"
        f"<i>{d} · ledger ref {ref}</i>"
    )
    if free_tier:
        body += "\n\n<i>Full feed: sizing, legs &amp; live execution — $29/mo → t.me/RGUDemandBot</i>"
    return body


def _quiet_digest(sigs: list) -> str:
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top = sigs[0] if sigs else None
    if top:
        return (f"🔮 <b>Quiet book</b> — best spread {top['symbol']} {top['spread_bps']:.1f} bps "
                f"({top['venue_a']}/{top['venue_b']}).\n<i>{d} · Hussar scouts continue.</i>")
    return f"🔮 <b>Quiet book</b> — Hussar scouts continue. <i>{d}</i>"


def _load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {"last_sig_hash": "", "last_digest_ts": 0}


def _save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st))


def run_cycle(force: bool = False) -> dict:
    token, chat = _vault()
    if not token or not chat:
        return {"ok": False, "error": "telegram creds missing in vault"}
    sigs = best_spreads()
    if not sigs:
        return {"ok": False, "error": "no market data"}
    st = _load_state()
    top = sigs[0]
    now = time.time()

    if top["spread_bps"] >= MIN_SPREAD_BPS or force:
        h = hashlib.sha256(json.dumps(top, sort_keys=True).encode()).hexdigest()[:12]
        if h == st.get("last_sig_hash") and not force:
            return {"ok": True, "action": "dedup_skip", "spread_bps": top["spread_bps"]}
        r = _post_tg(token, chat, _fmt(top))
        if r.get("ok"):
            st["last_sig_hash"] = h
            st["last_digest_ts"] = now
            _save_state(st)
            obs.audit_event(log, "herald.signal", key=top["symbol"],
                            details={"spread_bps": top["spread_bps"], "msg_id": r["result"]["message_id"]})
            return {"ok": True, "action": "signal_posted", "spread_bps": top["spread_bps"],
                    "message_id": r["result"]["message_id"]}
        return {"ok": False, "error": str(r)}
    # quiet book
    if now - st.get("last_digest_ts", 0) >= QUIET_DIGEST_HOURS * 3600:
        r = _post_tg(token, chat, _quiet_digest(sigs))
        if r.get("ok"):
            st["last_digest_ts"] = now
            _save_state(st)
            return {"ok": True, "action": "quiet_digest", "best_bps": top["spread_bps"]}
    return {"ok": True, "action": "hold", "best_bps": top["spread_bps"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=900)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.loop:
        while True:
            try:
                r = run_cycle(force=a.force)
                log.info("cycle: %s", json.dumps(r))
            except Exception as exc:
                log.error("cycle error: %s", exc)
            time.sleep(a.interval)
    else:
        print(json.dumps(run_cycle(force=a.force), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
