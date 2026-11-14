// ffp: FFP-APPIMAGE-RUNTIME edge-agent c
/*
 * appimage_runtime.c — TianxiaOS Sovereign Zero-FUSE AppImage Type-2 Static Runtime
 * Compiled statically via Zig musl (`x86_64-linux-musl` and `aarch64-linux-musl`).
 *
 * Capabilities:
 *   - Direct zero-FUSE execution (`./App.AppImage [args...]`) with Kali ephemeral cleanup
 *   - `--appimage-help`
 *   - `--appimage-version`
 *   - `--appimage-offset`
 *   - `--appimage-extract [pattern]` (extracts `squashfs-root/` + `AppDir` symlink)
 *   - `--appimage-extract-and-run [args...]`
 *   - Automatic bare-kernel Android/container fallback when `/bin/sh` is absent
 */

#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#if defined(__x86_64__)
#define AI_ARCH "x86_64"
#elif defined(__aarch64__)
#define AI_ARCH "aarch64"
#else
#define AI_ARCH "linux64"
#endif

#define TRAILER_SIZE 24
static const uint8_t TRAILER_MAGIC[8] = {'T', 'X', 'A', 'I', '2', 0, 0, 0};

typedef struct {
    uint64_t offset;
    uint64_t size;
} PayloadInfo;

static uint64_t read_le64(const uint8_t *p) {
    uint64_t v = 0;
    for (int i = 0; i < 8; ++i) {
        v |= ((uint64_t)p[i]) << (i * 8);
    }
    return v;
}

static uint64_t parse_octal(const char *s, size_t n) {
    uint64_t val = 0;
    size_t i = 0;
    while (i < n && (s[i] == ' ' || s[i] == '\0')) i++;
    for (; i < n && s[i] >= '0' && s[i] <= '7'; ++i) {
        val = (val << 3) | (uint64_t)(s[i] - '0');
    }
    return val;
}

static int resolve_self_exe(const char *argv0, char *out, size_t cap) {
    ssize_t n = readlink("/proc/self/exe", out, cap - 1);
    if (n > 0) {
        out[n] = '\0';
        return 0;
    }
    if (argv0 && argv0[0]) {
        snprintf(out, cap, "%s", argv0);
        return 0;
    }
    return -1;
}

static int read_trailer(int fd, PayloadInfo *info) {
    off_t end = lseek(fd, 0, SEEK_END);
    if (end < TRAILER_SIZE) return -1;
    if (lseek(fd, end - TRAILER_SIZE, SEEK_SET) < 0) return -1;
    uint8_t buf[TRAILER_SIZE];
    ssize_t r = read(fd, buf, TRAILER_SIZE);
    if (r != TRAILER_SIZE) return -1;
    if (memcmp(buf, TRAILER_MAGIC, 8) != 0) return -1;
    info->offset = read_le64(buf + 8);
    info->size = read_le64(buf + 16);
    if (info->offset + info->size + TRAILER_SIZE > (uint64_t)end) return -1;
    return 0;
}

static int is_safe_relpath(const char *p) {
    if (!p || !p[0] || p[0] == '/') return 0;
    if (strstr(p, "..") != NULL) return 0;
    return 1;
}

static int mkdir_p(const char *dir, mode_t mode) {
    char tmp[1024];
    size_t len = strlen(dir);
    if (len == 0 || len >= sizeof(tmp)) return -1;
    memcpy(tmp, dir, len + 1);
    if (tmp[len - 1] == '/') tmp[len - 1] = '\0';
    for (char *p = tmp + 1; *p; ++p) {
        if (*p == '/') {
            *p = '\0';
            if (mkdir(tmp, mode) != 0 && errno != EEXIST) {
                return -1;
            }
            *p = '/';
        }
    }
    if (mkdir(tmp, mode) != 0 && errno != EEXIST) return -1;
    return 0;
}

static int ensure_parent_dir(const char *fullpath) {
    char tmp[1024];
    snprintf(tmp, sizeof(tmp), "%s", fullpath);
    char *slash = strrchr(tmp, '/');
    if (!slash || slash == tmp) return 0;
    *slash = '\0';
    return mkdir_p(tmp, 0755);
}

