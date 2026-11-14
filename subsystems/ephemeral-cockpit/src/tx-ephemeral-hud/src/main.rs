use memmap2::MmapOptions;
use smithay_client_toolkit::{
    compositor::{CompositorHandler, CompositorState},
    delegate_compositor, delegate_keyboard, delegate_layer, delegate_output, delegate_pointer,
    delegate_registry, delegate_seat, delegate_shm,
    output::{OutputHandler, OutputState},
    registry::{ProvidesRegistryState, RegistryState},
    registry_handlers,
    seat::{
        keyboard::{KeyEvent, KeyboardHandler, Keysym, Modifiers},
        pointer::{PointerEvent, PointerEventKind, PointerHandler},
        Capability, SeatHandler, SeatState,
    },
    shell::{
        wlr_layer::{
            Anchor, KeyboardInteractivity, Layer, LayerShell, LayerShellHandler, LayerSurface,
            LayerSurfaceConfigure,
        },
        WaylandSurface,
    },
    shm::{slot::SlotPool, Shm, ShmHandler},
};
use std::{
    fs::OpenOptions,
    io::Write,
    os::unix::net::UnixStream,
    sync::atomic::{fence, Ordering},
};
use wayland_client::{
    globals::registry_queue_init,
    protocol::{wl_keyboard, wl_output, wl_pointer, wl_seat, wl_shm, wl_surface},
    Connection, QueueHandle,
};

// Rasa-X-Machina Brand Kit Palette (ARGB8888)
const COLOR_VOID_BG: u32 = 0xE0080808;      // #080808 @ 88% alpha (ignorealpha 0.15 safe)
const COLOR_SLATE_DIM: u32 = 0xD010161A;    // #10161A Inactive Column
const COLOR_CYAN_GLOW: u32 = 0xFF00F0FF;    // #00F0FF Active / Nominal / MANAS
const COLOR_EMBER_WARN: u32 = 0xFFFF5533;   // #FF5533 Delinquent / MicroVM / Alert
const COLOR_EMERALD_OK: u32 = 0xFF00FF66;   // #00FF66 Solvency Lock / Verified
const COLOR_TEXT_MAIN: u32 = 0xFFE6F7FF;    // Crisp HUD White-Cyan
const COLOR_TEXT_MUTED: u32 = 0xFF5A727C;   // Dimmed Spine Label

#[repr(u8)]
#[derive(Copy, Clone, PartialEq, Eq)]
pub enum IsolationPlane {
    NativeInspect = 0,
    ElasticNamespace = 1,
    EphemeralMicroVm = 2,
}

#[repr(C)]
#[derive(Copy, Clone)]
pub struct MenuNode {
    pub id: u32,
    pub parent_id: u32,
    pub tier: u8,
    pub isolation: u8,
    pub _pad: u16,
    pub status_color_rgb: u32,
    pub ephemeral_score_q16: u16,
    pub judgment_warn_flag: u16,
    pub label: [u8; 64],
    pub target_path: [u8; 128],
    pub telemetry_summary: [u8; 64],
}

#[repr(C)]
pub struct SharedMenuState {
    pub sequence_lock: u64,
    pub active_generation: u32,
    pub manas_latency_us: u32,
    pub node_count: u32,
    pub hot_node_indices: [u32; 3],
    pub nodes: [MenuNode; 256],
}

#[repr(C)]
pub struct BrokerDispatchPacket {
    pub magic: u32, // 0x54584F53 ("TXOS")
    pub node_id: u32,
    pub plane: u8,
    pub intent_len: u8,
    pub _reserved: u16,
    pub intent_query: [u8; 128],
}

struct TianxiaHud {
    registry_state: RegistryState,
    seat_state: SeatState,
    output_state: OutputState,
    shm: Shm,
    pool: SlotPool,
    layer_surface: LayerSurface,
    width: u32,
    height: u32,
    configured: bool,
    exit: bool,
    modifiers: Modifiers,
    selected_tier: usize,
    selected_row_per_tier: [usize; 5],
    intent_buffer: String,
    shm_map: Option<memmap2::Mmap>,
    fallback_nodes: Vec<MenuNode>,
}

