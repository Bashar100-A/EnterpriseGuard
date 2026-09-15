import pytest
from pathlib import Path
from enterpriseguard.monitors.integrity_monitor import (
    compute_file_sha256,
    generate_baseline,
    load_baseline,
)

def test_compute_file_sha256(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("enterprise guard test integrity", encoding="utf-8")
    
    hash_val = compute_file_sha256(test_file)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 length

def test_baseline_generation_and_load(tmp_path):
    test_file = tmp_path / "config.json"
    test_file.write_text('{"status": "ok"}', encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"

    baseline_data = generate_baseline([test_file], output_path=baseline_path)
    assert baseline_data is not None

    loaded_data = load_baseline(baseline_path)
    assert loaded_data is not None
