#!/usr/bin/env python3
# ffp: TX-HUSSAR glue python
# REVISION: tx_hussar v0.1 — DSS-14 glue; hierarchical orchestration (HALO/AgentOrchestra-inspired)
"""Tianxia Hussar — hierarchical orchestration MVP (HALO / AgentOrchestra-inspired).

Plan -> Assign -> Dispatch -> Review with context isolation per subgoal.
Supervisor is one of our own units (default: teacher Crownforge :11502), workers
are Substrate members (config/substrate_identity.json), review by Veritas
(:11504) when available. Every run emits a trace + memory record.

Usage:
  tx_hussar.py run --task "..." [--max-subgoals 3] [--review] [--json]
  tx_hussar.py selftest
Governance: honors AUTONOMY_PAUSED / PROBE_STOP; list-args subprocess only.
"""
import argparse
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

logr = logging.getLogger("tx_hussar")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")

BIN = "/var/lib/tianxia/bin"
LOCAL_BIN = os.path.dirname(os.path.abspath(__file__))
for _p in (LOCAL_BIN, BIN):
    if _p not in sys.path:
        sys.path.insert(0, _p)
TRACE_DIR = os.environ.get("TX_HUSSAR_TRACE_DIR", "/var/lib/tianxia/logs/hussar")
KILL = ("/var/lib/tianxia/AUTONOMY_PAUSED", "/var/lib/tianxia/PROBE_STOP")
DEFAULT_TIMEOUT = int(os.environ.get("TX_HUSSAR_TIMEOUT", "600"))
ROUTE_PORT = {
    "uncensored36": 11502, "uncensored": 11503, "security": 11504,
    "vishwakarma": 11505, "naga-pasha": 11506, "uncensored30": 11507, "pluginus": 11508,
}
DEFAULT_SUPERVISOR = 11502
DEFAULT_REVIEWER = 11504


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def halted():
    return any(os.path.exists(p) for p in KILL)


def ask(port, system, user, timeout=600, maxtok=1200):
    body = json.dumps({
        "model": "m",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.3, "max_tokens": maxtok,
    }).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    msg = d["choices"][0]["message"]
    txt = msg.get("content") or ""
    if not txt.strip():
        txt = msg.get("reasoning_content") or msg.get("reasoning") or ""
    return txt


def load_routes():
    try:
        cfg = json.loads(open("/var/lib/tianxia/config/substrate_identity.json").read())
        return cfg.get("routes", {})
    except Exception:
        return {}


def plan(task, sup_port, max_subgoals):
    sys_p = ("You are a Tianxia planner. Decompose the task into at most "
             f"{max_subgoals} independent subgoals. Return strict JSON only: "
             '{"subgoals":[{"id":1,"goal":"...","domain":"one of: doctrine|security|plugins|memory|language|operations|knowledge"}]}')
    try:
        txt = ask(sup_port, sys_p, task, timeout=600, maxtok=400)
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            d = json.loads(m.group(0))
            subs = d.get("subgoals") or []
            if subs:
                return subs[:max_subgoals]
    except Exception as exc:
        log(f"planner fallback ({exc})")
    return [{"id": 1, "goal": task, "domain": "operations"}]


DOMAIN_MEMBER = {
    "doctrine": "uncensored36", "knowledge": "uncensored30", "operations": "uncensored30",
    "security": "security", "plugins": "pluginus", "memory": "naga-pasha",
    "language": "vishwakarma", "time": "uncensored", "anomaly": "uncensored",
}


def health_ok(port, timeout=3):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=timeout) as r:
            return b'"ok"' in r.read()
    except Exception:
        return False


_HEALTH_CACHE = {}


def live_route(route):
    port = ROUTE_PORT.get(route)
    if not port:
        return None
    if port not in _HEALTH_CACHE:
        _HEALTH_CACHE[port] = health_ok(port)
    return route if _HEALTH_CACHE[port] else None


def assign(subgoal):
    dom = (subgoal.get("domain") or "operations").lower()
    route = DOMAIN_MEMBER.get(dom, "uncensored36")
    if live_route(route):
        return route
    fallback = "uncensored36"
    if live_route(fallback):
        logr.warning("route %s not live -> fallback %s", route, fallback)
        return fallback
    for r in ROUTE_PORT:
        if live_route(r):
            logr.warning("route %s not live -> fallback %s", route, r)
            return r
    return route


def dispatch(subgoal, route, results, timeout):
    port = ROUTE_PORT.get(route)
    member, domain, roles = route, "", ""
    try:
        from tx_identity import member_entry
        e = member_entry(route) or {}
        member, domain, roles = e.get("member", route), e.get("domain", ""), e.get("roles", "")
    except Exception as exc:
        logr.debug("identity lookup fallback: %s", exc)
    system = (f"You are {member}, a Tianxia Substrate member. Domain: {domain}. Roles: {roles}. "
              "Answer succinctly and stay in role.") if member else "You are a Tianxia Substrate member."
    t0 = time.time()
    try:
        txt = ask(port, system, subgoal["goal"], timeout=timeout)
        results[subgoal["id"]] = {"route": route, "member": member, "output": txt,
                                  "latency_s": round(time.time() - t0, 1)}
    except Exception as exc:
        results[subgoal["id"]] = {"route": route, "member": member, "error": str(exc)[:160],
                                  "latency_s": round(time.time() - t0, 1)}


