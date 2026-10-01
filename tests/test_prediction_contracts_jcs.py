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
