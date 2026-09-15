"""
EnterpriseGuard ADIE Policy Foundation
======================================

Adaptive Defense Intelligence Engine (ADIE)

Purpose
-------
Provides the policy-decision layer between prediction and downstream
decision/planning components.

Architecture
------------

    State
      |
      v
    Prediction
      |
      v
    Policy
      |
      v
    Decision
      |
      +----> Checkpoint
      |
      +----> Playbook
      |
      +----> Rollback
      |
      v
    Orchestration / Integration

Design principles
-----------------
- Policy evaluates security context.
- Policy does not execute security actions.
- Decisions are immutable.
- Decisions are explainable.
- Thresholds are explicit and validated.
- Unknown or insufficient evidence fails safely.
- The output contract remains valid for downstream components.
- No destructive action is performed here.
- The module remains independent from response executors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional
import math


# ============================================================================
# Module metadata
# ============================================================================

MODULE_NAME = "adie.policy"
MODULE_VERSION = "1.0.0"

DEFAULT_MONITOR_THRESHOLD = 0.30
DEFAULT_ALERT_THRESHOLD = 0.70
DEFAULT_CONTAIN_THRESHOLD = 0.90

MIN_PROBABILITY = 0.0
MAX_PROBABILITY = 1.0


# ============================================================================
# Exceptions
# ============================================================================


class PolicyError(Exception):
    """Base exception for ADIE policy errors."""


class PolicyValidationError(PolicyError):
    """Raised when policy configuration or input is invalid."""


class PolicyDecisionError(PolicyError):
    """Raised when a policy decision cannot be produced safely."""


# ============================================================================
# Enums
# ============================================================================


class PolicyLevel(str, Enum):
    """
    Policy severity level.

    The level represents what the policy recommends,
    not what the system executes.
    """

    NONE = "none"
    MONITOR = "monitor"
    ALERT = "alert"
    CONTAIN = "contain"
    ISOLATE = "isolate"


class DecisionConfidence(str, Enum):
    """Qualitative confidence classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# Immutable policy decision
# ============================================================================


@dataclass(frozen=True)
class PolicyDecision:
    """
    Immutable policy decision.

    This object describes the recommended security posture.

    It does NOT execute an action.
    """

    level: PolicyLevel
    confidence: DecisionConfidence

    risk_score: float
    threat_probability: float

    reason: str

    recommended_action: Optional[str] = None

    requires_approval: bool = False
    fail_safe: bool = False

    policy_version: str = MODULE_VERSION

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate immutable decision data."""

        if not isinstance(self.level, PolicyLevel):
            raise PolicyValidationError(
                "level must be a PolicyLevel."
            )

        if not isinstance(self.confidence, DecisionConfidence):
            raise PolicyValidationError(
                "confidence must be a DecisionConfidence."
            )

        _validate_probability(
            self.risk_score,
            "risk_score",
        )

        _validate_probability(
            self.threat_probability,
            "threat_probability",
        )

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise PolicyValidationError(
                "reason must be a non-empty string."
            )

        if self.recommended_action is not None:
            if not isinstance(self.recommended_action, str):
                raise PolicyValidationError(
                    "recommended_action must be a string or None."
                )

        if not isinstance(self.requires_approval, bool):
            raise PolicyValidationError(
                "requires_approval must be boolean."
            )

        if not isinstance(self.fail_safe, bool):
            raise PolicyValidationError(
                "fail_safe must be boolean."
            )

        if not isinstance(self.policy_version, str):
            raise PolicyValidationError(
                "policy_version must be a string."
            )

        if not isinstance(self.metadata, Mapping):
            raise PolicyValidationError(
                "metadata must be mapping-like."
            )

    @property
    def executes_security_actions(self) -> bool:
        """
        Policy layer never executes security actions.
        """

        return False

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the decision."""

        return {
            "level": self.level.value,
            "confidence": self.confidence.value,
            "risk_score": self.risk_score,
            "threat_probability": self.threat_probability,
            "reason": self.reason,
            "recommended_action": self.recommended_action,
            "requires_approval": self.requires_approval,
            "fail_safe": self.fail_safe,
            "policy_version": self.policy_version,
            "metadata": dict(self.metadata),
            "executes_security_actions": False,
        }


# ============================================================================
# Policy configuration
# ============================================================================


