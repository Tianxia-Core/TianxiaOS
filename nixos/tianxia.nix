# ffp: TX-TIANXIA declarative nix
{ config, pkgs, ... }:

{
  boot.devShmSize = "28G";

  environment.systemPackages = with pkgs; [
    llama-cpp
    aria2
    pv
    jq
    rsync
    python3
    procps
    iproute2
    psmisc
    android-tools
    netcat-gnu
    avahi
  ];

  services.udev.extraRules = ''
    ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", TAG+="systemd", ENV{SYSTEMD_WANTS}+="tianxia-adb-hotplug.service"
    ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="2717", TAG+="systemd", ENV{SYSTEMD_WANTS}+="tianxia-adb-hotplug.service"
  '';

  systemd.services.tianxia-adb-hotplug = {
    description = "Tianxia Mobile Node ADB Hotplug Sync";
    path = with pkgs; [ bash android-tools procps coreutils gnugrep gawk ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_adb_hotplug_sync.sh";
    };
  };

  systemd.services.tianxia-adb-wifi-discovery = {
    description = "Tianxia Mobile Node Wireless ADB Auto-Discovery";
    path = with pkgs; [ bash android-tools netcat-gnu iputils procps coreutils gnugrep gawk ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_adb_wifi_discovery.sh";
    };
  };

  systemd.timers.tianxia-adb-wifi-discovery = {
    description = "Poll for Wireless ADB Mobile Nodes every 15s";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "10s";
      OnUnitActiveSec = "15s";
      AccuracySec = "1s";
    };
  };

  systemd.services.tianxia-tensor-lattice = {
    description = "Tianxia Omphalos 8912-Node Tensor Inference & Ring Substrate";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ bash llama-cpp procps iproute2 gnugrep gawk coreutils ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      LimitMEMLOCK = "infinity";
      LimitNOFILE = 65536;
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_start_tier1_backends.sh";
    };
  };

  systemd.services.tianxia-vector-sink = {
    description = "Tianxia Tier-1 SHM Vector Server";
    after = [ "network.target" "tianxia-tensor-lattice.service" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ python3 ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/services/tx_vector_server.py";
      Restart = "always";
      RestartSec = "3s";
    };
  };

  systemd.services.tianxia-mesh-gateway = {
    description = "Tianxia Cross-Node Swarm Mesh Gateway";
    after = [ "network.target" "tianxia-tensor-lattice.service" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ python3 ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/services/tx_mesh_gateway.py";
      Restart = "always";
      RestartSec = "3s";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
