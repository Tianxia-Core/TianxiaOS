# ffp: FFP-NDIMMORWYN-SOVEREIGN-GTM-GLUE glue python
# File: tianxiaos_ndimmorwyn_enterprise/python/tx_sovereign_gtm.py
# Compliance: DSS-14.2 (PARAMASIVA + KAMALA + ANNAPURNA + MAHASARASVATI) + SLECO-SO++ + ENHAN3
"""
tx_sovereign_gtm.py -- Sovereign Glue Orchestrator for Ndimmôrwyn GTM, Prospecting & Lead Generation.
Integrates native Rust release daemons (tx_spear_and_meter, tx_career_spear_matcher),
tx_career_spear, tx_scour, tx_opportunity_miner, and 40 Family Offices
into TianxiaOS's 41 RGUs across the 5-Level Make It Pay (MIP) ladder.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure workspace is in sys.path
WORKSPACE = Path("${TX_WORKSPACE:-/var/lib/tianxia}")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from tx_career_spear.core.gtm_swarm import (
    SignalAgent, EnrichmentAgent, ScoringAgent, ResearchAgent,
    CopywritingAgent, SequenceAgent, ContentAgent, CRMAgent, InboxAgent, GTMBrain
)
from tx_career_spear.outreach.family_offices import FamilyOfficesDirectory
from tx_career_spear.outreach.grinfi_ingest import GrinfiIngestor
from tx_career_spear.outreach.telegrin_client import TelegrinClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] tx_sovereign_gtm: %(message)s")
log = logging.getLogger("tx_sovereign_gtm")


class SovereignGTMEngine:
    """
    Master engine orchestrating prospecting, outreach, and patient-capital syndication for TianxiaOS.
    """
    NDIMMORWYN_DIR = WORKSPACE / "tianxia" / "docs" / "ndimmorwyn"
    DOWNLOAD_DIR = Path("/sdcard/Download")

    def __init__(self) -> None:
        self.NDIMMORWYN_DIR.mkdir(parents=True, exist_ok=True)
        self.telegrin = TelegrinClient()

    def run_full_gtm_sweep(self) -> Dict[str, Any]:
        t0 = time.time()
        log.info("Starting Sovereign GTM & Lead Generation Sweep across TianxiaOS...")

        # 1. Ingest Grinfi Leads
        leads = GrinfiIngestor.load_leads()
        log.info(f"Loaded {len(leads)} decision-makers from Grinfi")

        # 2. Ingest Family Offices (40 Patient Capital targets)
        family_offices = FamilyOfficesDirectory.get_all_offices()
        log.info(f"Loaded {len(family_offices)} Family Offices replacing VCs")

        # 3. Execute 10-Agent Swarm Pipeline over top leads
        orchestrated_leads = []
        for lead in leads[:25]:
            lead_dict = lead.to_dict()
            signals = SignalAgent.evaluate_signals(lead_dict)
            enrichment = EnrichmentAgent.enrich(lead_dict)
            scoring = ScoringAgent.score_deal(lead_dict, signals)
            research = ResearchAgent.analyze_context(lead_dict)
            copy = CopywritingAgent.generate_all_channels(lead_dict, research, enrichment)
            cadence = SequenceAgent.build_cadence(lead_dict, copy)

            orchestrated_leads.append({
                "name": lead.full_name,
                "company": lead.company,
                "tier": scoring["target_tier"],
                "bant_score": scoring["bant_score"],
                "identified_pain": research["identified_pain_point"],
                "matched_asset": research["matched_tianxia_asset"],
                "recommended_rgu_offer": scoring["recommended_rgu_level"],
                "email_pitch": copy["email_subject"],
                "telegrin_pitch": copy["telegrin_pitch"],
                "cadence_steps": len(cadence),
            })

        # 4. Generate Social Thought-Leadership Hooks
        social_hooks = ContentAgent.generate_social_hook("AF_XDP_vs_Standard_Sockets")

        # 5. Export Family Office Syndication Sheet
        fo_sheet_path = self.DOWNLOAD_DIR / "tx_family_offices_syndication.xlsx"
        FamilyOfficesDirectory.export_spreadsheet(fo_sheet_path)

        # 6. Execute Native Rust Outcome Meter & Karuna Shandoff Generator (tx_spear_and_meter)
        top_company = orchestrated_leads[0]["company"] if orchestrated_leads else "Sovereign Target Enterprise"
        rust_spear_bin = WORKSPACE / "tianxiaos_ndimmorwyn_enterprise" / "target" / "release" / "tx_spear_and_meter"
        shandoff_log = ""
        if rust_spear_bin.exists():
            import subprocess
            try:
                proc = subprocess.run([str(rust_spear_bin), top_company], capture_output=True, text=True, timeout=5)
                shandoff_log = proc.stdout.strip()
            except Exception as e:
                shandoff_log = f"Failed to execute native spear binary: {e}"

        # 7. Build Master Telemetry Summary
        telemetry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "SOVEREIGN_GTM_SWEEP_COMPLETE",
            "duration_seconds": round(time.time() - t0, 2),
            "stats": {
                "decision_maker_leads_active": len(leads),
                "family_offices_syndicated": len(family_offices),
                "swarms_orchestrated": len(orchestrated_leads),
                "telegrin_readiness": "ACTIVE_AETHERVAULT_AUTHENTICATED" if self.telegrin.api_key else "STANDBY",
                "native_rust_compute_kernel": "tx_career_spear_matcher (release v8.0.0)",
                "native_rust_rgu_meter": "tx_spear_and_meter (release v8.0.0)",
            },
            "top_prospects": orchestrated_leads[:10],
            "native_rgu_shandoff_telemetry": shandoff_log,
            "social_inbound_hooks": social_hooks,
            "mip_rgu_ladder": {
                "Level_0_Lead_Magnet": "11.40 Mpps AF_XDP Zero-Copy Whitepaper & BitNet b1.58 Benchmarks",
                "Level_1_Diagnostic": "€1,250 48-Hour Systems Architecture Diagnostic / Advisory",
                "Level_2_Sprint": "€9,500 Flat 72-Hour Zero-Stub 8-FFP RGU Deployment Sprint",
                "Level_3_Retainer": "€14,000/mo - €25,000/mo Fractional Principal Systems Architect",
                "Level_4_Programmatic": "Telegrin / Grinfi API Outbound & Telemetry Micropayments",
                "Level_5_Sovereign_Capital": "Private Equity & Sovereign Compute Syndication across 40 Family Offices",
            }
        }

        # Write reports
        report_ndimmorwyn = self.NDIMMORWYN_DIR / "SOVEREIGN_GTM_REPORT.json"
        report_ndimmorwyn.write_text(json.dumps(telemetry, indent=2), encoding="utf-8")

        report_download = self.DOWNLOAD_DIR / "tx_sovereign_gtm_report.json"
        report_download.write_text(json.dumps(telemetry, indent=2), encoding="utf-8")

        log.info(f"Sovereign GTM Report generated: {report_ndimmorwyn}")
        return telemetry


def main() -> int:
    parser = argparse.ArgumentParser(description="tx_sovereign_gtm - Ndimmorwyn Sovereign GTM & Prospecting Engine")
    parser.add_argument("--run-sweep", action="store_true", help="Execute complete GTM and prospecting sweep")
    parser.add_argument("--family-offices", action="store_true", help="Export 40 Family Offices syndication spreadsheet")
    args = parser.parse_args()

    engine = SovereignGTMEngine()
    if args.family_offices:
        out = engine.DOWNLOAD_DIR / "tx_family_offices_syndication.xlsx"
        FamilyOfficesDirectory.export_spreadsheet(out)
        print(f"Exported Family Offices spreadsheet to {out}")
        return 0

    res = engine.run_full_gtm_sweep()
    print("\n" + "=" * 70)
    print("  TIANXIAOS NDIMMORWYN SOVEREIGN GTM & PROSPECTING REPORT")
    print("=" * 70)
    print(f"Status               : {res['status']}")
    print(f"Decision-Maker Leads : {res['stats']['decision_maker_leads_active']}")
    print(f"Family Offices Active: {res['stats']['family_offices_syndicated']}")
    print(f"Telegrin Readiness   : {res['stats']['telegrin_readiness']}")
    print(f"Top Strike Targets   : {len(res['top_prospects'])} orchestrated with multi-channel copy")
    print(f"Report Location      : {engine.NDIMMORWYN_DIR / 'SOVEREIGN_GTM_REPORT.json'}")
    print(f"Downloads Sync       : {engine.DOWNLOAD_DIR / 'tx_sovereign_gtm_report.json'}")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
