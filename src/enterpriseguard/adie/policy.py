"""
EnterpriseGuard ADIE - Policy Contracts
=======================================

Canonical Production Policy Domain.

Architecture Boundary
---------------------

Prediction Evidence
        |
        v
Policy Evaluation
        |
        v
Decision Evaluation
        |
        v
Decision Contract


Purpose
-------

The Policy domain is the authoritative constraint and authorization
boundary of ADIE.

Policy determines whether a defensive intent is permitted under
configured governance rules.

Prediction provides evidence only.

Prediction MUST NOT:
- authorize actions
- bypass policy
- create decisions directly


Security Boundary
-----------------

This module:

- evaluates policy constraints.
- produces immutable policy contracts.
- provides audit-ready provenance.
- fails safely on invalid evidence.

This module does NOT:

- execute commands.
- modify infrastructure.
- isolate systems.
- disable accounts.
- invoke response systems.
- perform remediation.


Design Principles
-----------------

1. Policy authority over prediction.
2. Immutable domain contracts.
3. Deterministic evaluation.
4. Complete audit provenance.
5. UTC-only timestamps.
6. JSON-safe serialization.
7. Fail-safe behavior.
8. Separation between authorization and execution.
9. Thread-safe execution and evaluation tracking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from math import isfinite
import threading
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence


MODULE_NAME = "adie.policy"
MODULE_VERSION = "2.0.0"


MIN_SCORE = 0.0
MAX_SCORE = 1.0


DEFAULT_MONITOR_THRESHOLD = 0.40
DEFAULT_ALERT_THRESHOLD = 0.70
DEFAULT_CONTAIN_THRESHOLD = 0.85
DEFAULT_ISOLATE_THRESHOLD = 0.95


EXECUTES_SECURITY_ACTIONS = False
DESTRUCTIVE_ACTIONS_ALLOWED = False


# ============================================================================
# Exceptions
# ============================================================================


class PolicyError(Exception):
    """Base ADIE policy exception."""


class PolicyValidationError(PolicyError):
    """Invalid policy contract or evidence."""


class PolicyEvaluationError(PolicyError):
    """Policy evaluation failure."""


# ============================================================================
# Enums
# ============================================================================


class PolicyIntent(str, Enum):
    """
    Policy-authorized defensive intent.

    These values describe permission boundaries only.
    They do not execute actions.
    """

    ALLOW = "allow"
    MONITOR = "monitor"
    ALERT = "alert"
    CONTAIN = "contain"
    ISOLATE = "isolate"
    DENY = "deny"


class PolicyLifecycle(str, Enum):
    """
    Lifecycle state of a policy evaluation.
    """

    GENERATED = "generated"
    APPROVED = "approved"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    INVALID = "invalid"


# ============================================================================
# Utility functions
# ============================================================================


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _validate_utc(value: datetime, field_name: str) -> None:
    """Enforce datetime presence and explicit timezone awareness."""
    if not isinstance(value, datetime):
        raise PolicyValidationError(
            f"{field_name} must be a datetime instance"
        )

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise PolicyValidationError(
            f"{field_name} must be timezone-aware (UTC)"
        )


def _iso(value: datetime) -> str:
    """Format datetime as strict UTC ISO-8601 string."""
    _validate_utc(value, "timestamp")
    return value.astimezone(timezone.utc).isoformat()


def _validate_score(
    value: Any,
    name: str,
) -> float:
    """Validate numeric bounded probability and risk scores [0.0, 1.0]."""
    if isinstance(value, bool):
        raise PolicyValidationError(
            f"{name} cannot be a boolean"
        )

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise PolicyValidationError(
            f"{name} must be numeric"
        ) from exc

    if not isfinite(numeric):
        raise PolicyValidationError(
            f"{name} must be a finite number"
        )

    if not MIN_SCORE <= numeric <= MAX_SCORE:
        raise PolicyValidationError(
            f"{name} must be between {MIN_SCORE} and {MAX_SCORE}"
        )

    return numeric


def _validate_str(value: Any, name: str) -> str:
    """Validate non-empty string identifier."""
    if not isinstance(value, str) or not value.strip():
        raise PolicyValidationError(
            f"{name} must be a non-empty string"
        )
    return value.strip()


def _freeze(value: Any) -> Any:
    """Recursively freeze structures into immutable proxies."""
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)

    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)

    return value


def _unfreeze(value: Any) -> Any:
    """Recursively convert immutable proxies into standard JSON-serializable types."""
    if isinstance(value, (Mapping, MappingProxyType)):
        return {key: _unfreeze(item) for key, item in value.items()}

    if isinstance(value, (tuple, list, frozenset, set)):
        return [_unfreeze(item) for item in value]

    return value


# ============================================================================
# Policy Configuration Contract
# ============================================================================


@dataclass(frozen=True)
class PolicyConfig:
    """
    Immutable policy configuration contract.
    """

    policy_id: str
    policy_version: str

    monitor_threshold: float = DEFAULT_MONITOR_THRESHOLD
    alert_threshold: float = DEFAULT_ALERT_THRESHOLD
    contain_threshold: float = DEFAULT_CONTAIN_THRESHOLD
    isolate_threshold: float = DEFAULT_ISOLATE_THRESHOLD

    destructive_actions_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _validate_str(self.policy_id, "policy_id"),
        )
        object.__setattr__(
            self,
            "policy_version",
            _validate_str(self.policy_version, "policy_version"),
        )

        monitor = _validate_score(
            self.monitor_threshold,
            "monitor_threshold",
        )
        alert = _validate_score(
            self.alert_threshold,
            "alert_threshold",
        )
        contain = _validate_score(
            self.contain_threshold,
            "contain_threshold",
        )
        isolate = _validate_score(
            self.isolate_threshold,
            "isolate_threshold",
        )

        if alert < monitor:
            raise PolicyValidationError(
                "alert threshold cannot be below monitor threshold"
            )

        if contain < alert:
            raise PolicyValidationError(
                "contain threshold cannot be below alert threshold"
            )

        if isolate < contain:
            raise PolicyValidationError(
                "isolate threshold cannot be below contain threshold"
            )

        if self.destructive_actions_allowed:
            raise PolicyValidationError(
                "ADIE policy cannot enable destructive actions"
            )

        object.__setattr__(self, "monitor_threshold", monitor)
        object.__setattr__(self, "alert_threshold", alert)
        object.__setattr__(self, "contain_threshold", contain)
        object.__setattr__(self, "isolate_threshold", isolate)


# ============================================================================
# Policy Evidence Contract
# ============================================================================


@dataclass(frozen=True)
class PolicyEvidence:
    """
    Immutable evidence consumed by the policy domain.

    Evidence is informational.
    It does not represent authorization.
    """

    prediction_id: str
    threat_probability: float
    prediction_confidence: float
    state_risk: float
    state_id: Optional[str]
    collected_at: datetime
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "prediction_id",
            _validate_str(self.prediction_id, "prediction_id"),
        )

        if self.state_id is not None:
            object.__setattr__(
                self,
                "state_id",
                _validate_str(self.state_id, "state_id"),
            )

        _validate_utc(self.collected_at, "collected_at")

        object.__setattr__(
            self,
            "threat_probability",
            _validate_score(
                self.threat_probability,
                "threat_probability",
            ),
        )

        object.__setattr__(
            self,
            "prediction_confidence",
            _validate_score(
                self.prediction_confidence,
                "prediction_confidence",
            ),
        )

        object.__setattr__(
            self,
            "state_risk",
            _validate_score(
                self.state_risk,
                "state_risk",
            ),
        )

        object.__setattr__(
            self,
            "context",
            _freeze(self.context),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert evidence contract to plain dictionary."""
        return {
            "prediction_id": self.prediction_id,
            "threat_probability": self.threat_probability,
            "prediction_confidence": self.prediction_confidence,
            "state_risk": self.state_risk,
            "state_id": self.state_id,
            "collected_at": _iso(self.collected_at),
            "context": _unfreeze(self.context),
        }


