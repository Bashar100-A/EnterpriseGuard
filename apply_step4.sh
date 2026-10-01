#!/usr/bin/env bash

TEST_FILE="tests/test_prediction_contracts_jcs.py"
OUTPUT_FILE="step4_report.txt"

echo "==========================================" > "$OUTPUT_FILE"
echo " EnterpriseGuard - Step 4 Implementation Report" >> "$OUTPUT_FILE"
echo " Date: $(date -u)" >> "$OUTPUT_FILE"
echo "==========================================" >> "$OUTPUT_FILE"

# Create unit tests file for JCS contracts
cat << 'PYTHON_TEST' > "$TEST_FILE"
import math
import pytest
from pydantic import ValidationError
from enterpriseguard.intelligence.prediction.contracts import (
    TypedFeatureSnapshot,
    PredictionContract,
)


def test_typed_feature_snapshot_immutability():
    snapshot = TypedFeatureSnapshot(
        snapshot_id="snap-123",
        features={"cpu_usage": 0.85, "memory_mb": 1024}
    )
    with pytest.raises(ValidationError):
        snapshot.snapshot_id = "snap-456"


def test_typed_feature_snapshot_rejects_nan_and_inf():
    with pytest.raises(ValidationError, match="contains non-serializable float value"):
        TypedFeatureSnapshot(
            snapshot_id="snap-nan",
            features={"invalid_val": math.nan}
        )

    with pytest.raises(ValidationError, match="contains non-serializable float value"):
        TypedFeatureSnapshot(
            snapshot_id="snap-inf",
            features={"invalid_val": math.inf}
        )


def test_prediction_contract_canonicalization_and_hash():
    snapshot = TypedFeatureSnapshot(
        snapshot_id="snap-001",
        features={"z_score": 1.5, "anomaly_count": 0}
    )
    contract1 = PredictionContract(
        contract_id="contract-999",
        model_name="ADIE_Detector",
        model_version="2.1.0",
        feature_snapshot=snapshot,
        prediction_value="normal",
        confidence={"score": 0.99},
        created_at="2026-09-30T12:00:00Z"
    )

    contract2 = PredictionContract(
        contract_id="contract-999",
        model_name="ADIE_Detector",
        model_version="2.1.0",
        feature_snapshot=snapshot,
        prediction_value="normal",
        confidence={"score": 0.99},
        created_at="2026-09-30T12:00:00Z"
    )

    assert contract1.canonical_bytes() == contract2.canonical_bytes()
    assert contract1.canonical_hash() == contract2.canonical_hash()
    assert isinstance(contract1.canonical_hash(), str)
    assert len(contract1.canonical_hash()) == 64
PYTHON_TEST

echo -e "\n--- [1] Running pytest on new JCS test file ---" >> "$OUTPUT_FILE"
pytest "$TEST_FILE" -v >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [2] Verification of total test suite status ---" >> "$OUTPUT_FILE"
pytest tests/ -q --maxfail=1 >> "$OUTPUT_FILE" 2>&1

echo "Done. Report generated in $OUTPUT_FILE"
