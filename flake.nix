# ffp: FFP-NIX-FLAKE declarative nix
{
  description = "TianxiaOS v8.7.0 Crownforge — 2816-Node Heterogeneous Omni-Lattice & Sovereign AI Operating System";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

      mkTianxiaSuite = pkgs:
        pkgs.stdenv.mkDerivation {
          pname = "tianxiaos";
          version = "8.7.0";
          src = ./crates/tianxia-suite;
          nativeBuildInputs = [ pkgs.rustc ];
          buildPhase = ''
            runHook preBuild
            rustc --edition=2021 -C opt-level=3 -C panic=abort -C strip=symbols \
              src/main.rs -o tianxia
            runHook postBuild
          '';
          installPhase = ''
            runHook preInstall
            mkdir -p $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps
            install -m 0755 tianxia $out/bin/tianxia
            for tui_alias in tx-sovereign-tui tx-scour-tui tx-miner-tui tx-ledger-tui tx-dss14-tui tx-etamanga-tui tx-fortress-tui tx-models-tui tx-tracer-tui; do
              ln -sf tianxia "$out/bin/$tui_alias"
            done
            cp ${./platforms/rasa-x-machina/ui/icon.svg} $out/share/icons/hicolor/scalable/apps/tianxia.svg
            cat > $out/share/applications/tianxia.desktop <<EOF
            [Desktop Entry]
            Version=1.5
            Type=Application
            Name=TianxiaOS Sovereign Suite
            Comment=TianxiaOS Sovereign CLI & 9-App Interactive Terminal Cockpit
            Exec=$out/bin/tianxia tui
            Icon=tianxia
            Terminal=true
            Categories=System;Security;ConsoleOnly;
            EOF
            runHook postInstall
          '';
          meta = with pkgs.lib; {
            description = "TianxiaOS v8.7.0 Sovereign CLI & 9-App Fullscreen TUI Suite";
            homepage = "https://rasaxmachina.com";
            license = licenses.bsl11;
            platforms = supportedSystems;
            mainProgram = "tianxia";
          };
        };
    in {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          tianxiaPkg = mkTianxiaSuite pkgs;
        in
        {
          default = tianxiaPkg;
          tianxia = tianxiaPkg;
        }
        // nixpkgs.lib.optionalAttrs (system == "x86_64-linux") {
          tx-manas-cpu = pkgs.stdenv.mkDerivation {
            pname = "tx-manas-cpu";
            version = "8.7.0";
            src = ./subsystems/ephemeral-cockpit/src/tx-cuda-manas;
            buildPhase = ''
              cc -O3 -mavx2 -mfma -shared -fPIC tx_manas_cpu.c -o libtx_manas_cpu.so -lm
            '';
            installPhase = ''
              mkdir -p $out/lib
              install -m 0755 libtx_manas_cpu.so $out/lib/libtx_manas_cpu.so
            '';
          };
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/tianxia";
        };
        tianxia = {
          type = "app";
          program = "${self.packages.${system}.tianxia}/bin/tianxia";
        };
      });

      overlays.default = final: prev: {
        tianxia = mkTianxiaSuite final;
        tianxiaos = mkTianxiaSuite final;
      };

      nixosModules = rec {
        default = tianxiaos;
        tianxiaos = { config, lib, pkgs, ... }:
          let
            cfg = config.services.tianxiaos;
          in {
            options.services.tianxiaos = {
              enable = lib.mkEnableOption "TianxiaOS Sovereign CLI, TUI & Watchdog Suite";
              package = lib.mkOption {
                type = lib.types.package;
                default = self.packages.${pkgs.stdenv.hostPlatform.system}.tianxia;
                description = "TianxiaOS sovereign CLI/TUI package.";
              };
            };

            config = lib.mkIf cfg.enable {
              environment.systemPackages = [ cfg.package ];
              systemd.services.tianxiaos-seal-verify = {
                description = "TianxiaOS Build Law Cryptographic Seal Verification";
                wantedBy = [ "multi-user.target" ];
                serviceConfig = {
                  Type = "oneshot";
                  ExecStart = "${cfg.package}/bin/tianxia verify-law --json";
                  NoNewPrivileges = true;
                  ProtectSystem = "strict";
                  MemoryMax = "256M";
                  TasksMax = 32;
                };
              };
            };
          };
      };

      nixosConfigurations = {
        latitude-tianxia = nixpkgs.lib.nixosSystem {
          system = "x86_64-linux";
          modules = [
            ./nixos/configuration.nix
          ];
        };
      };
    };
}