def review(task, results, rev_port, timeout):
    digest = "\n\n".join(
        f"### Subgoal {k} ({v.get('member')})\n{v.get('output') or v.get('error')}"
        for k, v in sorted(results.items()))
    sys_r = ('You are Veritas, Tianxia truth auditor. Validate the collected results against the task. '
             'Return strict JSON only: {"verdict":"pass|fail","score":1-5,"flags":["..."],"notes":"..."}')
    try:
        txt = ask(rev_port, sys_r, f"TASK:\n{task}\n\nRESULTS:\n{digest}", timeout=timeout, maxtok=300)
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else {"raw": txt[:300]}
    except Exception as exc:
        return {"error": str(exc)[:160]}


def run(args):
    if halted():
        log("halted by kill-switch")
        return 3
    os.makedirs(TRACE_DIR, exist_ok=True)
    sup = args.supervisor or DEFAULT_SUPERVISOR
    subgoals = plan(args.task, sup, args.max_subgoals)
    log(f"plan: {len(subgoals)} subgoals")
    assigned = []
    for sg in subgoals:
        route = assign(sg)
        assigned.append((sg, route))
        log(f"  #{sg['id']} [{sg.get('domain')}] -> {route} :: {str(sg.get('goal'))[:70]}")
    results = {}
    threads = []
    for sg, route in assigned:
        t = threading.Thread(target=dispatch, args=(sg, route, results, args.timeout))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    rev = review(args.task, results, args.reviewer, args.timeout) if args.review else None
    trace = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "task": args.task,
             "subgoals": subgoals, "assignments": {str(s["id"]): r for s, r in assigned},
             "results": {str(k): {"member": v.get("member"), "route": v.get("route"),
                                  "latency_s": v.get("latency_s"),
                                  "output": (v.get("output") or v.get("error") or "")[:2000]}
                         for k, v in results.items()},
             "review": rev}
    path = os.path.join(TRACE_DIR, f"hussar-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}.json")
    with open(path, "w") as f:
        json.dump(trace, f, indent=1)
    log(f"trace: {path}")
    if args.json:
        print(json.dumps(trace, indent=1))
    else:
        for k, v in sorted(results.items()):
            log(f"#{k} {v.get('member')}: {(v.get('output') or v.get('error') or '')[:160]}")
        if rev:
            log(f"review: {json.dumps(rev)[:200]}")
    try:
        subprocess.run(["python3", f"{BIN}/tx_memory.py", "--remember",
                        f"HUSSAR run: {args.task[:120]} -> {path}",
                        "--kind", "experience", "--source", "hussar"],
                       check=False, capture_output=True, timeout=120)
    except Exception as exc:
        logr.warning("memory record failed: %s", exc)
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--task", required=True)
    r.add_argument("--max-subgoals", type=int, default=3)
    r.add_argument("--supervisor", type=int, default=0, help="port override (default teacher)")
    r.add_argument("--reviewer", type=int, default=DEFAULT_REVIEWER)
    r.add_argument("--review", action="store_true")
    r.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    r.add_argument("--json", action="store_true")
    sub.add_parser("selftest")
    leg = sub.add_parser("legions")
    leg.add_argument("--json", action="store_true")
    leg.add_argument("--force-subdomains", action="store_true")
    pat = sub.add_parser("patrol")
    pat.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd in ("legions", "patrol"):
        import tx_hussar_legions
        rep = tx_hussar_legions.run_patrol_cycle(force_subdomain_sweep=getattr(a, "force_subdomains", False))
        if getattr(a, "json", False):
            print(json.dumps(rep, indent=2, ensure_ascii=False))
        else:
            log(f"7-Legions Patrol: {rep.get('overall_status')} ({rep.get('legions_passed')}/{rep.get('legions_total')})")
        return 0 if rep.get("all_passed") else 1
    if a.cmd == "selftest":
        assert DOMAIN_MEMBER.get("security") == "security"
        assert DOMAIN_MEMBER.get("unknown-thing", "uncensored36") == "uncensored36"
        assert callable(live_route) and callable(health_ok)
        print("HUSSAR-SELFTEST-OK", flush=True)
        if os.environ.get("INVOCATION_ID"):
            log("Entering continuous Hussar 7-Legion patrol daemon loop (interval=60s)...")
            import tx_hussar_legions
            while not halted():
                status_map = {name: health_ok(port) for name, port in ROUTE_PORT.items()}
                legion_rep = {}
                try:
                    legion_rep = tx_hussar_legions.run_patrol_cycle(force_subdomain_sweep=False)
                    log(f"7-Legions cycle: {legion_rep.get('overall_status')} "
                        f"({legion_rep.get('legions_passed')}/{legion_rep.get('legions_total')} in {legion_rep.get('duration_s')}s)")
                except Exception as exc:
                    logr.error("legion patrol error: %s", exc)
                shm_tmp = "/dev/shm/tx_hussar_patrol.json.tmp"
                shm_dst = "/dev/shm/tx_hussar_patrol.json"
                try:
                    with open(shm_tmp, "w") as sf:
                        json.dump({
                            "ts": time.time(),
                            "routes": status_map,
                            "status": "patrolling",
                            "legions_overall": legion_rep.get("overall_status", "UNKNOWN"),
                            "legions_passed": legion_rep.get("legions_passed", 0),
                            "legions_total": legion_rep.get("legions_total", 7),
                        }, sf)
                    os.replace(shm_tmp, shm_dst)
                except Exception as exc:
                    logr.debug("patrol shm write: %s", exc)
                for _ in range(60):
                    if halted():
                        break
                    time.sleep(1)
        return 0
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
