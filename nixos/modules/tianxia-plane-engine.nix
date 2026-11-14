# ffp: TX-TIANXIA-PLANE-ENGINE declarative nix
{ config, pkgs, lib, ... }:
{
  # ==========================================================================
  # DASAVIDYAYANA COMPUTE-ENGINE PLANE CONFIG
  # 14 archetypes mapped to 5 resource classes on 12 cores. Not 14 literal
  # cores (that would oversubscribe). Planes are pinned by class so kernel /
  # I/O / state work never contends with heavy inference.
  # ==========================================================================

  # 1. Kill the powersave governor; compute node runs at performance.
  powerManagement.cpuFreqGovernor = "performance";

  # Intel thermal management: userspace governor over coretemp readings.
  services.thermald.enable = true;

  # 2. Reserve low cores for kernel + I/O planes (Tara/Bhairavi), keep the
  #    inference planes (cores 2-7) free for the model forest.
  #    CPUAffinity is set per-service below.

  # Core 02 Tara (WireGuard) + NATS: I/O plane, cores 8-11
  
  systemd.services.nats.serviceConfig = {
    CPUAffinity = "8-11";
  };

  # Core 08 Bagalamukhi (state-lock) + Core 14 Paramasiva (UDS fastpath):
  # state/fast plane, cores 10-11, high weight for sub-ms routing.
  systemd.services.tianxia-uds-gateway.serviceConfig = {
    CPUAffinity = "10-11";
    CPUWeight = 300;
  };

  # Core 03 Tripura (Forgejo source control): I/O plane, cores 8-9, low weight.
  systemd.services.forgejo.serviceConfig = {
    CPUAffinity = "8-9";
    CPUWeight = 50;
  };

  # Inference plane servers (Kali/TimesFM, Matangi/Kokoro) -> cores 2-3
  systemd.services.tianxia-timesfm.serviceConfig = {
    CPUAffinity = "2-3";
  };
  systemd.services.tianxia-kokoro.serviceConfig = {
    CPUAffinity = "2-3";
  };

  # 3. Cap model-server threads. Six resident servers defaulting to nproc=12
  #    each would spawn ~72 threads on 12 cores (6x oversubscription). The
  #    lights pin to cores 2-5 with 4 threads; heavies stay tier-gated.
  #    (Threads passed inline on the light units; see model-forest override.)
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
