# ffp: FFP-NIX-001 crownforge-flake declarative
{
  description = "TianxiaOS V8.6.0 Supplementary Codex: Omphalos Reasonwashing, Noetic Kenning & Maha Madpie";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            rustc
            cargo
            gcc
            clang
            zig
            go
            nim
            ocaml
            nodejs
            julia-bin
            python3
            sqlite
            blake3
          ];
        };

        packages.default = pkgs.rustPlatform.buildRustPackage {
          pname = "tianxiaos_crownforge_codex";
          version = "8.6.0";
          src = ./.;
          cargoLock = {
            lockFile = ./Cargo.lock;
          };
        };
      }
    );
}
