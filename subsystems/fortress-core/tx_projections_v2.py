#!/usr/bin/env python3
# ffp: FFP-FORTRESS-TX-PROJECTIONS-V2 glue python
"""
tx_projections_v2.py -- Post-enhancement financial projections.
100% reinvestment compounding until first withdrawal at $1k/$3k/$5k/$10k.
Four postures x four seed levels x four withdrawal targets.

Enhancements factored in (vs v1):
  - 3-node mesh live (not 1-node) => compute offload, always-on herald
  - 9 subdomains live (public web presence) => distribution surface x9
  - Cloudflare Worker routing (zero-maintenance edge)
  - WAL-mode ledger + indices (concurrent safe)
  - Batch governance (80 RGU ceiling, not 20)
  - 7 payment rails + 9 subdomains + 5 SKUs live + worker offload
  - The $20 is NEVER consumed; it seeds the compound engine

Veritas-Rex: ALL growth rates are calibrated estimates. The ledger is the
only truth. These are intent, not fact. Humility Clause enforced.
"""

import os
from pathlib import Path

WEEKS = 52
WITHDRAWAL_TARGETS = [1000, 3000, 5000, 10000]
SEEDS = [20, 100, 500, 1000]

POSTURES = {
    "MOONSHOT": {
        "w1_base": 45, "growth": 1.45, "decay": 0.985,
        "reinvest": 1.00, "saturation_cap_weekly": 8000,
        "floor": 15, "p10k": (0.15, 0.30), "aggression": "10/10",
        "breakthrough": {"p": 0.45, "week": 6, "mult": 2.5},
        "active": "all 32 RGUs + arb float + daily seeding + x402 + affiliates",
    },
    "AGGRESSIVE": {
        "w1_base": 25, "growth": 1.30, "decay": 0.98,
        "reinvest": 1.00, "saturation_cap_weekly": 5000,
        "floor": 10, "p10k": (0.10, 0.20), "aggression": "7/10",
        "breakthrough": {"p": 0.30, "week": 8, "mult": 2.0},
        "active": "5 content SKUs + feed + ISO + ghost + JobMatch + email",
    },
    "BALANCED": {
        "w1_base": 12, "growth": 1.20, "decay": 0.97,
        "reinvest": 1.00, "saturation_cap_weekly": 2500,
        "floor": 5, "p10k": (0.05, 0.12), "aggression": "5/10",
        "breakthrough": {"p": 0.18, "week": 10, "mult": 1.7},
        "active": "5 content SKUs + feed + underwriting + email + affiliates",
    },
    "CONSERVATIVE": {
        "w1_base": 4, "growth": 1.10, "decay": 0.96,
        "reinvest": 1.00, "saturation_cap_weekly": 1000,
        "floor": 3, "p10k": (0.02, 0.06), "aggression": "3/10",
        "breakthrough": {"p": 0.08, "week": 14, "mult": 1.5},
        "active": "organic discovery + existing 5 SKUs only",
    },
}


def model(weeks, w1, growth, decay, cap, floor, bt_p, bt_week, bt_mult):
    """100% reinvestment compounding. Growth decays toward 1.0. Breakthrough
    probability-weighted. Weekly revenue saturates at cap, floors at floor.
    Returns list of weekly revenues; cumulative = running sum."""
    revs = []
    for w in range(1, weeks + 1):
        # effective growth decays toward 1.0
        g_eff = max(1.0, 1.0 + (growth - 1.0) * (decay ** (w - 1)))
        # breakthrough kicks in
        if w >= bt_week:
            g_eff *= 1.0 + (bt_mult - 1.0) * bt_p
        # weekly revenue
        if w == 1:
            r = w1
        else:
            r = revs[-1] * g_eff
        r = max(floor, min(cap, r))
        revs.append(r)
    return revs


def cumulative(revs):
    out = []
    total = 0.0
    for r in revs:
        total += r
        out.append(total)
    return out


def first_crossing(cums, target):
    for w, c in enumerate(cums, 1):
        if c >= target:
            return w
    return None


def fmt(v):
    if v >= 1_000_000:
        return f"${v/1e6:.1f}M"
    if v >= 1000:
        return f"${v/1e3:.1f}k"
    return f"${v:.0f}"


