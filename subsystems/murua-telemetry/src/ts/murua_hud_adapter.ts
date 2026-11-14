// ffp: FFP-MURUA-TS frontend typescript
/**
 * TianxiaOS / Murua Cockpit PWA HUD Adapter
 * Renders TOON/TRON streams, acoustic Lamb wave charts, and delivery hazard curves.
 */

export interface ToonItem {
    corridor: string;
    itemId: string;
    preAdvDt: string | null;
    pickupDt: string;
    cfcStampDt: string | null;
    hubSprayDt: string | null;
    delivDt: string | null;
    massGrams: number;
    thicknessMm: number;
    format: string;
    kixOk: boolean;
    status: string;
}

export interface SrmTelemetry {
    f0Hz: number;
    zeta: number;
    deltaF0: number;
    deltaInvQ: number;
    estimatedMassG: number;
    status: "EMPTY_COMPARTMENT" | "MAIL_PRESENT_LOADED" | "AMBIGUOUS";
}

export class MuruaHudAdapter {
    static parseToonStream(rawStream: string): ToonItem[] {
        const lines = rawStream.trim().split("\n");
        const items: ToonItem[] = [];

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith("#") || trimmed.startsWith("@TOON")) {
                continue;
            }
            const p = trimmed.split("|");
            if (p.length < 12) continue;

            items.push({
                corridor: p[0],
                itemId: p[1],
                preAdvDt: p[2] === "null" ? null : p[2],
                pickupDt: p[3],
                cfcStampDt: p[4] === "null" ? null : p[4],
                hubSprayDt: p[5] === "null" ? null : p[5],
                delivDt: p[6] === "null" ? null : p[6],
                massGrams: parseFloat(p[7]) || 0,
                thicknessMm: parseFloat(p[8]) || 0,
                format: p[9],
                kixOk: p[10] === "true",
                status: p[11],
            });
        }
        return items;
    }

    static formatHudSummary(items: ToonItem[], srm: SrmTelemetry): string {
        const total = items.length;
        const oxbow = items.filter((i) => i.status.includes("OXBOW")).length;
        const delivered = items.filter((i) => i.status.includes("DELIVERED")).length;

        return `[MURUA HUD] Active Consignments: ${total} | In Oxbow Queue: ${oxbow} | Delivered: ${delivered}\n` +
               `[SRM SENSOR] Tray State: ${srm.status} (Delta F0: ${srm.deltaF0.toFixed(1)} Hz, Delta Q^-1: ${srm.deltaInvQ.toFixed(4)})`;
    }
}

// Self-test execution
const sampleToon = `@TOON:v1|corridor|item_id|pre_adv_dt|pickup_dt|cfc_stamp_dt|hub_spray_dt|deliv_dt|mass_g|thick_mm|fmt|kix_ok|status
NL-AMS_EE-TLL_12618|58b73b08|2026-10-25T14:10|2026-10-27T11:00|2026-10-27|null|null|65.0|4.0|STD_ENV|true|IN_OXBOW_BUFFER
NL-AMS_EE-TLL_12618|c31f078b|2026-10-26T14:40|2026-10-27T11:00|2026-10-27|null|null|65.0|4.0|STD_ENV|true|IN_OXBOW_BUFFER`;

const parsed = MuruaHudAdapter.parseToonStream(sampleToon);
const srmSample: SrmTelemetry = {
    f0Hz: 404.3,
    zeta: 0.024,
    deltaF0: -15.7,
    deltaInvQ: 0.040,
    estimatedMassG: 130.0,
    status: "MAIL_PRESENT_LOADED"
};

console.log(MuruaHudAdapter.formatHudSummary(parsed, srmSample));
