# ffp: TX-TIANXIA-WEBHOOK declarative nix
{ config, pkgs, ... }:

{
  systemd.services.tianxia-webhook-rebuilder = {
    description = "Tianxia Forgejo Automated CI/CD Webhook Rebuilder";
    after = [ "network.target"  ];
    wantedBy = [ "multi-user.target" ];

    path = with pkgs; [
      libnotify
      sudo
      bash
      coreutils
      git
      nix
      nixos-rebuild
      python3
      systemd
      iproute2
    ];

    serviceConfig = {
      Type = "simple";
      User = "root";
      Group = "root";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_webhook_rebuild.py";
      Restart = "always";
      RestartSec = "5s";
      StandardOutput = "journal";
      StandardError = "journal";
      MemoryMax = "256M";
      LimitNOFILE = 65535;
    };
  };

  # Open webhook listener port on local mesh
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
