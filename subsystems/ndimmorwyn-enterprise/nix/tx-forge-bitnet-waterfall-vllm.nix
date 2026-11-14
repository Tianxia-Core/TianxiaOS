# ffp: FFP-NIX-213 shandoff-forge-bitnet declarative
# Shandoff Hook Module for AI & DevTools Startups (79.6% Token OpEx Reduction)
{ pkgs, ... }:

{
  services.forgeInferenceWaterfall = {
    enable = true;
    tier1Local = "bitnet-b1.58-cpu";
    tier2Vulkan = "vuda-softem-moe";
    tier3Vllm = "deepseek-v3-r1";
    marginFloorRatio = 0.85;
    compressionCodec = "TOON";
  };
}
