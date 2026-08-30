"""
EnterpriseGuard - ADIE Prediction Contracts
============================================

Adaptive Defense Intelligence Engine (ADIE)

Prediction Domain Contracts
----------------------------

This module defines the immutable domain contracts used by the
ADIE prediction layer.

Architecture
------------

    EnterpriseState
          |
          v
    Prediction Input
          |
          v
    Prediction Engine
          |
          v
    Prediction Result
          |
          v
    Policy / Decision Layer


Design Principles
-----------------

The prediction contract layer is intentionally:

- immutable
- deterministic in structure
- framework-independent
- serialization-safe
- validation-oriented
- domain-focused
- independent from UI
- independent from DashboardService
- independent from Detector
- independent from ModelManager
- independent from training
- independent from filesystem
- independent from networking

This module defines WHAT a prediction means.

It does not define HOW prediction is performed.


Contract Hierarchy
------------------

PredictionTarget
        |
        v
PredictionEvidence
        |
        v
PredictionCandidate
        |
        v
PredictionResult


PredictionRequest
        |
        v
PredictionResult


Temporal semantics
------------------

ADIE operates on evolving enterprise state.

Therefore predictions carry:

- reference timestamp
- prediction horizon
- generated timestamp
- confidence
- predicted state/action
- supporting evidence
- model metadata


No prediction contract is allowed to mutate after creation.
"""


from __future__ import annotations


# ============================================================================
# Standard library
# ============================================================================

import dataclasses

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence


# ============================================================================
# Module metadata
# ============================================================================

__all__ = [
    "PredictionStatus",
    "PredictionTarget",
    "PredictionEvidence",
    "PredictionCandidate",
    "PredictionRequest",
    "PredictionResult",
]


# ============================================================================
# Utility functions
# ============================================================================


def _utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


def _ensure_utc(
    value: datetime,
) -> datetime:
    """
    Normalize a datetime to timezone-aware UTC.

    Naive datetimes are rejected because temporal prediction
    contracts must never silently mix local and UTC time.
    """

    if not isinstance(value, datetime):
        raise TypeError(
            "timestamp must be a datetime"
        )

    if value.tzinfo is None:
        raise ValueError(
            "timestamp must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _validate_non_empty_string(
    value: str,
    field_name: str,
) -> str:
    """
    Validate a required non-empty string.
    """

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    return normalized


def _validate_probability(
    value: float,
    field_name: str,
) -> float:
    """
    Validate a normalized probability/confidence value.
    """

    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be a number between 0 and 1"
        )

    try:
        numeric = float(value)

    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"{field_name} must be a number between 0 and 1"
        ) from exc

    if not 0.0 <= numeric <= 1.0:
        raise ValueError(
            f"{field_name} must be between 0 and 1"
        )

    return numeric


def _validate_positive_int(
    value: int,
    field_name: str,
) -> int:
    """
    Validate a positive integer.
    """

    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be a positive integer"
        )

    if not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be a positive integer"
        )

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero"
        )

    return value


def _freeze_mapping(
    value: Mapping[str, Any] | None,
) -> tuple[tuple[str, Any], ...]:
    """
    Convert a mapping into an immutable tuple representation.

    The prediction contracts deliberately avoid exposing mutable
    dictionaries internally.
    """

    if value is None:
        return ()

    if not isinstance(value, Mapping):
        raise TypeError(
            "metadata must be a mapping"
        )

    normalized: list[tuple[str, Any]] = []

    for key, item in value.items():

        if not isinstance(key, str):
            raise TypeError(
                "metadata keys must be strings"
            )

        normalized.append(
            (
                key,
                item,
            )
        )

    return tuple(normalized)


def _mapping_from_frozen(
    value: tuple[tuple[str, Any], ...],
) -> dict[str, Any]:
    """
    Convert immutable mapping representation into a plain dictionary.
    """

    return {
        key: item
        for key, item in value
    }


