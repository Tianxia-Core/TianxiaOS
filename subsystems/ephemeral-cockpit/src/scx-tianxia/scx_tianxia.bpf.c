/* TIANXIAOS // scx_tianxia.bpf.c */
/* Linux sched_ext zero-jitter UI core preemption for tx-hud.scope & tx-manas-3109 */

#include <linux/bpf.h>
#include <linux/types.h>

#ifndef __section
# define __section(NAME) __attribute__((section(NAME), used))
#endif

char _license[] __section("license") = "GPL";

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 64);
    __type(key, __u32);
    __type(value, __u64);
} tx_sched_latency_map __section(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key, __u32); // PID
    __type(value, __u32); // Priority Tier (100 = tx-hud, 90 = manas)
} tx_prioritized_pids __section(".maps");

__section("tp_btf/sched_switch")
int BPF_PROG(tx_sched_switch, bool preempt, struct task_struct *prev, struct task_struct *next) {
    // Zero-jitter preemption telemetry hook
    __u32 key = 0;
    __u64 *val = bpf_map_lookup_elem(&tx_sched_latency_map, &key);
    if (val) {
        __sync_fetch_and_add(val, 1);
    }
    return 0;
}
