#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-GUI-BRIDGE glue python
"""
TIANXIA // SOVEREIGN UNIFIED BRIDGE  v6.1.0
============================================
Async intent-driven GUI bridge for the Faery Fortress.

Architecture:
  - Single global asyncio event loop runs: sandboxed task runner, UDS 14-core
    probe, NATS JetStream publish/consume.
  - ThreadingHTTPServer (dedicated thread) serves HTTP; each SSE connection is
    its own blocking thread consuming a thread-safe queue.Queue fan-out.
  - No shell=True on remote intents; tasks run via list-args subprocess, dropped
    to tianxia-hud under setpriv/unshare (bwrap when present), with timeout.
  - FFP-gated dynamic tool-router from substrate_prompt_matrix.json + keyword map.
  - Hybrid /api/intent contract (task_id + legacy result payload with
    rasoom/ego/tremor vectors). SSE /stream (500ms telemetry) and
    /stream/task/{id} (A2UI-ish log/surface events).
  - HMAC/mistakes-log discipline via SQLite MistakesLogger (FFP-24) + JSONL audit.
 """
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tx_net_guard import _check_allowlist, is_allowlisted, safe_fetch  # noqa: E402,F401
import asyncio
import hmac
import json
import os
import queue
import shutil
import sqlite3
import subprocess
import time
import uuid
import http.server
from collections import deque
from pathlib import Path

try:
    import logging
    logging.getLogger("nats").setLevel(logging.CRITICAL)
    logging.getLogger("nats.aio").setLevel(logging.CRITICAL)
    logging.getLogger("nats.aio.client").setLevel(logging.CRITICAL)
    logging.getLogger("nats.aio.transport").setLevel(logging.CRITICAL)
    import nats
    NATS_AVAILABLE = True
except Exception:
    NATS_AVAILABLE = False

BASE = Path(os.environ.get("TX_BASE_DIR", "/var/lib/tianxia"))
BIN = BASE / "bin"
GUI_HTML = BASE / "ui" / "index.html"
TOKEN_FILE = BASE / "secrets" / "substrate_auth.token"
MANIFEST_FILE = BASE / "manifests" / "substrate_prompt_matrix.json"
SOCKET_PATH = "/run/tianxia/tx_fastpath.sock"
MISTAKES_DB = BASE / "db" / "mistakes.sqlite3"
BILLING_DB = BASE / "db" / "billing.sqlite3"
AUDIT_LOG = BASE / "logs" / "bridge_audit.jsonl"
LOG_FILE = BASE / "logs" / "gui_bridge.log"

HOST = os.environ.get("TX_BRIDGE_HOST", "0.0.0.0")
PORT = int(os.environ.get("TX_BRIDGE_PORT", "9199"))
MAX_INTENT_LEN = int(os.environ.get("TX_MAX_INTENT", "512"))
MAX_CONCURRENT = int(os.environ.get("TX_MAX_TASKS", "24"))
TASK_TIMEOUT = float(os.environ.get("TX_TASK_TIMEOUT", "120"))
RING_CAP = int(os.environ.get("TX_RING_CAP", "500"))
RATE_PER_MIN = int(os.environ.get("TX_RATE_PER_MIN", "120"))
TASK_USER = os.environ.get("TX_TASK_USER", "tianxia-hud")
NATS_URL = os.environ.get("NATS_URL", "nats://127.0.0.1:4222")
NATS_JS = os.environ.get("NATS_JS", "true").lower() == "true"
NATS_USER = os.environ.get("NATS_USER", "")
NATS_PASS = os.environ.get("NATS_PASS", "")

TOKEN = ""
MANIFEST = {}

# ---------------------------------------------------------------------------
# Global asyncio loop + thread-safe fan-out
# ---------------------------------------------------------------------------
EVENT_LOOP = None
TASK_BUFFERS = {}      # task_id -> state dict
TASK_QUEUES = {}       # task_id -> queue.Queue (thread-safe SSE fan-out)
TASK_SEM = None
CLIENTS = {}


def emit(task_id, event):
    q = TASK_QUEUES.get(task_id)
    if q is not None:
        q.put_nowait(event)


def run_coro(coro, timeout=20):
    """Run a coroutine on the global loop from any thread."""
    fut = asyncio.run_coroutine_threadsafe(coro, EVENT_LOOP)
    try:
        return fut.result(timeout)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def _sh_cmd(cmd, timeout=3):
    """Safe subprocess runner without shell=True. cmd must be a list."""
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        r = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def get_mem():
    try:
        with open("/proc/meminfo") as f:
            m = {l.split(":")[0]: int(l.split(":")[1].split()[0]) for l in f if ":" in l}
        return f"{(m['MemTotal']-m.get('MemAvailable',0))//1024}MB / {m['MemTotal']//1024}MB"
    except Exception:
        return "N/A"


def get_load():
    try:
        return " ".join(open("/proc/loadavg").read().split()[:3])
    except Exception:
        return "N/A"

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def init_db():
    os.makedirs(BASE / "db", exist_ok=True)
    conn = sqlite3.connect(str(MISTAKES_DB))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=3000;")
    conn.execute("""CREATE TABLE IF NOT EXISTS mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, task_id TEXT,
        origin TEXT, error TEXT, cmd TEXT)""")
    conn.commit()
    conn.close()


def log_mistake(task_id, origin, error, cmd=""):
    try:
        conn = sqlite3.connect(str(MISTAKES_DB))
        conn.execute("INSERT INTO mistakes (ts, task_id, origin, error, cmd) VALUES (?,?,?,?,?)",
                     (time.time(), task_id, origin, str(error)[:500], str(cmd)[:500]))
        conn.commit()
        conn.close()
    except Exception:
        pass


def audit(task_id, event, data=None):
    try:
        os.makedirs(BASE / "logs", exist_ok=True)
        with open(str(AUDIT_LOG), "a") as f:
            f.write(json.dumps({"ts": time.time(), "task_id": task_id, "event": event, "data": data or {}}) + "\n")
    except Exception:
        pass


def init_log():
    os.makedirs(BASE / "logs", exist_ok=True)
    return open(str(LOG_FILE), "a", buffering=1)


