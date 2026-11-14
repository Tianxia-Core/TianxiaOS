# ffp: TX-MODEL-FOREST-SERVICES declarative nix
{ config, pkgs, ... }:
{
  systemd.services.tianxia-timesfm = {
    description = "Tianxia TimesFM Telemetry & Forecaster Daemon (:9191)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_timesfm_daemon.py";
      Restart = "always";
      RestartSec = "2s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-kokoro = {
    description = "Tianxia Kokoro Acoustic Telemetry Synthesizer (:9192)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_kokoro_daemon.py";
      Restart = "always";
      RestartSec = "2s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-uds-gateway = {
    description = "Tianxia 14-Core Dasavidyayana Orchestrator (/run/tianxia/tx_fastpath.sock)";
    after = [ "network.target" "ollama.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_dasavidya_nexus.py";
      Restart = "always";
      RestartSec = "2s";
      RuntimeDirectory = "tianxia";
      RuntimeDirectoryMode = "0770";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-minicpm = {
    description = "MiniCPM5 ATLAS ledger engine (:11490)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/minicpm5/MiniCPM5-2B-Q4_K_M.gguf -c 8192 --port 11490";
      Restart = "always";
      RestartSec = "10s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-uncensored = {
    description = "Uncensored 4B (SWAA-fusang build) (:11496)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-uncensored.off" "/var/lib/tianxia/models/uncensored/build/uncensored-4b-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/uncensored/build/uncensored-4b-Q4_K_M.gguf -c 8192 --port 11496 --parallel 2";
      Restart = "always";
      RestartSec = "10s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

      systemd.services.tianxia-uncensored-36-sft = {
    description = "Tianxia-trained Qwen3.6-35B uncensored (:11501)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-uncensored-36-sft.off" "/var/lib/tianxia/models/uncensored-36/trained/uncensored-36-sft-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/uncensored-36/trained/uncensored-36-sft-Q4_K_M.gguf -c 4096 --port 11501 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

    systemd.services.tianxia-uncensored-36-lora = {
    description = "Tianxia LoRA over uncensored 35B (:11502)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-uncensored-36-lora.off" "/var/lib/tianxia/models/uncensored-36/trained/uncensored-36-tianxia-v7-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/uncensored-36/trained/uncensored-36-tianxia-v7-Q4_K_M.gguf -c 8192 --port 11502 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-lady-naga-4b = {
    description = "Tianxia Lady Naga 4B (:11503)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-lady-naga-4b.off" "/var/lib/tianxia/models/tianxia-lady-naga-4b-noembed-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/tianxia-lady-naga-4b-noembed-Q4_K_M.gguf -c 4096 --port 11503 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-veritas-8b = {
    description = "Tianxia Veritas 8B (:11504)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-veritas-8b.off" "/var/lib/tianxia/models/tianxia-veritas-8b-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/tianxia-veritas-8b-Q4_K_M.gguf -c 4096 --port 11504 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-vishwakarma-8b = {
    description = "Tianxia Vishwakarma 8B (:11505)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-vishwakarma-8b.off" "/var/lib/tianxia/models/tianxia-vishwakarma-8b-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/tianxia-vishwakarma-8b-Q4_K_M.gguf -c 4096 --port 11505 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-naga-pasha-4b = {
    description = "Tianxia Naga-Pasha 4B (:11506)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-naga-pasha-4b.off" "/var/lib/tianxia/models/tianxia-naga-pasha-4b-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/tianxia-naga-pasha-4b-Q4_K_M.gguf -c 4096 --port 11506 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-lord-naga-30b = {
    description = "Tianxia Lord Naga 30B (:11507)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-lord-naga-30b.off" "/var/lib/tianxia/models/tianxia-lord-naga-30b-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/tianxia-lord-naga-30b-Q4_K_M.gguf -c 4096 --port 11507 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-pluginus-4b = {
    description = "Tianxia Pluginus 4B (:11508)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-pluginus-4b.off" "/var/lib/tianxia/models/tianxia-pluginus-4b-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/tianxia-pluginus-4b-Q4_K_M.gguf -c 4096 --port 11508 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-uncensored-30b = {
    description = "Uncensored 30B-A3B-Thinking fusang (:11500)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-uncensored-30b.off" "/var/lib/tianxia/models/uncensored/build/unc30b-thinking-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/uncensored/build/unc30b-thinking-Q4_K_M.gguf -c 4096 --port 11500 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-uncensored-36 = {
    description = "Uncensored Qwen3.6-35B-A3B HauhauCS (:11494)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = [ "!/var/lib/tianxia/tiers/tianxia-uncensored-36.off" "/var/lib/tianxia/models/uncensored-36/uncensored-36-35b-Q4_K_M.gguf" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/uncensored-36/uncensored-36-35b-Q4_K_M.gguf -c 4096 --port 11494 --cache-type-k q8_0 --cache-type-v q8_0";
      Restart = "always"; RestartSec = "10s"; WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal"; StandardError = "journal";
    };
  };

  systemd.services.tianxia-vibe = {
    description = "VibeThinker-3B reasoning engine (:11491)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/eval/VibeThinker-3B.Q4_K_M.gguf -c 8192 --port 11491";
      Restart = "always";
      RestartSec = "10s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-lfm = {
    description = "LFM-CyberSec triage engine (:11492)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/eval/LiquidAI_LFM2.5-2.6B__project-lfm2.5-2.6b-cybersec_1786722551.Q4_K_M.gguf -c 8192 --port 11492";
      Restart = "always";
      RestartSec = "10s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-rpc-tunnel = {
    description = "Cloudflared public RPC tunnel (etamanga)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.cloudflared}/bin/cloudflared tunnel --config /var/lib/tianxia/secrets/cloudflared-rpc.yml run";
      Restart = "always";
      RestartSec = "10s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-qwen-dl = {
    description = "Qwen3.6-27B resume download (oneshot)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/etamanga-build/qwen_dl.sh";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-qwen = {
    unitConfig.ConditionPathExists = "!/var/lib/tianxia/tiers/tianxia-qwen.off";
    description = "Qwen3.6-27B code + arbitration engine (:11493)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/etamanga-build/run_qwen.sh";
      Restart = "always";
      RestartSec = "15s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-moe = {
    description = "Qwen3.6-35B-A3B MoE code engine (:11494)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = "!/var/lib/tianxia/tiers/tianxia-moe.off";
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx_moe_up.sh";
      Restart = "always";
      RestartSec = "15s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-tini = {
    description = "Tini-Cybersec triage champion (:11498)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = "!/var/lib/tianxia/tiers/tianxia-tini.off";
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/maxbatch/Tini-Cybersec-8B-A1B-Q4_K_M.gguf -c 8192 --port 11498";
      Restart = "always";
      RestartSec = "15s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-granite = {
    description = "Granite-8B deep-scoring standby (:11499)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = "!/var/lib/tianxia/tiers/tianxia-granite.off";
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/maxbatch/granite-4.2-8b-Q4_K_M.gguf -c 8192 --port 11499";
      Restart = "always";
      RestartSec = "15s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-bge = {
    description = "bge-reranker production rerank (:11497)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx_bge_up.sh";
      Restart = "always";
      RestartSec = "15s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.emb06-server = {
    description = "Qwen3-Embedding-0.6B recall engine (:11495)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx_mesh_bind.sh ${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/eval/Qwen3-Embedding-0.6B-Q8_0.gguf -c 2048 --port 11495 --embedding --host @MESH_BIND@";
      Restart = "always";
      RestartSec = "15s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
