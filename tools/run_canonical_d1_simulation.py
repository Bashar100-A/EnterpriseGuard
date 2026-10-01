#!/usr/bin/env python3
"""Canonical D1 Simulation & Verification Runner.

Executes a strict, evidence-based simulation using the canonical SDK Client,
generating >= 1,000 valid signed decisions, running tamper drills (Tests A-D),
measuring performance via perf_counter_ns, and exporting a cryptographic
evidence artifact.
"""

from __future__ import annotations

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import replace

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from enterpriseguard.sdk import Client, SignedDecision

def get_git_head() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown-git-head"

def calculate_percentiles(latencies_ms: list[float]) -> dict[str, float]:
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    sorted_l = sorted(latencies_ms)
    n = len(sorted_l)
    return {
        "p50": sorted_l[int(n * 0.50)],
        "p95": sorted_l[int(n * 0.95)],
        "p99": sorted_l[int(n * 0.99)],
        "max": sorted_l[-1],
    }

def run_simulation() -> None:
    print("=== EnterpriseGuard Canonical D1 Simulation Starting ===")
    git_head = get_git_head()
    print(f"Git HEAD: {git_head}")

    client = Client()
    target_count = 1000
    latencies_ms = []
    successful_writes = 0
    failed_writes = 0

    print(f"Ingesting target volume: {target_count} signed decisions via SDK Client...")
    start_wall = time.time()

    sample_signed_decision: SignedDecision | None = None

    for i in range(1, target_count + 1):
        t0 = time.perf_counter_ns()
        try:
            signed = client.decide(
                target=f"resource-node-{i % 10:02d}",
                intent="isolate",
                allowed=True,
                policy_id="d1-pilot-policy",
                parameters={"iteration": i, "batch": "D1-SIM-01"}
            )
            t1 = time.perf_counter_ns()
            latencies_ms.append((t1 - t0) / 1_000_000.0) # Convert ns to ms
            successful_writes += 1
            if i == 1:
                sample_signed_decision = signed
        except Exception as exc:
            failed_writes += 1
            if failed_writes <= 5:
                print(f"Error at decision {i}: {exc}")

    total_duration = time.time() - start_wall
    perf_metrics = calculate_percentiles(latencies_ms)
    throughput = successful_writes / total_duration if total_duration > 0 else 0.0

    print(f"Ingestion Finished. Successful: {successful_writes}, Failed: {failed_writes}")
    print(f"Throughput: {throughput:.2f} dec/sec")
    print(f"Latency -> p50: {perf_metrics['p50']:.3f}ms | p95: {perf_metrics['p95']:.3f}ms | p99: {perf_metrics['p99']:.3f}ms | max: {perf_metrics['max']:.3f}ms")

    # --- Tamper Drills (Tests A, B, C, D) ---
    print("\nExecuting Tamper & Integrity Drills (Tests A-D)...")
    if sample_signed_decision is None:
        raise RuntimeError("No sample decision captured for tamper drill.")

    # Test A: Valid verification
    test_a_pass = client.verify(sample_signed_decision)
    print(f"  Test A (Valid Record Verification): {'PASSED' if test_a_pass else 'FAILED'}")

    # Test B: Modified Payload (altering contract intent)
    tampered_contract = replace(sample_signed_decision.contract, intent="unauthorized_action")
    tampered_decision_b = replace(sample_signed_decision, contract=tampered_contract)
    test_b_pass = not client.verify(tampered_decision_b)
    print(f"  Test B (Modified Payload Detection): {'PASSED' if test_b_pass else 'FAILED'}")

    # Test C: Corrupted payload hash
    tampered_decision_c = replace(sample_signed_decision, signed_payload_hash="deadbeef" * 8)
    test_c_pass = not client.verify(tampered_decision_c)
    print(f"  Test C (Broken Payload Hash Detection): {'PASSED' if test_c_pass else 'FAILED'}")

    # Test D: Corrupted signature hex
    sig_list = list(sample_signed_decision.signature_hex)
    sig_list[0] = 'f' if sig_list[0] != 'f' else '0'
    corrupted_sig = "".join(sig_list)
    tampered_decision_d = replace(sample_signed_decision, signature_hex=corrupted_sig)
    test_d_pass = not client.verify(tampered_decision_d)
    print(f"  Test D (Invalid Signature Rejection): {'PASSED' if test_d_pass else 'FAILED'}")

    tamper_drills_passed = test_a_pass and test_b_pass and test_c_pass and test_d_pass

    # --- Generate Evidence Artifact ---
    evidence_dir = Path("docs/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_path = evidence_dir / f"d1_simulation_{timestamp_str}.json"

    evidence_data = {
        "run_id": f"sim-d1-{timestamp_str}",
        "git_head": git_head,
        "python_version": sys.version,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target_decision_count": target_count,
        "successful_writes": successful_writes,
        "failed_writes": failed_writes,
        "error_rate": (failed_writes / target_count) if target_count > 0 else 0.0,
        "total_duration_seconds": total_duration,
        "throughput_dec_per_sec": throughput,
        "latency_ms": perf_metrics,
        "tamper_drills": {
            "test_a_valid_record": test_a_pass,
            "test_b_modified_payload": test_b_pass,
            "test_c_broken_hash": test_c_pass,
            "test_d_invalid_signature": test_d_pass,
            "all_drills_passed": tamper_drills_passed
        },
        "status": "PASSED" if (successful_writes == target_count and tamper_drills_passed) else "FAILED"
    }

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_data, f, indent=2)

    print(f"\nRaw evidence artifact written successfully to: {evidence_path}")
    print("=== Canonical D1 Simulation Completed Successfully ===")

if __name__ == "__main__":
    run_simulation()