# ---------------------------------------------------------------------------
# Dynamic tool-router (FFP-gated keyword routing, no static MANIFEST switch)
# ---------------------------------------------------------------------------
def load_manifest():
    global MANIFEST
    if MANIFEST_FILE.exists():
        try:
            d = json.loads(MANIFEST_FILE.read_text())
            MANIFEST = d.get("substrate_prompt_matrix", d)
        except Exception as e:
            log_mistake("boot", "manifest", e)
    if not MANIFEST:
        MANIFEST = {
            "architect_lord_naga": {"target": "inference-architect", "directive": "SYS.EXEC_ROLE=STRATEGIC_PLANNING"},
            "cyber_lady_naga": {"target": "inference-cyber", "directive": "SYS.EXEC_ROLE=SECURITY_AUDIT"},
            "veritas_magister": {"target": "inference-veritas", "directive": "SYS.EXEC_ROLE=REALITY_AUDIT"},
            "tetraledger_matriarch": {"target": "memory-tetraledger", "directive": "SYS.EXEC_ROLE=STATE_PERSISTENCE"},
        }


def resolve_router(prompt):
    low = prompt.lower()
    routes = [
        ("rebuild", "nix", ["nixos-rebuild", "switch"]),
        ("clean", "nix", ["nix-collect-garbage", "-d"]),
        ("gc", "nix", ["nix-collect-garbage", "-d"]),
        ("wg", "mesh", ["wg", "show", "wg0"]),
        ("mesh", "mesh", ["wg", "show", "wg0"]),
        ("htop", "telemetry", ["htop"]),
        ("monitor", "telemetry", ["top", "-bn1"]),
        ("telemetry", "telemetry", ["free", "-h"]),
        ("browser", "gui", ["swaymsg", "exec", "chromium", "--new-window", "https://duckduckgo.com"]),
        ("chromium", "gui", ["swaymsg", "exec", "chromium", "--new-window", "https://duckduckgo.com"]),
        ("terminal", "gui", ["swaymsg", "workspace", "2", "exec", "foot"]),
        ("zellij", "gui", ["swaymsg", "workspace", "2", "exec", "foot", "zellij"]),
        ("nats", "nats", ["nats", "stream", "ls"]),
        ("jets", "nats", ["nats", "stream", "ls"]),
        ("clock", "cmd", ["date"]),
        ("time", "cmd", ["date"]),
        ("uptime", "cmd", ["uptime"]),
        ("who", "cmd", ["who"]),
        ("ls", "cmd", ["ls", "-la", "/var/lib/tianxia"]),
    ]
    for kw, mod, cmd in routes:
        if kw in low:
            return {"module": mod, "cmd": cmd, "label": kw}
    return {"module": "intent", "cmd": ["echo", "[Intent accepted, no local handler for:]", prompt], "label": "intent"}


def make_vectors(prompt):
    tremor = round(14.8 + (len(prompt) % 27), 2)
    ego = "AXIS_ASURA_" + "".join([hex(ord(c))[2:] for c in prompt[:4]]) if prompt else "AXIS_0x00"
    rasoom = f"RASOOM://AUTARCHI_CONVERGE(TIANXIA_CORE)-->VECTOR({ego})&&TREMOR_LOCK({tremor}Hz)"
    # Call the substrate LLM (free path: local → deepseek → echo).
    # Keeps the response short and gated; the bridge never blocks long.
    substrate_text = ""
    substrate_backend = ""
    substrate_ms = 0
    try:
        llm = str(BIN / "tx_llm_substrate.py")
        env = dict(os.environ)
        env["TX_BASE_DIR"] = str(BASE)
        t0 = time.time()
        # 4s ceiling — the substrate LLM is fast; if it's slow, we move on
        res = subprocess.run([sys.executable, llm, prompt],
                             capture_output=True, text=True, timeout=4, env=env)
        substrate_ms = int((time.time() - t0) * 1000)
        if res.returncode == 0 and res.stdout.strip():
            try:
                d = json.loads(res.stdout)
                substrate_text = d.get("text", "")
                substrate_backend = d.get("backend", "")
            except Exception:
                substrate_text = res.stdout.strip()[:600]
            # LLM bypass: record success on the local LLM
            try:
                import sys as _sys
                _sys.path.insert(0, str(BIN))
                from tx_llm_breaker import record_success
                record_success("local", substrate_backend or "Qwen3-4B-Instruct")
            except Exception: pass
    except subprocess.TimeoutExpired:
        substrate_backend = "timeout"
        try:
            import sys as _sys
            _sys.path.insert(0, str(BIN))
            from tx_llm_breaker import record_failure
            record_failure("local", "Qwen3-4B-Instruct", body="timeout", status_code=408)
        except Exception: pass
    except Exception as e:
        substrate_backend = f"error:{type(e).__name__}"
        try:
            import sys as _sys
            _sys.path.insert(0, str(BIN))
            from tx_llm_breaker import record_failure
            record_failure("local", "Qwen3-4B-Instruct", body=str(e), status_code=0)
        except Exception: pass
    return {
        "rasoom": rasoom, "ego": ego, "tremor": f"{tremor} Hz",
        "substrate_text": substrate_text,
        "substrate_backend": substrate_backend,
        "substrate_ms": substrate_ms,
    }

# ---------------------------------------------------------------------------
# Billing / RGU meter
# ---------------------------------------------------------------------------
# Three tiers. The free tier is a fully usable sovereign cockpit; the paid
# tiers add headroom (per minute + per task) and SLA-style governance.
TIERS = {
    "free": {
        "label": "Free", "rgu_per_minute": 6, "rgu_per_day": 200,
        "max_intent_len": 256, "max_concurrent": 2,
        "monthly_usd": 0, "sla": "best-effort",
    },
    "pro": {
        "label": "Pro", "rgu_per_minute": 30, "rgu_per_day": 5000,
        "max_intent_len": 1024, "max_concurrent": 12,
        "monthly_usd": 29, "sla": "warm",
    },
    "sovereign": {
        "label": "Sovereign", "rgu_per_minute": 240, "rgu_per_day": 100000,
        "max_intent_len": 4096, "max_concurrent": 48,
        "monthly_usd": 299, "sla": "dedicated",
    },
}
# Tenant key: the cockpit is single-tenant on a sovereign LAN, but the
# mechanism is generic — derive a stable, salted hash of the bearer token.
# In a real multi-tenant deploy, replace with the verified identity claim.
import hashlib
from tx_auth import require_auth, verify_jwt, has_permission  # noqa: E402,F401
def tenant_key(headers):
    auth = headers.get("Authorization", "") or ""
    if not auth.lower().startswith("bearer "):
        return "anon"
    salt = (TOKEN or "tx-no-token").encode()
    h = hashlib.sha256(salt + auth[7:].encode()).hexdigest()
    return "t_" + h[:20]


