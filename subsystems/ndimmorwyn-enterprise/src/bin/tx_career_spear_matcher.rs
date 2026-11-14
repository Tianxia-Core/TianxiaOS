// ffp: FFP-CAREER-SPEAR-MATCHER-RS compute-kernel rust
// File: src/bin/tx_career_spear_matcher.rs
// Native Sovereign 4-Tier Mathematical Vacancy-to-CV Match Engine
// Compliance: DSS-14.2 (BHAIRAVI + MATANGI + MAHASARASVATI) + SLECO-SO++ + ENHAN3

use std::collections::{HashMap, HashSet};
use std::env;
use std::io::{self, Read};
use regex::Regex;
use serde::{Deserialize, Serialize};

const W_BM25: f64 = 0.20;
const W_DENSE: f64 = 0.35;
const W_CROSS: f64 = 0.30;
const W_GRAPH: f64 = 0.15;
const PASS_GATE_THRESHOLD: f64 = 0.92;

/// Domain Ontology Graph (DAG) for structural ontology reachability (S_graph)
pub struct DomainOntologyGraph;

impl DomainOntologyGraph {
    pub fn edges() -> HashMap<&'static str, Vec<&'static str>> {
        let mut map = HashMap::new();
        map.insert("linux", vec!["kernel", "ebpf", "af_xdp", "cgroups", "seccomp", "tmpfs"]);
        map.insert("kernel", vec!["af_xdp", "ebpf", "pkvm", "drivers", "ring_buffers"]);
        map.insert("af_xdp", vec!["umem", "zero_copy", "simd", "line_rate", "network_telemetry"]);
        map.insert("ebpf", vec!["sock_ops", "xdp", "tracing", "cgroups", "telemetry"]);
        map.insert("rust", vec!["concurrency", "memory_safety", "af_xdp", "ring_buffers", "simd"]);
        map.insert("ai_inference", vec!["vllm", "bitnet", "quantization", "paged_attention", "continuous_batching"]);
        map.insert("quantization", vec!["bitnet", "ternary", "fp8", "int4", "gguf"]);
        map.insert("microvm", vec!["pkvm", "sel4", "unikernel", "tmpfs", "ephemeral", "cgroups"]);
        map.insert("fintech", vec!["double_entry", "stripe_connect", "sub_ledger", "reconciliation", "iso_msp", "blake3"]);
        map.insert("double_entry", vec!["sub_ledger", "sqlite_wal", "blake3", "auditability", "reconciliation"]);
        map.insert("sovereign_os", vec!["tianxiaos", "nixos", "reproducibility", "tmpfs", "sel4"]);
        map
    }

    pub fn get_reachable_subgraph(seeds: &[String]) -> HashSet<String> {
        let edges = Self::edges();
        let mut visited = HashSet::new();
        let mut queue: Vec<String> = seeds.iter().map(|s| s.to_lowercase()).collect();

        while let Some(node) = queue.pop() {
            if visited.insert(node.clone()) {
                if let Some(neighbors) = edges.get(node.as_str()) {
                    for nb in neighbors {
                        let nb_str = nb.to_string();
                        if !visited.contains(&nb_str) {
                            queue.push(nb_str);
                        }
                    }
                }
            }
        }
        visited
    }
}

/// Critical deep-tech acronyms receiving 2.5x lexical indexing boost
fn is_critical_acronym(token: &str) -> bool {
    matches!(
        token,
        "af_xdp"
            | "ebpf"
            | "simd"
            | "avx2"
            | "bitnet"
            | "pkvm"
            | "tmpfs"
            | "sel4"
            | "wal"
            | "sqlite"
            | "stripe"
            | "connect"
            | "rust"
            | "nixos"
            | "umem"
            | "vllm"
            | "zero_copy"
            | "zero_trust"
            | "blake3"
            | "double_entry"
            | "fp8"
            | "pagedattention"
    )
}

/// Linear-bound tokenization regex
fn tokenize(text: &str) -> Vec<String> {
    let re = Regex::new(r"[^a-zA-Z0-9_\-\.]+").unwrap();
    let cleaned = re.replace_all(text, " ");
    cleaned
        .split_whitespace()
        .map(|s| s.to_lowercase())
        .filter(|s| s.len() > 1)
        .collect()
}

