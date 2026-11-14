# ffp: TX-TIANXIA-GRAFANA-DASHBOARDS declarative nix
{ config, pkgs, lib, ... }:
let
  dasavidyayanaDashboard = {
    dashboard = {
      id = null;
      title = "Tianxia Dasavidyayana 14-Core Sovereign Matrix";
      tags = [ "tianxia" "autarchi" "neo-noir" ];
      timezone = "browser";
      schemaVersion = 38;
      version = 1;
      refresh = "2s";
      panels = [
        {
          id = 1;
          title = "Core Execution Roundtrip Latency (ms)";
          type = "timeseries";
          gridPos = { h = 8; w = 12; x = 0; y = 0; };
          targets = [
            {
              datasource = { type = "prometheus"; uid = "prometheus"; };
              expr = "tianxia_core_latency_ms";
              legendFormat = "{{core}}";
            }
          ];
        }
        {
          id = 2;
          title = "14-Core Binary Availability State";
          type = "stat";
          gridPos = { h = 8; w = 12; x = 12; y = 0; };
          targets = [
            {
              datasource = { type = "prometheus"; uid = "prometheus"; };
              expr = "sum(tianxia_core_status)";
            }
          ];
        }
      ];
    };
  };
in
{
  services.grafana.provision.dashboards.settings.providers = [
    {
      name = "Tianxia Sovereign Dashboards";
      options.path = pkgs.runCommand "tianxia-dashboards" {} ''
        mkdir -p $out
        cat > $out/dasavidyayana.json << 'JSON_EOF'
        ${builtins.toJSON dasavidyayanaDashboard.dashboard}
        JSON_EOF
      '';
    }
  ];
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