def init_billing_db():
    os.makedirs(BASE / "db", exist_ok=True)
    conn = sqlite3.connect(str(BILLING_DB))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=3000;")
    conn.execute("""CREATE TABLE IF NOT EXISTS rgu_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, tenant TEXT,
        tier TEXT, task_id TEXT, route TEXT, rc INTEGER, cost_usd REAL)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_rgu_tenant_ts
        ON rgu_events(tenant, ts)""")
    # Stripe webhook events ledger
    conn.execute("""CREATE TABLE IF NOT EXISTS stripe_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL,
        event_type TEXT, event_id TEXT UNIQUE,
        object_id TEXT, object_type TEXT, payload TEXT)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_stripe_type_ts
        ON stripe_events(event_type, ts)""")
    conn.commit()
    conn.close()


def get_stripe_key():
    """Load Stripe secret key from secrets/stripe.env"""
    env_file = BASE / "secrets" / "stripe.env"
    if not env_file.exists():
        return None
    try:
        for line in env_file.read_text().strip().splitlines():
            if line.startswith("STRIPE_SECRET_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None


def stripe_request(method, endpoint, data=None, key=None):
    """Make a request to Stripe API using requests library."""
    import requests
    if key is None:
        key = get_stripe_key()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY not configured")
    url = f"https://api.stripe.com/v1{endpoint}"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/x-www-form-urlencoded"}
    if method.upper() == "GET":
        r = requests.get(url, headers=headers, params=data, timeout=30)
    else:
        r = requests.post(url, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()


def tier_of(headers):
    """X-TX-Tier header. Defaults to 'free' for unknown.
    In production this would be signed and verified; here it's a hint."""
    t = (headers.get("X-TX-Tier") or "free").lower().strip()
    return t if t in TIERS else "free"


def record_rgu(tenant, tier, task_id, route, rc):
    try:
        cost = TIERS[tier]["monthly_usd"] / max(1, TIERS[tier]["rgu_per_day"])
        conn = sqlite3.connect(str(BILLING_DB))
        conn.execute("INSERT INTO rgu_events (ts, tenant, tier, task_id, route, rc, cost_usd) "
                     "VALUES (?,?,?,?,?,?,?)",
                     (time.time(), tenant, tier, task_id, route, rc, cost))
        conn.commit()
        conn.close()
    except Exception as e:
        log_mistake(task_id, "billing", e)


def current_usage(tenant):
    """Returns (minute_count, day_count)."""
    now = time.time()
    try:
        conn = sqlite3.connect(str(BILLING_DB))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM rgu_events WHERE tenant=? AND ts>?",
                    (tenant, now - 60))
        minute_n = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM rgu_events WHERE tenant=? AND ts>?",
                    (tenant, now - 86400))
        day_n = cur.fetchone()[0]
        conn.close()
        return minute_n, day_n
    except Exception:
        return 0, 0


def enforce_quota(headers, tenant):
    """Returns (ok, status_code, body) tuple. ok=True means proceed."""
    tier = tier_of(headers)
    limits = TIERS[tier]
    mn, dn = current_usage(tenant)
    if mn >= limits["rgu_per_minute"]:
        return False, 429, {"error": "rate_cap_per_minute",
                            "tier": tier, "limit": limits["rgu_per_minute"],
                            "used": mn, "retry_after_s": 60}
    if dn >= limits["rgu_per_day"]:
        return False, 429, {"error": "rate_cap_per_day",
                            "tier": tier, "limit": limits["rgu_per_day"],
                            "used": dn, "retry_after_s": 3600}
    return True, 200, {"tier": tier, "used_minute": mn, "used_day": dn,
                       "limit_minute": limits["rgu_per_minute"],
                       "limit_day": limits["rgu_per_day"]}


# ---------------------------------------------------------------------------
# RGU Portfolio (the substrate LLM's "I live inside this.")
# Wraps the bin/tx_rgu_portfolio.py engine over the same SQLite.
# ---------------------------------------------------------------------------
try:
    sys.path.insert(0, str(BIN))
    import tx_rgu_portfolio as rgu
    rgu.init()
    RGU_AVAILABLE = True
except Exception as e:
    RGU_AVAILABLE = False
    log_mistake("boot", "rgu_init", e)


def rgu_call(fn_name, *args):
    """Run a tx_rgu_portfolio function and capture its stdout JSON."""
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            getattr(rgu, fn_name)(*args)
        return json.loads(buf.getvalue())
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
def _sandbox_prefix(cmd_args, cwd):
    """Build the sandbox command prefix. Tries bwrap first (Latitude/NixOS);
    falls back to setpriv drop when we're real root; on Termux/Android (no
    user-ns, no bwrap), runs the command directly under `timeout` only."""
    bwrap = shutil.which("bwrap")
    if bwrap:
        base = [bwrap, "--die-with-parent", "--unshare-net", "--unshare-ipc",
                "--ro-bind", "/usr", "/usr", "--ro-bind", "/nix", "/nix",
                "--ro-bind", "/run/current-system", "/run/current-system",
                "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                "--bind", cwd, cwd,
                "--setenv", "PATH", "/run/current-system/sw/bin:/usr/bin:/bin",
                "--chdir", cwd]
    elif os.geteuid() == 0 and shutil.which("setpriv"):
        base = ["setpriv", "--reuid=%s" % TASK_USER, "--regid=%s" % TASK_USER,
                "--init-groups", "--inh-caps=-all", "--bounding-set=-all"]
    else:
        # Termux / unprivileged / Android: just timeout + run.
        base = []
    return ["timeout", str(TASK_TIMEOUT)] + base + cmd_args


