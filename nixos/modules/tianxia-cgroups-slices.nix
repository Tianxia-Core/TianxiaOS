# ffp: TX-TIANXIA-CGROUPS-SLICES declarative nix
# Hierarchical cgroup v2 resource partitioning for TianxiaOS Swarm substrate.
# Enforces real-time responsiveness for MANAS and Pointer Bridge (60fps guaranteed HUD)
# while isolating autonomous agent execution and background scour memory consumption.
{ config, lib, pkgs, ... }:

{
  # Ensure cgroup v2 unified hierarchy is active
  boot.kernelParams = [
    "systemd.unified_cgroup_hierarchy=1"
    "cgroup_no_v1=all"
  ];

  systemd.slices = {
    # Tier 0: Critical Path (MANAS System-1, Pointer Bridge, Workspace Bus)
    "tianxia-critical" = {
      description = "Tianxia Real-Time Critical Substrate (MANAS, Pointer, Bus)";
      sliceConfig = {
        CPUWeight = 10000;
        IOWeight = 10000;
        MemoryMin = "1G";
        MemoryLow = "2G";
        TasksMax = 4096;
      };
    };

    # Tier 1: Interactive Cockpit & Compositor (Hyprland, WayVNC, GUI Bridge)
    "tianxia-gui" = {
      description = "Tianxia Interactive Cockpit & Wayland Compositor";
      sliceConfig = {
        CPUWeight = 8000;
        IOWeight = 8000;
        MemoryMin = "1G";
        MemoryLow = "2G";
        TasksMax = 8192;
      };
    };

    # Tier 2: Autonomous Swarm Agents & Inference Engines
    "tianxia-agents" = {
      description = "Tianxia Autonomous Agent Execution & Local ML Inference";
      sliceConfig = {
        CPUWeight = 2000;
        IOWeight = 2000;
        MemoryHigh = "12G";
        MemoryMax = "14G";
        TasksMax = 16384;
      };
    };

    # Tier 3: Background Scour Pulses & Asynchronous Sync
    "tianxia-scour" = {
      description = "Tianxia Background Scour Pulses, Harvesters & Attestation";
      sliceConfig = {
        CPUWeight = 100;
        IOWeight = 100;
        MemoryHigh = "2G";
        MemoryMax = "4G";
        TasksMax = 2048;
      };
    };
  };
}