static int extract_ustar_payload(int fd, const PayloadInfo *info, const char *dest_root, int verbose, char *primary_bin, size_t primary_cap) {
    if (lseek(fd, (off_t)info->offset, SEEK_SET) < 0) return -1;
    if (mkdir_p(dest_root, 0755) != 0) return -1;

    uint64_t remaining = info->size;
    uint8_t hdr[512];
    primary_bin[0] = '\0';

    while (remaining >= 512) {
        ssize_t n = read(fd, hdr, 512);
        if (n != 512) return -1;
        remaining -= 512;

        int all_zero = 1;
        for (int i = 0; i < 512; ++i) {
            if (hdr[i] != 0) {
                all_zero = 0;
                break;
            }
        }
        if (all_zero) break;

        char name[256];
        char prefix[156];
        memcpy(prefix, hdr + 345, 155);
        prefix[155] = '\0';
        char raw_name[101];
        memcpy(raw_name, hdr, 100);
        raw_name[100] = '\0';

        if (prefix[0]) {
            snprintf(name, sizeof(name), "%s/%s", prefix, raw_name);
        } else {
            snprintf(name, sizeof(name), "%s", raw_name);
        }

        const char *rel = name;
        if (strncmp(rel, "./", 2) == 0) rel += 2;
        if (strncmp(rel, "AppDir/", 7) == 0) rel += 7;
        if (strncmp(rel, "squashfs-root/", 14) == 0) rel += 14;

        uint64_t fsize = parse_octal((const char *)(hdr + 124), 12);
        mode_t fmode = (mode_t)parse_octal((const char *)(hdr + 100), 8);
        char typeflag = (char)hdr[156];
        uint64_t padded = (fsize + 511u) & ~511ULL;

        if (!rel[0] || !is_safe_relpath(rel)) {
            if (padded > remaining) return -1;
            if (lseek(fd, (off_t)padded, SEEK_CUR) < 0) return -1;
            remaining -= padded;
            continue;
        }

        char out_path[1024];
        snprintf(out_path, sizeof(out_path), "%s/%s", dest_root, rel);

        if (verbose) {
            printf("squashfs-root/%s\n", rel);
        }

        if (strncmp(rel, "usr/bin/", 8) == 0 && rel[8] != '\0' && primary_bin[0] == '\0') {
            snprintf(primary_bin, primary_cap, "%s", out_path);
        }

        if (typeflag == '5') {
            if (mkdir_p(out_path, fmode ? fmode : 0755) != 0) return -1;
        } else if (typeflag == '2') {
            char linkname[101];
            memcpy(linkname, hdr + 157, 100);
            linkname[100] = '\0';
            if (ensure_parent_dir(out_path) != 0) return -1;
            unlink(out_path);
            if (symlink(linkname, out_path) != 0) return -1;
        } else if (typeflag == '0' || typeflag == '\0') {
            if (ensure_parent_dir(out_path) != 0) return -1;
            int out_fd = open(out_path, O_CREAT | O_TRUNC | O_WRONLY, fmode ? fmode : 0644);
            if (out_fd < 0) return -1;

            uint64_t to_copy = fsize;
            uint8_t chunk[16384];
            while (to_copy > 0) {
                size_t want = to_copy > sizeof(chunk) ? sizeof(chunk) : (size_t)to_copy;
                ssize_t got = read(fd, chunk, want);
                if (got <= 0) {
                    close(out_fd);
                    return -1;
                }
                ssize_t off = 0;
                while (off < got) {
                    ssize_t w = write(out_fd, chunk + off, (size_t)(got - off));
                    if (w <= 0) {
                        close(out_fd);
                        return -1;
                    }
                    off += w;
                }
                to_copy -= (uint64_t)got;
            }
            fchmod(out_fd, fmode ? fmode : 0644);
            close(out_fd);

            uint64_t tail = padded - fsize;
            if (tail > 0) {
                if (lseek(fd, (off_t)tail, SEEK_CUR) < 0) return -1;
            }
            if (padded > remaining) return -1;
            remaining -= padded;
            continue;
        }

        if (padded > 0) {
            if (padded > remaining) return -1;
            if (lseek(fd, (off_t)padded, SEEK_CUR) < 0) return -1;
            remaining -= padded;
        }
    }
    return 0;
}

static void rm_rf(const char *path, int depth) {
    if (depth > 8 || !path || !path[0] || strcmp(path, "/") == 0) return;
    struct stat st;
    if (lstat(path, &st) != 0) return;
    if (!S_ISDIR(st.st_mode)) {
        unlink(path);
        return;
    }
    DIR *d = opendir(path);
    if (d) {
        struct dirent *ent;
        while ((ent = readdir(d)) != NULL) {
            if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0) continue;
            char child[1024];
            snprintf(child, sizeof(child), "%s/%s", path, ent->d_name);
            rm_rf(child, depth + 1);
        }
        closedir(d);
    }
    rmdir(path);
}

static void resolve_temp_base(char *out, size_t cap) {
    const char *env_tmp = getenv("TMPDIR");
    if (env_tmp && env_tmp[0] && access(env_tmp, W_OK) == 0) {
        snprintf(out, cap, "%s", env_tmp);
        return;
    }
    if (access("/tmp", W_OK) == 0) {
        snprintf(out, cap, "/tmp");
        return;
    }
    if (access("${TMPDIR:-/tmp}", W_OK) == 0) {
        snprintf(out, cap, "${TMPDIR:-/tmp}");
        return;
    }
    snprintf(out, cap, ".");
}

