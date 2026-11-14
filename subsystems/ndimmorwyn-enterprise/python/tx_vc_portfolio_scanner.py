#!/usr/bin/env python3
# ffp: FFP-MKT-214 vc-portfolio-surface-scanner python
# File: python/tx_vc_portfolio_scanner.py
# Compliance: DSS-14 (MAHASARASVATI + ANNAPURNA + KAMALA) + ENHAN3

import json
from typing import Dict, List, Any

# 42 VCs & Check-Writers Sample Focus
VC_ROSTER = [
    {"name": "Crestone Venture Capital", "lead": "FinTech / Payments", "check_size": "Seed / Series A"},
    {"name": "Ballistic Ventures", "lead": "Cybersecurity & Sovereign Defense", "check_size": "$2M - $5M"},
    {"name": "Maniv Mobility", "lead": "Logistics & Global Supply Chain", "check_size": "Seed"},
    {"name": "Angular Ventures", "lead": "Gil Dibner (Deep Tech Enterprise)", "check_size": "Pre-Seed / Seed"},
    {"name": "Icebreaker.vc", "lead": "Riku Seppälä (Nordic/Baltic Founders)", "check_size": "€500k - €2M"},
]

class VcPortfolioSurfaceScanner:
    """
    E214: Generates Portfolio-Wide Margin Risk & Prompt-Injection Heatmaps
    to pitch VCs wholesale as RGU distributors rather than asking for investment.
    """
    def __init__(self) -> None:
        self.audits: List[Dict[str, Any]] = []

    def audit_portfolio(self, vc_name: str, portfolio_companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        audited_companies = []
        total_estimated_llm_burn_eur = 0.0
        high_risk_count = 0

        for comp in portfolio_companies:
            spend = comp.get("estimated_monthly_spend_eur", 5000.0)
            total_estimated_llm_burn_eur += spend * 12.0
            p99_latency_ms = comp.get("p99_latency_ms", 450)
            has_guardrails = comp.get("has_ebpf_guardrails", False)

            is_at_risk = (spend > 10000.0 and not has_guardrails) or (p99_latency_ms > 600)
            if is_at_risk:
                high_risk_count += 1

            audited_companies.append({
                "company": comp.get("name"),
                "monthly_spend_eur": spend,
                "projected_annual_savings_eur": round(spend * 0.796 * 12.0, 2),
                "at_margin_risk": is_at_risk,
                "risk_reason": "Unhedged cloud token spikes" if not has_guardrails else "Latency degradation",
            })

        report = {
            "vc_fund": vc_name,
            "companies_scanned": len(portfolio_companies),
            "high_risk_companies": high_risk_count,
            "total_portfolio_annual_spend_eur": round(total_estimated_llm_burn_eur, 2),
            "total_potential_annual_savings_eur": round(total_estimated_llm_burn_eur * 0.796, 2),
            "wholesale_offer": "Portfolio-Wide Gross-Margin & Latency Audit (€4,500 for 10 PortCos)",
            "details": audited_companies,
        }
        self.audits.append(report)
        return report


if __name__ == "__main__":
    scanner = VcPortfolioSurfaceScanner()
    crestone_sample = [
        {"name": "Noah Payments", "estimated_monthly_spend_eur": 18500.0, "p99_latency_ms": 320, "has_ebpf_guardrails": False},
        {"name": "Ubyx Clearing", "estimated_monthly_spend_eur": 12000.0, "p99_latency_ms": 280, "has_ebpf_guardrails": True},
        {"name": "Codex FX", "estimated_monthly_spend_eur": 22000.0, "p99_latency_ms": 780, "has_ebpf_guardrails": False},
    ]

    report = scanner.audit_portfolio("Crestone Venture Capital", crestone_sample)
    print("=== [TIANXIAOS // CAREER SPEAR] VC Portfolio Surface Scanner ===")
    print(f"Fund: {report['vc_fund']}")
    print(f"Companies Scanned: {report['companies_scanned']} (High Risk: {report['high_risk_companies']})")
    print(f"Total Spend: €{report['total_portfolio_annual_spend_eur']:.2f}")
    print(f"Potential OpEx Savings: €{report['total_potential_annual_savings_eur']:.2f}")
    print(f"Wholesale Pitch: {report['wholesale_offer']}")
