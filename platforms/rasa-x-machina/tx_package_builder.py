#!/usr/bin/env python3
# ffp: FFP-PKG-BUILDER content-pipeline python
"""
tx_package_builder.py — Sovereign Universal Multi-Format Rootless Package Builder.
Deterministically generates and verifies:
  1. Debian Binary Packages (`.deb`: `ar` + `debian-binary` + `control.tar.gz` + `data.tar.gz`)
  2. Red Hat / Fedora / SUSE Packages (`.rpm`: RPM v4 Lead + Signature Header + Metadata Header + SVR4 `070701` cpio.gz)
  3. Zero-FUSE Portable Linux AppImages (`.AppImage`: Type-2 ELF64 musl runtime + embedded `AppDir`)
  4. Sovereign Tarballs (`.tar.gz`: `bin/`, `share/`, SLECO-SO++ `install.sh`, CycloneDX `SBOM.cdx.json`, `LICENSE`, `RELEASE_SIGNING_KEY.pub.pem`)
  5. Hermetic Nix Flake (`flake.nix`: `packages`, `apps`, `overlays.default`, `nixosModules`)
  6. Ed25519 Detached Signatures (`.sig`), `SHA256SUMS`, `SHA256SUMS.sig` & CycloneDX 1.5 `SBOM.cdx.json`
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import platform
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

SOURCE_DATE_EPOCH = 1762992000  # Deterministic reproducible timestamp (2025-11-13T00:00:00Z)

SCRIPT_DIR = Path(__file__).resolve().parent
SIGNER_SCRIPT = SCRIPT_DIR / "tx_sign_release.py"
WORKSPACE_ROOT = Path("${TX_WORKSPACE:-/var/lib/tianxia}")
TIANXIAOS_ROOT = WORKSPACE_ROOT / "TianxiaOS"

ICON_SVG_CANDIDATES = [
    TIANXIAOS_ROOT / "platforms" / "rasa-x-machina" / "ui" / "icon.svg",
    Path("/var/lib/tianxia/ui/icon.svg"),
]
LICENSE_CANDIDATES = [
    TIANXIAOS_ROOT / "LICENSE",
]
PUBKEY_CANDIDATES = [
    TIANXIAOS_ROOT / "keys" / "RELEASE_SIGNING_KEY.pub.pem",
    Path("/var/lib/tianxia/releases/RELEASE_SIGNING_KEY.pub.pem"),
    Path.home() / ".config" / "tianxia" / "release_signing" / "rxm_ed25519.pub.pem",
]
APPIMAGE_C_CANDIDATES = [
    TIANXIAOS_ROOT / "zig" / "appimage_runtime.c",
    SCRIPT_DIR / "appimage_runtime.c",
]
APPIMAGE_RUNTIME_CACHE = SCRIPT_DIR / ".appimage_runtime"


@dataclass(frozen=True)
class RepoPackageSpec:
    repo: str
    pkg_name: str
    app_title: str
    bin_name: str
    bin_prefix: str
    version: str
    summary: str
    description: str
    license_id: str
    homepage: str


REPO_SPECS: dict[str, RepoPackageSpec] = {
    "tianxiaos": RepoPackageSpec(
        repo="Tianxia-Core/TianxiaOS",
        pkg_name="tianxiaos",
        app_title="TianxiaOS",
        bin_name="tianxia",
        bin_prefix="tianxia",
        version="8.7.0",
        summary="TianxiaOS Sovereign CLI, 9-App TUI & Polyglot Operating Substrate",
        description=(
            "Deterministic zero-dependency polyglot CLI, 9-tab interactive terminal cockpit,\n"
            "TetraLedger 4-way verifier, and DSS-14.2 / GDPR++ Build Law suite engineered by Rasa-X-Machina."
        ),
        license_id="Apache-2.0",
        homepage="https://rasaxmachina.com",
    ),
    "tianxiaos-releases": RepoPackageSpec(
        repo="Tianxia-Core/tianxiaos-releases",
        pkg_name="tianxiaos",
        app_title="TianxiaOS",
        bin_name="tianxia",
        bin_prefix="tianxia",
        version="8.7.0",
        summary="TianxiaOS Sovereign CLI, 9-App TUI & Polyglot Operating Substrate",
        description=(
            "Deterministic zero-dependency polyglot CLI, 9-tab interactive terminal cockpit,\n"
            "TetraLedger 4-way verifier, and DSS-14.2 / GDPR++ Build Law suite engineered by Rasa-X-Machina."
        ),
        license_id="Apache-2.0",
        homepage="https://rasaxmachina.com",
    ),
    "nimbus2": RepoPackageSpec(
        repo="Tianxia-Core/nimbus2",
        pkg_name="nimbus2",
        app_title="Nimbus2",
        bin_name="nimbus2",
        bin_prefix="nimbus2",
        version="2.5.0",
        summary="Nimbus2 Unified High-Performance Polyglot Proxy & Route Intelligence Suite",
        description=(
            "Unified polyglot proxy router, ASN validator, route benchmark engine, and\n"
            "multiboot resilience toolkit engineered by Rasa-X-Machina."
        ),
        license_id="Apache-2.0",
        homepage="https://rasaxmachina.com",
    ),
    "007-scanner": RepoPackageSpec(
        repo="Tianxia-Core/AegisScan",
        pkg_name="007-scanner",
        app_title="007-Scanner",
        bin_name="007-scanner",
        bin_prefix="007-scanner",
        version="2.1.0",
        summary="007-Scanner Standalone 8-Domain Polyglot Security & Supply-Chain Auditor",
        description=(
            "Zero-dependency 8-domain static security scanner covering secrets, injection,\n"
            "cryptography, ACLs, AI prompt safety, and CI/CD supply-chain posture."
        ),
        license_id="MIT",
        homepage="https://rasaxmachina.com",
    ),
    "secrets-vault": RepoPackageSpec(
        repo="Tianxia-Core/AetherVault",
        pkg_name="secrets-vault",
        app_title="Secrets-Vault",
        bin_name="secrets-vault",
        bin_prefix="secrets-vault",
        version="2.1.0",
        summary="Secrets Vault Zero-Dependency AES-256-GCM Cryptographic Vault & HMAC Ledger",
        description=(
            "Authenticated AES-256-GCM secret store with HKDF-SHA256 key derivation and\n"
            "append-only HMAC audit chain engineered by Rasa-X-Machina."
        ),
        license_id="MIT",
        homepage="https://rasaxmachina.com",
    ),
    "tianxia-mobile": RepoPackageSpec(
        repo="Tianxia-Core/tianxia-mobile",
        pkg_name="tianxia-mobile",
        app_title="Tianxia-Mobile",
        bin_name="tx-mobile-bridge",
        bin_prefix="tx-mobile-bridge",
        version="2.1.0",
        summary="Tianxia Mobile Sovereign Android Client, AetherMesh Daemon & Host Bridge",
        description=(
            "Cross-platform sovereign mobile mesh host bridge and Android arm64-v8a\n"
            "companion suite engineered by Rasa-X-Machina."
        ),
        license_id="Apache-2.0",
        homepage="https://rasaxmachina.com",
    ),
}


DEFAULT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <!-- ffp: FFP-PKG-ICON frontend svg -->
  <rect width="512" height="512" rx="108" fill="#080808"/>
  <polygon points="256,64 422,160 422,352 256,448 90,352 90,160" fill="none" stroke="#00f59b" stroke-width="22" stroke-linejoin="round"/>
  <path d="M188 196 H324 M256 196 V336 M202 316 L256 254 L310 316" fill="none" stroke="#22d3ee" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

APACHE_LICENSE_TEXT = """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright 2025-2026 Collins Takem / Rasa-X-Machina (Proposed RASA-X-MACHINA OU, Tallinn, Estonia)
Licensed under the Apache License, Version 2.0.
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def load_icon_svg() -> bytes:
    for p in ICON_SVG_CANDIDATES:
        if p.is_file():
            return p.read_bytes()
    return DEFAULT_SVG.encode("utf-8")


