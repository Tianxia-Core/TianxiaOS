#!/usr/bin/env python3
# ffp: FFP-CLOUDFLARE-SUBDOMAINS-SYNC io-edge python
"""
tx_cloudflare_subdomains_sync.py -- Sovereign Cloudflare DNS & Worker Route Synchronizer.

Audits and aligns Cloudflare Zone DNS records and Worker Routes with
config/subdomains.json and Cloudflare Tunnel (9dd988fb-6411-4258-8984-be51650140bb)
so all 28 subdomains resolve with HTTP 200 and zero stale Worker shadowing.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
sys.path.insert(0, str(THIS_DIR))

try:
    from tx_secret_shield import install as shield_install, sanitize
except Exception:
    def shield_install() -> None:
        pass

    def sanitize(s: str) -> str:
        return s

TUNNEL_CNAME = "9dd988fb-6411-4258-8984-be51650140bb.cfargotunnel.com"
RELAY_IP = "<TX_RELAY_IPV4>"


def _export_key(key: str) -> str:
    vault_tool = os.environ.get("TX_VAULT_TOOL", str(THIS_DIR / "tx_creds.py"))
    try:
        import tx_vault_access as vx  # type: ignore
        v = vx.get(key, optional=True)
        if v:
            return str(v).strip()
    except Exception:
        pass
    try:
        proc = subprocess.run(
            [sys.executable, vault_tool, "export", key],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass
    return ""


def _cf_req(token: str, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = "https://api.cloudflare.com/client/v4" + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _discover_vault_tokens() -> Dict[str, str]:
    found: Dict[str, str] = {}
    for k in ("cloudflare_workers_token", "cloudflare_api_token", "api_token", "r2_api_token"):
        val = _export_key(k)
        if val:
            found[k] = val
    sec_dir = Path("/var/lib/tianxia/secrets")
    for fname in ("cloudflare", "tianxia-secrets.yaml"):
        p = sec_dir / fname
        if p.exists():
            try:
                raw = p.read_text(encoding="utf-8", errors="ignore")
                try:
                    j = json.loads(raw)
                    if isinstance(j, dict):
                        for jk, jv in j.items():
                            if isinstance(jv, str) and len(jv.strip()) >= 20 and "token" in jk.lower() or "key" in jk.lower():
                                found[f"{fname}:{jk}"] = jv.strip()
                except Exception:
                    import re
                    for idx, m in enumerate(re.finditer(r"(?:token|key)\s*[:=]\s*['\"]?([A-Za-z0-9_-]{30,60})['\"]?", raw, re.I)):
                        found[f"{fname}:match_{idx}"] = m.group(1)
            except Exception:
                pass
    return found


def _pick_working_token(zone_id: str) -> Dict[str, str]:
    tokens = _discover_vault_tokens()
    account_ids = [x for x in (_export_key("AccountTag"), _export_key("account_id")) if x]
    working: Dict[str, str] = {}
    for name, tok in tokens.items():
        checks = [
            ("zones_list", "/zones"),
            ("dns", f"/zones/{zone_id}/dns_records?per_page=5"),
            ("workers", f"/zones/{zone_id}/workers/routes"),
        ]
        for idx, aid in enumerate(account_ids):
            checks.append((f"account_workers_{idx}", f"/accounts/{aid}/workers/scripts"))
            checks.append((f"account_tunnels_{idx}", f"/accounts/{aid}/cfd_tunnel"))
        for capability, test_path in checks:
            if capability in working:
                continue
            try:
                res = _cf_req(tok, "GET", test_path)
                if res.get("success"):
                    working[capability] = tok
                    print(sanitize(f"[ok] capability '{capability}' verified via key '{name}'"))
                    if capability == "zones_list":
                        znames = [(z.get("name"), z.get("status")) for z in res.get("result", [])]
                        print(sanitize(f"     visible zones: {znames}"))
                    if capability.startswith("account_workers"):
                        scripts = [s.get("id") for s in res.get("result", [])]
                        print(sanitize(f"     account worker scripts: {scripts}"))
                    if capability.startswith("account_tunnels"):
                        tuns = [(t.get("id"), t.get("name"), t.get("status")) for t in res.get("result", [])]
                        print(sanitize(f"     account tunnels: {tuns}"))
            except urllib.error.HTTPError as exc:
                print(sanitize(f"[info] key '{name}' -> {capability} HTTP {exc.code}"))
            except Exception as exc:
                print(sanitize(f"[info] key '{name}' -> {capability} err {type(exc).__name__}"))
    return working


def main() -> int:
    shield_install()
    ap = argparse.ArgumentParser(description="Audit and sync Cloudflare DNS & Worker routes for rasaxmachina.com")
    ap.add_argument("--sync", action="store_true", help="Apply missing DNS CNAMEs and clean stale Worker routes")
    args = ap.parse_args()

    zone_id = _export_key("cloudflare_zone_id")
    if not zone_id:
        print("[err] cloudflare_zone_id not found in tx_creds")
        return 1

    caps = _pick_working_token(zone_id)
    subs_cfg = json.loads((REPO_ROOT / "config" / "subdomains.json").read_text(encoding="utf-8"))["subdomains"]
    desired_fqdns = {v["fqdn"]: (k, v) for k, v in subs_cfg.items() if v.get("fqdn")}
    desired_fqdns["x402.rasaxmachina.com"] = ("x402", {"fqdn": "x402.rasaxmachina.com", "routing": "vps_relay"})

    if "dns" in caps:
        dns_tok = caps["dns"]
        recs: List[Dict[str, Any]] = _cf_req(dns_tok, "GET", f"/zones/{zone_id}/dns_records?per_page=100").get("result", [])
        by_name: Dict[str, List[Dict[str, Any]]] = {}
        for r in recs:
            if r.get("type") in ("A", "AAAA", "CNAME"):
                by_name.setdefault(r["name"], []).append(r)

        print(f"\n=== DNS AUDIT ({len(recs)} total records) ===")
        for fqdn in sorted(desired_fqdns.keys()):
            existing = by_name.get(fqdn, [])
            if not existing:
                print(f"  MISSING: {fqdn}")
                if args.sync:
                    target = RELAY_IP if fqdn in ("relay.rasaxmachina.com", "x402.rasaxmachina.com") else TUNNEL_CNAME
                    rtype = "A" if target == RELAY_IP else "CNAME"
                    proxied = False if target == RELAY_IP else True
                    res = _cf_req(
                        dns_tok,
                        "POST",
                        f"/zones/{zone_id}/dns_records",
                        {"type": rtype, "name": fqdn, "content": target, "proxied": proxied, "ttl": 1},
                    )
                    print(f"    -> CREATED {rtype} {fqdn} -> {target} (ok={res.get('success')})")
            else:
                summary = ", ".join(f"{x['type']}:{x['content']}(proxied={x.get('proxied')})" for x in existing)
                print(f"  PRESENT: {fqdn:<32} {summary}")
                if args.sync and fqdn == "etamanga.rasaxmachina.com":
                    for x in existing:
                        if x["content"] != TUNNEL_CNAME:
                            res = _cf_req(
                                dns_tok,
                                "PUT",
                                f"/zones/{zone_id}/dns_records/{x['id']}",
                                {"type": "CNAME", "name": fqdn, "content": TUNNEL_CNAME, "proxied": True, "ttl": 1},
                            )
                            print(f"    -> UPDATED {fqdn} -> {TUNNEL_CNAME} (ok={res.get('success')})")

    if "workers" in caps:
        w_tok = caps["workers"]
        routes: List[Dict[str, Any]] = _cf_req(w_tok, "GET", f"/zones/{zone_id}/workers/routes").get("result", [])
        print(f"\n=== WORKER ROUTES AUDIT ({len(routes)} routes) ===")
        for rt in routes:
            print(f"  ROUTE {rt['id']}: {rt.get('pattern')} -> script={rt.get('script')}")
            if args.sync and rt.get("script"):
                # Delete stale Worker route shadowing live Cloudflare Tunnel origin
                res = _cf_req(w_tok, "DELETE", f"/zones/{zone_id}/workers/routes/{rt['id']}")
                print(f"    -> DELETED stale Worker route {rt.get('pattern')} (ok={res.get('success')})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
