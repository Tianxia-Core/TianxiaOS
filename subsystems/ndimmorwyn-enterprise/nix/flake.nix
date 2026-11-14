# ffp: FFP-NIX-001 enterprise-flake-definition declarative
{
  description = "TianxiaOS & Ndimmôrwyn: Enterprise Production-Grade Architecture Flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        packages.default = pkgs.rustPlatform.buildRustPackage {
          pname = "tianxiaos_ndimmorwyn_enterprise";
          version = "8.0.0";
          src = ../.;
          cargoLock = {
            lockFile = ../Cargo.lock;
          };

          nativeBuildInputs = [ pkgs.pkg-config ];
          buildInputs = [ pkgs.openssl pkgs.blake3 ];

          meta = with pkgs.lib; {
            description = "TianxiaOS & Ndimmôrwyn: Enterprise Production-Grade Sovereign Suite";
            homepage = "https://github.com/tianxiaos/ndimmorwyn";
            license = licenses.mit;
            maintainers = [ "tianxia-core" ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            rustc
            cargo
            python311
            blake3
            pkg-config
            openssl
          ];
        };
      }
    );
}