def load_license_bytes(custom_path: Path | None = None) -> bytes:
    if custom_path and custom_path.is_file():
        return custom_path.read_bytes()
    for p in LICENSE_CANDIDATES:
        if p.is_file():
            return p.read_bytes()
    return APACHE_LICENSE_TEXT.encode("utf-8")


def load_pubkey_bytes() -> bytes:
    for p in PUBKEY_CANDIDATES:
        if p.is_file():
            return p.read_bytes()
    raise FileNotFoundError("RELEASE_SIGNING_KEY.pub.pem not found in canonical paths")


def gzip_deterministic(raw: bytes, level: int = 9) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, compresslevel=level, mtime=0) as gz:
        gz.write(raw)
    return buf.getvalue()


def build_desktop_entry(spec: RepoPackageSpec, exec_path: str | None = None) -> bytes:
    cmd = exec_path or f"/usr/bin/{spec.bin_name}"
    text = (
        "[Desktop Entry]\n"
        "Version=1.5\n"
        "Type=Application\n"
        f"Name={spec.app_title}\n"
        f"GenericName={spec.summary}\n"
        f"Comment={spec.summary}\n"
        f"Exec={cmd}\n"
        f"Icon={spec.bin_name}\n"
        "Terminal=true\n"
        "Categories=System;Security;ConsoleOnly;\n"
        f"Keywords=Tianxia;Sovereign;RasaXMachina;{spec.app_title};\n"
    )
    return text.encode("utf-8")


def build_manpage_gz(spec: RepoPackageSpec) -> bytes:
    roff = (
        f'.TH "{spec.bin_name.upper()}" "1" "2026-11-13" "{spec.app_title} {spec.version}" "Rasa-X-Machina Sovereign Manual"\n'
        ".SH NAME\n"
        f"{spec.bin_name} \\- {spec.summary}\n"
        ".SH SYNOPSIS\n"
        f".B {spec.bin_name}\n"
        "[\\fICOMMAND\\fR] [\\fIOPTIONS\\fR]\n"
        ".SH DESCRIPTION\n"
        f"{spec.description}\n"
        ".PP\n"
        "Built deterministically under TianxiaOS Build Law (DSS-14.2 / Polyglot FFP-First / SLECO-SO++ / GDPR++)\n"
        "and cryptographically attested with Ed25519 detached signatures.\n"
        ".SH OPTIONS\n"
        ".TP\n"
        ".B \\-\\-version\n"
        "Display version, target architecture, and Build Law edition.\n"
        ".TP\n"
        ".B \\-\\-help\n"
        "Display command reference and subcommands.\n"
        ".SH AUTHOR\n"
        "Collins Takem <collinstaken525-cloud@users.noreply.github.com> / Rasa-X-Machina (Proposed RASA-X-MACHINA OU, Tallinn, Estonia).\n"
    )
    return gzip_deterministic(roff.encode("utf-8"))


def build_debian_copyright(spec: RepoPackageSpec) -> bytes:
    text = (
        "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
        f"Upstream-Name: {spec.pkg_name}\n"
        "Upstream-Contact: Collins Takem <collinstaken525-cloud@users.noreply.github.com>\n"
        f"Source: https://github.com/{spec.repo}\n\n"
        "Files: *\n"
        "Copyright: 2025-2026 Collins Takem / Rasa-X-Machina (Proposed RASA-X-MACHINA OU, Tallinn, Estonia)\n"
        f"License: {spec.license_id}\n"
        " Distributed under sovereign cryptographic release attestation. See /usr/share/doc/ copyright terms.\n"
    )
    return text.encode("utf-8")


def build_postinst_script() -> bytes:
    text = (
        "#!/bin/sh\n"
        "# ffp: FFP-DEB-POSTINST content-pipeline sh\n"
        "set +e\n"
        "if command -v update-desktop-database >/dev/null 2>&1; then\n"
        "    update-desktop-database -q /usr/share/applications >/dev/null 2>&1 || true\n"
        "fi\n"
        "exit 0\n"
    )
    return text.encode("utf-8")


