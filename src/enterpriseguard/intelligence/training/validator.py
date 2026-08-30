"""
EnterpriseGuard - Training Dataset Validator
=============================================

Production-grade validation boundary for supervised training datasets.

Architectural responsibility
----------------------------

This module validates a TrainingDataset before the dataset is accepted
by the training pipeline.

Ownership boundaries
--------------------

dataset.py owns:

    - canonical feature names
    - feature count
    - feature semantics
    - feature-level validation
    - label semantics
    - TrainingDataset structure

validator.py owns:

    - dataset-level validation policy
    - minimum dataset size
    - required class presence
    - class-distribution warnings
    - immutable validation results
    - strict validation APIs
    - machine-readable validation status

This module does NOT:

    - train models
    - load models
    - save models
    - mutate model state
    - access the network
    - execute shell commands
    - mutate the supplied TrainingDataset
    - redefine feature semantics
    - redefine label semantics


Architecture
------------

    TrainingDataset
          |
          v
    validate_training_dataset()
          |
          +--> dataset.py feature validation
          |
          +--> dataset.py label validation
          |
          +--> dataset-level policy
          |
          v
    ValidationResult
          |
          +----------------------+
          |                      |
          v                      v
    Training Pipeline     TrainingDatasetValidator
                                 |
                                 +--> strict API
                                 +--> status API


Validation policy
-----------------

Hard failures:

    - invalid validator configuration
    - wrong dataset type
    - empty dataset
    - dataset below minimum size
    - invalid sample structure
    - invalid feature vector
    - invalid label
    - missing benign class
    - missing threat class

Warnings:

    - strong class imbalance

Important:

    Class imbalance is a warning, not a validation failure.

A dataset is valid only when there are no hard validation errors.


Design principles
-----------------

    - One canonical validation engine.
    - Dataset owns feature semantics.
    - Validator owns dataset-level policy.
    - Immutable validation results.
    - Deterministic validation.
    - Machine-readable results.
    - No dataset mutation.
    - No training side effects.
    - Backward-compatible functional APIs.
    - Object-oriented validator API.
    - Explicit configuration validation.
    - Defensive handling of corrupted internal dataset state.
    - Stable metadata/versioning.
    - Safe direct-module compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ============================================================================
# Dataset imports
# ============================================================================

try:
    from .dataset import (
        FEATURE_COUNT,
        FEATURE_NAMES,
        TrainingDataset,
        validate_feature_vector,
        validate_label,
    )
except ImportError:  # pragma: no cover
    # Compatibility path for direct execution from the training directory.
    # Package execution remains the canonical architecture.
    from dataset import (  # type: ignore
        FEATURE_COUNT,
        FEATURE_NAMES,
        TrainingDataset,
        validate_feature_vector,
        validate_label,
    )


# ============================================================================
# Validator metadata
# ============================================================================

VALIDATOR_NAME = (
    "EnterpriseGuard Training Dataset Validator"
)

VALIDATOR_VERSION = "2.0.0"

VALIDATOR_SCHEMA_VERSION = 3


# ============================================================================
# Validation policy
# ============================================================================

MINIMUM_SAMPLES = 4

IMBALANCE_LOW_THRESHOLD = 0.20

IMBALANCE_HIGH_THRESHOLD = 0.80


# ============================================================================
# Exceptions
# ============================================================================


class ValidationError(Exception):
    """
    Base exception for training dataset validation failures.
    """


class EmptyDatasetError(ValidationError):
    """
    Raised when a dataset contains no samples.
    """


class ClassDistributionError(ValidationError):
    """
    Raised when a dataset does not contain both required classes.

    Note:
        This exception represents a hard class-distribution failure,
        such as a missing benign or threat class.

        Strong but non-zero imbalance remains a warning.
    """


# ============================================================================
# Validation Result
# ============================================================================


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Immutable machine-readable validation result.

    The result contains no reference to the original TrainingDataset.

    This makes it safe to:

        - serialize
        - log
        - cache
        - compare
        - pass between services
        - expose through APIs

    Parameters
    ----------
    valid:
        True only when no hard validation errors exist.

    total_samples:
        Number of samples inspected.

    benign_samples:
        Number of valid labels equal to 0.

    threat_samples:
        Number of valid labels equal to 1.

    feature_count:
        Canonical feature count imported from dataset.py.

    errors:
        Hard validation failures.

    warnings:
        Non-fatal validation observations.
    """

    valid: bool

    total_samples: int

    benign_samples: int

    threat_samples: int

    feature_count: int

    errors: tuple[str, ...]

    warnings: tuple[str, ...]

    validator: str = VALIDATOR_NAME

    validator_version: str = VALIDATOR_VERSION

    schema_version: int = VALIDATOR_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """
        Return a detached machine-readable representation.

        Lists are intentionally created from the immutable tuples so
        callers cannot mutate the ValidationResult itself.
        """

        return {
            "valid": self.valid,
            "total_samples": self.total_samples,
            "benign_samples": self.benign_samples,
            "threat_samples": self.threat_samples,
            "feature_count": self.feature_count,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "validator": self.validator,
            "validator_version": self.validator_version,
            "schema_version": self.schema_version,
        }