impl TianxiaHud {
    fn build_default_lattice() -> Vec<MenuNode> {
        let mut nodes = Vec::with_capacity(32);
        let mut push_node = |id: u32, parent: u32, tier: u8, col: u32, score: u16, warn: u16, lbl: &str, path: &str, tele: &str| {
            let mut n = MenuNode {
                id,
                parent_id: parent,
                tier,
                isolation: 0,
                _pad: 0,
                status_color_rgb: col,
                ephemeral_score_q16: score,
                judgment_warn_flag: warn,
                label: [0; 64],
                target_path: [0; 128],
                telemetry_summary: [0; 64],
            };
            for (i, b) in lbl.bytes().take(63).enumerate() { n.label[i] = b; }
            for (i, b) in path.bytes().take(127).enumerate() { n.target_path[i] = b; }
            for (i, b) in tele.bytes().take(63).enumerate() { n.telemetry_summary[i] = b; }
            nodes.push(n);
        };

        // Tier 0: TianxiaOS Root
        push_node(1, 0, 0, COLOR_CYAN_GLOW, 65000, 0, "Sovereign-Cluster [LAT-5591]", "tianxia://cluster/workhorse", "41 RGUs | DSS-14.2 | GEN 142");
        push_node(2, 0, 0, COLOR_CYAN_GLOW, 52000, 0, "Pointer-Bridge [:8732 <-> XPS]", "tianxia://bridge/xps13", "AF_XDP <0.6ms | ACTIVE");
        push_node(3, 0, 0, COLOR_EMERALD_OK, 48000, 0, "tmpfs-Sanitizer [Zero-Leak]", "tianxia://security/sanitize", "RAM Root | Blake3 Verified");

        // Tier 1: Systems
        push_node(10, 1, 1, COLOR_CYAN_GLOW, 64000, 0, "TetraLedger-FinOps", "system://tetraledger", "$350K Prin | $494.3K Out | 3 ACT 1 WARN");
        push_node(11, 1, 1, COLOR_CYAN_GLOW, 61000, 0, "Nixyr-Substrate", "system://nixyr", "Intel UHD 630 + MX130 sm_50");
        push_node(12, 1, 1, COLOR_CYAN_GLOW, 59000, 0, "Faery-Fortress [AEG-COM]", "system://faery", "AF_XDP 11.4Mpps @ 3.8us p99");
        push_node(13, 1, 1, COLOR_CYAN_GLOW, 57000, 0, "Artificial-Kenning [MANAS]", "system://kenning", "Port 3109 <14ms | 70.6% OpEx Cut");
        push_node(14, 1, 1, COLOR_EMERALD_OK, 50000, 0, "Herald-Spear [111-ICP]", "system://spear", "Career Spear + Inbound Closer");

        // Tier 2: Subsystems
        push_node(20, 10, 2, COLOR_EMBER_WARN, 65500, 1, "Credit-Facilities [TX_NIMUE]", "sub://tetraledger/facilities", "SQLite WAL | 1 Covenant Warn");
        push_node(21, 11, 2, COLOR_CYAN_GLOW, 58000, 0, "CUDA-SM50-Coprocessor", "sub://nixyr/cuda-sm50", "GeForce MX130 2GB | RTD3 Ready");
        push_node(22, 12, 2, COLOR_CYAN_GLOW, 60000, 0, "WireGuard-Mesh [wg0]", "sub://faery/wg0", "Multi-Node Encrypted Fabric");

        // Tier 3: Units
        push_node(30, 20, 3, COLOR_EMERALD_OK, 54000, 0, "FAC-TOKEN-001 // SYNAPSE-AI", "unit://fac/token-001", "$50K -> $65.5K | 2250 bps (22.5%)");
        push_node(31, 20, 3, COLOR_EMBER_WARN, 65535, 1, "FAC-LEASE-002 // METRO-LOG", "unit://fac/lease-002", "$85K -> $125.8K | Ratio 38.7% < 40%");
        push_node(32, 20, 3, COLOR_EMERALD_OK, 53000, 0, "FAC-INFRA-003 // NORDIC-COMP", "unit://fac/infra-003", "$120K -> $165.6K | 62.5C IPMI");
        push_node(33, 20, 3, COLOR_EMERALD_OK, 52000, 0, "FAC-EV-004 // BALTIC-FLEET", "unit://fac/ev-004", "$95K -> $136.5K | SoH 91.5% OBD2");

        // Tier 4: Files & Atomic Actions
        push_node(40, 31, 4, COLOR_EMBER_WARN, 65535, 1, "ENFORCE LOCK [PAYFAC_ESCALATE]", "action://tetraledger/lock/lease-002", "Blake3 WAL Commit + Rail Freeze");
        push_node(41, 31, 4, COLOR_CYAN_GLOW, 62000, 0, "ADJUST HOLDBACK [+250 BPS SPLIT]", "action://tetraledger/bps/lease-002", "Escalate 3500 -> 3750 bps");
        push_node(42, 31, 4, COLOR_EMERALD_OK, 58000, 0, "Inspect tx_nimue.sqlite-wal", "/var/lib/tianxia/ledger/tx_nimue.sqlite-wal", "Zero-Copy WAL Page Inspection");
        nodes
    }

