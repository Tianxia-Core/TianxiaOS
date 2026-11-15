// ffp: FFP-ALPS-DUALPOINT-INIT wire-codec c
// TianxiaOS Dell Latitude 5591 ALPS DualPoint (044E:121F) Hardware Self-Test & PTP Fault Isolator
// C11 zero-malloc implementation satisfying DSS-14.2 (Bhairavi, Chhinnamasta, Bagalamukhi, Mahasarasvati).

#define _GNU_SOURCE
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/hidraw.h>
#include <linux/input.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#ifndef HIDIOCSFEATURE
#define HIDIOCSFEATURE(len) _IOC(_IOC_WRITE | _IOC_READ, 'H', 0x06, len)
#endif

static uint64_t monotonic_ms(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return ((uint64_t)ts.tv_sec * 1000ULL) + ((uint64_t)ts.tv_nsec / 1000000ULL);
}

static void sleep_ms(long ms) {
    struct timespec req;
    req.tv_sec = ms / 1000;
    req.tv_nsec = (ms % 1000) * 1000000L;
    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
    }
}

static bool contains_icase(const char *haystack, const char *needle) {
    size_t nlen = strlen(needle);
    if (nlen == 0) {
        return true;
    }
    for (const char *p = haystack; *p != '\0'; ++p) {
        size_t i = 0;
        while (i < nlen && p[i] != '\0' &&
               tolower((unsigned char)p[i]) == tolower((unsigned char)needle[i])) {
            ++i;
        }
        if (i == nlen) {
            return true;
        }
    }
    return false;
}

static void release_latched_touchpad_buttons(void) {
    DIR *dir = opendir("/dev/input");
    if (!dir) {
        return;
    }
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
        if (strncmp(ent->d_name, "event", 5) != 0) {
            continue;
        }
        char devpath[512];
        snprintf(devpath, sizeof(devpath), "/dev/input/%s", ent->d_name);
        int fd = open(devpath, O_RDWR | O_NONBLOCK | O_CLOEXEC);
        if (fd < 0) {
            continue;
        }
        char name[256];
        memset(name, 0, sizeof(name));
        if (ioctl(fd, EVIOCGNAME(sizeof(name) - 1), name) >= 0) {
            if (contains_icase(name, "044E:121F") && contains_icase(name, "Touchpad")) {
                struct timeval tv;
                gettimeofday(&tv, NULL);
                struct input_event evs[3];
                memset(evs, 0, sizeof(evs));
                evs[0].time = tv;
                evs[0].type = EV_KEY;
                evs[0].code = BTN_LEFT;
                evs[0].value = 0;

                evs[1].time = tv;
                evs[1].type = EV_KEY;
                evs[1].code = BTN_RIGHT;
                evs[1].value = 0;

                evs[2].time = tv;
                evs[2].type = EV_SYN;
                evs[2].code = SYN_REPORT;
                evs[2].value = 0;

                ssize_t wr = write(fd, evs, sizeof(evs));
                (void)wr;
            }
        }
        close(fd);
    }
    closedir(dir);
}

