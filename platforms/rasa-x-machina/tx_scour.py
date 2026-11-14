#!/usr/bin/env python3
# ffp: TX-SCOUR io-edge python
"""tx_scour.py -- unified scour dispatcher (thin merge slice, App D.3).

Adapter registry over existing fetchers (no logic duplication, no refetch):
  scour modes -> bin/tx_scour_extra.py <mode> --hits N
  github/arxiv -> bin/tx_opportunity_mine.py <sub>
  threat       -> bin/tx_threatintel.py --hits N (CISA-KEV/NVD/URLhaus/ThreatFox)
  propose      -> mine propose --infile <staged fetch output>
  refresh      -> scour all + github + arxiv + threat + propose (one call)

Merges stdout JSONL, dedupes by url (fallback: source+name), writes
append-only MERGED_SIGNALS.jsonl {source,subsource,kind,title,text,url,
metrics,score,ts}. SIGNALS_EXTRA.json / OPPORTUNITIES.json / omen_store.json
remain derived views owned by their writers.

REVISION: TX-SCOUR-001
Env: TX_BASE_DIR, TX_SCOUR_HITS, TX_SCOUR_OUT, TX_SCOUR_TIMEOUT_S.
Honors AUTONOMY_PAUSED / PROBE_STOP. Subprocesses via list-args only.
capability note: subprocess targets are fixed to sibling fetcher scripts in
THIS_DIR (tx_scour_extra.py, tx_opportunity_mine.py, tx_threatintel.py); no
remote input, no systemctl/nft/socket surfaces. Writes confined to --out.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import time

REVISION = "TX-SCOUR-001"
log = logging.getLogger("tx_scour")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_DIR = os.path.dirname(THIS_DIR)
BASE = os.environ.get("TX_BASE_DIR") or ("/var/lib/tianxia" if os.path.isdir("/var/lib/tianxia") else _REPO_DIR)
HITS = int(os.environ.get("TX_SCOUR_HITS", "20"))
TIMEOUT_S = int(os.environ.get("TX_SCOUR_TIMEOUT_S", "280"))
DEFAULT_OUT = os.environ.get(
    "TX_SCOUR_OUT",
    os.path.join(BASE, "docs", "ndimmorwyn", "MERGED_SIGNALS.jsonl"))

SCOUR_MODES = ("defillama", "hn", "gnews", "fediverse", "gitee", "codeberg",
               "nature", "crypto", "vast", "fragment", "merchant", "quota",
               "livelihood", "recovery", "triad", "asura", "x402", "digest")
MINE_SUBS = ("github", "arxiv")
PY = [sys.executable]


def _kill_switch() -> bool:
    return bool(os.environ.get("AUTONOMY_PAUSED") or os.environ.get("PROBE_STOP"))


def run_adapter(args: list[str], timeout: int) -> list[dict]:
    """Run one fetcher, return parsed JSONL records (skip non-JSON lines)."""
    try:
        proc = subprocess.run(args, capture_output=True, text=True,
                              timeout=timeout, cwd=BASE)
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("adapter failed %s: %s", args[2] if len(args) > 2 else args,
                    exc)
        return []
    if proc.returncode != 0:
        log.warning("adapter rc=%d %s: %s", proc.returncode, args,
                    (proc.stderr or "")[:200])
    records = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            records.append(obj)
    return records


def normalize(obj: dict) -> dict:
    raw_text = obj.get("desc", obj.get("summary", obj.get("text", "")))
    return {"source": str(obj.get("source", "unknown")),
            "subsource": str(obj.get("query", obj.get("subsource", ""))),
            "kind": str(obj.get("type", obj.get("kind", "signal"))),
            "title": str(obj.get("name", obj.get("title", ""))),
            "text": str(raw_text or "")[:500],
            "url": str(obj.get("url", obj.get("ref", ""))),
            "metrics": {k: obj.get(k) for k in
                        ("apy", "tvlUsd", "stars", "score") if obj.get(k) is not None},
            "score": obj.get("score"),
            "ts": obj.get("ts", time.time())}


def dedupe(records: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for rec in records:
        key = rec["url"] or (rec["source"], rec["title"])
        if key in seen or not rec["title"]:
            continue
        seen.add(key)
        out.append(rec)
    return out


def collect(mode: str, hits: int) -> list[dict]:
    if _kill_switch():
        raise RuntimeError("kill-switch engaged, refusing to scour")
    gathered: list[dict] = []
    if mode in ("all", "refresh"):
        modes = list(SCOUR_MODES)
    elif mode in SCOUR_MODES:
        modes = [mode]
    else:
        modes = []
    for m in modes:
        gathered.extend(run_adapter(
            PY + [os.path.join(THIS_DIR, "tx_scour_extra.py"), m, "--hits",
                  str(hits)], TIMEOUT_S))
    if mode in ("all", "refresh", "threat"):
        gathered.extend(run_adapter(
            PY + [os.path.join(THIS_DIR, "tx_threatintel.py"), "--hits",
                  str(hits)], TIMEOUT_S))
    fetch_out: list[dict] = []
    if mode in ("all", "refresh", "github", "arxiv"):
        subs = list(MINE_SUBS) if mode in ("all", "refresh") else [mode]
        for sub in subs:
            fetch_out.extend(run_adapter(
                PY + [os.path.join(THIS_DIR, "tx_opportunity_mine.py"), sub],
                150))
    if mode in ("refresh", "propose"):
        stage = None
        try:
            if mode == "refresh" or fetch_out:
                with tempfile.NamedTemporaryFile("w", suffix=".jsonl",
                                                 delete=False) as fh:
                    for obj in fetch_out:
                        fh.write(json.dumps(obj) + "\n")
                    stage = fh.name
                if stage:
                    propose = run_adapter(
                        PY + [os.path.join(THIS_DIR, "tx_opportunity_mine.py"),
                              "propose", "--infile", stage], 150)
                    gathered.extend(propose)
        finally:
            if stage:
                try:
                    os.remove(stage)
                except OSError as exc:
                    log.warning("stage cleanup failed: %s", exc)
    elif mode == "propose":
        log.warning("propose needs fetch output; use refresh or github+arxiv first")
    gathered.extend(fetch_out)
    return dedupe([normalize(r) for r in gathered])


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="unified scour dispatcher")
    ap.add_argument("mode", nargs="?",
                    choices=("all", "refresh", "propose", "threat") + SCOUR_MODES + MINE_SUBS,
                    default="all")
    ap.add_argument("--hits", type=int, default=HITS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0,
                    help="print first N merged records (0 = count only)")
    args = ap.parse_args(argv)
    try:
        merged = collect(args.mode, args.hits)
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1
    try:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "a", encoding="utf-8") as fh:
            for rec in merged:
                fh.write(json.dumps(rec) + "\n")
    except OSError as exc:
        log.error("write failed %s: %s", args.out, exc)
        return 1
    print(f"merged {len(merged)} records -> {args.out}")
    for rec in merged[:args.limit]:
        print(json.dumps(rec)[:220])
    return 0


if __name__ == "__main__":
    sys.exit(main())