    fn read_active_nodes(&self) -> Vec<MenuNode> {
        if let Some(ref mmap) = self.shm_map {
            if mmap.len() >= std::mem::size_of::<SharedMenuState>() {
                unsafe {
                    let ptr = mmap.as_ptr() as *const SharedMenuState;
                    let seq1 = std::ptr::read_volatile(&(*ptr).sequence_lock);
                    fence(Ordering::Acquire);
                    let count = (std::ptr::read_volatile(&(*ptr).node_count) as usize).min(256);
                    if count > 0 && (seq1 & 1) == 0 {
                        let mut out = Vec::with_capacity(count);
                        for i in 0..count {
                            out.push(std::ptr::read_volatile(&(*ptr).nodes[i]));
                        }
                        fence(Ordering::Acquire);
                        let seq2 = std::ptr::read_volatile(&(*ptr).sequence_lock);
                        if seq1 == seq2 {
                            return out;
                        }
                    }
                }
            }
        }
        self.fallback_nodes.clone()
    }

    fn dispatch_selection(&self, plane: IsolationPlane) {
        let nodes = self.read_active_nodes();
        let tier_nodes: Vec<&MenuNode> = nodes
            .iter()
            .filter(|n| n.tier as usize == self.selected_tier)
            .collect();
        let row = self.selected_row_per_tier[self.selected_tier];
        let target_id = tier_nodes.get(row).map(|n| n.id).unwrap_or(0);

        let mut pkt = BrokerDispatchPacket {
            magic: 0x54584F53,
            node_id: target_id,
            plane: plane as u8,
            intent_len: self.intent_buffer.len().min(127) as u8,
            _reserved: 0,
            intent_query: [0; 128],
        };
        for (i, b) in self.intent_buffer.bytes().take(127).enumerate() {
            pkt.intent_query[i] = b;
        }

        if let Ok(mut stream) = UnixStream::connect("/run/tianxia/broker.sock") {
            let bytes: &[u8] = unsafe {
                std::slice::from_raw_parts(
                    (&pkt as *const BrokerDispatchPacket) as *const u8,
                    std::mem::size_of::<BrokerDispatchPacket>(),
                )
            };
            let _ = stream.write_all(bytes);
        }
    }

    fn fill_rect(canvas: &mut [u32], stride: usize, x: usize, y: usize, w: usize, h: usize, color: u32) {
        let max_y = (y + h).min(canvas.len() / stride);
        let max_x = (x + w).min(stride);
        for row in y..max_y {
            let offset = row * stride;
            for col in x..max_x {
                canvas[offset + col] = color;
            }
        }
    }

    fn draw_border(canvas: &mut [u32], stride: usize, x: usize, y: usize, w: usize, h: usize, thickness: usize, color: u32) {
        Self::fill_rect(canvas, stride, x, y, w, thickness, color);
        Self::fill_rect(canvas, stride, x, (y + h).saturating_sub(thickness), w, thickness, color);
        Self::fill_rect(canvas, stride, x, y, thickness, h, color);
        Self::fill_rect(canvas, stride, (x + w).saturating_sub(thickness), y, thickness, h, color);
    }

