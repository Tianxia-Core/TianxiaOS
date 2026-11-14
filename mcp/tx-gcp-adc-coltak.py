#!${TX_PREFIX:-/usr/local}/files/usr/bin/python3
# ffp: FFP-GCP-ADC-COLTAK crypto-signer python
"""
TianxiaOS GCP ADC & Project TianxiaOS Provisioner for collinstaken525-cloud@users.noreply.github.com
Configures Application Default Credentials (ADC) for Antigravity CLI, google-agents-cli,
and Vertex AI on Project TianxiaOS (with attached billing account & free GCP credits),
and syncs ADC across Termux (pixel8pro) and latitude-tianxia.
"""
import argparse
import hashlib
import base64
import json
import os
import secrets
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Official Google Cloud SDK OAuth2 installed-app client ID & secret (public per RFC 8252)
GCLOUD_CLIENT_ID = "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com"
GCLOUD_CLIENT_SECRET = "d-FL95Q19q7MQmFpd7hHD0Ty"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/appengine.admin",
    "https://www.googleapis.com/auth/sqlservice.login",
    "https://www.googleapis.com/auth/compute",
    "https://www.googleapis.com/auth/accounts.reauth",
]
ADC_PATH = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
GCLOUD_CFG = Path.home() / ".config" / "gcloud" / "configurations" / "config_default"


def status():
    print("=== [TIANXIAOS // GCP ADC & AGENTS-CLI STATUS] ===")
    if ADC_PATH.exists():
        data = json.loads(ADC_PATH.read_text())
        ctype = data.get("type", "unknown")
        proj = data.get("quota_project_id") or data.get("project_id") or os.environ.get("GOOGLE_CLOUD_PROJECT", "TianxiaOS")
        ident = data.get("client_email") or "collinstaken525-cloud@users.noreply.github.com"
        print(f"ADC File         : {ADC_PATH} (present, mode={oct(ADC_PATH.stat().st_mode & 0o777)})")
        print(f"Credential Type  : {ctype}")
        print(f"Identity         : {ident}")
        print(f"Target Project   : {proj}")
    else:
        print(f"ADC File         : MISSING ({ADC_PATH})")
    return 0


def login(project_hint="TianxiaOS", email_hint="collinstaken525-cloud@users.noreply.github.com"):
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    redirect_uri = "http://localhost:8085/"
    params = {
        "response_type": "code",
        "client_id": GCLOUD_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
        "login_hint": email_hint,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    print("=== [TIANXIAOS // collinstaken525-cloud@users.noreply.github.com GCP ADC LOGIN] ===")
    print("1. Open this URL in your browser (pre-targeted to collinstaken525-cloud@users.noreply.github.com):")
    print(f"\n   {url}\n")
    print("2. Sign in as collinstaken525-cloud@users.noreply.github.com and approve access.")
    print("3. Copy the full http://localhost:8085/?code=... URL (or just the code= value) from the address bar:")
    raw = input("\nPaste URL or authorization code here: ").strip()
    if "code=" in raw:
        parsed = urllib.parse.parse_qs(urllib.parse.urlsplit(raw).query)
        code = parsed.get("code", [raw])[0]
    else:
        code = raw
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": GCLOUD_CLIENT_ID,
        "client_secret": GCLOUD_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        tok = json.loads(resp.read().decode())
    access_token = tok["access_token"]
    refresh_token = tok["refresh_token"]

    # Discover exact project ID for TianxiaOS
    resolved_project = project_hint
    try:
        preq = urllib.request.Request(
            "https://cloudresourcemanager.googleapis.com/v1/projects",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(preq, timeout=10) as presp:
            projects = json.loads(presp.read().decode()).get("projects", [])
        for p in projects:
            pid = p.get("projectId", "")
            pname = p.get("name", "")
            print(f"   Found GCP Project: name={pname!r} projectId={pid!r}")
            if pname.lower() == "tianxiaos" or "tianxia" in pid.lower():
                resolved_project = pid
    except Exception as exc:
        print(f"   Note: project auto-discovery skipped ({exc}); using {resolved_project}")

    adc_payload = {
        "account": email_hint,
        "client_id": GCLOUD_CLIENT_ID,
        "client_secret": GCLOUD_CLIENT_SECRET,
        "quota_project_id": resolved_project,
        "refresh_token": refresh_token,
        "type": "authorized_user",
        "universe_domain": "googleapis.com",
    }
    ADC_PATH.parent.mkdir(parents=True, exist_ok=True)
    ADC_PATH.write_text(json.dumps(adc_payload, indent=2) + "\n")
    os.chmod(ADC_PATH, 0o600)
    GCLOUD_CFG.parent.mkdir(parents=True, exist_ok=True)
    GCLOUD_CFG.write_text(f"[core]\naccount = {email_hint}\nproject = {resolved_project}\n[billing]\nquota_project = {resolved_project}\n")
    subprocess.run(["scp", str(ADC_PATH), "latitude-lan:/root/.config/gcloud/application_default_credentials.json"], check=False)
    print(f"\n[OK] ADC saved for {email_hint} (project={resolved_project}) and synced to latitude-tianxia!")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", nargs="?", default="status", choices=["status", "login"])
    ap.add_argument("--project", default="TianxiaOS")
    ap.add_argument("--email", default="collinstaken525-cloud@users.noreply.github.com")
    args = ap.parse_args()
    sys.exit(status() if args.action == "status" else login(args.project, args.email))
