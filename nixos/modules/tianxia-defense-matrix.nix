# ffp: TX-TIANXIA-DEFENSE-MATRIX declarative nix
{ pkgs, ... }:

let
  tianxia-bin-suite = pkgs.runCommandLocal "tianxia-bin-suite" {} ''
    mkdir -p $out/bin
    for cmd in tx_monitor tx_quarantine tx_alert_clean signature_blacklist tx_study_trap tx_alert_sentinel tx_telemetry_receiver replicate_signatures; do
      cat << WRAPPER > $out/bin/$cmd
#!${pkgs.bash}/bin/bash
name="''${cmd%.sh}"; name="''${name#tx_}"
if [[ -x "/var/lib/tianxia/bin/$cmd" ]]; then
  exec "/var/lib/tianxia/bin/$cmd" "\$@"
elif [[ -x "/var/lib/tianxia/bin/$cmd.py" ]]; then
  exec "${pkgs.python3}/bin/python3" "/var/lib/tianxia/bin/$cmd.py" "\$@"
elif [[ -x "/var/lib/tianxia/src/rust/txsuite/target/release/$name" ]]; then
  exec "/var/lib/tianxia/src/rust/txsuite/target/release/$name" "\$@"
fi
WRAPPER
      chmod +x $out/bin/$cmd
    done
  '';
in
{
  environment.systemPackages = with pkgs; [
    tianxia-bin-suite
    python3
    sqlite
    nftables
    rsync
    openssh
    iputils
    jq
    tmux
  ];

  services.openssh.extraConfig = ''
    ClientAliveInterval 30
    ClientAliveCountMax 5
  '';

  networking.nftables.enable = true;
  networking.nftables.tables."tianxia-sentinel" = {
    family = "inet";
    content = ''
      set study_quarantine {
        type ipv4_addr
        flags timeout
      }
      chain input_trap {
        type filter hook input priority filter - 10; policy accept;
        ct state established,related accept
        iifname "lo" accept
        ip saddr @study_quarantine tcp dport { 22, 80, 443, 8089, 9095 } counter drop
      }
    '';
  };

  networking.firewall.allowedTCPPorts = [ 22 8089 2222 8023 ];

  systemd.services.tianxia-study-trap = {
    description = "Tianxia Polymorphic Study Trap Honeypot Daemon";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ python3 sqlite nftables coreutils ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_study_trap.py";
      Restart = "always";
      MemoryMax = "128M";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-telemetry-receiver = {
    description = "Tianxia WireGuard Mesh Telemetry Ingest Receiver";
    after = [ "network.target"  ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ python3 sqlite coreutils ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_telemetry_receiver.py";
      Restart = "always";
      MemoryMax = "64M";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-alert-sentinel = {
    description = "Tianxia Security Burst Alert Sentinel";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ python3 sqlite coreutils ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_alert_sentinel.py";
      Restart = "always";
      MemoryMax = "64M";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-signature-sync = {
    description = "Tianxia Signature Blacklist Recompile & Mesh Distribution";
    after = [ "network.target" ];
    path = with pkgs; [ bash python3 sqlite rsync openssh iputils coreutils ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = pkgs.writeShellScript "tx-sig-sync" ''
        /var/lib/tianxia/src/rust/txsuite/target/release/signature_blacklist
        /var/lib/tianxia/src/rust/txsuite/target/release/replicate_signatures
      '';
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
  systemd.timers.tianxia-signature-sync = {
    description = "30-min Timer for Tianxia Signature Synthesis & Replication";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "2min"; OnUnitActiveSec = "30min"; Persistent = true; };
  };

  systemd.services.tianxia-telemetry-prune = {
    description = "Tianxia Telemetry Daily 7-Day Purge";
    path = with pkgs; [ python3 sqlite coreutils ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_alert_clean purge 168";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
  systemd.timers.tianxia-telemetry-prune = {
    description = "Daily Timer for Tianxia Telemetry Retention Purge";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnCalendar = "*-*-* 03:30:00 UTC"; Persistent = true; };
  };

  environment.shellAliases = {
    txm = "tx_monitor";
    tx-alerts = "tx_alert_clean list";
    tx-ack = "tx_alert_clean ack-all";
    tx-sig = "/var/lib/tianxia/src/rust/txsuite/target/release/signature_blacklist";
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