@dataclass(frozen=True)
class PolicyConfig:
    """
    Immutable ADIE policy configuration.

    Thresholds are ordered:

        monitor <= alert <= contain
    """

    monitor_threshold: float = DEFAULT_MONITOR_THRESHOLD
    alert_threshold: float = DEFAULT_ALERT_THRESHOLD
    contain_threshold: float = DEFAULT_CONTAIN_THRESHOLD

    approval_required_for_isolation: bool = True

    allow_destructive_actions: bool = False

    version: str = MODULE_VERSION

    def __post_init__(self) -> None:
        """Validate policy thresholds and safety settings."""

        _validate_probability(
            self.monitor_threshold,
            "monitor_threshold",
        )

        _validate_probability(
            self.alert_threshold,
            "alert_threshold",
        )

        _validate_probability(
            self.contain_threshold,
            "contain_threshold",
        )

        if self.monitor_threshold > self.alert_threshold:
            raise PolicyValidationError(
                "monitor_threshold must be less than or equal "
                "to alert_threshold."
            )

        if self.alert_threshold > self.contain_threshold:
            raise PolicyValidationError(
                "alert_threshold must be less than or equal "
                "to contain_threshold."
            )

        if not isinstance(
            self.approval_required_for_isolation,
            bool,
        ):
            raise PolicyValidationError(
                "approval_required_for_isolation must be boolean."
            )

        if self.allow_destructive_actions:
            raise PolicyValidationError(
                "Policy layer cannot enable destructive actions."
            )

        if not isinstance(self.version, str) or not self.version:
            raise PolicyValidationError(
                "version must be a non-empty string."
            )


# ============================================================================
# Policy engine
# ============================================================================


