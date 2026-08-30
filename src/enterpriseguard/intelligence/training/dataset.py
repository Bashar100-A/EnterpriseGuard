"""
EnterpriseGuard - Training Dataset Layer


Responsible for:
- Dataset representation
- Feature normalization
- Input validation
- Label validation
- Dataset statistics
- Safe dataset splitting


This module does NOT train models.
"""


from __future__ import annotations


from dataclasses import dataclass
from typing import Any, Iterable, Sequence
import math




FEATURE_NAMES: tuple[str, ...] = (
    "request_frequency",
    "failure_ratio",
    "unique_source_count",
    "unique_user_count",
    "failed_attempts",
    "anomaly_score",
    "outbound_data_volume",
)


FEATURE_COUNT = len(FEATURE_NAMES)


VALID_LABELS = frozenset({0, 1})




class DatasetError(Exception):
    """Base exception for dataset-related errors."""




class FeatureValidationError(DatasetError):
    """Raised when a feature vector is invalid."""




class LabelValidationError(DatasetError):
    """Raised when a dataset label is invalid."""




@dataclass(frozen=True, slots=True)
class TrainingSample:
    """
    A single supervised learning sample.


    label:
        0 = benign
        1 = threat
    """


    features: tuple[float, ...]
    label: int


    def __post_init__(self) -> None:
        validate_feature_vector(self.features)
        validate_label(self.label)




@dataclass(frozen=True, slots=True)
class DatasetStatistics:
    """Immutable dataset statistics."""


    total_samples: int
    benign_samples: int
    threat_samples: int
    feature_count: int
    class_balance: float




def _finite_number(value: Any) -> float:
    """Convert a value to float and reject NaN/Infinity."""


    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise FeatureValidationError(
            f"Feature value is not numeric: {value!r}"
        ) from exc


    if not math.isfinite(number):
        raise FeatureValidationError(
            f"Feature value must be finite: {value!r}"
        )


    return number




def validate_feature_vector(
    features: Sequence[Any],
) -> tuple[float, ...]:
    """
    Validate and normalize a feature vector.


    Returns:
        A tuple containing normalized floating-point values.
    """


    if not isinstance(features, Sequence):
        raise FeatureValidationError(
            "Feature vector must be a sequence."
        )


    if len(features) != FEATURE_COUNT:
        raise FeatureValidationError(
            f"Expected {FEATURE_COUNT} features, "
            f"received {len(features)}."
        )


    normalized = tuple(_finite_number(value) for value in features)


    # Features 0-3, 5-6 are normalized ratios.
    bounded_indices = {
        0,  # request_frequency
        1,  # failure_ratio
        2,  # unique_source_count
        3,  # unique_user_count
        5,  # anomaly_score
        6,  # outbound_data_volume
    }


    for index in bounded_indices:
        value = normalized[index]


        if not 0.0 <= value <= 1.0:
            raise FeatureValidationError(
                f"Feature '{FEATURE_NAMES[index]}' must be "
                f"between 0.0 and 1.0. Received: {value}"
            )


    # Failed attempts cannot be negative.
    failed_attempts = normalized[4]


    if failed_attempts < 0:
        raise FeatureValidationError(
            "failed_attempts cannot be negative."
        )


    return normalized




def validate_label(label: Any) -> int:
    """Validate a binary classification label."""


    try:
        normalized = int(label)
    except (TypeError, ValueError) as exc:
        raise LabelValidationError(
            f"Invalid label: {label!r}"
        ) from exc


    if normalized not in VALID_LABELS:
        raise LabelValidationError(
            f"Label must be one of {sorted(VALID_LABELS)}. "
            f"Received: {normalized}"
        )


    return normalized