def build_sleco_install_sh(spec: RepoPackageSpec) -> bytes:
    lines = [
        "#!/usr/bin/env bash",
        "# ffp: FFP-TAR-INSTALLER content-pipeline bash",
        "# SLECO-SO++ Sovereign Rootless-Capable Package Installer",
        "set +e",
        "set +u",
        "",
        'SCRIPT_PATH="${0}"',
        'SRC_ROOT="${SCRIPT_PATH%/*}"',
        'if [ "${SRC_ROOT}" = "${SCRIPT_PATH}" ]; then',
        '    SRC_ROOT="."',
        "fi",
        "",
        'if [ "${UID:-$(id -u)}" -eq 0 ]; then',
        '    PREFIX="${PREFIX:-/usr/local}"',
        "else",
        '    PREFIX="${PREFIX:-${HOME}/.local}"',
        "fi",
        "",
        "cleanup_install() {",
        "    local rc=$?",
        '    if [ "${rc}" -ne 0 ]; then',
        "        printf '[install] ERROR: installation exited with code %d\\n' \"${rc}\" >&2",
        "    fi",
        "}",
        "trap cleanup_install EXIT",
        "",
        'mkdir -p "${PREFIX}/bin" "${PREFIX}/share/applications" "${PREFIX}/share/icons/hicolor/scalable/apps" "${PREFIX}/share/man/man1"',
        'if [ $? -ne 0 ]; then exit 2; fi',
        "",
        f'if [ -f "${{SRC_ROOT}}/bin/{spec.bin_name}" ]; then',
        f'    cp -f "${{SRC_ROOT}}/bin/{spec.bin_name}" "${{PREFIX}}/bin/{spec.bin_name}"',
        f'    chmod 0755 "${{PREFIX}}/bin/{spec.bin_name}"',
        "fi",
        f'if [ -f "${{SRC_ROOT}}/share/applications/{spec.bin_name}.desktop" ]; then',
        f'    cp -f "${{SRC_ROOT}}/share/applications/{spec.bin_name}.desktop" "${{PREFIX}}/share/applications/{spec.bin_name}.desktop"',
        "fi",
        f'if [ -f "${{SRC_ROOT}}/share/icons/hicolor/scalable/apps/{spec.bin_name}.svg" ]; then',
        f'    cp -f "${{SRC_ROOT}}/share/icons/hicolor/scalable/apps/{spec.bin_name}.svg" "${{PREFIX}}/share/icons/hicolor/scalable/apps/{spec.bin_name}.svg"',
        "fi",
        f'if [ -f "${{SRC_ROOT}}/share/man/man1/{spec.bin_name}.1.gz" ]; then',
        f'    cp -f "${{SRC_ROOT}}/share/man/man1/{spec.bin_name}.1.gz" "${{PREFIX}}/share/man/man1/{spec.bin_name}.1.gz"',
        "fi",
        f"printf '[install] Installed {spec.app_title} v{spec.version} to %s\\n' \"${{PREFIX}}\"",
        "exit 0",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def create_deterministic_tar(entries: list[tuple[str, bytes | None, int, str]], fmt: int = tarfile.GNU_FORMAT) -> bytes:
    """
    entries: list of (arcname, data_or_None_for_dir, mode, link_target)
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=fmt) as tf:
        for arcname, data, mode, link_target in entries:
            ti = tarfile.TarInfo(name=arcname)
            ti.mtime = SOURCE_DATE_EPOCH
            ti.uid = 0
            ti.gid = 0
            ti.uname = "root"
            ti.gname = "root"
            ti.mode = mode
            if link_target:
                ti.type = tarfile.SYMTYPE
                ti.linkname = link_target
                ti.size = 0
                tf.addfile(ti)
            elif data is None:
                ti.type = tarfile.DIRTYPE
                ti.size = 0
                tf.addfile(ti)
            else:
                ti.type = tarfile.REGTYPE
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


# ─── 1. Debian `.deb` Builder (`ar` + `control.tar.gz` + `data.tar.gz`) ───────

def pack_ar_archive(members: list[tuple[str, bytes]]) -> bytes:
    out = bytearray(b"!<arch>\n")
    for name, payload in members:
        if len(name) > 16:
            raise ValueError(f"ar member name exceeds 16 chars: {name}")
        hdr = (
            f"{name:<16}"
            f"{SOURCE_DATE_EPOCH:<12d}"
            f"{0:<6d}"
            f"{0:<6d}"
            f"{'100644':<8s}"
            f"{len(payload):<10d}"
            "`\n"
        ).encode("ascii")
        if len(hdr) != 60:
            raise AssertionError(f"Invalid ar header length {len(hdr)}")
        out.extend(hdr)
        out.extend(payload)
        if len(payload) % 2 == 1:
            out.append(0x0A)
    return bytes(out)


def build_deb_package(spec: RepoPackageSpec, bin_bytes: bytes, deb_arch: str, out_path: Path) -> Path:
    desktop_bytes = build_desktop_entry(spec, f"/usr/bin/{spec.bin_name}")
    svg_bytes = load_icon_svg()
    man_bytes = build_manpage_gz(spec)
    copyright_bytes = build_debian_copyright(spec)

    file_map: list[tuple[str, bytes, int]] = [
        (f"usr/bin/{spec.bin_name}", bin_bytes, 0o755),
        (f"usr/share/applications/{spec.bin_name}.desktop", desktop_bytes, 0o644),
        (f"usr/share/icons/hicolor/scalable/apps/{spec.bin_name}.svg", svg_bytes, 0o644),
        (f"usr/share/man/man1/{spec.bin_name}.1.gz", man_bytes, 0o644),
        (f"usr/share/doc/{spec.pkg_name}/copyright", copyright_bytes, 0o644),
    ]

    dirs = [
        "./",
        "./usr/",
        "./usr/bin/",
        "./usr/share/",
        "./usr/share/applications/",
        "./usr/share/icons/",
        "./usr/share/icons/hicolor/",
        "./usr/share/icons/hicolor/scalable/",
        "./usr/share/icons/hicolor/scalable/apps/",
        "./usr/share/man/",
        "./usr/share/man/man1/",
        "./usr/share/doc/",
        f"./usr/share/doc/{spec.pkg_name}/",
    ]
    data_entries: list[tuple[str, bytes | None, int, str]] = [(d, None, 0o755, "") for d in dirs]
    md5_lines: list[str] = []
    total_bytes = 0
    for rel_path, content, mode in file_map:
        data_entries.append((f"./{rel_path}", content, mode, ""))
        md5_lines.append(f"{md5_bytes(content)}  {rel_path}")
        total_bytes += len(content)

    data_tar_gz = gzip_deterministic(create_deterministic_tar(data_entries))

    installed_kib = max(1, (total_bytes + 1023) // 1024)
    desc_formatted = "\n".join(f" {line}" if line.strip() else " ." for line in spec.description.splitlines())
    control_text = (
        f"Package: {spec.pkg_name}\n"
        f"Version: {spec.version}\n"
        "Section: utils\n"
        "Priority: optional\n"
        f"Architecture: {deb_arch}\n"
        f"Installed-Size: {installed_kib}\n"
        "Maintainer: Collins Takem <collinstaken525-cloud@users.noreply.github.com>\n"
        f"Homepage: {spec.homepage}\n"
        f"Description: {spec.summary}\n"
        f"{desc_formatted}\n"
    ).encode("utf-8")

    md5sums_bytes = ("\n".join(md5_lines) + "\n").encode("utf-8")
    postinst_bytes = build_postinst_script()

    control_entries: list[tuple[str, bytes | None, int, str]] = [
        ("./", None, 0o755, ""),
        ("./control", control_text, 0o644, ""),
        ("./md5sums", md5sums_bytes, 0o644, ""),
        ("./postinst", postinst_bytes, 0o755, ""),
    ]
    control_tar_gz = gzip_deterministic(create_deterministic_tar(control_entries))

    deb_bytes = pack_ar_archive([
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", control_tar_gz),
        ("data.tar.gz", data_tar_gz),
    ])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(deb_bytes)
    return out_path


# ─── 2. RPM v4 Binary Builder (Lead + Sig Header + Meta Header + SVR4 cpio.gz) ─

RPM_INT16 = 3
RPM_INT32 = 4
RPM_STRING = 6
RPM_BIN = 7
RPM_STRING_ARRAY = 8
RPM_I18NSTRING = 9


def pack_cpio_newc(files: list[tuple[str, bytes, int, int]]) -> bytes:
    """
    files: list of (cpio_path_starting_with_dot_slash, content_bytes, st_mode_with_S_IFREG, ino)
    """
    out = bytearray()
    for cpio_name, content, full_mode, ino in files:
        name_bytes = cpio_name.encode("utf-8") + b"\x00"
        hdr = (
            "070701"
            f"{ino:08X}"
            f"{full_mode:08X}"
            f"{0:08X}"
            f"{0:08X}"
            f"{1:08X}"
            f"{SOURCE_DATE_EPOCH:08X}"
            f"{len(content):08X}"
            f"{0:08X}"
            f"{1:08X}"
            f"{0:08X}"
            f"{0:08X}"
            f"{len(name_bytes):08X}"
            f"{0:08X}"
        ).encode("ascii")
        out.extend(hdr)
        out.extend(name_bytes)
        pad_hdr = (4 - (len(out) % 4)) % 4
        if pad_hdr:
            out.extend(b"\x00" * pad_hdr)
        out.extend(content)
        pad_data = (4 - (len(out) % 4)) % 4
        if pad_data:
            out.extend(b"\x00" * pad_data)

    trailer_name = b"TRAILER!!!\x00"
    trailer_hdr = (
        "070701"
        + ("00000000" * 3)
        + "00000001"
        + ("00000000" * 7)
        + f"{len(trailer_name):08X}"
        + "00000000"
    ).encode("ascii")
    out.extend(trailer_hdr)
    out.extend(trailer_name)
    pad_end = (4 - (len(out) % 4)) % 4
    if pad_end:
        out.extend(b"\x00" * pad_end)
    return bytes(out)


def encode_rpm_header(tags: list[tuple[int, int, object]], region_tag: int) -> bytes:
    """
    Encodes an RPM v4 header structure (`0x8eade801\x00\x00\x00\x00`) with an immutable region trailer (`62` or `63`).
    """
    sorted_tags = sorted(tags, key=lambda item: item[0])
    store = bytearray()
    index_entries: list[tuple[int, int, int, int]] = []

    for tag, dtype, val in sorted_tags:
        if dtype == RPM_INT16:
            align = 2
        elif dtype == RPM_INT32:
            align = 4
        else:
            align = 1
        pad = (align - (len(store) % align)) % align
        if pad:
            store.extend(b"\x00" * pad)
        offset = len(store)

        if dtype == RPM_INT16:
            seq = list(val)  # type: ignore[arg-type]
            count = len(seq)
            for v in seq:
                store.extend(struct.pack(">H", int(v) & 0xFFFF))
        elif dtype == RPM_INT32:
            seq = list(val)  # type: ignore[arg-type]
            count = len(seq)
            for v in seq:
                store.extend(struct.pack(">I", int(v) & 0xFFFFFFFF))
        elif dtype in (RPM_STRING, RPM_I18NSTRING):
            s = str(val).encode("utf-8") + b"\x00"
            count = 1
            store.extend(s)
        elif dtype == RPM_STRING_ARRAY:
            seq_s = [str(x).encode("utf-8") + b"\x00" for x in val]  # type: ignore[union-attr]
            count = len(seq_s)
            for sb in seq_s:
                store.extend(sb)
        elif dtype == RPM_BIN:
            raw_b = bytes(val)  # type: ignore[arg-type]
            count = len(raw_b)
            store.extend(raw_b)
        else:
            raise ValueError(f"Unsupported RPM dtype {dtype}")

        index_entries.append((tag, dtype, offset, count))

    total_entries = len(index_entries) + 1
    region_offset = len(store)
    region_trailer = struct.pack(">IIiI", region_tag, RPM_BIN, -(total_entries * 16), 16)
    store.extend(region_trailer)

    all_indices = [(region_tag, RPM_BIN, region_offset, 16)] + index_entries
    hdr = bytearray(b"\x8e\xad\xe8\x01\x00\x00\x00\x00")
    hdr.extend(struct.pack(">II", len(all_indices), len(store)))
    for t, dt_code, off, cnt in all_indices:
        hdr.extend(struct.pack(">IIiI", t, dt_code, off, cnt))
    hdr.extend(store)
    return bytes(hdr)


def build_rpm_package(spec: RepoPackageSpec, bin_bytes: bytes, rpm_arch: str, out_path: Path) -> Path:
    desktop_bytes = build_desktop_entry(spec, f"/usr/bin/{spec.bin_name}")
    svg_bytes = load_icon_svg()
    man_bytes = build_manpage_gz(spec)
    copyright_bytes = build_debian_copyright(spec)

    # Ordered by full path for RPM determinism
    raw_items: list[tuple[str, str, bytes, int, int]] = [
        ("/usr/bin/", spec.bin_name, bin_bytes, stat.S_IFREG | 0o755, 0),
        ("/usr/share/applications/", f"{spec.bin_name}.desktop", desktop_bytes, stat.S_IFREG | 0o644, 0),
        (f"/usr/share/doc/{spec.pkg_name}/", "copyright", copyright_bytes, stat.S_IFREG | 0o644, 2),
        ("/usr/share/icons/hicolor/scalable/apps/", f"{spec.bin_name}.svg", svg_bytes, stat.S_IFREG | 0o644, 0),
        ("/usr/share/man/man1/", f"{spec.bin_name}.1.gz", man_bytes, stat.S_IFREG | 0o644, 2),
    ]

    dirnames: list[str] = []
    dirindexes: list[int] = []
    basenames: list[str] = []
    filesizes: list[int] = []
    filemodes: list[int] = []
    filerdevs: list[int] = []
    filemtimes: list[int] = []
    filemd5s: list[str] = []
    filelinktos: list[str] = []
    fileflags: list[int] = []
    fileusernames: list[str] = []
    filegroupnames: list[str] = []
    filedevices: list[int] = []
    fileinodes: list[int] = []
    filelangs: list[str] = []
    cpio_entries: list[tuple[str, bytes, int, int]] = []

    for idx, (dname, bname, content, fmode, fflag) in enumerate(raw_items, start=1):
        if dname not in dirnames:
            dirnames.append(dname)
        dirindexes.append(dirnames.index(dname))
        basenames.append(bname)
        filesizes.append(len(content))
        filemodes.append(fmode)
        filerdevs.append(0)
        filemtimes.append(SOURCE_DATE_EPOCH)
        filemd5s.append(md5_bytes(content))
        filelinktos.append("")
        fileflags.append(fflag)
        fileusernames.append("root")
        filegroupnames.append("root")
        filedevices.append(1)
        fileinodes.append(idx)
        filelangs.append("")
        cpio_entries.append((f".{dname}{bname}", content, fmode, idx))

    raw_cpio = pack_cpio_newc(cpio_entries)
    gz_cpio = gzip_deterministic(raw_cpio)
    total_size = sum(filesizes)

    meta_tags: list[tuple[int, int, object]] = [
        (100, RPM_STRING_ARRAY, ["C"]),
        (1000, RPM_STRING, spec.pkg_name),
        (1001, RPM_STRING, spec.version),
        (1002, RPM_STRING, "1"),
        (1004, RPM_I18NSTRING, spec.summary),
        (1005, RPM_I18NSTRING, spec.description),
        (1006, RPM_INT32, [SOURCE_DATE_EPOCH]),
        (1007, RPM_STRING, "latitude-tianxia.rasaxmachina.internal"),
        (1009, RPM_INT32, [total_size]),
        (1011, RPM_STRING, "Rasa-X-Machina (Proposed OU, Tallinn, Estonia)"),
        (1014, RPM_STRING, spec.license_id),
        (1016, RPM_I18NSTRING, "Applications/System"),
        (1020, RPM_STRING, spec.homepage),
        (1021, RPM_STRING, "linux"),
        (1022, RPM_STRING, rpm_arch),
        (1028, RPM_INT32, filesizes),
        (1030, RPM_INT16, filemodes),
        (1033, RPM_INT16, filerdevs),
        (1034, RPM_INT32, filemtimes),
        (1035, RPM_STRING_ARRAY, filemd5s),
        (1036, RPM_STRING_ARRAY, filelinktos),
        (1037, RPM_INT32, fileflags),
        (1039, RPM_STRING_ARRAY, fileusernames),
        (1040, RPM_STRING_ARRAY, filegroupnames),
        (1047, RPM_STRING_ARRAY, [spec.pkg_name]),
        (1095, RPM_INT32, filedevices),
        (1096, RPM_INT32, fileinodes),
        (1097, RPM_STRING_ARRAY, filelangs),
        (1112, RPM_INT32, [0x08]),
        (1113, RPM_STRING_ARRAY, [f"{spec.version}-1"]),
        (1116, RPM_INT32, dirindexes),
        (1117, RPM_STRING_ARRAY, basenames),
        (1118, RPM_STRING_ARRAY, dirnames),
        (1124, RPM_STRING, "cpio"),
        (1125, RPM_STRING, "gzip"),
        (1126, RPM_STRING, "9"),
        (5062, RPM_STRING, "utf-8"),
        (5092, RPM_STRING_ARRAY, [hashlib.sha256(gz_cpio).hexdigest()]),
        (5093, RPM_INT32, [8]),
        (5097, RPM_STRING_ARRAY, [hashlib.sha256(raw_cpio).hexdigest()]),
    ]
    meta_hdr = encode_rpm_header(meta_tags, region_tag=63)

    sha1_hex = hashlib.sha1(meta_hdr).hexdigest()
    sha256_hex = hashlib.sha256(meta_hdr).hexdigest()
    md5_raw = hashlib.md5(meta_hdr + gz_cpio).digest()

    sig_tags: list[tuple[int, int, object]] = [
        (269, RPM_STRING, sha1_hex),
        (273, RPM_STRING, sha256_hex),
        (1000, RPM_INT32, [len(meta_hdr) + len(gz_cpio)]),
        (1004, RPM_BIN, md5_raw),
        (1007, RPM_INT32, [len(raw_cpio)]),
    ]
    sig_hdr = bytearray(encode_rpm_header(sig_tags, region_tag=62))
    sig_pad = (8 - (len(sig_hdr) % 8)) % 8
    if sig_pad:
        sig_hdr.extend(b"\x00" * sig_pad)

    archnum = 1 if rpm_arch == "x86_64" else 19
    lead_name = f"{spec.pkg_name}-{spec.version}-1".encode("utf-8")[:65]
    lead_name_padded = lead_name + (b"\x00" * (66 - len(lead_name)))
    lead = struct.pack(">4sBBHH66sHH16s", b"\xed\xab\xee\xdb", 3, 0, 0, archnum, lead_name_padded, 1, 5, b"\x00" * 16)
    if len(lead) != 96:
        raise AssertionError(f"Invalid RPM lead size {len(lead)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(lead + bytes(sig_hdr) + meta_hdr + gz_cpio)
    return out_path


# ─── 3. Zero-FUSE Portable `.AppImage` Builder ───────────────────────────────

def ensure_appimage_runtime(arch: str) -> bytes:
    """
    Returns static musl ELF64 AppImage Type-2 runtime stub for `x86_64` or `aarch64`.
    Uses TRIPURA 3-way resolution: cached runtime -> Zig cross-compile -> host cc.
    """
    APPIMAGE_RUNTIME_CACHE.mkdir(parents=True, exist_ok=True)
    cached = APPIMAGE_RUNTIME_CACHE / f"runtime-{arch}"
    if cached.is_file() and cached.stat().st_size > 4096:
        raw = bytearray(cached.read_bytes())
    else:
        c_src = next((p for p in APPIMAGE_C_CANDIDATES if p.is_file()), None)
        if c_src is None:
            raise FileNotFoundError("Missing appimage_runtime.c and no cached AppImage runtime found")
        zig_bin = shutil.which("zig") or "${TX_PREFIX:-/usr/local}/files/usr/bin/zig"
        if Path(zig_bin).is_file():
            subprocess.run(
                [
                    zig_bin, "cc",
                    "-target", f"{arch}-linux-musl",
                    "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-static", "-s",
                    str(c_src), "-o", str(cached),
                ],
                check=True,
            )
            raw = bytearray(cached.read_bytes())
        else:
            host_arch = platform.machine()
            cc_bin = shutil.which("gcc") or shutil.which("cc")
            if cc_bin and host_arch == arch:
                subprocess.run([cc_bin, "-std=c11", "-O2", "-static", "-s", str(c_src), "-o", str(cached)], check=True)
                raw = bytearray(cached.read_bytes())
            else:
                raise RuntimeError(f"Cannot build AppImage runtime for {arch}: neither cached stub nor zig found")

    # Stamp AppImage Type 2 magic `AI\x02` at ELF e_ident[8..10]
    if raw[:4] != b"\x7fELF":
        raise RuntimeError(f"AppImage runtime for {arch} is not a valid ELF binary")
    raw[8:11] = b"AI\x02"
    return bytes(raw)


def build_appimage_package(spec: RepoPackageSpec, bin_bytes: bytes, arch: str, out_path: Path) -> Path:
    runtime_bytes = ensure_appimage_runtime(arch)
    pad_len = (4096 - (len(runtime_bytes) % 4096)) % 4096
    runtime_aligned = runtime_bytes + (b"\x00" * pad_len)

    apprun_script = (
        "#!/bin/sh\n"
        "# ffp: FFP-APPIMAGE-APPRUN content-pipeline sh\n"
        "set +e\n"
        'HERE="${APPDIR:-$(dirname "$(readlink -f "$0")")}"\n'
        'export PATH="${HERE}/usr/bin:${PATH:-/usr/bin:/bin}"\n'
        'export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"\n'
        f'exec "${{HERE}}/usr/bin/{spec.bin_name}" "$@"\n'
    ).encode("utf-8")

    desktop_bytes = build_desktop_entry(spec, spec.bin_name)
    svg_bytes = load_icon_svg()
    license_bytes = load_license_bytes()

    # Pure POSIX ustar entries so the C11 zero-FUSE extractor unpacks in O(N) without external tools
    ustar_entries: list[tuple[str, bytes | None, int, str]] = [
        ("AppDir", None, 0o755, ""),
        ("AppDir/AppRun", apprun_script, 0o755, ""),
        (f"AppDir/{spec.bin_name}.desktop", desktop_bytes, 0o644, ""),
        (f"AppDir/{spec.bin_name}.svg", svg_bytes, 0o644, ""),
        ("AppDir/.DirIcon", svg_bytes, 0o644, ""),
        ("AppDir/usr", None, 0o755, ""),
        ("AppDir/usr/bin", None, 0o755, ""),
        (f"AppDir/usr/bin/{spec.bin_name}", bin_bytes, 0o755, ""),
        ("AppDir/usr/share", None, 0o755, ""),
        ("AppDir/usr/share/applications", None, 0o755, ""),
        (f"AppDir/usr/share/applications/{spec.bin_name}.desktop", desktop_bytes, 0o644, ""),
        ("AppDir/usr/share/icons", None, 0o755, ""),
        ("AppDir/usr/share/icons/hicolor", None, 0o755, ""),
        ("AppDir/usr/share/icons/hicolor/scalable", None, 0o755, ""),
        ("AppDir/usr/share/icons/hicolor/scalable/apps", None, 0o755, ""),
        (f"AppDir/usr/share/icons/hicolor/scalable/apps/{spec.bin_name}.svg", svg_bytes, 0o644, ""),
        ("AppDir/usr/share/doc", None, 0o755, ""),
        (f"AppDir/usr/share/doc/{spec.pkg_name}", None, 0o755, ""),
        (f"AppDir/usr/share/doc/{spec.pkg_name}/LICENSE", license_bytes, 0o644, ""),
    ]
    payload_tar = create_deterministic_tar(ustar_entries, fmt=tarfile.USTAR_FORMAT)
    offset = len(runtime_aligned)
    trailer = b"TXAI2\x00\x00\x00" + struct.pack("<QQ", offset, len(payload_tar))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(runtime_aligned + payload_tar + trailer)
    out_path.chmod(0o755)
    return out_path


# ─── 4. Structured Sovereign `.tar.gz` Builder ───────────────────────────────

def build_tarball_package(
    spec: RepoPackageSpec,
    bin_bytes: bytes,
    platform_tag: str,
    out_path: Path,
    is_windows: bool = False,
    license_path: Path | None = None,
) -> Path:
    root = f"{spec.pkg_name}-v{spec.version}-{platform_tag}"
    exe_name = f"{spec.bin_name}.exe" if is_windows else spec.bin_name
    desktop_bytes = build_desktop_entry(spec, f"/usr/local/bin/{spec.bin_name}")
    svg_bytes = load_icon_svg()
    man_bytes = build_manpage_gz(spec)
    install_sh = build_sleco_install_sh(spec)
    license_bytes = load_license_bytes(license_path)
    pubkey_bytes = load_pubkey_bytes()

    mini_sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": "2026-11-13T00:00:00Z",
            "component": {
                "type": "application",
                "name": spec.app_title,
                "version": f"v{spec.version}",
                "publisher": "Rasa-X-Machina (Proposed OÜ — Tallinn, Estonia)",
            },
        },
        "components": [
            {
                "type": "application",
                "name": exe_name,
                "version": f"v{spec.version}",
                "hashes": [{"alg": "SHA-256", "content": sha256_bytes(bin_bytes)}],
            }
        ],
    }
    sbom_bytes = (json.dumps(mini_sbom, indent=2) + "\n").encode("utf-8")

    entries: list[tuple[str, bytes | None, int, str]] = [
        (root, None, 0o755, ""),
        (f"{root}/bin", None, 0o755, ""),
        (f"{root}/bin/{exe_name}", bin_bytes, 0o755, ""),
        (f"{root}/share", None, 0o755, ""),
        (f"{root}/share/applications", None, 0o755, ""),
        (f"{root}/share/applications/{spec.bin_name}.desktop", desktop_bytes, 0o644, ""),
        (f"{root}/share/icons", None, 0o755, ""),
        (f"{root}/share/icons/hicolor", None, 0o755, ""),
        (f"{root}/share/icons/hicolor/scalable", None, 0o755, ""),
        (f"{root}/share/icons/hicolor/scalable/apps", None, 0o755, ""),
        (f"{root}/share/icons/hicolor/scalable/apps/{spec.bin_name}.svg", svg_bytes, 0o644, ""),
        (f"{root}/share/man", None, 0o755, ""),
        (f"{root}/share/man/man1", None, 0o755, ""),
        (f"{root}/share/man/man1/{spec.bin_name}.1.gz", man_bytes, 0o644, ""),
        (f"{root}/install.sh", install_sh, 0o755, ""),
        (f"{root}/SBOM.cdx.json", sbom_bytes, 0o644, ""),
        (f"{root}/LICENSE", license_bytes, 0o644, ""),
        (f"{root}/RELEASE_SIGNING_KEY.pub.pem", pubkey_bytes, 0o644, ""),
    ]
    tar_gz = gzip_deterministic(create_deterministic_tar(entries))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(tar_gz)
    return out_path


# ─── 5. Hermetic Nix Flake Generator ─────────────────────────────────────────

def generate_release_flake_nix(
    spec: RepoPackageSpec,
    x86_64_sha256: str,
    aarch64_sha256: str,
    release_repo: str | None = None,
) -> str:
    dl_repo = release_repo or spec.repo
    mod_attr = spec.pkg_name.replace("-", "")
    return f"""# ffp: FFP-NIX-FLAKE declarative nix
{{
  description = "{spec.app_title} v{spec.version} — {spec.summary}";

  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  }};

  outputs = {{ self, nixpkgs, ... }}:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      artifactMeta = {{
        "x86_64-linux" = {{
          url = "https://github.com/{dl_repo}/releases/download/v{spec.version}/{spec.bin_prefix}-v{spec.version}-linux-x86_64";
          sha256 = "{x86_64_sha256}";
        }};
        "aarch64-linux" = {{
          url = "https://github.com/{dl_repo}/releases/download/v{spec.version}/{spec.bin_prefix}-v{spec.version}-linux-aarch64";
          sha256 = "{aarch64_sha256}";
        }};
      }};
      mkSovereignPkg = pkgs: system:
        let
          metaInfo = artifactMeta.${{system}};
        in
        pkgs.stdenvNoCC.mkDerivation {{
          pname = "{spec.pkg_name}";
          version = "{spec.version}";
          src = pkgs.fetchurl {{
            inherit (metaInfo) url sha256;
          }};
          dontUnpack = true;
          installPhase = ''
            runHook preInstall
            mkdir -p $out/bin
            install -m 0755 $src $out/bin/{spec.bin_name}
            runHook postInstall
          '';
          meta = with pkgs.lib; {{
            description = "{spec.summary}";
            homepage = "{spec.homepage}";
            platforms = supportedSystems;
            mainProgram = "{spec.bin_name}";
          }};
        }};
    in {{
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs {{ inherit system; }};
          pkg = mkSovereignPkg pkgs system;
        in {{
          default = pkg;
          "{spec.bin_name}" = pkg;
        }}
      );

      apps = forAllSystems (system: {{
        default = {{
          type = "app";
          program = "${{self.packages.${{system}}.default}}/bin/{spec.bin_name}";
        }};
      }});

      overlays.default = final: prev: {{
        "{spec.pkg_name}" = mkSovereignPkg final final.stdenv.hostPlatform.system;
      }};

      nixosModules.{mod_attr} = {{ config, lib, pkgs, ... }}:
        let
          cfg = config.services.{mod_attr};
        in {{
          options.services.{mod_attr} = {{
            enable = lib.mkEnableOption "{spec.app_title} Sovereign Service";
            package = lib.mkOption {{
              type = lib.types.package;
              default = self.packages.${{pkgs.stdenv.hostPlatform.system}}.default;
              description = "Package providing {spec.bin_name}.";
            }};
          }};
          config = lib.mkIf cfg.enable {{
            environment.systemPackages = [ cfg.package ];
          }};
        }};
    }};
}}
"""


# ─── Verification Suite ──────────────────────────────────────────────────────

def verify_built_packages(dist_dir: Path, spec: RepoPackageSpec) -> dict[str, object]:
    results: dict[str, object] = {"verified": True, "checks": []}

    def record(name: str, ok: bool, detail: str) -> None:
        if not ok:
            results["verified"] = False
        results["checks"].append({"check": name, "passed": ok, "detail": detail})  # type: ignore[attr-defined]

    # 1. Verify .deb via ar header + dpkg-deb if installed
    dpkg_deb = shutil.which("dpkg-deb")
    for deb_arch in ("amd64", "arm64"):
        deb = dist_dir / f"{spec.pkg_name}_{spec.version}_{deb_arch}.deb"
        if not deb.is_file():
            record(f"deb:{deb.name}", False, "missing")
            continue
        magic_ok = deb.read_bytes()[:8] == b"!<arch>\n"
        detail = "ar-magic=OK"
        if dpkg_deb:
            p1 = subprocess.run([dpkg_deb, "--info", str(deb)], capture_output=True, text=True, check=False)
            p2 = subprocess.run([dpkg_deb, "--contents", str(deb)], capture_output=True, text=True, check=False)
            ok = magic_ok and p1.returncode == 0 and p2.returncode == 0 and f"usr/bin/{spec.bin_name}" in p2.stdout
            detail = f"dpkg-deb info+contents rc={p1.returncode}/{p2.returncode}"
        else:
            ok = magic_ok
        record(f"deb:{deb.name}", ok, detail)

    # 2. Verify .rpm lead + signature + metadata magic + payload gzip
    for rpm_arch in ("x86_64", "aarch64"):
        rpm = dist_dir / f"{spec.pkg_name}-{spec.version}-1.{rpm_arch}.rpm"
        if not rpm.is_file():
            record(f"rpm:{rpm.name}", False, "missing")
            continue
        raw = rpm.read_bytes()
        lead_ok = raw[:4] == b"\xed\xab\xee\xdb"
        sig_ok = raw[96:100] == b"\x8e\xad\xe8\x01"
        ok = lead_ok and sig_ok and b"070701" in gzip.decompress(raw[raw.index(b"\x1f\x8b"):]) and b"TRAILER!!!" in gzip.decompress(raw[raw.index(b"\x1f\x8b"):])
        record(f"rpm:{rpm.name}", ok, f"lead+sig+cpio.gz verified ({len(raw)} bytes)")

    # 3. Verify .AppImage ELF Type-2 magic + execute native arch `--version`
    host_arch = platform.machine()
    if host_arch in ("arm64", "aarch64"):
        host_arch = "aarch64"
    for ai_arch in ("x86_64", "aarch64"):
        ai = dist_dir / f"{spec.app_title}-{spec.version}-{ai_arch}.AppImage"
        if not ai.is_file():
            record(f"appimage:{ai.name}", False, "missing")
            continue
        head = ai.read_bytes()[:16]
        elf_ok = head[:4] == b"\x7fELF" and head[8:11] == b"AI\x02"
        detail = "ELF+AI2=OK"
        ok = elf_ok
        if elf_ok and ai_arch == host_arch:
            p = subprocess.run([str(ai), "--version"], capture_output=True, text=True, timeout=15, check=False)
            if p.returncode != 0:
                p = subprocess.run([str(ai), "version"], capture_output=True, text=True, timeout=15, check=False)
            if p.returncode != 0:
                p = subprocess.run([str(ai), "--help"], capture_output=True, text=True, timeout=15, check=False)
            out_combined = p.stdout + p.stderr
            ok = p.returncode == 0 and len(out_combined.strip()) > 0
            detail = f"exec rc={p.returncode}: {out_combined.splitlines()[0] if out_combined else ''}"
        record(f"appimage:{ai.name}", ok, detail)

    # 4. Verify .tar.gz bundles
    for tgz in sorted(dist_dir.glob(f"{spec.pkg_name}-v{spec.version}-*.tar.gz")):
        with tarfile.open(tgz, "r:gz") as tf:
            names = tf.getnames()
        has_req = any("/install.sh" in n for n in names) and any("/SBOM.cdx.json" in n for n in names) and any("/bin/" in n for n in names)
        record(f"tar.gz:{tgz.name}", has_req, f"entries={len(names)}")

    # 5. Verify SHA256SUMS & OpenSSL Ed25519 signature
    sums = dist_dir / "SHA256SUMS"
    sums_sig = dist_dir / "SHA256SUMS.sig"
    pub = dist_dir / "RELEASE_SIGNING_KEY.pub.pem"
    sbom = dist_dir / "SBOM.cdx.json"
    if sums.is_file() and sums_sig.is_file() and pub.is_file() and sbom.is_file():
        v = subprocess.run(
            ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(pub), "-rawin", "-in", str(sums), "-sigfile", str(sums_sig)],
            capture_output=True, text=True, check=False,
        )
        record("openssl:SHA256SUMS.sig", v.returncode == 0, f"rc={v.returncode}")
    else:
        record("openssl:SHA256SUMS.sig", False, "missing metadata/sig")

    return results


# ─── Orchestration for a Release Directory ───────────────────────────────────

def build_all_packages_in_dir(
    dist_dir: Path,
    spec: RepoPackageSpec,
    license_path: Path | None = None,
    flake_out: Path | None = None,
    release_repo_override: str | None = None,
) -> dict[str, object]:
    vtag = f"v{spec.version}"
    linux_x64 = dist_dir / f"{spec.bin_prefix}-{vtag}-linux-x86_64"
    linux_arm64 = dist_dir / f"{spec.bin_prefix}-{vtag}-linux-aarch64"
    win_x64 = dist_dir / f"{spec.bin_prefix}-{vtag}-windows-x86_64.exe"
    android_arm64 = dist_dir / f"{spec.bin_prefix}-{vtag}-android-aarch64"

    if not linux_x64.is_file() or not linux_arm64.is_file():
        raise FileNotFoundError(
            f"Missing base Linux binaries in {dist_dir}: expected {linux_x64.name} and {linux_arm64.name}"
        )

    x64_bytes = linux_x64.read_bytes()
    arm64_bytes = linux_arm64.read_bytes()

    # 1. Build .deb (amd64 & arm64)
    build_deb_package(spec, x64_bytes, "amd64", dist_dir / f"{spec.pkg_name}_{spec.version}_amd64.deb")
    build_deb_package(spec, arm64_bytes, "arm64", dist_dir / f"{spec.pkg_name}_{spec.version}_arm64.deb")

    # 2. Build .rpm (x86_64 & aarch64)
    build_rpm_package(spec, x64_bytes, "x86_64", dist_dir / f"{spec.pkg_name}-{spec.version}-1.x86_64.rpm")
    build_rpm_package(spec, arm64_bytes, "aarch64", dist_dir / f"{spec.pkg_name}-{spec.version}-1.aarch64.rpm")

    # 3. Build .AppImage (x86_64 & aarch64)
    build_appimage_package(spec, x64_bytes, "x86_64", dist_dir / f"{spec.app_title}-{spec.version}-x86_64.AppImage")
    build_appimage_package(spec, arm64_bytes, "aarch64", dist_dir / f"{spec.app_title}-{spec.version}-aarch64.AppImage")

    # 4. Build .tar.gz for all available platforms
    build_tarball_package(spec, x64_bytes, "linux-x86_64", dist_dir / f"{spec.pkg_name}-{vtag}-linux-x86_64.tar.gz", False, license_path)
    build_tarball_package(spec, arm64_bytes, "linux-aarch64", dist_dir / f"{spec.pkg_name}-{vtag}-linux-aarch64.tar.gz", False, license_path)
    if win_x64.is_file():
        build_tarball_package(spec, win_x64.read_bytes(), "windows-x86_64", dist_dir / f"{spec.pkg_name}-{vtag}-windows-x86_64.tar.gz", True, license_path)
    if android_arm64.is_file():
        build_tarball_package(spec, android_arm64.read_bytes(), "android-aarch64", dist_dir / f"{spec.pkg_name}-{vtag}-android-aarch64.tar.gz", False, license_path)

    # 5. Optional flake.nix + flake.lock generation
    if flake_out is not None:
        flake_text = generate_release_flake_nix(
            spec,
            sha256_bytes(x64_bytes),
            sha256_bytes(arm64_bytes),
            release_repo=release_repo_override,
        )
        flake_out.parent.mkdir(parents=True, exist_ok=True)
        flake_out.write_text(flake_text, encoding="utf-8")
        lock_json = {
            "nodes": {
                "nixpkgs": {
                    "locked": {
                        "lastModified": 1767313136,
                        "narHash": "sha256-16KkgfdYqjaeRGBaYsNrhPRRENs0qzkQVUooNHtoy2w=",
                        "owner": "NixOS",
                        "repo": "nixpkgs",
                        "rev": "ac62194c3917d5f474c1a844b6fd6da2db95077d",
                        "type": "github",
                    },
                    "original": {
                        "owner": "NixOS",
                        "ref": "nixos-25.05",
                        "repo": "nixpkgs",
                        "type": "github",
                    },
                },
                "root": {"inputs": {"nixpkgs": "nixpkgs"}},
            },
            "root": "root",
            "version": 7,
        }
        flake_out.with_name("flake.lock").write_text(json.dumps(lock_json, indent=2) + "\n", encoding="utf-8")

    # 6. Sign every artifact & generate SHA256SUMS + SBOM.cdx.json
    rc = subprocess.run(
        [sys.executable, str(SIGNER_SCRIPT), str(dist_dir), "--project", spec.app_title, "--version", vtag],
        check=False,
    ).returncode
    if rc != 0:
        raise RuntimeError(f"tx_sign_release.py failed with exit code {rc}")

    return verify_built_packages(dist_dir, spec)


def resolve_spec(key_or_repo: str, version_override: str | None) -> RepoPackageSpec:
    slug = key_or_repo.split("/")[-1].lower()
    base = REPO_SPECS.get(slug)
    if base is None:
        raise KeyError(f"Unknown project/repo '{key_or_repo}'. Supported: {', '.join(sorted(REPO_SPECS))}")
    if version_override:
        clean_ver = version_override.lstrip("v")
        return RepoPackageSpec(
            repo=base.repo,
            pkg_name=base.pkg_name,
            app_title=base.app_title,
            bin_name=base.bin_name,
            bin_prefix=base.bin_prefix,
            version=clean_ver,
            summary=base.summary,
            description=base.description,
            license_id=base.license_id,
            homepage=base.homepage,
        )
    return base


def build_sibling_repo_pipeline(repo_full: str, version_override: str | None, upload_release: bool) -> dict[str, object]:
    """
    Clones a sibling `Tianxia-Core/<repo>` into an ephemeral staging dir, compiles fresh cross-platform
    executables (`linux-x86_64`, `linux-aarch64`, `windows-x86_64.exe`, `android-aarch64`, plus `.apk` for mobile),
    generates `.deb`, `.rpm`, `.AppImage`, `.tar.gz`, `flake.nix`, signs all assets, commits `flake.nix`,
    and optionally creates/updates the GitHub Release via `gh`.
    """
    spec = resolve_spec(repo_full, version_override)
    vtag = f"v{spec.version}"

    tmp_base = Path(os.environ.get("TMPDIR", "${TMPDIR:-/tmp}"))
    if not tmp_base.exists():
        tmp_base = Path(tempfile.gettempdir())
    work_root = Path(tempfile.mkdtemp(prefix=f"tx_pkg_{spec.pkg_name}_", dir=str(tmp_base)))
    repo_dir = work_root / spec.pkg_name
    dist_dir = work_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(["gh", "repo", "clone", spec.repo, str(repo_dir)], check=True)
        go_bin = shutil.which("go") or "${TX_PREFIX:-/usr/local}/files/usr/bin/go"

        # Locate Go main package in repo
        go_mod = repo_dir / "go.mod"
        go_subdir = repo_dir / "go" / "go.mod"
        go_cwd = repo_dir if go_mod.is_file() else (repo_dir / "go" if go_subdir.is_file() else None)

        if go_cwd is not None:
            cmd_dirs = sorted((go_cwd / "cmd").iterdir()) if (go_cwd / "cmd").is_dir() else [go_cwd]
            main_pkg = f"./cmd/{cmd_dirs[0].name}" if (go_cwd / "cmd").is_dir() and cmd_dirs else "."
            # Patch version strings in Go sources if present
            for go_file in go_cwd.rglob("*.go"):
                txt = go_file.read_text(encoding="utf-8")
                for old_v in ("2.4.0", "2.0.0"):
                    if old_v in txt and old_v != spec.version:
                        txt = txt.replace(old_v, spec.version)
                        go_file.write_text(txt, encoding="utf-8")

            targets = [
                ("linux", "amd64", f"{spec.bin_prefix}-{vtag}-linux-x86_64"),
                ("linux", "arm64", f"{spec.bin_prefix}-{vtag}-linux-aarch64"),
                ("windows", "amd64", f"{spec.bin_prefix}-{vtag}-windows-x86_64.exe"),
                ("android", "arm64", f"{spec.bin_prefix}-{vtag}-android-aarch64"),
            ]
            for goos, goarch, out_name in targets:
                env = os.environ.copy()
                env["CGO_ENABLED"] = "0"
                env["GOOS"] = goos
                env["GOARCH"] = goarch
                out_file = dist_dir / out_name
                rc = subprocess.run(
                    [go_bin, "build", "-trimpath", "-ldflags=-s -w", "-o", str(out_file), main_pkg],
                    cwd=str(go_cwd),
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if rc.returncode != 0 and goos == "android":
                    # Pure static Linux arm64 CGO_ENABLED=0 ELF runs identically on Android/Termux kernel
                    shutil.copy2(dist_dir / f"{spec.bin_prefix}-{vtag}-linux-aarch64", out_file)
                elif rc.returncode != 0:
                    raise RuntimeError(f"Go build failed for {spec.repo} ({goos}/{goarch}): {rc.stderr}")
                if not out_name.endswith(".exe"):
                    out_file.chmod(0o755)

        # Special handling for tianxia-mobile Android APK + Rust aether_mesh
        if spec.pkg_name == "tianxia-mobile":
            cargo_toml = repo_dir / "Cargo.toml"
            if cargo_toml.is_file():
                ct = cargo_toml.read_text(encoding="utf-8").replace('version = "2.0.0"', f'version = "{spec.version}"')
                cargo_toml.write_text(ct, encoding="utf-8")
                for rs_file in repo_dir.rglob("*.rs"):
                    rt = rs_file.read_text(encoding="utf-8")
                    if "2.0.0" in rt:
                        rs_file.write_text(rt.replace("2.0.0", spec.version), encoding="utf-8")
                subprocess.run(["cargo", "build", "--release"], cwd=str(repo_dir), check=True)
                mesh_bin = repo_dir / "target" / "release" / "aether_mesh"
                if mesh_bin.is_file():
                    dest_mesh = dist_dir / f"aether-mesh-{vtag}-android-aarch64"
                    shutil.copy2(mesh_bin, dest_mesh)
                    dest_mesh.chmod(0o755)

            # Build signed Android APK for tianxia-mobile using workspace APK builder
            apk_builder = WORKSPACE_ROOT / "app" / "build_apk_termux.sh"
            if apk_builder.is_file():
                out_apk = dist_dir / f"tianxia-mobile-{vtag}-android-arm64.apk"
                cli_ref = TIANXIAOS_ROOT / "dist" / "releases" / "tianxia-v8.7.0-android-aarch64"
                subprocess.run(["bash", str(apk_builder), str(out_apk), str(cli_ref)], check=True)

        flake_path = repo_dir / "flake.nix"
        report = build_all_packages_in_dir(
            dist_dir=dist_dir,
            spec=spec,
            license_path=repo_dir / "LICENSE",
            flake_out=flake_path,
        )

        if upload_release:
            subprocess.run(["git", "config", "user.name", "Collins Takem"], cwd=str(repo_dir), check=True)
            subprocess.run(["git", "config", "user.email", "collinstaken525-cloud@users.noreply.github.com"], cwd=str(repo_dir), check=True)
            subprocess.run(["git", "add", "-A"], cwd=str(repo_dir), check=True)
            diff_rc = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(repo_dir), check=False).returncode
            if diff_rc != 0:
                subprocess.run(
                    ["git", "commit", "-m", f"feat(packaging): add Nix flake & universal multi-format release {vtag}"],
                    cwd=str(repo_dir),
                    check=True,
                )
                subprocess.run(["git", "push", "origin", "HEAD"], cwd=str(repo_dir), check=True)

            assets = sorted(str(p) for p in dist_dir.iterdir() if p.is_file())
            view_rc = subprocess.run(
                ["gh", "release", "view", vtag, "--repo", spec.repo],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode
            notes = (
                f"## {spec.app_title} {vtag} — Universal Multi-Format Signed Release\n\n"
                f"Ships deterministic rootless packages across **`.deb`**, **`.rpm`**, **`.AppImage`**, **`.tar.gz`**, "
                f"**Nix Flake (`flake.nix`)**, **Windows `.exe`**, and **Android (`aarch64` / `.apk`)**, "
                f"with Ed25519 detached signatures (`.sig`), `SHA256SUMS`, and CycloneDX 1.5 `SBOM.cdx.json`."
            )
            if view_rc == 0:
                subprocess.run(["gh", "release", "upload", vtag, *assets, "--clobber", "--repo", spec.repo], check=True)
            else:
                subprocess.run(
                    ["gh", "release", "create", vtag, *assets, "--repo", spec.repo, "--title", f"{spec.app_title} {vtag} — Universal Multi-Format Signed Suite", "--notes", notes],
                    check=True,
                )
            report["release_url"] = f"https://github.com/{spec.repo}/releases/tag/{vtag}"
        return report
    finally:
        shutil.rmtree(work_root, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build & sign universal multi-format sovereign packages.")
    ap.add_argument("--dist-dir", type=Path, default=TIANXIAOS_ROOT / "dist" / "releases", help="Release artifact directory")
    ap.add_argument("--project", default="tianxiaos", help="Project slug (tianxiaos, nimbus2, 007-scanner, secrets-vault, tianxia-mobile)")
    ap.add_argument("--version", default=None, help="Override semantic version (e.g. 8.7.0)")
    ap.add_argument("--flake-out", type=Path, default=None, help="Optional path to write generated release flake.nix")
    ap.add_argument("--release-repo", default=None, help="Override GitHub owner/repo for Nix flake fetchurl")
    ap.add_argument("--repo", default=None, help="Clone, build, package, and optionally publish a Tianxia-Core repo")
    ap.add_argument("--upload-release", action="store_true", help="Commit flake.nix & upload GitHub Release when --repo is set")
    ap.add_argument("--verify-only", action="store_true", help="Only verify existing packages in --dist-dir")
    args = ap.parse_args()

    if args.repo:
        res = build_sibling_repo_pipeline(args.repo, args.version, args.upload_release)
        print(json.dumps(res, indent=2))
        return 0 if res.get("verified") else 1

    spec = resolve_spec(args.project, args.version)
    if args.verify_only:
        res = verify_built_packages(args.dist_dir, spec)
    else:
        res = build_all_packages_in_dir(
            dist_dir=args.dist_dir,
            spec=spec,
            flake_out=args.flake_out,
            release_repo_override=args.release_repo,
        )
    print(json.dumps(res, indent=2))
    return 0 if res.get("verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
