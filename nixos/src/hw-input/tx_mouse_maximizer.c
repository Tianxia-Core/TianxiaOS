// ffp: FFP-MOUSE-MAXIMIZER concurrent-daemon c
// TianxiaOS Zero-Latency External Mouse Extra-Button Maximizer Daemon
// Passively observes EV_KEY events (without EVIOCGRAB, preserving 0ms 1000Hz KWin cursor tracking)
// on multi-button mice (Redragon M602U-KS 1a2c:8fff, Logitech Lightspeed, Bluetooth mice)
// and bridges unmapped hardware buttons 6/7/8 (BTN_FORWARD, BTN_BACK, BTN_TASK) to KDE Plasma 6
// Wayland desktop actions via /dev/uinput.

#define _GNU_SOURCE
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/inotify.h>
#include <sys/ioctl.h>
#include <unistd.h>

#define MAX_WATCHED_MICE 16
#define BITS_PER_LONG (sizeof(unsigned long) * 8)
#define NBITS(x) ((((x) - 1) / BITS_PER_LONG) + 1)
#define TEST_BIT(bit, array) \
    (((array[(bit) / BITS_PER_LONG]) >> ((bit) % BITS_PER_LONG)) & 1UL)

struct watched_mouse {
    int fd;
    char path[512];
};

static volatile sig_atomic_t g_stop = 0;

static void handle_signal(int sig) {
    (void)sig;
    g_stop = 1;
}

static bool contains_icase(const char *haystack, const char *needle) {
    size_t nlen = strlen(needle);
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

static int setup_uinput_bridge(void) {
    int ufd = open("/dev/uinput", O_WRONLY | O_NONBLOCK | O_CLOEXEC);
    if (ufd < 0) {
        fprintf(stderr, "[tx-mouse-maximizer] open /dev/uinput failed: %s\n", strerror(errno));
        return -1;
    }

    static const int keys[] = {
        KEY_LEFTMETA, KEY_LEFTCTRL, KEY_LEFTALT, KEY_LEFTSHIFT,
        KEY_W, KEY_F10, KEY_SPACE, KEY_TAB
    };

    if (ioctl(ufd, UI_SET_EVBIT, EV_KEY) < 0 ||
        ioctl(ufd, UI_SET_EVBIT, EV_SYN) < 0) {
        close(ufd);
        return -1;
    }
    for (size_t i = 0; i < sizeof(keys) / sizeof(keys[0]); ++i) {
        if (ioctl(ufd, UI_SET_KEYBIT, keys[i]) < 0) {
            close(ufd);
            return -1;
        }
    }

    struct uinput_setup usetup;
    memset(&usetup, 0, sizeof(usetup));
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1d6b;
    usetup.id.product = 0x0104;
    usetup.id.version = 1;
    snprintf(usetup.name, sizeof(usetup.name), "TianxiaOS Sovereign Mouse Chord Bridge");

    if (ioctl(ufd, UI_DEV_SETUP, &usetup) < 0 ||
        ioctl(ufd, UI_DEV_CREATE) < 0) {
        fprintf(stderr, "[tx-mouse-maximizer] UI_DEV_CREATE failed: %s\n", strerror(errno));
        close(ufd);
        return -1;
    }
    return ufd;
}

static void emit_ev(int ufd, uint16_t type, uint16_t code, int32_t val) {
    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.type = type;
    ev.code = code;
    ev.value = val;
    ssize_t wr = write(ufd, &ev, sizeof(ev));
    (void)wr;
}

static void emit_chord(int ufd, uint16_t mod_key, uint16_t main_key) {
    emit_ev(ufd, EV_KEY, mod_key, 1);
    emit_ev(ufd, EV_SYN, SYN_REPORT, 0);
    emit_ev(ufd, EV_KEY, main_key, 1);
    emit_ev(ufd, EV_SYN, SYN_REPORT, 0);
    emit_ev(ufd, EV_KEY, main_key, 0);
    emit_ev(ufd, EV_SYN, SYN_REPORT, 0);
    emit_ev(ufd, EV_KEY, mod_key, 0);
    emit_ev(ufd, EV_SYN, SYN_REPORT, 0);
}

static bool is_tracked(const struct watched_mouse *mice, const char *path) {
    for (int i = 0; i < MAX_WATCHED_MICE; ++i) {
        if (mice[i].fd >= 0 && strcmp(mice[i].path, path) == 0) {
            return true;
        }
    }
    return false;
}

static void try_add_mouse(int epfd, struct watched_mouse *mice, const char *devpath) {
    if (is_tracked(mice, devpath)) {
        return;
    }
    int slot = -1;
    for (int i = 0; i < MAX_WATCHED_MICE; ++i) {
        if (mice[i].fd < 0) {
            slot = i;
            break;
        }
    }
    if (slot < 0) {
        return;
    }

    int fd = open(devpath, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) {
        return;
    }

    char name[256];
    memset(name, 0, sizeof(name));
    if (ioctl(fd, EVIOCGNAME(sizeof(name) - 1), name) < 0) {
        close(fd);
        return;
    }

    if (contains_icase(name, "TianxiaOS Sovereign") || contains_icase(name, "Touchpad")) {
        close(fd);
        return;
    }

    unsigned long relbits[NBITS(REL_MAX + 1)];
    unsigned long keybits[NBITS(KEY_MAX + 1)];
    memset(relbits, 0, sizeof(relbits));
    memset(keybits, 0, sizeof(keybits));

    if (ioctl(fd, EVIOCGBIT(EV_REL, sizeof(relbits)), relbits) < 0 ||
        ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(keybits)), keybits) < 0) {
        close(fd);
        return;
    }

    bool is_rel_xy = TEST_BIT(REL_X, relbits) && TEST_BIT(REL_Y, relbits);
    bool has_extra_btns = TEST_BIT(BTN_FORWARD, keybits) ||
                          TEST_BIT(BTN_BACK, keybits) ||
                          TEST_BIT(BTN_TASK, keybits);
    if (!is_rel_xy || !has_extra_btns) {
        close(fd);
        return;
    }

    struct epoll_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.events = EPOLLIN;
    ev.data.fd = fd;
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &ev) < 0) {
        close(fd);
        return;
    }

    mice[slot].fd = fd;
    snprintf(mice[slot].path, sizeof(mice[slot].path), "%s", devpath);
    fprintf(stdout, "[tx-mouse-maximizer] bound %s (%s) [passive 0ms non-grab mode]\n",
            devpath, name);
    fflush(stdout);
}

