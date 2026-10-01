#!/usr/bin/env python3
"""Canonical SDK D1 Simulation.

Validates the canonical SDK Client's decision creation, signing,
verification, cryptographic tamper rejection, and decision latency.

This simulation does NOT prove:
- persistent storage
- SQLite/WAL performance
- WORM immutability
- first-partner onboarding
- production deployment readiness

The produced JSON file is a raw evidence artifact for this simulation.
It is not itself a signed or cryptographically protected evidence record.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository / import bootstrap
# ---------------------------------------------------------------------------

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REPO_ROOT = repo_root()
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from enterpriseguard.sdk import Client, SignedDecision  # noqa: E402


# ---------------------------------------------------------------------------
# Simulation configuration
# ---------------------------------------------------------------------------

TARGET_COUNT = 1000
SIMULATION_ID = "D1-SDK-SIMULATION"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_git_head() -> str:
    """Return the current Git HEAD hash or 'unknown' if unavailable."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "rev-parse",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def calculate_percentiles(values_ms: list[float]) -> dict[str, float]:
    """Calculate p50, p95, p99, and max latency values in milliseconds."""
    if not values_ms:
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "max": 0.0,
        }

    data = sorted(values_ms)

    if len(data) == 1:
        value = data[0]
        return {
            "p50": value,
            "p95": value,
            "p99": value,
            "max": value,
        }

    quantiles = statistics.quantiles(
        data,
        n=100,
        method="inclusive",
    )

    return {
        "p50": quantiles[49],
        "p95": quantiles[94],
        "p99": quantiles[98],
        "max": data[-1],
    }


