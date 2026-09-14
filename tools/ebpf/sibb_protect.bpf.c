// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#define MAX_PATH_LEN 256
#define TARGET_PREFIX "/home/bashar/.enterpriseguard/sibb"
#define EPERM 1

#define O_WRONLY 1
#define O_RDWR 2
#define O_TRUNC 01000
#define O_APPEND 02000

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

struct tamper_event {
    __u32 pid;
    __u32 uid;
    char comm[16];
    char path[MAX_PATH_LEN];
};

SSEC("lsm/file_open")
int BPF_PROG(file_open, struct file *file)
{
    return -EPERM;  // حظر كل فتح للملفات للاختبار فقط
}
    char path[MAX_PATH_LEN];
    long ret = bpf_d_path(&file->f_path, path, sizeof(path));
    if (ret < 0) return 0;

    int prefix_len = sizeof(TARGET_PREFIX) - 1;
    if (bpf_strncmp(path, prefix_len, TARGET_PREFIX) == 0) {
        struct tamper_event *evt = bpf_ringbuf_reserve(&events, sizeof(*evt), 0);
        if (evt) {
            evt->pid = bpf_get_current_pid_tgid() >> 32;
            evt->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
            bpf_get_current_comm(&evt->comm, sizeof(evt->comm));
            bpf_probe_read_kernel_str(&evt->path, sizeof(evt->path), path);
            bpf_ringbuf_submit(evt, 0);
        }
        return -EPERM;
    }
    return 0;
}

char _license[] SEC("license") = "GPL";