static void scan_input_dir(int epfd, struct watched_mouse *mice) {
    DIR *dir = opendir("/dev/input");
    if (!dir) {
        return;
    }
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
        if (strncmp(ent->d_name, "event", 5) == 0) {
            char path[512];
            snprintf(path, sizeof(path), "/dev/input/%s", ent->d_name);
            try_add_mouse(epfd, mice, path);
        }
    }
    closedir(dir);
}

static void remove_mouse_fd(int epfd, struct watched_mouse *mice, int fd) {
    for (int i = 0; i < MAX_WATCHED_MICE; ++i) {
        if (mice[i].fd == fd) {
            epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
            close(fd);
            fprintf(stdout, "[tx-mouse-maximizer] detached %s\n", mice[i].path);
            fflush(stdout);
            mice[i].fd = -1;
            mice[i].path[0] = '\0';
            return;
        }
    }
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handle_signal;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);

    int ufd = setup_uinput_bridge();
    if (ufd < 0) {
        return 1;
    }

    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd < 0) {
        ioctl(ufd, UI_DEV_DESTROY);
        close(ufd);
        return 1;
    }

    int infd = inotify_init1(IN_NONBLOCK | IN_CLOEXEC);
    if (infd >= 0) {
        inotify_add_watch(infd, "/dev/input", IN_CREATE | IN_ATTRIB);
        struct epoll_event inev = {.events = EPOLLIN, .data.fd = infd};
        epoll_ctl(epfd, EPOLL_CTL_ADD, infd, &inev);
    }

    struct watched_mouse mice[MAX_WATCHED_MICE];
    for (int i = 0; i < MAX_WATCHED_MICE; ++i) {
        mice[i].fd = -1;
        mice[i].path[0] = '\0';
    }

    scan_input_dir(epfd, mice);

    struct epoll_event events[16];
    while (!g_stop) {
        int n = epoll_wait(epfd, events, 16, 2000);
        if (n < 0) {
            if (errno == EINTR) {
                continue;
            }
            break;
        }
        for (int i = 0; i < n; ++i) {
            int cur_fd = events[i].data.fd;
            if (cur_fd == infd) {
                char ibuf[1024];
                while (read(infd, ibuf, sizeof(ibuf)) > 0) {
                }
                scan_input_dir(epfd, mice);
                continue;
            }
            if (events[i].events & (EPOLLERR | EPOLLHUP)) {
                remove_mouse_fd(epfd, mice, cur_fd);
                continue;
            }
            struct input_event ev;
            while (true) {
                ssize_t r = read(cur_fd, &ev, sizeof(ev));
                if (r < 0) {
                    if (errno == EAGAIN || errno == EWOULDBLOCK) {
                        break;
                    }
                    remove_mouse_fd(epfd, mice, cur_fd);
                    break;
                }
                if (r != (ssize_t)sizeof(ev)) {
                    break;
                }
                if (ev.type == EV_KEY && ev.value == 1) {
                    if (ev.code == BTN_TASK) {
                        // Button 8 -> KDE Plasma 6 Overview / Mission Control (Meta+W)
                        emit_chord(ufd, KEY_LEFTMETA, KEY_W);
                    } else if (ev.code == BTN_FORWARD) {
                        // Button 6 -> KDE Plasma 6 Present All Windows (Ctrl+F10)
                        emit_chord(ufd, KEY_LEFTCTRL, KEY_F10);
                    } else if (ev.code == BTN_BACK) {
                        // Button 7 -> KRunner Instant Command Launcher (Alt+Space)
                        emit_chord(ufd, KEY_LEFTALT, KEY_SPACE);
                    }
                }
            }
        }
    }

    for (int i = 0; i < MAX_WATCHED_MICE; ++i) {
        if (mice[i].fd >= 0) {
            close(mice[i].fd);
        }
    }
    if (infd >= 0) {
        close(infd);
    }
    close(epfd);
    ioctl(ufd, UI_DEV_DESTROY);
    close(ufd);
    return 0;
}
