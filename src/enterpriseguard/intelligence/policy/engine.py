"""
EnterpriseGuard - ADIE Policy Engine
====================================

Adaptive Defense Intelligence Engine (ADIE)

Policy Evaluation Layer
-----------------------

Architecture

    EnterpriseState
          |
          v
    PredictionResult
          |
          v
    PolicyEngine
          |
          +----> Rule evaluation
          |
          +----> Constraint evaluation
          |
          +----> Violation analysis
          |
          +----> Policy classification
          |
          v
    PolicyEvaluation
          |
          v
      Decision Layer


Purpose
-------

The PolicyEngine is the policy-domain execution boundary.

It evaluates enterprise security state and prediction information
against declarative policy contracts and produces a structured,
auditable policy evaluation.

The PolicyEngine does NOT execute security actions.


Strict architectural restrictions
---------------------------------

This module MUST NOT:

- execute security actions
- modify EnterpriseState
- mutate PredictionResult
- execute shell commands
- access filesystem
- perform network operations
- access Streamlit
- access DashboardAPI
- access DashboardService
- access ResponseEngine
- access ResponseExecutor
- access DecisionOrchestrator
- access training pipelines
- load or persist ML models
- depend on a concrete ML framework


Design principles
-----------------

- contract-driven
- deterministic
- immutable-input oriented
- explainable
- auditable
- policy-only
- framework-independent
- domain isolated
- future Decision-compatible
"""

from __future__ import annotations


# ============================================================================
# Standard library
# ============================================================================

import dataclasses

from dataclasses import (
    asdict,
    fields,
    is_dataclass,
)
from datetime import (
    datetime,
    timezone,
)
from enum import Enum
from math import isfinite
from time import perf_counter
from typing import (
    Any,
    Mapping,
    Sequence,
)


# ============================================================================
# Canonical policy contracts
# ============================================================================

from .contracts import (
    PolicyConstraint,
    PolicyConstraintType,
    PolicyDecisionClass,
    PolicyEvaluation,
    PolicyRequest,
    PolicyRule,
    PolicyRuleEffect,
    PolicyStatus,
    PolicyViolation,
    validate_policy_evaluation,
    validate_policy_request,
)


# ============================================================================
# Module metadata
# ============================================================================

ENGINE_NAME = "EnterpriseGuard ADIE Policy Engine"

ENGINE_VERSION = "1.0.1"

SCHEMA_VERSION = 1

DEFAULT_MAX_RULES = 100

MIN_MAX_RULES = 1

MAX_MAX_RULES = 1000

DEFAULT_MAX_CONSTRAINTS = 100

MIN_MAX_CONSTRAINTS = 1

MAX_MAX_CONSTRAINTS = 1000


# ============================================================================
# Exceptions
# ============================================================================


class PolicyEngineError(Exception):
    """Base exception for PolicyEngine."""


class PolicyInputError(PolicyEngineError):
    """Raised when policy input is invalid."""


class PolicyContractError(PolicyEngineError):
    """Raised when policy contracts cannot be constructed."""


# ============================================================================
# Basic utilities
# ============================================================================


