# ffp: MCP-RESERVE-SVC declarative nix
# Tianxia MCP reserve (TX-MCP-RESERVE): the recovered nimbus2 unified MCP tool
# suite, materialized from the workspace-backup reserve and running as a
# durable service so it survives reboots.
#
# Endpoints: 69 routes (kai3, pari, softem, autarchi, litdiscovery, millihan,
# enhan3, secenhan, tremor/perimeter, cheri/capabilities, bao/hypervisor,
# serpent, corpus, persona, fc-dle). Bound to the mesh IP, not 0.0.0.0, so the
# reserve is reachable from mesh peers only.
#
# SecretShield installs on import and redacts all stdout/stderr/logging.
{ config, lib, pkgs, ... }:
{
  systemd.services.tx-mcp-reserve = {
    description = "Tianxia MCP reserve — unified hardened MCP tool suite (:8099)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    # systemd puts startLimit* in [Unit]; keep it out of serviceConfig so the
    # rebuild stops warning about an unknown [Service] key.
    startLimitIntervalSec = 900;
    serviceConfig = {
      Type = "simple";
      Restart = "on-failure";
      RestartSec = "30";
      StartLimitBurst = 5;
      WorkingDirectory = "/var/lib/tianxia/mcp_server";
      Environment = "PYTHONUNBUFFERED=1";
      ExecStart = "/var/lib/tianxia/bin/tx_mesh_bind.sh /var/lib/tianxia/mcp_server/venv/bin/python tianxia_mcp_server.py --host @MESH_BIND@ --port 8099 --log-level warning";
      # The venv is provisioned out-of-band (pip install fastapi uvicorn);
      # guard so a missing venv fails loudly rather than silently looping.
      ExecStartPre = "/var/lib/tianxia/mcp_server/venv/bin/python -c 'import fastapi, uvicorn'";
    };
  };
}
