// ffp: TX-WORKER-AUTOSCALER concurrent-daemon rust
//! Elastic NATS worker autoscaler with thermal/load throttling.
//! Converted from tx_worker_autoscaler.py. Adds the missing kill-switch.
use serde_json::Value;
use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::net::TcpStream;
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::thread::sleep;
use std::time::{Duration, Instant};

const STREAM_NAME: &str = "TIANXIA_TASKS";
const CONSUMER_GROUP: &str = "TIANXIA_WORKERS";
const NATS_HOST: &str = "127.0.0.1";
const NATS_PORT: u16 = 4222;
const MIN_WORKERS: usize = 1;
const MAX_WORKERS: usize = 6;
const SCALE_DOWN_COOLDOWN: f64 = 12.0;
const TEMP_THROTTLE_C: f64 = 78.0;
const TEMP_CRITICAL_C: f64 = 88.0;
const LOAD_FACTOR_THROTTLE: f64 = 1.35;

fn halted() -> bool {
    Path::new("/var/lib/tianxia/AUTONOMY_PAUSED").exists()
        || Path::new("/var/lib/tianxia/PROBE_STOP").exists()
}

fn system_health() -> (f64, f64, f64) {
    let mut max_temp = 0.0f64;
    for pat in ["/sys/class/thermal", "/sys/class/hwmon"] {
        if let Ok(rd) = fs::read_dir(pat) {
            for e in rd.flatten() {
                let dir = e.path();
                if let Ok(files) = fs::read_dir(&dir) {
                    for f in files.flatten() {
                        let name = f.file_name().to_string_lossy().to_string();
                        if name == "temp" || (name.starts_with("temp") && name.ends_with("_input")) {
                            if let Ok(t) = fs::read_to_string(f.path()) {
                                if let Ok(mut v) = t.trim().parse::<f64>() {
                                    if v > 1000.0 {
                                        v /= 1000.0;
                                    }
                                    if v > 0.0 && v < 130.0 && v > max_temp {
                                        max_temp = v;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    let load1 = fs::read_to_string("/proc/loadavg")
        .ok()
        .and_then(|t| t.split_whitespace().next().and_then(|v| v.parse::<f64>().ok()))
        .unwrap_or(0.0);
    let cores = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1) as f64;
    (max_temp, load1, cores)
}

struct NatsClient {
    stream: Option<TcpStream>,
    buffer: Vec<u8>,
}

impl NatsClient {
    fn new() -> Self {
        NatsClient { stream: None, buffer: vec![] }
    }

    fn connect(&mut self) -> bool {
        let addr = format!("{}:{}", NATS_HOST, NATS_PORT);
        match TcpStream::connect_timeout(&addr.parse().unwrap(), Duration::from_millis(2500)) {
            Ok(s) => {
                let _ = s.set_read_timeout(Some(Duration::from_millis(2000)));
                let _ = s.set_nodelay(true);
                self.stream = Some(s);
                let mut buf = [0u8; 4096];
                if let Some(st) = self.stream.as_mut() {
                    let _ = st.read(&mut buf);
                    let _ = st.write_all(b"CONNECT {\"verbose\":false,\"pedantic\":false,\"protocol\":1}\r\n");
                }
                true
            }
            Err(_) => {
                self.stream = None;
                false
            }
        }
    }

    fn backlog(&mut self) -> Option<(i64, i64)> {
        if self.stream.is_none() && !self.connect() {
            return None;
        }
        let inbox = format!("_INBOX.scale_req.{}", Instant::now().elapsed().as_nanos());
        let subject = format!("$JS.API.CONSUMER.INFO.{}.{}", STREAM_NAME, CONSUMER_GROUP);
        {
            let st = self.stream.as_mut()?;
            let _ = st.write_all(format!("SUB {} 99\r\n", inbox).as_bytes());
            let _ = st.write_all(format!("PUB {} {} 2\r\n{{}}\r\n", subject, inbox).as_bytes());
        }
        let deadline = Instant::now() + Duration::from_secs(2);
        while Instant::now() < deadline {
            let mut buf = [0u8; 4096];
            if let Some(st) = self.stream.as_mut() {
                match st.read(&mut buf) {
                    Ok(0) => break,
                    Ok(n) => self.buffer.extend_from_slice(&buf[..n]),
                    Err(_) => break,
                }
            }
            if let Some(pos) = self.buffer.windows(2).position(|w| w == b"\r\n") {
                let line = String::from_utf8_lossy(&self.buffer[..pos]).to_string();
                self.buffer.drain(..pos + 2);
                if line.starts_with("MSG ") {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    let len: usize = parts.last().and_then(|v| v.parse().ok()).unwrap_or(0);
                    let deadline2 = Instant::now() + Duration::from_secs(2);
                    while self.buffer.len() < len && Instant::now() < deadline2 {
                        let mut b2 = [0u8; 4096];
                        if let Some(st) = self.stream.as_mut() {
                            if let Ok(n) = st.read(&mut b2) {
                                self.buffer.extend_from_slice(&b2[..n]);
                            }
                        }
                    }
                    let msg = String::from_utf8_lossy(&self.buffer[..len]).to_string();
                    self.buffer.drain(..(len + 2).min(self.buffer.len()));
                    if let Some(st) = self.stream.as_mut() {
                        let _ = st.write_all(b"UNSUB 99\r\n");
                    }
                    if let Ok(v) = serde_json::from_str::<Value>(&msg) {
                        return Some((
                            v.get("num_pending").and_then(|x| x.as_i64()).unwrap_or(0),
                            v.get("num_ack_pending").and_then(|x| x.as_i64()).unwrap_or(0),
                        ));
                    }
                    return None;
                }
            }
        }
        None
    }
}

struct Workers {
    children: BTreeMap<usize, Child>,
}

impl Workers {
    fn start(&mut self, idx: usize) {
        let w_id = format!("latitude-w{}", idx);
        let py = "/var/lib/tianxia/venv/timesfm/bin/python";
        if let Ok(child) = Command::new(py)
            .args(["-u", "/var/lib/tianxia/bin/tx_workqueue_engine.py",
                   "--mode", "worker", &format!("--worker-id={}", w_id), "--server", "127.0.0.1"])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
        {
            println!("[{}] [SCALE UP] Spawned worker #{} (PID {}) -> Active: {}",
                     now_hms(), idx, child.id(), self.children.len() + 1);
            self.children.insert(idx, child);
        }
    }

    fn stop(&mut self, idx: usize) {
        if let Some(mut child) = self.children.remove(&idx) {
            let _ = child.kill();
            let _ = child.wait();
            println!("[{}] [SCALE DOWN] Reaped worker #{} -> Active: {}", now_hms(), idx, self.children.len());
        }
    }
}

fn now_hms() -> String {
    Command::new("date").arg("+%H:%M:%S")
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

fn calculate_target(pending: i64, cur: usize, temp: f64, load1: f64, cores: f64) -> usize {
    let mut target = if pending >= 250 {
        MAX_WORKERS
    } else if pending >= 120 {
        4
    } else if pending >= 30 {
        3
    } else if pending >= 5 {
        2
    } else {
        MIN_WORKERS
    };
    if temp >= TEMP_CRITICAL_C {
        println!("[!] [THERMAL CRITICAL] {:.1}°C >= {}°C — shedding to {}", temp, TEMP_CRITICAL_C, MIN_WORKERS);
        return MIN_WORKERS;
    }
    if temp >= TEMP_THROTTLE_C && target > cur {
        println!("[-] [THERMAL THROTTLE] {:.1}°C — freezing scale-up at {}", temp, cur);
        target = cur;
    }
    let max_load = cores * LOAD_FACTOR_THROTTLE;
    if load1 >= max_load && target > cur {
        println!("[-] [LOAD THROTTLE] load {:.2} >= {:.2} — freezing at {}", load1, max_load, cur);
        target = cur;
    }
    target.clamp(MIN_WORKERS, MAX_WORKERS)
}

fn main() {
    let (t, _l, cores) = system_health();
    println!("[*] Tianxia Elastic Autoscaler (rust) [Cores: {:.0} | Max: {}w | Baseline: {:.1}°C]",
             cores, MAX_WORKERS, t);
    let mut workers = Workers { children: BTreeMap::new() };
    for i in 1..=MIN_WORKERS {
        workers.start(i);
    }
    let mut client = NatsClient::new();
    let mut last_high_backlog = Instant::now();

    while !halted() {
        let dead: Vec<usize> = workers.children.iter_mut()
            .filter_map(|(idx, c)| c.try_wait().ok().flatten().map(|_| *idx))
            .collect();
        for idx in dead {
            println!("[!] Worker #{} exited — restarting", idx);
            workers.children.remove(&idx);
            workers.start(idx);
        }
        if let Some((pending, _ack)) = client.backlog() {
            let (temp, load1, cores) = system_health();
            let cur = workers.children.len();
            let target = calculate_target(pending, cur, temp, load1, cores);
            if pending > 0 {
                last_high_backlog = Instant::now();
            }
            if target > cur {
                for idx in 1..=MAX_WORKERS {
                    if !workers.children.contains_key(&idx) && workers.children.len() < target {
                        workers.start(idx);
                    }
                }
            } else if target < cur && last_high_backlog.elapsed().as_secs_f64() >= SCALE_DOWN_COOLDOWN {
                let idxs: Vec<usize> = workers.children.keys().rev().cloned().collect();
                for idx in idxs {
                    if workers.children.len() > target && workers.children.len() > MIN_WORKERS {
                        workers.stop(idx);
                    }
                }
            }
        }
        sleep(Duration::from_secs(1));
    }
    for idx in workers.children.keys().cloned().collect::<Vec<_>>() {
        workers.stop(idx);
    }
    println!("[*] Autoscaler halted by kill-switch");
}