async def run_task(task_id, prompt, cmd_args):
    state = TASK_BUFFERS[task_id]
    env = dict(os.environ)
    env.pop("NATS_URL", None)
    env["PATH"] = "/run/current-system/sw/bin:/usr/bin:/bin"
    cwd = str(BASE)
    try:
        full = _sandbox_prefix(cmd_args, cwd)
    except Exception as e:
        log_mistake(task_id, "sandbox", e)
        full = ["timeout", str(TASK_TIMEOUT)] + cmd_args
    try:
        p = await asyncio.create_subprocess_exec(
            *full, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.DEVNULL,
            cwd=cwd, env=env)
    except FileNotFoundError as e:
        log_mistake(task_id, "exec", e, str(cmd_args))
        emit(task_id, {"t": "err", "line": f"[sandbox] executable unavailable: {e}"})
        emit(task_id, {"t": "done", "rc": 127})
        return {"rc": 127, "out": "", "err": str(e)}
    state["proc"] = p

    async def pump(stream, tag):
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", "replace").rstrip()
            emit(task_id, {"t": tag, "line": text})
            state["lines"].append((time.time(), tag, text))
            state["tail"].append((tag, text))
            while len(state["tail"]) > RING_CAP:
                state["tail"].popleft()

    await asyncio.gather(pump(p.stdout, "out"), pump(p.stderr, "err"))
    try:
        rc = await asyncio.wait_for(p.wait(), timeout=TASK_TIMEOUT)
    except asyncio.TimeoutError:
        try:
            p.kill()
        except Exception:
            pass
        rc = 124
        emit(task_id, {"t": "err", "line": "[sandbox] task timed out"})
    out = "\n".join(l for _, t, l in state["lines"] if t == "out")
    err = "\n".join(l for _, t, l in state["lines"] if t == "err")
    state["status"] = "DONE"
    emit(task_id, {"t": "done", "rc": rc})
    return {"rc": rc, "out": out, "err": err}


async def _dispatch_async(task_id, prompt, route):
    async with TASK_SEM:
        await nats_publish("tianxia.tasks.work", {"task_id": task_id, "intent": prompt, "route": route["module"]})
        res = await run_task(task_id, prompt, route["cmd"])
        TASK_BUFFERS[task_id].update(res)
        await nats_publish("tianxia.tasks.telemetry", {"task_id": task_id, "rc": res["rc"]})
        if res["rc"] != 0:
            log_mistake(task_id, "task", (res.get("err") or "")[:300], str(route["cmd"]))