def run_tamper_drills(
    client: Client,
    sample_signed_decision: SignedDecision,
) -> dict[str, bool]:
    """Run explicit cryptographic integrity / tamper rejection tests."""

    # Test A — untouched record must verify.
    test_a = client.verify(sample_signed_decision)

    # Test B — modify the contract after signing.
    tampered_contract = replace(
        sample_signed_decision.contract,
        allowed=not sample_signed_decision.contract.allowed,
    )

    tampered_b = replace(
        sample_signed_decision,
        contract=tampered_contract,
    )

    test_b = not client.verify(tampered_b)

    # Test C — modify the signed payload hash.
    tampered_c = replace(
        sample_signed_decision,
        signed_payload_hash="deadbeef" * 8,
    )

    test_c = not client.verify(tampered_c)

    # Test D — modify the signature.
    original_signature = sample_signed_decision.signature_hex

    if not original_signature:
        test_d = False
    else:
        modified_first_character = (
            "f"
            if original_signature[0] != "f"
            else "0"
        )

        tampered_signature = (
            modified_first_character + original_signature[1:]
        )

        tampered_d = replace(
            sample_signed_decision,
            signature_hex=tampered_signature,
        )

        test_d = not client.verify(tampered_d)

    return {
        "test_a_valid_record": test_a,
        "test_b_modified_contract": test_b,
        "test_c_modified_payload_hash": test_c,
        "test_d_modified_signature": test_d,
    }


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------

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
    successful_verifications = 0
    failed_verifications = 0

    sample_signed_decision: SignedDecision | None = None

    # Measures the decision creation/signing operation itself.
    decision_batch_start_ns = time.perf_counter_ns()

    for i in range(1, TARGET_COUNT + 1):
        operation_start_ns = time.perf_counter_ns()

        signed: SignedDecision | None = None

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
                (operation_end_ns - operation_start_ns)
                / 1_000_000.0
            )

            successful_decisions += 1

            if sample_signed_decision is None:
                sample_signed_decision = signed

        except Exception as exc:
            failed_decisions += 1

            if failed_decisions <= 5:
                print(
                    f"[ERROR] decision {i}: {exc}"
                )

            continue

        # Verification is intentionally measured separately from the
        # decision/signing latency above.
        try:
            if not client.verify(signed):
                raise RuntimeError(
                    f"Generated SignedDecision failed immediate "
                    f"verification: {i}"
                )

            successful_verifications += 1

        except Exception as exc:
            failed_verifications += 1

            if failed_verifications <= 5:
                print(
                    f"[ERROR] verification {i}: {exc}"
                )

    decision_batch_end_ns = time.perf_counter_ns()

    decision_duration_s = (
        decision_batch_end_ns - decision_batch_start_ns
    ) / 1_000_000_000.0

    finished_utc = datetime.now(timezone.utc)

    latency = calculate_percentiles(latencies_ms)

    decision_throughput = (
        successful_decisions / decision_duration_s
        if decision_duration_s > 0
        else 0.0
    )

    decision_error_rate = (
        failed_decisions / TARGET_COUNT
        if TARGET_COUNT
        else 0.0
    )

    verification_success_rate = (
        successful_verifications / successful_decisions
        if successful_decisions > 0
        else 0.0
    )

    print(
        f"SDK decisions: "
        f"{successful_decisions}/{TARGET_COUNT}"
    )

    print(
        f"SDK verifications: "
        f"{successful_verifications}/{successful_decisions}"
    )

    print(
        f"Decision error rate: "
        f"{decision_error_rate:.6f}"
    )

    print(
        f"Verification success rate: "
        f"{verification_success_rate:.6f}"
    )

    print(
        f"Decision/signing throughput: "
        f"{decision_throughput:.2f} decisions/sec"
    )

    print(
        "Decision/signing latency: "
        f"p50={latency['p50']:.3f}ms "
        f"p95={latency['p95']:.3f}ms "
        f"p99={latency['p99']:.3f}ms "
        f"max={latency['max']:.3f}ms"
    )

    if sample_signed_decision is None:
        raise RuntimeError(
            "No valid SignedDecision available for tamper tests."
        )

    # -----------------------------------------------------------------------
    # Cryptographic integrity drills
    # -----------------------------------------------------------------------

    print("\n=== SDK Cryptographic Integrity Drills ===")

    drills = run_tamper_drills(
        client,
        sample_signed_decision,
    )

    all_drills_passed = all(drills.values())

    for name, passed in drills.items():
        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    # -----------------------------------------------------------------------
    # Final simulation status
    # -----------------------------------------------------------------------

    simulation_passed = (
        successful_decisions == TARGET_COUNT
        and successful_verifications == TARGET_COUNT
        and all_drills_passed
    )

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
        "successful_verifications": successful_verifications,
        "failed_verifications": failed_verifications,
        "decision_error_rate": decision_error_rate,
        "verification_success_rate": verification_success_rate,
        "decision_duration_seconds": decision_duration_s,
        "decision_throughput_decisions_per_second": decision_throughput,
        "latency_ms": latency,
        "cryptographic_integrity_drills": {
            **drills,
            "all_passed": all_drills_passed,
        },

        # Explicit scope boundaries.
        "storage_tested": False,
        "partner_onboarding_tested": False,
        "worm_immutability_tested": False,

        # Prevents overstating the nature of the generated JSON file.
        "artifact_type": "raw_unprotected_json_evidence",
        "artifact_is_cryptographically_signed": False,

        "status": (
            "PASS"
            if simulation_passed
            else "FAIL"
        ),
    }

    # -----------------------------------------------------------------------
    # Evidence artifact
    # -----------------------------------------------------------------------

    evidence_dir = REPO_ROOT / "docs" / "evidence"
    evidence_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = finished_utc.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    evidence_path = (
        evidence_dir
        / f"d1_sdk_simulation_{timestamp}.json"
    )

    with evidence_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            evidence,
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")

    print(
        f"\nEvidence artifact: "
        f"{evidence_path}"
    )

    print(
        f"Final simulation status: "
        f"{evidence['status']}"
    )

    # Make a failed simulation visible to shell / CI callers.
    if not simulation_passed:
        raise RuntimeError(
            "D1 SDK simulation failed. "
            "Inspect the printed failures and evidence artifact."
        )


if __name__ == "__main__":
    run_simulation()
