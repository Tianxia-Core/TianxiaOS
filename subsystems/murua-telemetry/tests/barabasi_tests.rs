// ffp: FFP-MURUA-TEST-BARABASI test rust
use chrono::{Duration, TimeZone, Utc};
use murua_architecture_enhancement::barabasi::{
    BarabasiOxbowEstimator, CorridorParameters,
};

#[test]
fn test_ccbd_tensor_calculation() {
    let params = CorridorParameters::default();
    let estimator = BarabasiOxbowEstimator::new(params.clone());

    let ccbd_tracked = estimator.compute_ccbd(true);
    let ccbd_untracked = estimator.compute_ccbd(false);

    assert!(ccbd_tracked.edi_active);
    assert!(!ccbd_untracked.edi_active);

    // Tracked channel has high volume with locker injection (~11500)
    assert!(ccbd_tracked.aggregate_ccbd > 1000.0);
    // Untracked oxbow channel is constrained by queue drag and low CFC pass-through
    assert!(ccbd_untracked.aggregate_ccbd > 0.0);
    assert!(ccbd_untracked.aggregate_ccbd < ccbd_tracked.aggregate_ccbd);
}

#[test]
fn test_barabasi_waiting_density_decay() {
    let params = CorridorParameters::default();
    let estimator = BarabasiOxbowEstimator::new(params);

    let pdf_2h = estimator.oxbow_waiting_density(2.0);
    let pdf_24h = estimator.oxbow_waiting_density(24.0);
    let pdf_72h = estimator.oxbow_waiting_density(72.0);

    // Power law with negative exponent -1.5 ensures strict monotonic decay
    assert!(pdf_2h > pdf_24h);
    assert!(pdf_24h > pdf_72h);

    // Boundary condition: wait time <= 1.0 hour produces zero density
    assert_eq!(estimator.oxbow_waiting_density(0.5), 0.0);
    assert_eq!(estimator.oxbow_waiting_density(1.0), 0.0);
}

#[test]
fn test_heddle_p75_escalation_detection() {
    let params = CorridorParameters::default();
    let estimator = BarabasiOxbowEstimator::new(params);

    let p75 = estimator.calculate_p75_dwell();
    assert!(p75 > 5.0 && p75 < 200.0);

    let now = Utc::now();
    let pickup_recent = now - Duration::hours(10);
    let shipped_recent = pickup_recent - Duration::hours(12);

    let decomp_recent = estimator.evaluate_heddle_escalation(
        "TEST_RECENT",
        shipped_recent,
        pickup_recent,
        now,
    );
    assert!(!decomp_recent.priority_escalation_required);

    // After 9 days (~216h), dwell far exceeds P75 and requires priority escalation
    let pickup_old = now - Duration::days(9);
    let shipped_old = pickup_old - Duration::hours(24);

    let decomp_old = estimator.evaluate_heddle_escalation(
        "TEST_STAGNANT",
        shipped_old,
        pickup_old,
        now,
    );
    assert!(decomp_old.priority_escalation_required);
    assert_eq!(decomp_old.status, "PRIORITY_ESCALATION_REQUIRED_SLA_BREACH_RISK");
}

#[test]
fn test_kandeteenus_delivery_window() {
    // Wednesday 13:00 UTC -> 15:00 EET (within [11:30, 16:00] window)
    let wed_13 = Utc.with_ymd_and_hms(2026, 11, 4, 13, 0, 0).unwrap();
    assert!(BarabasiOxbowEstimator::is_kandeteenus_active(wed_13));

    // Wednesday 18:00 UTC -> 20:00 EET (outside window)
    let wed_18 = Utc.with_ymd_and_hms(2026, 11, 4, 18, 0, 0).unwrap();
    assert!(!BarabasiOxbowEstimator::is_kandeteenus_active(wed_18));

    // Sunday 13:00 UTC -> Weekend letter blackout
    let sun_13 = Utc.with_ymd_and_hms(2026, 11, 1, 13, 0, 0).unwrap();
    assert!(!BarabasiOxbowEstimator::is_kandeteenus_active(sun_13));
}

#[test]
fn test_prediction_calibration_day_8() {
    let params = CorridorParameters::default();
    let estimator = BarabasiOxbowEstimator::new(params);

    let pickup = Utc.with_ymd_and_hms(2026, 10, 27, 11, 0, 0).unwrap();
    let evaluate_time = Utc.with_ymd_and_hms(2026, 11, 5, 17, 25, 0).unwrap();
    let target_win_start = Utc.with_ymd_and_hms(2026, 11, 6, 9, 30, 0).unwrap();
    let target_win_end = Utc.with_ymd_and_hms(2026, 11, 6, 14, 0, 0).unwrap();
    let auto_fin = Utc.with_ymd_and_hms(2026, 11, 9, 12, 10, 0).unwrap();

    let pred = estimator.predict_delivery_window(
        "58b73b08",
        pickup,
        evaluate_time,
        target_win_start,
        target_win_end,
        auto_fin,
    );

    // Business day 8 prediction calibration: 91.2% single, 86.4% joint
    assert_eq!(pred.completed_business_days, 7.0);
    assert!((pred.prob_next_window_single - 0.912).abs() < 0.01);
    assert!((pred.prob_next_window_joint - 0.864).abs() < 0.01);
    assert!((pred.residual_spillover_prob - 0.088).abs() < 0.01);

    // Escrow dispute lock deadline must be exactly 48h before auto-fin
    let expected_lock = auto_fin - Duration::hours(48);
    assert_eq!(pred.escrow_dispute_lock_deadline_utc, expected_lock);
}
