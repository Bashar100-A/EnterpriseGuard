#!/usr/bin/env python3
"""Canonical SDK D1 Simulation.

Validates the canonical SDK Client's decision creation, signing,
verification, cryptographic tamper rejection, and latency.

This simulation does NOT prove persistence, SQLite/WAL performance,
WORM immutability, or first-partner onboarding.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import replace

from enterpriseguard.sdk import Client, SignedDecision


TARGET_COUNT = 1000
SIMULATION_ID = "D1-SDK-SIMULATION"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_git_head() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root()), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def calculate_percentiles(values_ms: list[float]) -> dict[str, float]:
    if not values_ms:
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "max": 0.0,
        }

    data = sorted(values_ms)

    if len(data) == 1:
        return {
            "p50": data[0],
            "p95": data[0],
            "p99": data[0],
            "max": data[0],
        }

    q = statistics.quantiles(data, n=100, method="inclusive")

    return {
        "p50": q[49],
        "p95": q[94],
        "p99": q[98],
        "max": data[-1],
    }


def run_simulation() -> None:
    print("=== EnterpriseGuard D1 SDK Simulation ===")

    started_utc = datetime.now(timezone.utc)
    git_head = get_git_head()

    print(f"Simulation: {SIMULATION_ID}")
    print(f"Git HEAD: {git_head}")
    print(f"Target decisions: {TARGET_COUNT}")

    client = Client()

    latencies_ms: list[float] = []
    successful_decisions = 0
    failed_decisions = 0

    sample_signed_decision: SignedDecision | None = None

    start_ns = time.perf_counter_ns()

    for i in range(1, TARGET_COUNT + 1):
        operation_start_ns = time.perf_counter_ns()

        try:
            signed = client.decide(
                target=f"resource-node-{i % 10:02d}",
                intent="isolate",
                allowed=True,
                policy_id="d1-pilot-policy",
                parameters={
                    "iteration": i,
                    "simulation_id": SIMULATION_ID,
                },
            )

            operation_end_ns = time.perf_counter_ns()

            latencies_ms.append(
                (operation_end_ns - operation_start_ns) / 1_000_000.0
            )

            if not client.verify(signed):
                raise RuntimeError(
                    f"Generated SignedDecision failed immediate verification: {i}"
                )

            successful_decisions += 1

            if sample_signed_decision is None:
                sample_signed_decision = signed

        except Exception as exc:
            failed_decisions += 1

            if failed_decisions <= 5:
                print(f"[ERROR] decision {i}: {exc}")

    total_duration_s = (
        time.perf_counter_ns() - start_ns
    ) / 1_000_000_000.0

    latency = calculate_percentiles(latencies_ms)

    throughput = (
        successful_decisions / total_duration_s
        if total_duration_s > 0
        else 0.0
    )

    error_rate = (
        failed_decisions / TARGET_COUNT
        if TARGET_COUNT
        else 0.0
    )

    print(
        f"SDK decisions: {successful_decisions}/{TARGET_COUNT}"
    )
    print(f"Error rate: {error_rate:.6f}")
    print(f"Throughput: {throughput:.2f} decisions/sec")
    print(
        "Latency: "
        f"p50={latency['p50']:.3f}ms "
        f"p95={latency['p95']:.3f}ms "
        f"p99={latency['p99']:.3f}ms "
        f"max={latency['max']:.3f}ms"
    )

    if sample_signed_decision is None:
        raise RuntimeError("No valid SignedDecision available for tamper tests.")

    print("\n=== SDK Cryptographic Integrity Drills ===")

    # Test A — valid verification
    test_a = client.verify(sample_signed_decision)

    # Test B — modified contract
    tampered_contract = replace(
        sample_signed_decision.contract,
        intent="unauthorized_action",
    )
    tampered_b = replace(
        sample_signed_decision,
        contract=tampered_contract,
    )
    test_b = not client.verify(tampered_b)

    # Test C — modified signed payload hash
    tampered_c = replace(
        sample_signed_decision,
        signed_payload_hash="deadbeef" * 8,
    )
    test_c = not client.verify(tampered_c)

    # Test D — modified signature
    signature = list(sample_signed_decision.signature_hex)
    signature[0] = "f" if signature[0] != "f" else "0"

    tampered_d = replace(
        sample_signed_decision,
        signature_hex="".join(signature),
    )
    test_d = not client.verify(tampered_d)

    drills = {
        "test_a_valid_record": test_a,
        "test_b_modified_contract": test_b,
        "test_c_modified_payload_hash": test_c,
        "test_d_modified_signature": test_d,
    }

    all_drills_passed = all(drills.values())

    for name, passed in drills.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    finished_utc = datetime.now(timezone.utc)

    evidence = {
        "evidence_type": "D1_SDK_SIMULATION",
        "simulation_id": SIMULATION_ID,
        "git_head": git_head,
        "started_at_utc": started_utc.isoformat(),
        "finished_at_utc": finished_utc.isoformat(),
        "python_version": sys.version,
        "target_decisions": TARGET_COUNT,
        "successful_signed_decisions": successful_decisions,
        "failed_decisions": failed_decisions,
        "error_rate": error_rate,
        "duration_seconds": total_duration_s,
        "throughput_decisions_per_second": throughput,
        "latency_ms": latency,
        "cryptographic_integrity_drills": {
            **drills,
            "all_passed": all_drills_passed,
        },
        "storage_tested": False,
        "partner_onboarding_tested": False,
        "worm_immutability_tested": False,
        "status": (
            "PASS"
            if successful_decisions == TARGET_COUNT
            and all_drills_passed
            else "FAIL"
        ),
    }

    evidence_dir = repo_root() / "docs" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = finished_utc.strftime("%Y%m%dT%H%M%SZ")
    evidence_path = evidence_dir / f"d1_sdk_simulation_{timestamp}.json"

    with evidence_path.open("w", encoding="utf-8") as handle:
        json.dump(
            evidence,
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")

    print(f"\nEvidence artifact: {evidence_path}")
    print(f"Final simulation status: {evidence['status']}")


if __name__ == "__main__":
    # The repository's src-layout should be supplied by the caller/environment.
    if "src" not in sys.path:
        sys.path.insert(
            0,
            str(repo_root() / "src"),
        )

    run_simulation()
