# TianxiaOS v8.7.0 Universal Multi-Format Signed Release Bundle

All release executables and rootless distribution packages are built deterministically under **TianxiaOS Build Law (`v4.4-DASAVIDYAYANA-GLOBAL42-GDPR++`)** via `tx_package_builder.py` and signed with the sovereign **Ed25519 (RFC 8032)** release key (`TianxiaOS/keys/RELEASE_SIGNING_KEY.pub.pem`), accompanied by `SHA256SUMS`, `SHA256SUMS.sig`, and a CycloneDX 1.5 `SBOM.cdx.json`.

## Published Artifacts (`v8.7.0`)

| Artifact | Platform / ABI | Format & Installation |
| :--- | :--- | :--- |
| `tianxiaos_8.7.0_amd64.deb` | Debian / Ubuntu / Kali `amd64` | Standard Debian `ar` package (`sudo dpkg -i tianxiaos_8.7.0_amd64.deb`) |
| `tianxiaos_8.7.0_arm64.deb` | Debian / Ubuntu / RPi `arm64` | Standard Debian `ar` package (`sudo dpkg -i tianxiaos_8.7.0_arm64.deb`) |
| `tianxiaos-8.7.0-1.x86_64.rpm` | Fedora / RHEL / openSUSE `x86_64` | RPM v4 SVR4 `cpio.gz` package (`sudo rpm -Uvh tianxiaos-8.7.0-1.x86_64.rpm`) |
| `tianxiaos-8.7.0-1.aarch64.rpm` | Fedora / RHEL / openSUSE `aarch64` | RPM v4 SVR4 `cpio.gz` package (`sudo rpm -Uvh tianxiaos-8.7.0-1.aarch64.rpm`) |
| `TianxiaOS-8.7.0-x86_64.AppImage` | Universal Linux `x86_64` | Zero-FUSE Type-2 Portable AppImage (`chmod +x && ./TianxiaOS-8.7.0-x86_64.AppImage`) |
| `TianxiaOS-8.7.0-aarch64.AppImage` | Universal Linux `aarch64` | Zero-FUSE Type-2 Portable AppImage (`chmod +x && ./TianxiaOS-8.7.0-aarch64.AppImage`) |
| `tianxiaos-v8.7.0-linux-x86_64.tar.gz` | Linux `x86_64` | Sovereign Tarball (`bin/`, `share/`, SLECO-SO++ `install.sh`, `SBOM.cdx.json`) |
| `tianxiaos-v8.7.0-linux-aarch64.tar.gz` | Linux `aarch64` | Sovereign Tarball (`bin/`, `share/`, SLECO-SO++ `install.sh`, `SBOM.cdx.json`) |
| `tianxiaos-v8.7.0-windows-x86_64.tar.gz` | Windows 10/11 `x86_64` | Sovereign Windows Archive (`bin/tianxia.exe`, `SBOM.cdx.json`, `LICENSE`) |
| `tianxiaos-v8.7.0-android-aarch64.tar.gz` | Android / Termux `aarch64` | Sovereign Android CLI Archive (`bin/tianxia`, `install.sh`, `SBOM.cdx.json`) |
| `tianxia-v8.7.0-linux-x86_64` | Linux `x86_64` | 100% Static musl ELF (`statically linked, stripped`) |
| `tianxia-v8.7.0-linux-aarch64` | Linux `aarch64` | 100% Static musl ELF (`statically linked, stripped`) |
| `tianxia-v8.7.0-android-aarch64` | Android / Termux `aarch64` | Native Rust PIE ELF (`aarch64-linux-android`, zero external crates) |
| `tianxia-v8.7.0-windows-x86_64.exe` | Windows 10/11 `x86_64` | Static PE32+ Console Executable (ANSI VT TUI + Full CLI) |
| `TianxiaOS-Sovereign-v8.7.0-android.apk` | Android 8.0–16 (`arm64-v8a`) | Page-Aligned (`zipalign -p 4`) + 4096-bit RSA APK Signature Scheme v2/v3 |

## Cryptographic Verification

```bash
openssl pkeyutl -verify -pubin -inkey RELEASE_SIGNING_KEY.pub.pem -rawin -in SHA256SUMS -sigfile SHA256SUMS.sig
sha256sum -c SHA256SUMS
```
