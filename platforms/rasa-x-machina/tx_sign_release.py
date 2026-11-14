#!/usr/bin/env python3
# ffp: FFP-RELEASE-SIGNER crypto-signer python
"""
tx_sign_release.py — Deterministic Ed25519 Release Signer, Checksum & CycloneDX SBOM Generator.
Signs Linux, Windows, and Android release executables using the Rasa-X-Machina Ed25519 key
and verifies every signature with OpenSSL 3.x (`-rawin`) before returning success.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PRIV_KEY = Path.home() / ".config" / "tianxia" / "release_signing" / "rxm_ed25519.pem"
PUB_KEY = Path("${TX_WORKSPACE:-/var/lib/tianxia}/TianxiaOS/keys/RELEASE_SIGNING_KEY.pub.pem")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sign_and_verify(target: Path, priv_key: Path, pub_key: Path) -> Path:
    sig_path = target.with_name(target.name + ".sig")
    subprocess.run(
        [
            "openssl", "pkeyutl", "-sign",
            "-inkey", str(priv_key),
            "-rawin",
            "-in", str(target),
            "-out", str(sig_path),
        ],
        check=True,
    )
    subprocess.run(
        [
            "openssl", "pkeyutl", "-verify",
            "-pubin", "-inkey", str(pub_key),
            "-rawin",
            "-in", str(target),
            "-sigfile", str(sig_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return sig_path


def sign_directory(dist_dir: Path, project_name: str, version: str) -> int:
    if not PRIV_KEY.exists() or not PUB_KEY.exists():
        print(f"[tx_sign_release] ERROR: Missing signing keys ({PRIV_KEY} / {PUB_KEY})", file=sys.stderr)
        return 2

    dist_dir.mkdir(parents=True, exist_ok=True)
    # Remove old generated metadata before computing fresh checksums
    for stale in ("SHA256SUMS", "SHA256SUMS.sig", "SBOM.cdx.json", "RELEASE_SIGNING_KEY.pub.pem"):
        p = dist_dir / stale
        if p.exists():
            p.unlink()
    for stale_sig in list(dist_dir.glob("*.sig")):
        stale_sig.unlink()

    artifacts = sorted(
        p for p in dist_dir.iterdir()
        if p.is_file() and not p.name.endswith(".sig")
    )
    if not artifacts:
        print(f"[tx_sign_release] ERROR: No artifacts found in {dist_dir}", file=sys.stderr)
        return 3

    components = []
    sum_lines = []
    for art in artifacts:
        digest = sha256_file(art)
        sig = sign_and_verify(art, PRIV_KEY, PUB_KEY)
        sig_digest = sha256_file(sig)
        sum_lines.append(f"{digest}  {art.name}")
        sum_lines.append(f"{sig_digest}  {sig.name}")
        components.append({
            "type": "application",
            "name": art.name,
            "version": version,
            "hashes": [{"alg": "SHA-256", "content": digest}],
            "properties": [
                {"name": "tianxia:signature", "value": sig.name},
                {"name": "tianxia:size_bytes", "value": str(art.stat().st_size)},
            ],
        })

    pub_dest = dist_dir / "RELEASE_SIGNING_KEY.pub.pem"
    shutil.copy2(PUB_KEY, pub_dest)
    sum_lines.append(f"{sha256_file(pub_dest)}  {pub_dest.name}")

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "component": {
                "type": "application",
                "name": project_name,
                "version": version,
                "publisher": "Rasa-X-Machina (Proposed OÜ — Tallinn, Estonia)",
            },
            "properties": [
                {"name": "tianxia:build_law_edition", "value": "v4.4-DASAVIDYAYANA-GLOBAL42-GDPR++"},
                {"name": "tianxia:signature_algorithm", "value": "Ed25519 (RFC 8032)"},
            ],
        },
        "components": components,
    }
    sbom_path = dist_dir / "SBOM.cdx.json"
    sbom_path.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    sum_lines.append(f"{sha256_file(sbom_path)}  {sbom_path.name}")

    sums_path = dist_dir / "SHA256SUMS"
    sums_path.write_text("\n".join(sum_lines) + "\n", encoding="utf-8")
    sign_and_verify(sums_path, PRIV_KEY, PUB_KEY)
    print(f"[tx_sign_release] Signed & verified {len(artifacts)} executables in {dist_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Sign and verify multi-platform release artifacts.")
    ap.add_argument("dist_dir", type=Path, help="Directory containing built executables")
    ap.add_argument("--project", default="TianxiaOS", help="Project name for CycloneDX SBOM")
    ap.add_argument("--version", default="v8.6.0", help="Release version string")
    args = ap.parse_args()
    return sign_directory(args.dist_dir, args.project, args.version)


if __name__ == "__main__":
    raise SystemExit(main())
