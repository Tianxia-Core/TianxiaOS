# ffp: FFP-MURUA-FLAKE nix-flake declarative
{
  description = "TianxiaOS Murua Universal Tracer & Sovereign Actuation Suite (v8.4-OMEGA)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.default = pkgs.rustPlatform.buildRustPackage {
          pname = "murua_architecture_enhancement";
          version = "8.4.0";
          src = ./.;
          cargoLock = {
            lockFile = ./Cargo.lock;
          };
          nativeBuildInputs = [ pkgs.pkg-config ];
          buildInputs = [ pkgs.openssl ];
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            rustc
            cargo
            gcc
            zig
            go
            nim
            ocaml
            python3
            sqlite
          ];
        };
      }
    ) // {
      nixosModules.murua = import ./nix/murua-module.nix;
    };
}
