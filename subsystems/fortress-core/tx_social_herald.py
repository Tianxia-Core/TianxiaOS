#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-SOCIAL-HERALD glue python
"""
tx_social_herald.py -- Social outreach drafts, platform-native.  Generates
X/Twitter, Reddit, HN (Show-HN comment), and LinkedIn drafts from the live
fortress state (track record, SKUs, mission stats).  Posts through available
credentials (Telegram bot now; X/Reddit/LinkedIn await API keys — drafts
queue to CRM activities either way).

Honesty firewall: drafts may only cite ledger numbers.  No invented stats.

Usage:
  tx_social_herald.py drafts                # one draft per platform
  tx_social_herald.py queue <lead_id>       # attach drafts to a CRM lead
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tx_observability as obs
import tx_crm

log = obs.get_logger("tx_social_herald")
BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))
DB = BASE / "db" / "portfolio.sqlite3"
GUMROOD_URLS = {
    "lead_magnet": "https://coltak.gumroad.com/l/dsxuo",
    "kai3_codex": "https://coltak.gumroad.com/l/twylx",
    "asura_matrix": "https://coltak.gumroad.com/l/cbwfy",
    "blueprint": "https://coltak.gumroad.com/l/ekpnaz",
    "manual": "https://coltak.gumroad.com/l/wbevjc",
}


def _ledger_stats() -> dict:
    try:
        con = sqlite3.connect(DB)
        n_herald = 0
        audit = BASE / "logs" / "audit.jsonl"
        if audit.exists():
            n_herald = sum(1 for line in audit.read_text().splitlines()
                           if '"herald.signal"' in line)
        rev = con.execute("select coalesce(sum(amount_usd),0) from rgu_revenue_events").fetchone()[0]
        con.close()
        return {"signals": n_herald, "ledger_usd": round(rev, 2)}
    except Exception:
        return {"signals": 0, "ledger_usd": 0.0}


def drafts() -> dict:
    s = _ledger_stats()
    today = datetime.now(timezone.utc).strftime("%b %d")
    return {
        "x": (
            f"Every trading signal channel shows you winners.\n\nWe publish the "
            f"quiet days too. {s['signals']} signals, ledger-audited, timestamped, "
            f"public record.\n\nThe full track record (free, no email games beyond "
            f"one): {GUMROOD_URLS['lead_magnet']}"
        ),
        "reddit_r_algotrading": (
            f"[Data] I run an automated cross-venue spread monitor and publish every "
            f"signal to a public ledger — including days with no actionable spread. "
            f"{s['signals']} signals so far. Honest question for the sub: would a "
            f"timestamped, no-curation record change how you evaluate signal feeds? "
            f"Free record: {GUMROOD_URLS['lead_magnet']}"
        ),
        "hn_comment": (
            f"Related: I built a substrate that publishes every trading signal it "
            f"emits to an append-only ledger — the audit trail IS the product. "
            f"Track record: {GUMROOD_URLS['lead_magnet']}. Happy to share the "
            f"ledger schema (sqlite + jsonl audit) if useful."
        ),
        "linkedin": (
            f"Most signal vendors sell confidence. We sell evidence.\n\nThe RasaXM "
            f"Alpha feed publishes {s['signals']} timestamped signals to an "
            f"append-only ledger — winners and quiet days alike. The honesty layer "
            f"is the differentiator in a market full of screenshot-merchants.\n\n"
            f"Public record: {GUMROOD_URLS['lead_magnet']}"
        ),
    }


def queue_to_lead(lead_id: int) -> dict:
    d = drafts()
    for platform, text in d.items():
        tx_crm.log_activity(lead_id, "outreach", f"[{platform}] {text[:500]}")
    return {"ok": True, "lead_id": lead_id, "platforms": list(d.keys())}


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "drafts"
    if cmd == "queue":
        print(json.dumps(queue_to_lead(int(sys.argv[2])), indent=1))
    else:
        print(json.dumps(drafts(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
