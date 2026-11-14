// ffp: FFP-TST-006 test-polyglot-14core rust

use tianxiaos_polyglot_kenning::nimbus::NimbusSupervisor;

#[test]
fn test_nimbus_14core_matrix() {
    let supervisor = NimbusSupervisor::new();
    let status = supervisor.audit_nimbus_matrix();

    assert_eq!(status.total_cores, 14);
    assert_eq!(status.active_cores, 14);
    assert!(status.all_gates_compliant);
    assert_eq!(status.cores.len(), 14);
    assert!(!status.supervisor_signature_b3.is_empty());

    // Verify mapping of Rust, Zig, C++, OCaml, Go, Julia, Nim
    let core1 = supervisor.get_core(1).unwrap();
    assert_eq!(core1.assigned_language, "Rust");
    assert!(core1.bound_mahavidya_gate.contains("KALI"));

    let core2 = supervisor.get_core(2).unwrap();
    assert_eq!(core2.assigned_language, "Zig");
    assert!(core2.bound_mahavidya_gate.contains("BHAIRAVI"));

    let core3 = supervisor.get_core(3).unwrap();
    assert_eq!(core3.assigned_language, "C++ (AVX2/FMA)");
    assert!(core3.bound_mahavidya_gate.contains("PRATYANGIRA"));

    let core4 = supervisor.get_core(4).unwrap();
    assert_eq!(core4.assigned_language, "OCaml");
    assert!(core4.bound_mahavidya_gate.contains("BAGALAMUKHI"));

    let core5 = supervisor.get_core(5).unwrap();
    assert_eq!(core5.assigned_language, "Go");
    assert!(core5.bound_mahavidya_gate.contains("TARA"));

    let core6 = supervisor.get_core(6).unwrap();
    assert_eq!(core6.assigned_language, "Julia");
    assert!(core6.bound_mahavidya_gate.contains("TRIPURA"));

    let core7 = supervisor.get_core(7).unwrap();
    assert_eq!(core7.assigned_language, "Nim");
    assert!(core7.bound_mahavidya_gate.contains("BHUVANESVARI"));
}
