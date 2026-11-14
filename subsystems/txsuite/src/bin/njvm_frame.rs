// ffp: TX-NJVM-FRAME wire-codec rust
//! 32B NJ-VM telemetry frame codec. Converted from tx_njvm_frame.py.
//! [0..2]=magic 0x4E4A, [2]=opcode, [3]=rank, [4..12]=u64 node,
//! [12..28]=16B payload, [28..32]=CRC-32 IEEE (matches python zlib.crc32).
use std::process::exit;

const MAGIC: [u8; 2] = [0x4E, 0x4A];
const FRAME_LEN: usize = 32;

fn kind(op: u8) -> Option<&'static str> {
    match op {
        0x01 => Some("bindu"),
        0x02 => Some("enclosure"),
        0x03 => Some("vector"),
        0x04 => Some("wire"),
        _ => None,
    }
}

fn crc32_ieee(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &b in data {
        crc ^= b as u32;
        for _ in 0..8 {
            if crc & 1 != 0 {
                crc = (crc >> 1) ^ 0xEDB8_8320;
            } else {
                crc >>= 1;
            }
        }
    }
    !crc
}

pub fn fnv1a(data: &[u8]) -> u64 {
    let mut h: u64 = 0xCBF2_9CE4_8422_2325;
    for &b in data {
        h ^= b as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01B3);
    }
    h
}

fn pack(op: u8, rank: u8, node: u64, payload: &[u8]) -> Result<Vec<u8>, String> {
    if kind(op).is_none() {
        return Err(format!("bad op {:#x}", op));
    }
    if rank > 7 {
        return Err(format!("rank {} outside R0-R7", rank));
    }
    if payload.len() != 16 {
        return Err("payload must be 16B".into());
    }
    let mut f = Vec::with_capacity(FRAME_LEN);
    f.extend_from_slice(&MAGIC);
    f.push(op);
    f.push(rank);
    f.extend_from_slice(&node.to_le_bytes());
    f.extend_from_slice(payload);
    let crc = crc32_ieee(&f);
    f.extend_from_slice(&crc.to_le_bytes());
    Ok(f)
}

fn unpack(frame: &[u8]) -> Result<(u8, u8, u64, [u8; 16]), String> {
    if frame.len() != FRAME_LEN {
        return Err(format!("frame must be {}B, got {}", FRAME_LEN, frame.len()));
    }
    if frame[0..2] != MAGIC {
        return Err("magic mismatch".into());
    }
    let op = frame[2];
    let rank = frame[3];
    if kind(op).is_none() {
        return Err(format!("bad op {:#x}", op));
    }
    let mut nb = [0u8; 8];
    nb.copy_from_slice(&frame[4..12]);
    let node = u64::from_le_bytes(nb);
    let mut payload = [0u8; 16];
    payload.copy_from_slice(&frame[12..28]);
    let mut cb = [0u8; 4];
    cb.copy_from_slice(&frame[28..32]);
    let crc = u32::from_le_bytes(cb);
    if crc32_ieee(&frame[..28]) != crc {
        return Err("crc mismatch".into());
    }
    Ok((op, rank, node, payload))
}

fn hex_encode(b: &[u8]) -> String {
    b.iter().map(|x| format!("{:02x}", x)).collect()
}

fn hex_decode(s: &str) -> Option<Vec<u8>> {
    let s = s.trim();
    if s.len() % 2 != 0 {
        return None;
    }
    let bytes = s.as_bytes();
    let mut out = Vec::with_capacity(s.len() / 2);
    let mut i = 0;
    while i < bytes.len() {
        let hi = (bytes[i] as char).to_digit(16)?;
        let lo = (bytes[i + 1] as char).to_digit(16)?;
        out.push((hi * 16 + lo) as u8);
        i += 2;
    }
    Some(out)
}

fn arg_val(args: &[String], key: &str) -> Option<String> {
    args.iter().position(|a| a == key).and_then(|i| args.get(i + 1).cloned())
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: njvm_frame pack --op N --rank N --node N --payload-hex HEX | unpack --hex HEX | scan --hex HEX | selftest");
        exit(64);
    }
    match args[1].as_str() {
        "pack" => {
            let op: u8 = arg_val(&args, "--op").and_then(|v| v.parse().ok()).unwrap_or(0);
            let rank: u8 = arg_val(&args, "--rank").and_then(|v| v.parse().ok()).unwrap_or(0);
            let node: u64 = arg_val(&args, "--node").and_then(|v| v.parse().ok()).unwrap_or(0);
            let payload = arg_val(&args, "--payload-hex")
                .and_then(|h| hex_decode(&h))
                .unwrap_or_default();
            match pack(op, rank, node, &payload) {
                Ok(f) => println!("{}", hex_encode(&f)),
                Err(e) => {
                    eprintln!("pack error: {}", e);
                    exit(2);
                }
            }
        }
        "unpack" => {
            let hex = arg_val(&args, "--hex").unwrap_or_default();
            let frame = match hex_decode(&hex) {
                Some(f) => f,
                None => {
                    eprintln!("invalid hex");
                    exit(2);
                }
            };
            match unpack(&frame) {
                Ok((op, rank, node, payload)) => {
                    println!(
                        "{{\"op\":{},\"kind\":\"{}\",\"rank\":{},\"node\":{},\"payload\":\"{}\"}}",
                        op,
                        kind(op).unwrap(),
                        rank,
                        node,
                        hex_encode(&payload)
                    );
                }
                Err(e) => {
                    eprintln!("unpack error: {}", e);
                    exit(2);
                }
            }
        }
        "scan" => {
            let hex = arg_val(&args, "--hex").unwrap_or_default();
            let buf = match hex_decode(&hex) {
                Some(f) => f,
                None => {
                    eprintln!("invalid hex");
                    exit(2);
                }
            };
            let mut out = vec![];
            let mut i = 0usize;
            while i + FRAME_LEN <= buf.len() {
                if buf[i..i + 2] == MAGIC {
                    if let Ok((op, rank, node, _)) = unpack(&buf[i..i + FRAME_LEN]) {
                        out.push(format!(
                            "{{\"offset\":{},\"op\":{},\"kind\":\"{}\",\"rank\":{},\"node\":{}}}",
                            i,
                            op,
                            kind(op).unwrap(),
                            rank,
                            node
                        ));
                        i += FRAME_LEN;
                        continue;
                    }
                }
                i += 1;
            }
            println!("[{}]", out.join(","));
        }
        "selftest" => {
            let f = pack(3, 5, 42, &[7u8; 16]).expect("pack");
            let (op, rank, node, _) = unpack(&f).expect("unpack");
            let mut tampered = f.clone();
            tampered[12] ^= 0xFF;
            let caught = unpack(&tampered).is_err();
            let _ = crc32_ieee(b"123456789");
            let fnv = fnv1a(b"tx");
            println!(
                "selftest: op={} rank={} node={} tamper_caught={} fnv1a={:x}",
                op, rank, node, caught, fnv
            );
            if op != 3 || rank != 5 || node != 42 || !caught {
                exit(1);
            }
        }
        other => {
            eprintln!("unknown command {}", other);
            exit(64);
        }
    }
}