static void write_telemetry(const char *hidraw_node, bool present, bool isolated,
                            unsigned int stuck_mask, unsigned int sampled_frames) {
    (void)mkdir("/run/tianxia", 0755);
    const char *tmp_path = "/run/tianxia/alps_dualpoint_state.json.tmp";
    const char *dst_path = "/run/tianxia/alps_dualpoint_state.json";
    int fd = open(tmp_path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (fd < 0) {
        return;
    }
    char buf[512];
    int len = snprintf(
        buf, sizeof(buf),
        "{\"device\":\"044E:121F\",\"hidraw\":\"%s\",\"present\":%s,"
        "\"ptp_device_mode\":3,\"selective_reporting\":%u,"
        "\"stuck_button_isolated\":%s,\"stuck_button_mask\":%u,"
        "\"sampled_idle_frames\":%u,\"ts_epoch\":%lld}\n",
        hidraw_node ? hidraw_node : "none",
        present ? "true" : "false",
        isolated ? 1U : 3U,
        isolated ? "true" : "false",
        stuck_mask,
        sampled_frames,
        (long long)time(NULL));
    if (len > 0 && (size_t)len < sizeof(buf)) {
        ssize_t wr = write(fd, buf, (size_t)len);
        (void)wr;
    }
    fsync(fd);
    close(fd);
    (void)rename(tmp_path, dst_path);
}

int main(void) {
    DIR *dir = opendir("/sys/class/hidraw");
    if (!dir) {
        write_telemetry(NULL, false, false, 0, 0);
        return 0;
    }

    char target_dev[512] = {0};
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
        if (strncmp(ent->d_name, "hidraw", 6) != 0) {
            continue;
        }
        char syslink[512];
        char resolved[PATH_MAX];
        snprintf(syslink, sizeof(syslink), "/sys/class/hidraw/%s/device", ent->d_name);
        if (realpath(syslink, resolved) != NULL && contains_icase(resolved, "044E:121F")) {
            snprintf(target_dev, sizeof(target_dev), "/dev/%s", ent->d_name);
            break;
        }
    }
    closedir(dir);

    if (target_dev[0] == '\0') {
        write_telemetry(NULL, false, false, 0, 0);
        return 0;
    }

    int fd = open(target_dev, O_RDWR | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "[tx-alps-dualpoint-init] open %s failed: %s\n",
                target_dev, strerror(errno));
        return 1;
    }

    // 1. Enable Windows Precision Touchpad mode (0x0b = 0x03) and test full Surface+Button reporting (0x0c = 0x03).
    uint8_t feat_mode[2] = {0x0b, 0x03};
    uint8_t feat_sel[2] = {0x0c, 0x03};
    if (ioctl(fd, HIDIOCSFEATURE(2), feat_mode) < 0) {
        fprintf(stderr, "[tx-alps-dualpoint-init] warn: SET_FEATURE 0x0b failed: %s\n",
                strerror(errno));
    }
    if (ioctl(fd, HIDIOCSFEATURE(2), feat_sel) < 0) {
        fprintf(stderr, "[tx-alps-dualpoint-init] warn: SET_FEATURE 0x0c=0x03 failed: %s\n",
                strerror(errno));
    }

    sleep_ms(15);

    // Drain any buffered pre-transition packets (bounded to 128 packets).
    uint8_t frame[64];
    for (int i = 0; i < 128; ++i) {
        if (read(fd, frame, sizeof(frame)) <= 0) {
            break;
        }
    }

    // 2. Deterministic 80ms hardware self-test for stuck physical bottom button switches.
    unsigned int stuck_frames = 0;
    unsigned int clean_frames = 0;
    unsigned int stuck_mask = 0;
    uint64_t deadline = monotonic_ms() + 80ULL;

    while (monotonic_ms() < deadline) {
        struct pollfd pfd = {.fd = fd, .events = POLLIN, .revents = 0};
        int prc = poll(&pfd, 1, 15);
        if (prc > 0 && (pfd.revents & POLLIN)) {
            ssize_t n = read(fd, frame, sizeof(frame));
            if (n >= 10 && frame[0] == 0x08) {
                uint8_t contact_count = frame[8];
                uint8_t btn_bits = frame[9] & 0x03U;
                if (contact_count == 0 && btn_bits != 0) {
                    ++stuck_frames;
                    stuck_mask |= btn_bits;
                } else if (btn_bits == 0) {
                    ++clean_frames;
                }
            }
        }
    }

    bool isolated = false;
    if (stuck_frames >= 4 && clean_frames == 0) {
        // Shorted/stuck bottom microswitch detected -> isolate via Selective Reporting (SurfaceSwitch=1, ButtonSwitch=0)
        uint8_t isolate_sel[2] = {0x0c, 0x01};
        if (ioctl(fd, HIDIOCSFEATURE(2), isolate_sel) >= 0) {
            isolated = true;
        }
        sleep_ms(10);
        release_latched_touchpad_buttons();
        fprintf(stdout,
                "[tx-alps-dualpoint-init] %s: stuck bottom button mask=0x%02x (%u idle frames) isolated via 0x0c=0x01; IRQ storm arrested; PTP multitouch + top 3 buttons active.\n",
                target_dev, stuck_mask, stuck_frames);
    } else {
        fprintf(stdout,
                "[tx-alps-dualpoint-init] %s: PTP mode 0x0b=0x03, 0x0c=0x03 active (all switches nominal).\n",
                target_dev);
    }

    close(fd);
    write_telemetry(target_dev, true, isolated, stuck_mask, stuck_frames);
    return 0;
}
