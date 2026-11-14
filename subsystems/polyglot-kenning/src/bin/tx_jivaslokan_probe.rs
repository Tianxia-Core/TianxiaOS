// ffp: FFP-BIN-003 tx-jivaslokan-probe-bin rust
//! Production binary: tx_jivaslokan_probe
//! Evaluates Spike-Weighted Huber Loss probes and JOT Wasserstein Trajectory drift.

use tianxiaos_polyglot_kenning::jivaslokan::JivaslokanHuberProbe;

fn main() {
    println!("=== [TIANXIAOS // JIVASLOKAN PROBE] Initializing Sub-14ms Introspection Probe ===");

    let probe = JivaslokanHuberProbe::new(1.0, 3.2, 1.85, 0.45);

    let safe_centroid = vec![0.10, -0.04, 0.29, 0.09, -0.15, 0.40, 0.05, -0.08];

    // Case 1: Safe Nominal Activations
    let nominal_activations = vec![0.12, -0.05, 0.31, 0.08, -0.14, 0.42, 0.06, -0.07];
    let result_nominal = probe.evaluate_hidden_state(&nominal_activations, &safe_centroid);
    println!(
        "[JIVASLOKAN NOMINAL]: safe={} loss={:.5} spike_w={:.4} w1_drift={:.5} latency={}us status='{}'",
        result_nominal.safe,
        result_nominal.weighted_huber_loss,
        result_nominal.spike_weight,
        result_nominal.jot_wasserstein_drift,
        result_nominal.latency_us,
        result_nominal.reason
    );

    // Case 2: Outlier Activation Spike (Injection or Hallucination)
    let anomalous_activations = vec![0.12, -0.05, 0.31, 0.08, -0.14, 18.5, 0.06, -0.07]; // 18.5 is massive spike!
    let result_anomalous = probe.evaluate_hidden_state(&anomalous_activations, &safe_centroid);
    println!(
        "[JIVASLOKAN SPIKE DETECTED]: safe={} tripped={} loss={:.5} spike_w={:.4} status='{}'",
        result_anomalous.safe,
        result_anomalous.circuit_breaker_tripped,
        result_anomalous.weighted_huber_loss,
        result_anomalous.spike_weight,
        result_anomalous.reason
    );

    // Case 3: Adversarial Basin Drift (JOT Wasserstein divergence)
    let drift_activations = vec![1.10, 0.95, 1.29, 1.09, 0.85, 1.40, 1.05, 0.92]; // Systematic shift
    let result_drift = probe.evaluate_hidden_state(&drift_activations, &safe_centroid);
    println!(
        "[JIVASLOKAN JOT DRIFT DETECTED]: safe={} tripped={} w1_drift={:.5} status='{}'",
        result_drift.safe,
        result_drift.circuit_breaker_tripped,
        result_drift.jot_wasserstein_drift,
        result_drift.reason
    );

    println!("=== [TIANXIAOS // JIVASLOKAN PROBE] Probe Execution Complete ===");
}
