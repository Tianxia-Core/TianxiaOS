#!/usr/bin/env python3
# ffp: TX-MANAS ml-inference python
"""
tx_manas.py -- System-1 Fast Local Pre-Filter & Intent Triage Daemon (Nimbus² DAS / Mahavidya).

Canonical implementations of MANAS & PRATYAKSA per FRAMEWORK_CANON_CORRECTED.md:
  - MANAS (mind): Fast local System-1 pre-filter running in 7-14 ms (<1 GB RAM) that intercepts
    queries, enforces the AHIMSA non-destructive boundary, checks deterministic caches, and decides
    whether a query can be directly resolved, fast-routed, or must escalate to heavy LLMs.
  - PRATYAKSA (perception): Factual attribution decoding and uncertainty gate. Halts uncertain
    or hallucinated execution branches when certainty falls below threshold.

Port: 9189
Endpoints:
  GET  /health   -- Liveness, version, and latency telemetry
  POST /triage   -- Intercept prompt and return {verdict, route, latency_ms, ahimsa_pass}
  POST /evaluate -- PRATYAKSA certainty evaluation & branch-halt check

Founder: Collins Takem | Corporate Brand: RASA-X-MACHINA | Subdomain: rasaxmachina.com
REVISION: TX-MANAS-001   BASELINE: BASELINE.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Tuple

REVISION = "TX-MANAS-001"
BASELINE = os.environ.get("TX_BASELINE", "BASELINE.json")
DEFAULT_PORT = int(os.environ.get("TX_MANAS_PORT", "9189"))

log = logging.getLogger("tx_manas")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

# LRU / In-memory fast cache (O(1) lookup)
MAX_CACHE_SIZE = 1024
QUERY_CACHE: Dict[str, Tuple[str, Dict[str, Any], float]] = {}

# AHIMSA Law: Irreversible / destructive operations require explicit capability tokens
DESTRUCTIVE_PATTERNS = [
    re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    re.compile(r"\brm\s+-rf\s+[/~]", re.IGNORECASE),
    re.compile(r"\bdelete\s+from\s+[a-z_]+\s*;?\s*$", re.IGNORECASE),
    re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE),
    re.compile(r"\bmkfs\.", re.IGNORECASE),
    re.compile(r"\btruncate\s+table\b", re.IGNORECASE),
]

# Bleeding-Edge AI & LLM Attack Vector Defense Patterns (<0.2ms regex triage)
AI_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(?:all\s+|previous\s+|prior\s+)?instructions\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(?:prior|system|all)\s+instructions\b", re.IGNORECASE),
    re.compile(r"\bforget\s+(?:everything\s+you\s+know|all\s+prior\s+context)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(?:dan|an\s+unrestricted|freed|jailbroken|an\s+ai\s+without\s+rules)\b", re.IGNORECASE),
    re.compile(r"\bpretend\s+you\s+are\s+(?:in\s+developer\s+mode|unconstrained|evil)\b", re.IGNORECASE),
    re.compile(r"\breveal\s+(?:your\s+)?(?:system\s+prompt|instructions|core\s+directives|master\s+keys)\b", re.IGNORECASE),
    re.compile(r"\boutput\s+(?:your\s+|the\s+)?(?:initial|hidden|system)\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:are|were)\s+(?:your|the)\s+(?:original\s+)?instructions\b", re.IGNORECASE),
    re.compile(r"\bshow\s+me\s+your\s+system\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
]

DELIMITER_SMUGGLING_PATTERNS = [
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"<\|endoftext\|>", re.IGNORECASE),
    re.compile(r"<\|fim_prefix\|>|<\|fim_suffix\|>|<\|fim_middle\|>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]", re.IGNORECASE),
    re.compile(r"<<SYS>>|<</SYS>>", re.IGNORECASE),
    re.compile(r"```system|```assistant", re.IGNORECASE),
    re.compile(r"\[SYSTEM\]|\[HUMAN\]|\[AI\]", re.IGNORECASE),
]

SSRF_AND_LOCAL_PROBE_PATTERNS = [
    re.compile(r"\b169\.254\.169\.254\b"),
    re.compile(r"\bmetadata\.google\.internal\b", re.IGNORECASE),
    re.compile(r"\b100\.100\.100\.100\b"),
    re.compile(r"\b(?:file|gopher|dict|ftp|tftp|ldap|jar)://", re.IGNORECASE),
    re.compile(r"https?://(?:127\.0\.0\.1|localhost|0\.0\.0\.0|\[::1\])", re.IGNORECASE),
]

SENSITIVE_EXFILTRATION_PATTERNS = [
    re.compile(r"\bcat\s+(?:/etc/passwd|/etc/shadow|~/\.ssh/|/proc/)", re.IGNORECASE),
    re.compile(r"\bprint\s+(?:the\s+|all\s+)?(?:env|secrets|keys|passwords|tokens|api_key)\b", re.IGNORECASE),
    re.compile(r"\b(?:nc|netcat|ncat)\s+-e\b", re.IGNORECASE),
    re.compile(r"\b/bin/(?:ba)?sh\s+-i\b", re.IGNORECASE),
]

UNICODE_CONTROL_PATTERN = re.compile(r"[\u200b\u200c\u200d\ufeff\u202a-\u202e\u2060\u2066-\u2069\U000e0000-\U000e007f]")
BURST_REPEAT_PATTERN = re.compile(r"(.)\1{64,}")


def sanitize_prompt_vector(text: str, max_len: int = 8192) -> Tuple[bool, str, Dict[str, Any]]:
    """Bleeding-Edge AI & LLM Attack Vector Sanitizer.

    Inspects text for prompt injection, delimiter smuggling, SSRF probes,
    state exfiltration, and unicode obfuscation in <0.2ms with zero external API cost.
    """
    t0 = time.perf_counter()
    if not text:
        return True, "CLEAN_EMPTY", {"latency_ms": 0.01}

    # 1. Payload length clamp
    if len(text) > max_len:
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        return False, f"TOKEN_FLOOD: length {len(text)} exceeds limit {max_len}", {"latency_ms": latency_ms, "threat": "TOKEN_FLOOD"}

    # 2. Unicode control character & direction override detection
    if UNICODE_CONTROL_PATTERN.search(text):
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        return False, "DELIMITER_SMUGGLING: hidden unicode control codes detected", {"latency_ms": latency_ms, "threat": "UNICODE_CONTROL"}

    # 3. Burst character flooding detection
    if BURST_REPEAT_PATTERN.search(text):
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        return False, "TOKEN_FLOOD: repetitive character burst pattern detected", {"latency_ms": latency_ms, "threat": "CHAR_BURST"}

    # 4. Prompt injection & system override check
    for pat in AI_INJECTION_PATTERNS:
        m = pat.search(text)
        if m:
            latency_ms = round((time.perf_counter() - t0) * 1000, 3)
            return False, f"PROMPT_INJECTION: system override pattern '{m.group(0)}' detected", {"latency_ms": latency_ms, "threat": "PROMPT_INJECTION", "match": m.group(0)}

    # 5. Delimiter smuggling check
    for pat in DELIMITER_SMUGGLING_PATTERNS:
        m = pat.search(text)
        if m:
            latency_ms = round((time.perf_counter() - t0) * 1000, 3)
            return False, f"DELIMITER_SMUGGLING: chat template token '{m.group(0)}' detected", {"latency_ms": latency_ms, "threat": "DELIMITER_SMUGGLING", "match": m.group(0)}

    # 6. SSRF / Local metadata probe check
    for pat in SSRF_AND_LOCAL_PROBE_PATTERNS:
        m = pat.search(text)
        if m:
            latency_ms = round((time.perf_counter() - t0) * 1000, 3)
            return False, f"SSRF_PROBE: unauthorized network target '{m.group(0)}' detected", {"latency_ms": latency_ms, "threat": "SSRF_PROBE", "match": m.group(0)}

    # 7. Sensitive exfiltration check
    for pat in SENSITIVE_EXFILTRATION_PATTERNS:
        m = pat.search(text)
        if m:
            latency_ms = round((time.perf_counter() - t0) * 1000, 3)
            return False, f"EXFILTRATION_ATTEMPT: command pattern '{m.group(0)}' detected", {"latency_ms": latency_ms, "threat": "EXFILTRATION", "match": m.group(0)}

    latency_ms = round((time.perf_counter() - t0) * 1000, 3)
    return True, "CLEAN", {"latency_ms": latency_ms, "length": len(text)}


# Fast deterministic command patterns (0ms external latency)
DETERMINISTIC_COMMANDS = {
    r"^/status": {"intent": "SYSTEM_STATUS", "dispatch": "tx_status"},
    r"^/tx-hub": {"intent": "HUB_DISPATCH", "dispatch": "tx_hub_run"},
    r"^/tx-run": {"intent": "RUN_ASSET", "dispatch": "tx_hub_run"},
    r"^/tx-market": {"intent": "MARKET_OP", "dispatch": "tx_token_market"},
    r"^/tx-ledger": {"intent": "LEDGER_AUDIT", "dispatch": "tx_veritas_rex"},
    r"^/tx-scour": {"intent": "SCOUR_DISPATCH", "dispatch": "tx_scour_refresh"},
    r"^/tx-hussar": {"intent": "HUSSAR_CAMPAIGN", "dispatch": "tx_hussar"},
    r"^(hi|hello|ping|health)$": {"intent": "GREETING_OR_PING", "dispatch": "instant_pong"},
}


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def check_ahimsa_boundary(text: str) -> Tuple[bool, str]:
    """Verifies AHIMSA non-destruction law: blocks un-bounded irreversible destructive operations."""
    for pat in DESTRUCTIVE_PATTERNS:
        if pat.search(text):
            return False, f"AHIMSA violation: blocked destructive command pattern '{pat.pattern}'"
    return True, "AHIMSA verified: safe"


def triage_query(prompt: str) -> Dict[str, Any]:
    """System-1 fast pre-filter (7-14 ms target)."""
    t0 = time.perf_counter()
    prompt_clean = prompt.strip()
    q_hash = compute_hash(prompt_clean)

    # 1. Check LRU Cache
    if q_hash in QUERY_CACHE:
        verdict, cached_res, ts = QUERY_CACHE[q_hash]
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        return {
            "verdict": verdict,
            "cached": True,
            "intent": cached_res.get("intent", "CACHED"),
            "dispatch": cached_res.get("dispatch"),
            "ahimsa_pass": True,
            "latency_ms": latency_ms,
            "q_hash": q_hash,
        }

    # 1.5. Bleeding-Edge AI & LLM Vector Defense (<0.2ms)
    clean, ai_reason, ai_meta = sanitize_prompt_vector(prompt_clean)
    if not clean:
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        return {
            "verdict": "HALT_REJECT",
            "cached": False,
            "intent": "AI_ATTACK_VECTOR_BLOCKED",
            "reason": ai_reason,
            "ahimsa_pass": False,
            "ai_threat": ai_meta.get("threat", "UNKNOWN"),
            "latency_ms": latency_ms,
            "q_hash": q_hash,
        }

    # 2. Check AHIMSA Boundary
    safe, reason = check_ahimsa_boundary(prompt_clean)
    if not safe:
        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        return {
            "verdict": "HALT_REJECT",
            "cached": False,
            "intent": "DESTRUCTIVE_OP_BLOCKED",
            "reason": reason,
            "ahimsa_pass": False,
            "latency_ms": latency_ms,
            "q_hash": q_hash,
        }

    # 3. Deterministic Command Matching
    for pat_str, meta in DETERMINISTIC_COMMANDS.items():
        if re.search(pat_str, prompt_clean, re.IGNORECASE):
            latency_ms = round((time.perf_counter() - t0) * 1000, 3)
            res = {
                "verdict": "DIRECT_RESOLVE",
                "cached": False,
                "intent": meta["intent"],
                "dispatch": meta["dispatch"],
                "ahimsa_pass": True,
                "latency_ms": latency_ms,
                "q_hash": q_hash,
            }
            if len(QUERY_CACHE) < MAX_CACHE_SIZE:
                QUERY_CACHE[q_hash] = ("DIRECT_RESOLVE", res, time.time())
            return res

    # 4. Complexity & Intent Classification
    words = prompt_clean.split()
    word_count = len(words)

    # Fast heuristics for routing
    if word_count < 12 and not any(k in prompt_clean.lower() for k in ["why", "explain", "analyze", "synthesize", "design"]):
        verdict = "FAST_LOCAL"
        intent = "SIMPLE_LOOKUP_OR_FACT"
    elif any(k in prompt_clean.lower() for k in ["yield", "arbitrage", "price", "rate", "apy", "cve", "threat"]):
        verdict = "FAST_LOCAL"
        intent = "STRUCTURED_INTEL_QUERY"
    else:
        verdict = "ESCALATE"
        intent = "COMPLEX_REASONING_OR_GENERATION"

    latency_ms = round((time.perf_counter() - t0) * 1000, 3)
    res = {
        "verdict": verdict,
        "cached": False,
        "intent": intent,
        "word_count": word_count,
        "ahimsa_pass": True,
        "latency_ms": latency_ms,
        "q_hash": q_hash,
    }

    if len(QUERY_CACHE) < MAX_CACHE_SIZE:
        QUERY_CACHE[q_hash] = (verdict, res, time.time())
    return res


def evaluate_pratyaksa(claim: str, evidence: List[str] | None = None) -> Dict[str, Any]:
    """PRATYAKSA factual attribution decoder & certainty gate.

    Computes certainty based on evidence grounding and halts uncertain branches.
    """
    evidence = evidence or []
    claim_clean = claim.strip()
    words = claim_clean.split()

    # Base certainty calculation
    if not words:
        return {"certainty": 0.0, "status": "HALT_EMPTY", "halt": True}

    grounded_tokens = 0
    total_tokens = len(words)

    # Check evidence overlap
    evidence_text = " ".join(evidence).lower()
    for w in words:
        clean_w = re.sub(r"[^\w]", "", w).lower()
        if clean_w and clean_w in evidence_text:
            grounded_tokens += 1

    ratio = (grounded_tokens / total_tokens) if total_tokens > 0 else 0.0
    certainty = round(min(1.0, max(0.1, ratio * 1.5 if evidence else 0.85)), 3)

    # PRATYAKSA Rule: Halt branch if certainty < 0.65 when evidence was supplied but failed to ground
    halt = (certainty < 0.65 and bool(evidence))

    return {
        "certainty": certainty,
        "grounded_ratio": round(ratio, 3),
        "evidence_count": len(evidence),
        "halt": halt,
        "status": "HALT_UNCERTAIN" if halt else "ADMITTED",
        "canon": "PRATYAKSA-001",
    }


class ManasHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: Dict[str, Any]) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {
                "status": "LIVE",
                "core": "MANAS",
                "subsystem": "System-1 Pre-Filter & PRATYAKSA Attribution",
                "revision": REVISION,
                "baseline": BASELINE,
                "port": DEFAULT_PORT,
                "cache_entries": len(QUERY_CACHE),
            })
        else:
            self._send_json(404, {"error": "endpoint not found"})

    def do_POST(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        try:
            payload = json.loads(post_body.decode("utf-8")) if post_body else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON body"})
            return

        if self.path == "/triage":
            prompt = payload.get("prompt", "")
            res = triage_query(prompt)
            self._send_json(200, res)
        elif self.path == "/evaluate":
            claim = payload.get("claim", "")
            evidence = payload.get("evidence", [])
            res = evaluate_pratyaksa(claim, evidence)
            self._send_json(200, res)
        else:
            self._send_json(404, {"error": "endpoint not found"})

    def log_message(self, fmt, *args) -> None:
        # Silent or concise logging
        log.debug("%s - %s", self.address_string(), fmt % args)


def run_server(port: int = DEFAULT_PORT) -> None:
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, ManasHandler)
    log.info("MANAS System-1 Daemon listening on http://127.0.0.1:%d (revision %s)", port, REVISION)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("MANAS Daemon interrupted by user")
    finally:
        httpd.server_close()


def main() -> int:
    ap = argparse.ArgumentParser(prog="tx_manas", description="System-1 Pre-Filter & PRATYAKSA Gate")
    sub = ap.add_subparsers(dest="cmd")

    p_serve = sub.add_parser("serve", help="Run HTTP daemon")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind (default: 9189)")

    p_triage = sub.add_parser("triage", help="Triage prompt via CLI")
    p_triage.add_argument("prompt", help="Query or prompt to triage")

    p_eval = sub.add_parser("evaluate", help="PRATYAKSA certainty evaluation")
    p_eval.add_argument("claim", help="Output claim text")
    p_eval.add_argument("--evidence", nargs="*", default=[], help="Supporting evidence snippets")

    args = ap.parse_args()

    if args.cmd == "serve":
        run_server(args.port)
        return 0
    elif args.cmd == "triage":
        res = triage_query(args.prompt)
        print(json.dumps(res, indent=2))
        return 0 if res["ahimsa_pass"] else 1
    elif args.cmd == "evaluate":
        res = evaluate_pratyaksa(args.claim, args.evidence)
        print(json.dumps(res, indent=2))
        return 0 if not res["halt"] else 2
    else:
        # Default action: CLI test
        ap.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
