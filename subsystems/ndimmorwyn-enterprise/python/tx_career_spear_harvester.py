#!/usr/bin/env python3
# ffp: FFP-MKT-211 reverse-mercor-vacancy-harvester python
# File: python/tx_career_spear_harvester.py
# Compliance: DSS-14 (ANNAPURNA + KAMALA + MAHASARASVATI) + ENHAN3

import json
import sys
from typing import Dict, List, Any

# 15 USD Remote Platforms + YC Work at a Startup
REMOTE_PLATFORMS = [
    "Wellfound", "Arc.dev", "Toptal", "Contra", "We Work Remotely",
    "RemoteOK", "Dynamite Jobs", "Crossover", "JustRemote", "Working Nomads",
    "Remote.co", "FlexJobs", "Remotive", "Hubstaff Talent", "Remote Woman"
]

TARGET_ROLES = [
    "Principal Architect", "Staff Rust Engineer", "Head of AI Infra",
    "Founding Engineer", "Lead Platform Engineer", "Core Banking Architect"
]

class CareerSpearHarvester:
    """
    E211: Inverts the Mercor ($10B) recruitment broker model.
    Treats open vacancies as live enterprise pain-signal telemetry feeds.
    """
    def __init__(self) -> None:
        self.strike_targets: List[Dict[str, Any]] = []

    def score_vacancy(self, company: str, role: str, days_open: int, platform: str, estimated_budget_eur: float) -> Dict[str, Any]:
        """
        Calculates Urgency & RGU Opportunity Score:
        If days_open > 14, triggers immediate RGU Sprint / Fractional Strike.
        """
        is_senior = any(t.lower() in role.lower() for t in TARGET_ROLES)
        urgency_score = min(1.0, (days_open / 45.0)) * (1.5 if is_senior else 1.0)

        # Level 1 Strike: Fractional Principal / 48-Hour Diagnostic
        # Level 2 Strike: Flat €9,500 RGU Deployment Sprint
        if days_open > 14 and is_senior:
            strike_tier = "LEVEL_2_RGU_REPLACEMENT"
            recommended_offer = "€9,500 Flat 72-Hour RGU Deployment Sprint"
            pitch_script = (
                f"Noticed your {role} search at {company} has been open for {days_open} days on {platform}. "
                f"Rather than spending €60k+ in recruiter fees and 90 days onboarding, we deploy our pre-audited, "
                f"zero-stub 8-FFP sovereign appliance in 72 hours under a fixed €9,500 sprint."
            )
        else:
            strike_tier = "LEVEL_1_FRACTIONAL_ARCHITECT"
            recommended_offer = "€1,250 48-Hour Architecture Diagnostic / €14k/mo Fractional Lead"
            pitch_script = (
                f"Following your {role} listing at {company}. We offer an immediate 48-hour architectural diagnostic "
                f"(€1,250) to unblock the current technical roadmap while your full-time hiring pipeline runs."
            )

        target_record = {
            "company": company,
            "role": role,
            "days_open": days_open,
            "platform": platform,
            "urgency_score": round(urgency_score, 3),
            "strike_tier": strike_tier,
            "recommended_offer": recommended_offer,
            "pitch_script": pitch_script,
        }
        self.strike_targets.append(target_record)
        return target_record


if __name__ == "__main__":
    harvester = CareerSpearHarvester()
    sample_openings = [
        ("Noah Payments", "Staff Rust Core Banking Engineer", 24, "Arc.dev", 180000.0),
        ("Paid.ai", "Head of AI Infrastructure", 19, "Wellfound", 210000.0),
        ("Harbor Security", "Principal Systems Architect", 31, "Toptal", 220000.0),
        ("Polar.sh", "Senior Billing Rails Developer", 12, "RemoteOK", 140000.0),
    ]

    print("=== [TIANXIAOS // CAREER SPEAR] Reverse-Mercor Vacancy Harvester ===")
    for company, role, days, plat, budget in sample_openings:
        res = harvester.score_vacancy(company, role, days, plat, budget)
        print(f"\n[TARGET: {res['company']}] Urgency: {res['urgency_score']}")
        print(f"  Role: {res['role']} ({res['days_open']} days on {res['platform']})")
        print(f"  Tier: {res['strike_tier']} -> {res['recommended_offer']}")
        print(f"  Script: {res['pitch_script']}")
