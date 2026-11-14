// ffp: FFP-BIN-004 tx-rasoom-nkg-bin rust
//! Production binary: tx_rasoom_nkg
//! Encodes Nsibidi 16-bit Ideographic hyper-edges and generates Carnatic Konnakol TDMA mesh schedules.

use tianxiaos_polyglot_kenning::rasoom::RasoomNkgEngine;

fn run_diagnostics(rasoom: &RasoomNkgEngine) {
    // 1. Encode Nsibidi Hyper-Edges
    let edge1 = rasoom.encode_nsibidi_edge("Ndimmorwyn", "TetraLedger", 0x0101, b"TETRALEDGER_SETTLEMENT_EUR_628");
    println!("[NSIBIDI HYPER-EDGE 1]: {}", edge1);

    let edge2 = rasoom.encode_nsibidi_edge("Nimue", "EscrowGateway", 0x0102, b"MURUA_DISPUTE_CN08_FREEZE");
    println!("[NSIBIDI HYPER-EDGE 2]: {}", edge2);

    let edge3 = rasoom.encode_nsibidi_edge("AgentSwarm", "MemoryOverlay", 0x0103, b"IREB_ABSCISSION_PRUNE");
    println!("[NSIBIDI HYPER-EDGE 3]: {}", edge3);

    let edge4 = rasoom.encode_nsibidi_edge("KarunaEngine", "AgentThread", 0x0104, b"KARUNA_VR_MIRROR_HEAL");
    println!("[NSIBIDI HYPER-EDGE 4]: {}", edge4);

    let edge5 = rasoom.encode_nsibidi_edge("SecurityAuditor", "TargetProcess", 0x0105, b"NIMUE_DEFAULT_PROXY_KILL");
    println!("[NSIBIDI HYPER-EDGE 5]: {}", edge5);

    // 2. Generate Konnakol [3, 2] Khanda Chapu TDMA Schedule across 5 Nodes
    let schedule = rasoom.generate_konnakol_tdma_schedule(1000);
    println!(
        "\n[KONNAKOL TDMA MESH]: epoch={}ms nodes={} korvai_convergence_b3={}",
        schedule.epoch_duration_ms, schedule.total_nodes, &schedule.korvai_convergence_hash[..16]
    );

    for slot in schedule.slots {
        println!(
            "  * [{:<12} | {:<10}] Gati={:<12} (sub={}) Solkattu={:<32} Phase={:6.2}ms Burst={:5.2}ms Token={}",
            slot.node_name,
            slot.ip_address,
            slot.gati_name,
            slot.subdivision,
            slot.solkattu_syllables,
            slot.phase_offset_ms,
            slot.burst_duration_ms,
            slot.korvai_checkpoint_token
        );
    }
}

fn main() {
    println!("=== [TIANXIAOS // RASOOM-NKG] Initializing Semiotic Graph & Konnakol Bus ===");
    let rasoom = RasoomNkgEngine::new();
    run_diagnostics(&rasoom);

    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--daemon") {
        println!("[RASOOM MESH] Entering persistent TDMA scheduler loop...");
        loop {
            std::thread::sleep(std::time::Duration::from_secs(30));
        }
    }

    println!("=== [TIANXIAOS // RASOOM-NKG] Dispatch Complete ===");
}
