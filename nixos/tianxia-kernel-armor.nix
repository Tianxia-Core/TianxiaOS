# ffp: TX-TIANXIA-KERNEL-ARMOR declarative nix
{ config, pkgs, ... }:
{
  boot.kernel.sysctl = {
    "kernel.yama.ptrace_scope" = 2;
    "kernel.kptr_restrict" = 2;
    "kernel.dmesg_restrict" = 1;
    "kernel.unprivileged_bpf_disabled" = 1;
    "net.core.bpf_jit_harden" = 2;
    "net.core.bpf_jit_enable" = 1;
    "net.core.rmem_max" = 16777216;
    "net.core.wmem_max" = 16777216;
    "net.core.somaxconn" = 4096;
    "fs.file-max" = 2097152;
    "fs.protected_hardlinks" = 1;
    "fs.protected_symlinks" = 1;
    "fs.protected_fifos" = 2;
    "fs.protected_regular" = 2;
    "vm.dirty_background_ratio" = 5;
    "vm.dirty_ratio" = 10;
    "vm.swappiness" = 10;
    "vm.vfs_cache_pressure" = 50;
    "vm.max_map_count" = 262144;
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