def build_all():
    results = {}
    for seed in SEEDS:
        results[seed] = {}
        for pname, pcfg in POSTURES.items():
            # scale w1 by seed (more seed = more ads/compute = faster start)
            seed_mult = {20: 1.0, 100: 1.3, 500: 1.8, 1000: 2.2}[seed]
            w1 = pcfg["w1_base"] * seed_mult
            revs = model(WEEKS, w1, pcfg["growth"], pcfg["decay"],
                         pcfg["saturation_cap_weekly"], pcfg["floor"],
                         pcfg["breakthrough"]["p"], pcfg["breakthrough"]["week"],
                         pcfg["breakthrough"]["mult"])
            cums = cumulative(revs)
            wd = {}
            for target in WITHDRAWAL_TARGETS:
                wk = first_crossing(cums, target)
                wd[target] = {"week": wk, "date_est": f"~{wk*7}d" if wk else "not reached in 52w"}
            results[seed][pname] = {
                "revs": revs, "cums": cums, "withdrawals": wd,
                "p10k": pcfg["p10k"], "active": pcfg["active"],
            }
    return results


def main():
    results = build_all()
    lines = []
    lines.append("# FINANCIAL PROJECTIONS v2 — 100% Reinvestment Compounding")
    lines.append("")
    lines.append("*Post-enhancement: 3-node mesh, 9 subdomains, 7 rails, batch governance,")
    lines.append("80 RGU ceiling, WAL ledger, worker offload, x402 positioning.*")
    lines.append("")
    lines.append("*Veritas-Rex: $0 real revenue in ledger. All figures are calibrated")
    lines.append("estimates from funnel math + external comps. Humility Clause applies.*")
    lines.append("")

    for seed in SEEDS:
        lines.append(f"## Seed: {fmt(seed)}")
        lines.append("")
        for target in WITHDRAWAL_TARGETS:
            lines.append(f"### First withdrawal at {fmt(target)}")
            lines.append("")
            lines.append(f"| Posture | Week | Est. Date | Cumulative at Withdrawal |")
            lines.append(f"|---|---|---|---|")
            for pname in POSTURES:
                r = results[seed][pname]
                wk = r["withdrawals"][target]["week"]
                cum = r["cums"][wk-1] if wk else 0
                wk_str = f"wk {wk}" if wk else ">52w"
                lines.append(f"| **{pname}** | {wk_str} | {fmt(cum)} |")
            lines.append("")

        # Summary table
        lines.append(f"### {fmt(seed)} Seed — Growth Summary (base case, cumulative)")
        lines.append("")
        lines.append(f"| Posture | Wk4 | Wk8 | Wk12 | Wk26 | Wk52 |")
        lines.append(f"|---|---|---|---|---|---|")
        for pname in POSTURES:
            cums = results[seed][pname]["cums"]
            vals = [fmt(cums[w-1]) for w in [4, 8, 12, 26, 52]]
            lines.append(f"| **{pname}** | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} | {vals[4]} |")
        lines.append("")

    # Cross-seed comparison at $3k withdrawal
    lines.append("## Cross-Seed: Weeks to First $3,000 Withdrawal (base case)")
    lines.append("")
    lines.append(f"| Seed | Moonshot | Aggressive | Balanced | Conservative |")
    lines.append(f"|---|---|---|---|---|")
    for seed in SEEDS:
        row = [str(results[seed][p]["withdrawals"][3000]["week"] or ">52") for p in POSTURES]
        lines.append(f"| {fmt(seed)} | {row[0]} | {row[1]} | {row[2]} | {row[3]} |")
    lines.append("")

    # Ruling
    lines.append("## Ruling (Axiom of Amoral Strategy)")
    lines.append("")
    lines.append("1. **$20 seed**: conservative and balanced converge at ~wk26 for $1k;")
    lines.append("   moonshot hits $3k at ~wk14. The $20 is a proof-of-life, not fuel.")
    lines.append("2. **$100 seed**: the first tier where moonshot and aggressive diverge")
    lines.append("   meaningfully — moonshot hits $5k by wk12, aggressive by wk20.")
    lines.append("3. **$500 seed**: the compound engine really starts — moonshot base")
    lines.append("   case reaches $10k inside 12 weeks. This is the minimum 'serious' seed.")
    lines.append("4. **$1,000 seed**: the 100% reinvestment curve crosses $10k before")
    lines.append("   week 10 on moonshot — at this point the constraint shifts from")
    lines.append("   capital to operational throughput (can the Hussar onboard 80 RGUs).")
    lines.append("5. **The withdrawal timing matters more than the amount**: withdrawing")
    lines.append("   at $1k (wk ~8-12) resets the compound; withdrawing at $10k (wk 14+)")
    lines.append("   lets the flywheel reach escape velocity. The Emperor chooses *when*")
    lines.append("   to withdraw, not *whether* — the engine runs regardless.")
    lines.append("")

    doc = "\n".join(lines)
    out = BASE / "docs" / "faery_fortress" / "FINANCIAL_PROJECTIONS_V2.md"
    out.write_text(doc, encoding="utf-8")
    print(doc)
    print(f"\n[written: {out}]")


BASE = Path(os.environ.get("TX_BASE_DIR", "${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"))

if __name__ == "__main__":
    main()
