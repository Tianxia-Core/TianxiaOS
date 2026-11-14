#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-CRM glue python
"""
tx_crm.py -- In-house CRM for the Faery Fortress.  SQLite-backed, zero
dependencies, bridge-ready.  Pipeline: RAW -> SCORED -> CONTACTED ->
ENGAGED -> NEGOTIATING -> CLOSED_WON | CLOSED_LOST.

Tables: leads, activities, deals.  Every consumer (leadgen, ISO agents,
social outreach, email ops) reads/writes here.  One ledger for humans too:
if it's not in the CRM, it didn't happen.

CLI:
  tx_crm.py add <name> <channel> <source> [notes]     # new lead
  tx_crm.py score <lead_id> <0-100>                   # set ICP score
  tx_crm.py stage <lead_id> <stage>                   # move pipeline
  tx_crm.py note <lead_id> <text>                     # activity log
  tx_crm.py list [--stage S] [--min-score N]          # pipeline view
  tx_crm.py deal <lead_id> <value_usd> <stage>        # attach a deal
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tx_observability as obs

log = obs.get_logger("tx_crm")
BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))
DB = BASE / "db" / "crm.sqlite3"

STAGES = ["RAW", "SCORED", "CONTACTED", "ENGAGED", "NEGOTIATING", "CLOSED_WON", "CLOSED_LOST"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    channel TEXT,              -- email|telegram|x|reddit|github|hn|webform|manual
    source TEXT,               -- campaign/harvest id
    handle TEXT,               -- email/address/@handle
    icp TEXT,                  -- ICP-SOVEREIGN-OP | ICP-TRADER | ICP-DEFENDER | ICP-MERCHANT | ICP-INSTITUTION
    score INTEGER DEFAULT 0,   -- 0-100 ICP fit
    stage TEXT DEFAULT 'RAW',
    owner TEXT DEFAULT 'hussar',
    created_at REAL,
    updated_at REAL,
    notes TEXT DEFAULT '',
    UNIQUE(name, handle)
);
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    ts REAL,
    kind TEXT,                 -- note|outreach|reply|stage_change|deal
    text TEXT
);
CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    value_usd REAL,
    stage TEXT,
    kind TEXT,                 -- sku|iso_residual|subscription|service
    created_at REAL,
    closed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_leads_stage ON leads(stage);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score);
"""


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.executescript(_SCHEMA)
    con.commit()
    return con


def add_lead(name: str, channel: str, source: str, handle: str = "",
             icp: str = "", notes: str = "") -> int:
    con = _con()
    now = time.time()
    cur = con.execute(
        "insert or ignore into leads (name, channel, source, handle, icp, stage, created_at, updated_at, notes) "
        "values (?,?,?,?,?,?,?,?,?)",
        (name, channel, source, handle, icp, "RAW", now, now, notes))
    con.commit()
    lid = cur.lastrowid
    if lid:
        con.execute("insert into activities (lead_id, ts, kind, text) values (?,?,?,?)",
                    (lid, now, "note", f"lead created via {source}"))
        con.commit()
        obs.audit_event(log, "crm.lead.add", key=name, details={"source": source, "icp": icp})
    con.close()
    return lid or 0


def set_stage(lead_id: int, stage: str) -> bool:
    if stage not in STAGES:
        raise ValueError(f"bad stage: {stage}")
    con = _con()
    con.execute("update leads set stage=?, updated_at=? where id=?", (stage, time.time(), lead_id))
    con.execute("insert into activities (lead_id, ts, kind, text) values (?,?,?,?)",
                (lead_id, time.time(), "stage_change", f"-> {stage}"))
    con.commit()
    con.close()
    return True


def set_score(lead_id: int, score: int) -> bool:
    con = _con()
    con.execute("update leads set score=?, stage=CASE WHEN stage='RAW' THEN 'SCORED' ELSE stage END, "
                "updated_at=? where id=?", (max(0, min(100, score)), time.time(), lead_id))
    con.commit()
    con.close()
    return True


def log_activity(lead_id: int, kind: str, text: str) -> None:
    con = _con()
    con.execute("insert into activities (lead_id, ts, kind, text) values (?,?,?,?)",
                (lead_id, time.time(), kind, text))
    con.commit()
    con.close()


