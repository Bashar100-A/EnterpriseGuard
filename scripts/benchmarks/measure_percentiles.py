#!/usr/bin/env python3
"""Compute latency percentiles from C2 raw JSONL.

Usage:
    python3 scripts/benchmarks/measure_percentiles.py <path/to/raw.jsonl>
"""
from __future__ import annotations

import argparse
import json
import sys
from statistics import mean, median


def percentile(sorted_vals: list, p: float) -> float:
    """Linear-interpolation percentile (p in [0, 100])."""
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", help="Path to raw JSONL from run_benchmark.py")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = ap.parse_args()

    latencies: list = []
    errors = 0
    threads: set = set()

    with open(args.jsonl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "error" in row:
                errors += 1
                continue
            if row.get("success"):
                latencies.append(row["latency_ns"])
                threads.add(row["thread"])
            else:
                errors += 1

    if not latencies:
        print("No successful timings", file=sys.stderr)
        return 1

    latencies.sort()
    n = len(latencies)

    stats = {
        "samples": n,
        "errors": errors,
        "writers": len(threads),
        "min_ms": latencies[0] / 1e6,
        "p50_ms": percentile(latencies, 50) / 1e6,
        "p95_ms": percentile(latencies, 95) / 1e6,
        "p99_ms": percentile(latencies, 99) / 1e6,
        "p999_ms": percentile(latencies, 99.9) / 1e6,
        "max_ms": latencies[-1] / 1e6,
        "mean_ms": mean(latencies) / 1e6,
        "median_ms": median(latencies) / 1e6,
    }

    if args.json:
        print(json.dumps(stats, indent=2))
        return 0

    print("=== C2 Raw Timing Analysis ===")
    print(f"Samples:          {stats['samples']}")
    print(f"Errors:           {stats['errors']}")
    print(f"Distinct writers: {stats['writers']}")
    print()
    print(f"Min:              {stats['min_ms']:.3f} ms")
    print(f"p50:              {stats['p50_ms']:.3f} ms")
    print(f"p95:              {stats['p95_ms']:.3f} ms")
    print(f"p99:              {stats['p99_ms']:.3f} ms")
    print(f"p99.9:            {stats['p999_ms']:.3f} ms")
    print(f"Max:              {stats['max_ms']:.3f} ms")
    print(f"Mean:             {stats['mean_ms']:.3f} ms")
    print(f"Median:           {stats['median_ms']:.3f} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
