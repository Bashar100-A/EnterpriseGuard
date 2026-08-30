"""
EnterpriseGuard / ADIE
Adaptive Defense Intelligence Engine
====================================

Prediction Foundation
----------------------

This module defines the prediction contract used by ADIE.

Responsibilities
----------------
- Represent predictions about future security states or actions.
- Preserve probability and confidence separately.
- Represent prediction horizons.
- Provide deterministic validation and serialization.
- Keep prediction independent from policy, playbooks, remediation,
  rollback, and execution.

Architectural rule
------------------
Prediction is an intelligence output.

It does NOT:
- authorize an action,
- create a response plan,
- execute an action,
- modify enterprise state,
- perform remediation,
- perform rollback.

Architecture
------------

    State
      |
      v
    Predictor
      |
      v
    PredictionResult
      |
      v
    Policy
      |
      v
    Playbook
      |
      v
    Response / Execution

Design goals
------------
- Explicit contracts
- Immutable prediction results
- Deep immutability
- Strict validation
- UTC timestamps
- No hidden side effects
- Safe serialization
- Forward-compatible prediction types
- No dependency on ML implementation details
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping, Optional
from uuid import uuid4


# ============================================================================
# Constants
# ============================================================================

MODULE_NAME = "adie.prediction"
MODULE_VERSION = "1.1.0"

MIN_PROBABILITY = 0.0
MAX_PROBABILITY = 1.0

DEFAULT_PROBABILITY_THRESHOLD = 0.70

DEFAULT_PREDICTION_HORIZON_SECONDS = 300

MAX_PREDICTION_HORIZON_SECONDS = 7 * 24 * 60 * 60


# ============================================================================
# Exceptions
# ============================================================================


class PredictionError(Exception):
    """Base exception for ADIE prediction errors."""


class PredictionValidationError(PredictionError):
    """Raised when prediction input or output is invalid."""


class PredictionContractError(PredictionError):
    """Raised when a prediction violates the ADIE prediction contract."""


# ============================================================================
# Enums
# ============================================================================


class PredictionType(str, Enum):
    """Type of future event/state being predicted."""

    STATE = "state"
    ACTION = "action"
    THREAT = "threat"
    ANOMALY = "anomaly"
    TRANSITION = "transition"
    UNKNOWN = "unknown"


class PredictionStatus(str, Enum):
    """Lifecycle status of a prediction."""

    GENERATED = "generated"
    VALIDATED = "validated"
    EXPIRED = "expired"
    INVALID = "invalid"


# ============================================================================
# Internal Helpers
# ============================================================================


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _ensure_probability(
    value: float,
    field_name: str,
) -> float:
    """Validate a normalized probability in the range [0.0, 1.0]."""

    if isinstance(value, bool):
        raise PredictionValidationError(
            f"{field_name} must be a numeric probability."
        )

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise PredictionValidationError(
            f"{field_name} must be numeric."
        ) from exc

    if not isfinite(numeric):
        raise PredictionValidationError(
            f"{field_name} must be finite."
        )

    if not MIN_PROBABILITY <= numeric <= MAX_PROBABILITY:
        raise PredictionValidationError(
            f"{field_name} must be between "
            f"{MIN_PROBABILITY} and {MAX_PROBABILITY}."
        )

    return numeric


def _ensure_non_empty_string(
    value: str,
    field_name: str,
) -> str:
    """Validate a required non-empty string."""

    if not isinstance(value, str):
        raise PredictionValidationError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise PredictionValidationError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _ensure_horizon(value: int) -> int:
    """Validate prediction horizon in seconds."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise PredictionValidationError(
            "horizon_seconds must be an integer."
        )

    if value <= 0:
        raise PredictionValidationError(
            "horizon_seconds must be greater than zero."
        )

    if value > MAX_PREDICTION_HORIZON_SECONDS:
        raise PredictionValidationError(
            "horizon_seconds exceeds the maximum supported horizon."
        )

    return value