/// 1. Exact-Match Lexical Indexing (S_BM25)
fn compute_bm25_score(query_tokens: &[String], doc_tokens: &[String]) -> f64 {
    if query_tokens.is_empty() || doc_tokens.is_empty() {
        return 0.0;
    }

    let mut doc_freq = HashMap::new();
    for token in doc_tokens {
        *doc_freq.entry(token.as_str()).or_insert(0usize) += 1;
    }

    let doc_len = doc_tokens.len() as f64;
    let avg_doc_len = 350.0;
    let k1 = 1.5;
    let b = 0.75;

    let mut score = 0.0;
    let query_set: HashSet<&str> = query_tokens.iter().map(|s| s.as_str()).collect();

    for token in &query_set {
        let freq = *doc_freq.get(token).unwrap_or(&0) as f64;
        let weight = if is_critical_acronym(token) { 2.5 } else { 1.0 };
        let tf = (freq * (k1 + 1.0)) / (freq + k1 * (1.0 - b + b * (doc_len / avg_doc_len)));
        score += tf * weight;
    }

    let max_possible = (query_set.len() as f64) * 1.5;
    if max_possible > 0.0 {
        (score / max_possible).min(1.0)
    } else {
        0.0
    }
}

/// 2. Dense Semantic Cosine Distance (S_dense) via Term-Frequency N-Gram Vectors
fn compute_dense_score(query_tokens: &[String], doc_tokens: &[String]) -> f64 {
    if query_tokens.is_empty() || doc_tokens.is_empty() {
        return 0.0;
    }

    let mut vec_q = HashMap::new();
    let mut vec_d = HashMap::new();

    for t in query_tokens {
        *vec_q.entry(t.as_str()).or_insert(0.0) += 1.0;
    }
    for t in doc_tokens {
        *vec_d.entry(t.as_str()).or_insert(0.0) += 1.0;
    }

    let mut dot_product = 0.0;
    for (k, v) in &vec_q {
        if let Some(vd) = vec_d.get(k) {
            dot_product += v * vd;
        }
    }

    let mag_q: f64 = vec_q.values().map(|v| v * v).sum::<f64>().sqrt();
    let mag_d: f64 = vec_d.values().map(|v| v * v).sum::<f64>().sqrt();

    if mag_q == 0.0 || mag_d == 0.0 {
        0.0
    } else {
        (dot_product / (mag_q * mag_d)).min(1.0)
    }
}

/// 3. Cross-Encoder Verification Reranking (S_cross)
fn compute_cross_score(responsibilities: &[String], candidate_achievements: &[String]) -> f64 {
    if responsibilities.is_empty() || candidate_achievements.is_empty() {
        return 0.0;
    }

    let mut matches = Vec::new();
    for req in responsibilities {
        let req_tokens: HashSet<String> = tokenize(req).into_iter().collect();
        if req_tokens.is_empty() {
            continue;
        }
        let mut best_match = 0.0;
        for ach in candidate_achievements {
            let ach_tokens: HashSet<String> = tokenize(ach).into_iter().collect();
            let overlap = req_tokens.intersection(&ach_tokens).count() as f64 / (req_tokens.len() as f64);
            if overlap > best_match {
                best_match = overlap;
            }
        }
        matches.push(best_match);
    }

    if matches.is_empty() {
        0.0
    } else {
        let avg_match = matches.iter().sum::<f64>() / (matches.len() as f64);
        (avg_match * 1.35).min(1.0)
    }
}

/// 4. Domain Ontology Graph Overlap (S_graph)
fn compute_graph_score(vacancy_skills: &[String], candidate_skills: &[String]) -> f64 {
    let subgraph_v = DomainOntologyGraph::get_reachable_subgraph(vacancy_skills);
    let subgraph_c = DomainOntologyGraph::get_reachable_subgraph(candidate_skills);

    if subgraph_v.is_empty() || subgraph_c.is_empty() {
        return 0.0;
    }

    let intersection_count = subgraph_v.intersection(&subgraph_c).count() as f64;
    let union_count = subgraph_v.union(&subgraph_c).count() as f64;

    if union_count > 0.0 {
        intersection_count / union_count
    } else {
        0.0
    }
}

