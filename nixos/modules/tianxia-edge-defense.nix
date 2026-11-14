# ffp: TX-TIANXIA-EDGE-DEFENSE declarative nix
{ pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    python3
    nftables
    rsync
  ];

  networking.nftables.enable = true;
  networking.nftables.tables."xps-sentinel" = {
    family = "inet";
    content = ''
      set mesh_quarantine {
        type ipv4_addr
        flags timeout
      }
      chain mesh_input {
        type filter hook input priority filter - 10; policy accept;
        ct state established,related accept
        iifname "lo" accept
        ip saddr @mesh_quarantine tcp dport { 22, 8022, 8089, 9095 } counter drop
      }
    '';
  };

  # 1. Telemetry Drop Forwarder Service
  systemd.services.tianxia-drop-forwarder = {
    description = "Tianxia XPS 13 Drop Telemetry Forwarder";
    after = [ "network.target"  ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ python3 nftables coreutils ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_forward_drops.py";
      Restart = "always";
      RestartSec = "3s";
      MemoryMax = "32M";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # 2. Blacklist Signature Enforcement One-shot Service
  systemd.services.tianxia-signature-enforce = {
    description = "Tianxia Edge Signature Enforcer";
    path = with pkgs; [ python3 nftables coreutils ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_enforce_signatures.py";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # 3. Path Watcher for Replicated Signature JSON
  systemd.paths.tianxia-signature-enforce = {
    description = "Watch Signature Blacklist Updates from Core";
    wantedBy = [ "multi-user.target" ];
    pathConfig = {
      PathModified = "/var/lib/tianxia/security/signature_blacklist.json";
      Unit = "tianxia-signature-enforce.service";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