def _validate_sequence(
    value: Sequence[Any],
    field_name: str,
) -> tuple[Any, ...]:
    """
    Normalize a sequence into an immutable tuple.
    """

    if isinstance(value, (str, bytes)):
        raise TypeError(
            f"{field_name} must be a sequence of values"
        )

    try:
        return tuple(value)

    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be a sequence"
        ) from exc


# ============================================================================
# Prediction status
# ============================================================================


class PredictionStatus(str, Enum):
    """
    Lifecycle status of a prediction result.
    """

    GENERATED = "generated"

    ACCEPTED = "accepted"

    REJECTED = "rejected"

    EXPIRED = "expired"

    INVALID = "invalid"


# ============================================================================
# Prediction target
# ============================================================================


@dataclass(frozen=True, slots=True)
class PredictionTarget:
    """
    Describes what the prediction engine is attempting to predict.

    Examples
    --------

    target_type="next_action"
    target_type="risk_change"
    target_type="security_state"
    """

    target_type: str

    target_id: str | None = None

    horizon_seconds: int = 300

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "target_type",
            _validate_non_empty_string(
                self.target_type,
                "target_type",
            ),
        )

        if self.target_id is not None:

            object.__setattr__(
                self,
                "target_id",
                _validate_non_empty_string(
                    self.target_id,
                    "target_id",
                ),
            )

        object.__setattr__(
            self,
            "horizon_seconds",
            _validate_positive_int(
                self.horizon_seconds,
                "horizon_seconds",
            ),
        )


# ============================================================================
# Prediction evidence
# ============================================================================


@dataclass(frozen=True, slots=True)
class PredictionEvidence:
    """
    Immutable evidence supporting a prediction.

    Evidence is descriptive.

    It does not execute actions and does not make policy decisions.
    """

    source: str

    feature: str

    value: Any

    weight: float = 1.0

    timestamp: datetime = field(
        default_factory=_utc_now
    )

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "source",
            _validate_non_empty_string(
                self.source,
                "source",
            ),
        )

        object.__setattr__(
            self,
            "feature",
            _validate_non_empty_string(
                self.feature,
                "feature",
            ),
        )

        object.__setattr__(
            self,
            "weight",
            _validate_probability(
                self.weight,
                "weight",
            ),
        )

        object.__setattr__(
            self,
            "timestamp",
            _ensure_utc(
                self.timestamp
            ),
        )


# ============================================================================
# Prediction candidate
# ============================================================================


