# ffp: TX-TIANXIA-SPOKE declarative nix
{ config, pkgs, lib, ... }:

let
  spokeIp = if config.networking.hostName == "xps13-tianxia" then "10.0.99.1/16" else "10.0.99.2/16";
in
{
  boot.kernel.sysctl = {
    "net.ipv4.ip_forward" = lib.mkForce 1;
    "net.ipv4.conf.all.forwarding" = lib.mkForce 1;
    "net.ipv6.conf.all.forwarding" = lib.mkForce 1;
    "net.ipv4.conf.all.rp_filter" = lib.mkForce 2;
    "net.ipv4.conf.default.rp_filter" = lib.mkForce 2;
    "net.core.default_qdisc" = "fq";
    "net.ipv4.tcp_congestion_control" = "bbr";
  };

  networking = {
    firewall = {
      enable = lib.mkForce true;
      checkReversePath = lib.mkForce "loose";
      allowedTCPPorts = [ 22 5900 ];  # LAN: SSH + wayvnc (all mesh services via trusted interfaces)
      allowedUDPPorts = [ 51820 ];
      trustedInterfaces = [ "tailscale0" ];
    };

    
  };

  systemd.services.tianxia-http-telemetry = {
    enable = lib.mkForce false;
    wantedBy = lib.mkForce [ ];
    serviceConfig = {
      ExecStart = lib.mkForce "${pkgs.coreutils}/bin/true";
      Restart = lib.mkForce "no";
    };
  };

  systemd.services.tianxia-telemetry-push = {
    description = "Tianxia Spoke Telemetry Push Pipeline";
    path = with pkgs; [ coreutils procps openssh iproute2 wireguard-tools jq gawk gnused ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = pkgs.writeShellScript "tx-telemetry-push" ''
        set -uo pipefail
        mkdir -p /var/spool/tianxia /var/log/tianxia

        RELAY_IP="10.0.99.254"
        NODE_NAME="$(hostname -s 2>/dev/null || echo latitude-coordinator)"
        TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
        EPOCH="$(date +%s)"
        LOAD="$(cut -d " " -f 1-3 /proc/loadavg 2>/dev/null || echo "0.00 0.00 0.00")"
        MEM_TOTAL="$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")"
        MEM_AVAIL="$(grep MemAvailable /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")"
        WG_TX_RX="$(wg show wg0 transfer 2>/dev/null | tr '\t' ' ' | tr '\n' ' | ' || echo "inactive")"

        PAYLOAD=$(printf '{"node":"%s","timestamp":"%s","epoch":%s,"loadavg":"%s","memory_total_kb":%s,"memory_available_kb":%s,"wg_transfer":"%s"}' \
          "$NODE_NAME" "$TIMESTAMP" "$EPOCH" "$LOAD" "$MEM_TOTAL" "$MEM_AVAIL" "$WG_TX_RX")

        SPOOL_FILE="/var/spool/tianxia/last_''${NODE_NAME}_metrics.json"
        echo "$PAYLOAD" > "$SPOOL_FILE"

        ssh -i /root/.ssh/id_ed25519 \
            -o BatchMode=yes \
            -o ConnectTimeout=5 \
            -o StrictHostKeyChecking=accept-new \
            root@"$RELAY_IP" \
            "mkdir -p /var/log/tianxia && cat > /var/log/tianxia/''${NODE_NAME}_telemetry.json" < "$SPOOL_FILE" 2>/dev/null || true
      '';
    };
  };

  systemd.timers.tianxia-telemetry-push = {
    description = "Tianxia Telemetry Periodic Push Timer";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "15s";
      OnUnitActiveSec = "60s";
      Persistent = true;
    };
  };
  systemd.services.tianxia-relay-refresh = {
    description = "Tianxia relay endpoint refresh (hub-side DDNS)";
    after = [ ];
    wants = [ ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = "/var/lib/tianxia/bin/tx_relay_refresh.sh --once";
    };
  };
  systemd.timers.tianxia-relay-refresh = {
    description = "Tianxia relay refresh timer (10min)";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      Unit = "tianxia-relay-refresh.service";
      OnBootSec = "2min";
      OnUnitActiveSec = "10min";
      Persistent = true;
    };
  };

  # Mesh DNS resolver: Quad9 over DoT for all mesh clients (phone DNS=10.0.99.2)
  services.unbound = {
    enable = true;
    settings = {
      server = {
        # the WireGuard mesh (10.0.99.2) is DEAD -- the tailnet replaced it,
        # and a phantom bind makes unbound LOOK like it serves the mesh while
        # nothing can reach it. Serve loopback + the tailnet range.
        interface = [ "127.0.0.1" ];
        "access-control" = [ "100.64.0.0/10 allow" "127.0.0.0/8 allow" ];
        "tls-cert-bundle" = "/etc/ssl/certs/ca-certificates.crt";
        "hide-identity" = true;
        "hide-version" = true;
        "qname-minimisation" = true;
        prefetch = true;
        verbosity = 1;
      };
      "remote-control" = { "control-enable" = false; };
      "forward-zone" = [
        {
          name = ".";
          "forward-tls-upstream" = true;
          "forward-addr" = [ "9.9.9.9@853#dns.quad9.net" "149.112.112.112@853#dns.quad9.net" ];
        }
      ];
    };
  };

  # Daily post-snapshot replication: mesh tiers + offsite relay (keep latest)
  systemd.services.tianxia-offsite-replicate = {
    description = "Tianxia backup replication (mesh + offsite relay)";
    after = [ "network-online.target" "tianxia-snapshot-backup.service" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = "/var/lib/tianxia/bin/tx_replicate_backups.sh";
      TimeoutStartSec = "5400";
    };
  };
  systemd.timers.tianxia-offsite-replicate = {
    description = "Daily backup replication at 05:30 (after 04:02 snapshot)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnCalendar = "05:30"; Persistent = true; };
  };

  # Honeypot telemetry pull (cowrie decoy sessions -> learning loop)
  systemd.services.tianxia-honeypot-pull = {
    description = "Pull + summarize cowrie honeypot telemetry";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/var/lib/tianxia/bin/tx_honeypot_pull.sh"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tianxia-honeypot-pull = {
    description = "Honeypot telemetry pull (30min)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "5min"; OnUnitActiveSec = "30min"; Persistent = true; };
  };

  # IOC watch: lost-account indicators in breach/honeypot logs
  systemd.services.tianxia-ioc-watch = {
    description = "Scan breach/honeypot logs for lost-account IOCs";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/var/lib/tianxia/bin/tx_ioc_watch.sh"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tianxia-ioc-watch = {
    description = "IOC watch (30min)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "12min"; OnUnitActiveSec = "30min"; Persistent = true; };
  };

  # Attacker device/tool fingerprint pipeline (masked + internal)
  systemd.services.tianxia-attacker-fp = {
    description = "Fingerprint attackers (HASSH, tooling, clusters, identifiers)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/run/current-system/sw/bin/python3 /var/lib/tianxia/bin/tx_attacker_fp.py"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tianxia-attacker-fp = {
    description = "Attacker fingerprint pipeline (30min)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "20min"; OnUnitActiveSec = "30min"; Persistent = true; };
  };

  # Recovery inbox watcher (support replies for lost accounts)
  systemd.services.tianxia-recovery-inbox = {
    description = "Watch recovery inbox for support replies";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/run/current-system/sw/bin/python3 /var/lib/tianxia/bin/tx_recovery_inbox.py"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tianxia-recovery-inbox = {
    description = "Recovery inbox watcher (1h)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "25min"; OnUnitActiveSec = "1h"; Persistent = true; };
  };

  systemd.services.tx-relay-audit = {
    description = "Daily relay drift audit (listeners/services/sysctl/keys/nft)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/var/lib/tianxia/bin/tx_relay_audit.sh"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tx-relay-audit = {
    description = "Relay drift audit (daily)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "40min"; OnUnitActiveSec = "24h"; Persistent = true; };
  };
  systemd.services.tx-hetzner-abuse = {
    description = "Hetzner abuse dossier + stateful reporting";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/run/current-system/sw/bin/python3 /var/lib/tianxia/bin/tx_hetzner_abuse.py"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tx-hetzner-abuse = {
    description = "Hetzner abuse tracking (daily)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "45min"; OnUnitActiveSec = "24h"; Persistent = true; };
  };

  systemd.services.tx-vast-watch = {
    description = "Vast.ai uncensored 30B build guardian";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/var/lib/tianxia/bin/tx_vast_watch.sh"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tx-vast-watch = {
    description = "Vast.ai build guardian (5min)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "1min"; OnUnitActiveSec = "5min"; Persistent = true; };
  };

  systemd.services.tx-ram-guard = {
    description = "Stop big inference units under RAM pressure";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = { Type = "oneshot"; User = "root"; ExecStart = "/var/lib/tianxia/bin/tx_ram_guard.sh"; Environment = "PATH=/run/current-system/sw/bin:/usr/bin:/bin"; };
  };
  systemd.timers.tx-ram-guard = {
    description = "RAM guard (1min)";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "2min"; OnUnitActiveSec = "1min"; Persistent = true; };
  };

}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
