# ffp: TX-TIANXIA-FORGEJO-RUNNER declarative nix
{ config, pkgs, lib, ... }:
{
  services.gitea-actions-runner = {
    package = pkgs.forgejo-runner;
    instances."latitude-tianxia-runner" = {
      enable = true;
      name = "latitude-coordinator-runner";
      url = "http://git.rasaxmachina.com:3000";
      tokenFile = "/etc/tianxia/secrets/runner-token.txt";
      labels = [
        "native:host"
        "nixos:host"
      ];
      settings = {
        runner = {
          capacity = 2;
          timeout = "1h";
          insecure = true;
        };
      };
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