# ============================================================================
# Internal configuration helpers
# ============================================================================


def _normalize_minimum_samples(
    minimum_samples: Any,
) -> int:
    """
    Validate and normalize minimum_samples.

    Rules
    -----

    Accepted:

        positive integers

    Rejected:

        bool
        float
        string
        None
        zero
        negative integers

    bool is rejected explicitly because Python treats bool as a subclass
    of int.
    """

    if isinstance(minimum_samples, bool):
        raise ValueError(
            "minimum_samples must be an integer greater than zero."
        )

    if not isinstance(minimum_samples, int):
        raise ValueError(
            "minimum_samples must be an integer greater than zero."
        )

    if minimum_samples < 1:
        raise ValueError(
            "minimum_samples must be greater than zero."
        )

    return minimum_samples


def _validate_imbalance_thresholds() -> None:
    """
    Validate the static class-distribution policy.

    This protects the module from accidental configuration drift.
    """

    low = IMBALANCE_LOW_THRESHOLD
    high = IMBALANCE_HIGH_THRESHOLD

    if not (0.0 <= low < high <= 1.0):
        raise ValueError(
            "Class imbalance thresholds must satisfy "
            "0 <= low < high <= 1."
        )


# ============================================================================
# Validation Result Factory
# ============================================================================


def _result(
    *,
    valid: bool,
    total_samples: int,
    benign_samples: int,
    threat_samples: int,
    errors: list[str],
    warnings: list[str],
) -> ValidationResult:
    """
    Construct the canonical immutable ValidationResult.
    """

    return ValidationResult(
        valid=bool(valid),
        total_samples=int(total_samples),
        benign_samples=int(benign_samples),
        threat_samples=int(threat_samples),
        feature_count=FEATURE_COUNT,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


# ============================================================================
# Canonical Validation Engine
# ============================================================================


def validate_training_dataset(
    dataset: TrainingDataset,
    minimum_samples: int = MINIMUM_SAMPLES,
) -> ValidationResult:
    """
    Validate a complete supervised TrainingDataset.

    This is the SINGLE canonical dataset-level validation engine.

    Validation stages
    -----------------

    1. Validator configuration
    2. Dataset type
    3. Dataset size
    4. Sample structure
    5. Feature vectors
    6. Labels
    7. Required class presence
    8. Class distribution

    Feature and label semantics are delegated to dataset.py.

    The supplied dataset is never intentionally mutated.
    """

    errors: list[str] = []

    warnings: list[str] = []

    # ------------------------------------------------------------------
    # 1. Validator configuration
    # ------------------------------------------------------------------

    try:
        normalized_minimum = _normalize_minimum_samples(
            minimum_samples
        )

        _validate_imbalance_thresholds()

    except ValueError as exc:
        return _result(
            valid=False,
            total_samples=0,
            benign_samples=0,
            threat_samples=0,
            errors=[str(exc)],
            warnings=[],
        )

    # ------------------------------------------------------------------
    # 2. Dataset type
    # ------------------------------------------------------------------

    if not isinstance(dataset, TrainingDataset):
        return _result(
            valid=False,
            total_samples=0,
            benign_samples=0,
            threat_samples=0,
            errors=[
                "dataset must be a TrainingDataset instance."
            ],
            warnings=[],
        )

    # ------------------------------------------------------------------
    # 3. Dataset size
    # ------------------------------------------------------------------

    try:
        total_samples = int(dataset.size)

    except Exception as exc:
        return _result(
            valid=False,
            total_samples=0,
            benign_samples=0,
            threat_samples=0,
            errors=[
                f"Unable to determine dataset size: {exc}"
            ],
            warnings=[],
        )

    if total_samples < 0:
        return _result(
            valid=False,
            total_samples=total_samples,
            benign_samples=0,
            threat_samples=0,
            errors=[
                "Training dataset reported a negative size."
            ],
            warnings=[],
        )

    if total_samples == 0:
        errors.append(
            "Training dataset is empty."
        )

    elif total_samples < normalized_minimum:
        errors.append(
            f"Training dataset contains {total_samples} samples; "
            f"at least {normalized_minimum} are required."
        )

    # ------------------------------------------------------------------
    # Obtain samples defensively
    # ------------------------------------------------------------------

    try:
        samples = dataset.samples

    except Exception as exc:
        errors.append(
            f"Unable to access training dataset samples: {exc}"
        )

        return _result(
            valid=False,
            total_samples=total_samples,
            benign_samples=0,
            threat_samples=0,
            errors=errors,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Internal consistency check
    # ------------------------------------------------------------------

    try:
        actual_sample_count = len(samples)

    except Exception as exc:
        errors.append(
            f"Unable to inspect training dataset samples: {exc}"
        )

        return _result(
            valid=False,
            total_samples=total_samples,
            benign_samples=0,
            threat_samples=0,
            errors=errors,
            warnings=warnings,
        )

    if actual_sample_count != total_samples:
        errors.append(
            "Training dataset size is inconsistent with its "
            "sample collection."
        )

    # ------------------------------------------------------------------
    # 4 + 5 + 6. Sample validation
    # ------------------------------------------------------------------

    benign_samples = 0

    threat_samples = 0

    for index, sample in enumerate(samples):

        # --------------------------------------------------------------
        # Sample structure
        # --------------------------------------------------------------

        if not hasattr(sample, "features"):
            errors.append(
                f"Sample {index}: missing features attribute."
            )

        if not hasattr(sample, "label"):
            errors.append(
                f"Sample {index}: missing label attribute."
            )

        if (
            not hasattr(sample, "features")
            or not hasattr(sample, "label")
        ):
            continue

        # --------------------------------------------------------------
        # Feature validation
        # --------------------------------------------------------------

        try:
            validate_feature_vector(
                sample.features
            )

        except Exception as exc:
            errors.append(
                f"Sample {index}: invalid feature vector: {exc}"
            )

        # --------------------------------------------------------------
        # Label validation
        # --------------------------------------------------------------

        try:
            label = validate_label(
                sample.label
            )

        except Exception as exc:
            errors.append(
                f"Sample {index}: invalid label: {exc}"
            )

            continue

        # --------------------------------------------------------------
        # Class counters
        # --------------------------------------------------------------

        if label == 0:
            benign_samples += 1

        elif label == 1:
            threat_samples += 1

    # ------------------------------------------------------------------
    # 7. Required class presence
    # ------------------------------------------------------------------

    if total_samples > 0:

        if benign_samples == 0:
            errors.append(
                "Training dataset contains no benign samples."
            )

        if threat_samples == 0:
            errors.append(
                "Training dataset contains no threat samples."
            )

    # ------------------------------------------------------------------
    # 8. Class distribution
    # ------------------------------------------------------------------

    if total_samples > 0:

        threat_ratio = (
            threat_samples / total_samples
        )

        if (
            threat_ratio < IMBALANCE_LOW_THRESHOLD
            or threat_ratio > IMBALANCE_HIGH_THRESHOLD
        ):
            warnings.append(
                "Dataset class distribution is strongly imbalanced."
            )

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    return _result(
        valid=len(errors) == 0,
        total_samples=total_samples,
        benign_samples=benign_samples,
        threat_samples=threat_samples,
        errors=errors,
        warnings=warnings,
    )


# ============================================================================
# TrainingDatasetValidator
# ============================================================================


class TrainingDatasetValidator:
    """
    Object-oriented dataset validation interface.

    This class intentionally contains no independent validation algorithm.

    All validation is delegated to:

        validate_training_dataset()
    """

    def __init__(
        self,
        *,
        minimum_samples: int = MINIMUM_SAMPLES,
    ) -> None:

        self.minimum_samples = (
            _normalize_minimum_samples(
                minimum_samples
            )
        )

        self._last_result: (
            ValidationResult | None
        ) = None

    # ------------------------------------------------------------------
    # Main validation API
    # ------------------------------------------------------------------

    def validate(
        self,
        dataset: TrainingDataset,
    ) -> ValidationResult:
        """
        Validate a dataset.

        The immutable result is stored as the latest validation state.
        """

        result = validate_training_dataset(
            dataset,
            minimum_samples=self.minimum_samples,
        )

        self._last_result = result

        return result

    # ------------------------------------------------------------------
    # Strict validation API
    # ------------------------------------------------------------------

    def assert_valid(
        self,
        dataset: TrainingDataset,
    ) -> ValidationResult:
        """
        Validate a dataset and raise ValidationError when invalid.
        """

        result = self.validate(
            dataset
        )

        if not result.valid:

            raise ValidationError(
                _format_validation_error(
                    result
                )
            )

        return result

    # ------------------------------------------------------------------
    # Status API
    # ------------------------------------------------------------------

    def status(
        self,
        dataset: TrainingDataset,
    ) -> dict[str, Any]:
        """
        Return machine-readable validation status.
        """

        return self.validate(
            dataset
        ).to_dict()

    # ------------------------------------------------------------------
    # Last result
    # ------------------------------------------------------------------

    @property
    def last_result(
        self,
    ) -> ValidationResult | None:
        """
        Return the most recent immutable validation result.
        """

        return self._last_result

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configuration(
        self,
    ) -> dict[str, Any]:
        """
        Return validator configuration and canonical dataset contract.
        """

        return {
            "validator": VALIDATOR_NAME,
            "version": VALIDATOR_VERSION,
            "schema_version": VALIDATOR_SCHEMA_VERSION,
            "minimum_samples": self.minimum_samples,
            "feature_count": FEATURE_COUNT,
            "feature_names": list(FEATURE_NAMES),
            "required_classes": {
                "benign": 0,
                "threat": 1,
            },
            "imbalance_warning_thresholds": {
                "low": IMBALANCE_LOW_THRESHOLD,
                "high": IMBALANCE_HIGH_THRESHOLD,
            },
        }


# ============================================================================
# Validation Error Formatting
# ============================================================================


def _format_validation_error(
    result: ValidationResult,
) -> str:
    """
    Format a deterministic strict-validation error message.
    """

    message = (
        "Training dataset validation failed."
    )

    if result.errors:
        message += " " + " | ".join(
            result.errors
        )

    return message


# ============================================================================
# Legacy Strict Validation API
# ============================================================================


def assert_valid_training_dataset(
    dataset: TrainingDataset,
    minimum_samples: int = MINIMUM_SAMPLES,
) -> ValidationResult:
    """
    Backward-compatible strict validation API.

    Raises
    ------
    ValidationError
        When the dataset is invalid.
    """

    result = validate_training_dataset(
        dataset,
        minimum_samples=minimum_samples,
    )

    if not result.valid:
        raise ValidationError(
            _format_validation_error(
                result
            )
        )

    return result


# ============================================================================
# Legacy Machine-Readable Status API
# ============================================================================


def dataset_validation_status(
    dataset: TrainingDataset,
) -> dict[str, Any]:
    """
    Backward-compatible machine-readable status API.
    """

    return validate_training_dataset(
        dataset
    ).to_dict()


# ============================================================================
# Test Dataset Helpers
# ============================================================================


def _build_invalid_feature_dataset() -> TrainingDataset:
    """
    Build a deliberately corrupted dataset.

    This bypasses normal TrainingDataset sample validation so the validator
    can prove that it detects malformed internal state.
    """

    dataset = TrainingDataset()

    class InvalidSample:
        features = {
            "request_frequency": 0.1,
        }

        label = 0

    # Intentional corruption for self-test only.
    dataset._samples = [  # type: ignore[attr-defined]
        InvalidSample()
    ]

    return dataset


def _build_invalid_label_dataset() -> TrainingDataset:
    """
    Build a deliberately corrupted dataset containing an invalid label.
    """

    dataset = TrainingDataset()

    class InvalidLabelSample:
        features = (
            0.10,
            0.02,
            0.05,
            0.10,
            1.0,
            0.05,
            0.05,
        )

        label = 99

    # Intentional corruption for self-test only.
    dataset._samples = [  # type: ignore[attr-defined]
        InvalidLabelSample()
    ]

    return dataset


def _build_imbalanced_dataset() -> TrainingDataset:
    """
    Build a strongly imbalanced but structurally valid dataset.

    Six benign samples and one threat sample produce a threat ratio
    below the configured low threshold.
    """

    dataset = TrainingDataset()

    benign_features = (
        0.10,
        0.02,
        0.05,
        0.10,
        1.0,
        0.05,
        0.05,
    )

    threat_features = (
        0.90,
        0.80,
        0.70,
        0.75,
        8.0,
        0.75,
        0.10,
    )

    for _ in range(6):
        dataset.add_raw(
            benign_features,
            0,
        )

    dataset.add_raw(
        threat_features,
        1,
    )

    return dataset


def _build_balanced_dataset() -> TrainingDataset:
    """
    Build a small balanced dataset independent from build_demo_dataset().
    """

    dataset = TrainingDataset()

    benign_features = (
        0.10,
        0.02,
        0.05,
        0.10,
        1.0,
        0.05,
        0.05,
    )

    threat_features = (
        0.90,
        0.80,
        0.70,
        0.75,
        8.0,
        0.75,
        0.10,
    )

    for _ in range(2):
        dataset.add_raw(
            benign_features,
            0,
        )

        dataset.add_raw(
            threat_features,
            1,
        )

    return dataset


# ============================================================================
# Self-Test
# ============================================================================


def _self_test() -> None:
    """
    Run comprehensive validator integration tests.

    Tests:

        1. Canonical feature contract
        2. Demo dataset
        3. Canonical validation API
        4. Object-oriented API
        5. API equivalence
        6. Machine-readable status
        7. Strict validation
        8. Last-result behavior
        9. Configuration
        10. Empty dataset rejection
        11. Minimum-size rejection
        12. Missing threat class rejection
        13. Missing benign class rejection
        14. Invalid feature rejection
        15. Invalid label rejection
        16. Class imbalance warning
        17. Balanced dataset behavior
        18. Invalid minimum_samples handling
        19. Boolean minimum_samples rejection
        20. Float minimum_samples rejection
        21. Invalid dataset type
        22. ValidationResult immutability
        23. Detached dictionary behavior
        24. Dataset non-mutation
    """

    # ------------------------------------------------------------------
    # Import demo dataset using package-safe compatibility.
    # ------------------------------------------------------------------

    try:
        from .dataset import build_demo_dataset
    except ImportError:  # pragma: no cover
        from dataset import build_demo_dataset  # type: ignore

    print("=" * 78)
    print(
        "EnterpriseGuard Training Dataset Validator - Self Test"
    )
    print("=" * 78)

    # ------------------------------------------------------------------
    # 1. Canonical feature contract
    # ------------------------------------------------------------------

    print("\n[1] Canonical feature contract")

    print(
        {
            "feature_count": FEATURE_COUNT,
            "feature_names": list(FEATURE_NAMES),
        }
    )

    assert FEATURE_COUNT == len(
        FEATURE_NAMES
    )

    assert FEATURE_COUNT == 7

    print(
        "PASS - canonical feature contract verified."
    )

    # ------------------------------------------------------------------
    # 2. Demo dataset
    # ------------------------------------------------------------------

    print("\n[2] Demo dataset")

    dataset = build_demo_dataset()

    print(
        {
            "type": type(dataset).__name__,
            "samples": dataset.size,
            "features": FEATURE_COUNT,
        }
    )

    assert isinstance(
        dataset,
        TrainingDataset,
    )

    assert dataset.size == 8

    print(
        "PASS - demo dataset created."
    )

    # ------------------------------------------------------------------
    # 3. Canonical validation API
    # ------------------------------------------------------------------

    print("\n[3] Canonical validation API")

    legacy_result = (
        validate_training_dataset(
            dataset
        )
    )

    print(
        legacy_result.to_dict()
    )

    assert legacy_result.valid is True

    assert legacy_result.total_samples == 8

    assert legacy_result.benign_samples == 4

    assert legacy_result.threat_samples == 4

    assert legacy_result.feature_count == 7

    assert not legacy_result.errors

    assert not legacy_result.warnings

    assert (
        legacy_result.validator
        == VALIDATOR_NAME
    )

    assert (
        legacy_result.validator_version
        == VALIDATOR_VERSION
    )

    assert (
        legacy_result.schema_version
        == VALIDATOR_SCHEMA_VERSION
    )

    print(
        "PASS - canonical validation succeeded."
    )

    # ------------------------------------------------------------------
    # 4. Object-oriented API
    # ------------------------------------------------------------------

    print("\n[4] TrainingDatasetValidator API")

    validator = TrainingDatasetValidator()

    class_result = validator.validate(
        dataset
    )

    print(
        class_result.to_dict()
    )

    assert class_result.valid is True

    print(
        "PASS - object-oriented validation succeeded."
    )

    # ------------------------------------------------------------------
    # 5. API equivalence
    # ------------------------------------------------------------------

    print("\n[5] API compatibility")

    assert class_result == legacy_result

    print(
        "PASS - canonical API == object-oriented API."
    )

    # ------------------------------------------------------------------
    # 6. Machine-readable status
    # ------------------------------------------------------------------

    print("\n[6] Machine-readable status")

    status = dataset_validation_status(
        dataset
    )

    print(status)

    assert status["valid"] is True

    assert status["total_samples"] == 8

    assert status["benign_samples"] == 4

    assert status["threat_samples"] == 4

    assert status["feature_count"] == 7

    assert status["errors"] == []

    assert status["warnings"] == []

    print(
        "PASS - machine-readable status verified."
    )

    # ------------------------------------------------------------------
    # 7. Strict validation
    # ------------------------------------------------------------------

    print("\n[7] Strict validation")

    assert_valid_training_dataset(
        dataset
    )

    validator.assert_valid(
        dataset
    )

    print(
        "PASS - strict validation succeeded."
    )

    # ------------------------------------------------------------------
    # 8. Last result
    # ------------------------------------------------------------------

    print("\n[8] Last result")

    assert validator.last_result == class_result

    print(
        validator.last_result.to_dict()
        if validator.last_result is not None
        else None
    )

    print(
        "PASS - last_result verified."
    )

    # ------------------------------------------------------------------
    # 9. Configuration
    # ------------------------------------------------------------------

    print("\n[9] Configuration")

    configuration = validator.configuration()

    print(configuration)

    assert (
        configuration["minimum_samples"]
        == MINIMUM_SAMPLES
    )

    assert (
        configuration["feature_count"]
        == FEATURE_COUNT
    )

    assert (
        configuration["feature_names"]
        == list(FEATURE_NAMES)
    )

    assert (
        configuration["validator"]
        == VALIDATOR_NAME
    )

    assert (
        configuration["version"]
        == VALIDATOR_VERSION
    )

    assert (
        configuration["schema_version"]
        == VALIDATOR_SCHEMA_VERSION
    )

    assert (
        configuration["required_classes"]
        == {
            "benign": 0,
            "threat": 1,
        }
    )

    print(
        "PASS - configuration verified."
    )

    # ------------------------------------------------------------------
    # 10. Empty dataset rejection
    # ------------------------------------------------------------------

    print("\n[10] Empty dataset rejection")

    empty_dataset = TrainingDataset()

    empty_result = (
        validate_training_dataset(
            empty_dataset
        )
    )

    print(
        empty_result.to_dict()
    )

    assert empty_result.valid is False

    assert any(
        "empty"
        in error.lower()
        for error in empty_result.errors
    )

    print(
        "PASS - empty dataset rejected."
    )

    # ------------------------------------------------------------------
    # 11. Minimum-size rejection
    # ------------------------------------------------------------------

    print("\n[11] Minimum-size rejection")

    small_dataset = _build_balanced_dataset()

    small_result = (
        validate_training_dataset(
            small_dataset,
            minimum_samples=5,
        )
    )

    print(
        small_result.to_dict()
    )

    assert small_result.valid is False

    assert any(
        "at least 5"
        in error
        for error in small_result.errors
    )

    print(
        "PASS - minimum dataset size enforced."
    )

    # ------------------------------------------------------------------
    # 12. Missing threat class
    # ------------------------------------------------------------------

    print("\n[12] Missing threat class rejection")

    benign_only = TrainingDataset()

    for _ in range(4):
        benign_only.add_raw(
            [
                0.10,
                0.02,
                0.05,
                0.10,
                1,
                0.05,
                0.05,
            ],
            0,
        )

    benign_result = (
        validate_training_dataset(
            benign_only
        )
    )

    print(
        benign_result.to_dict()
    )

    assert benign_result.valid is False

    assert any(
        "no threat samples"
        in error.lower()
        for error in benign_result.errors
    )

    print(
        "PASS - missing threat class rejected."
    )

    # ------------------------------------------------------------------
    # 13. Missing benign class
    # ------------------------------------------------------------------

    print("\n[13] Missing benign class rejection")

    threat_only = TrainingDataset()

    for _ in range(4):
        threat_only.add_raw(
            [
                0.90,
                0.80,
                0.70,
                0.75,
                8,
                0.75,
                0.10,
            ],
            1,
        )

    threat_result = (
        validate_training_dataset(
            threat_only
        )
    )

    print(
        threat_result.to_dict()
    )

    assert threat_result.valid is False

    assert any(
        "no benign samples"
        in error.lower()
        for error in threat_result.errors
    )

    print(
        "PASS - missing benign class rejected."
    )

    # ------------------------------------------------------------------
    # 14. Invalid feature rejection
    # ------------------------------------------------------------------

    print("\n[14] Invalid feature rejection")

    invalid_feature_dataset = (
        _build_invalid_feature_dataset()
    )

    invalid_feature_result = (
        validate_training_dataset(
            invalid_feature_dataset
        )
    )

    print(
        invalid_feature_result.to_dict()
    )

    assert invalid_feature_result.valid is False

    assert any(
        "invalid feature vector"
        in error.lower()
        for error in invalid_feature_result.errors
    )

    print(
        "PASS - invalid feature representation rejected."
    )

    # ------------------------------------------------------------------
    # 15. Invalid label rejection
    # ------------------------------------------------------------------

    print("\n[15] Invalid label rejection")

    invalid_label_dataset = (
        _build_invalid_label_dataset()
    )

    invalid_label_result = (
        validate_training_dataset(
            invalid_label_dataset
        )
    )

    print(
        invalid_label_result.to_dict()
    )

    assert invalid_label_result.valid is False

    assert any(
        "invalid label"
        in error.lower()
        for error in invalid_label_result.errors
    )

    print(
        "PASS - invalid label rejected."
    )

    # ------------------------------------------------------------------
    # 16. Class imbalance warning
    # ------------------------------------------------------------------

    print("\n[16] Class imbalance warning")

    imbalanced_dataset = (
        _build_imbalanced_dataset()
    )

    imbalanced_result = (
        validate_training_dataset(
            imbalanced_dataset
        )
    )

    print(
        imbalanced_result.to_dict()
    )

    assert imbalanced_result.valid is True

    assert any(
        "imbalanced"
        in warning.lower()
        for warning in imbalanced_result.warnings
    )

    print(
        "PASS - class imbalance warning verified."
    )

    # ------------------------------------------------------------------
    # 17. Balanced dataset behavior
    # ------------------------------------------------------------------

    print("\n[17] Balanced dataset behavior")

    balanced_dataset = (
        _build_balanced_dataset()
    )

    balanced_result = (
        validate_training_dataset(
            balanced_dataset
        )
    )

    print(
        balanced_result.to_dict()
    )

    assert balanced_result.valid is True

    assert balanced_result.benign_samples == 2

    assert balanced_result.threat_samples == 2

    assert not balanced_result.warnings

    print(
        "PASS - balanced dataset produces no warning."
    )

    # ------------------------------------------------------------------
    # 18. Invalid minimum_samples
    # ------------------------------------------------------------------

    print("\n[18] Invalid minimum_samples")

    invalid_minimum_result = (
        validate_training_dataset(
            dataset,
            minimum_samples=0,
        )
    )

    print(
        invalid_minimum_result.to_dict()
    )

    assert invalid_minimum_result.valid is False

    assert any(
        "minimum_samples"
        in error
        for error in invalid_minimum_result.errors
    )

    print(
        "PASS - invalid minimum_samples rejected."
    )

    # ------------------------------------------------------------------
    # 19. Boolean minimum_samples
    # ------------------------------------------------------------------

    print("\n[19] Boolean minimum_samples rejection")

    try:
        TrainingDatasetValidator(
            minimum_samples=True
        )

        raise AssertionError(
            "Boolean minimum_samples should have been rejected."
        )

    except ValueError:
        pass

    print(
        "PASS - boolean minimum_samples rejected."
    )

    # ------------------------------------------------------------------
    # 20. Float minimum_samples
    # ------------------------------------------------------------------

    print("\n[20] Float minimum_samples rejection")

    try:
        TrainingDatasetValidator(
            minimum_samples=4.5
        )

        raise AssertionError(
            "Float minimum_samples should have been rejected."
        )

    except ValueError:
        pass

    print(
        "PASS - float minimum_samples rejected."
    )

    # ------------------------------------------------------------------
    # 21. Invalid dataset type
    # ------------------------------------------------------------------

    print("\n[21] Invalid dataset type")

    invalid_type_result = (
        validate_training_dataset(
            dataset={"samples": []},  # type: ignore[arg-type]
        )
    )

    print(
        invalid_type_result.to_dict()
    )

    assert invalid_type_result.valid is False

    assert any(
        "TrainingDataset"
        in error
        for error in invalid_type_result.errors
    )

    print(
        "PASS - invalid dataset type rejected."
    )

    # ------------------------------------------------------------------
    # 22. ValidationResult immutability
    # ------------------------------------------------------------------

    print("\n[22] ValidationResult immutability")

    try:
        legacy_result.valid = False  # type: ignore[misc]

        raise AssertionError(
            "ValidationResult should be immutable."
        )

    except AttributeError:
        pass

    print(
        "PASS - ValidationResult immutability verified."
    )

    # ------------------------------------------------------------------
    # 23. Detached dictionary behavior
    # ------------------------------------------------------------------

    print("\n[23] Detached dictionary behavior")

    exported = legacy_result.to_dict()

    exported["errors"].append(
        "EXTERNAL_MUTATION"
    )

    exported["warnings"].append(
        "EXTERNAL_WARNING"
    )

    assert (
        "EXTERNAL_MUTATION"
        not in legacy_result.errors
    )

    assert (
        "EXTERNAL_WARNING"
        not in legacy_result.warnings
    )

    print(
        "PASS - exported dictionaries are detached."
    )

    # ------------------------------------------------------------------
    # 24. Dataset non-mutation
    # ------------------------------------------------------------------

    print("\n[24] Dataset non-mutation")

    before_size = dataset.size

    before_samples = tuple(
        dataset.samples
    )

    before_snapshot = tuple(
        (
            getattr(sample, "features", None),
            getattr(sample, "label", None),
        )
        for sample in before_samples
    )

    _ = validate_training_dataset(
        dataset
    )

    after_size = dataset.size

    after_samples = tuple(
        dataset.samples
    )

    after_snapshot = tuple(
        (
            getattr(sample, "features", None),
            getattr(sample, "label", None),
        )
        for sample in after_samples
    )

    assert before_size == after_size

    assert before_snapshot == after_snapshot

    print(
        "PASS - validator does not mutate dataset."
    )

    # ------------------------------------------------------------------
    # Final
    # ------------------------------------------------------------------

    print("\n" + "=" * 78)

    print(
        "Training Dataset Validator self-test "
        "completed successfully."
    )

    print("=" * 78)


# ============================================================================
# Entry Point
# ============================================================================


if __name__ == "__main__":
    _self_test()