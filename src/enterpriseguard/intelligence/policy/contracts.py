"""
EnterpriseGuard - ADIE Policy Contracts
========================================

Adaptive Defense Intelligence Engine (ADIE)

Policy Domain Contracts
-----------------------

This module defines the immutable contracts used by the ADIE Policy
layer.

Architecture
------------

    EnterpriseState
          |
          v
    PredictionResult
          |
          v
    PolicyRequest
          |
          v
    PolicyEvaluation
          |
          v
      Decision Layer


Purpose
-------

The Policy contract layer defines WHAT policy evaluation means.

It does NOT implement:

- security actions
- response execution
- playbooks
- rollback
- detection
- ML inference
- model loading
- model training
- networking
- filesystem operations
- UI rendering


Policy responsibility
---------------------

Policy evaluates:

    current state
        +
    predicted future
        +
    explicit policy rules
        +
    constraints

and produces a structured evaluation.

Policy does NOT directly execute the resulting recommendation.


Design Principles
-----------------

1. Immutable contracts
2. Explicit validation
3. Stable serialization
4. Framework independence
5. Domain isolation
6. Explainable policy evaluation
7. Explicit rule provenance
8. Constraint visibility
9. Decision-layer compatibility
10. Safe forward evolution


Policy flow
-----------

    PolicyRequest
          |
          +---- Current State Reference
          |
          +---- Prediction Result
          |
          +---- Policy Context
          |
          v
    PolicyEvaluation
          |
          +---- Rule evaluations
          +---- Violations
          +---- Constraints
          +---- Risk posture
          +---- Recommended decision class
          |
          v
       Decision Layer


Important semantic boundary
---------------------------

Policy may recommend a decision class.

Policy MUST NOT execute the decision.

For example:

    "ESCALATE"

is an evaluation output.

It is NOT an executed security action.


Version
-------

1.0.0
"""


from __future__ import annotations


# ============================================================================
# Standard library
# ============================================================================

import dataclasses

from dataclasses import (
    MISSING,
    dataclass,
    field,
    fields,
)
from datetime import (
    datetime,
    timezone,
)
from enum import Enum
from math import isfinite
from typing import (
    Any,
    Mapping,
    Sequence,
)


# ============================================================================
# Module metadata
# ============================================================================

__all__ = [
    "POLICY_CONTRACT_VERSION",
    "PolicyStatus",
    "PolicyDecisionClass",
    "PolicyRuleEffect",
    "PolicyConstraintType",
    "PolicyRule",
    "PolicyViolation",
    "PolicyConstraint",
    "PolicyRequest",
    "PolicyEvaluation",
    "validate_policy_request",
    "validate_policy_evaluation",
    "policy_request_to_dict",
    "policy_evaluation_to_dict",
    "is_policy_evaluation_usable",
]


# ============================================================================
# Constants
# ============================================================================

POLICY_CONTRACT_VERSION = "1.0.0"

MAX_RULE_COUNT = 10_000

MAX_VIOLATION_COUNT = 10_000

MAX_CONSTRAINT_COUNT = 10_000

MAX_CONTEXT_ITEMS = 1_000

MIN_SCORE = 0.0

MAX_SCORE = 1.0


# ============================================================================
# Utility functions
# ============================================================================


