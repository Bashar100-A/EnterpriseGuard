"""
EnterpriseGuard ADIE
Adaptive Defense Intelligence Engine

Decision Foundation
===================

Canonical Production Decision Domain.

Architecture:

Prediction
    |
    v
Policy Evaluation
    |
    v
Decision Evaluation
    |
    v
Decision Contract
    |
    v
Playbook / Response Intent


Security Boundary:

Decision represents defensive intent only.

It does NOT:

- execute actions
- call external systems
- modify infrastructure
- perform remediation
- bypass policy
- override prediction uncertainty


Design Principles:

- Policy authority before decision
- Immutable contracts
- Deep immutability
- Deterministic evaluation
- Audit provenance
- UTC timestamps
- JSON-safe serialization
"""

from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping
import json



# ============================================================================
# Constants
# ============================================================================


MODULE_NAME = "adie.decision"

MODULE_VERSION = "3.0.1"


MIN_SCORE = 0.0

MAX_SCORE = 1.0



ALERT_THRESHOLD = 0.70

CONTAIN_THRESHOLD = 0.85

ISOLATE_THRESHOLD = 0.95



EXECUTES_SECURITY_ACTIONS = False



# ============================================================================
# Exceptions
# ============================================================================


class DecisionError(Exception):
    """Base ADIE decision exception."""



class DecisionValidationError(DecisionError):
    """Raised when decision data is invalid."""



class DecisionContractError(DecisionError):
    """Raised when decision boundary is violated."""



# ============================================================================
# Enums
# ============================================================================


class DecisionIntent(str, Enum):
    """
    Defensive intent only.

    These values never execute actions.
    """

    ALLOW = "allow"

    MONITOR = "monitor"

    ALERT = "alert"

    CONTAIN = "contain"

    ISOLATE = "isolate"

    DEFER = "defer"



class DecisionLifecycle(str, Enum):
    """
    Decision lifecycle state.
    """

    GENERATED = "generated"

    APPROVED = "approved"

    BLOCKED = "blocked"

    DEFERRED = "deferred"

    EXPIRED = "expired"

    INVALID = "invalid"



# ============================================================================
# Internal Helpers
# ============================================================================


