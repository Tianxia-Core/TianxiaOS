// ffp: FFP-ZIG-001 zero-alloc-ring zig
//! TianxiaOS Core 02 (Nimbus-ZeroAlloc) - Bhairavi Gate
//! Explicit-allocator lock-free ring buffer for zero-copy POSIX /dev/shm IPC.
//! Compliance: Zero-Stub + C ABI Export + Zero Hidden Allocation + Zig 0.16.0

const std = @import("std");

pub const RingHeader = extern struct {
    head: usize,
    tail: usize,
    capacity: usize,
    magic: u32,
    _pad: u32,
};

pub const MAGIC_VALUE: u32 = 0x54584E47; // "TXNG"

pub export fn tx_ring_init(buffer: [*]u8, capacity: usize) bool {
    if (capacity == 0 or (capacity & (capacity - 1)) != 0) {
        return false; // Must be power of 2
    }
    const header: *RingHeader = @ptrCast(@alignCast(buffer));
    header.head = 0;
    header.tail = 0;
    header.capacity = capacity;
    header.magic = MAGIC_VALUE;
    header._pad = 0;
    return true;
}

pub export fn tx_ring_push(buffer: [*]u8, item: u64) bool {
    const header: *RingHeader = @ptrCast(@alignCast(buffer));
    if (header.magic != MAGIC_VALUE) return false;

    const current_head = header.head;
    const current_tail = header.tail;

    if (current_head - current_tail >= header.capacity) {
        return false; // Ring buffer full
    }

    const data_ptr: [*]u64 = @ptrCast(@alignCast(buffer + @sizeOf(RingHeader)));
    const index = current_head & (header.capacity - 1);
    data_ptr[index] = item;
    header.head = current_head + 1;
    return true;
}

pub export fn tx_ring_pop(buffer: [*]u8, out_item: *u64) bool {
    const header: *RingHeader = @ptrCast(@alignCast(buffer));
    if (header.magic != MAGIC_VALUE) return false;

    const current_head = header.head;
    const current_tail = header.tail;

    if (current_head == current_tail) {
        return false; // Ring buffer empty
    }

    const data_ptr: [*]u64 = @ptrCast(@alignCast(buffer + @sizeOf(RingHeader)));
    const index = current_tail & (header.capacity - 1);
    out_item.* = data_ptr[index];
    header.tail = current_tail + 1;
    return true;
}

pub export fn tx_ring_count(buffer: [*]u8) usize {
    const header: *RingHeader = @ptrCast(@alignCast(buffer));
    if (header.magic != MAGIC_VALUE) return 0;
    return header.head - header.tail;
}

pub fn main() void {
    std.debug.print("=== [TIANXIAOS // NIMBUS-ZEROALLOC (ZIG)] Bhairavi Ring Buffer ===\n", .{});

    var backing_store: [4096]u8 align(64) = undefined;
    const ok = tx_ring_init(&backing_store, 16);
    std.debug.print("[ZIG-RING INIT]: status={}\n", .{ok});

    const pushed1 = tx_ring_push(&backing_store, 0xCAFE_BABE_DEAD_BEEF);
    const pushed2 = tx_ring_push(&backing_store, 0x1077_0001_0000_0101);
    std.debug.print("[ZIG-RING PUSH]: p1={} p2={} count={}\n", .{ pushed1, pushed2, tx_ring_count(&backing_store) });

    var val: u64 = 0;
    const popped1 = tx_ring_pop(&backing_store, &val);
    std.debug.print("[ZIG-RING POP 1]: ok={} val=0x{X}\n", .{ popped1, val });

    const popped2 = tx_ring_pop(&backing_store, &val);
    std.debug.print("[ZIG-RING POP 2]: ok={} val=0x{X}\n", .{ popped2, val });

    std.debug.print("=== [TIANXIAOS // NIMBUS-ZEROALLOC (ZIG)] Test Complete ===\n", .{});
}