def _utc_now() -> datetime:
    """
    Return the current timezone-aware UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    )


def _ensure_utc(
    value: datetime,
) -> datetime:
    """
    Normalize a datetime to UTC.

    Naive timestamps are rejected because policy evaluation
    participates in ADIE temporal reasoning.
    """

    if not isinstance(
        value,
        datetime,
    ):
        raise TypeError(
            "timestamp must be a datetime"
        )

    if value.tzinfo is None:
        raise ValueError(
            "timestamp must be timezone-aware"
        )

    return value.astimezone(
        timezone.utc
    )


def _validate_string(
    value: str,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> str:
    """
    Validate and normalize a string value.
    """

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if (
        not allow_empty
        and not normalized
    ):
        raise ValueError(
            f"{field_name} must not be empty"
        )

    return normalized


def _validate_score(
    value: float,
    field_name: str,
) -> float:
    """
    Validate a normalized 0..1 score.
    """

    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    try:
        numeric = float(value)

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise TypeError(
            f"{field_name} must be numeric"
        ) from exc

    if not isfinite(
        numeric
    ):
        raise ValueError(
            f"{field_name} must be finite"
        )

    if not (
        MIN_SCORE
        <= numeric
        <= MAX_SCORE
    ):
        raise ValueError(
            f"{field_name} must be between "
            "0.0 and 1.0"
        )

    return numeric


def _validate_non_negative_int(
    value: int,
    field_name: str,
) -> int:
    """
    Validate a non-negative integer.
    """

    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    if not isinstance(
        value,
        int,
    ):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    if value < 0:
        raise ValueError(
            f"{field_name} must not be negative"
        )

    return value


def _freeze_pairs(
    value: Mapping[str, Any] | Sequence[tuple[str, Any]] | None,
    field_name: str,
    *,
    maximum: int = MAX_CONTEXT_ITEMS,
) -> tuple[tuple[str, Any], ...]:
    """
    Convert a mapping-like structure into immutable pairs.
    """

    if value is None:
        return ()

    if isinstance(
        value,
        Mapping,
    ):

        items = list(
            value.items()
        )

    else:

        if isinstance(
            value,
            (
                str,
                bytes,
            ),
        ):
            raise TypeError(
                f"{field_name} must be a mapping or pair sequence"
            )

        try:
            items = list(
                value
            )

        except TypeError as exc:
            raise TypeError(
                f"{field_name} must be mapping-like"
            ) from exc

    if len(items) > maximum:
        raise ValueError(
            f"{field_name} contains too many items"
        )

    normalized: list[
        tuple[str, Any]
    ] = []

    for item in items:

        if not isinstance(
            item,
            tuple,
        ) or len(item) != 2:
            raise TypeError(
                f"{field_name} entries must be "
                "(key, value) pairs"
            )

        key, val = item

        normalized_key = _validate_string(
            key,
            f"{field_name} key",
        )

        normalized.append(
            (
                normalized_key,
                val,
            )
        )

    return tuple(
        normalized
    )


def _pairs_to_dict(
    value: Sequence[tuple[str, Any]],
) -> dict[str, Any]:
    """
    Convert immutable pairs into a plain dictionary.
    """

    return {
        key: item
        for key, item in value
    }


def _normalize_sequence(
    value: Sequence[Any],
    field_name: str,
    *,
    maximum: int,
) -> tuple[Any, ...]:
    """
    Normalize a sequence to an immutable tuple.
    """

    if isinstance(
        value,
        (
            str,
            bytes,
        ),
    ):
        raise TypeError(
            f"{field_name} must be a sequence"
        )

    try:
        items = tuple(
            value
        )

    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be a sequence"
        ) from exc

    if len(items) > maximum:
        raise ValueError(
            f"{field_name} contains too many items"
        )

    return items


# ============================================================================
# Enums
# ============================================================================


class PolicyStatus(str, Enum):
    """
    Lifecycle status of policy evaluation.
    """

    EVALUATED = "evaluated"

    ACCEPTED = "accepted"

    REJECTED = "rejected"

    CONSTRAINED = "constrained"

    INVALID = "invalid"


class PolicyDecisionClass(str, Enum):
    """
    Decision class produced by policy evaluation.

    This is a recommendation/evaluation output.

    It is NOT an executed action.
    """

    NONE = "none"

    MONITOR = "monitor"

    ALERT = "alert"

    ESCALATE = "escalate"

    RESTRICT = "restrict"


class PolicyRuleEffect(str, Enum):
    """
    Effect produced when a policy rule matches.
    """

    ALLOW = "allow"

    DENY = "deny"

    REQUIRE_REVIEW = "require_review"

    ESCALATE = "escalate"

    MONITOR = "monitor"


class PolicyConstraintType(str, Enum):
    """
    Types of policy constraints.
    """

    SAFETY = "safety"

    AUTHORIZATION = "authorization"

    ENVIRONMENT = "environment"

    CONFIDENCE = "confidence"

    TEMPORAL = "temporal"

    OPERATIONAL = "operational"


# ============================================================================
# Policy Rule
# ============================================================================


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """
    Immutable policy rule definition.

    A rule describes a policy condition and its semantic effect.

    It does not execute any action.
    """

    rule_id: str

    name: str

    effect: PolicyRuleEffect

    priority: int = 100

    enabled: bool = True

    condition: Mapping[str, Any] | Sequence[tuple[str, Any]] = field(
        default_factory=dict
    )

    description: str | None = None

    metadata: Mapping[str, Any] | Sequence[tuple[str, Any]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "rule_id",
            _validate_string(
                self.rule_id,
                "rule_id",
            ),
        )

        object.__setattr__(
            self,
            "name",
            _validate_string(
                self.name,
                "name",
            ),
        )

        if not isinstance(
            self.effect,
            PolicyRuleEffect,
        ):

            try:

                normalized_effect = (
                    PolicyRuleEffect(
                        self.effect
                    )
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "effect must be a valid PolicyRuleEffect"
                ) from exc

            object.__setattr__(
                self,
                "effect",
                normalized_effect,
            )

        object.__setattr__(
            self,
            "priority",
            _validate_non_negative_int(
                self.priority,
                "priority",
            ),
        )

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be boolean"
            )

        condition = _freeze_pairs(
            self.condition,
            "condition",
        )

        metadata = _freeze_pairs(
            self.metadata,
            "metadata",
        )

        object.__setattr__(
            self,
            "condition",
            condition,
        )

        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

        if self.description is not None:

            object.__setattr__(
                self,
                "description",
                _validate_string(
                    self.description,
                    "description",
                ),
            )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the rule.
        """

        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "effect": self.effect.value,
            "priority": self.priority,
            "enabled": self.enabled,
            "condition": _pairs_to_dict(
                self.condition
            ),
            "description": self.description,
            "metadata": _pairs_to_dict(
                self.metadata
            ),
        }