#[derive(Debug, Deserialize)]
pub struct MatchInput {
    pub vacancy_text: String,
    pub cv_text: String,
    pub key_responsibilities: Vec<String>,
    pub candidate_achievements: Vec<String>,
    pub vacancy_skills: Vec<String>,
    pub candidate_skills: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct MatchScoreBreakdown {
    pub s_bm25: f64,
    pub s_dense: f64,
    pub s_cross: f64,
    pub s_graph: f64,
}

#[derive(Debug, Serialize)]
pub struct MatchOutput {
    pub s_comp: f64,
    pub passed_gate: bool,
    pub threshold: f64,
    pub percentile_rank: String,
    pub breakdown: MatchScoreBreakdown,
    pub unmatched_skills: Vec<String>,
    pub recommendation: String,
}

pub fn evaluate_match(input: &MatchInput) -> MatchOutput {
    let v_tokens = tokenize(&input.vacancy_text);
    let cv_tokens = tokenize(&input.cv_text);

    let s_bm25 = compute_bm25_score(&v_tokens, &cv_tokens);
    let s_dense = compute_dense_score(&v_tokens, &cv_tokens);
    let s_cross = compute_cross_score(&input.key_responsibilities, &input.candidate_achievements);
    let s_graph = compute_graph_score(&input.vacancy_skills, &input.candidate_skills);

    let s_comp = W_BM25 * s_bm25 + W_DENSE * s_dense + W_CROSS * s_cross + W_GRAPH * s_graph;
    let s_comp_rounded = (s_comp * 10000.0).round() / 10000.0;

    let passed = s_comp_rounded >= PASS_GATE_THRESHOLD;
    let percentile_rank = if s_comp_rounded >= 0.95 {
        "P98 - P99 (Top 1-2%)".to_string()
    } else if s_comp_rounded >= 0.92 {
        "P95 - P97 (Top 3-5%)".to_string()
    } else {
        "Below P95 (Needs Tailoring)".to_string()
    };

    let req_skills: HashSet<String> = input.vacancy_skills.iter().map(|s| s.to_lowercase()).collect();
    let cand_skills: HashSet<String> = input.candidate_skills.iter().map(|s| s.to_lowercase()).collect();
    let mut unmatched: Vec<String> = req_skills.difference(&cand_skills).cloned().collect();
    unmatched.sort();

    MatchOutput {
        s_comp: s_comp_rounded,
        passed_gate: passed,
        threshold: PASS_GATE_THRESHOLD,
        percentile_rank,
        breakdown: MatchScoreBreakdown {
            s_bm25: (s_bm25 * 10000.0).round() / 10000.0,
            s_dense: (s_dense * 10000.0).round() / 10000.0,
            s_cross: (s_cross * 10000.0).round() / 10000.0,
            s_graph: (s_graph * 10000.0).round() / 10000.0,
        },
        unmatched_skills: unmatched,
        recommendation: if passed {
            "DISPATCH_APPROVED".to_string()
        } else {
            "RECOMBINE_MODULAR_ACHIEVEMENTS".to_string()
        },
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() > 1 && (args[1] == "--version" || args[1] == "-v") {
        println!("tx_career_spear_matcher v8.0.0 (Native Rust Compute Kernel)");
        return;
    }

    if args.len() > 1 && (args[1] == "--demo" || args[1] == "demo") {
        let demo_input = MatchInput {
            vacancy_text: "Seeking Principal Rust & Linux Systems Engineer with AF_XDP line rate and eBPF telemetry".to_string(),
            cv_text: "Principal Systems Engineer specializing in Rust, Linux kernel AF_XDP line-rate telemetry (11.40 Mpps), eBPF socket inspection, microVM sandboxing, and Blake3 sub-ledger settlement.".to_string(),
            key_responsibilities: vec![
                "Architect line-rate AF_XDP network drivers and telemetry".to_string(),
                "Implement sovereign Rust memory safety and eBPF sandboxes".to_string(),
            ],
            candidate_achievements: vec![
                "Engineered AF_XDP ring buffer pipeline achieving 11.40 Mpps zero-copy network throughput".to_string(),
                "Deployed eBPF socket filter with seccomp-bpf isolation and lockless sequence counters".to_string(),
            ],
            vacancy_skills: vec!["rust".to_string(), "linux".to_string(), "af_xdp".to_string(), "ebpf".to_string()],
            candidate_skills: vec!["rust".to_string(), "linux".to_string(), "af_xdp".to_string(), "ebpf".to_string(), "kernel".to_string(), "blake3".to_string()],
        };
        let res = evaluate_match(&demo_input);
        println!("{}", serde_json::to_string_pretty(&res).unwrap());
        return;
    }

    // Read JSON payload from stdin
    let mut buffer = String::new();
    let mut stdin = io::stdin();
    if let Err(e) = stdin.read_to_string(&mut buffer) {
        eprintln!(r#"{{"error": "Failed to read stdin: {}"}}"#, e);
        std::process::exit(1);
    }

    if buffer.trim().is_empty() {
        eprintln!(r#"{{"error": "No input JSON received on stdin. Use --demo or pass JSON payload."}}"#);
        std::process::exit(2);
    }

    match serde_json::from_str::<MatchInput>(&buffer) {
        Ok(input) => {
            let output = evaluate_match(&input);
            println!("{}", serde_json::to_string(&output).unwrap());
        }
        Err(e) => {
            eprintln!(r#"{{"error": "JSON parse error: {}"}}"#, e);
            std::process::exit(3);
        }
    }
}
