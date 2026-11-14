#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-LEADGEN glue python
"""
tx_leadgen.py -- Demand-generation harvester.  Sources public surfaces
(HackerNews Algolia API, Reddit public JSON, GitHub search), scores leads
against ICP keyword matrices, dedups, and feeds tx_crm.

ICP keyword matrices (Axiom of Amoral Strategy: measurable fit only):
  ICP-MERCHANT  — high-risk verticals seeking payment (ISO engine feeds this)
  ICP-SOVEREIGN-OP — self-hosters / indie hackers
  ICP-TRADER    — algo/quant traders
  ICP-DEFENDER  — security teams

Usage:
  tx_leadgen.py harvest            # run all sources, insert into CRM
  tx_leadgen.py harvest --source hn
  tx_leadgen.py top <n>            # highest-scored RAW leads
"""
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tx_observability as obs
import tx_crm
from tx_net_guard import _check_allowlist

log = obs.get_logger("tx_leadgen")

ICP_KEYWORDS = {
    "ICP-MERCHANT": ["high risk", "high-risk", "payment processor", "merchant account",
                     "iso", "acquiring", "chargeback", "cbd payments", "gaming payments",
                     "offshore payment", "visa mastercard"],
    "ICP-SOVEREIGN-OP": ["self-hosted", "self-hosting", "indie hacker", "nixos", "homelab",
                         "solo founder", "bootstrapped", "rag", "local llm", "self hosted ai"],
    "ICP-TRADER": ["algo trading", "arbitrage", "market making", "quant", "trading bot",
                   "funding rate", "spread", "backtest", "strategy"],
    "ICP-DEFENDER": ["honeypot", "deception", "siem", "threat detection", "soc", "red team",
                     "incident response", "ciso", "yara", "threat intel"],
}


def score_text(text: str) -> tuple:
    low = text.lower()
    best_icp, best_score = "", 0
    for icp, kws in ICP_KEYWORDS.items():
        s = sum(3 for kw in kws if kw in low)
        if s > best_score:
            best_icp, best_score = icp, s
    return best_icp, min(100, best_score * 8)


def _get(url: str) -> bytes:
    _check_allowlist(url)
    req = urllib.request.Request(url, headers={"User-Agent": "TianxiaHussar/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def harvest_hn(queries: list = None, capture: list = None) -> int:
    """HackerNews Algolia search -> CRM.  Who's-hiring / seeking-founder threads
    plus topical searches per ICP."""
    added = 0
    queries = queries or ["high risk merchant", "payment processor rejected",
                          "self-hosted AI", "algo trading bot", "honeypot detection",
                          "ISO agent payment"]
    for q in queries:
        try:
            url = ("https://hn.algolia.com/api/v1/search?query="
                   + urllib.parse.quote(q) + "&tags=story&hitsPerPage=15")
            data = json.loads(_get(url))
            for hit in data.get("hits", []):
                title = hit.get("title") or ""
                author = hit.get("author") or ""
                object_id = hit.get("objectID") or ""
                if not title:
                    continue
                icp, score = score_text(title + " " + (hit.get("story_text") or "")[:500])
                if score < 12:
                    continue
                if capture is not None:
                    capture.append({"name": title[:120], "channel": "hn", "source": f"hn:{q}",
                                    "handle": f"hn.com/item?id={object_id}", "icp": icp, "score": score})
                else:
                    lid = tx_crm.add_lead(title[:120], "hn", f"hn:{q}", handle=f"hn.com/item?id={object_id}",
                                          icp=icp, notes=f"author={author} pts={hit.get('points')}")
                    if lid:
                        tx_crm.set_score(lid, score)
                        added += 1
        except Exception as e:
            log.warning("hn harvest fail %s: %s", q, str(e)[:80])
    return added


def harvest_reddit(subs: list = None, capture: list = None) -> int:
    """Reddit public JSON from business/trading/security subs -> CRM."""
    added = 0
    subs = subs or ["merchants", "PaymentProcessing", "highriskmerchant", "algotrading",
                    "selfhosted", "cybersecurity"]
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            data = json.loads(_get(url))
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                title = d.get("title", "")
                if d.get("stickied") or not title:
                    continue
                icp, score = score_text(title + " " + (d.get("selftext") or "")[:400])
                if score < 12:
                    continue
                if capture is not None:
                    capture.append({"name": title[:120], "channel": "reddit", "source": f"reddit:r/{sub}",
                                    "handle": f"reddit.com{d.get('permalink', '')}", "icp": icp, "score": score})
                else:
                    lid = tx_crm.add_lead(title[:120], "reddit", f"reddit:r/{sub}",
                                          handle=f"reddit.com{d.get('permalink', '')}", icp=icp)
                    if lid:
                        tx_crm.set_score(lid, score)
                        added += 1
        except Exception as e:
            log.warning("reddit harvest fail r/%s: %s", sub, str(e)[:80])
    return added


def harvest() -> dict:
    n_hn = harvest_hn()
    n_rd = harvest_reddit()
    summary = tx_crm.pipeline_summary()
    obs.audit_event(log, "leadgen.harvest", key="crm",
                    details={"hn": n_hn, "reddit": n_rd, "total_leads": summary["total_leads"]})
    return {"ok": True, "hn_new": n_hn, "reddit_new": n_rd, "pipeline": summary}


def top(n: int = 10) -> list:
    return tx_crm.list_leads(min_score=20, limit=n)


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "capture":
        captured = []
        saved_hn = harvest_hn.__wrapped__ if hasattr(harvest_hn, "__wrapped__") else None
        cap = []
        # run both harvesters in capture mode
        import json as _json
        for q in ["high risk merchant", "payment processor rejected", "self-hosted AI",
                  "algo trading bot", "honeypot detection", "ISO agent payment"]:
            try:
                harvest_hn([q], capture=cap)
            except Exception:
                pass
        for sub in ["merchants", "PaymentProcessing", "highriskmerchant", "algotrading",
                    "selfhosted", "cybersecurity"]:
            try:
                harvest_reddit([sub], capture=cap)
            except Exception:
                pass
        for row in cap:
            print(_json.dumps(row))
    elif len(sys.argv) > 1 and sys.argv[1] == "harvest":
        print(json.dumps(harvest(), indent=1))
    elif len(sys.argv) > 1 and sys.argv[1] == "top":
        print(json.dumps(top(int(sys.argv[2]) if len(sys.argv) > 2 else 10), indent=1))
    else:
        print(json.dumps({"usage": "harvest | top <n>"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
