const std = @import("std");

// Linux / POSIX Constants
const O_RDWR: c_int = 2;
const O_CREAT: c_int = 64;
const PROT_READ: c_int = 1;
const PROT_WRITE: c_int = 2;
const MAP_SHARED: c_int = 1;
const AF_UNIX: c_int = 1;
const SOCK_STREAM: c_int = 1;
const SOL_SOCKET: c_int = 1;
const SO_PEERCRED: c_int = 17;

// Direct C Library Bindings
extern "c" fn open(path: [*:0]const u8, flags: c_int, mode: c_uint) c_int;
extern "c" fn close(fd: c_int) c_int;
extern "c" fn ftruncate(fd: c_int, length: c_long) c_int;
extern "c" fn mmap(addr: ?*anyopaque, length: usize, prot: c_int, flags: c_int, fd: c_int, offset: c_long) ?*anyopaque;
extern "c" fn munmap(addr: *anyopaque, length: usize) c_int;
extern "c" fn socket(domain: c_int, socket_type: c_int, protocol: c_int) c_int;
extern "c" fn bind(sockfd: c_int, addr: *const anyopaque, addrlen: c_uint) c_int;
extern "c" fn listen(sockfd: c_int, backlog: c_int) c_int;
extern "c" fn accept(sockfd: c_int, addr: ?*anyopaque, addrlen: ?*c_uint) c_int;
extern "c" fn read(fd: c_int, buf: [*]u8, count: usize) isize;
extern "c" fn write(fd: c_int, buf: [*]const u8, count: usize) isize;
extern "c" fn unlink(path: [*:0]const u8) c_int;
extern "c" fn getsockopt(sockfd: c_int, level: c_int, optname: c_int, optval: *anyopaque, optlen: *c_uint) c_int;
extern "c" fn mkdir(path: [*:0]const u8, mode: c_uint) c_int;
extern "c" fn fork() c_int;
extern "c" fn execvp(file: [*:0]const u8, argv: [*]const ?[*:0]const u8) c_int;
extern "c" fn _exit(status: c_int) noreturn;

const sockaddr_un = extern struct {
    sun_family: u16 = AF_UNIX,
    sun_path: [108]u8 = [_]u8{0} ** 108,
};

const ucred = extern struct {
    pid: i32,
    uid: u32,
    gid: u32,
};

pub const IsolationPlane = enum(u8) {
    native_inspect = 0,
    elastic_namespace = 1,
    ephemeral_microvm = 2,
};

pub const MenuNode = extern struct {
    id: u32,
    parent_id: u32,
    tier: u8,
    isolation: u8,
    _pad: u16,
    status_color_rgb: u32,
    ephemeral_score_q16: u16,
    judgment_warn_flag: u16,
    label: [64]u8,
    target_path: [128]u8,
    telemetry_summary: [64]u8,
};

pub const SharedMenuState = extern struct {
    sequence_lock: u64,
    active_generation: u32,
    manas_latency_us: u32,
    node_count: u32,
    hot_node_indices: [3]u32,
    nodes: [256]MenuNode,
};

pub const BrokerDispatchPacket = extern struct {
    magic: u32, // 0x54584F53 ("TXOS")
    node_id: u32,
    plane: u8,
    intent_len: u8,
    _reserved: u16,
    intent_query: [128]u8,
};

pub fn initSharedMemory() !*SharedMenuState {
    const shm_path = "/dev/shm/tx_menu_ast";
    const fd = open(shm_path, O_RDWR | O_CREAT, 0o660);
    if (fd < 0) return error.ShmOpenFailed;
    defer _ = close(fd);

    const size: c_long = @sizeOf(SharedMenuState);
    if (ftruncate(fd, size) != 0) return error.ShmTruncateFailed;

    const ptr = mmap(null, @sizeOf(SharedMenuState), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == null or ptr == @as(?*anyopaque, @ptrFromInt(std.math.maxInt(usize)))) {
        return error.ShmMmapFailed;
    }
    return @ptrCast(@alignCast(ptr.?));
}