def _utc_now() -> datetime:
    """
    Return current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    )



def _validate_datetime(
    value: datetime,
    field_name: str,
) -> datetime:

    if not isinstance(
        value,
        datetime,
    ):
        raise DecisionValidationError(
            f"{field_name} must be datetime"
        )


    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise DecisionValidationError(
            f"{field_name} must be timezone aware"
        )


    return value.astimezone(
        timezone.utc
    )



def _iso(
    value: datetime,
) -> str:

    return _validate_datetime(
        value,
        "timestamp",
    ).isoformat()



def _validate_score(
    value: Any,
    field_name: str,
) -> float:

    if isinstance(
        value,
        bool,
    ):
        raise DecisionValidationError(
            f"{field_name} cannot be boolean"
        )


    try:

        numeric = float(value)

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise DecisionValidationError(
            f"{field_name} must be numeric"
        ) from exc



    if not isfinite(numeric):

        raise DecisionValidationError(
            f"{field_name} must be finite"
        )



    if not (
        MIN_SCORE
        <= numeric
        <= MAX_SCORE
    ):

        raise DecisionValidationError(
            f"{field_name} must be between 0 and 1"
        )


    return numeric



def _freeze(
    value: Any,
) -> Any:
    """
    Deep freeze mutable structures.
    """


    if isinstance(
        value,
        Mapping,
    ):

        return MappingProxyType(
            {
                str(key):
                _freeze(item)

                for key, item
                in value.items()
            }
        )


    if isinstance(
        value,
        list,
    ):

        return tuple(
            _freeze(item)
            for item in value
        )


    if isinstance(
        value,
        tuple,
    ):

        return tuple(
            _freeze(item)
            for item in value
        )


    if isinstance(
        value,
        set,
    ):

        return frozenset(
            _freeze(item)
            for item in value
        )


    return value



def _thaw(
    value: Any,
) -> Any:

    if isinstance(
        value,
        Mapping,
    ):

        return {
            key:
            _thaw(item)

            for key, item
            in value.items()
        }


    if isinstance(
        value,
        tuple,
    ):

        return [
            _thaw(item)
            for item in value
        ]


    if isinstance(
        value,
        (set, frozenset),
    ):

        return [
            _thaw(item)
            for item in value
        ]


    return value
# ============================================================================
# Decision Evidence Contract
# ============================================================================


@dataclass(frozen=True)
class DecisionEvidence:
    """
    Immutable evidence entering the decision domain.

    Evidence is provided by upstream intelligence
    and policy layers.

    It does not authorize execution.
    """

    prediction_id: str

    policy_id: str

    threat_probability: float

    prediction_confidence: float

    state_risk: float

    policy_allowed: bool

    collected_at: datetime

    context: Mapping[str, Any] = field(
        default_factory=dict
    )


    def __post_init__(self) -> None:

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
            "collected_at",
            _validate_datetime(
                self.collected_at,
                "collected_at",
            ),
        )

        if not isinstance(
            self.context,
            Mapping,
        ):
            raise DecisionValidationError(
                "context must be mapping"
            )

        object.__setattr__(
            self,
            "context",
            _freeze(
                self.context
            ),
        )


    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "prediction_id":
                self.prediction_id,

            "policy_id":
                self.policy_id,

            "threat_probability":
                self.threat_probability,

            "prediction_confidence":
                self.prediction_confidence,

            "state_risk":
                self.state_risk,

            "policy_allowed":
                self.policy_allowed,

            "collected_at":
                _iso(
                    self.collected_at
                ),

            "context":
                _thaw(
                    self.context
                ),
        }



# ============================================================================
# Decision Contract
# ============================================================================


@dataclass(frozen=True)
class DecisionContract:
    """
    Immutable ADIE decision result.

    Represents defensive intent only.

    Never executes actions.
    """

    decision_id: str

    intent: DecisionIntent

    lifecycle: DecisionLifecycle

    decision_score: float

    confidence: float

    prediction_id: str

    policy_id: str

    rationale: str

    reason_codes: tuple[str, ...]

    created_at: datetime

    audit_metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    executes_security_actions: bool = False


    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "decision_score",
            _validate_score(
                self.decision_score,
                "decision_score",
            ),
        )

        object.__setattr__(
            self,
            "confidence",
            _validate_score(
                self.confidence,
                "confidence",
            ),
        )

        object.__setattr__(
            self,
            "created_at",
            _validate_datetime(
                self.created_at,
                "created_at",
            ),
        )

        if self.executes_security_actions:

            raise DecisionContractError(
                "Decision layer cannot execute actions"
            )


        object.__setattr__(
            self,
            "audit_metadata",
            _freeze(
                self.audit_metadata
            ),
        )


    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {

            "decision_id":
                self.decision_id,

            "intent":
                self.intent.value,

            "lifecycle":
                self.lifecycle.value,

            "decision_score":
                self.decision_score,

            "confidence":
                self.confidence,

            "prediction_id":
                self.prediction_id,

            "policy_id":
                self.policy_id,

            "rationale":
                self.rationale,

            "reason_codes":
                list(
                    self.reason_codes
                ),

            "created_at":
                _iso(
                    self.created_at
                ),

            "audit_metadata":
                _thaw(
                    self.audit_metadata
                ),

            "executes_security_actions":
                False,
        }



# ============================================================================
# Decision Engine
# ============================================================================


class DecisionEngine:
    """
    Canonical ADIE decision evaluator.

    Converts validated evidence into
    defensive intent.

    Does not execute.
    """


    def __init__(self) -> None:

        self._decision_count = 0



    def evaluate(
        self,
        evidence: DecisionEvidence,
    ) -> DecisionContract:

        if not isinstance(
            evidence,
            DecisionEvidence,
        ):

            raise DecisionValidationError(
                "DecisionEvidence required"
            )


        self._decision_count += 1


        score = self._calculate_score(
            evidence
        )


        if not evidence.policy_allowed:

            intent = DecisionIntent.DEFER

            lifecycle = (
                DecisionLifecycle.DEFERRED
            )

            reasons = (
                "POLICY_NOT_ALLOWED",
            )


        else:

            intent, reasons = (
                self._resolve_intent(
                    score
                )
            )

            lifecycle = (
                DecisionLifecycle.GENERATED
            )


        decision_id = (
            self._generate_id(
                evidence,
                score,
            )
        )


        return DecisionContract(

            decision_id=decision_id,

            intent=intent,

            lifecycle=lifecycle,

            decision_score=score,

            confidence=
                evidence.prediction_confidence,

            prediction_id=
                evidence.prediction_id,

            policy_id=
                evidence.policy_id,

            rationale=(
                "Decision generated from "
                "prediction evidence and "
                "policy authority."
            ),

            reason_codes=tuple(
                reasons
            ),

            created_at=_utc_now(),

            audit_metadata={

                "module":
                    MODULE_NAME,

                "version":
                    MODULE_VERSION,

                "decision_number":
                    self._decision_count,
            },
        )



    @staticmethod
    def _calculate_score(
        evidence: DecisionEvidence,
    ) -> float:

        score = (

            0.55
            *
            evidence.threat_probability

            +

            0.25
            *
            evidence.prediction_confidence

            +

            0.20
            *
            evidence.state_risk

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



    @staticmethod
    def _resolve_intent(
        score: float,
    ) -> tuple[
        DecisionIntent,
        list[str],
    ]:


        if score >= ISOLATE_THRESHOLD:

            return (
                DecisionIntent.ISOLATE,
                [
                    "ISOLATE_THRESHOLD_REACHED"
                ],
            )


        if score >= CONTAIN_THRESHOLD:

            return (
                DecisionIntent.CONTAIN,
                [
                    "CONTAIN_THRESHOLD_REACHED"
                ],
            )


        if score >= ALERT_THRESHOLD:

            return (
                DecisionIntent.ALERT,
                [
                    "ALERT_THRESHOLD_REACHED"
                ],
            )


        if score >= 0.40:

            return (
                DecisionIntent.MONITOR,
                [
                    "MONITOR_REQUIRED"
                ],
            )


        return (
            DecisionIntent.ALLOW,
            [
                "LOW_RISK"
            ],
        )



    @staticmethod
    def _generate_id(
        evidence: DecisionEvidence,
        score: float,
    ) -> str:

        payload = json.dumps(
            {
                "prediction":
                    evidence.prediction_id,

                "policy":
                    evidence.policy_id,

                "score":
                    score,
            },
            sort_keys=True,
        )


        digest = sha256(
            payload.encode(
                "utf-8"
            )
        ).hexdigest()


        return (
            "decision-"
            +
            digest[:24]
        )



    def status(self) -> dict[str, Any]:

        return {

            "module":
                MODULE_NAME,

            "version":
                MODULE_VERSION,

            "decision_count":
                self._decision_count,

            "executes_security_actions":
                False,
        }



    def self_test(self) -> dict[str, Any]:

        evidence = DecisionEvidence(

            prediction_id="prediction-test",

            policy_id="policy-test",

            threat_probability=0.90,

            prediction_confidence=0.95,

            state_risk=0.80,

            policy_allowed=True,

            collected_at=_utc_now(),
        )


        result = self.evaluate(
            evidence
        )


        passed = (

            isinstance(
                result,
                DecisionContract,
            )

            and

            result.intent
            in {
                DecisionIntent.ALERT,
                DecisionIntent.CONTAIN,
                DecisionIntent.ISOLATE,
            }

            and

            result.executes_security_actions
            is False
        )


        return {

            "passed":
                passed,

            "module":
                MODULE_NAME,

            "version":
                MODULE_VERSION,

            "decision":
                result.to_dict(),

            "executes_security_actions":
                False,
        }



# ============================================================================
# Default Engine
# ============================================================================


_default_engine: DecisionEngine | None = None



def get_decision_engine() -> DecisionEngine:

    global _default_engine


    if _default_engine is None:

        _default_engine = DecisionEngine()


    return _default_engine



# ============================================================================
# Public API
# ============================================================================


__all__ = [

    "MODULE_NAME",

    "MODULE_VERSION",

    "DecisionError",

    "DecisionValidationError",

    "DecisionContractError",

    "DecisionIntent",

    "DecisionLifecycle",

    "DecisionEvidence",

    "DecisionContract",

    "DecisionEngine",

    "get_decision_engine",

]



# ============================================================================
# Direct Execution
# ============================================================================


def _main() -> int:

    result = DecisionEngine().self_test()


    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


    return (
        0
        if result["passed"]
        else 1
    )



if __name__ == "__main__":

    raise SystemExit(
        _main()
    )