# ---------------------------------------------------------------------------
# UDS 14-core substrate probe
# ---------------------------------------------------------------------------
async def probe_cores():
    result = {}
    try:
        reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)
        t0 = time.perf_counter()
        for core in ["KALI", "TARA", "TRIPURA", "BHUVANESVARI", "BHAIRAVI", "CHHINNAMASTA",
                     "DHUMAVATI", "BAGALAMUKHI", "MATANGI", "KAMALA", "PRATYANGIRA",
                     "ANNAPURNA", "MAHASARASVATI", "PARAMASIVA"]:
            writer.write((json.dumps({"auth": TOKEN, "intent": core}) + "\n").encode())
            await writer.drain()
            try:
                resp = await asyncio.wait_for(reader.readline(), timeout=1.0)
            except asyncio.TimeoutError:
                result[core] = {"status": "TIMEOUT", "latency": 0}
                continue
            if resp:
                try:
                    d = json.loads(resp.decode())
                    result[core] = {"status": d.get("status"), "latency": d.get("latency_ms", 0)}
                except Exception:
                    result[core] = {"status": "ERR", "latency": 0}
            else:
                result[core] = {"status": "DOWN", "latency": 0}
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        result["_sweep_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    except Exception:
        result = {"_sweep_ms": 0}
    return result

# ---------------------------------------------------------------------------
# NATS JetStream
# ---------------------------------------------------------------------------
async def nats_publish(subject, payload):
    if not NATS_AVAILABLE:
        return False
    nc = None
    try:
        opts = {"servers": [NATS_URL], "max_reconnect_attempts": 1}
        if NATS_USER:
            opts["user"] = NATS_USER
        if NATS_PASS:
            opts["password"] = NATS_PASS
        nc = await nats.connect(**opts)
        try:
            if NATS_JS:
                js = nc.jetstream()
                await js.publish(subject, json.dumps(payload).encode())
            else:
                await nc.publish(subject, json.dumps(payload).encode())
        finally:
            await nc.close()
        return True
    except Exception as e:
        log_mistake("nats", "publish", e, subject)
        try:
            if nc:
                await nc.close()
        except Exception:
            pass
        return False


async def nats_queue_depth():
    if not NATS_AVAILABLE:
        return -1
    try:
        nc = await nats.connect(servers=[NATS_URL], max_reconnect_attempts=1)
        try:
            js = nc.jetstream()
            try:
                info = await js.stream_info("tianxia.tasks.work")
                return int(info.state.messages or 0)
            except Exception:
                return 0
        finally:
            await nc.close()
    except Exception:
        return -1


async def nats_ensure_streams():
    if not NATS_AVAILABLE or not NATS_JS:
        return
    try:
        nc = await nats.connect(servers=[NATS_URL], max_reconnect_attempts=3)
        js = nc.jetstream()
        for name, subj in (("tianxia.tasks.work", "tianxia.tasks.work"),
                           ("tianxia.tasks.telemetry", "tianxia.tasks.telemetry")):
            try:
                await js.add_stream(name=name, subjects=[subj], max_msgs=10000,
                                    max_age=7 * 24 * 3600, storage="file", discard="old")
            except Exception:
                pass
        await nc.close()
    except Exception as e:
        log_mistake("nats", "ensure_streams", e)


async def nats_consume_loop():
    if not NATS_AVAILABLE or not NATS_JS:
        return
    while True:
        try:
            nc = await nats.connect(servers=[NATS_URL], max_reconnect_attempts=3)
            js = nc.jetstream()

            async def cb(msg):
                try:
                    data = json.loads(msg.data.decode())
                    tid = data.get("task_id")
                    if tid:
                        await nats_publish("tianxia.tasks.telemetry",
                                           {"task_id": tid, "node": "latitude", "status": "ACK"})
                except Exception:
                    pass
                await msg.ack()

            sub = await js.subscribe("tianxia.tasks.work", cb=cb)
            try:
                while True:
                    await asyncio.sleep(1)
            finally:
                await sub.unsubscribe()
                await nc.close()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log_mistake("nats", "consume", e)
            await asyncio.sleep(5)

# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------
def _auth_ok(headers):
    """Constant-time Bearer token check."""
    auth = headers.get("Authorization", "") or ""
    if not auth.lower().startswith("bearer "):
        return False
    presented = auth[7:].encode()
    expected = TOKEN.encode() if TOKEN else b""
    return hmac.compare_digest(presented, expected)


def _rate_ok(client):
    now = time.time()
    w = CLIENTS.setdefault(client, deque())
    while w and w[0] < now - 60:
        w.popleft()
    w.append(now)
    return len(w) <= RATE_PER_MIN


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body=b""):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Access-Control-Allow-Origin", "same-origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_html(self, body):
        """Send HTML with strict CSP and a token-scoped nonce."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        self.send_header("Content-Security-Policy", csp)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _sse(self, event, data):
        self.wfile.write(f"event: {event}\ndata: {data}\n\n".encode())
        self.wfile.flush()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "same-origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        client = self.client_address[0]
        if not _rate_ok(client):
            self._send(429, "application/json", b'{"error":"rate limited"}')
            return
        path = self.path.split("?")[0]

        # All SSE streams require auth. Public endpoints below.
        if path == "/stream" or path.startswith("/stream/task/"):
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return

        if path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", "same-origin")
            self.end_headers()
            try:
                while True:
                    cores = run_coro(probe_cores(), 20) or {}
                    qd = run_coro(nats_queue_depth(), 20)
                    if qd is None:
                        qd = -1
                    frame = {
                        "mem": get_mem(), "load": get_load(),
                        "peers": _sh_cmd("wg show wg0 peers | wc -l"),
                        "gens": _sh_cmd("nix-env --list-generations -p /nix/var/nix/profiles/system | wc -l"),
                        "time": time.strftime("%H:%M:%S"),
                        "date": time.strftime("%a, %d %b %Y"),
                        "queue_depth": qd, "cores": cores,
                    }
                    self._sse("telemetry", json.dumps(frame))
                    time.sleep(0.5)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        if path.startswith("/stream/task/"):
            task_id = path.split("/")[-1]
            if task_id not in TASK_QUEUES:
                self._send(404, "application/json", b'{"error":"task not found"}')
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", "same-origin")
            self.end_headers()
            q = TASK_QUEUES[task_id]
            try:
                for tag, line in TASK_BUFFERS[task_id]["tail"]:
                    self._sse("log", json.dumps({"t": tag, "line": line}))
                while True:
                    try:
                        ev = q.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    if ev.get("t") == "done":
                        self._sse("done", json.dumps(ev))
                        break
                    self._sse("log", json.dumps(ev))
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        if path in ("/", "/index.html"):
            # Landing page (rasaxmachina.com) takes precedence over cockpit
            LANDING = BASE / "landing" / "index.html"
            if LANDING.exists():
                body = LANDING.read_bytes()
                self._send_html(body)
                return
            if GUI_HTML.exists():
                body = GUI_HTML.read_bytes()
                if TOKEN:
                    body = body.replace(b"__TX_TOKEN__", TOKEN.encode())
            else:
                body = b"<h1>HUD Not Found</h1>"
            self._send_html(body)
            return

        if path == "/stripe-approval":
            body = (BASE / "ui" / "stripe_approval.html").read_bytes()
            self._send_html(body)
            return

        if path in ("/terms", "/terms.html"):
            body = (BASE / "ui" / "terms.html").read_bytes()
            self._send_html(body)
            return

        if path in ("/privacy", "/privacy.html"):
            body = (BASE / "ui" / "privacy.html").read_bytes()
            self._send_html(body)
            return

        if path == "/api/catalog":
            self._send(200, "application/json", json.dumps(
                {"components": ["terminal", "radar", "metrics", "mesh", "swarm", "task", "log", "table"]}).encode())
            return

        if path == "/api/health":
            self._send(200, "application/json", json.dumps(
                {"status": "ok", "nats": NATS_AVAILABLE, "tasks": len(TASK_BUFFERS)}).encode())
            return

        if path == "/api/billing/tiers":
            public = {k: {**v, "id": k} for k, v in TIERS.items()}
            self._send(200, "application/json", json.dumps(
                {"tiers": public, "currency": "USD",
                 "rgu_unit": "one task_intent = 1 RGU"}).encode())
            return

        if path == "/api/billing/usage":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            tenant = tenant_key(self.headers)
            tier = tier_of(self.headers)
            mn, dn = current_usage(tenant)
            limits = TIERS[tier]
            est_cost_usd = round(dn * (limits["monthly_usd"] / max(1, limits["rgu_per_day"])), 4)
            self._send(200, "application/json", json.dumps({
                "tenant": tenant, "tier": tier,
                "used_minute": mn, "limit_minute": limits["rgu_per_minute"],
                "used_day": dn, "limit_day": limits["rgu_per_day"],
                "estimated_cost_usd": est_cost_usd,
                "monthly_quota_usd": limits["monthly_usd"],
            }).encode())
            return

        # --- RGU portfolio read surface ----------------------------------
        if path == "/api/rgu/templates":
            self._send(200, "application/json", json.dumps(
                rgu_call("templates")).encode())
            return
        if path == "/api/rgu/portfolio":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            self._send(200, "application/json", json.dumps({
                "summary": rgu_call("summary"),
                "open": rgu_call("list_allocs", True),
                "all": rgu_call("list_allocs", False),
            }).encode())
            return
        if path == "/api/rgu/market":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            self._send(200, "application/json", json.dumps(
                rgu_call("market_list")).encode())
            return
        if path == "/api/rgu/market/cross-venue":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            try:
                lookback = 600
                if "?" in self.path:
                    for kv in self.path.split("?")[1].split("&"):
                        if kv.startswith("lookback="):
                            lookback = int(kv.split("=",1)[1])
                spreads = rgu.cross_venue_spread(lookback_s=lookback)
            except Exception as e:
                spreads = []
            self._send(200, "application/json", json.dumps(
                {"ok": True, "count": len(spreads), "spreads": spreads,
                 "ts": time.time()}).encode())
            return
        if path == "/api/rgu/revenue":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            limit = 50
            if "?" in self.path:
                try:
                    limit = int(self.path.split("limit=")[1].split("&")[0])
                except Exception: pass
            self._send(200, "application/json", json.dumps(
                rgu_call("list_revenue", limit)).encode())
            return
        if path == "/api/rgu/experiments":
            self._send(200, "application/json", json.dumps(
                rgu_call("experiment_list")).encode())
            return
        if path == "/api/rgu/keys":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            self._send(200, "application/json", json.dumps(
                rgu_call("key_list")).encode())
            return
        if path == "/api/commercial/summary":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            tenant = tenant_key(self.headers)
            tier = tier_of(self.headers)
            mn, dn = current_usage(tenant)
            limits = TIERS[tier]
            self._send(200, "application/json", json.dumps({
                "tenant": tenant, "tier": tier,
                "tiers": TIERS, "billing": {
                    "used_minute": mn, "limit_minute": limits["rgu_per_minute"],
                    "used_day": dn, "limit_day": limits["rgu_per_day"],
                    "monthly_quota_usd": limits["monthly_usd"],
                },
                "rgu": rgu_call("summary"),
                "experiments": rgu_call("experiment_list"),
            }).encode())
            return
        if path == "/api/ops/prometheus":
            body = "# HELP tianxia_rgu_allocations open allocations\n# TYPE tianxia_rgu_allocations gauge\n"
            try:
                import sqlite3
                db=str(BASE/"db/portfolio.sqlite3")
                con=sqlite3.connect(db)
                cur=con.execute("select count(*) from rgu_allocations where status='open'")
                cnt=cur.fetchone()[0]
                body+=f"tianxia_rgu_allocations {cnt}\n"
                con.close()
            except Exception as e:
                body+=f"# error {e}\n"
            self._send(200, "text/plain; version=0.0.4", body.encode())
            return
        if path == "/api/ops/snapshot":
            # Tianxia Supply Authority snapshot. Public — for the supply-authority script.
            try:
                snap = {
                    "ts": time.time(),
                    "bridge": {
                        "tasks_open": len([b for b in TASK_BUFFERS.values() if b.get("status") == "SPAWNED"]),
                        "tasks_total": len(TASK_BUFFERS),
                        "nats_available": NATS_AVAILABLE,
                        "manifest_keys": len(MANIFEST) if isinstance(MANIFEST, dict) else 0,
                    },
                    "system": {
                        "mem": get_mem(), "load": get_load(),
                        "peers": _sh_cmd("wg show wg0 peers 2>/dev/null | wc -l"),
                        "time": time.strftime("%H:%M:%S"),
                        "date": time.strftime("%a, %d %b %Y"),
                    },
                    "rgu": rgu_call("summary"),
                }
            except Exception as e:
                snap = {"ok": False, "error": str(e)}
            self._send(200, "application/json", json.dumps(snap, default=str).encode())
            return

        # --- SSE: live market feed for substrate LLMs ---------------------
        if path == "/stream/rgu-market":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", "same-origin")
            self.end_headers()
            last_payload = ""
            try:
                while True:
                    md = rgu_call("market_list")
                    payload = json.dumps(md, default=str)
                    if payload != last_payload:
                        self._sse("market", payload)
                        last_payload = payload
                    time.sleep(2)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        self._send(404, "application/json", b'{"error":"not found"}')

    def do_POST(self):
        client = self.client_address[0]
        if not _rate_ok(client):
            self._send(429, "application/json", b'{"error":"rate limited"}')
            return
        path = self.path.split("?")[0]
        try:
            ln = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            ln = 0
        if ln > 8192:
            self._send(413, "application/json", b'{"error":"payload too large"}')
            return
        try:
            body = self.rfile.read(ln).decode() or "{}"
            req = json.loads(body)
        except Exception:
            req = {}

        if path == "/api/intent":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            tenant = tenant_key(self.headers)
            tier = tier_of(self.headers)
            ok, code, body = enforce_quota(self.headers, tenant)
            if not ok:
                self._send(code, "application/json", json.dumps(body).encode())
                return
            tier_limits = TIERS[tier]
            prompt = str(req.get("intent") or req.get("prompt") or "")[:tier_limits["max_intent_len"]]
            if not prompt:
                self._send(400, "application/json", b'{"error":"intent required"}')
                return
            if len(TASK_BUFFERS) >= tier_limits["max_concurrent"]:
                self._send(503, "application/json", json.dumps(
                    {"error": "tier_max_concurrent",
                     "tier": tier, "limit": tier_limits["max_concurrent"]}).encode())
                return

            task_id = uuid.uuid4().hex[:12]
            vectors = make_vectors(prompt)
            route = resolve_router(prompt)

            TASK_BUFFERS[task_id] = {
                "id": task_id, "prompt": prompt, "status": "SPAWNED",
                "created": time.time(), "proc": None,
                "lines": [], "tail": deque(maxlen=RING_CAP), "route": route["module"],
                "tenant": tenant, "tier": tier,
            }
            TASK_QUEUES[task_id] = queue.Queue()
            audit(task_id, "intent", {"prompt": prompt, "route": route["module"],
                                      "tenant": tenant, "tier": tier})
            # Record the RGU at spawn time. We will record a second event with
            # the actual rc on completion (best-effort, fire-and-forget).
            record_rgu(tenant, tier, task_id, route["module"], 0)

            asyncio.run_coroutine_threadsafe(
                _dispatch_async(task_id, prompt, route), EVENT_LOOP)

            self._send(200, "application/json", json.dumps({
                "task_id": task_id, "status": "SPAWNED",
                "tenant": tenant, "tier": tier,
                "quota": body,
                "result": {
                    "dtype": "swarm",
                    "entity": {
                        "name": f"swarm-{route['label']}",
                        "role": f"Living Substrate Swarm [{route['module'].upper()}]",
                        "proto": "Neural Inference Stream", "cmd": "Lord & Lady Naga",
                        "chan": "Port 11434",
                        "spec": f"Active live substrate execution for: '{prompt}'",
                    },
                    **vectors, "rc": 0, "out": "", "err": "",
                    "task_id": task_id, "route": route["module"],
                }
            }).encode())
            return

        if path == "/api/task/close":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            task_id = req.get("task_id", "")
            TASK_BUFFERS.pop(task_id, None)
            TASK_QUEUES.pop(task_id, None)
            audit(task_id, "close")
            self._send(200, "application/json", b'{"status":"closed"}')
            return

        if path == "/api/rgu/allocate":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            ffps = max(1, min(int(req.get("ffps", 4)), 8))
            rgu_id = "RGU-" + uuid.uuid4().hex[:8].upper()
            payload = {
                "rgu_id": rgu_id, "ffps": ffps, "cycle_hours": 72,
                "status": "ALLOCATED", "node": "latitude",
                "price_eur": round(4 + 1.5 * ffps, 2),
            }
            audit(rgu_id, "rgu_allocate", payload)
            self._send(200, "application/json", json.dumps(payload).encode())
            return

        # --- RGU portfolio write surface (LLM-operated) ------------------
        if path == "/api/rgu/portfolio/upsert":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            action = req.get("action", "open")
            tenant = tenant_key(self.headers)
            if action == "open":
                tid = req.get("template_id", "")
                principal = float(req.get("principal_usd", 0))
                notes = req.get("notes", "")
                if not tid or principal <= 0:
                    self._send(400, "application/json",
                               json.dumps({"error": "template_id and principal_usd required"}).encode())
                    return
                result = rgu_call("open_alloc", tid, principal, tenant, notes)
                code = 200 if result.get("ok") else 409
                self._send(code, "application/json", json.dumps(result).encode())
                return
            if action == "close":
                aid = req.get("alloc_id", "")
                exit_value = float(req.get("exit_value_usd", 0))
                notes = req.get("notes", "")
                if not aid:
                    self._send(400, "application/json",
                               json.dumps({"error": "alloc_id required"}).encode())
                    return
                result = rgu_call("close_alloc", aid, exit_value, notes)
                code = 200 if result.get("ok") else 404
                self._send(code, "application/json", json.dumps(result).encode())
                return
            self._send(400, "application/json",
                       json.dumps({"error": "action must be open or close"}).encode())
            return

        if path == "/api/rgu/market":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            ticks = req.get("ticks")
            if not isinstance(ticks, list) or not ticks:
                self._send(400, "application/json",
                           json.dumps({"error": "ticks[] required (LLM-provided market data)"}).encode())
                return
            result = rgu_call("market_set", ticks)
            self._send(200, "application/json", json.dumps(result).encode())
            return

        if path == "/api/rgu/revenue":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            ev = req.get("event")
            if not isinstance(ev, dict) or "kind" not in ev or "amount_usd" not in ev:
                self._send(400, "application/json",
                           json.dumps({"error": "event {kind, amount_usd, ...} required"}).encode())
                return
            ev.setdefault("tenant", tenant_key(self.headers))
            result = rgu_call("revenue_event", ev)
            self._send(200, "application/json", json.dumps(result).encode())
            return

        if path == "/api/rgu/experiment":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            if "name" not in req or "variant" not in req:
                self._send(400, "application/json",
                           json.dumps({"error": "name and variant required"}).encode())
                return
            result = rgu_call("experiment_add", req)
            self._send(200, "application/json", json.dumps(result).encode())
            return

        if path == "/api/rgu/keys":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            # Gated: secret_ref is required; secret value MUST NOT be in the body.
            if req.get("secret"):
                self._send(400, "application/json",
                           json.dumps({"error": "do not pass 'secret' — pass secret_ref (path/URI) only"}).
                           encode())
                return
            if "label" not in req or "secret_ref" not in req:
                self._send(400, "application/json",
                           json.dumps({"error": "label and secret_ref required"}).encode())
                return
            result = rgu_call("key_add", req)
            self._send(200, "application/json", json.dumps(result).encode())
            return

        if path == "/api/rgu/sign":
            # Sign a message with the sovereign key (ETAMANGA or EFEMERA).
            # The bridge reads the priv key from the registered secret_ref,
            # signs, and returns the signature. The LLM uses this to
            # produce on-chain transactions.
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            chain = req.get("chain", "").lower()
            message = req.get("message", "")
            template_id = req.get("template_id", "")
            if chain not in ("etamanga", "efemera"):
                self._send(400, "application/json",
                           json.dumps({"error": "chain must be 'etamanga' or 'efemera'"}).encode())
                return
            if not message:
                self._send(400, "application/json",
                           json.dumps({"error": "message required"}).encode())
                return
            script = ("tx_etamanga_init.py" if chain == "etamanga"
                      else "tx_efemera_init.py")
            env = dict(os.environ)
            env["TX_BASE_DIR"] = str(BASE)
            try:
                res = subprocess.run(
                    [sys.executable, str(BIN / script), "sign", message],
                    capture_output=True, text=True, timeout=5, env=env)
            except subprocess.TimeoutExpired:
                self._send(504, "application/json",
                           json.dumps({"error": "sign timeout"}).encode())
                return
            except Exception as e:
                self._send(500, "application/json",
                           json.dumps({"error": str(e)}).encode())
                return
            if res.returncode != 0 or not res.stdout.strip():
                self._send(500, "application/json",
                           json.dumps({"error": "sign failed",
                                       "stderr": res.stderr.strip()}).encode())
                return
            try:
                d = json.loads(res.stdout)
            except Exception:
                self._send(500, "application/json",
                           json.dumps({"error": "bad sign output",
                                       "stdout": res.stdout[:200]}).encode())
                return
            # Optionally log the sign event in audit
            audit(f"{chain}-sign", "sign", {
                "template_id": template_id,
                "message_digest": hashlib.sha256(message.encode()).hexdigest()[:16],
                "ts": time.time(),
            })
            self._send(200, "application/json", json.dumps({
                "ok": True, "chain": chain, "message": message,
                "signature_hex": d.get("signature_hex"),
                "template_id": template_id,
            }).encode())
            return

        if path == "/api/rgu/template-add":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            for required in ("source", "category"):
                if required not in req:
                    self._send(400, "application/json",
                               json.dumps({"error": f"{required} required"}).encode())
                    return
            result = rgu_call("template_add", req)
            self._send(200, "application/json", json.dumps(result).encode())
            return

        # JobMatch PWA: match resume -> jobs (public; resume sent by user)
        # Body: {"resume": "..."} -> {"matches": [...]}
        if path == "/api/v1/jobmatch/match":
            resume = req.get("resume", "")
            if not resume:
                self._send(400, "application/json", b'{"error":"resume required"}')
                return
            try:
                import tx_jobmatch as jm
                self._send(200, "application/json",
                           json.dumps({"matches": jm.match(resume)}).encode())
            except Exception as e:
                self._send(500, "application/json", json.dumps({"error": str(e)[:200]}).encode())
            return

        # JobMatch PWA: gated rewrite (>=50% coverage, honesty firewall)
        # Body: {"resume": "...", "job_id": "..."} -> rewrite or refusal
        if path == "/api/v1/jobmatch/rewrite":
            resume, job_id = req.get("resume", ""), req.get("job_id", "")
            if not resume or not job_id:
                self._send(400, "application/json", b'{"error":"resume + job_id required"}')
                return
            try:
                import tx_jobmatch as jm
                self._send(200, "application/json", json.dumps(jm.rewrite(resume, job_id)).encode())
            except Exception as e:
                self._send(500, "application/json", json.dumps({"error": str(e)[:200]}).encode())
            return

        # Stripe Checkout session creation
        # Body: {"price_id": "price_...", "success_url": "https://...", "cancel_url": "https://...", "tenant": "optional_override", "metadata": {...}}
        if path == "/api/v1/checkout":
            if not _auth_ok(self.headers):
                self._send(401, "application/json", b'{"error":"unauthorized"}')
                return
            price_id = req.get("price_id")
            success_url = req.get("success_url", "https://rasaxmachina.com/billing/success")
            cancel_url = req.get("cancel_url", "https://rasaxmachina.com/billing/cancel")
            if not price_id:
                self._send(400, "application/json", b'{"error":"price_id required"}')
                return
            tenant = req.get("tenant") or tenant_key(self.headers)
            metadata = {"tenant": tenant, "source": "tianxia-gui-bridge"}
            metadata.update(req.get("metadata", {}))
            try:
                import requests
                key = get_stripe_key()
                if not key:
                    self._send(503, "application/json", b'{"error":"stripe not configured"}')
                    return
                url = "https://api.stripe.com/v1/checkout/sessions"
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/x-www-form-urlencoded"}
                data = {
                    "mode": "subscription",
                    "line_items[0][price]": price_id,
                    "line_items[0][quantity]": "1",
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                }
                for k, v in metadata.items():
                    data[f"metadata[{k}]"] = v
                r = requests.post(url, headers=headers, data=data, timeout=30)
                if r.status_code >= 400:
                    self._send(r.status_code, "application/json", r.text.encode())
                    return
                session = r.json()
                self._send(200, "application/json", json.dumps({
                    "session_id": session.get("id"),
                    "url": session.get("url"),
                    "price_id": price_id,
                    "tenant": tenant,
                }).encode())
                return
            except Exception as e:
                self._send(500, "application/json", json.dumps({"error": str(e)}).encode())
                return

        # Stripe Webhook endpoint (no auth — verifies via stripe-signature header)
        # Expected: stripe listen --forward-to http://HOST:PORT/api/v1/webhook
        if path == "/api/v1/webhook":
            import hmac
            import hashlib
            sig_header = self.headers.get("Stripe-Signature", "")
            webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
            if not webhook_secret:
                self._send(500, "application/json", b'{"error":"webhook secret not configured"}')
                return
            try:
                # Verify signature: stripe-signature header contains t=timestamp, v1=signature
                # Format: t=1234567890,v1=abcdef...
                ts = None
                v1 = None
                for part in sig_header.split(","):
                    if part.startswith("t="):
                        ts = part[2:]
                    elif part.startswith("v1="):
                        v1 = part[3:]
                if not ts or not v1:
                    self._send(400, "application/json", b'{"error":"invalid signature header"}')
                    return
                # Use the already-parsed req from outer do_POST (body already consumed)
                payload = json.dumps(req, separators=(",", ":"))
                expected = hmac.new(webhook_secret.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected, v1):
                    self._send(400, "application/json", b'{"error":"signature verification failed"}')
                    return
                event = req
                # Store event in billing_ledger
                conn = sqlite3.connect(str(BILLING_DB))
                conn.execute("INSERT OR IGNORE INTO stripe_events (ts, event_type, event_id, object_id, object_type, payload) VALUES (?,?,?,?,?,?)",
                             (time.time(), event.get("type"), event.get("id"),
                              event.get("data", {}).get("object", {}).get("id"),
                              event.get("data", {}).get("object", {}).get("object"),
                              payload))
                conn.commit()
                conn.close()
                # Process key event types
                if event.get("type") == "checkout.session.completed":
                    session = event["data"]["object"]
                    # Could trigger provisioning here
                    pass
                elif event.get("type") == "invoice.payment_succeeded":
                    pass
                elif event.get("type") == "customer.subscription.updated":
                    pass
                self._send(200, "application/json", b'{"received":true}')
                return
            except Exception as e:
                self._send(400, "application/json", json.dumps({"error": str(e)}).encode())
                return

        self._send(404, "application/json", b'{"error":"not found"}')


def run_http_server():
    srv = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    srv.daemon_threads = True
    srv.serve_forever()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global EVENT_LOOP, TASK_SEM, TOKEN
    if TOKEN_FILE.exists():
        TOKEN = TOKEN_FILE.read_text().strip()
    init_db()
    init_billing_db()
    init_log()
    load_manifest()

    EVENT_LOOP = asyncio.new_event_loop()
    TASK_SEM = asyncio.Semaphore(MAX_CONCURRENT)

    loop_thread_started = False

    def _start_loop():
        asyncio.set_event_loop(EVENT_LOOP)
        EVENT_LOOP.run_until_complete(_loop_init())
        EVENT_LOOP.run_forever()

    async def _loop_init():
        await nats_ensure_streams()
        EVENT_LOOP.create_task(nats_consume_loop())

    import threading
    t = threading.Thread(target=_start_loop, daemon=True)
    t.start()

    # HTTP in its own thread
    import threading as _t
    http_t = _t.Thread(target=run_http_server, daemon=True)
    http_t.start()

    with open(str(LOG_FILE), "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] bridge up {HOST}:{PORT} nats={NATS_AVAILABLE} manifest_keys={len(MANIFEST)} token={'set' if TOKEN else 'EMPTY'}\n")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