@dataclass(frozen=True, slots=True)
class PredictionCandidate:
    """
    Represents one possible future outcome.

    Multiple candidates can exist in a prediction result.

    Example:

        block       0.72
        challenge   0.18
        allow       0.10
    """

    value: str

    probability: float

    rank: int

    evidence: tuple[PredictionEvidence, ...] = ()

    metadata: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "value",
            _validate_non_empty_string(
                self.value,
                "value",
            ),
        )

        object.__setattr__(
            self,
            "probability",
            _validate_probability(
                self.probability,
                "probability",
            ),
        )

        object.__setattr__(
            self,
            "rank",
            _validate_positive_int(
                self.rank,
                "rank",
            ),
        )

        evidence = _validate_sequence(
            self.evidence,
            "evidence",
        )

        for item in evidence:

            if not isinstance(
                item,
                PredictionEvidence,
            ):
                raise TypeError(
                    "evidence must contain PredictionEvidence objects"
                )

        object.__setattr__(
            self,
            "evidence",
            evidence,
        )

        metadata = tuple(
            self.metadata
        )

        for key, _ in metadata:

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    "metadata keys must be strings"
                )

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the candidate into a plain dictionary.
        """

        return {
            "value": self.value,
            "probability": self.probability,
            "rank": self.rank,
            "evidence": [
                {
                    "source": item.source,
                    "feature": item.feature,
                    "value": item.value,
                    "weight": item.weight,
                    "timestamp": item.timestamp.isoformat(),
                }
                for item in self.evidence
            ],
            "metadata": _mapping_from_frozen(
                self.metadata
            ),
        }


# ============================================================================
# Prediction request
# ============================================================================


@dataclass(frozen=True, slots=True)
class PredictionRequest:
    """
    Immutable request submitted to the prediction layer.

    The request describes:

    - the current temporal reference
    - the prediction target
    - optional state identifier
    - optional contextual metadata

    The request does not contain a model instance.
    """

    target: PredictionTarget

    reference_time: datetime = field(
        default_factory=_utc_now
    )

    state_id: str | None = None

    context: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:

        if not isinstance(
            self.target,
            PredictionTarget,
        ):
            raise TypeError(
                "target must be a PredictionTarget"
            )

        object.__setattr__(
            self,
            "reference_time",
            _ensure_utc(
                self.reference_time
            ),
        )

        if self.state_id is not None:

            object.__setattr__(
                self,
                "state_id",
                _validate_non_empty_string(
                    self.state_id,
                    "state_id",
                ),
            )

        context = tuple(
            self.context
        )

        for key, _ in context:

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    "context keys must be strings"
                )

        object.__setattr__(
            self,
            "context",
            context,
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the request.
        """

        return {
            "target": {
                "target_type": self.target.target_type,
                "target_id": self.target.target_id,
                "horizon_seconds": self.target.horizon_seconds,
            },
            "reference_time": (
                self.reference_time.isoformat()
            ),
            "state_id": self.state_id,
            "context": _mapping_from_frozen(
                self.context
            ),
        }


