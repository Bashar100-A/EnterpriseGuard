#!/bin/bash
set -e

BPF_SRC="$(dirname "$0")/sibb_protect.bpf.c"
BPF_OBJ="$(dirname "$0")/sibb_protect.bpf.o"
BPF_PIN_DIR="/sys/fs/bpf/sibb_protect"

# Compile
echo "Compiling eBPF program..."
clang -O2 -g -target bpf -D__TARGET_ARCH_x86 -c "$BPF_SRC" -o "$BPF_OBJ" -I"$(dirname "$0")"

# Create pin directory
mkdir -p "$BPF_PIN_DIR"

# Load as LSM programs and pin maps
echo "Loading eBPF LSM programs..."
bpftool prog loadall "$BPF_OBJ" "$BPF_PIN_DIR" \
    type lsm pinmaps "$BPF_PIN_DIR"

# Attach LSM program using bpftool link attach
echo "Attaching LSM hook file_open..."
bpftool link attach pinned "$BPF_PIN_DIR/file_open" lsm file_open

echo "eBPF protection loaded successfully."