def _ensure_utc_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    """
    Validate and normalize a timezone-aware datetime to UTC.

    Naive timestamps are rejected deliberately because ADIE
    prediction timing must be unambiguous.
    """

    if not isinstance(value, datetime):
        raise PredictionValidationError(
            f"{field_name} must be a datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PredictionValidationError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _freeze_value(value: Any) -> Any:
    """
    Recursively freeze common mutable containers.

    Mapping -> MappingProxyType
    list    -> tuple
    tuple   -> tuple
    set     -> frozenset
    scalar  -> unchanged

    This prevents nested metadata mutation after a
    PredictionResult has been created.
    """

    if isinstance(value, Mapping):
        frozen = {
            str(key): _freeze_value(item)
            for key, item in value.items()
        }

        return MappingProxyType(frozen)

    if isinstance(value, list):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, tuple):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, set):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, frozenset):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    return value


def _thaw_value(value: Any) -> Any:
    """
    Convert immutable internal structures into detached
    ordinary Python structures suitable for serialization.
    """

    if isinstance(value, Mapping):
        return {
            key: _thaw_value(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [
            _thaw_value(item)
            for item in value
        ]

    if isinstance(value, (set, frozenset)):
        return [
            _thaw_value(item)
            for item in value
        ]

    return value


def _serialize_datetime(value: datetime) -> str:
    """Serialize a timezone-aware datetime as UTC ISO-8601."""

    normalized = _ensure_utc_datetime(
        value,
        "datetime",
    )

    return normalized.isoformat()


# ============================================================================
# Prediction Result
# ============================================================================


@dataclass(frozen=True)
class PredictionResult:
    """
    Immutable ADIE prediction result.

    This object describes what ADIE believes may happen.

    It does not authorize or execute anything.

    probability:
        Estimated probability of the predicted outcome.

    confidence:
        Confidence in the quality/reliability of the prediction.

    risk_signal:
        Informational probability * confidence signal.
        It is NOT an enterprise risk decision.

    next_action:
        Optional predicted action.
        It is descriptive only and is never executed here.
    """

    prediction_id: str

    prediction_type: PredictionType

    target: str

    predicted_value: Any

    probability: float

    confidence: float

    horizon_seconds: int

    status: PredictionStatus = PredictionStatus.GENERATED

    generated_at: datetime = field(
        default_factory=_utc_now
    )

    source: str = "adie"

    next_action: Optional[str] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Validate and freeze the prediction contract."""

        prediction_id = _ensure_non_empty_string(
            self.prediction_id,
            "prediction_id",
        )

        target = _ensure_non_empty_string(
            self.target,
            "target",
        )

        source = _ensure_non_empty_string(
            self.source,
            "source",
        )

        probability = _ensure_probability(
            self.probability,
            "probability",
        )

        confidence = _ensure_probability(
            self.confidence,
            "confidence",
        )

        horizon_seconds = _ensure_horizon(
            self.horizon_seconds,
        )

        generated_at = _ensure_utc_datetime(
            self.generated_at,
            "generated_at",
        )

        if not isinstance(
            self.prediction_type,
            PredictionType,
        ):
            try:
                prediction_type = PredictionType(
                    self.prediction_type
                )
            except (TypeError, ValueError) as exc:
                raise PredictionValidationError(
                    "prediction_type must be a valid "
                    "PredictionType."
                ) from exc
        else:
            prediction_type = self.prediction_type

        if not isinstance(
            self.status,
            PredictionStatus,
        ):
            try:
                status = PredictionStatus(
                    self.status
                )
            except (TypeError, ValueError) as exc:
                raise PredictionValidationError(
                    "status must be a valid "
                    "PredictionStatus."
                ) from exc
        else:
            status = self.status

        if self.next_action is not None:
            next_action = _ensure_non_empty_string(
                self.next_action,
                "next_action",
            )
        else:
            next_action = None

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise PredictionValidationError(
                "metadata must be a mapping."
            )
        frozen_predicted_value = _freeze_value(
            self.predicted_value
        )    

        frozen_metadata = _freeze_value(
            self.metadata
        )

        object.__setattr__(
            self,
            "prediction_id",
            prediction_id,
        )

        object.__setattr__(
            self,
            "prediction_type",
            prediction_type,
        )

        object.__setattr__(
            self,
            "target",
            target,
        )

        object.__setattr__(
            self,
            "probability",
            probability,
        )

        object.__setattr__(
            self,
            "confidence",
            confidence,
        )

        object.__setattr__(
            self,
            "horizon_seconds",
            horizon_seconds,
        )

        object.__setattr__(
            self,
            "status",
            status,
        )

        object.__setattr__(
            self,
            "generated_at",
            generated_at,
        )

        object.__setattr__(
            self,
            "source",
            source,
        )

        object.__setattr__(
            self,
            "next_action",
            next_action,
        )
        object.__setattr__(
            self,
            "predicted_value",
            frozen_predicted_value,
        )        

        object.__setattr__(
            self,
            "metadata",
            frozen_metadata,
        )

    @property
    def expires_at(self) -> datetime:
        """Return the UTC expiration timestamp."""

        return self.generated_at + timedelta(
            seconds=self.horizon_seconds
        )

    @property
    def is_high_probability(self) -> bool:
        """Return True when probability is at least 0.70."""

        return (
            self.probability
            >= DEFAULT_PROBABILITY_THRESHOLD
        )

    @property
    def is_high_confidence(self) -> bool:
        """Return True when confidence is at least 0.70."""

        return (
            self.confidence
            >= DEFAULT_PROBABILITY_THRESHOLD
        )

    @property
    def risk_signal(self) -> float:
        """
        Return a combined informational prediction signal.

        This is NOT a risk decision.
        """

        return round(
            self.probability * self.confidence,
            6,
        )

    def is_expired(
        self,
        now: Optional[datetime] = None,
    ) -> bool:
        """Return whether the prediction horizon has elapsed."""

        current_time = (
            _utc_now()
            if now is None
            else _ensure_utc_datetime(
                now,
                "now",
            )
        )

        return current_time >= self.expires_at

    # ============================================================================
# Backward Compatibility
# ============================================================================

    # ============================================================================
    # Serialization
    # ============================================================================


    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the prediction into a detached dictionary.


        The returned structure is intentionally independent from
        the immutable internal representation.
        """


        return {
            "prediction_id": self.prediction_id,
            "prediction_type": self.prediction_type.value,
            "target": self.target,
            "predicted_value": _thaw_value(
                self.predicted_value
            ),
            "probability": self.probability,
            "confidence": self.confidence,
            "risk_signal": self.risk_signal,
            "horizon_seconds": self.horizon_seconds,
            "status": self.status.value,
            "generated_at": _serialize_datetime(
                self.generated_at
            ),
            "expires_at": _serialize_datetime(
                self.expires_at
            ),
            "source": self.source,
            "next_action": self.next_action,
            "metadata": _thaw_value(
                self.metadata
            ),
        }


    def to_json_dict(self) -> dict[str, Any]:
        """Return the serialized prediction dictionary."""


        return self.to_dict()


# ============================================================================
# Prediction Builder
# ============================================================================


class PredictionBuilder:
    """Controlled builder for PredictionResult objects."""

    @staticmethod
    def create(
        *,
        prediction_type: PredictionType,
        target: str,
        predicted_value: Any,
        probability: float,
        confidence: float,
        horizon_seconds: int = (
            DEFAULT_PREDICTION_HORIZON_SECONDS
        ),
        source: str = "adie",
        next_action: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        prediction_id: Optional[str] = None,
        generated_at: Optional[datetime] = None,
    ) -> PredictionResult:
        """Create and validate a prediction result."""

        return PredictionResult(
            prediction_id=(
                prediction_id
                if prediction_id is not None
                else f"pred-{uuid4().hex}"
            ),
            prediction_type=prediction_type,
            target=target,
            predicted_value=predicted_value,
            probability=probability,
            confidence=confidence,
            horizon_seconds=horizon_seconds,
            status=PredictionStatus.GENERATED,
            generated_at=(
                generated_at
                if generated_at is not None
                else _utc_now()
            ),
            source=source,
            next_action=next_action,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )


# ============================================================================
# Predictor Contract
# ============================================================================


class Predictor:
    """
    Minimal predictor contract for ADIE.

    Concrete ML/statistical predictors can be added later.

    This base implementation deliberately refuses to fabricate
    predictions.
    """

    name = "base_predictor"
    version = "1.0.0"

    def predict(
        self,
        state: Mapping[str, Any],
    ) -> PredictionResult:
        """Produce a prediction from enterprise state."""

        if not isinstance(state, Mapping):
            raise PredictionValidationError(
                "state must be a mapping."
            )

        raise PredictionContractError(
            "Base Predictor does not implement "
            "prediction logic."
        )

    def status(self) -> dict[str, Any]:
        """Return predictor status."""

        return {
            "name": self.name,
            "version": self.version,
            "ready": False,
            "module": MODULE_NAME,
        }


# ============================================================================
# Deterministic Baseline Predictor
# ============================================================================


class BaselinePredictor(Predictor):
    """
    Safe deterministic predictor used by the Foundation.

    This is NOT an ML model.

    If state contains:
        threat_probability

    that value is used as the predicted threat probability.

    Otherwise:
        probability = 0.0

    Confidence remains deliberately low because this predictor
    contains no learned model.
    """

    name = "baseline_predictor"
    version = "1.0.0"

    def predict(
        self,
        state: Mapping[str, Any],
    ) -> PredictionResult:
        """Produce a deterministic baseline threat prediction."""

        if not isinstance(state, Mapping):
            raise PredictionValidationError(
                "state must be a mapping."
            )

        raw_probability = state.get(
            "threat_probability",
            0.0,
        )

        probability = _ensure_probability(
            raw_probability,
            "threat_probability",
        )

        predicted_value = (
            "threat"
            if probability >= 0.50
            else "benign"
        )

        return PredictionBuilder.create(
            prediction_type=PredictionType.THREAT,
            target="enterprise_security_state",
            predicted_value=predicted_value,
            probability=probability,
            confidence=0.25,
            horizon_seconds=(
                DEFAULT_PREDICTION_HORIZON_SECONDS
            ),
            source=self.name,
            metadata={
                "prediction_mode": (
                    "deterministic_baseline"
                ),
                "ml_prediction": False,
            },
        )

    def status(self) -> dict[str, Any]:
        """Return baseline predictor status."""

        return {
            "name": self.name,
            "version": self.version,
            "ready": True,
            "ml_enabled": False,
            "module": MODULE_NAME,
        }


# ============================================================================
# Prediction Service
# ============================================================================


class PredictionService:
    """
    Public ADIE prediction service.

    Responsibilities:
    - accept state,
    - delegate prediction,
    - validate result,
    - expose status,
    - never execute actions.
    """

    def __init__(
        self,
        predictor: Optional[Predictor] = None,
    ) -> None:

        self._predictor = (
            predictor
            if predictor is not None
            else BaselinePredictor()
        )

        if not callable(
            getattr(
                self._predictor,
                "predict",
                None,
            )
        ):
            raise PredictionContractError(
                "predictor must provide a callable predict()."
            )

        self._prediction_count = 0
        self._successful_predictions = 0
        self._failed_predictions = 0

        self._last_prediction: Optional[
            PredictionResult
        ] = None

    def predict(
        self,
        state: Mapping[str, Any],
    ) -> PredictionResult:
        """Generate one validated prediction."""

        self._prediction_count += 1

        try:
            result = self._predictor.predict(
                state
            )

            if not isinstance(
                result,
                PredictionResult,
            ):
                raise PredictionContractError(
                    "Predictor must return "
                    "PredictionResult."
                )

            self._validate_result(result)

            self._successful_predictions += 1
            self._last_prediction = result

            return result

        except PredictionError:
            self._failed_predictions += 1
            raise

        except Exception as exc:
            self._failed_predictions += 1

            raise PredictionError(
                "Prediction failed unexpectedly."
            ) from exc

    def _validate_result(
        self,
        result: PredictionResult,
    ) -> None:
        """Validate prediction invariants."""

        if not (
            0.0
            <= result.probability
            <= 1.0
        ):
            raise PredictionContractError(
                "Prediction probability is outside [0, 1]."
            )

        if not (
            0.0
            <= result.confidence
            <= 1.0
        ):
            raise PredictionContractError(
                "Prediction confidence is outside [0, 1]."
            )

        if result.horizon_seconds <= 0:
            raise PredictionContractError(
                "Prediction horizon must be positive."
            )

        if not result.target.strip():
            raise PredictionContractError(
                "Prediction target cannot be empty."
            )

        if (
            result.generated_at.tzinfo is None
            or result.generated_at.utcoffset() is None
        ):
            raise PredictionContractError(
                "Prediction timestamp must be timezone-aware."
            )

    def get_last_prediction(
        self,
    ) -> Optional[PredictionResult]:
        """Return the latest prediction."""

        return self._last_prediction

    def status(self) -> dict[str, Any]:
        """Return prediction service status."""

        return {
            "module": MODULE_NAME,
            "version": MODULE_VERSION,
            "predictor": self._predictor.status(),
            "prediction_count": (
                self._prediction_count
            ),
            "successful_predictions": (
                self._successful_predictions
            ),
            "failed_predictions": (
                self._failed_predictions
            ),
            "last_prediction_id": (
                self._last_prediction.prediction_id
                if self._last_prediction is not None
                else None
            ),
            "executes_security_actions": False,
        }

    def health_check(self) -> dict[str, Any]:
        """Return a lightweight health check."""

        status = self.status()

        return {
            "healthy": (
                status["failed_predictions"] == 0
                or status["successful_predictions"] > 0
            ),
            "module": MODULE_NAME,
            "predictor_ready": status[
                "predictor"
            ].get("ready", False),
            "executes_security_actions": False,
        }

    def self_test(self) -> dict[str, Any]:
        """Run deterministic internal service tests."""

        test_state = {
            "threat_probability": 0.80,
        }

        result = self.predict(
            test_state
        )

        passed = (
            isinstance(
                result,
                PredictionResult,
            )
            and result.prediction_type
            == PredictionType.THREAT
            and result.predicted_value
            == "threat"
            and result.probability == 0.80
            and result.confidence == 0.25
            and result.next_action is None
            and result.generated_at.tzinfo
            is not None
        )

        return {
            "passed": passed,
            "module": MODULE_NAME,
            "prediction": result.to_dict(),
            "executes_security_actions": False,
        }


# ============================================================================
# Default Service
# ============================================================================


_default_prediction_service: Optional[
    PredictionService
] = None


def get_prediction_service() -> PredictionService:
    """Return the process-local default PredictionService."""

    global _default_prediction_service

    if _default_prediction_service is None:
        _default_prediction_service = (
            PredictionService()
        )

    return _default_prediction_service


# ============================================================================
# Module Self-Test
# ============================================================================


def self_test() -> dict[str, Any]:
    """
    Run module-level validation.

    This test performs no external security action.
    """

    service = PredictionService()

    service_result = service.self_test()

    # ------------------------------------------------------------------
    # Immutability: top-level
    # ------------------------------------------------------------------

    immutable = False

    prediction = service.get_last_prediction()

    try:
        if prediction is not None:
            prediction.probability = 0.10  # type: ignore[misc]

    except (AttributeError, TypeError):
        immutable = True

    # ------------------------------------------------------------------
    # Deep immutability
    # ------------------------------------------------------------------

    original_metadata = {
        "environment": {
            "region": "test",
            "tags": ["a", "b"],
        }
    }

    prediction_with_metadata = PredictionBuilder.create(
        prediction_type=PredictionType.THREAT,
        target="enterprise_security_state",
        predicted_value={
            "classification": "threat"
        },
        probability=0.80,
        confidence=0.25,
        metadata=original_metadata,
    )

    # Mutate the original caller-owned object.
    original_metadata["environment"]["tags"].append(
        "CALLER_MUTATION"
    )

    deep_immutable = (
        "CALLER_MUTATION"
        not in prediction_with_metadata.metadata[
            "environment"
        ]["tags"]
    )

    # Try to mutate nested internal data.
    nested_mutation_blocked = False

    try:
        prediction_with_metadata.metadata[
            "environment"
        ]["region"] = "MUTATION"

    except (TypeError, AttributeError):
        nested_mutation_blocked = True

    # ------------------------------------------------------------------
    # Serialization isolation
    # ------------------------------------------------------------------

    exported = prediction_with_metadata.to_dict()

    exported["metadata"]["environment"]["tags"].append(
        "EXTERNAL_MUTATION"
    )

    serialization_isolated = (
        "EXTERNAL_MUTATION"
        not in prediction_with_metadata.metadata[
            "environment"
        ]["tags"]
    )

    # ------------------------------------------------------------------
    # Invalid probability
    # ------------------------------------------------------------------

    invalid_probability_rejected = False

    try:
        PredictionBuilder.create(
            prediction_type=PredictionType.THREAT,
            target="test",
            predicted_value="threat",
            probability=1.5,
            confidence=0.5,
        )

    except PredictionValidationError:
        invalid_probability_rejected = True

    # ------------------------------------------------------------------
    # Invalid status
    # ------------------------------------------------------------------

    invalid_status_rejected = False

    try:
        PredictionResult(
            prediction_id="pred-test",
            prediction_type=PredictionType.THREAT,
            target="test",
            predicted_value="threat",
            probability=0.5,
            confidence=0.5,
            horizon_seconds=300,
            status="invalid-status",
        )

    except PredictionValidationError:
        invalid_status_rejected = True

    # ------------------------------------------------------------------
    # Naive datetime rejected
    # ------------------------------------------------------------------

    naive_timestamp_rejected = False

    try:
        PredictionResult(
            prediction_id="pred-test-naive",
            prediction_type=PredictionType.THREAT,
            target="test",
            predicted_value="threat",
            probability=0.5,
            confidence=0.5,
            horizon_seconds=300,
            generated_at=datetime.now(),
        )

    except PredictionValidationError:
        naive_timestamp_rejected = True

    # ------------------------------------------------------------------
    # Invalid horizon
    # ------------------------------------------------------------------

    invalid_horizon_rejected = False

    try:
        PredictionBuilder.create(
            prediction_type=PredictionType.THREAT,
            target="test",
            predicted_value="threat",
            probability=0.5,
            confidence=0.5,
            horizon_seconds=0,
        )

    except PredictionValidationError:
        invalid_horizon_rejected = True

    # ------------------------------------------------------------------
    # Expiration
    # ------------------------------------------------------------------

    expiration_test = PredictionBuilder.create(
        prediction_type=PredictionType.THREAT,
        target="expiration_test",
        predicted_value="threat",
        probability=0.5,
        confidence=0.5,
        horizon_seconds=1,
    )

    expiration_logic_valid = (
        expiration_test.expires_at
        > expiration_test.generated_at
        and not expiration_test.is_expired(
            expiration_test.generated_at
        )
        and expiration_test.is_expired(
            expiration_test.expires_at
        )
    )

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    passed = all(
        (
            service_result["passed"],
            immutable,
            deep_immutable,
            nested_mutation_blocked,
            serialization_isolated,
            invalid_probability_rejected,
            invalid_status_rejected,
            naive_timestamp_rejected,
            invalid_horizon_rejected,
            expiration_logic_valid,
        )
    )

    return {
        "passed": passed,
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "prediction_test_passed": (
            service_result["passed"]
        ),
        "immutable_result": immutable,
        "deep_immutability": deep_immutable,
        "nested_mutation_blocked": (
            nested_mutation_blocked
        ),
        "serialization_isolated": (
            serialization_isolated
        ),
        "invalid_probability_rejected": (
            invalid_probability_rejected
        ),
        "invalid_status_rejected": (
            invalid_status_rejected
        ),
        "naive_timestamp_rejected": (
            naive_timestamp_rejected
        ),
        "invalid_horizon_rejected": (
            invalid_horizon_rejected
        ),
        "expiration_logic_valid": (
            expiration_logic_valid
        ),
        "executes_security_actions": False,
    }


# ============================================================================
# Public API
# ============================================================================


__all__ = [
    "MODULE_NAME",
    "MODULE_VERSION",
    "DEFAULT_PROBABILITY_THRESHOLD",
    "DEFAULT_PREDICTION_HORIZON_SECONDS",
    "MAX_PREDICTION_HORIZON_SECONDS",
    "PredictionError",
    "PredictionValidationError",
    "PredictionContractError",
    "PredictionType",
    "PredictionStatus",
    "PredictionResult",
    "PredictionBuilder",
    "Predictor",
    "BaselinePredictor",
    "PredictionService",
    "get_prediction_service",
    "self_test",
]


# ============================================================================
# Direct Execution
# ============================================================================


if __name__ == "__main__":
    import json

    output = self_test()

    print(
        json.dumps(
            output,
            indent=2,
            default=str,
        )
    )

    if not output["passed"]:
        raise SystemExit(1)