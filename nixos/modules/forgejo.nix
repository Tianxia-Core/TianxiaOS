# ffp: TX-FORGEJO declarative nix
{ config, pkgs, lib, ... }:
{
  services.forgejo = {
    enable = true;
    package = pkgs.forgejo;
    stateDir = "/var/lib/forgejo";
    
    database = {
      type = "sqlite3";
      path = "/var/lib/forgejo/data/forgejo.db";
    };

    settings = {
      DEFAULT = {
        APP_NAME = "Tianxia Sovereign Forge";
        RUN_MODE = "prod";
      };

      server = {
        HTTP_ADDR = "0.0.0.0";
        HTTP_PORT = 3000;
        ROOT_URL = "http://${TX_HUB_HOST:-127.0.0.1}:3000/";
        DOMAIN = "latitude-tianxia.tail7a45a7.ts.net";
        
        START_SSH_SERVER = true;
        SSH_LISTEN_HOST = "0.0.0.0";
        SSH_PORT = 22222;
        SSH_DOMAIN = "${TX_HUB_HOST:-127.0.0.1}";
        
        PROTOCOL = "http";
        DISABLE_ROUTER_LOG = true;
      };

      service = {
        DISABLE_REGISTRATION = true;
        ALLOW_ONLY_EXTERNAL_REGISTRATION = false;
        ENABLE_CAPTCHA = false;
        REQUIRE_SIGNIN_VIEW = false;
      };

      repository = {
        ROOT = "/var/lib/forgejo/repositories";
        DEFAULT_BRANCH = "main";
        DISABLE_HTTP_GIT = false;
      };

      "repository.upload" = {
        FILE_MAX_SIZE = 4096;
      };

      security = {
        INSTALL_LOCK = true;
      };

      log = {
        MODE = "console";
        LEVEL = "Warn";
      };
    };

    secrets = {
      security = {
        SECRET_KEY = "/var/lib/tianxia/secrets/forgejo_secret.key";
      };
    };
  };

  users.users.forgejo.extraGroups = [ "wheel" ];
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
