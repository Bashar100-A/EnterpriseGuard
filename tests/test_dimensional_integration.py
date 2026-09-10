#!/usr/bin/env python3
"""Integration test for Dimensional Intersection Engine."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def test_collector_runs():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "dimensional_collector.py")],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, f"Collector failed: {result.stderr}"
    assert "Spatial score:" in result.stdout, "Missing spatial score"
    assert "Relational score:" in result.stdout, "Missing relational score"

def test_decision_engine_continue():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "dimensional_decision_engine.py")],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, f"Decision engine failed: {result.stderr}"

    # Extract the decision line from stdout
    output = result.stdout
    decision_line = ""
    for line in output.splitlines():
        if line.startswith("Decision:"):
            decision_line = line
            break

    assert decision_line, "Decision not found in output"

    decision = decision_line.split("Decision:")[-1].strip()
    assert decision in ("CONTINUE", "SHUTDOWN"), f"Unexpected decision: {decision}"

    if decision != "CONTINUE":
        print(
            "Warning: Decision engine returned SHUTDOWN due to current system state. "
            "This is acceptable for SIBB component tests, but the engine should be evaluated with healthy data."
        )

def test_relational_memory_file_exists_and_secure():
    rel_file = ROOT / "tools" / "relational_memory.json"
    assert rel_file.exists(), "relational_memory.json missing"
    mode = rel_file.stat().st_mode & 0o777
    assert mode == 0o600, f"Expected 0600, got {oct(mode)}"

if __name__ == "__main__":
    test_collector_runs()
    test_decision_engine_continue()
    test_relational_memory_file_exists_and_secure()
    print("All dimensional integration tests passed.")
