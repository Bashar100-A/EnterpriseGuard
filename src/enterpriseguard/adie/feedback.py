"""
EnterpriseGuard ADIE - Feedback
================================

Adaptive Defense Intelligence Engine.

Feedback and learning signal layer.

Responsibilities
-----------------
- Record ADIE decision outcomes.
- Compare expected vs actual results.
- Generate learning signals.
- Preserve decision lineage.
- Detect possible performance degradation.
- Provide immutable feedback artifacts.

Important Safety Boundary
-------------------------
This module DOES NOT:

- retrain models,
- modify intelligence models,
- execute security actions,
- change policies,
- alter system state.

It only creates feedback evidence and learning signals.

Architecture
------------

    Decision
        |
        v
    Outcome
        |
        v
    FeedbackEvent
        |
        v
    FeedbackEngine
        |
        +---- evaluation
        +---- learning signal generation
        +---- drift indication
        |
        v
    LearningSignal

Security Principles
-------------------
- Immutable feedback records.
- No model mutation.
- No execution authority.
- Deterministic fingerprints.
- Audit friendly outputs.
- Fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Optional


__all__ = [
    "FEEDBACK_VERSION",
    "FeedbackError",
    "FeedbackValidationError",
    "FeedbackOutcome",
    "FeedbackEvent",
    "LearningSignal",
    "FeedbackEngine",
    "self_test",
]


FEEDBACK_VERSION = "1.0.0"


# ============================================================================
# Exceptions
# ============================================================================


class FeedbackError(Exception):
    """Base feedback exception."""


class FeedbackValidationError(FeedbackError):
    """Raised when feedback data is invalid."""


# ============================================================================
# Enums
# ============================================================================


class FeedbackOutcome(str, Enum):
    """
    Observed result of a defensive decision.
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"


# ============================================================================
# Immutable Contracts
# ============================================================================


