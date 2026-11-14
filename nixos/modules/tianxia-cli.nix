# ffp: TX-TIANXIA-CLI declarative nix
{ pkgs, ... }:

let
  # Package that automatically creates wrappers in /run/current-system/sw/bin
  # pointing dynamically to any executable in /var/lib/tianxia/bin
  tianxia-bin-suite = pkgs.runCommandLocal "tianxia-bin-suite" {} ''
    mkdir -p $out/bin
    
    # Static fallback wrappers for core orchestration tools
    for cmd in tx_monitor tx_snapshot_backup.sh tx_replicate_backups.sh tx_forgejo_push.sh tx-cli; do
      cat << WRAPPER > $out/bin/$cmd
#!/usr/bin/env bash
if [[ -x "/var/lib/tianxia/bin/$cmd" ]]; then
  exec "/var/lib/tianxia/bin/$cmd" "\$@"
else
  echo "[-] /var/lib/tianxia/bin/$cmd not found or not executable." >&2
  exit 127
fi
WRAPPER
      chmod +x $out/bin/$cmd
    done
  '';
in
{
  environment.systemPackages = [
    tianxia-bin-suite
    pkgs.python3
    pkgs.sqlite
  ];

  # Guarantee PATH insertion in system-wide environment configurations
  environment.sessionVariables = {
    PATH = [ "/var/lib/tianxia/bin" ];
  };

  environment.extraInit = ''
    if [[ -d "/var/lib/tianxia/bin" && ":$PATH:" != *":/var/lib/tianxia/bin:"* ]]; then
        export PATH="/var/lib/tianxia/bin:$PATH"
    fi
  '';
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
