#!/usr/bin/env python3
"""Benchmark signing performance: RSA vs ECDSA."""

import os
import sys
import time
from tools.signing_backend import sign_bytes

sys.dont_write_bytecode = True

MESSAGE = "benchmark-message-1234567890"
ITERATIONS = 100

def run_benchmark(backend):
    os.environ["AAAC_SIGNING_BACKEND"] = backend
    start = time.perf_counter()
    for _ in range(ITERATIONS):
        sign_bytes(MESSAGE)
    end = time.perf_counter()
    return end - start

if __name__ == "__main__":
    print(f"Running {ITERATIONS} signatures per backend...")

    # RSA
    rsa_time = run_benchmark("local")
    print(f"RSA: {rsa_time:.4f} seconds ({rsa_time/ITERATIONS*1000:.2f} ms/sig)")

    # ECDSA
    ecdsa_time = run_benchmark("ecdsa_local")
    print(f"ECDSA: {ecdsa_time:.4f} seconds ({ecdsa_time/ITERATIONS*1000:.2f} ms/sig)")

    improvement = ((rsa_time - ecdsa_time) / rsa_time) * 100 if rsa_time > 0 else 0
    print(f"\nPerformance improvement: {improvement:.1f}%")