# ============================================================================
# Policy Evaluation Contract
# ============================================================================


@dataclass(frozen=True)
class PolicyEvaluation:
    """
    Immutable result of policy evaluation.

    This contract answers:
    "Is this defensive intent permitted under current governance rules?"

    It does NOT execute anything.
    """

    evaluation_id: str
    policy_id: str
    policy_version: str
    intent: PolicyIntent
    lifecycle: PolicyLifecycle
    allowed: bool
    decision_score: float
    prediction_id: str
    evaluated_at: datetime
    constraints: Mapping[str, Any] = field(default_factory=dict)
    violations: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    rationale: str = ""
    executes_security_actions: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evaluation_id",
            _validate_str(self.evaluation_id, "evaluation_id"),
        )
        object.__setattr__(
            self,
            "policy_id",
            _validate_str(self.policy_id, "policy_id"),
        )
        object.__setattr__(
            self,
            "policy_version",
            _validate_str(self.policy_version, "policy_version"),
        )
        object.__setattr__(
            self,
            "prediction_id",
            _validate_str(self.prediction_id, "prediction_id"),
        )

        _validate_utc(self.evaluated_at, "evaluated_at")

        object.__setattr__(
            self,
            "decision_score",
            _validate_score(
                self.decision_score,
                "decision_score",
            ),
        )

        if self.executes_security_actions:
            raise PolicyValidationError(
                "Policy layer cannot execute actions"
            )

        object.__setattr__(
            self,
            "constraints",
            _freeze(self.constraints),
        )

        if not isinstance(self.violations, tuple):
            object.__setattr__(
                self,
                "violations",
                tuple(self.violations),
            )

        if not isinstance(self.reason_codes, tuple):
            object.__setattr__(
                self,
                "reason_codes",
                tuple(self.reason_codes),
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert evaluation contract to JSON-safe dictionary."""
        return {
            "evaluation_id": self.evaluation_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "intent": self.intent.value,
            "lifecycle": self.lifecycle.value,
            "allowed": self.allowed,
            "decision_score": self.decision_score,
            "prediction_id": self.prediction_id,
            "evaluated_at": _iso(self.evaluated_at),
            "constraints": _unfreeze(self.constraints),
            "violations": list(self.violations),
            "reason_codes": list(self.reason_codes),
            "rationale": self.rationale,
            "executes_security_actions": False,
        }


# ============================================================================
# Policy Engine
# ============================================================================


class ADIEPolicy:
    """
    Canonical ADIE policy evaluator.

    Responsibilities:
    - evaluate evidence.
    - enforce constraints.
    - produce PolicyEvaluation.
    - preserve audit semantics.

    Non responsibilities:
    - prediction.
    - decision execution.
    - response handling.
    """

    def __init__(
        self,
        config: Optional[PolicyConfig] = None,
    ) -> None:
        self._config = (
            config
            if config is not None
            else PolicyConfig(
                policy_id="default-policy",
                policy_version="1.0.0",
            )
        )

        self._evaluation_counter = 0
        self._lock = threading.Lock()

    def evaluate(
        self,
        evidence: PolicyEvidence,
    ) -> PolicyEvaluation:
        """
        Evaluate evidence against policy.
        """
        if not isinstance(evidence, PolicyEvidence):
            raise PolicyValidationError("PolicyEvidence required")

        with self._lock:
            self._evaluation_counter += 1
            counter = self._evaluation_counter

        score = self._calculate_score(evidence)

        intent, allowed, reasons = self._evaluate_intent(score)

        lifecycle = (
            PolicyLifecycle.APPROVED
            if allowed
            else PolicyLifecycle.BLOCKED
        )

        evaluation_id = self._create_evaluation_id(
            evidence,
            score,
            counter,
        )

        return PolicyEvaluation(
            evaluation_id=evaluation_id,
            policy_id=self._config.policy_id,
            policy_version=self._config.policy_version,
            intent=intent,
            lifecycle=lifecycle,
            allowed=allowed,
            decision_score=score,
            prediction_id=evidence.prediction_id,
            evaluated_at=_utc_now(),
            constraints={
                "monitor_threshold": self._config.monitor_threshold,
                "alert_threshold": self._config.alert_threshold,
                "contain_threshold": self._config.contain_threshold,
                "isolate_threshold": self._config.isolate_threshold,
            },
            violations=() if allowed else ("POLICY_BLOCKED",),
            reason_codes=tuple(reasons),
            rationale=(
                "Policy evaluation completed. "
                "Execution remains outside ADIE."
            ),
        )

    @staticmethod
    def _calculate_score(
        evidence: PolicyEvidence,
    ) -> float:
        """
        Calculate deterministic weighted decision score.
        """
        score = (
            (0.55 * evidence.threat_probability)
            + (0.25 * evidence.prediction_confidence)
            + (0.20 * evidence.state_risk)
        )

        return round(
            min(
                1.0,
                max(
                    0.0,
                    score,
                ),
            ),
            6,
        )

    def _evaluate_intent(
        self,
        score: float,
    ) -> tuple[PolicyIntent, bool, list[str]]:
        """
        Evaluate policy intent boundaries based on thresholds.
        """
        reasons: list[str] = []

        if score >= self._config.isolate_threshold:
            reasons.append("ISOLATE_THRESHOLD_REACHED")
            return PolicyIntent.ISOLATE, True, reasons

        if score >= self._config.contain_threshold:
            reasons.append("CONTAIN_THRESHOLD_REACHED")
            return PolicyIntent.CONTAIN, True, reasons

        if score >= self._config.alert_threshold:
            reasons.append("ALERT_THRESHOLD_REACHED")
            return PolicyIntent.ALERT, True, reasons

        if score >= self._config.monitor_threshold:
            reasons.append("MONITORING_REQUIRED")
            return PolicyIntent.MONITOR, True, reasons

        reasons.append("LOW_RISK")
        return PolicyIntent.ALLOW, True, reasons

    def _create_evaluation_id(
        self,
        evidence: PolicyEvidence,
        score: float,
        counter: int,
    ) -> str:
        """
        Create deterministic policy evaluation identifier.
        """
        payload = {
            "counter": counter,
            "prediction_id": evidence.prediction_id,
            "state_id": evidence.state_id,
            "threat_probability": f"{evidence.threat_probability:.6f}",
            "prediction_confidence": f"{evidence.prediction_confidence:.6f}",
            "state_risk": f"{evidence.state_risk:.6f}",
            "score": f"{score:.6f}",
            "policy_id": self._config.policy_id,
            "policy_version": self._config.policy_version,
        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = sha256(serialized.encode("utf-8")).hexdigest()

        return f"peval-{digest[:24]}"

    def status(self) -> dict[str, Any]:
        """
        Return policy engine status snapshot.
        """
        with self._lock:
            count = self._evaluation_counter

        return {
            "module": MODULE_NAME,
            "version": MODULE_VERSION,
            "policy_id": self._config.policy_id,
            "policy_version": self._config.policy_version,
            "evaluation_count": count,
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    def health_check(self) -> dict[str, Any]:
        """
        Validate policy boundary health.
        """
        healthy = (
            EXECUTES_SECURITY_ACTIONS is False
            and DESTRUCTIVE_ACTIONS_ALLOWED is False
        )

        return {
            "healthy": healthy,
            "module": MODULE_NAME,
            "version": MODULE_VERSION,
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    def self_test(self) -> dict[str, Any]:
        """
        Production policy contract validation.
        """
        tests: dict[str, bool] = {}

        try:
            evidence = PolicyEvidence(
                prediction_id="prediction-test",
                threat_probability=0.90,
                prediction_confidence=0.95,
                state_risk=0.80,
                state_id="state-test",
                collected_at=_utc_now(),
            )

            result = self.evaluate(evidence)

            tests["evaluation_created"] = isinstance(
                result, PolicyEvaluation
            )

            tests["policy_authority"] = (
                result.allowed is True
                and result.intent
                in {
                    PolicyIntent.CONTAIN,
                    PolicyIntent.ISOLATE,
                    PolicyIntent.ALERT,
                }
            )

            tests["immutable_contract"] = False
            try:
                result.intent = PolicyIntent.ALLOW  # type: ignore
            except Exception:
                tests["immutable_contract"] = True

            tests["utc_timestamp"] = result.evaluated_at.tzinfo is not None

            serialized = result.to_dict()

            tests["json_safe"] = (
                isinstance(serialized, dict)
                and isinstance(serialized["reason_codes"], list)
            )

            tests["execution_boundary"] = (
                result.executes_security_actions is False
            )

            tests["deterministic_id"] = result.evaluation_id.startswith(
                "peval-"
            )

            passed = all(tests.values())

            return {
                "passed": passed,
                "module": MODULE_NAME,
                "version": MODULE_VERSION,
                "policy_test_passed": passed,
                "tests": tests,
                "executes_security_actions": False,
                "destructive_actions_allowed": False,
            }

        except Exception as exc:
            return {
                "passed": False,
                "module": MODULE_NAME,
                "version": MODULE_VERSION,
                "policy_test_passed": False,
                "tests": tests,
                "error": type(exc).__name__,
                "error_message": str(exc),
                "executes_security_actions": False,
            }


# ============================================================================
# Default Policy Instance (Thread-Safe Singleton)
# ============================================================================


_default_policy: Optional[ADIEPolicy] = None
_policy_lock = threading.Lock()


def get_policy() -> ADIEPolicy:
    """
    Return process-local default ADIE policy (Thread-Safe).
    """
    global _default_policy

    if _default_policy is None:
        with _policy_lock:
            if _default_policy is None:
                _default_policy = ADIEPolicy()

    return _default_policy


def self_test() -> dict[str, Any]:
    """
    Module-level self test.
    """
    return ADIEPolicy().self_test()


# ============================================================================
# Public API
# ============================================================================


__all__ = [
    "MODULE_NAME",
    "MODULE_VERSION",
    "PolicyError",
    "PolicyValidationError",
    "PolicyEvaluationError",
    "PolicyIntent",
    "PolicyLifecycle",
    "PolicyConfig",
    "PolicyEvidence",
    "PolicyEvaluation",
    "ADIEPolicy",
    "get_policy",
    "self_test",
]


# ============================================================================
# Module Execution
# ============================================================================


def _main() -> int:

    result = self_test()

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    )

    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
