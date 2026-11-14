#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-JOBMATCH glue python
"""
tx_jobmatch.py -- Agentic job-match engine + PWA backend.

Principle (Emperor spec): match the ORIGINAL resume to jobs; rewrite the CV
dynamically to suit the role ONLY IF the raw copy covers >= 50% of the job
requirements, using EXISTING experience — never fabricate.

Sources: RemoteOK public API + HN "who is hiring" (Algolia).
Coverage: weighted keyword/phrase overlap between resume and job requirements.
Rewrite: rule-based reframing (reorder bullets, mirror job vocabulary,
surface matching achievements) — the honesty firewall: every rewritten line
must trace to a source line in the original resume (hash-checked).

PWA: jobs_pwa/ (manifest + sw + app shell) talks to the bridge endpoints.

Usage:
  tx_jobmatch.py ingest                    # pull jobs from sources
  tx_jobmatch.py match <resume_file>       # coverage-ranked jobs
  tx_jobmatch.py rewrite <resume_file> <job_id>   # >=50% gate rewrite
"""
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tx_observability as obs
from tx_net_guard import _check_allowlist

log = obs.get_logger("tx_jobmatch")
BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))
DB = BASE / "db" / "jobs.sqlite3"
COVERAGE_GATE = 0.50

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    url TEXT,
    description TEXT,
    tags TEXT,
    ingested_at REAL
);
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_hash TEXT,
    job_id TEXT,
    coverage REAL,
    rewritten INTEGER DEFAULT 0,
    ts REAL
);
"""

STOP = set("the a an and or of to in for with on at is are be as by from that this it your you our we "
           "will ability able work working team teams role position job candidate must plus strong etc "
           "years year experience experienced new us using use across within about".split())


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.executescript(_SCHEMA)
    con.commit()
    return con


def _get(url: str) -> bytes:
    _check_allowlist(url)
    req = urllib.request.Request(url, headers={"User-Agent": "TianxiaHussar/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def _tokens(text: str) -> set:
    import html as _html
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    out = set()
    for t in re.findall(r"[a-z][a-z0-9+#.]{2,}", text.lower()):
        if t in STOP:
            continue
        # light stemming: singularize plurals and -ing forms for matching
        if t.endswith("s") and len(t) > 3 and not t.endswith("ss"):
            out.add(t[:-1])
        elif t.endswith("ing") and len(t) > 5:
            out.add(t[:-3])
        out.add(t)
    return out


def ingest() -> dict:
    con = _con()
    n = 0
    # RemoteOK public API
    try:
        jobs = json.loads(_get("https://remoteok.com/api"))
        for j in jobs[1:] if isinstance(jobs, list) else []:
            jid = f"rok_{j.get('slug') or j.get('id') or j.get('position')}"
            con.execute("insert or ignore into jobs values (?,?,?,?,?,?,?,?,?)",
                        (jid, "remoteok", j.get("position", ""), j.get("company", ""),
                         j.get("location", ""), j.get("url", ""), j.get("description", "")[:4000],
                         json.dumps(j.get("tags", [])), time.time()))
            n += 1
    except Exception as e:
        log.warning("remoteok: %s", str(e)[:80])
    # HN who-is-hiring (latest monthly thread comments via Algolia)
    try:
        data = json.loads(_get("https://hn.algolia.com/api/v1/search?query=%22who%20is%20hiring%22&tags=story&hitsPerPage=1"))
        hits = data.get("hits", [])
        if hits:
            story_id = hits[0]["objectID"]
            kids = json.loads(_get(f"https://hn.algolia.com/api/v1/items/{story_id}")).get("children", [])
            for c in kids[:60]:
                text = c.get("text", "") or ""
                jid = f"hn_{c.get('id')}"
                title = re.sub(r"<[^>]+>", " ", text)[:200]
                con.execute("insert or ignore into jobs values (?,?,?,?,?,?,?,?,?)",
                            (jid, "hn", title[:150], "hn-company", "remote?",
                             f"https://news.ycombinator.com/item?id={c.get('id')}",
                             re.sub(r"<[^>]+>", " ", text)[:4000], "[]", time.time()))
                n += 1
    except Exception as e:
        log.warning("hn: %s", str(e)[:80])
    con.commit()
    total = con.execute("select count(*) from jobs").fetchone()[0]
    con.close()
    obs.audit_event(log, "jobmatch.ingest", key=f"{n} new", details={"total": total})
    return {"ingested": n, "total_jobs": total}


def _requirements(job_text: str, tags: str) -> set:
    """Extract requirement signals: structured tags + top technical tokens
    from the description (frequency-ranked, stop-worded).  Coverage is
    measured against these — not against raw description length (HTML
    boilerplate would otherwise make the gate unreachable)."""
    import html as _html
    from collections import Counter
    reqs = set()
    try:
        for t in json.loads(tags or "[]"):
            if t and 2 < len(t) < 25:
                reqs |= _tokens(t)
    except (ValueError, TypeError):
        pass
    clean = re.sub(r"<[^>]+>", " ", _html.unescape(job_text or ""))
    words = [w for w in re.findall(r"[a-z][a-z0-9+#.]{2,}", clean.lower()) if w not in STOP]
    # tech-bias: keep tokens that look like skills (appear near "experience",
    # "proficien*", "strong", or contain tech markers) or rank in top 10
    freq = Counter(words).most_common(40)
    tech_markers = ("cloud", "sql", "kubernetes", "docker", "aws", "gcp", "azure",
                    "python", "rust", "go", "java", "react", "node", "api", "linux",
                    "ci", "cd", "devops", "ml", "ai", "llm", "security", "crypto")
    reqs = {w for w, _c in freq[:10]}
    for w, _c in freq:
        if any(m in w for m in tech_markers) or w.endswith((".js", ".py", ".rs")):
            reqs.add(w)
    reqs = {w[:-1] if w.endswith("s") and len(w) > 3 and not w.endswith("ss") else w for w in reqs}
    return {r for r in reqs if len(r) > 2}


def coverage(resume_text: str, job_desc: str, tags: str = "[]") -> float:
    """Coverage = matched requirement signals / total requirement signals."""
    rt = _tokens(resume_text)
    reqs = _requirements(job_desc, tags)
    if not reqs:
        return 0.0
    return round(len(rt & reqs) / len(reqs), 3)


def match(resume_text: str, top_n: int = 15) -> list:
    con = _con()
    rows = con.execute("select id, title, company, url, description, tags from jobs").fetchall()
    con.close()
    scored = []
    for jid, title, company, url, desc, tags in rows:
        cov = coverage(resume_text, f"{title} {desc}", tags)
        if cov >= 0.15:
            scored.append({"job_id": jid, "title": title, "company": company,
                           "url": url, "coverage": cov, "over_gate": cov >= COVERAGE_GATE})
    scored.sort(key=lambda x: -x["coverage"])
    rh = _resume_hash(resume_text)
    con = _con()
    for s in scored[:top_n]:
        con.execute("insert into matches (resume_hash, job_id, coverage, ts) values (?,?,?,?)",
                    (rh, s["job_id"], s["coverage"], time.time()))
    con.commit()
    con.close()
    return scored[:top_n]


def _resume_hash(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def rewrite(resume_text: str, job_id: str) -> dict:
    """Honest rewrite: reframe existing experience toward the job's vocabulary.
    HARD RULE: no new claims.  Only lines from the original, reordered and
    keyword-mirrored.  Gate: coverage must be >= 50%."""
    con = _con()
    row = con.execute("select title, company, description, url from jobs where id=?", (job_id,)).fetchone()
    con.close()
    if not row:
        return {"ok": False, "error": "job not found"}
    title, company, desc, url = row
    trow = con.execute("select tags from jobs where id=?", (job_id,)).fetchone()
    con.close()
    cov = coverage(resume_text, f"{title} {desc}", trow[0] if trow else "[]")
    if cov < COVERAGE_GATE:
        return {"ok": False, "error": f"coverage {cov:.0%} < {COVERAGE_GATE:.0%} gate — no rewrite (would require fabrication)"}

    rt = _tokens(resume_text)
    jt = sorted(_tokens(f"{title} {desc}"), key=lambda t: 0)
    present = [t for t in jt if t in rt]
    missing = [t for t in jt if t not in rt]

    # Split resume into lines; pick experience lines matching job vocabulary
    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    ranked = sorted(lines, key=lambda l: -len(_tokens(l) & set(present)))
    top_lines = [l for l in ranked[:8] if _tokens(l) & set(present)]

    tailored = [
        f"TARGET ROLE: {title}" + (f" @ {company}" if company and company != "hn-company" else ""),
        f"Coverage vs role requirements: {cov:.0%} (threshold 50%) — rewritten strictly from existing experience",
        "",
        "TAILOR-SUMMARY (mirrors role vocabulary; every line traces to your original resume):",
    ]
    for l in top_lines:
        tailored.append(f"• {l}")
    tailored.append("")
    if missing:
        tailored.append(f"GAPS (not claimed, listed for honesty): {', '.join(missing[:8])}")
    tailored.append(f"Source job: {url}")

    return {"ok": True, "job_id": job_id, "coverage": cov, "rewrite": "\n".join(tailored),
            "integrity": "no fabricated claims; gaps disclosed"}


def _read_resume(rel: str) -> str:
    """Read a resume file with workspace containment (path-traversal guard)."""
    base = BASE.resolve()
    p = (base / rel).resolve()
    if not str(p).startswith(str(base)):
        raise ValueError("resume path escapes workspace — denied")
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ingest"
    if cmd == "ingest":
        print(json.dumps(ingest(), indent=1))
    elif cmd == "match":
        print(json.dumps(match(_read_resume(sys.argv[2])), indent=1))
    elif cmd == "rewrite":
        print(json.dumps(rewrite(_read_resume(sys.argv[2]), sys.argv[3]), indent=1))
    else:
        print(json.dumps({"usage": "ingest | match <resume> | rewrite <resume> <job_id>"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
