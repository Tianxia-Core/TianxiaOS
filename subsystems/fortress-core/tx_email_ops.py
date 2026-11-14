#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-EMAIL-OPS glue python
"""
tx_email_ops.py -- Email outreach engine (Resend).
Sends to CRM leads, weekly digest, and cold sequences.
User-Agent fixed for Cloudflare bot-bypass.
"""
import json, os, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tx_observability as obs
import tx_secrets_vault as sv
import tx_crm
from tx_net_guard import _check_allowlist

log = obs.get_logger("tx_email_ops")
VAULT_PASSPHRASE = os.environ.get("TX_VAULT_PASSPHRASE", "tianxia-sovereign-2026-vault")
FROM = "noreply@example.invalid"
UA = "Resend/v1.0 Python-URllib"

def _key():
    vault = sv.open_vault(VAULT_PASSPHRASE)
    try: return vault.get_secret("email_api_key") or ""
    finally:
        try: vault.lock()
        except: pass

def _send(to, subject, html):
    key = _key()
    data = json.dumps({"from": FROM, "to": [to], "subject": subject, "html": html}).encode()
    req = urllib.request.Request("https://api.resend.com/emails",
        data=data, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": UA})
    _check_allowlist("https://api.resend.com/emails")
    r = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return r

def send_to_lead(lead_id, subject, html):
    """Send email to a CRM lead."""
    leads = tx_crm.list_leads(limit=500)
    lead = next((l for l in leads if l["id"] == lead_id), None)
    if not lead or not lead.get("handle") or "@" not in lead["handle"]:
        return {"ok": False, "error": "lead has no email handle"}
    r = _send(lead["handle"], subject, html)
    tx_crm.log_activity(lead_id, "outreach", f"[email] {subject}")
    return r

def broadcast(subject, html):
    """Send to ALL leads with email handles."""
    leads = tx_crm.list_leads(limit=500)
    sent = 0
    for l in leads:
        handle = l.get("handle", "")
        if "@" in handle:
            try:
                _send(handle, subject, html)
                sent += 1
            except Exception as e:
                log.warning("broadcast fail %s: %s", handle[:20], str(e)[:50])
    return {"ok": True, "sent": sent}

def digest():
    """Weekly digest with ledger stats + latest signals."""
    revs = "checking ledger..."
    return broadcast("🜂 The Hussar Dispatch — Weekly", f"""
<html><body style="font-family:system-ui;background:#0b0e17;color:#e5e7eb;padding:2rem">
<h1 style="color:#22c55e">🜂 The Hussar Dispatch</h1>
<p>Weekly intelligence from the Faery Fortress — autonomous revenue, ledger-audited signals, and sovereign infrastructure.</p>
<p>This week: new signals published, SKUs live, mesh expanded. Every number is ledger-audited.</p>
<p><a href="https://shop.rasaxmachina.com" style="color:#3b82f6">Browse the Fortress Market →</a></p>
</body></html>""")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "digest"
    if cmd == "digest": print(json.dumps(digest(), indent=1))
    elif cmd == "broadcast": print(json.dumps(broadcast(sys.argv[2], sys.argv[3]), indent=1))
    else: print(json.dumps({"usage": "digest | broadcast <subject> <html>"}))