pub fn authenticateCallerPeer(client_fd: c_int, allowed_uid: u32) !void {
    var cred: ucred = undefined;
    var len: c_uint = @sizeOf(ucred);
    const rc = getsockopt(client_fd, SOL_SOCKET, SO_PEERCRED, &cred, &len);
    if (rc != 0) {
        return error.GetSockOptFailed;
    }
    if (cred.uid != allowed_uid and cred.uid != 0) {
        std.log.warn("[TX_BROKER] SO_PEERCRED rejection: caller UID={d} (expected {d} or 0)", .{ cred.uid, allowed_uid });
        return error.UnauthorizedPeerCred;
    }
}

pub fn dispatchAction(alloc: std.mem.Allocator, pkt: *const BrokerDispatchPacket) !void {
    if (pkt.magic != 0x54584F53) return error.InvalidPacketMagic;
    const plane: IsolationPlane = @enumFromInt(pkt.plane);

    var unit_buf: [32]u8 = undefined;
    const unit_str = try std.fmt.bufPrintZ(&unit_buf, "tx-node-{d}", .{pkt.node_id});

    const query_slice = pkt.intent_query[0..@min(pkt.intent_len, 127)];
    std.log.info("[TX_BROKER] Action: Node ID {d}, Plane {s}, Query: '{s}'", .{
        pkt.node_id,
        @tagName(plane),
        query_slice,
    });

    const pid = fork();
    if (pid < 0) {
        std.log.err("[TX_BROKER] fork() failed", .{});
        return;
    }

    if (pid == 0) {
        // Child execution path
        switch (plane) {
            .native_inspect => {
                const argv = [_]?[*:0]const u8{
                    "/run/current-system/sw/bin/systemctl",
                    "status",
                    "--no-pager",
                    unit_str.ptr,
                    null,
                };
                _ = execvp("/run/current-system/sw/bin/systemctl", &argv);
            },
            .elastic_namespace => {
                const argv = [_]?[*:0]const u8{
                    "/run/current-system/sw/bin/systemd-run",
                    "--collect",
                    "-p",
                    "PrivateTmp=yes",
                    "-p",
                    "ProtectSystem=strict",
                    "-p",
                    "NoNewPrivileges=yes",
                    "/var/lib/tianxia/bin/tx-elastic-exec",
                    unit_str.ptr,
                    null,
                };
                _ = execvp("/run/current-system/sw/bin/systemd-run", &argv);
            },
            .ephemeral_microvm => {
                const argv = [_]?[*:0]const u8{
                    "/var/lib/tianxia/bin/tx-zygote-resume",
                    "--snapshot",
                    "/dev/shm/tx_vm_zygote",
                    "--vsock-wayland",
                    "/run/tianxia/virtwl.sock",
                    "--target",
                    unit_str.ptr,
                    null,
                };
                _ = execvp("/var/lib/tianxia/bin/tx-zygote-resume", &argv);
            },
        }
        _exit(1);
    }
    _ = alloc;
}

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    std.log.info("[TX_BROKER] Booting TianxiaOS Polyglot Ephemeral Menu Broker...", .{});

    const shm = try initSharedMemory();
    @atomicStore(u64, &shm.sequence_lock, 2, .release);
    shm.active_generation = 142;
    shm.manas_latency_us = 2310;

    _ = mkdir("/run/tianxia", 0o755);

    const sock_path = "/run/tianxia/broker.sock";
    _ = unlink(sock_path);

    const server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) return error.SocketCreationFailed;
    defer _ = close(server_fd);

    var addr = sockaddr_un{};
    const path_bytes = sock_path;
    @memcpy(addr.sun_path[0..path_bytes.len], path_bytes);

    if (bind(server_fd, @ptrCast(&addr), @sizeOf(sockaddr_un)) != 0) {
        return error.SocketBindFailed;
    }

    if (listen(server_fd, 16) != 0) {
        return error.SocketListenFailed;
    }

    std.log.info("[TX_BROKER] Master Sovereign Broker active on {s}", .{sock_path});

    while (true) {
        const client_fd = accept(server_fd, null, null);
        if (client_fd < 0) continue;
        defer _ = close(client_fd);

        authenticateCallerPeer(client_fd, 1000) catch continue;

        var pkt: BrokerDispatchPacket = undefined;
        const n = read(client_fd, @ptrCast(&pkt), @sizeOf(BrokerDispatchPacket));
        if (n == @sizeOf(BrokerDispatchPacket)) {
            dispatchAction(alloc, &pkt) catch |err| {
                std.log.err("[TX_BROKER] Dispatch error: {any}", .{err});
            };
        }
    }
}