def _utc_now() -> datetime:
    """Return timezone-aware current UTC time."""

    return datetime.now(
        timezone.utc
    )


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert to finite float."""

    try:
        result = float(value)

    except (TypeError, ValueError):
        return default

    if not isfinite(result):
        return default

    return result


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """Safely convert to integer."""

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _normalize_text(
    value: Any,
    default: str = "",
) -> str:
    """Normalize arbitrary value into text."""

    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def _normalize_probability(
    value: Any,
) -> float:
    """
    Normalize a score/probability into [0, 1].

    Values in [1, 100] are interpreted as percentages.
    """

    numeric = _safe_float(
        value,
        0.0,
    )

    if (
        numeric > 1.0
        and numeric <= 100.0
    ):
        numeric /= 100.0

    return max(
        0.0,
        min(
            1.0,
            numeric,
        ),
    )


def _enum_value(
    value: Any,
) -> Any:
    """Return the raw value for Enum members."""

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    return value


# ============================================================================
# Structural access helpers
# ============================================================================


def _get(
    source: Any,
    *keys: str,
    default: Any = None,
) -> Any:
    """
    Retrieve values without destroying dataclass object identity.

    Important:
    ---------

    Dataclass objects are accessed through their attributes FIRST.

    We do not call asdict() before accessing nested objects because
    that would recursively convert PolicyRule / PredictionResult /
    other domain contracts into ordinary dictionaries.
    """

    if source is None:
        return default

    # ------------------------------------------------------------------------
    # Direct attribute access first.
    # ------------------------------------------------------------------------

    for key in keys:

        if hasattr(
            source,
            key,
        ):

            try:

                return getattr(
                    source,
                    key,
                )

            except Exception:
                continue

    # ------------------------------------------------------------------------
    # Mapping access second.
    # ------------------------------------------------------------------------

    if isinstance(
        source,
        Mapping,
    ):

        for key in keys:

            if key in source:
                return source[key]

    # ------------------------------------------------------------------------
    # to_dict fallback.
    # ------------------------------------------------------------------------

    to_dict = getattr(
        source,
        "to_dict",
        None,
    )

    if callable(
        to_dict
    ):

        try:

            data = to_dict()

            if isinstance(
                data,
                Mapping,
            ):

                for key in keys:

                    if key in data:
                        return data[key]

        except Exception:
            pass

    return default


def _to_plain_dict(
    value: Any,
) -> dict[str, Any]:
    """
    Convert an object to a plain dictionary for presentation/diagnostics.

    This function is intentionally NOT used for internal domain
    contract traversal.
    """

    if isinstance(
        value,
        Mapping,
    ):

        return dict(
            value
        )

    to_dict = getattr(
        value,
        "to_dict",
        None,
    )

    if callable(
        to_dict
    ):

        try:

            result = to_dict()

            if isinstance(
                result,
                Mapping,
            ):
                return dict(
                    result
                )

        except Exception:
            pass

    if (
        is_dataclass(value)
        and not isinstance(
            value,
            type,
        )
    ):

        try:
            return dict(
                asdict(value)
            )
        except Exception:
            return {}

    return {}


def _sequence(
    value: Any,
) -> tuple[Any, ...]:
    """Normalize sequence-like values into an immutable tuple."""

    if value is None:
        return ()

    if isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
        ),
    ):
        return ()

    if isinstance(
        value,
        tuple,
    ):
        return value

    if isinstance(
        value,
        list,
    ):
        return tuple(
            value
        )

    try:
        return tuple(
            value
        )

    except TypeError:
        return ()


# ============================================================================
# Contract diagnostics
# ============================================================================


def _contract_fields(
    contract_type: type[Any],
) -> tuple[str, ...]:
    """Return declared dataclass field names."""

    try:

        return tuple(
            field.name
            for field in fields(
                contract_type
            )
        )

    except Exception:
        return ()


def contract_diagnostics() -> dict[str, Any]:
    """Return non-mutating diagnostics for policy contracts."""

    return {
        "policy_request": _contract_fields(
            PolicyRequest
        ),
        "policy_evaluation": _contract_fields(
            PolicyEvaluation
        ),
        "policy_rule": _contract_fields(
            PolicyRule
        ),
        "policy_violation": _contract_fields(
            PolicyViolation
        ),
        "policy_constraint": _contract_fields(
            PolicyConstraint
        ),
    }


# ============================================================================
# State extraction
# ============================================================================


def _extract_risk_score(
    state: Any,
) -> float:
    """Extract normalized risk score."""

    value = _get(
        state,
        "risk_score",
        "risk",
        "threat_score",
        "risk_probability",
        default=0.0,
    )

    if isinstance(
        value,
        Mapping,
    ):

        value = value.get(
            "score",
            value.get(
                "value",
                value.get(
                    "probability",
                    0.0,
                ),
            ),
        )

    return _normalize_probability(
        value
    )


def _extract_anomaly_score(
    state: Any,
) -> float:
    """Extract normalized anomaly score."""

    value = _get(
        state,
        "anomaly_score",
        "anomaly",
        "anomaly_probability",
        default=0.0,
    )

    if isinstance(
        value,
        Mapping,
    ):

        value = value.get(
            "score",
            value.get(
                "value",
                value.get(
                    "probability",
                    0.0,
                ),
            ),
        )

    return _normalize_probability(
        value
    )


def _extract_alert_count(
    state: Any,
) -> int:
    """Extract active alert count."""

    value = _get(
        state,
        "alert_count",
        "active_alerts",
        "alerts",
        default=0,
    )

    if isinstance(
        value,
        Sequence,
    ) and not isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
        ),
    ):

        return max(
            0,
            len(value),
        )

    return max(
        0,
        _safe_int(
            value,
            0,
        ),
    )


def _extract_security_posture(
    state: Any,
) -> str:
    """Extract normalized security posture."""

    value = _get(
        state,
        "security_posture",
        "posture",
        "security_status",
        default="unknown",
    )

    if isinstance(
        value,
        Mapping,
    ):

        value = value.get(
            "status",
            value.get(
                "value",
                "unknown",
            ),
        )

    return _normalize_text(
        value,
        "unknown",
    ).lower()


# ============================================================================
# Prediction extraction
# ============================================================================


def _extract_prediction_confidence(
    prediction: Any,
) -> float:
    """Extract primary prediction confidence."""

    if prediction is None:
        return 0.0

    direct = _get(
        prediction,
        "confidence",
        default=None,
    )

    if direct is not None:
        return _normalize_probability(
            direct
        )

    candidates = _sequence(
        _get(
            prediction,
            "candidates",
            "predictions",
            default=(),
        )
    )

    probabilities: list[float] = []

    for candidate in candidates:

        probability = _get(
            candidate,
            "probability",
            default=0.0,
        )

        probabilities.append(
            _normalize_probability(
                probability
            )
        )

    return max(
        probabilities,
        default=0.0,
    )


def _extract_prediction_value(
    prediction: Any,
) -> str:
    """Extract primary predicted value."""

    if prediction is None:
        return "unknown"

    direct = _get(
        prediction,
        "predicted_value",
        default=None,
    )

    if direct is not None:

        return _normalize_text(
            _enum_value(direct),
            "unknown",
        ).lower()

    top_candidate = _get(
        prediction,
        "top_candidate",
        default=None,
    )

    if top_candidate is not None:

        return _normalize_text(
            _enum_value(
                _get(
                    top_candidate,
                    "value",
                    default="unknown",
                )
            ),
            "unknown",
        ).lower()

    candidates = _sequence(
        _get(
            prediction,
            "candidates",
            "predictions",
            default=(),
        )
    )

    if candidates:

        return _normalize_text(
            _enum_value(
                _get(
                    candidates[0],
                    "value",
                    default="unknown",
                )
            ),
            "unknown",
        ).lower()

    return "unknown"


# ============================================================================
# PolicyEngine
# ============================================================================


class PolicyEngine:
    """
    ADIE Policy Evaluation Engine.

    The engine evaluates policy against state and prediction data.

    It never executes the resulting decision.
    """

    def __init__(
        self,
        *,
        engine_name: str = ENGINE_NAME,
        engine_version: str = ENGINE_VERSION,
        max_rules: int = DEFAULT_MAX_RULES,
        max_constraints: int = DEFAULT_MAX_CONSTRAINTS,
    ) -> None:

        self._engine_name = _normalize_text(
            engine_name,
            ENGINE_NAME,
        )

        self._engine_version = _normalize_text(
            engine_version,
            ENGINE_VERSION,
        )

        self._max_rules = (
            self._validate_limit(
                max_rules,
                "max_rules",
                MIN_MAX_RULES,
                MAX_MAX_RULES,
            )
        )

        self._max_constraints = (
            self._validate_limit(
                max_constraints,
                "max_constraints",
                MIN_MAX_CONSTRAINTS,
                MAX_MAX_CONSTRAINTS,
            )
        )

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def engine_name(self) -> str:
        """Return engine name."""

        return self._engine_name

    @property
    def engine_version(self) -> str:
        """Return engine version."""

        return self._engine_version

    @property
    def max_rules(self) -> int:
        """Return rule limit."""

        return self._max_rules

    @property
    def max_constraints(self) -> int:
        """Return constraint limit."""

        return self._max_constraints

    # ========================================================================
    # Metadata
    # ========================================================================

    def metadata(self) -> dict[str, Any]:
        """Return immutable engine metadata snapshot."""

        return {
            "engine": self._engine_name,
            "version": self._engine_version,
            "schema_version": SCHEMA_VERSION,
            "deterministic": True,
            "max_rules": self._max_rules,
            "max_constraints": self._max_constraints,
            "executes_security_actions": False,
            "modifies_security_state": False,
            "filesystem_access": False,
            "network_operations": False,
            "shell_execution": False,
            "ml_framework_dependency": False,
        }

    # ========================================================================
    # Public API
    # ========================================================================

    def create_request(
        self,
        state: Any,
        *,
        prediction: Any | None = None,
        rules: Sequence[PolicyRule] | None = None,
        constraints: Sequence[PolicyConstraint] | None = None,
        state_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> PolicyRequest:
        """
        Construct the project's canonical PolicyRequest.

        The current contract accepts:

            state_id
            prediction
            rules
            requested_at
            context
            source

        The full state is therefore carried by context.
        """

        if state is None:
            raise PolicyInputError(
                "state must not be None."
            )

        # --------------------------------------------------------------------
        # State ID
        # --------------------------------------------------------------------

        resolved_state_id = (
            state_id
            if state_id is not None
            else _get(
                state,
                "state_id",
                "id",
                "snapshot_id",
                default="state-current",
            )
        )

        resolved_state_id = _normalize_text(
            resolved_state_id,
            "state-current",
        )

        # --------------------------------------------------------------------
        # Rules
        # --------------------------------------------------------------------

        if rules is None:

            normalized_rules = (
                self._default_rules()
            )

        else:

            normalized_rules = tuple(
                rules
            )

        for rule in normalized_rules:

            if not isinstance(
                rule,
                PolicyRule,
            ):
                raise PolicyInputError(
                    "rules must contain PolicyRule instances."
                )

        if len(
            normalized_rules
        ) > self._max_rules:

            raise PolicyInputError(
                "rules exceed configured maximum."
            )

        # --------------------------------------------------------------------
        # Constraints
        # --------------------------------------------------------------------

        if constraints is None:

            normalized_constraints = ()

        else:

            normalized_constraints = tuple(
                constraints
            )

        for constraint in normalized_constraints:

            if not isinstance(
                constraint,
                PolicyConstraint,
            ):
                raise PolicyInputError(
                    "constraints must contain PolicyConstraint instances."
                )

        if len(
            normalized_constraints
        ) > self._max_constraints:

            raise PolicyInputError(
                "constraints exceed configured maximum."
            )

        # --------------------------------------------------------------------
        # Context
        # --------------------------------------------------------------------

        context_data = (
            dict(context)
            if context is not None
            else {}
        )

        if (
            "enterprise_state"
            in context_data
        ):
            raise PolicyInputError(
                "context must not override enterprise_state."
            )

        context_data[
            "enterprise_state"
        ] = state

        if normalized_constraints:

            context_data[
                "policy_constraints"
            ] = normalized_constraints

        # --------------------------------------------------------------------
        # Prediction
        # --------------------------------------------------------------------

        resolved_prediction = (
            prediction
            if prediction is not None
            else self._default_prediction()
        )

        # --------------------------------------------------------------------
        # Canonical request
        # --------------------------------------------------------------------

        try:

            request = PolicyRequest(
                state_id=resolved_state_id,
                prediction=resolved_prediction,
                rules=normalized_rules,
                requested_at=_utc_now(),
                context=tuple(
                    context_data.items()
                ),
                source="enterpriseguard",
            )

        except Exception as exc:

            raise PolicyContractError(
                "Unable to construct canonical PolicyRequest."
            ) from exc

        validate_policy_request(
            request
        )

        return request

    def evaluate(
        self,
        request: PolicyRequest,
    ) -> PolicyEvaluation:
        """
        Evaluate a canonical PolicyRequest.
        """

        started = perf_counter()

        self._validate_request(
            request
        )

        state = self._state_from_request(
            request
        )

        prediction = request.prediction

        rules = request.rules

        constraints = self._constraints_from_request(
            request
        )

        applicable_rules = tuple(
            rule
            for rule in rules
            if self._rule_applies(
                rule,
                state,
                prediction,
            )
        )

        violations = self._evaluate(
            state=state,
            prediction=prediction,
            rules=applicable_rules,
            constraints=constraints,
        )

        decision_class = self._classify(
            violations
        )

        policy_score = (
            self._calculate_policy_score(
                state=state,
                prediction=prediction,
                violations=violations,
            )
        )

        latency_ms = (
            perf_counter()
            - started
        ) * 1000.0

        evaluation = self._build_evaluation(
            request=request,
            decision_class=decision_class,
            policy_score=policy_score,
            applicable_rules=applicable_rules,
            violations=violations,
            constraints=constraints,
            latency_ms=latency_ms,
        )

        validate_policy_evaluation(
            evaluation
        )

        return evaluation

    def evaluate_state(
        self,
        state: Any,
        *,
        prediction: Any | None = None,
        rules: Sequence[PolicyRule] | None = None,
        constraints: Sequence[PolicyConstraint] | None = None,
        state_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> PolicyEvaluation:
        """
        Evaluate state directly through the canonical request boundary.
        """

        request = self.create_request(
            state,
            prediction=prediction,
            rules=rules,
            constraints=constraints,
            state_id=state_id,
            context=context,
        )

        return self.evaluate(
            request
        )

    # ========================================================================
    # Validation
    # ========================================================================

    @staticmethod
    def _validate_limit(
        value: Any,
        field_name: str,
        minimum: int,
        maximum: int,
    ) -> int:
        """Validate engine numeric limits."""

        if isinstance(
            value,
            bool,
        ):
            raise PolicyInputError(
                f"{field_name} must be an integer."
            )

        if not isinstance(
            value,
            int,
        ):
            raise PolicyInputError(
                f"{field_name} must be an integer."
            )

        if not (
            minimum
            <= value
            <= maximum
        ):
            raise PolicyInputError(
                f"{field_name} must be between "
                f"{minimum} and {maximum}."
            )

        return value

    def _validate_request(
        self,
        request: PolicyRequest,
    ) -> None:
        """Validate canonical PolicyRequest."""

        if request is None:
            raise PolicyInputError(
                "PolicyRequest must not be None."
            )

        if not isinstance(
            request,
            PolicyRequest,
        ):
            raise PolicyInputError(
                "request must be a PolicyRequest."
            )

        validate_policy_request(
            request
        )

        rules = request.rules

        for rule in rules:

            if not isinstance(
                rule,
                PolicyRule,
            ):
                raise PolicyInputError(
                    "PolicyRequest contains a non-PolicyRule object."
                )

        state = self._state_from_request(
            request
        )

        if state is None:
            raise PolicyInputError(
                "PolicyRequest context does not contain enterprise_state."
            )

    # ========================================================================
    # Request extraction
    # ========================================================================

    @staticmethod
    def _state_from_request(
        request: PolicyRequest,
    ) -> Any | None:
        """
        Extract EnterpriseState from request.context.

        The current contracts intentionally keep the concrete state
        implementation outside the PolicyRequest public fields.
        """

        context = request.context

        try:

            return dict(
                context
            ).get(
                "enterprise_state"
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _constraints_from_request(
        request: PolicyRequest,
    ) -> tuple[PolicyConstraint, ...]:
        """Extract constraints from request context."""

        context = request.context

        try:

            data = dict(
                context
            )

        except (
            TypeError,
            ValueError,
        ):

            return ()

        raw = data.get(
            "policy_constraints",
            (),
        )

        constraints = _sequence(
            raw
        )

        for constraint in constraints:

            if not isinstance(
                constraint,
                PolicyConstraint,
            ):
                raise PolicyInputError(
                    "PolicyRequest contains invalid policy constraint."
                )

        return tuple(
            constraints
        )

    # ========================================================================
    # Rule applicability
    # ========================================================================

    def _rule_applies(
        self,
        rule: PolicyRule,
        state: Any,
        prediction: Any,
    ) -> bool:
        """
        Determine whether a rule is applicable.

        Rules without conditions apply by default.
        """

        if not rule.enabled:
            return False

        condition = dict(
            rule.condition
        )

        if not condition:
            return True

        field_name = _normalize_text(
            condition.get(
                "field",
                "risk_score",
            ),
            "risk_score",
        )

        operator = _normalize_text(
            condition.get(
                "operator",
                ">=",
            ),
            ">=",
        )

        threshold = condition.get(
            "threshold",
            condition.get(
                "value",
                0.70,
            ),
        )

        observed = self._resolve_signal(
            state=state,
            prediction=prediction,
            field_name=field_name,
        )

        return self._compare(
            observed,
            operator,
            threshold,
        )

    # ========================================================================
    # Main policy evaluation
    # ========================================================================

    def _evaluate(
        self,
        *,
        state: Any,
        prediction: Any,
        rules: Sequence[PolicyRule],
        constraints: Sequence[PolicyConstraint],
    ) -> tuple[PolicyViolation, ...]:
        """Evaluate baseline policy, rules, and constraints."""

        violations: list[
            PolicyViolation
        ] = []

        risk = _extract_risk_score(
            state
        )

        anomaly = _extract_anomaly_score(
            state
        )

        alerts = _extract_alert_count(
            state
        )

        confidence = (
            _extract_prediction_confidence(
                prediction
            )
        )

        prediction_value = (
            _extract_prediction_value(
                prediction
            )
        )

        # --------------------------------------------------------------------
        # Baseline risk
        # --------------------------------------------------------------------

        if risk >= 0.70:

            violation = self._make_violation(
                rule_id="baseline-risk-threshold",
                code="RISK_THRESHOLD",
                message=(
                    "Enterprise risk meets or exceeds the baseline "
                    "policy threshold."
                ),
                severity=self._score_severity(
                    risk
                ),
                evidence={
                    "risk_score": risk,
                    "threshold": 0.70,
                },
            )

            if violation is not None:
                violations.append(
                    violation
                )

        # --------------------------------------------------------------------
        # Baseline anomaly
        # --------------------------------------------------------------------

        if anomaly >= 0.75:

            violation = self._make_violation(
                rule_id="baseline-anomaly-threshold",
                code="ANOMALY_THRESHOLD",
                message=(
                    "Anomaly score meets or exceeds the baseline "
                    "policy threshold."
                ),
                severity=self._score_severity(
                    anomaly
                ),
                evidence={
                    "anomaly_score": anomaly,
                    "threshold": 0.75,
                },
            )

            if violation is not None:
                violations.append(
                    violation
                )

        # --------------------------------------------------------------------
        # Baseline alerts
        # --------------------------------------------------------------------

        if alerts > 5:

            violation = self._make_violation(
                rule_id="baseline-alert-threshold",
                code="ALERT_VOLUME_THRESHOLD",
                message=(
                    "Active alert volume exceeds the baseline "
                    "policy threshold."
                ),
                severity=self._count_severity(
                    alerts
                ),
                evidence={
                    "alert_count": alerts,
                    "threshold": 5,
                },
            )

            if violation is not None:
                violations.append(
                    violation
                )

        # --------------------------------------------------------------------
        # Prediction signal
        # --------------------------------------------------------------------

        if (
            confidence >= 0.50
            and self._prediction_is_elevating(
                prediction_value
            )
        ):

            violation = self._make_violation(
                rule_id="prediction-security-elevation",
                code="PREDICTED_SECURITY_ELEVATION",
                message=(
                    "Prediction indicates a sufficiently confident "
                    "future elevation in security pressure."
                ),
                severity="high",
                evidence={
                    "prediction_value": prediction_value,
                    "confidence": confidence,
                },
            )

            if violation is not None:
                violations.append(
                    violation
                )

        # --------------------------------------------------------------------
        # Explicit rules
        # --------------------------------------------------------------------

        for rule in rules:

            violation = self._rule_violation(
                rule
            )

            if violation is not None:
                violations.append(
                    violation
                )

        # --------------------------------------------------------------------
        # Explicit constraints
        # --------------------------------------------------------------------

        for constraint in constraints:

            if constraint.satisfied:
                continue

            violation = (
                self._constraint_violation(
                    constraint
                )
            )

            if violation is not None:
                violations.append(
                    violation
                )

        return tuple(
            violations
        )

    # ========================================================================
    # Signal resolution
    # ========================================================================

    def _resolve_signal(
        self,
        *,
        state: Any,
        prediction: Any,
        field_name: str,
    ) -> Any:
        """Resolve a policy signal."""

        normalized = (
            field_name.strip().lower()
        )

        aliases = {
            "risk": "risk_score",
            "risk_probability": "risk_score",
            "anomaly": "anomaly_score",
            "alerts": "alert_count",
            "active_alerts": "alert_count",
            "posture": "security_posture",
            "prediction": "prediction_value",
            "prediction_probability": "prediction_confidence",
        }

        normalized = aliases.get(
            normalized,
            normalized,
        )

        if normalized == "risk_score":

            return _extract_risk_score(
                state
            )

        if normalized == "anomaly_score":

            return _extract_anomaly_score(
                state
            )

        if normalized == "alert_count":

            return _extract_alert_count(
                state
            )

        if normalized == "security_posture":

            return _extract_security_posture(
                state
            )

        if normalized == "prediction_confidence":

            return _extract_prediction_confidence(
                prediction
            )

        if normalized == "prediction_value":

            return _extract_prediction_value(
                prediction
            )

        value = _get(
            state,
            normalized,
            default=None,
        )

        if value is not None:
            return value

        return _get(
            prediction,
            normalized,
            default=None,
        )

    # ========================================================================
    # Comparison
    # ========================================================================

    @staticmethod
    def _compare(
        observed: Any,
        operator: str,
        expected: Any,
    ) -> bool:
        """Perform deterministic policy comparison."""

        operator = operator.strip().lower()

        observed_number = _safe_float(
            observed,
            float("nan"),
        )

        expected_number = _safe_float(
            expected,
            float("nan"),
        )

        numeric = (
            isfinite(
                observed_number
            )
            and isfinite(
                expected_number
            )
        )

        if numeric:

            if operator == ">":
                return (
                    observed_number
                    > expected_number
                )

            if operator == ">=":
                return (
                    observed_number
                    >= expected_number
                )

            if operator == "<":
                return (
                    observed_number
                    < expected_number
                )

            if operator == "<=":
                return (
                    observed_number
                    <= expected_number
                )

            if operator == "==":
                return (
                    observed_number
                    == expected_number
                )

            if operator == "!=":
                return (
                    observed_number
                    != expected_number
                )

        observed_text = _normalize_text(
            _enum_value(
                observed
            )
        ).lower()

        expected_text = _normalize_text(
            _enum_value(
                expected
            )
        ).lower()

        if operator in {
            "equals",
            "equal",
        }:

            return (
                observed_text
                == expected_text
            )

        if operator in {
            "not_equals",
            "not_equal",
        }:

            return (
                observed_text
                != expected_text
            )

        if operator == "contains":

            return (
                expected_text
                in observed_text
            )

        return False

    # ========================================================================
    # Violation builders
    # ========================================================================

    @staticmethod
    def _make_violation(
        *,
        rule_id: str,
        code: str,
        message: str,
        severity: str,
        evidence: Mapping[str, Any],
    ) -> PolicyViolation | None:
        """Construct canonical PolicyViolation."""

        try:

            return PolicyViolation(
                rule_id=rule_id,
                code=code,
                message=message,
                severity=severity,
                evidence=tuple(
                    evidence.items()
                ),
                timestamp=_utc_now(),
            )

        except Exception:

            return None

    def _rule_violation(
        self,
        rule: PolicyRule,
    ) -> PolicyViolation | None:
        """Create violation for an applicable rule."""

        description = (
            rule.description
            if rule.description
            else (
                f"Policy rule '{rule.name}' matched."
            )
        )

        metadata = dict(
            rule.metadata
        )

        severity = _normalize_text(
            metadata.get(
                "severity",
                "medium",
            ),
            "medium",
        )

        code = (
            "RULE_"
            + rule.rule_id.upper().replace(
                "-",
                "_",
            )
        )

        return self._make_violation(
            rule_id=rule.rule_id,
            code=code,
            message=description,
            severity=severity,
            evidence={
                "effect": rule.effect.value,
                "priority": rule.priority,
                "condition": dict(
                    rule.condition
                ),
            },
        )

    def _constraint_violation(
        self,
        constraint: PolicyConstraint,
    ) -> PolicyViolation | None:
        """Create violation for an unsatisfied constraint."""

        code = (
            "CONSTRAINT_"
            + constraint.constraint_id.upper().replace(
                "-",
                "_",
            )
        )

        return self._make_violation(
            rule_id=constraint.constraint_id,
            code=code,
            message=constraint.description,
            severity="high",
            evidence={
                "constraint_type": (
                    constraint.constraint_type.value
                ),
                "source": constraint.source,
            },
        )

    # ========================================================================
    # Policy score
    # ========================================================================

    @staticmethod
    def _calculate_policy_score(
        *,
        state: Any,
        prediction: Any,
        violations: Sequence[PolicyViolation],
    ) -> float:
        """
        Calculate a normalized policy-pressure score.

        This is an evaluation metric, not action authorization.
        """

        risk = _extract_risk_score(
            state
        )

        anomaly = _extract_anomaly_score(
            state
        )

        confidence = (
            _extract_prediction_confidence(
                prediction
            )
        )

        violation_pressure = min(
            1.0,
            len(
                violations
            ) / 5.0,
        )

        score = (
            risk * 0.35
            + anomaly * 0.20
            + confidence * 0.20
            + violation_pressure * 0.25
        )

        return max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

    # ========================================================================
    # Classification
    # ========================================================================

    @staticmethod
    def _classify(
        violations: Sequence[
            PolicyViolation
        ],
    ) -> PolicyDecisionClass:
        """
        Classify evaluation result.

        Classification does not execute an action.
        """

        if not violations:

            return (
                PolicyDecisionClass.NONE
            )

        severities = {
            _normalize_text(
                violation.severity,
                "medium",
            ).lower()
            for violation
            in violations
        }

        if "critical" in severities:

            return (
                PolicyDecisionClass.RESTRICT
            )

        if "high" in severities:

            return (
                PolicyDecisionClass.ESCALATE
            )

        return (
            PolicyDecisionClass.ALERT
        )

    # ========================================================================
    # Evaluation construction
    # ========================================================================

    def _build_evaluation(
        self,
        *,
        request: PolicyRequest,
        decision_class: PolicyDecisionClass,
        policy_score: float,
        applicable_rules: Sequence[PolicyRule],
        violations: Sequence[PolicyViolation],
        constraints: Sequence[PolicyConstraint],
        latency_ms: float,
    ) -> PolicyEvaluation:
        """Construct canonical PolicyEvaluation."""

        evaluation_id = (
            "policy-"
            f"{int(_utc_now().timestamp() * 1_000_000)}"
        )

        rationale = self._rationale(
            decision_class=decision_class,
            policy_score=policy_score,
            violation_count=len(
                violations
            ),
        )

        metadata = {
            "engine": self._engine_name,
            "engine_version": self._engine_version,
            "schema_version": SCHEMA_VERSION,
            "processing_time_ms": round(
                max(
                    0.0,
                    latency_ms,
                ),
                3,
            ),
            "applicable_rule_count": len(
                applicable_rules
            ),
            "violation_count": len(
                violations
            ),
            "constraint_count": len(
                constraints
            ),
            "executes_security_actions": False,
            "modifies_security_state": False,
        }

        try:

            return PolicyEvaluation(
                request=request,
                status=PolicyStatus.EVALUATED,
                decision_class=decision_class,
                policy_score=policy_score,
                applicable_rules=tuple(
                    applicable_rules
                ),
                violations=tuple(
                    violations
                ),
                constraints=tuple(
                    constraints
                ),
                rationale=rationale,
                evaluated_at=_utc_now(),
                evaluator_version=self._engine_version,
                evaluation_id=evaluation_id,
                metadata=tuple(
                    metadata.items()
                ),
            )

        except Exception as exc:

            raise PolicyContractError(
                "Unable to construct PolicyEvaluation."
            ) from exc

    @staticmethod
    def _rationale(
        *,
        decision_class: PolicyDecisionClass,
        policy_score: float,
        violation_count: int,
    ) -> str:
        """Build deterministic evaluation rationale."""

        decision = (
            decision_class.value
        )

        if violation_count == 0:

            return (
                "No policy violations were identified. "
                f"Policy score={policy_score:.3f}; "
                f"classification={decision}."
            )

        return (
            f"{violation_count} policy violation(s) identified. "
            f"Policy score={policy_score:.3f}; "
            f"classification={decision}."
        )

    # ========================================================================
    # Defaults
    # ========================================================================

    @staticmethod
    def _default_prediction() -> dict[str, Any]:
        """Return a neutral prediction representation."""

        return {
            "predicted_value": "unknown",
            "confidence": 0.0,
            "candidates": (),
        }

    @staticmethod
    def _default_rules() -> tuple[PolicyRule, ...]:
        """Return baseline declarative policy rules."""

        return (
            PolicyRule(
                rule_id="baseline-risk-review",
                name="Baseline Risk Review",
                effect=PolicyRuleEffect.REQUIRE_REVIEW,
                priority=10,
                enabled=True,
                condition={
                    "field": "risk_score",
                    "operator": ">=",
                    "threshold": 0.70,
                },
                description=(
                    "Risk reaches the baseline policy review threshold."
                ),
                metadata={
                    "severity": "high",
                    "source": "baseline",
                },
            ),
            PolicyRule(
                rule_id="baseline-anomaly-review",
                name="Baseline Anomaly Review",
                effect=PolicyRuleEffect.REQUIRE_REVIEW,
                priority=20,
                enabled=True,
                condition={
                    "field": "anomaly_score",
                    "operator": ">=",
                    "threshold": 0.75,
                },
                description=(
                    "Anomaly score reaches the baseline policy review threshold."
                ),
                metadata={
                    "severity": "high",
                    "source": "baseline",
                },
            ),
        )

    # ========================================================================
    # Severity
    # ========================================================================

    @staticmethod
    def _score_severity(
        score: float,
    ) -> str:
        """Map score to severity."""

        if score >= 0.90:
            return "critical"

        if score >= 0.75:
            return "high"

        if score >= 0.50:
            return "medium"

        return "low"

    @staticmethod
    def _count_severity(
        count: int,
    ) -> str:
        """Map alert count to severity."""

        if count >= 20:
            return "critical"

        if count >= 10:
            return "high"

        if count >= 6:
            return "medium"

        return "low"

    @staticmethod
    def _prediction_is_elevating(
        value: str,
    ) -> bool:
        """Return whether a prediction indicates elevated risk."""

        normalized = value.strip().lower()

        indicators = (
            "threat",
            "attack",
            "intrusion",
            "escalation",
            "malicious",
            "compromise",
            "elevated",
            "suspicious",
            "danger",
            "continued",
        )

        return any(
            indicator in normalized
            for indicator in indicators
        )


# ============================================================================
# Module-level convenience API
# ============================================================================


def evaluate_policy(
    request: PolicyRequest,
) -> PolicyEvaluation:
    """Evaluate a PolicyRequest using a fresh engine."""

    return PolicyEngine().evaluate(
        request
    )


def evaluate_state(
    state: Any,
    *,
    prediction: Any | None = None,
    rules: Sequence[PolicyRule] | None = None,
    constraints: Sequence[PolicyConstraint] | None = None,
    state_id: str | None = None,
    context: Mapping[str, Any] | None = None,
) -> PolicyEvaluation:
    """Evaluate state using a fresh PolicyEngine."""

    return PolicyEngine().evaluate_state(
        state,
        prediction=prediction,
        rules=rules,
        constraints=constraints,
        state_id=state_id,
        context=context,
    )


# ============================================================================
# Self-test fixtures
# ============================================================================


def _build_test_state() -> dict[str, Any]:
    """Create deterministic test state."""

    return {
        "state_id": "state-policy-self-test-001",
        "risk_score": 0.82,
        "anomaly_score": 0.45,
        "alert_count": 3,
        "security_posture": "elevated",
    }


def _build_test_prediction() -> dict[str, Any]:
    """Create deterministic test prediction."""

    return {
        "predicted_value": (
            "continued_threat_activity"
        ),
        "confidence": 0.78,
        "candidates": (
            {
                "value": "continued_threat_activity",
                "probability": 0.78,
            },
            {
                "value": "security_state_stabilization",
                "probability": 0.22,
            },
        ),
    }


# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Comprehensive isolated PolicyEngine self-test.
    """

    # ========================================================================
    # 1. Initialization
    # ========================================================================

    engine = PolicyEngine()

    assert isinstance(
        engine,
        PolicyEngine,
    )

    print(
        "[PASS] Engine initialization"
    )

    # ========================================================================
    # 2. Metadata
    # ========================================================================

    metadata = engine.metadata()

    assert (
        metadata["engine"]
        == ENGINE_NAME
    )

    assert (
        metadata["version"]
        == ENGINE_VERSION
    )

    assert (
        metadata["deterministic"]
        is True
    )

    assert (
        metadata["executes_security_actions"]
        is False
    )

    print(
        "[PASS] Engine metadata contract"
    )

    # ========================================================================
    # 3. Contract diagnostics
    # ========================================================================

    diagnostics = (
        contract_diagnostics()
    )

    assert (
        "policy_request"
        in diagnostics
    )

    assert (
        "policy_evaluation"
        in diagnostics
    )

    assert (
        "state_id"
        in diagnostics[
            "policy_request"
        ]
    )

    assert (
        "prediction"
        in diagnostics[
            "policy_request"
        ]
    )

    assert (
        "rules"
        in diagnostics[
            "policy_request"
        ]
    )

    print(
        "[PASS] Contract diagnostics"
    )

    # ========================================================================
    # 4. Test fixtures
    # ========================================================================

    state = _build_test_state()

    prediction = _build_test_prediction()

    assert (
        state["risk_score"]
        == 0.82
    )

    assert (
        prediction["confidence"]
        == 0.78
    )

    print(
        "[PASS] Test fixtures"
    )

    # ========================================================================
    # 5. Request construction
    # ========================================================================

    request = engine.create_request(
        state,
        prediction=prediction,
    )

    assert isinstance(
        request,
        PolicyRequest,
    )

    assert (
        request.state_id
        == state["state_id"]
    )

    assert all(
        isinstance(
            rule,
            PolicyRule,
        )
        for rule in request.rules
    )

    context = dict(
        request.context
    )

    assert (
        context[
            "enterprise_state"
        ]
        is state
    )

    print(
        "[PASS] Policy request construction"
    )

    # ========================================================================
    # 6. Request validation
    # ========================================================================

    engine._validate_request(
        request
    )

    print(
        "[PASS] Policy request validation"
    )

    # ========================================================================
    # 7. Evaluation
    # ========================================================================

    evaluation = engine.evaluate(
        request
    )

    assert isinstance(
        evaluation,
        PolicyEvaluation,
    )

    print(
        "[PASS] Policy evaluation"
    )

    # ========================================================================
    # 8. Evaluation validation
    # ========================================================================

    validate_policy_evaluation(
        evaluation
    )

    print(
        "[PASS] Evaluation contract validation"
    )

    # ========================================================================
    # 9. Violations
    # ========================================================================

    assert (
        len(
            evaluation.violations
        )
        >= 1
    )

    print(
        "[PASS] Policy violation analysis"
    )

    # ========================================================================
    # 10. Classification
    # ========================================================================

    assert isinstance(
        evaluation.decision_class,
        PolicyDecisionClass,
    )

    assert (
        evaluation.decision_class
        in {
            PolicyDecisionClass.ALERT,
            PolicyDecisionClass.ESCALATE,
            PolicyDecisionClass.RESTRICT,
        }
    )

    print(
        "[PASS] Policy classification"
    )

    # ========================================================================
    # 11. Score
    # ========================================================================

    assert (
        0.0
        <= evaluation.policy_score
        <= 1.0
    )

    print(
        "[PASS] Policy score"
    )

    # ========================================================================
    # 12. Rationale
    # ========================================================================

    assert (
        isinstance(
            evaluation.rationale,
            str,
        )
        and evaluation.rationale
    )

    print(
        "[PASS] Policy rationale"
    )

    # ========================================================================
    # 13. Serialization
    # ========================================================================

    serialized = (
        evaluation.to_dict()
    )

    assert isinstance(
        serialized,
        dict,
    )

    assert (
        serialized["status"]
        == "evaluated"
    )

    assert (
        "decision_class"
        in serialized
    )

    assert (
        "policy_score"
        in serialized
    )

    assert (
        "violations"
        in serialized
    )

    print(
        "[PASS] Policy serialization"
    )

    # ========================================================================
    # 14. Convenience API
    # ========================================================================

    convenience = (
        engine.evaluate_state(
            state,
            prediction=prediction,
        )
    )

    assert isinstance(
        convenience,
        PolicyEvaluation,
    )

    print(
        "[PASS] Convenience policy API"
    )

    # ========================================================================
    # 15. Safe state
    # ========================================================================

    safe_state = {
        "state_id": "state-safe-001",
        "risk_score": 0.10,
        "anomaly_score": 0.05,
        "alert_count": 0,
        "security_posture": "healthy",
    }

    safe_evaluation = (
        engine.evaluate_state(
            safe_state
        )
    )

    assert (
        len(
            safe_evaluation.violations
        )
        == 0
    )

    assert (
        safe_evaluation.decision_class
        == PolicyDecisionClass.NONE
    )

    print(
        "[PASS] Policy-compliant state"
    )

    # ========================================================================
    # 16. Custom rule
    # ========================================================================

    custom_rule = PolicyRule(
        rule_id="CUSTOM-001",
        name="Custom Risk Escalation",
        effect=PolicyRuleEffect.ESCALATE,
        priority=1,
        enabled=True,
        condition={
            "field": "risk_score",
            "operator": ">=",
            "threshold": 0.80,
        },
        description=(
            "Custom rule triggered by elevated risk."
        ),
        metadata={
            "severity": "high",
        },
    )

    custom_evaluation = (
        engine.evaluate_state(
            state,
            prediction=prediction,
            rules=(
                custom_rule,
            ),
        )
    )

    custom_rule_ids = {
        item.rule_id
        for item
        in custom_evaluation.violations
    }

    assert (
        "CUSTOM-001"
        in custom_rule_ids
    )

    print(
        "[PASS] Custom policy rule"
    )

    # ========================================================================
    # 17. Constraint
    # ========================================================================

    constraint = PolicyConstraint(
        constraint_id="CONSTRAINT-001",
        constraint_type=(
            PolicyConstraintType.CONFIDENCE
        ),
        description=(
            "Prediction confidence must satisfy policy requirements."
        ),
        satisfied=False,
        source="self-test",
    )

    constraint_evaluation = (
        engine.evaluate_state(
            state,
            prediction=prediction,
            constraints=(
                constraint,
            ),
        )
    )

    constraint_ids = {
        item.rule_id
        for item
        in constraint_evaluation.violations
    }

    assert (
        "CONSTRAINT-001"
        in constraint_ids
    )

    print(
        "[PASS] Policy constraint evaluation"
    )

    # ========================================================================
    # 18. Invalid request
    # ========================================================================

    invalid_request_failed = False

    try:

        engine.evaluate(
            None
        )

    except PolicyInputError:

        invalid_request_failed = True

    assert (
        invalid_request_failed
        is True
    )

    print(
        "[PASS] Invalid request rejection"
    )

    # ========================================================================
    # 19. Invalid rules
    # ========================================================================

    invalid_rule_failed = False

    try:

        engine.create_request(
            state,
            prediction=prediction,
            rules=(
                "not-a-policy-rule",
            ),
        )

    except PolicyInputError:

        invalid_rule_failed = True

    assert (
        invalid_rule_failed
        is True
    )

    print(
        "[PASS] Rule type validation"
    )

    # ========================================================================
    # 20. State immutability
    # ========================================================================

    original_state = dict(
        state
    )

    engine.evaluate_state(
        state,
        prediction=prediction,
    )

    assert (
        state
        == original_state
    )

    print(
        "[PASS] State immutability"
    )

    # ========================================================================
    # 21. Prediction immutability
    # ========================================================================

    original_prediction = dict(
        prediction
    )

    engine.evaluate_state(
        state,
        prediction=prediction,
    )

    assert (
        prediction
        == original_prediction
    )

    print(
        "[PASS] Prediction immutability"
    )

    # ========================================================================
    # 22. Evaluation metadata
    # ========================================================================

    assert (
        serialized[
            "evaluator_version"
        ]
        == ENGINE_VERSION
    )

    assert (
        serialized[
            "evaluation_id"
        ]
    )

    assert (
        serialized[
            "contract_version"
        ]
    )

    print(
        "[PASS] Evaluation metadata"
    )

    # ========================================================================
    # 23. Safety boundary
    # ========================================================================

    assert (
        metadata[
            "executes_security_actions"
        ]
        is False
    )

    assert (
        metadata[
            "modifies_security_state"
        ]
        is False
    )

    assert (
        metadata[
            "filesystem_access"
        ]
        is False
    )

    assert (
        metadata[
            "network_operations"
        ]
        is False
    )

    assert (
        metadata[
            "shell_execution"
        ]
        is False
    )

    print(
        "[PASS] Policy safety boundary"
    )

    # ========================================================================
    # 24. Domain isolation
    # ========================================================================

    namespace = globals()

    forbidden_dependencies = (
        "DashboardAPI",
        "DashboardService",
        "DecisionOrchestrator",
        "ResponseEngine",
        "ResponseExecutor",
        "ModelManager",
        "Detector",
        "TrainingService",
        "streamlit",
    )

    for dependency in forbidden_dependencies:

        assert (
            dependency
            not in namespace
        ), (
            "PolicyEngine must not directly depend on "
            f"{dependency}."
        )

    print(
        "[PASS] Policy domain isolation"
    )

    # ========================================================================
    # 25. Evaluation immutability
    # ========================================================================

    immutable_failed = False

    try:

        evaluation.policy_score = 0.10

    except dataclasses.FrozenInstanceError:

        immutable_failed = True

    assert (
        immutable_failed
        is True
    )

    print(
        "[PASS] Evaluation immutability"
    )

    # ========================================================================
    # 26. Rule semantics
    # ========================================================================

    assert (
        custom_rule.effect
        == PolicyRuleEffect.ESCALATE
    )

    assert (
        custom_rule.to_dict()[
            "effect"
        ]
        == "escalate"
    )

    print(
        "[PASS] Rule semantic contract"
    )

    return True


# ============================================================================
# Module execution
# ============================================================================


if __name__ == "__main__":

    print("=" * 70)

    print(
        "EnterpriseGuard - ADIE Policy Engine Self-Test"
    )

    print("=" * 70)

    try:

        self_test()

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