class ADIEPolicy:
    """
    ADIE policy decision engine.

    Responsibilities
    ----------------
    - Validate prediction input.
    - Extract normalized threat probability.
    - Evaluate risk.
    - Classify policy level.
    - Determine confidence.
    - Produce an immutable PolicyDecision.
    - Preserve a valid downstream contract.

    Non-responsibilities
    --------------------
    - No command execution.
    - No endpoint isolation.
    - No process termination.
    - No firewall modification.
    - No remediation.
    - No direct interaction with response executors.
    """

    def __init__(
        self,
        config: Optional[PolicyConfig] = None,
    ) -> None:
        """Initialize the policy engine."""

        self._config = config or PolicyConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        prediction: Mapping[str, Any],
        state: Optional[Mapping[str, Any]] = None,
    ) -> PolicyDecision:
        """
        Evaluate a prediction and produce a policy decision.

        Supported prediction probability fields:

            1. threat_probability
            2. probability
            3. risk_score

        ``threat_probability`` has the highest priority.

        Missing or invalid probability data results in a fail-safe
        MONITOR decision with a valid numeric downstream contract.
        """

        if not isinstance(prediction, Mapping):
            raise PolicyDecisionError(
                "prediction must be mapping-like."
            )

        if state is not None and not isinstance(state, Mapping):
            raise PolicyDecisionError(
                "state must be mapping-like or None."
            )

        threat_probability = _extract_threat_probability(
            prediction
        )

        risk_score = _extract_probability(
            prediction,
            "risk_score",
        )

        # If an explicit risk score is unavailable, use the normalized
        # threat probability as the risk score.
        if risk_score is None:
            risk_score = threat_probability

        # If prediction evidence is unavailable, preserve the fail-safe
        # semantic while returning a contract-valid numeric probability.
        if threat_probability is None and risk_score is None:
            return self._fail_safe_decision(
                reason=(
                    "Insufficient prediction evidence; "
                    "policy defaults to monitoring."
                ),
                state=state,
            )

        # At this point at least one valid numeric signal exists.
        #
        # If threat_probability is absent but risk_score exists, use the
        # risk score as the normalized threat probability. This keeps the
        # PolicyDecision contract complete for downstream DecisionEngine.
        if threat_probability is None:
            threat_probability = risk_score

        if risk_score is None:
            risk_score = threat_probability

        confidence = self._classify_confidence(
            prediction,
            threat_probability,
        )

        level = self._determine_level(
            risk_score=risk_score,
            threat_probability=threat_probability,
        )

        reason = self._build_reason(
            level=level,
            risk_score=risk_score,
            threat_probability=threat_probability,
            prediction=prediction,
        )

        recommended_action = self._recommended_action(level)

        requires_approval = (
            level == PolicyLevel.ISOLATE
            and self._config.approval_required_for_isolation
        )

        return PolicyDecision(
            level=level,
            confidence=confidence,
            risk_score=round(risk_score, 6),
            threat_probability=round(
                threat_probability,
                6,
            ),
            reason=reason,
            recommended_action=recommended_action,
            requires_approval=requires_approval,
            fail_safe=False,
            policy_version=self._config.version,
            metadata={
                "state_available": state is not None,
                "destructive_actions_allowed": False,
            },
        )

    def evaluate_risk(
        self,
        risk_score: float,
    ) -> PolicyDecision:
        """
        Evaluate a standalone normalized risk score.
        """

        _validate_probability(
            risk_score,
            "risk_score",
        )

        return self.evaluate(
            {
                "risk_score": risk_score,
                "threat_probability": risk_score,
            }
        )

    def get_config(self) -> PolicyConfig:
        """Return the immutable policy configuration."""

        return self._config

    def get_status(self) -> dict[str, Any]:
        """Return policy engine status."""

        return {
            "module": MODULE_NAME,
            "version": self._config.version,
            "healthy": True,
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
            "thresholds": {
                "monitor": self._config.monitor_threshold,
                "alert": self._config.alert_threshold,
                "contain": self._config.contain_threshold,
            },
        }

    def health_check(self) -> bool:
        """Return whether the policy engine is healthy."""

        return True

    # ------------------------------------------------------------------
    # Decision logic
    # ------------------------------------------------------------------

    def _determine_level(
        self,
        *,
        risk_score: float,
        threat_probability: float,
    ) -> PolicyLevel:
        """
        Determine policy level from normalized risk.

        A very high threat probability may elevate the decision to
        ISOLATE, but the policy only recommends that level.
        """

        probability = max(
            risk_score,
            threat_probability,
        )

        if probability < self._config.monitor_threshold:
            return PolicyLevel.NONE

        if probability < self._config.alert_threshold:
            return PolicyLevel.MONITOR

        if probability < self._config.contain_threshold:
            return PolicyLevel.ALERT

        return PolicyLevel.ISOLATE

    def _classify_confidence(
        self,
        prediction: Mapping[str, Any],
        threat_probability: Optional[float],
    ) -> DecisionConfidence:
        """
        Classify confidence conservatively.

        Explicit confidence takes precedence when valid.
        Otherwise probability distance from 0.5 is used as fallback.
        """

        explicit = prediction.get("confidence")

        if explicit is not None:
            try:
                value = float(explicit)
            except (TypeError, ValueError):
                value = None

            if value is not None and math.isfinite(value):
                value = max(
                    MIN_PROBABILITY,
                    min(MAX_PROBABILITY, value),
                )

                if value >= 0.85:
                    return DecisionConfidence.HIGH

                if value >= 0.60:
                    return DecisionConfidence.MEDIUM

                return DecisionConfidence.LOW

        if threat_probability is None:
            return DecisionConfidence.LOW

        distance = abs(
            threat_probability - 0.5
        )

        if distance >= 0.35:
            return DecisionConfidence.HIGH

        if distance >= 0.15:
            return DecisionConfidence.MEDIUM

        return DecisionConfidence.LOW

    def _recommended_action(
        self,
        level: PolicyLevel,
    ) -> Optional[str]:
        """
        Map policy level to a non-executing recommendation.
        """

        recommendations = {
            PolicyLevel.NONE: None,
            PolicyLevel.MONITOR: "monitor",
            PolicyLevel.ALERT: "alert",
            PolicyLevel.CONTAIN: "contain",
            PolicyLevel.ISOLATE: "isolate",
        }

        return recommendations[level]

    def _build_reason(
        self,
        *,
        level: PolicyLevel,
        risk_score: float,
        threat_probability: float,
        prediction: Mapping[str, Any],
    ) -> str:
        """Build an explainable policy reason."""

        predicted_class = prediction.get(
            "predicted_class",
            prediction.get(
                "predicted_value",
                "unknown",
            ),
        )

        return (
            f"Policy level={level.value}; "
            f"risk_score={risk_score:.3f}; "
            f"threat_probability={threat_probability:.3f}; "
            f"predicted_class={predicted_class}."
        )

    def _fail_safe_decision(
        self,
        *,
        reason: str,
        state: Optional[Mapping[str, Any]],
    ) -> PolicyDecision:
        """
        Produce the safest decision when evidence is insufficient.

        Important:
        The fail-safe result remains explicitly marked as fail-safe,
        while its probability fields remain numeric so downstream
        components receive a valid contract.
        """

        return PolicyDecision(
            level=PolicyLevel.MONITOR,
            confidence=DecisionConfidence.LOW,
            risk_score=0.0,
            threat_probability=0.0,
            reason=reason,
            recommended_action="monitor",
            requires_approval=False,
            fail_safe=True,
            policy_version=self._config.version,
            metadata={
                "state_available": state is not None,
                "failure_mode": "insufficient_evidence",
                "destructive_actions_allowed": False,
            },
        )


# ============================================================================
# Probability utilities
# ============================================================================


def _validate_probability(
    value: Any,
    field_name: str,
) -> None:
    """Validate a normalized probability."""

    if isinstance(value, bool):
        raise PolicyValidationError(
            f"{field_name} must be numeric, not boolean."
        )

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise PolicyValidationError(
            f"{field_name} must be numeric."
        ) from exc

    if not math.isfinite(numeric):
        raise PolicyValidationError(
            f"{field_name} must be finite."
        )

    if not (
        MIN_PROBABILITY
        <= numeric
        <= MAX_PROBABILITY
    ):
        raise PolicyValidationError(
            f"{field_name} must be between 0 and 1."
        )