    // Compact 5x7 Bitmapped Glyph Renderer for Zero-Dependency Sub-Millisecond Text
    fn glyph_bits(c: u8) -> [u8; 7] {
        match c.to_ascii_uppercase() {
            b'A' => [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
            b'B' => [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
            b'C' => [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
            b'D' => [0b11100, 0b10010, 0b10001, 0b10001, 0b10001, 0b10010, 0b11100],
            b'E' => [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
            b'F' => [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
            b'G' => [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
            b'H' => [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
            b'I' => [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
            b'J' => [0b00111, 0b00010, 0b00010, 0b00010, 0b10010, 0b10010, 0b01100],
            b'K' => [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
            b'L' => [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
            b'M' => [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
            b'N' => [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
            b'O' => [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
            b'P' => [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
            b'Q' => [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
            b'R' => [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
            b'S' => [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
            b'T' => [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
            b'U' => [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
            b'V' => [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
            b'W' => [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
            b'X' => [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
            b'Y' => [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
            b'Z' => [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
            b'0' => [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
            b'1' => [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
            b'2' => [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
            b'3' => [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
            b'4' => [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
            b'5' => [0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b00001, 0b11110],
            b'6' => [0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
            b'7' => [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
            b'8' => [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
            b'9' => [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110],
            b'-' => [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
            b'_' => [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111],
            b':' => [0b00000, 0b00100, 0b00100, 0b00000, 0b00100, 0b00100, 0b00000],
            b'/' => [0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000],
            b'[' => [0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110],
            b']' => [0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110],
            b'$' => [0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100],
            b'%' => [0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011],
            b'.' => [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100],
            b'+' => [0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000],
            b'>' => [0b10000, 0b01000, 0b00100, 0b00010, 0b00100, 0b01000, 0b10000],
            b'<' => [0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010],
            b'|' => [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
            _ => [0; 7],
        }
    }

    fn draw_text(canvas: &mut [u32], stride: usize, x: usize, y: usize, text: &str, color: u32) {
        let mut cursor_x = x;
        let max_y = canvas.len() / stride;
        for ch in text.bytes() {
            if cursor_x + 6 >= stride {
                break;
            }
            let glyph = Self::glyph_bits(ch);
            for (row_idx, bits) in glyph.iter().enumerate() {
                let py = y + row_idx;
                if py >= max_y {
                    continue;
                }
                for col_idx in 0..5 {
                    if (bits & (1 << (4 - col_idx))) != 0 {
                        canvas[py * stride + cursor_x + col_idx] = color;
                    }
                }
            }
            cursor_x += 6;
        }
    }

    fn cstr_to_str(buf: &[u8]) -> &str {
        let len = buf.iter().position(|&b| b == 0).unwrap_or(buf.len());
        std::str::from_utf8(&buf[..len]).unwrap_or("")
    }

    fn draw(&mut self, qh: &QueueHandle<Self>) {
        if !self.configured {
            return;
        }
        let width = self.width as usize;
        let height = self.height as usize;
        let stride = width * 4;

        let (buffer, canvas_bytes) = match self.pool.create_buffer(
            self.width as i32,
            self.height as i32,
            stride as i32,
            wl_shm::Format::Argb8888,
        ) {
            Ok(b) => b,
            Err(e) => {
                eprintln!("[TX_HUD] create_buffer error for {}x{}: {:?}", self.width, self.height, e);
                return;
            }
        };

        let canvas: &mut [u32] = unsafe {
            std::slice::from_raw_parts_mut(canvas_bytes.as_mut_ptr() as *mut u32, width * height)
        };

        // 1. Void Background (#080808) & Bioluminescent Cyan Outer Frame (#00F0FF)
        Self::fill_rect(canvas, width, 0, 0, width, height, COLOR_VOID_BG);
        Self::draw_border(canvas, width, 0, 0, width, height, 2, COLOR_CYAN_GLOW);

        // 2. Top Sovereign Telemetry Header Bar
        Self::fill_rect(canvas, width, 2, 2, width - 4, 28, COLOR_SLATE_DIM);
        Self::draw_text(
            canvas,
            width,
            12,
            12,
            "TIANXIA // EPHEMERAL COCKPIT V0.5.0 | DSS-14.2 | MANAS :3109 (<14MS) | BRIDGE :8732 [LAT-5591 <-> XPS-13]",
            COLOR_CYAN_GLOW,
        );

        // 3. 5-Tier Miller Columns (TianxiaOS -> System -> Subsystem -> Unit -> File)
        let tier_titles = [
            "T0: TIANXIAOS",
            "T1: SYSTEM",
            "T2: SUBSYSTEM",
            "T3: UNIT",
            "T4: FILE / STATE",
        ];
        let col_w = (width - 24) / 5;
        let col_top = 36;
        let col_h = height.saturating_sub(150);

        let all_nodes = self.read_active_nodes();

        for tier in 0..5 {
            let cx = 10 + tier * col_w;
            let is_active_tier = self.selected_tier == tier;
            let border_col = if is_active_tier { COLOR_CYAN_GLOW } else { COLOR_TEXT_MUTED };

            Self::fill_rect(canvas, width, cx, col_top, col_w - 6, col_h, COLOR_SLATE_DIM);
            Self::draw_border(canvas, width, cx, col_top, col_w - 6, col_h, 1, border_col);
            Self::draw_text(canvas, width, cx + 8, col_top + 8, tier_titles[tier], border_col);

            let tier_nodes: Vec<&MenuNode> = all_nodes
                .iter()
                .filter(|n| n.tier as usize == tier)
                .collect();

            let selected_row = self.selected_row_per_tier[tier].min(tier_nodes.len().saturating_sub(1));

            for (row_idx, node) in tier_nodes.iter().enumerate() {
                let ry = col_top + 26 + row_idx * 42;
                if ry + 38 >= col_top + col_h {
                    break;
                }
                let is_selected = is_active_tier && row_idx == selected_row;
                let row_bg = if is_selected { 0xFF162830 } else { COLOR_VOID_BG };
                Self::fill_rect(canvas, width, cx + 4, ry, col_w - 14, 36, row_bg);

                let indicator_col = if node.judgment_warn_flag != 0 {
                    COLOR_EMBER_WARN
                } else {
                    node.status_color_rgb
                };
                Self::fill_rect(canvas, width, cx + 4, ry, 3, 36, indicator_col);

                let lbl = Self::cstr_to_str(&node.label);
                let tele = Self::cstr_to_str(&node.telemetry_summary);
                let txt_col = if is_selected || node.ephemeral_score_q16 > 58000 {
                    COLOR_TEXT_MAIN
                } else {
                    COLOR_TEXT_MUTED
                };

                Self::draw_text(canvas, width, cx + 12, ry + 7, lbl, txt_col);
                Self::draw_text(canvas, width, cx + 12, ry + 20, tele, indicator_col);
            }
        }

        // 4. Ephemeral Huber-Boosted Hot-Node Bar (MX130 sm_50 Top Predictions)
        let hot_y = height.saturating_sub(106);
        Self::fill_rect(canvas, width, 10, hot_y, width - 20, 52, COLOR_SLATE_DIM);
        Self::draw_border(canvas, width, 10, hot_y, width - 20, 52, 1, COLOR_EMBER_WARN);
        Self::draw_text(
            canvas,
            width,
            18,
            hot_y + 8,
            "MX130 SM_50 EPHEMERAL HOT-NODES [ALT+1] FAC-LEASE-002 WARN (38.7% < 40.0%) -> ENFORCE LOCK [PAYFAC_ESCALATE]",
            COLOR_EMBER_WARN,
        );
        Self::draw_text(
            canvas,
            width,
            18,
            hot_y + 24,
            "[ALT+2] ADJUST HOLDBACK +250 BPS SPLIT   [ALT+3] INSPECT AF_XDP 11.4MPPS RINGBUF   [VERITAS-REX: ACTIVE]",
            COLOR_EMERALD_OK,
        );

        // 5. Bottom Bimodal Intent Command Bar (Port 3109 MANAS System-1 Gate)
        let bar_y = height.saturating_sub(46);
        Self::fill_rect(canvas, width, 10, bar_y, width - 20, 36, COLOR_VOID_BG);
        Self::draw_border(canvas, width, 10, bar_y, width - 20, 36, 1, COLOR_CYAN_GLOW);
        let prompt = format!(
            "INTENT (:3109) > {}_   [ENTER: NATIVE | SHIFT+ENTER: ELASTIC NS | CTRL+ENTER: PKVM MICROVM]",
            self.intent_buffer
        );
        Self::draw_text(canvas, width, 18, bar_y + 14, &prompt, COLOR_CYAN_GLOW);

        // 6. Commit Zero-Copy Buffer to Wayland Layer Surface
        self.layer_surface.wl_surface().attach(Some(buffer.wl_buffer()), 0, 0);
        self.layer_surface
            .wl_surface()
            .damage_buffer(0, 0, self.width as i32, self.height as i32);
        self.layer_surface.wl_surface().frame(qh, self.layer_surface.wl_surface().clone());
        self.layer_surface.commit();
    }
}

impl CompositorHandler for TianxiaHud {
    fn scale_factor_changed(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_surface::WlSurface, _: i32) {}
    fn transform_changed(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_surface::WlSurface, _: wl_output::Transform) {}
    fn frame(&mut self, _: &Connection, qh: &QueueHandle<Self>, _: &wl_surface::WlSurface, _: u32) {
        self.draw(qh);
    }
    fn surface_enter(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_surface::WlSurface, _: &wl_output::WlOutput) {}
    fn surface_leave(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_surface::WlSurface, _: &wl_output::WlOutput) {}
}

impl OutputHandler for TianxiaHud {
    fn output_state(&mut self) -> &mut OutputState { &mut self.output_state }
    fn new_output(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
    fn update_output(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
    fn output_destroyed(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
}

impl LayerShellHandler for TianxiaHud {
    fn closed(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &LayerSurface) {
        self.exit = true;
    }
    fn configure(&mut self, _: &Connection, qh: &QueueHandle<Self>, _: &LayerSurface, configure: LayerSurfaceConfigure, _: u32) {
        if configure.new_size.0 > 0 {
            self.width = configure.new_size.0;
        }
        if configure.new_size.1 > 0 {
            self.height = configure.new_size.1;
        }
        self.configured = true;
        self.draw(qh);
    }
}

impl SeatHandler for TianxiaHud {
    fn seat_state(&mut self) -> &mut SeatState { &mut self.seat_state }
    fn new_seat(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_seat::WlSeat) {}
    fn new_capability(&mut self, _: &Connection, qh: &QueueHandle<Self>, seat: wl_seat::WlSeat, capability: Capability) {
        if capability == Capability::Keyboard {
            let _ = self.seat_state.get_keyboard(qh, &seat, None);
        }
        if capability == Capability::Pointer {
            let _ = self.seat_state.get_pointer(qh, &seat);
        }
    }
    fn remove_capability(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_seat::WlSeat, _: Capability) {}
    fn remove_seat(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_seat::WlSeat) {}
}

impl KeyboardHandler for TianxiaHud {
    fn enter(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_keyboard::WlKeyboard, _: &wl_surface::WlSurface, _: u32, _: &[u32], _: &[Keysym]) {}
    fn leave(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_keyboard::WlKeyboard, _: &wl_surface::WlSurface, _: u32) {}
    fn press_key(&mut self, _: &Connection, qh: &QueueHandle<Self>, _: &wl_keyboard::WlKeyboard, _: u32, event: KeyEvent) {
        match event.keysym {
            Keysym::Escape => self.exit = true,
            Keysym::Left => {
                self.selected_tier = self.selected_tier.saturating_sub(1);
            }
            Keysym::Right => {
                self.selected_tier = (self.selected_tier + 1).min(4);
            }
            Keysym::Up => {
                let r = &mut self.selected_row_per_tier[self.selected_tier];
                *r = r.saturating_sub(1);
            }
            Keysym::Down => {
                let r = &mut self.selected_row_per_tier[self.selected_tier];
                *r = (*r + 1).min(15);
            }
            Keysym::BackSpace => {
                self.intent_buffer.pop();
            }
            Keysym::Return => {
                let plane = if self.modifiers.ctrl {
                    IsolationPlane::EphemeralMicroVm
                } else if self.modifiers.shift {
                    IsolationPlane::ElasticNamespace
                } else {
                    IsolationPlane::NativeInspect
                };
                self.dispatch_selection(plane);
            }
            _ => {
                if let Some(txt) = event.utf8 {
                    for ch in txt.chars() {
                        if !ch.is_control() && self.intent_buffer.len() < 96 {
                            self.intent_buffer.push(ch);
                        }
                    }
                }
            }
        }
        self.draw(qh);
    }
    fn release_key(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_keyboard::WlKeyboard, _: u32, _: KeyEvent) {}
    fn update_modifiers(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_keyboard::WlKeyboard, _: u32, modifiers: Modifiers, _: u32) {
        self.modifiers = modifiers;
    }
}

impl PointerHandler for TianxiaHud {
    fn pointer_frame(&mut self, _: &Connection, qh: &QueueHandle<Self>, _: &wl_pointer::WlPointer, events: &[PointerEvent]) {
        for ev in events {
            if let PointerEventKind::Press { button: 272, .. } = ev.kind {
                let col_w = ((self.width as usize).saturating_sub(24)) / 5;
                if col_w > 0 {
                    let clicked_tier = ((ev.position.0 as usize).saturating_sub(10) / col_w).min(4);
                    self.selected_tier = clicked_tier;
                    if ev.position.1 > 62.0 {
                        let clicked_row = ((ev.position.1 as usize - 62) / 42).min(15);
                        self.selected_row_per_tier[clicked_tier] = clicked_row;
                    }
                    self.draw(qh);
                }
            }
        }
    }
}

impl ShmHandler for TianxiaHud {
    fn shm_state(&mut self) -> &mut Shm { &mut self.shm }
}

delegate_compositor!(TianxiaHud);
delegate_output!(TianxiaHud);
delegate_shm!(TianxiaHud);
delegate_seat!(TianxiaHud);
delegate_keyboard!(TianxiaHud);
delegate_pointer!(TianxiaHud);
delegate_layer!(TianxiaHud);
delegate_registry!(TianxiaHud);

impl ProvidesRegistryState for TianxiaHud {
    fn registry(&mut self) -> &mut RegistryState { &mut self.registry_state }
    registry_handlers![OutputState, SeatState];
}

fn main() {
    let conn = Connection::connect_to_env().expect("Failed to connect to Wayland socket");
    let (globals, mut event_queue) = registry_queue_init(&conn).expect("Failed to init Wayland registry");
    let qh = event_queue.handle();

    let compositor = CompositorState::bind(&globals, &qh).expect("wl_compositor unavailable");
    let layer_shell = LayerShell::bind(&globals, &qh).expect("wlr_layer_shell_v1 unavailable");
    let shm = Shm::bind(&globals, &qh).expect("wl_shm unavailable");

    let surface = compositor.create_surface(&qh);
    let layer_surface = layer_shell.create_layer_surface(
        &qh,
        surface,
        Layer::Overlay,
        Some("tianxia-ephemeral-hud"),
        None,
    );

    layer_surface.set_anchor(Anchor::TOP | Anchor::LEFT | Anchor::RIGHT);
    layer_surface.set_size(1280, 480);
    layer_surface.set_margin(36, 24, 0, 24);
    layer_surface.set_keyboard_interactivity(KeyboardInteractivity::OnDemand);
    layer_surface.commit();

    let pool = SlotPool::new(1920 * 1080 * 4 * 2, &shm).expect("Failed to allocate SHM SlotPool");

    let shm_map = OpenOptions::new()
        .read(true)
        .open("/dev/shm/tx_menu_ast")
        .ok()
        .and_then(|f| unsafe { MmapOptions::new().map(&f).ok() });

    let mut hud = TianxiaHud {
        registry_state: RegistryState::new(&globals),
        seat_state: SeatState::new(&globals, &qh),
        output_state: OutputState::new(&globals, &qh),
        shm,
        pool,
        layer_surface,
        width: 1280,
        height: 480,
        configured: false,
        exit: false,
        modifiers: Modifiers::default(),
        selected_tier: 3, // Default focus on Tier 3 (Active Units / Facilities)
        selected_row_per_tier: [0, 0, 0, 1, 0],
        intent_buffer: String::from("pulse scour refresh + reconcile tetraledger"),
        shm_map,
        fallback_nodes: TianxiaHud::build_default_lattice(),
    };

    while !hud.exit {
        event_queue.blocking_dispatch(&mut hud).expect("Wayland dispatch failed");
    }
}
