#!/usr/bin/env bash
# ffp: FFP-TX-GJS-RUNNER frontend bash
# SLECO-SO++ O(1)-Cached GJS + GTK4 + Libadwaita Module Launcher for NixOS latitude-tianxia
set +e
set +u

if [ $# -lt 1 ]; then
    printf '[tx-gjs-run] ERROR: missing target .js module path\n' >&2
    exit 2
fi

MODULE_JS="$1"
shift

CACHE_FILE="/dev/shm/tx_gjs_runtime_env.sh"

resolve_gjs_env() {
    local gjs_bin=""
    gjs_bin="$(command -v gjs 2>/dev/null || true)"
    if [ -z "${gjs_bin}" ]; then
        for cand in /nix/store/*-gjs-1*/bin/gjs; do
            if [ -x "${cand}" ]; then
                gjs_bin="${cand}"
                break
            fi
        done
    fi
    if [ -z "${gjs_bin}" ]; then
        printf '[tx-gjs-run] ERROR: gjs binary not found in PATH or /nix/store\n' >&2
        return 1
    fi

    local typelibs="/run/current-system/sw/lib/girepository-1.0"
    local d=""
    for d in \
        /nix/store/*-gtk4-4*/lib/girepository-1.0 \
        /nix/store/*-libadwaita-1*/lib/girepository-1.0 \
        /nix/store/*-glib-2*/lib/girepository-1.0 \
        /nix/store/*-gobject-introspection-*/lib/girepository-1.0 \
        /nix/store/*-pango-1*/lib/girepository-1.0 \
        /nix/store/*-gdk-pixbuf-2*/lib/girepository-1.0 \
        /nix/store/*-graphene-1*/lib/girepository-1.0 \
        /nix/store/*-harfbuzz-*/lib/girepository-1.0 \
        /nix/store/*-cairo-*/lib/girepository-1.0 \
        /nix/store/*-fribidi-*/lib/girepository-1.0 \
        /nix/store/*-at-spi2-core-*/lib/girepository-1.0; do
        if [ -d "${d}" ]; then
            typelibs="${typelibs}:${d}"
        fi
    done

    local tmp_cache="${CACHE_FILE}.$$"
    printf 'GJS_RESOLVED_BIN="%s"\n' "${gjs_bin}" > "${tmp_cache}"
    printf 'GI_RESOLVED_PATH="%s"\n' "${typelibs}" >> "${tmp_cache}"
    mv -f "${tmp_cache}" "${CACHE_FILE}" 2>/dev/null || rm -f "${tmp_cache}"
    GJS_RESOLVED_BIN="${gjs_bin}"
    GI_RESOLVED_PATH="${typelibs}"
    return 0
}

GJS_RESOLVED_BIN=""
GI_RESOLVED_PATH=""

if [ -r "${CACHE_FILE}" ]; then
    # shellcheck disable=SC1090
    . "${CACHE_FILE}"
fi

if [ -z "${GJS_RESOLVED_BIN}" ] || [ ! -x "${GJS_RESOLVED_BIN}" ]; then
    resolve_gjs_env
    if [ $? -ne 0 ]; then
        exit 3
    fi
fi

if [ -n "${GI_TYPELIB_PATH:-}" ]; then
    export GI_TYPELIB_PATH="${GI_RESOLVED_PATH}:${GI_TYPELIB_PATH}"
else
    export GI_TYPELIB_PATH="${GI_RESOLVED_PATH}"
fi
export PATH="/usr/local/bin:/var/lib/tianxia/bin:/run/current-system/sw/bin:${PATH:-/bin}"

exec "${GJS_RESOLVED_BIN}" -m "${MODULE_JS}" "$@"
