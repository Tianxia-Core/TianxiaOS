// ffp: TX-WSS-FEED concurrent-daemon rust
//! Free Coinbase WSS depth feed — augments tx_market_feed.py REST snapshots.
//! Converted from tx_wss_feed.py.
//!
//! Transport: blocking tungstenite client with rustls + webpki roots, so both
//! `ws://` and `wss://` endpoints are supported. TLS handshake, RFC 6455
//! framing, masking, ping/pong, close and fragmentation are handled by
//! tungstenite. Override the endpoint with TX_WSS_URL (no CLI change).
use serde_json::{json, Value};
use std::env;
use std::io;
use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process;
use std::time::Duration;
use tungstenite::error::Error as WsError;
use tungstenite::stream::MaybeTlsStream;
use tungstenite::{connect, Message, WebSocket};

const DEFAULT_WSS_URL: &str = "wss://advanced-trade-ws.coinbase.com";
const SYMBOLS: [&str; 3] = ["BTC-USD", "ETH-USD", "SOL-USD"];
const READ_TICK: Duration = Duration::from_secs(2);

fn base_dir() -> PathBuf {
    PathBuf::from(
        env::var("TX_BASE_DIR")
            .ok()
            .filter(|v| !v.trim().is_empty())
            .unwrap_or_else(|| "/var/lib/tianxia".into()),
    )
}

fn halted(base: &Path) -> bool {
    base.join("AUTONOMY_PAUSED").exists()
        || base.join("PROBE_STOP").exists()
        || Path::new("/var/lib/tianxia/AUTONOMY_PAUSED").exists()
        || Path::new("/var/lib/tianxia/PROBE_STOP").exists()
}

#[allow(unreachable_patterns)]
fn configure_stream(ws: &mut WebSocket<MaybeTlsStream<TcpStream>>) {
    let stream = match ws.get_mut() {
        MaybeTlsStream::Plain(s) => s,
        MaybeTlsStream::Rustls(s) => &mut s.sock,
        _ => return,
    };
    let _ = stream.set_read_timeout(Some(READ_TICK));
    let _ = stream.set_write_timeout(Some(READ_TICK));
    let _ = stream.set_nodelay(true);
}

fn handle_text(data: &[u8]) {
    let txt = String::from_utf8_lossy(data);
    match serde_json::from_str::<Value>(&txt) {
        Ok(d) => {
            if d.get("type").and_then(|v| v.as_str()) == Some("l2update") {
                let product = d
                    .get("product_id")
                    .and_then(|v| v.as_str())
                    .unwrap_or("?");
                let n = d
                    .get("changes")
                    .and_then(|v| v.as_array())
                    .map(|a| a.len())
                    .unwrap_or(0);
                println!("[WSS] {} bids={}", product, n);
            } else if d.get("channel").and_then(|v| v.as_str()) == Some("l2_data") {
                if let Some(events) = d.get("events").and_then(|v| v.as_array()) {
                    for event in events {
                        let product = event
                            .get("product_id")
                            .and_then(|v| v.as_str())
                            .unwrap_or("?");
                        let n = event
                            .get("updates")
                            .and_then(|v| v.as_array())
                            .map(|a| a.len())
                            .unwrap_or(0);
                        println!("[WSS] {} bids={}", product, n);
                    }
                }
            }
        }
        Err(e) => eprintln!("[tx_wss_feed] malformed frame payload: {}", e),
    }
}

fn run_ws(url: &str, base: &Path) -> Result<(), Box<dyn std::error::Error>> {
    println!("[tx_wss_feed] connecting to {}", url);
    let (mut ws, _resp) = connect(url)?;
    configure_stream(&mut ws);
    println!(
        "[tx_wss_feed] websocket upgrade complete; subscribing level2 for {:?}",
        SYMBOLS
    );
    let sub = json!({"type": "subscribe", "product_ids": SYMBOLS, "channel": "level2"}).to_string();
    ws.send(Message::text(sub))?;

    loop {
        if halted(base) {
            println!("[tx_wss_feed] halted by kill-switch");
            let _ = ws.close(None);
            return Ok(());
        }
        match ws.read() {
            Ok(Message::Text(txt)) => handle_text(txt.as_bytes()),
            Ok(Message::Binary(_)) | Ok(Message::Pong(_)) | Ok(Message::Frame(_)) => {}
            Ok(Message::Ping(payload)) => {
                let _ = ws.send(Message::Pong(payload));
            }
            Ok(Message::Close(frame)) => {
                println!("[tx_wss_feed] close frame received; stream complete");
                let _ = ws.send(Message::Close(frame));
                return Ok(());
            }
            Err(WsError::Io(ref e))
                if matches!(
                    e.kind(),
                    io::ErrorKind::WouldBlock
                        | io::ErrorKind::TimedOut
                        | io::ErrorKind::Interrupted
                ) => {}
            Err(WsError::ConnectionClosed)
            | Err(WsError::AlreadyClosed)
            | Err(WsError::Protocol(
                tungstenite::error::ProtocolError::ResetWithoutClosingHandshake,
            )) => {
                println!("[tx_wss_feed] stream closed by server");
                return Ok(());
            }
            Err(e) => return Err(Box::new(e)),
        }
    }
}

fn main() {
    let base = base_dir();
    let url = env::var("TX_WSS_URL")
        .ok()
        .filter(|v| !v.trim().is_empty())
        .unwrap_or_else(|| DEFAULT_WSS_URL.to_string());

    if !url.starts_with("ws://") && !url.starts_with("wss://") {
        eprintln!("[tx_wss_feed] unsupported URL scheme: {}", url);
        process::exit(1);
    }
    if halted(&base) {
        println!("[tx_wss_feed] halted by kill-switch");
        return;
    }
    if let Err(e) = run_ws(&url, &base) {
        eprintln!(
            "[tx_wss_feed] endpoint unreachable or stream failed: {} — exiting gracefully",
            e
        );
    }
}