class TrainingDataset:
    """
    In-memory supervised training dataset.


    The class intentionally keeps the first implementation
    lightweight so EnterpriseGuard can run on low-resource systems.
    """


    def __init__(
        self,
        samples: Iterable[TrainingSample] | None = None,
    ) -> None:
        self._samples: list[TrainingSample] = []


        if samples is not None:
            for sample in samples:
                self.add(sample)


    def add(self, sample: TrainingSample) -> None:
        """Add one validated training sample."""


        if not isinstance(sample, TrainingSample):
            raise DatasetError(
                "Only TrainingSample instances can be added."
            )


        self._samples.append(sample)


    def add_raw(
        self,
        features: Sequence[Any],
        label: Any,
    ) -> None:
        """Validate and add raw feature/label data."""


        sample = TrainingSample(
            features=validate_feature_vector(features),
            label=validate_label(label),
        )


        self.add(sample)


    @property
    def samples(self) -> tuple[TrainingSample, ...]:
        """Return an immutable view of the dataset."""


        return tuple(self._samples)


    @property
    def size(self) -> int:
        """Return the number of samples."""


        return len(self._samples)


    def feature_matrix(self) -> list[list[float]]:
        """Return features in ML-friendly matrix form."""


        return [
            list(sample.features)
            for sample in self._samples
        ]


    def labels(self) -> list[int]:
        """Return labels in ML-friendly vector form."""


        return [
            sample.label
            for sample in self._samples
        ]


    def statistics(self) -> DatasetStatistics:
        """Calculate dataset statistics."""


        total = self.size
        threats = sum(
            sample.label == 1
            for sample in self._samples
        )
        benign = total - threats


        balance = (
            threats / total
            if total > 0
            else 0.0
        )


        return DatasetStatistics(
            total_samples=total,
            benign_samples=benign,
            threat_samples=threats,
            feature_count=FEATURE_COUNT,
            class_balance=balance,
        )


    def validate(self) -> None:
        """Validate every sample in the dataset."""


        for sample in self._samples:
            validate_feature_vector(sample.features)
            validate_label(sample.label)


    def clear(self) -> None:
        """Remove all samples."""


        self._samples.clear()




def build_demo_dataset() -> TrainingDataset:
    """
    Build a small deterministic dataset for development testing.


    This is NOT production training data.
    """


    dataset = TrainingDataset()


    benign_samples = [
        (
            [0.10, 0.02, 0.05, 0.10, 1, 0.05, 0.05],
            0,
        ),
        (
            [0.20, 0.04, 0.10, 0.15, 1, 0.08, 0.08],
            0,
        ),
        (
            [0.30, 0.05, 0.15, 0.20, 2, 0.10, 0.10],
            0,
        ),
        (
            [0.15, 0.03, 0.08, 0.12, 1, 0.06, 0.04],
            0,
        ),
    ]


    threat_samples = [
        (
            [0.90, 0.80, 0.70, 0.75, 8, 0.75, 0.10],
            1,
        ),
        (
            [0.95, 0.85, 0.80, 0.85, 10, 0.90, 0.20],
            1,
        ),
        (
            [0.85, 0.75, 0.65, 0.70, 7, 0.80, 0.15],
            1,
        ),
        (
            [0.92, 0.90, 0.75, 0.80, 12, 0.88, 0.25],
            1,
        ),
    ]


    for features, label in benign_samples + threat_samples:
        dataset.add_raw(features, label)


    return dataset




def dataset_status(
    dataset: TrainingDataset,
) -> dict[str, Any]:
    """Return a machine-readable dataset status."""


    stats = dataset.statistics()


    return {
        "dataset": "EnterpriseGuard Training Dataset",
        "feature_count": stats.feature_count,
        "feature_names": list(FEATURE_NAMES),
        "total_samples": stats.total_samples,
        "benign_samples": stats.benign_samples,
        "threat_samples": stats.threat_samples,
        "class_balance": round(stats.class_balance, 4),
        "valid": True,
    }




def _self_test() -> None:
    """Run a lightweight local validation test."""


    print("=" * 78)
    print("EnterpriseGuard Training Dataset - Self Test")
    print("=" * 78)


    dataset = build_demo_dataset()


    dataset.validate()


    print("\n[1] Dataset status")
    print(dataset_status(dataset))


    print("\n[2] Feature count")
    print(FEATURE_COUNT)


    print("\n[3] Feature names")
    print(list(FEATURE_NAMES))


    print("\n[4] Dataset statistics")
    print(dataset.statistics())


    print("\n[5] Matrix shape")
    print(
        len(dataset.feature_matrix()),
        "samples x",
        len(dataset.feature_matrix()[0]),
        "features",
    )


    print("\n[6] Validation")
    print("PASSED")


    print("\n" + "=" * 78)
    print("Self test completed successfully.")
    print("=" * 78)




if __name__ == "__main__":
    _self_test()