# ============================================================================
# Prediction result
# ============================================================================


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """
    Immutable result produced by the ADIE prediction layer.

    This is the primary prediction contract.

    Important
    ---------

    PredictionResult does not:

    - execute a response
    - authorize an action
    - change enterprise state
    - call a detector
    - call a policy engine

    It only describes the predicted future.
    """

    request: PredictionRequest

    candidates: tuple[PredictionCandidate, ...]

    generated_at: datetime = field(
        default_factory=_utc_now
    )

    model_version: str = "unknown"

    status: PredictionStatus = (
        PredictionStatus.GENERATED
    )

    prediction_id: str | None = None

    metadata: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:

        if not isinstance(
            self.request,
            PredictionRequest,
        ):
            raise TypeError(
                "request must be a PredictionRequest"
            )

        candidates = _validate_sequence(
            self.candidates,
            "candidates",
        )

        for candidate in candidates:

            if not isinstance(
                candidate,
                PredictionCandidate,
            ):
                raise TypeError(
                    "candidates must contain PredictionCandidate objects"
                )

        if not candidates:

            raise ValueError(
                "prediction result must contain at least one candidate"
            )

        probabilities = [
            candidate.probability
            for candidate in candidates
        ]

        total_probability = sum(
            probabilities
        )

        if total_probability <= 0.0:

            raise ValueError(
                "candidate probabilities must have a positive total"
            )

        object.__setattr__(
            self,
            "candidates",
            candidates,
        )

        object.__setattr__(
            self,
            "generated_at",
            _ensure_utc(
                self.generated_at
            ),
        )

        object.__setattr__(
            self,
            "model_version",
            _validate_non_empty_string(
                self.model_version,
                "model_version",
            ),
        )

        if not isinstance(
            self.status,
            PredictionStatus,
        ):

            try:
                status = PredictionStatus(
                    self.status
                )

            except ValueError as exc:

                raise ValueError(
                    "status must be a valid PredictionStatus"
                ) from exc

            object.__setattr__(
                self,
                "status",
                status,
            )

        if self.prediction_id is not None:

            object.__setattr__(
                self,
                "prediction_id",
                _validate_non_empty_string(
                    self.prediction_id,
                    "prediction_id",
                ),
            )

        metadata = tuple(
            self.metadata
        )

        for key, _ in metadata:

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    "metadata keys must be strings"
                )

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    # ------------------------------------------------------------------------
    # Primary prediction
    # ------------------------------------------------------------------------

    @property
    def top_candidate(
        self,
    ) -> PredictionCandidate:
        """
        Return the highest-probability candidate.
        """

        return max(
            self.candidates,
            key=lambda item: item.probability,
        )

    # ------------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------------

    @property
    def confidence(
        self,
    ) -> float:
        """
        Return the probability of the top candidate.
        """

        return self.top_candidate.probability

    # ------------------------------------------------------------------------
    # Predicted value
    # ------------------------------------------------------------------------

    @property
    def predicted_value(
        self,
    ) -> str:
        """
        Return the most probable predicted value.
        """

        return self.top_candidate.value

    # ------------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the complete prediction result.
        """

        return {
            "prediction_id": self.prediction_id,
            "status": self.status.value,
            "model_version": self.model_version,
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "request": self.request.to_dict(),
            "predicted_value": self.predicted_value,
            "confidence": self.confidence,
            "candidates": [
                candidate.to_dict()
                for candidate in self.candidates
            ],
            "metadata": _mapping_from_frozen(
                self.metadata
            ),
        }

    # ------------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------------

    @classmethod
    def from_candidates(
        cls,
        request: PredictionRequest,
        candidates: Sequence[PredictionCandidate],
        *,
        model_version: str = "unknown",
        prediction_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "PredictionResult":
        """
        Construct a PredictionResult from candidate predictions.
        """

        return cls(
            request=request,
            candidates=tuple(
                candidates
            ),
            model_version=model_version,
            prediction_id=prediction_id,
            metadata=_freeze_mapping(
                metadata
            ),
        )


# ============================================================================
# Contract validation
# ============================================================================


def validate_prediction_request(
    request: PredictionRequest,
) -> None:
    """
    Validate a prediction request.

    Raises
    ------

    TypeError
        If the object is not a PredictionRequest.

    ValueError
        If the request contains invalid temporal data.
    """

    if not isinstance(
        request,
        PredictionRequest,
    ):
        raise TypeError(
            "request must be a PredictionRequest"
        )

    _ensure_utc(
        request.reference_time
    )

    if request.target.horizon_seconds <= 0:
        raise ValueError(
            "prediction horizon must be positive"
        )


def validate_prediction_result(
    result: PredictionResult,
) -> None:
    """
    Validate a prediction result.

    This function intentionally performs contract validation only.
    """

    if not isinstance(
        result,
        PredictionResult,
    ):
        raise TypeError(
            "result must be a PredictionResult"
        )

    validate_prediction_request(
        result.request
    )

    if not result.candidates:
        raise ValueError(
            "prediction result must contain candidates"
        )

    for candidate in result.candidates:

        if not 0.0 <= candidate.probability <= 1.0:
            raise ValueError(
                "candidate probability must be between 0 and 1"
            )

    _ensure_utc(
        result.generated_at
    )


# ============================================================================
# Public helpers
# ============================================================================


def prediction_to_dict(
    result: PredictionResult,
) -> dict[str, Any]:
    """
    Public serialization helper.
    """

    validate_prediction_result(
        result
    )

    return result.to_dict()


def is_prediction_successful(
    result: PredictionResult,
) -> bool:
    """
    Return True when the prediction result is usable.
    """

    if not isinstance(
        result,
        PredictionResult,
    ):
        return False

    return (
        result.status
        in {
            PredictionStatus.GENERATED,
            PredictionStatus.ACCEPTED,
        }
        and result.confidence >= 0.0
    )


# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Comprehensive isolated self-test for prediction contracts.

    The test does not use:

    - models
    - detectors
    - training
    - filesystem
    - network
    - Streamlit
    - DashboardService
    - DecisionOrchestrator
    """

    # ------------------------------------------------------------------------
    # Test 1: enum
    # ------------------------------------------------------------------------

    assert (
        PredictionStatus.GENERATED.value
        == "generated"
    )

    # ------------------------------------------------------------------------
    # Test 2: target
    # ------------------------------------------------------------------------

    target = PredictionTarget(
        target_type="next_action",
        target_id="entity-001",
        horizon_seconds=300,
    )

    assert target.target_type == "next_action"

    assert target.target_id == "entity-001"

    assert target.horizon_seconds == 300

    # ------------------------------------------------------------------------
    # Test 3: evidence
    # ------------------------------------------------------------------------

    evidence = PredictionEvidence(
        source="state",
        feature="risk_score",
        value=0.82,
        weight=0.9,
    )

    assert evidence.source == "state"

    assert evidence.feature == "risk_score"

    assert evidence.weight == 0.9

    assert evidence.timestamp.tzinfo is not None

    # ------------------------------------------------------------------------
    # Test 4: candidate
    # ------------------------------------------------------------------------

    candidate = PredictionCandidate(
        value="challenge",
        probability=0.72,
        rank=1,
        evidence=(evidence,),
        metadata=(
            (
                "reason",
                "elevated_risk",
            ),
        ),
    )

    assert candidate.value == "challenge"

    assert candidate.probability == 0.72

    assert candidate.rank == 1

    assert len(candidate.evidence) == 1

    # ------------------------------------------------------------------------
    # Test 5: request
    # ------------------------------------------------------------------------

    request = PredictionRequest(
        target=target,
        state_id="state-001",
        context=(
            (
                "source",
                "enterprise_state",
            ),
        ),
    )

    assert request.target == target

    assert request.state_id == "state-001"

    assert request.context[0][0] == "source"

    # ------------------------------------------------------------------------
    # Test 6: result
    # ------------------------------------------------------------------------

    second_candidate = PredictionCandidate(
        value="allow",
        probability=0.28,
        rank=2,
    )

    result = PredictionResult(
        request=request,
        candidates=(
            candidate,
            second_candidate,
        ),
        model_version="adie-predictor-1.0",
        prediction_id="prediction-001",
    )

    assert result.status == PredictionStatus.GENERATED

    assert result.model_version == "adie-predictor-1.0"

    assert result.prediction_id == "prediction-001"

    # ------------------------------------------------------------------------
    # Test 7: top candidate
    # ------------------------------------------------------------------------

    assert (
        result.top_candidate
        == candidate
    )

    assert (
        result.predicted_value
        == "challenge"
    )

    assert (
        result.confidence
        == 0.72
    )

    # ------------------------------------------------------------------------
    # Test 8: serialization
    # ------------------------------------------------------------------------

    serialized = result.to_dict()

    assert isinstance(
        serialized,
        dict,
    )

    assert (
        serialized["prediction_id"]
        == "prediction-001"
    )

    assert (
        serialized["predicted_value"]
        == "challenge"
    )

    assert (
        serialized["confidence"]
        == 0.72
    )

    assert isinstance(
        serialized["candidates"],
        list,
    )

    # ------------------------------------------------------------------------
    # Test 9: public serializer
    # ------------------------------------------------------------------------

    public_serialized = prediction_to_dict(
        result
    )

    assert (
        public_serialized
        == serialized
    )

    # ------------------------------------------------------------------------
    # Test 10: validation
    # ------------------------------------------------------------------------

    validate_prediction_request(
        request
    )

    validate_prediction_result(
        result
    )

    # ------------------------------------------------------------------------
    # Test 11: successful prediction
    # ------------------------------------------------------------------------

    assert (
        is_prediction_successful(
            result
        )
        is True
    )

    # ------------------------------------------------------------------------
    # Test 12: immutability
    # ------------------------------------------------------------------------

    immutable_failed = False

    try:

        result.model_version = "changed"

    except (
        dataclasses.FrozenInstanceError,
    ):

        immutable_failed = True

    assert immutable_failed is True

    # ------------------------------------------------------------------------
    # Test 13: invalid confidence
    # ------------------------------------------------------------------------

    invalid_probability_failed = False

    try:

        PredictionCandidate(
            value="block",
            probability=1.5,
            rank=1,
        )

    except ValueError:

        invalid_probability_failed = True

    assert invalid_probability_failed is True

    # ------------------------------------------------------------------------
    # Test 14: invalid horizon
    # ------------------------------------------------------------------------

    invalid_horizon_failed = False

    try:

        PredictionTarget(
            target_type="risk_change",
            horizon_seconds=0,
        )

    except ValueError:

        invalid_horizon_failed = True

    assert invalid_horizon_failed is True

    # ------------------------------------------------------------------------
    # Test 15: naive datetime rejection
    # ------------------------------------------------------------------------

    naive_datetime_failed = False

    try:

        PredictionRequest(
            target=target,
            reference_time=datetime.now(),
        )

    except ValueError:

        naive_datetime_failed = True

    assert naive_datetime_failed is True

    # ------------------------------------------------------------------------
    # Test 16: empty candidates rejection
    # ------------------------------------------------------------------------

    empty_candidates_failed = False

    try:

        PredictionResult(
            request=request,
            candidates=(),
        )

    except ValueError:

        empty_candidates_failed = True

    assert empty_candidates_failed is True

    # ------------------------------------------------------------------------
    # Test 17: frozen mapping
    # ------------------------------------------------------------------------

    assert isinstance(
        result.metadata,
        tuple,
    )

    assert isinstance(
        candidate.metadata,
        tuple,
    )

    # ------------------------------------------------------------------------
    # Test 18: timezone normalization
    # ------------------------------------------------------------------------

    assert (
        result.generated_at.tzinfo
        is not None
    )

    assert (
        request.reference_time.tzinfo
        is not None
    )

    # ------------------------------------------------------------------------
    # Test 19: independent domain layer
    # ------------------------------------------------------------------------

    module_name = __name__

    assert (
        "dashboard"
        not in module_name.lower()
    )

    # ------------------------------------------------------------------------
    # Test 20: dataclass contract
    # ------------------------------------------------------------------------

    assert dataclasses.is_dataclass(
        PredictionTarget
    )

    assert dataclasses.is_dataclass(
        PredictionEvidence
    )

    assert dataclasses.is_dataclass(
        PredictionCandidate
    )

    assert dataclasses.is_dataclass(
        PredictionRequest
    )

    assert dataclasses.is_dataclass(
        PredictionResult
    )

    return True