def add_deal(lead_id: int, value_usd: float, stage: str, kind: str = "sku") -> int:
    con = _con()
    now = time.time()
    cur = con.execute(
        "insert into deals (lead_id, value_usd, stage, kind, created_at, closed_at) values (?,?,?,?,?,?)",
        (lead_id, value_usd, stage, kind, now, now if stage in ("CLOSED_WON", "CLOSED_LOST") else None))
    con.execute("insert into activities (lead_id, ts, kind, text) values (?,?,?,?)",
                (lead_id, now, "deal", f"{kind} ${value_usd} -> {stage}"))
    con.commit()
    did = cur.lastrowid
    con.close()
    return did


def list_leads(stage: str = "", min_score: int = 0, limit: int = 50) -> list:
    con = _con()
    q = "select id, name, channel, source, handle, icp, score, stage, created_at from leads where score >= ?"
    args = [min_score]
    if stage:
        q += " and stage = ?"
        args.append(stage)
    q += " order by score desc, updated_at desc limit ?"
    args.append(limit)
    rows = con.execute(q, args).fetchall()
    con.close()
    return [dict(zip(["id", "name", "channel", "source", "handle", "icp", "score", "stage", "created_at"], r)) for r in rows]




def import_from_jsonl(path) -> dict:
    """Import leads from a worker JSONL file.  Idempotent via UNIQUE(name, handle)."""
    import json as _json
    con = _con()
    added = skipped = 0
    now = time.time()
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = _json.loads(line)
        except ValueError:
            continue
        cur = con.execute(
            "insert or ignore into leads (name, channel, source, handle, icp, stage, created_at, updated_at, notes) "
            "values (?,?,?,?,?,?,?,?,?)",
            (r["name"], r.get("channel", ""), r.get("source", ""), r.get("handle", ""),
             r.get("icp", ""), "SCORED", now, now, ""))
        if cur.rowcount:
            con.execute("update leads set score=? where id=?", (int(r.get("score", 0)), cur.lastrowid))
            added += 1
        else:
            skipped += 1
    con.commit()
    con.close()
    return {"imported": added, "dup_skipped": skipped}


def pipeline_summary() -> dict:
    con = _con()
    stages = {s: con.execute("select count(*) from leads where stage=?", (s,)).fetchone()[0] for s in STAGES}
    won = con.execute("select coalesce(sum(value_usd),0) from deals where stage='CLOSED_WON'").fetchone()[0]
    open_val = con.execute("select coalesce(sum(value_usd),0) from deals where stage not in ('CLOSED_WON','CLOSED_LOST')").fetchone()[0]
    con.close()
    return {"stages": stages, "closed_won_usd": round(won, 2), "open_pipeline_usd": round(open_val, 2),
            "total_leads": sum(stages.values())}


def _cli() -> int:
    a = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if a == "add":
        lid = add_lead(sys.argv[2], sys.argv[3], sys.argv[4],
                       sys.argv[5] if len(sys.argv) > 5 else "",
                       sys.argv[6] if len(sys.argv) > 6 else "")
        print(json.dumps({"ok": bool(lid), "lead_id": lid}))
    elif a == "stage":
        print(json.dumps({"ok": set_stage(int(sys.argv[2]), sys.argv[3])}))
    elif a == "score":
        print(json.dumps({"ok": set_score(int(sys.argv[2]), int(sys.argv[3]))}))
    elif a == "note":
        log_activity(int(sys.argv[2]), "note", " ".join(sys.argv[3:]))
        print(json.dumps({"ok": True}))
    elif a == "deal":
        print(json.dumps({"deal_id": add_deal(int(sys.argv[2]), float(sys.argv[3]), sys.argv[4],
                                              sys.argv[5] if len(sys.argv) > 5 else "sku")}))
    elif a == "import":
        # read JSONL from stdin: {name, channel, source, handle, icp, score}
        import json as _json
        added = skipped = 0
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                r = _json.loads(line)
            except ValueError:
                continue
            lid = add_lead(r["name"], r.get("channel", ""), r.get("source", ""),
                           r.get("handle", ""), r.get("icp", ""))
            if lid:
                set_score(lid, int(r.get("score", 0)))
                added += 1
            else:
                skipped += 1
        print(_json.dumps({"imported": added, "dup_skipped": skipped}))
    elif a == "list":
        stage = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(list_leads(stage), indent=1))
    else:
        print(json.dumps(pipeline_summary(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
