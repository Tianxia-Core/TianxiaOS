// ffp: FFP-TS-001 osc7501-hud-adapter typescript
// TianxiaOS Core 10 (Nimbus-EdgeUI) - Mātaṅgī Schema & Protocol Gate
// Terminal OSC 7501 HUD Telemetry & B2C Agent Wallet Event Serializer

export interface TelemetryPacket {
    coreId: number;
    coreName: string;
    mahavidyaGate: string;
    latencyUs: number;
    zeroLossInvariant: boolean;
}

export class Osc7501HudAdapter {
    static formatOsc7501(title: string, value: string): string {
        // OSC 7501 format: ESC ] 7501 ; title = value BEL
        return `\x1b]7501;${title}=${value}\x07`;
    }

    static serializeTelemetry(packet: TelemetryPacket): string {
        const osc = this.formatOsc7501(`CORE_${packet.coreId}`, `${packet.latencyUs}us`);
        const badge = packet.zeroLossInvariant ? "[I1_ZERO_OK]" : "[FAIL]";
        return `[HUD] ${osc} ${badge} ${packet.coreName} (${packet.mahavidyaGate})`;
    }
}

// CLI execution test
function main() {
    console.log("=== [TIANXIAOS // NIMBUS-EDGEUI (TS)] Mātaṅgī HUD Adapter ===");
    const testPacket: TelemetryPacket = {
        coreId: 10,
        coreName: "Nimbus-EdgeUI",
        mahavidyaGate: "Mātangī",
        latencyUs: 42,
        zeroLossInvariant: true,
    };
    const output = Osc7501HudAdapter.serializeTelemetry(testPacket);
    console.log("[TS-OUTPUT]:", output);
    console.log("=== [TIANXIAOS // NIMBUS-EDGEUI (TS)] Execution Complete ===");
}

main();
