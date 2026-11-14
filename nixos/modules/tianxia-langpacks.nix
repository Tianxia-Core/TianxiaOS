# ffp: TX-TIANXIA-LANGPACKS declarative nix
{ config, pkgs, lib, ... }:
# ==========================================================================
# DSS-14 POLYGLOT LANGUAGE PACKS — all for the x86_64 HUB (Alpha/Latitude).
# Never install aarch64 packs here; the Pixel edge node stays lean.
# Packages: OCaml, Go, Julia, Nim, F#/.NET, Kotlin, Rust(+lld), C, Zig (base),
# Python+pip, uv. Mojo is NOT in nixpkgs (x86_64-only wheel from PyPI) — it is
# installed into an FHS-free venv with nix-ld providing the dynamic loader.
# ==========================================================================
{
  environment.systemPackages = with pkgs; [
    # L1 fetchable -> now present
    ocaml opam
    go
    julia
    nim
    dotnet-sdk          # F# lives inside the .NET SDK
    kotlin jdk21
    # Rust toolchain fixed properly (rustup shim lacked cc/lld)
    rustc cargo lld
    gcc clang gdb
    # Python / uv (uv can fetch a standalone CPython for the Mojo wheel)
    uv (python3.withPackages (ps: with ps; [ pycryptodome requests ]))
    # FFP build tooling discovered by optilang/optiframe audit
    typescript pandoc nodejs
    # convenience wrappers for the pip-installed Mojo compiler
    (writeShellScriptBin "mojo" ''
      exec /var/lib/tianxia/venvs/mojo/bin/mojo "$@"
    '')
  ];

  # manylinux wheels (Mojo) need the standard loader path
  programs.nix-ld.enable = true;
  programs.nix-ld.libraries = with pkgs; [
    stdenv.cc.cc.lib zlib zlib-ng openssl curl libxml2 glib ncurses libffi
  ];
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
