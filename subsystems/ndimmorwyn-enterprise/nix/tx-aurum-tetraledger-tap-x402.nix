# ffp: FFP-NIX-212 shandoff-aurum-x402 declarative
# Shandoff Hook Module for FinTech & Stablecoin Clearing Founders
{ pkgs, ... }:

{
  services.tetraLedgerTap = {
    enable = true;
    settlementRail = "x402";
    maxLatencyMicroseconds = 50;
    tier1BufferRatio = 0.15;
    merkleAuditing = true;
  };
}