@dataclass(frozen=True)
class FeedbackEvent:
    """
    Immutable record describing a completed ADIE decision outcome.

    This is evidence only.
    """

    event_id: str
    decision_id: str
    prediction_id: str
    expected_outcome: str
    actual_outcome: FeedbackOutcome
    confidence: float
    created_at: str = field(
        default_factory=lambda: _utc_now()
    )
    lineage: Mapping[str, str] = field(
        default_factory=dict
    )
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise FeedbackValidationError(
                "event_id is required."
            )

        if not self.decision_id.strip():
            raise FeedbackValidationError(
                "decision_id is required."
            )

        if not self.prediction_id.strip():
            raise FeedbackValidationError(
                "prediction_id is required."
            )

        if not isinstance(
            self.actual_outcome,
            FeedbackOutcome,
        ):
            raise FeedbackValidationError(
                "actual_outcome must be FeedbackOutcome."
            )

        if not (
            0.0 <= self.confidence <= 1.0
        ):
            raise FeedbackValidationError(
                "confidence must be between 0 and 1."
            )

        object.__setattr__(
            self,
            "lineage",
            _freeze_mapping(self.lineage),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


@dataclass(frozen=True)
class LearningSignal:
    """
    Immutable output produced by feedback analysis.
    """

    signal_id: str
    source_event_id: str
    accuracy_delta: float
    drift_detected: bool
    recommendation: str
    created_at: str
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.signal_id.strip():
            raise FeedbackValidationError(
                "signal_id is required."
            )

        if not self.source_event_id.strip():
            raise FeedbackValidationError(
                "source_event_id is required."
            )

        if not self.fingerprint:
            object.__setattr__(
                self,
                "fingerprint",
                _fingerprint_signal(self),
            )


# ============================================================================
# Feedback Engine
# ============================================================================


class FeedbackEngine:
    """
    ADIE feedback analysis engine.

    Safety Boundary:
        This engine generates intelligence signals only.

    It never:
        - modifies models,
        - changes policies,
        - executes actions.
    """

    VERSION = FEEDBACK_VERSION

    executes_security_actions = False
    modifies_models = False

    def __init__(
        self,
        *,
        drift_threshold: float = 0.30,
    ) -> None:

        if not (
            0.0 <= drift_threshold <= 1.0
        ):
            raise FeedbackValidationError(
                "drift_threshold must be between 0 and 1."
            )

        self._drift_threshold = drift_threshold

    def evaluate(
        self,
        event: FeedbackEvent,
    ) -> LearningSignal:
        """
        Evaluate feedback evidence and create learning signal.
        """

        if not isinstance(
            event,
            FeedbackEvent,
        ):
            raise FeedbackValidationError(
                "event must be FeedbackEvent."
            )

        accuracy_delta = self._calculate_delta(
            event
        )

        drift_detected = (
            abs(accuracy_delta)
            >= self._drift_threshold
        )

        recommendation = (
            "review_model_behavior"
            if drift_detected
            else "continue_monitoring"
        )

        signal_id = self._build_signal_id(
            event
        )

        return LearningSignal(
            signal_id=signal_id,
            source_event_id=event.event_id,
            accuracy_delta=accuracy_delta,
            drift_detected=drift_detected,
            recommendation=recommendation,
            created_at=_utc_now(),
        )

    def describe(
        self,
        signal: LearningSignal,
    ) -> Mapping[str, Any]:
        """
        Safe JSON compatible representation.
        """

        if not isinstance(
            signal,
            LearningSignal,
        ):
            raise FeedbackValidationError(
                "signal must be LearningSignal."
            )

        return {
            "signal_id": signal.signal_id,
            "source_event_id": signal.source_event_id,
            "accuracy_delta": signal.accuracy_delta,
            "drift_detected": signal.drift_detected,
            "recommendation": signal.recommendation,
            "fingerprint": signal.fingerprint,
            "executes_security_actions": False,
        }

    def status(self) -> Mapping[str, Any]:
        return {
            "module": "adie.feedback",
            "version": self.VERSION,
            "executes_security_actions": False,
            "modifies_models": False,
            "learning_only": True,
        }

    def _calculate_delta(
        self,
        event: FeedbackEvent,
    ) -> float:

        if (
            event.actual_outcome
            == FeedbackOutcome.SUCCESS
        ):
            return 0.0

        if (
            event.actual_outcome
            == FeedbackOutcome.PARTIAL
        ):
            return -0.25

        if (
            event.actual_outcome
            == FeedbackOutcome.FAILED
        ):
            return -1.0

        return -0.5

    def _build_signal_id(
        self,
        event: FeedbackEvent,
    ) -> str:

        material = (
            f"{event.event_id}:"
            f"{event.decision_id}:"
            f"{event.actual_outcome.value}"
        )

        digest = hashlib.sha256(
            material.encode("utf-8")
        ).hexdigest()

        return f"sig-{digest[:24]}"


# ============================================================================
# Helpers
# ============================================================================


def _utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _freeze_mapping(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:

    if value is None:
        return {}

    if not isinstance(
        value,
        Mapping,
    ):
        raise FeedbackValidationError(
            "Value must be mapping."
        )

    normalized = json.loads(
        json.dumps(
            dict(value),
            sort_keys=True,
            default=str,
        )
    )

    return _ImmutableDict(normalized)


class _ImmutableDict(dict):
    """
    Minimal immutable mapping.
    """

    def _blocked(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        raise TypeError(
            "Immutable mapping."
        )

    __setitem__ = _blocked
    __delitem__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked
    update = _blocked


def _fingerprint_signal(
    signal: LearningSignal,
) -> str:

    material = {
        "signal_id": signal.signal_id,
        "source_event_id": signal.source_event_id,
        "accuracy_delta": signal.accuracy_delta,
        "drift_detected": signal.drift_detected,
        "recommendation": signal.recommendation,
    }

    encoded = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        encoded.encode("utf-8")
    ).hexdigest()


# ============================================================================
# Self Test
# ============================================================================


def self_test() -> Mapping[str, Any]:
    tests = {
        "event_creation": False,
        "signal_generation": False,
        "immutable_output": False,
        "security_boundary": False,
    }

    try:
        engine = FeedbackEngine()

        event = FeedbackEvent(
            event_id="feedback-test-001",
            decision_id="decision-001",
            prediction_id="prediction-001",
            expected_outcome="success",
            actual_outcome=FeedbackOutcome.FAILED,
            confidence=0.90,
            lineage={
                "checkpoint": "cp-001"
            },
        )

        tests["event_creation"] = True

        signal = engine.evaluate(event)

        tests["signal_generation"] = (
            signal.source_event_id
            == event.event_id
        )

        try:
            signal.recommendation = "blocked"
            tests["immutable_output"] = False
        except Exception:
            tests["immutable_output"] = True

        tests["security_boundary"] = (
            engine.executes_security_actions
            is False
            and engine.modifies_models
            is False
        )

        passed = all(
            tests.values()
        )

        return {
            "passed": passed,
            "module": "adie.feedback",
            "version": FEEDBACK_VERSION,
            "tests": tests,
            "executes_security_actions": False,
            "modifies_models": False,
        }

    except Exception as exc:
        return {
            "passed": False,
            "module": "adie.feedback",
            "version": FEEDBACK_VERSION,
            "tests": tests,
            "error": str(exc),
            "executes_security_actions": False,
            "modifies_models": False,
        }


if __name__ == "__main__":
    print(
        json.dumps(
            self_test(),
            indent=2,
            sort_keys=True,
        )
    )