static void print_appimage_help(const char *argv0) {
    printf("AppImage options for %s (TianxiaOS Zero-FUSE Type-2 Runtime [%s]):\n\n", argv0, AI_ARCH);
    printf("  --appimage-extract [PATTERN]       Extract content from embedded AppDir image to squashfs-root/\n");
    printf("  --appimage-extract-and-run [ARGS]  Run embedded AppDir directly without FUSE\n");
    printf("  --appimage-help                    Print this help message\n");
    printf("  --appimage-offset                  Print byte offset to start of embedded AppDir image\n");
    printf("  --appimage-version                 Print version of Sovereign AppImage Type-2 Runtime\n");
}

int main(int argc, char **argv) {
    char self_path[1024];
    if (resolve_self_exe(argc > 0 ? argv[0] : NULL, self_path, sizeof(self_path)) != 0) {
        fprintf(stderr, "[AppImage] ERROR: unable to locate executable path\n");
        return 127;
    }

    int fd = open(self_path, O_RDONLY);
    if (fd < 0) {
        fprintf(stderr, "[AppImage] ERROR: cannot open %s\n", self_path);
        return 127;
    }

    PayloadInfo info;
    if (read_trailer(fd, &info) != 0) {
        close(fd);
        fprintf(stderr, "[AppImage] ERROR: missing or corrupt TXAI2 payload trailer in %s\n", self_path);
        return 127;
    }

    int arg_shift = 1;
    if (argc >= 2) {
        if (strcmp(argv[1], "--appimage-help") == 0) {
            close(fd);
            print_appimage_help(argv[0]);
            return 0;
        }
        if (strcmp(argv[1], "--appimage-version") == 0) {
            close(fd);
            printf("AppImage runtime version: tx-type2-zerofuse-8.7.0 (%s)\n", AI_ARCH);
            return 0;
        }
        if (strcmp(argv[1], "--appimage-offset") == 0) {
            close(fd);
            printf("%llu\n", (unsigned long long)info.offset);
            return 0;
        }
        if (strcmp(argv[1], "--appimage-extract") == 0) {
            char primary_bin[1024];
            rm_rf("squashfs-root", 0);
            int rc = extract_ustar_payload(fd, &info, "squashfs-root", 1, primary_bin, sizeof(primary_bin));
            close(fd);
            if (rc != 0) {
                fprintf(stderr, "[AppImage] ERROR: extraction failed\n");
                return 1;
            }
            struct stat ast;
            if (lstat("AppDir", &ast) != 0) {
                symlink("squashfs-root", "AppDir");
            }
            return 0;
        }
        if (strcmp(argv[1], "--appimage-extract-and-run") == 0) {
            arg_shift = 2;
        }
    }

    char tmp_base[512];
    resolve_temp_base(tmp_base, sizeof(tmp_base));
    char mount_dir[768];
    snprintf(mount_dir, sizeof(mount_dir), "%s/.mount_Tianxia_%ld", tmp_base, (long)getpid());

    char primary_bin[1024];
    if (extract_ustar_payload(fd, &info, mount_dir, 0, primary_bin, sizeof(primary_bin)) != 0) {
        close(fd);
        rm_rf(mount_dir, 0);
        fprintf(stderr, "[AppImage] ERROR: failed to unpack ephemeral AppDir in %s\n", mount_dir);
        return 126;
    }
    close(fd);

    char apprun_path[1024];
    snprintf(apprun_path, sizeof(apprun_path), "%s/AppRun", mount_dir);

    int child_argc = argc - arg_shift + 1;
    char **child_argv = (char **)calloc((size_t)(child_argc + 1), sizeof(char *));
    if (!child_argv) {
        rm_rf(mount_dir, 0);
        return 125;
    }
    child_argv[0] = argv[0];
    for (int i = arg_shift; i < argc; ++i) {
        child_argv[i - arg_shift + 1] = argv[i];
    }
    child_argv[child_argc] = NULL;

    pid_t pid = fork();
    if (pid < 0) {
        free(child_argv);
        rm_rf(mount_dir, 0);
        return 125;
    }
    if (pid == 0) {
        setenv("APPIMAGE", self_path, 1);
        setenv("APPDIR", mount_dir, 1);
        setenv("ARGV0", argv[0], 1);
        execv(apprun_path, child_argv);
        if (primary_bin[0] != '\0') {
            child_argv[0] = primary_bin;
            execv(primary_bin, child_argv);
        }
        fprintf(stderr, "[AppImage] ERROR: exec failed (%s)\n", strerror(errno));
        _exit(127);
    }

    int status = 0;
    while (waitpid(pid, &status, 0) < 0) {
        if (errno != EINTR) break;
    }
    free(child_argv);
    rm_rf(mount_dir, 0);

    if (WIFEXITED(status)) return WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
    return 1;
}