# ============================================================================
# Module execution
# ============================================================================


if __name__ == "__main__":

    print("=" * 70)

    print(
        "EnterpriseGuard - ADIE Prediction Contracts Self-Test"
    )

    print("=" * 70)

    try:

        self_test()

        print(
            "[PASS] Prediction status contract"
        )

        print(
            "[PASS] Prediction target"
        )

        print(
            "[PASS] Prediction evidence"
        )

        print(
            "[PASS] Prediction candidate"
        )

        print(
            "[PASS] Prediction request"
        )

        print(
            "[PASS] Prediction result"
        )

        print(
            "[PASS] Probability validation"
        )

        print(
            "[PASS] Temporal validation"
        )

        print(
            "[PASS] Serialization contract"
        )

        print(
            "[PASS] Immutability"
        )

        print(
            "[PASS] Error validation"
        )

        print(
            "[PASS] Domain-layer isolation"
        )

        print("=" * 70)

        print(
            "SELF-TEST PASSED"
        )

        print("=" * 70)

    except AssertionError as exc:

        print(
            "[FAIL] Assertion error:"
        )

        print(
            exc
        )

        raise SystemExit(1)

    except Exception as exc:

        print(
            "[FAIL] Unexpected error:"
        )

        print(
            exc
        )

        raise SystemExit(1)