# ============================================================================
# Policy Violation
# ============================================================================


@dataclass(frozen=True, slots=True)
class PolicyViolation:
    """
    Immutable policy violation.

    A violation describes why policy conditions were not satisfied.
    """

    rule_id: str

    code: str

    message: str

    severity: str = "medium"

    evidence: Mapping[str, Any] | Sequence[tuple[str, Any]] = field(
        default_factory=dict
    )

    timestamp: datetime = field(
        default_factory=_utc_now
    )

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "rule_id",
            _validate_string(
                self.rule_id,
                "rule_id",
            ),
        )

        object.__setattr__(
            self,
            "code",
            _validate_string(
                self.code,
                "code",
            ),
        )

        object.__setattr__(
            self,
            "message",
            _validate_string(
                self.message,
                "message",
            ),
        )

        object.__setattr__(
            self,
            "severity",
            _validate_string(
                self.severity,
                "severity",
            ),
        )

        object.__setattr__(
            self,
            "evidence",
            _freeze_pairs(
                self.evidence,
                "evidence",
            ),
        )

        object.__setattr__(
            self,
            "timestamp",
            _ensure_utc(
                self.timestamp
            ),
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the violation.
        """

        return {
            "rule_id": self.rule_id,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "evidence": _pairs_to_dict(
                self.evidence
            ),
            "timestamp": (
                self.timestamp.isoformat()
            ),
        }


# ============================================================================
# Policy Constraint
# ============================================================================


@dataclass(frozen=True, slots=True)
class PolicyConstraint:
    """
    Immutable policy constraint.

    A constraint limits or qualifies the applicability of a policy
    evaluation.

    It does not execute or block an external action by itself.
    """

    constraint_id: str

    constraint_type: PolicyConstraintType

    description: str

    satisfied: bool

    source: str = "policy"

    metadata: Mapping[str, Any] | Sequence[tuple[str, Any]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "constraint_id",
            _validate_string(
                self.constraint_id,
                "constraint_id",
            ),
        )

        if not isinstance(
            self.constraint_type,
            PolicyConstraintType,
        ):

            try:

                normalized_type = (
                    PolicyConstraintType(
                        self.constraint_type
                    )
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "constraint_type must be a valid "
                    "PolicyConstraintType"
                ) from exc

            object.__setattr__(
                self,
                "constraint_type",
                normalized_type,
            )

        object.__setattr__(
            self,
            "description",
            _validate_string(
                self.description,
                "description",
            ),
        )

        if not isinstance(
            self.satisfied,
            bool,
        ):
            raise TypeError(
                "satisfied must be boolean"
            )

        object.__setattr__(
            self,
            "source",
            _validate_string(
                self.source,
                "source",
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_pairs(
                self.metadata,
                "metadata",
            ),
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the constraint.
        """

        return {
            "constraint_id": self.constraint_id,
            "constraint_type": (
                self.constraint_type.value
            ),
            "description": self.description,
            "satisfied": self.satisfied,
            "source": self.source,
            "metadata": _pairs_to_dict(
                self.metadata
            ),
        }


# ============================================================================
# Policy Request
# ============================================================================


@dataclass(frozen=True, slots=True)
class PolicyRequest:
    """
    Immutable input contract for policy evaluation.

    Required conceptual inputs:

        state_id
        prediction
        rules

    The actual EnterpriseState object is intentionally not duplicated
    here. Policy consumes its stable reference plus contextual state
    information supplied by the caller.

    This keeps the contract decoupled from the concrete State class.
    """

    state_id: str

    prediction: Any

    rules: tuple[PolicyRule, ...]

    requested_at: datetime = field(
        default_factory=_utc_now
    )

    context: Mapping[str, Any] | Sequence[tuple[str, Any]] = field(
        default_factory=dict
    )

    source: str = "enterpriseguard"

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "state_id",
            _validate_string(
                self.state_id,
                "state_id",
            ),
        )

        if self.prediction is None:
            raise TypeError(
                "prediction must not be None"
            )

        rules = _normalize_sequence(
            self.rules,
            "rules",
            maximum=MAX_RULE_COUNT,
        )

        for rule in rules:

            if not isinstance(
                rule,
                PolicyRule,
            ):
                raise TypeError(
                    "rules must contain PolicyRule objects"
                )

        object.__setattr__(
            self,
            "rules",
            rules,
        )

        object.__setattr__(
            self,
            "requested_at",
            _ensure_utc(
                self.requested_at
            ),
        )

        object.__setattr__(
            self,
            "context",
            _freeze_pairs(
                self.context,
                "context",
            ),
        )

        object.__setattr__(
            self,
            "source",
            _validate_string(
                self.source,
                "source",
            ),
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the policy request.

        Prediction is serialized through to_dict() when available.
        """

        if hasattr(
            self.prediction,
            "to_dict",
        ):

            try:
                prediction_data = (
                    self.prediction.to_dict()
                )

            except Exception:
                prediction_data = str(
                    self.prediction
                )

        else:

            prediction_data = self.prediction

        return {
            "state_id": self.state_id,
            "prediction": prediction_data,
            "rules": [
                rule.to_dict()
                for rule in self.rules
            ],
            "requested_at": (
                self.requested_at.isoformat()
            ),
            "context": _pairs_to_dict(
                self.context
            ),
            "source": self.source,
        }


# ============================================================================
# Policy Evaluation
# ============================================================================


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    """
    Immutable result of policy evaluation.

    This is the primary Policy-domain output.

    It may contain a recommended decision class, but it never
    represents an executed action.
    """

    request: PolicyRequest

    status: PolicyStatus

    decision_class: PolicyDecisionClass

    policy_score: float

    applicable_rules: tuple[
        PolicyRule,
        ...
    ] = ()

    violations: tuple[
        PolicyViolation,
        ...
    ] = ()

    constraints: tuple[
        PolicyConstraint,
        ...
    ] = ()

    rationale: str = ""

    evaluated_at: datetime = field(
        default_factory=_utc_now
    )

    evaluator_version: str = (
        "adie-policy-contracts-1.0.0"
    )

    evaluation_id: str | None = None

    metadata: Mapping[str, Any] | Sequence[tuple[str, Any]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:

        if not isinstance(
            self.request,
            PolicyRequest,
        ):
            raise TypeError(
                "request must be a PolicyRequest"
            )

        if not isinstance(
            self.status,
            PolicyStatus,
        ):

            try:

                normalized_status = (
                    PolicyStatus(
                        self.status
                    )
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "status must be a valid PolicyStatus"
                ) from exc

            object.__setattr__(
                self,
                "status",
                normalized_status,
            )

        if not isinstance(
            self.decision_class,
            PolicyDecisionClass,
        ):

            try:

                normalized_decision = (
                    PolicyDecisionClass(
                        self.decision_class
                    )
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "decision_class must be a valid "
                    "PolicyDecisionClass"
                ) from exc

            object.__setattr__(
                self,
                "decision_class",
                normalized_decision,
            )

        object.__setattr__(
            self,
            "policy_score",
            _validate_score(
                self.policy_score,
                "policy_score",
            ),
        )

        applicable_rules = _normalize_sequence(
            self.applicable_rules,
            "applicable_rules",
            maximum=MAX_RULE_COUNT,
        )

        for rule in applicable_rules:

            if not isinstance(
                rule,
                PolicyRule,
            ):
                raise TypeError(
                    "applicable_rules must contain PolicyRule objects"
                )

        object.__setattr__(
            self,
            "applicable_rules",
            applicable_rules,
        )

        violations = _normalize_sequence(
            self.violations,
            "violations",
            maximum=MAX_VIOLATION_COUNT,
        )

        for violation in violations:

            if not isinstance(
                violation,
                PolicyViolation,
            ):
                raise TypeError(
                    "violations must contain PolicyViolation objects"
                )

        object.__setattr__(
            self,
            "violations",
            violations,
        )

        constraints = _normalize_sequence(
            self.constraints,
            "constraints",
            maximum=MAX_CONSTRAINT_COUNT,
        )

        for constraint in constraints:

            if not isinstance(
                constraint,
                PolicyConstraint,
            ):
                raise TypeError(
                    "constraints must contain PolicyConstraint objects"
                )

        object.__setattr__(
            self,
            "constraints",
            constraints,
        )

        object.__setattr__(
            self,
            "rationale",
            _validate_string(
                self.rationale,
                "rationale",
                allow_empty=True,
            ),
        )

        object.__setattr__(
            self,
            "evaluated_at",
            _ensure_utc(
                self.evaluated_at
            ),
        )

        object.__setattr__(
            self,
            "evaluator_version",
            _validate_string(
                self.evaluator_version,
                "evaluator_version",
            ),
        )

        if self.evaluation_id is not None:

            object.__setattr__(
                self,
                "evaluation_id",
                _validate_string(
                    self.evaluation_id,
                    "evaluation_id",
                ),
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_pairs(
                self.metadata,
                "metadata",
            ),
        )

    # ------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------

    @property
    def has_violations(
        self,
    ) -> bool:
        """
        Return True when policy violations exist.
        """

        return bool(
            self.violations
        )

    @property
    def has_unsatisfied_constraints(
        self,
    ) -> bool:
        """
        Return True when one or more constraints are not satisfied.
        """

        return any(
            not constraint.satisfied
            for constraint
            in self.constraints
        )

    @property
    def constraint_count(
        self,
    ) -> int:
        """
        Return total number of constraints.
        """

        return len(
            self.constraints
        )

    @property
    def satisfied_constraint_count(
        self,
    ) -> int:
        """
        Return number of satisfied constraints.
        """

        return sum(
            1
            for constraint
            in self.constraints
            if constraint.satisfied
        )

    @property
    def violation_count(
        self,
    ) -> int:
        """
        Return violation count.
        """

        return len(
            self.violations
        )

    # ------------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the complete policy evaluation.
        """

        return {
            "contract_version": (
                POLICY_CONTRACT_VERSION
            ),
            "evaluation_id": self.evaluation_id,
            "status": self.status.value,
            "decision_class": (
                self.decision_class.value
            ),
            "policy_score": self.policy_score,
            "request": self.request.to_dict(),
            "applicable_rules": [
                rule.to_dict()
                for rule in self.applicable_rules
            ],
            "violations": [
                violation.to_dict()
                for violation in self.violations
            ],
            "constraints": [
                constraint.to_dict()
                for constraint in self.constraints
            ],
            "rationale": self.rationale,
            "evaluated_at": (
                self.evaluated_at.isoformat()
            ),
            "evaluator_version": (
                self.evaluator_version
            ),
            "has_violations": self.has_violations,
            "has_unsatisfied_constraints": (
                self.has_unsatisfied_constraints
            ),
            "constraint_count": (
                self.constraint_count
            ),
            "satisfied_constraint_count": (
                self.satisfied_constraint_count
            ),
            "violation_count": (
                self.violation_count
            ),
            "metadata": _pairs_to_dict(
                self.metadata
            ),
        }


# ============================================================================
# Validation
# ============================================================================


def validate_policy_request(
    request: PolicyRequest,
) -> bool:
    """
    Validate a PolicyRequest.

    Raises TypeError/ValueError on invalid contracts.

    Returns True when valid.
    """

    if not isinstance(
        request,
        PolicyRequest,
    ):
        raise TypeError(
            "request must be a PolicyRequest"
        )

    if not request.state_id:
        raise ValueError(
            "request.state_id must not be empty"
        )

    if request.prediction is None:
        raise ValueError(
            "request.prediction must not be None"
        )

    if not request.rules:
        raise ValueError(
            "request must contain at least one policy rule"
        )

    return True


def validate_policy_evaluation(
    evaluation: PolicyEvaluation,
) -> bool:
    """
    Validate a PolicyEvaluation.

    Returns True when valid.
    """

    if not isinstance(
        evaluation,
        PolicyEvaluation,
    ):
        raise TypeError(
            "evaluation must be a PolicyEvaluation"
        )

    validate_policy_request(
        evaluation.request
    )

    _validate_score(
        evaluation.policy_score,
        "policy_score",
    )

    return True


# ============================================================================
# Serialization helpers
# ============================================================================


def policy_request_to_dict(
    request: PolicyRequest,
) -> dict[str, Any]:
    """
    Serialize a PolicyRequest.
    """

    validate_policy_request(
        request
    )

    return request.to_dict()


def policy_evaluation_to_dict(
    evaluation: PolicyEvaluation,
) -> dict[str, Any]:
    """
    Serialize a PolicyEvaluation.
    """

    validate_policy_evaluation(
        evaluation
    )

    return evaluation.to_dict()


def is_policy_evaluation_usable(
    evaluation: PolicyEvaluation,
) -> bool:
    """
    Determine whether an evaluation is usable by downstream layers.

    This does not mean the decision is approved or executed.
    """

    if not isinstance(
        evaluation,
        PolicyEvaluation,
    ):
        return False

    return (
        evaluation.status
        in {
            PolicyStatus.EVALUATED,
            PolicyStatus.ACCEPTED,
            PolicyStatus.CONSTRAINED,
        }
    )


# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Comprehensive isolated self-test for Policy Contracts.

    No:

    - Detector
    - ModelManager
    - Dashboard
    - Response subsystem
    - filesystem
    - network

    is required.
    """

    # ------------------------------------------------------------------------
    # Fake prediction object
    # ------------------------------------------------------------------------

    class FakePrediction:
        """
        Minimal prediction representation.

        It intentionally exposes the same conceptual fields consumed
        by the policy domain without importing PredictionResult itself.
        """

        def __init__(self) -> None:

            self.predicted_value = (
                "elevated_security_pressure"
            )

            self.confidence = 0.82

        def to_dict(self) -> dict[str, Any]:

            return {
                "predicted_value": (
                    self.predicted_value
                ),
                "confidence": (
                    self.confidence
                ),
            }

    prediction = FakePrediction()

    # ------------------------------------------------------------------------
    # Test 1: Rule
    # ------------------------------------------------------------------------

    rule = PolicyRule(
        rule_id="R-001",
        name="Elevated Risk Monitoring",
        effect=PolicyRuleEffect.ESCALATE,
        priority=10,
        enabled=True,
        condition={
            "risk_score": ">=0.70",
        },
        description=(
            "Escalate evaluations with elevated risk."
        ),
        metadata={
            "source": "self-test",
        },
    )

    assert (
        rule.rule_id
        == "R-001"
    )

    assert (
        rule.effect
        == PolicyRuleEffect.ESCALATE
    )

    assert (
        rule.priority
        == 10
    )

    assert (
        rule.to_dict()["effect"]
        == "escalate"
    )

    # ------------------------------------------------------------------------
    # Test 2: Violation
    # ------------------------------------------------------------------------

    violation = PolicyViolation(
        rule_id="R-001",
        code="RISK_THRESHOLD",
        message=(
            "Risk exceeds configured policy threshold."
        ),
        severity="high",
        evidence={
            "risk_score": 0.82,
        },
    )

    assert (
        violation.rule_id
        == "R-001"
    )

    assert (
        violation.severity
        == "high"
    )

    assert (
        violation.to_dict()["code"]
        == "RISK_THRESHOLD"
    )

    # ------------------------------------------------------------------------
    # Test 3: Constraint
    # ------------------------------------------------------------------------

    constraint = PolicyConstraint(
        constraint_id="C-001",
        constraint_type=(
            PolicyConstraintType.CONFIDENCE
        ),
        description=(
            "Prediction confidence must be sufficient."
        ),
        satisfied=True,
        source="self-test",
    )

    assert (
        constraint.constraint_type
        == PolicyConstraintType.CONFIDENCE
    )

    assert (
        constraint.satisfied
        is True
    )

    # ------------------------------------------------------------------------
    # Test 4: Policy request
    # ------------------------------------------------------------------------

    request = PolicyRequest(
        state_id="state-self-test-001",
        prediction=prediction,
        rules=(
            rule,
        ),
        context={
            "environment": "test",
            "region": "local",
        },
        source="self-test",
    )

    assert (
        request.state_id
        == "state-self-test-001"
    )

    assert (
        len(request.rules)
        == 1
    )

    assert (
        dict(request.context)[
            "environment"
        ]
        == "test"
    )

    validate_policy_request(
        request
    )

    # ------------------------------------------------------------------------
    # Test 5: Policy evaluation
    # ------------------------------------------------------------------------

    evaluation = PolicyEvaluation(
        request=request,
        status=PolicyStatus.EVALUATED,
        decision_class=(
            PolicyDecisionClass.ESCALATE
        ),
        policy_score=0.82,
        applicable_rules=(
            rule,
        ),
        violations=(
            violation,
        ),
        constraints=(
            constraint,
        ),
        rationale=(
            "The evaluated risk exceeds the configured "
            "policy threshold."
        ),
        evaluation_id=(
            "evaluation-self-test-001"
        ),
        metadata={
            "evaluator": "self-test",
        },
    )

    assert (
        evaluation.status
        == PolicyStatus.EVALUATED
    )

    assert (
        evaluation.decision_class
        == PolicyDecisionClass.ESCALATE
    )

    assert (
        evaluation.policy_score
        == 0.82
    )

    assert (
        evaluation.has_violations
        is True
    )

    assert (
        evaluation.has_unsatisfied_constraints
        is False
    )

    assert (
        evaluation.violation_count
        == 1
    )

    assert (
        evaluation.constraint_count
        == 1
    )

    assert (
        evaluation.satisfied_constraint_count
        == 1
    )

    # ------------------------------------------------------------------------
    # Test 6: Serialization
    # ------------------------------------------------------------------------

    serialized_request = (
        policy_request_to_dict(
            request
        )
    )

    assert isinstance(
        serialized_request,
        dict,
    )

    assert (
        serialized_request[
            "state_id"
        ]
        == "state-self-test-001"
    )

    serialized_evaluation = (
        policy_evaluation_to_dict(
            evaluation
        )
    )

    assert isinstance(
        serialized_evaluation,
        dict,
    )

    assert (
        serialized_evaluation[
            "status"
        ]
        == "evaluated"
    )

    assert (
        serialized_evaluation[
            "decision_class"
        ]
        == "escalate"
    )

    assert (
        serialized_evaluation[
            "policy_score"
        ]
        == 0.82
    )

    # ------------------------------------------------------------------------
    # Test 7: Usability
    # ------------------------------------------------------------------------

    assert (
        is_policy_evaluation_usable(
            evaluation
        )
        is True
    )

    # ------------------------------------------------------------------------
    # Test 8: Immutability
    # ------------------------------------------------------------------------

    immutable_failed = False

    try:

        evaluation.policy_score = 0.25

    except (
        dataclasses.FrozenInstanceError,
    ):

        immutable_failed = True

    assert (
        immutable_failed
        is True
    )

    # ------------------------------------------------------------------------
    # Test 9: Invalid score
    # ------------------------------------------------------------------------

    invalid_score_failed = False

    try:

        PolicyEvaluation(
            request=request,
            status=PolicyStatus.EVALUATED,
            decision_class=(
                PolicyDecisionClass.ALERT
            ),
            policy_score=1.50,
        )

    except ValueError:

        invalid_score_failed = True

    assert (
        invalid_score_failed
        is True
    )

    # ------------------------------------------------------------------------
    # Test 10: Invalid rule effect
    # ------------------------------------------------------------------------

    invalid_effect_failed = False

    try:

        PolicyRule(
            rule_id="R-invalid",
            name="Invalid",
            effect="not-a-real-effect",
        )

    except ValueError:

        invalid_effect_failed = True

    assert (
        invalid_effect_failed
        is True
    )

    # ------------------------------------------------------------------------
    # Test 11: Invalid violation
    # ------------------------------------------------------------------------

    invalid_violation_failed = False

    try:

        PolicyViolation(
            rule_id="",
            code="TEST",
            message="Invalid rule id",
        )

    except ValueError:

        invalid_violation_failed = True

    assert (
        invalid_violation_failed
        is True
    )

    # ------------------------------------------------------------------------
    # Test 12: Invalid constraint
    # ------------------------------------------------------------------------

    invalid_constraint_failed = False

    try:

        PolicyConstraint(
            constraint_id="C-invalid",
            constraint_type="invalid-type",
            description="Invalid",
            satisfied=True,
        )

    except ValueError:

        invalid_constraint_failed = True

    assert (
        invalid_constraint_failed
        is True
    )

    # ------------------------------------------------------------------------
    # Test 13: Request without rules
    # ------------------------------------------------------------------------

    empty_rules_failed = False

    try:

        empty_request = PolicyRequest(
            state_id="state-empty",
            prediction=prediction,
            rules=(),
        )

        validate_policy_request(
            empty_request
        )

    except ValueError:

        empty_rules_failed = True

    assert (
        empty_rules_failed
        is True
    )

    # ------------------------------------------------------------------------
    # Test 14: Timestamp
    # ------------------------------------------------------------------------

    assert (
        request.requested_at.tzinfo
        is not None
    )

    assert (
        evaluation.evaluated_at.tzinfo
        is not None
    )

    assert (
        violation.timestamp.tzinfo
        is not None
    )

    # ------------------------------------------------------------------------
    # Test 15: Frozen nested structures
    # ------------------------------------------------------------------------

    assert isinstance(
        request.rules,
        tuple,
    )

    assert isinstance(
        evaluation.applicable_rules,
        tuple,
    )

    assert isinstance(
        evaluation.violations,
        tuple,
    )

    assert isinstance(
        evaluation.constraints,
        tuple,
    )

    assert isinstance(
        rule.condition,
        tuple,
    )

    assert isinstance(
        rule.metadata,
        tuple,
    )

    # ------------------------------------------------------------------------
    # Test 16: Policy semantic boundary
    # ------------------------------------------------------------------------

    assert (
        evaluation.decision_class
        == PolicyDecisionClass.ESCALATE
    )

    # This means "policy recommends an escalation class".
    # It does not mean an escalation was executed.

    metadata = evaluation.to_dict()

    assert (
        "decision_class"
        in metadata
    )

    assert (
        "violations"
        in metadata
    )

    assert (
        "constraints"
        in metadata
    )

    # ------------------------------------------------------------------------
    # Test 17: Dataclass guarantees
    # ------------------------------------------------------------------------

    assert dataclasses.is_dataclass(
        PolicyRule
    )

    assert dataclasses.is_dataclass(
        PolicyViolation
    )

    assert dataclasses.is_dataclass(
        PolicyConstraint
    )

    assert dataclasses.is_dataclass(
        PolicyRequest
    )

    assert dataclasses.is_dataclass(
        PolicyEvaluation
    )

    # ------------------------------------------------------------------------
    # Test 18: Domain isolation
    # ------------------------------------------------------------------------

    namespace = globals()

    forbidden_dependencies = (
        "DashboardAPI",
        "DashboardService",
        "DecisionOrchestrator",
        "Detector",
        "ModelManager",
        "TrainingService",
        "ResponseExecutor",
        "streamlit",
    )

    for dependency in forbidden_dependencies:

        assert (
            dependency
            not in namespace
        ), (
            "Policy contracts must not directly "
            f"depend on {dependency}."
        )

    # ------------------------------------------------------------------------
    # Test 19: Enum completeness
    # ------------------------------------------------------------------------

    assert (
        PolicyDecisionClass.NONE.value
        == "none"
    )

    assert (
        PolicyDecisionClass.MONITOR.value
        == "monitor"
    )

    assert (
        PolicyDecisionClass.ALERT.value
        == "alert"
    )

    assert (
        PolicyDecisionClass.ESCALATE.value
        == "escalate"
    )

    assert (
        PolicyDecisionClass.RESTRICT.value
        == "restrict"
    )

    # ------------------------------------------------------------------------
    # Test 20: Contract version
    # ------------------------------------------------------------------------

    assert (
        POLICY_CONTRACT_VERSION
        == "1.0.0"
    )

    assert (
        serialized_evaluation[
            "contract_version"
        ]
        == POLICY_CONTRACT_VERSION
    )

    return True


# ============================================================================
# Module execution
# ============================================================================


if __name__ == "__main__":

    print("=" * 70)

    print(
        "EnterpriseGuard - ADIE Policy Contracts Self-Test"
    )

    print("=" * 70)

    try:

        self_test()

        print(
            "[PASS] Policy status contract"
        )

        print(
            "[PASS] Policy decision classes"
        )

        print(
            "[PASS] Policy rule contract"
        )

        print(
            "[PASS] Policy violation contract"
        )

        print(
            "[PASS] Policy constraint contract"
        )

        print(
            "[PASS] Policy request contract"
        )

        print(
            "[PASS] Policy evaluation contract"
        )

        print(
            "[PASS] Policy validation"
        )

        print(
            "[PASS] Policy serialization"
        )

        print(
            "[PASS] Policy immutability"
        )

        print(
            "[PASS] Policy semantic boundary"
        )

        print(
            "[PASS] Policy domain isolation"
        )

        print(
            "[PASS] Contract versioning"
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

        raise SystemExit(
            1
        )

    except Exception as exc:

        print(
            "[FAIL] Unexpected error:"
        )

        print(
            exc
        )

        raise SystemExit(
            1
        )