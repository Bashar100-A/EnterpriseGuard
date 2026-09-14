#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include <errno.h>

static volatile bool running = true;

void int_handler(int sig) {
    running = false;
}

int main(int argc, char **argv) {
    struct bpf_object *obj;
    struct bpf_program *prog;
    struct bpf_link *link = NULL;
    int err;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <bpf_object_file>\n", argv[0]);
        return 1;
    }

    // Open BPF object
    obj = bpf_object__open_file(argv[1], NULL);
    if (libbpf_get_error(obj)) {
        fprintf(stderr, "Failed to open BPF object: %s\n", strerror(errno));
        return 1;
    }

    // Load programs
    err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "Failed to load BPF object: %d\n", err);
        return 1;
    }

    // Attach LSM programs
    bpf_object__for_each_program(prog, obj) {
        link = bpf_program__attach_lsm(prog);
        if (libbpf_get_error(link)) {
            fprintf(stderr, "Failed to attach LSM program: %s\n", strerror(errno));
            return 1;
        }
    }

    printf("SIBB eBPF protection loaded and attached. Press Ctrl+C to exit.\n");

    // Set signal handler
    signal(SIGINT, int_handler);
    signal(SIGTERM, int_handler);

    // Keep running
    while (running) {
        sleep(1);
    }

    // Cleanup
    bpf_link__destroy(link);
    bpf_object__close(obj);
    return 0;
}
