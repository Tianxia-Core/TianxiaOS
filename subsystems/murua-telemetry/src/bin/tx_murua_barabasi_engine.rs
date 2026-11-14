// ffp: FFP-MURUA-BARABASI-BIN barabasi-engine-cli rust
//! Murua Barabási-Oxbow Calculation CLI Engine
//! Evaluates heavy-tail waiting time density, C_CBD score, and Heddle trajectory escalation.

use chrono::{Duration, Utc};
use murua_architecture_enhancement::barabasi::{BarabasiOxbowEstimator, CorridorParameters};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let corridor_id = args.get(1).map(|s| s.as_str()).unwrap_or("NL-AMS_EE-TLL_12618");

    let mut params = CorridorParameters::default();
    params.corridor_id = corridor_id.to_string();

    let estimator = BarabasiOxbowEstimator::new(params.clone());

    println!("================================================================================");
    println!(" MURUA BARABÁSI-OXBOW ANALYTICAL ENGINE");
    println!(" Corridor: {}", corridor_id);
    println!("================================================================================");

    let ccbd_untracked = estimator.compute_ccbd(false);
    let ccbd_tracked = estimator.compute_ccbd(true);

    println!("Constructal-Barabási Diffusion Tensor Scores:");
    println!("  Tracked Main Channel Score:   {:.3}", ccbd_tracked.aggregate_ccbd);
    println!("  Untracked Oxbow Channel Score: {:.3}", ccbd_untracked.aggregate_ccbd);
    println!("  Effective Characteristic Tau0: {:.2} hours", estimator.effective_tau0);

    let p75 = estimator.calculate_p75_dwell();
    println!("  75th Percentile Dwell Cutoff:  {:.2} hours", p75);

    println!("\nWaiting Time Density Sample P(tau_w):");
    for &h in &[6.0, 12.0, 24.0, 36.0, 48.0, 72.0, 96.0, 120.0, 168.0] {
        let pdf = estimator.oxbow_waiting_density(h);
        let cdf = estimator.cumulative_waiting_prob(h);
        println!("  At {:>3.0}h: PDF = {:>10.6}, CDF = {:>6.2}%", h, pdf, cdf * 100.0);
    }

    let now = Utc::now();
    let pickup = now - Duration::days(7);
    let _shipped = pickup - Duration::hours(36);
    let cutoff = now + Duration::hours(72);

    let pred = estimator.predict_delivery_window(
        "58b73b08",
        pickup,
        now,
        now + Duration::hours(18),
        now + Duration::hours(22),
        cutoff,
    );

    println!("\nDelivery Prediction for Item A (58b73b08):");
    println!("  Completed Business Days: {:.1}", pred.completed_business_days);
    println!("  Next Window Single Prob: {:.1}%", pred.prob_next_window_single * 100.0);
    println!("  Next Window Joint Prob:  {:.1}%", pred.prob_next_window_joint * 100.0);
    println!("  Residual Oxbow Spillover:{:.1}%", pred.residual_spillover_prob * 100.0);
    println!("  Dispute Lock Deadline:   {}", pred.escrow_dispute_lock_deadline_utc.to_rfc3339());
    println!("================================================================================");
}
