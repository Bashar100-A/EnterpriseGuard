#!/usr/bin/env python3
"""
Load SIBB eBPF protection program and populate protected paths.
Requires root and libbpf (via bcc or native bindings).
"""

import os
import sys
import json
import ctypes
from pathlib import Path

# Attempt to use bcc library (simpler)
try:
    from bcc import BPF
    USE_BCC = True
except ImportError:
    USE_BCC = False

def load_with_bcc(config_path):
    """Load eBPF program using bcc."""
    bpf_source = Path(__file__).parent / "sibb_protect.bpf.c"
    if not bpf_source.exists():
        print(f"eBPF source not found: {bpf_source}", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    b = BPF(src_file=str(bpf_source), cflags=["-w"])

    # Populate LPM trie map
    lpm_map = b.get_table("protected_paths")
    for path in config.get("protected_paths", []):
        # LPM trie key: prefixlen (4 bytes) + data (padded)
        prefixlen = len(path.encode())
        key = ctypes.create_string_buffer(4 + 256)
        ctypes.memmove(key, ctypes.byref(ctypes.c_uint(prefixlen)), 4)
        ctypes.memmove(ctypes.byref(key, 4), path.encode(), prefixlen)
        lpm_map[key] = ctypes.c_ubyte(1).value

    print("eBPF program loaded and maps populated.")
    return b

def load_with_native_libbpf(config_path):
    """Load using native libbpf (requires libbpf and pyroute2 etc.)."""
    # Complex; recommend using bcc for prototype.
    print("Native libbpf loading not implemented in prototype. Use bcc.", file=sys.stderr)
    sys.exit(1)

def main():
    if os.geteuid() != 0:
        print("Must run as root", file=sys.stderr)
        sys.exit(1)

    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        print("config.json not found", file=sys.stderr)
        sys.exit(1)

    if USE_BCC:
        b = load_with_bcc(config_path)

        # Print trace events
        print("Monitoring tamper events... Press Ctrl+C to stop.")
        def print_event(cpu, data, size):
            event = b["events"].event(data)
            print(f"Tamper attempt: PID={event.pid} UID={event.uid} "
                  f"Comm={event.comm.decode()} Path={event.path.decode()} "
                  f"Syscall={event.syscall_id}")
        b["events"].open_ring_buffer(print_event)
        try:
            while True:
                b.ring_buffer_poll()
        except KeyboardInterrupt:
            pass
    else:
        load_with_native_libbpf(config_path)

if __name__ == "__main__":
    main()
