# ffp: FFP-NIX-001 polyglot-kenning-flake nix
# TianxiaOS Core 11 (Nimbus-Flake) - Kamalā Resource & MIF Cap Gate
# Declarative Flake for TianxiaOS Polyglot Kenning & 14-Core Nimbus² DAS

{
  description = "TianxiaOS Polyglot Kenning, Oracular Engine & 14-Core DAS v3.0.0";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "tianxiaos-polyglot-kenning";
          version = "8.5.0";

          src = ./..;

          nativeBuildInputs = [
            pkgs.cargo
            pkgs.rustc
            pkgs.zig
            pkgs.gcc
            pkgs.pkg-config
          ];

          buildPhase = ''
            cargo build --release
          '';

          installPhase = ''
            mkdir -p $out/bin $out/share/tianxia
            cp target/release/tx_* $out/bin/
            cp -r config $out/share/tianxia/
          '';

          meta = with pkgs.lib; {
            description = "TianxiaOS Polyglot Kenning Suite";
            license = licenses.mit;
            platforms = platforms.linux;
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            rustc
            cargo
            zig
            go
            nim
            ocaml
            julia
            python3
            nodejs
            sqlite
          ];
        };
      }
    );
}
