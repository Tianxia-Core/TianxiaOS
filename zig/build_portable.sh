#!/usr/bin/env bash
# ffp: FFP-TX-PORTABLE-BUILD content-pipeline bash
# SLECO-SO++ Cross-Platform Static Binary Builder via Zig 0.17.0
set +e
set +u

OUT_DIR="${1:-${TMPDIR:-/tmp}/tx_releases/tianxiaos}"
SCRIPT_PATH="${0}"
SRC_DIR="${SCRIPT_PATH%/*}"
if [ "${SRC_DIR}" = "${SCRIPT_PATH}" ]; then
    SRC_DIR="."
fi
ZIG_BIN="${ZIG_BIN:-${TX_PREFIX:-/usr/local}/files/usr/bin/zig}"
VERSION_TAG="${VERSION_TAG:-v8.7.0}"

cleanup_on_exit() {
    local rc=$?
    if [ "${rc}" -ne 0 ]; then
        printf '[build_portable] ERROR: exited with code %d\n' "${rc}" >&2
    fi
}
trap cleanup_on_exit EXIT

mkdir -p "${OUT_DIR}"
if [ ! -x "${ZIG_BIN}" ]; then
    printf '[build_portable] ERROR: zig binary not found at %s\n' "${ZIG_BIN}" >&2
    exit 2
fi

COMMON_FLAGS="-std=c11 -O2 -fsanitize=undefined -fsanitize-trap=undefined -Wall -Wextra -Werror -s"

printf '[build_portable] Compiling Windows x86_64 PE32+ static executable...\n'
"${ZIG_BIN}" cc -target x86_64-windows-gnu ${COMMON_FLAGS} -static \
    "${SRC_DIR}/tianxia_portable.c" \
    -o "${OUT_DIR}/tianxia-${VERSION_TAG}-windows-x86_64.exe"
if [ $? -ne 0 ]; then
    printf '[build_portable] ERROR: Windows x86_64 build failed\n' >&2
    exit 3
fi

printf '[build_portable] Compiling Linux aarch64 static musl ELF executable...\n'
"${ZIG_BIN}" cc -target aarch64-linux-musl ${COMMON_FLAGS} -static \
    "${SRC_DIR}/tianxia_portable.c" \
    -o "${OUT_DIR}/tianxia-${VERSION_TAG}-linux-aarch64"
if [ $? -ne 0 ]; then
    printf '[build_portable] ERROR: Linux aarch64 musl build failed\n' >&2
    exit 4
fi
chmod 0755 "${OUT_DIR}/tianxia-${VERSION_TAG}-linux-aarch64"

printf '[build_portable] Compiling Linux x86_64 static musl ELF executable...\n'
"${ZIG_BIN}" cc -target x86_64-linux-musl ${COMMON_FLAGS} -static \
    "${SRC_DIR}/tianxia_portable.c" \
    -o "${OUT_DIR}/tianxia-${VERSION_TAG}-linux-x86_64"
if [ $? -ne 0 ]; then
    printf '[build_portable] ERROR: Linux x86_64 musl build failed\n' >&2
    exit 5
fi
chmod 0755 "${OUT_DIR}/tianxia-${VERSION_TAG}-linux-x86_64"

printf '[build_portable] Successfully built static portable binaries in %s\n' "${OUT_DIR}"
exit 0
