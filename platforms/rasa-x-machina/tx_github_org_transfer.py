#!/usr/bin/env python3
# ffp: FFP-GH-TRANSFER glue python
"""
tx_github_org_transfer.py — Atomic, Idempotent GitHub Organization Repository Transfer Engine.

Transfers all active and planned repositories from a source GitHub organization
(default: ``Tianxia-Core``) into a target GitHub organization (default:
``Rasa-X-Machina``) once ``collinstaken525-cloud`` is granted ``admin`` membership
on ``Rasa-X-Machina`` by ``coltak88``.

Satisfies DSS-14.2 / Dasavidyayana NL & SLECO-SO++ invariants:
- BHAIRAVI: Read-only ``--dry-run`` is default; mutating ``--execute`` requires an
  explicit capability gate (``--execute`` + verified org ``admin`` permission).
- PRATYANGIRA: Zero dynamic code execution or shell interpolation; strict ``subprocess.run`` argv arrays.
- BAGALAMUKHI: Bounded subprocess timeouts and clean shutdown flag handling.
- TARA: Structured exception handling with audit logging.
- TRIPURA: Three discovery/verification paths (REST ``orgs/{org}/repos``,
  ``gh repo list``, and offline manifest fallback).
- BHUVANESVARI: Queries ``os.environ`` for orgs, state directories, and timeouts.
- DHUMAVATI: Durable JSONL ledger trace for every planned and executed transfer.
- ANNAPURNA: Idempotent & resumable atomic state file via ``os.replace``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | tx_github_org_transfer | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("tx_github_org_transfer")

REVISION = "2026.11-DSS14-PINNED"
SHUTDOWN_REQUESTED = False


def _handle_signal(signum: int, _frame: Any) -> None:
    global SHUTDOWN_REQUESTED
    SHUTDOWN_REQUESTED = True
    logger.warning("Received signal %d; stopping cleanly after current repository.", signum)


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_state_dir() -> Path:
    base = os.environ.get("TX_STATE_DIR") or os.path.join(
        os.environ.get("HOME", "/tmp"), ".local", "state", "tianxia"
    )
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def append_ledger(ledger_path: Path, event: dict[str, Any]) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": utc_now(), **event}
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def save_state_atomic(state_path: Path, payload: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_path.with_name(f".{state_path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_path, state_path)


def run_gh(args: list[str], timeout_sec: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error("gh invocation failed (%s): %s", args[:3], exc)
        return subprocess.CompletedProcess(["gh", *args], returncode=127, stdout="", stderr=str(exc))


def discover_repos(source_org: str, manifest_fallback: Path | None, timeout_sec: int) -> list[dict[str, Any]]:
    """TRIPURA: Three independent ways to enumerate source organization repositories."""
    # Path 1: REST API pagination
    res = run_gh(
        ["api", "--paginate", f"orgs/{source_org}/repos?per_page=100&type=all"],
        timeout_sec=timeout_sec,
    )
    if res.returncode == 0 and res.stdout.strip():
        try:
            raw = json.loads(res.stdout)
            if isinstance(raw, list):
                return [
                    {
                        "name": r["name"],
                        "archived": bool(r.get("archived", False)),
                        "private": bool(r.get("private", True)),
                        "description": r.get("description") or "",
                        "topics": list(r.get("topics") or []),
                    }
                    for r in raw
                ]
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Primary REST parse fallback triggered: %s", exc)

    # Path 2: gh repo list CLI JSON
    res2 = run_gh(
        [
            "repo", "list", source_org, "--limit", "200",
            "--json", "name,isArchived,isPrivate,description,repositoryTopics",
        ],
        timeout_sec=timeout_sec,
    )
    if res2.returncode == 0 and res2.stdout.strip():
        try:
            raw2 = json.loads(res2.stdout)
            return [
                {
                    "name": r["name"],
                    "archived": bool(r.get("isArchived", False)),
                    "private": bool(r.get("isPrivate", True)),
                    "description": r.get("description") or "",
                    "topics": [t["name"] for t in (r.get("repositoryTopics") or []) if "name" in t],
                }
                for r in raw2
            ]
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Secondary gh repo list parse fallback triggered: %s", exc)

    # Path 3: Offline manifest fallback
    if manifest_fallback and manifest_fallback.exists():
        try:
            data = json.loads(manifest_fallback.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (OSError, ValueError) as exc:
            logger.error("Manifest fallback failed: %s", exc)

    raise RuntimeError(f"Unable to discover repositories for source org '{source_org}'.")


def verify_target_admin_gate(target_org: str, timeout_sec: int) -> tuple[bool, str]:
    """BHAIRAVI capability gate: verify authenticated user holds active admin role on target_org."""
    res = run_gh(["api", f"user/memberships/orgs/{target_org}"], timeout_sec=timeout_sec)
    if res.returncode != 0:
        return False, f"Not an active admin member of {target_org}: {res.stderr.strip()}"
    try:
        info = json.loads(res.stdout)
        role = info.get("role", "")
        state = info.get("state", "")
        if role == "admin" and state == "active":
            return True, f"Verified active admin permission on {target_org}"
        return False, f"Insufficient permission on {target_org}: role={role!r}, state={state!r}"
    except ValueError as exc:
        return False, f"Invalid membership JSON from GitHub API: {exc}"


def repo_exists_in_target(target_org: str, repo_name: str, timeout_sec: int) -> bool:
    res = run_gh(["api", f"repos/{target_org}/{repo_name}", "--jq", ".full_name"], timeout_sec=timeout_sec)
    return res.returncode == 0 and res.stdout.strip().lower() == f"{target_org}/{repo_name}".lower()


def sync_target_org_profile(target_org: str, timeout_sec: int) -> bool:
    res = run_gh(
        [
            "api", "-X", "PATCH", f"orgs/{target_org}",
            "-f", "name=Rasa-X-Machina",
            "-f", "blog=https://rasaxmachina.com",
            "-f", (
                "description=Rasa-X-Machina (Proposed Estonian Deep-Tech Entity) — "
                "Sovereign Polyglot Systems, Post-Quantum Security, & Autonomous Infrastructure"
            ),
        ],
        timeout_sec=timeout_sec,
    )
    return res.returncode == 0


def transfer_repository(source_org: str, target_org: str, repo_name: str, timeout_sec: int) -> tuple[bool, str]:
    res = run_gh(
        [
            "api", "-X", "POST",
            f"repos/{source_org}/{repo_name}/transfer",
            "-f", f"new_owner={target_org}",
        ],
        timeout_sec=timeout_sec,
    )
    if res.returncode == 0:
        return True, "accepted"
    return False, res.stderr.strip() or res.stdout.strip()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Transfer all Tianxia-Core repositories into Rasa-X-Machina with one command."
    )
    ap.add_argument(
        "--source",
        default=os.environ.get("GH_SOURCE_ORG", "Tianxia-Core"),
        help="Source GitHub organization (default: Tianxia-Core)",
    )
    ap.add_argument(
        "--target",
        default=os.environ.get("GH_TARGET_ORG", "Rasa-X-Machina"),
        help="Target GitHub organization (default: Rasa-X-Machina)",
    )
    ap.add_argument(
        "--include-archived",
        action="store_true",
        help="Also transfer archived repositories (default: skip archived repos)",
    )
    ap.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Repository names to skip during transfer",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional fallback JSON manifest path",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("TX_GH_TIMEOUT_SEC", "30")),
        help="Per-API-call timeout in seconds (default: 30)",
    )
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview transfer plan and verify permissions without mutating GitHub (default)",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Capability gate: execute live repository transfers into target org",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary on stdout",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    execute_mode = bool(args.execute)
    state_dir = default_state_dir()
    ledger_path = state_dir / "gh_org_transfer_ledger.jsonl"
    state_path = state_dir / "gh_org_transfer_state.json"

    try:
        repos = discover_repos(args.source, args.manifest, args.timeout)
    except RuntimeError as exc:
        logger.error("%s", exc)
        return 2

    excluded = {name.strip() for name in args.exclude if name.strip()}
    candidates = [
        r for r in sorted(repos, key=lambda x: x["name"].lower())
        if (args.include_archived or not r["archived"]) and r["name"] not in excluded
    ]

    admin_ok, admin_msg = verify_target_admin_gate(args.target, args.timeout)
    logger.info(
        "Discovered %d total repos in %s (%d eligible for transfer to %s). Target gate: %s",
        len(repos),
        args.source,
        len(candidates),
        args.target,
        admin_msg,
    )

    summary: dict[str, Any] = {
        "timestamp": utc_now(),
        "mode": "execute" if execute_mode else "dry-run",
        "source_org": args.source,
        "target_org": args.target,
        "target_admin_gate_passed": admin_ok,
        "target_admin_message": admin_msg,
        "total_discovered": len(repos),
        "eligible_count": len(candidates),
        "transferred": [],
        "already_present": [],
        "planned": [],
        "failed": [],
    }

    if not execute_mode:
        for repo in candidates:
            if repo_exists_in_target(args.target, repo["name"], args.timeout):
                summary["already_present"].append(repo["name"])
            else:
                summary["planned"].append(repo["name"])
        append_ledger(
            ledger_path,
            {
                "action": "dry_run_plan",
                "source_org": args.source,
                "target_org": args.target,
                "eligible_count": len(candidates),
                "target_admin_gate_passed": admin_ok,
            },
        )
        save_state_atomic(state_path, summary)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"[DRY-RUN] {args.source} -> {args.target}: {len(summary['planned'])} repos queued:")
            for name in summary["planned"]:
                print(f"  - {args.source}/{name} -> {args.target}/{name}")
            if not admin_ok:
                print(f"\n[GATE INFO] {admin_msg}")
                print(
                    f"Once coltak88 grants collinstaken525-cloud admin access on {args.target}, run:\n"
                    f"  python3 {Path(__file__).resolve()} --source {args.source} --target {args.target} --execute"
                )
        return 0

    # Mutating execution path gated by BHAIRAVI admin capability verification
    if not admin_ok:
        logger.error("BHAIRAVI capability gate blocked transfer: %s", admin_msg)
        append_ledger(
            ledger_path,
            {
                "action": "execute_blocked",
                "source_org": args.source,
                "target_org": args.target,
                "reason": admin_msg,
            },
        )
        if args.json:
            print(json.dumps(summary, indent=2))
        return 3

    sync_target_org_profile(args.target, args.timeout)

    for repo in candidates:
        if SHUTDOWN_REQUESTED:
            logger.warning("Graceful stop requested; halting transfer loop.")
            break
        name = repo["name"]
        if repo_exists_in_target(args.target, name, args.timeout):
            logger.info("Skipping %s (already exists in %s)", name, args.target)
            summary["already_present"].append(name)
            continue

        # Note: GitHub forbids transferring an archived repo unless unarchived first;
        # candidates excludes archived repos by default.
        ok, detail = transfer_repository(args.source, args.target, name, args.timeout)
        append_ledger(
            ledger_path,
            {
                "action": "repo_transfer",
                "repo": name,
                "source_org": args.source,
                "target_org": args.target,
                "success": ok,
                "detail": detail,
            },
        )
        if ok:
            logger.info("Transferred %s/%s -> %s/%s", args.source, name, args.target, name)
            summary["transferred"].append(name)
        else:
            logger.error("Failed transferring %s/%s: %s", args.source, name, detail)
            summary["failed"].append({"repo": name, "error": detail})
        save_state_atomic(state_path, summary)
        time.sleep(0.4)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(
            f"[EXECUTED] Transferred {len(summary['transferred'])}/{len(candidates)} repos "
            f"to {args.target} (failed={len(summary['failed'])})."
        )
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