def _extract_probability(
    mapping: Mapping[str, Any],
    key: str,
) -> Optional[float]:
    """
    Extract an optional normalized probability.

    Invalid values are treated as unavailable rather than being
    converted into unsafe decisions.
    """

    value = mapping.get(key)

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(numeric):
        return None

    if not (
        MIN_PROBABILITY
        <= numeric
        <= MAX_PROBABILITY
    ):
        return None

    return numeric


def _extract_threat_probability(
    prediction: Mapping[str, Any],
) -> Optional[float]:
    """
    Extract the canonical threat probability from a prediction.

    Priority:

        threat_probability
            ↓
        probability
            ↓
        risk_score

    The ``probability`` alias is required because the current
    PredictionResult contract emits ``probability``.
    """

    for key in (
        "threat_probability",
        "probability",
        "risk_score",
    ):
        value = _extract_probability(
            prediction,
            key,
        )

        if value is not None:
            return value

    return None


# ============================================================================
# Self-test
# ============================================================================


def self_test() -> dict[str, Any]:
    """
    Run a deterministic policy self-test.

    Verifies:

    - normal policy evaluation
    - prediction probability compatibility
    - alert-level recommendation
    - high-risk recommendation
    - fail-safe behavior
    - downstream contract validity
    - immutable decision
    - configuration safety
    - execution safety
    """

    policy = ADIEPolicy()

    # ------------------------------------------------------------------
    # Test 1: normal benign prediction using canonical threat_probability
    # ------------------------------------------------------------------

    low = policy.evaluate(
        {
            "predicted_class": "benign",
            "threat_probability": 0.10,
            "confidence": 0.90,
        }
    )

    assert low.level == PolicyLevel.NONE
    assert low.threat_probability == 0.10
    assert low.executes_security_actions is False

    # ------------------------------------------------------------------
    # Test 2: PredictionResult compatibility
    # ------------------------------------------------------------------

    prediction_contract = policy.evaluate(
        {
            "predicted_value": "benign",
            "probability": 0.0,
            "confidence": 0.25,
        }
    )

    assert prediction_contract.threat_probability == 0.0
    assert prediction_contract.risk_score == 0.0
    assert prediction_contract.fail_safe is False
    assert prediction_contract.executes_security_actions is False

    # ------------------------------------------------------------------
    # Test 3: alert-level prediction
    # ------------------------------------------------------------------

    alert = policy.evaluate(
        {
            "predicted_class": "threat",
            "threat_probability": 0.75,
            "confidence": 0.90,
        }
    )

    assert alert.level == PolicyLevel.ALERT
    assert alert.recommended_action == "alert"
    assert alert.threat_probability == 0.75

    # ------------------------------------------------------------------
    # Test 4: high-risk prediction
    # ------------------------------------------------------------------

    critical = policy.evaluate(
        {
            "predicted_class": "threat",
            "threat_probability": 0.95,
            "confidence": 0.95,
        }
    )

    assert critical.level == PolicyLevel.ISOLATE
    assert critical.requires_approval is True
    assert critical.executes_security_actions is False

    # ------------------------------------------------------------------
    # Test 5: risk-score fallback
    # ------------------------------------------------------------------

    risk_only = policy.evaluate(
        {
            "risk_score": 0.80,
            "confidence": 0.80,
        }
    )

    assert risk_only.threat_probability == 0.80
    assert risk_only.risk_score == 0.80
    assert risk_only.level == PolicyLevel.ALERT

    # ------------------------------------------------------------------
    # Test 6: insufficient evidence must fail safe
    # ------------------------------------------------------------------

    unknown = policy.evaluate({})

    assert unknown.fail_safe is True
    assert unknown.level == PolicyLevel.MONITOR
    assert unknown.threat_probability == 0.0
    assert unknown.risk_score == 0.0
    assert unknown.executes_security_actions is False

    # ------------------------------------------------------------------
    # Test 7: immutable result
    # ------------------------------------------------------------------

    immutable = False

    try:
        low.level = PolicyLevel.ALERT  # type: ignore[misc]
    except Exception:
        immutable = True

    assert immutable is True

    # ------------------------------------------------------------------
    # Test 8: configuration safety
    # ------------------------------------------------------------------

    assert (
        policy.get_config().allow_destructive_actions
        is False
    )

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    return {
        "passed": True,
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "policy_test_passed": True,
        "immutable_result": True,
        "prediction_probability_compatibility": True,
        "downstream_contract_valid": True,
        "executes_security_actions": False,
        "destructive_actions_allowed": False,
    }


# ============================================================================
# Module entry point
# ============================================================================


if __name__ == "__main__":
    import json

    result = self_test()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )