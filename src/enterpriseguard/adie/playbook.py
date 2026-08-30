"""
EnterpriseGuard ADIE - Adaptive Playbook Layer
==============================================

Version
-------
2.0.0

Purpose
-------
The Adaptive Playbook Layer converts an approved ADIE Decision Contract
into a deterministic, immutable and auditable response plan.

This module represents defensive intent only.

Security Boundary
-----------------
PLANNING ONLY.

This module does NOT:

- execute security actions
- isolate systems
- terminate processes
- modify infrastructure
- call external adapters
- perform rollback
- alter enterprise state

Execution belongs exclusively to downstream authorized systems.

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
Decision Contract
  |
  v
Adaptive Playbook
  |
  v
Checkpoint Reference
  |
  v
Response Executor


Design Goals
------------

1. Deterministic planning.
2. Immutable contracts.
3. Complete ADIE lineage.
4. Policy separation.
5. Audit readiness.
6. Fingerprint integrity.
7. Safe failure behavior.
8. No execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple
from datetime import datetime, timezone
import copy
import json
import uuid


__all__ = [
    "PLAYBOOK_VERSION",
    "PlaybookError",
    "PlaybookValidationError",
    "PlaybookActionType",
    "PlaybookStatus",
    "PlaybookAction",
    "Playbook",
    "PlaybookResult",
    "PlaybookEngine",
    "self_test",
]


PLAYBOOK_VERSION = "2.0.0"


# ======================================================================
# Exceptions
# ======================================================================


class PlaybookError(Exception):
    """Base ADIE playbook exception."""


class PlaybookValidationError(PlaybookError):
    """Raised when playbook validation fails."""


# ======================================================================
# Enumerations
# ======================================================================


class PlaybookActionType(str, Enum):
    """
    Logical response planning primitives.

    These values describe intent only.
    """

    MONITOR = "monitor"
    ALERT = "alert"
    ESCALATE = "escalate"
    CONTAIN = "contain"
    ISOLATE = "isolate"
    COLLECT_EVIDENCE = "collect_evidence"
    CREATE_CHECKPOINT = "create_checkpoint"
    REVIEW = "review"


class PlaybookStatus(str, Enum):

    DRAFT = "draft"
    READY = "ready"
    BLOCKED = "blocked"
    APPROVAL_REQUIRED = "approval_required"


# ======================================================================
# Utility Functions
# ======================================================================


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _freeze_mapping(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    return MappingProxyType(
        copy.deepcopy(
            dict(value)
        )
    )


def _safe_probability(
    value: Any,
) -> float:

    try:
        result = float(value)
    except Exception:
        return 0.0

    if result < 0:
        return 0.0

    if result > 1:
        return 1.0

    return result


def _hash_payload(
    payload: Mapping[str, Any],
) -> str:

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode(
        "utf-8"
    )

    return sha256(
        encoded
    ).hexdigest()


# ======================================================================
# Playbook Action Contract
# ======================================================================


@dataclass(frozen=True)
class PlaybookAction:
    """
    Immutable planned action.

    This is NOT an execution command.

    It only describes an intended response step.
    """

    action_id: str

    action_type: PlaybookActionType

    description: str

    priority: int = 100

    requires_approval: bool = False

    parameters: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:

        if not str(
            self.action_id
        ).strip():

            raise PlaybookValidationError(
                "action_id cannot be empty"
            )

        if not isinstance(
            self.action_type,
            PlaybookActionType,
        ):

            raise PlaybookValidationError(
                "invalid action type"
            )

        if not isinstance(
            self.priority,
            int,
        ):

            raise PlaybookValidationError(
                "priority must be integer"
            )

        if self.priority < 0:

            raise PlaybookValidationError(
                "priority must be >= 0"
            )

        object.__setattr__(
            self,
            "parameters",
            _freeze_mapping(
                self.parameters
            ),
        )


    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {

            "action_id":
                self.action_id,

            "action_type":
                self.action_type.value,

            "description":
                self.description,

            "priority":
                self.priority,

            "requires_approval":
                self.requires_approval,

            "parameters":
                copy.deepcopy(
                    dict(
                        self.parameters
                    )
                ),
        }


# ======================================================================
# Playbook Contract
# ======================================================================


@dataclass(frozen=True)
class Playbook:
    """
    Immutable ADIE Playbook Contract.

    Maintains complete lineage:

        state_id
            |
        prediction_id
            |
        decision_id
            |
        playbook_id
    """

    playbook_id: str

    name: str

    description: str

    actions: Tuple[
        PlaybookAction,
        ...

    ]

    status: PlaybookStatus

    decision_id: Optional[str] = None

    state_id: Optional[str] = None

    prediction_id: Optional[str] = None

    decision_fingerprint: Optional[str] = None

    checkpoint_reference: Optional[str] = None

    decision_action: Optional[str] = None

    decision_score: float = 0.0

    threat_probability: float = 0.0

    confidence: float = 0.0

    policy_allowed: bool = True

    created_at: datetime = field(
        default_factory=_utc_now
    )

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )
    def __post_init__(self) -> None:

        if not str(
            self.playbook_id
        ).strip():

            raise PlaybookValidationError(
                "playbook_id cannot be empty"
            )

        if not str(
            self.name
        ).strip():

            raise PlaybookValidationError(
                "name cannot be empty"
            )

        if not isinstance(
            self.status,
            PlaybookStatus,
        ):

            raise PlaybookValidationError(
                "invalid playbook status"
            )

        normalized_actions = tuple(
            self.actions
        )

        for action in normalized_actions:

            if not isinstance(
                action,
                PlaybookAction,
            ):

                raise PlaybookValidationError(
                    "invalid playbook action"
                )

        object.__setattr__(
            self,
            "actions",
            normalized_actions,
        )

        object.__setattr__(
            self,
            "decision_score",
            _safe_probability(
                self.decision_score
            ),
        )

        object.__setattr__(
            self,
            "threat_probability",
            _safe_probability(
                self.threat_probability
            ),
        )

        object.__setattr__(
            self,
            "confidence",
            _safe_probability(
                self.confidence
            ),
        )

        if self.created_at.tzinfo is None:

            raise PlaybookValidationError(
                "created_at must be timezone aware"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(
                self.metadata
            ),
        )


    @property
    def action_count(
        self,
    ) -> int:

        return len(
            self.actions
        )


    @property
    def fingerprint(
        self,
    ) -> str:

        payload = {

            "playbook_id":
                self.playbook_id,

            "decision_id":
                self.decision_id,

            "state_id":
                self.state_id,

            "prediction_id":
                self.prediction_id,

            "decision_fingerprint":
                self.decision_fingerprint,

            "checkpoint_reference":
                self.checkpoint_reference,

            "decision_action":
                self.decision_action,

            "decision_score":
                self.decision_score,

            "threat_probability":
                self.threat_probability,

            "confidence":
                self.confidence,

            "policy_allowed":
                self.policy_allowed,

            "actions":
                [
                    action.to_dict()
                    for action
                    in self.actions
                ],
        }

        return _hash_payload(
            payload
        )


    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {

            "playbook_id":
                self.playbook_id,

            "name":
                self.name,

            "description":
                self.description,

            "actions":
                [
                    action.to_dict()
                    for action
                    in self.actions
                ],

            "status":
                self.status.value,

            "decision_id":
                self.decision_id,

            "state_id":
                self.state_id,

            "prediction_id":
                self.prediction_id,

            "decision_fingerprint":
                self.decision_fingerprint,

            "checkpoint_reference":
                self.checkpoint_reference,

            "decision_action":
                self.decision_action,

            "decision_score":
                self.decision_score,

            "threat_probability":
                self.threat_probability,

            "confidence":
                self.confidence,

            "policy_allowed":
                self.policy_allowed,

            "created_at":
                self.created_at.isoformat(),

            "metadata":
                copy.deepcopy(
                    dict(
                        self.metadata
                    )
                ),

            "fingerprint":
                self.fingerprint,
        }


# ======================================================================
# Playbook Result
# ======================================================================


@dataclass(frozen=True)
class PlaybookResult:

    success: bool

    playbook: Optional[
        Playbook
    ]

    error: Optional[str] = None

    blocked: bool = False

    executes_security_actions: bool = False

    version: str = PLAYBOOK_VERSION


    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {

            "success":
                self.success,

            "playbook":
                (
                    self.playbook.to_dict()
                    if self.playbook
                    else None
                ),

            "error":
                self.error,

            "blocked":
                self.blocked,

            "executes_security_actions":
                False,

            "version":
                self.version,
        }



# ======================================================================
# Playbook Engine
# ======================================================================


class PlaybookEngine:
    """
    Generates ADIE adaptive playbooks.

    Responsibility:

    Decision Contract
          |
          v
    Planning Contract


    Does NOT execute anything.
    """


    VERSION = PLAYBOOK_VERSION


    def __init__(
        self,
        *,
        require_approval: bool = True,
    ) -> None:

        self._require_approval = bool(
            require_approval
        )


    def create(
        self,
        decision: Any,
    ) -> PlaybookResult:
        """
        Create playbook from DecisionContract
        or dictionary representation.
        """

        try:

            normalized = (
                self._normalize_decision(
                    decision
                )
            )


            if not normalized[
                "policy_allowed"
            ]:

                playbook = (
                    self._blocked_playbook(
                        normalized
                    )
                )

                return PlaybookResult(
                    success=True,
                    playbook=playbook,
                    blocked=True,
                )


            actions = (
                self._build_actions(
                    normalized
                )
            )


            playbook = Playbook(

                playbook_id=(
                    self._build_id(
                        normalized
                    )
                ),

                name=(
                    self._build_name(
                        normalized
                    )
                ),

                description=(
                    "ADIE adaptive "
                    "response planning contract."
                ),

                actions=tuple(
                    actions
                ),

                status=(
                    PlaybookStatus.READY
                ),

                decision_id=(
                    normalized[
                        "decision_id"
                    ]
                ),

                state_id=(
                    normalized[
                        "state_id"
                    ]
                ),

                prediction_id=(
                    normalized[
                        "prediction_id"
                    ]
                ),

                decision_fingerprint=(
                    normalized[
                        "decision_fingerprint"
                    ]
                ),

                checkpoint_reference=None,

                decision_action=(
                    normalized[
                        "action"
                    ]
                ),

                decision_score=(
                    normalized[
                        "score"
                    ]
                ),

                threat_probability=(
                    normalized[
                        "threat_probability"
                    ]
                ),

                confidence=(
                    normalized[
                        "confidence"
                    ]
                ),

                policy_allowed=True,

                metadata={

                    "module":
                        "adie.playbook",

                    "version":
                        PLAYBOOK_VERSION,

                    "planning_only":
                        True,

                    "executor_required":
                        bool(actions),
                },
            )


            return PlaybookResult(
                success=True,
                playbook=playbook,
            )


        except Exception as exc:

            return PlaybookResult(
                success=False,
                playbook=None,
                error=str(exc),
            )
    def validate(
        self,
        playbook: Playbook,
    ) -> bool:

        if not isinstance(
            playbook,
            Playbook,
        ):
            raise PlaybookValidationError(
                "invalid playbook object"
            )

        priorities = [
            action.priority
            for action in playbook.actions
        ]

        if priorities != sorted(priorities):
            raise PlaybookValidationError(
                "actions must be ordered by priority"
            )

        return True


    def verify_integrity(
        self,
        playbook: Playbook,
    ) -> bool:

        if not isinstance(
            playbook,
            Playbook,
        ):
            return False

        fingerprint = (
            playbook.fingerprint
        )

        return (
            isinstance(
                fingerprint,
                str,
            )
            and len(
                fingerprint
            ) == 64
        )


    def status(
        self,
    ) -> dict[str, Any]:

        return {

            "module":
                "adie.playbook",

            "version":
                PLAYBOOK_VERSION,

            "planning_only":
                True,

            "executes_security_actions":
                False,
        }


    def _normalize_decision(
        self,
        decision: Any,
    ) -> dict[str, Any]:

        if hasattr(
            decision,
            "to_dict",
        ):

            data = decision.to_dict()

        elif isinstance(
            decision,
            Mapping,
        ):

            data = dict(
                decision
            )

        else:

            raise PlaybookValidationError(
                "unsupported decision type"
            )


        return {

            "decision_id":
                data.get(
                    "decision_id"
                ),

            "state_id":
                data.get(
                    "state_id"
                ),

            "prediction_id":
                data.get(
                    "prediction_id"
                ),

            "decision_fingerprint":
                data.get(
                    "fingerprint"
                ),

            "action":
                str(
                    data.get(
                        "intent",
                        data.get(
                            "action",
                            "monitor"
                        )
                    )
                ).lower(),

            "score":
                _safe_probability(
                    data.get(
                        "decision_score",
                        data.get(
                            "risk_score",
                            0
                        )
                    )
                ),

            "threat_probability":
                _safe_probability(
                    data.get(
                        "threat_probability",
                        0
                    )
                ),

            "confidence":
                _safe_probability(
                    data.get(
                        "confidence",
                        0
                    )
                ),

            "policy_allowed":
                bool(
                    data.get(
                        "policy_allowed",
                        True
                    )
                ),
        }


    def _build_actions(
        self,
        decision: Mapping[str, Any],
    ) -> list[PlaybookAction]:

        actions = []


        actions.append(
            PlaybookAction(
                action_id="monitor-001",
                action_type=(
                    PlaybookActionType.MONITOR
                ),
                description=(
                    "Increase monitoring and "
                    "collect additional telemetry."
                ),
                priority=10,
            )
        )


        action = decision[
            "action"
        ]


        if action in {
            "alert",
            "contain",
            "isolate",
        }:

            actions.append(
                PlaybookAction(
                    action_id="alert-001",
                    action_type=(
                        PlaybookActionType.ALERT
                    ),
                    description=(
                        "Generate security alert "
                        "for authorized review."
                    ),
                    priority=20,
                )
            )


        if action == "contain":

            actions.append(
                PlaybookAction(
                    action_id="contain-001",
                    action_type=(
                        PlaybookActionType.CONTAIN
                    ),
                    description=(
                        "Prepare containment plan "
                        "for downstream executor."
                    ),
                    priority=40,
                    requires_approval=True,
                    parameters={
                        "planning_only": True
                    },
                )
            )


        if action == "isolate":

            actions.append(
                PlaybookAction(
                    action_id="isolate-001",
                    action_type=(
                        PlaybookActionType.ISOLATE
                    ),
                    description=(
                        "Prepare isolation plan "
                        "for downstream executor."
                    ),
                    priority=40,
                    requires_approval=True,
                    parameters={
                        "planning_only": True
                    },
                )
            )


        if decision["score"] >= 0.85:

            actions.append(
                PlaybookAction(
                    action_id="checkpoint-001",
                    action_type=(
                        PlaybookActionType.CREATE_CHECKPOINT
                    ),
                    description=(
                        "Create response checkpoint "
                        "reference."
                    ),
                    priority=50,
                )
            )


        return actions


    def _blocked_playbook(
        self,
        decision: Mapping[str, Any],
    ) -> Playbook:

        return Playbook(

            playbook_id=(
                "blocked-"
                + uuid.uuid4().hex[:12]
            ),

            name="blocked-policy-decision",

            description=(
                "Decision blocked by policy."
            ),

            actions=(
                PlaybookAction(
                    action_id="review-001",
                    action_type=(
                        PlaybookActionType.REVIEW
                    ),
                    description=(
                        "Review policy denial."
                    ),
                    priority=100,
                    requires_approval=True,
                ),
            ),

            status=(
                PlaybookStatus.BLOCKED
            ),

            decision_id=(
                decision[
                    "decision_id"
                ]
            ),

            policy_allowed=False,

            metadata={
                "blocked": True
            },
        )


    @staticmethod
    def _build_id(
        decision: Mapping[str, Any],
    ) -> str:

        digest = _hash_payload(
            decision
        )

        return (
            "playbook-"
            + digest[:24]
        )


    @staticmethod
    def _build_name(
        decision: Mapping[str, Any],
    ) -> str:

        return (
            str(
                decision[
                    "action"
                ]
            )
            +
            "-adaptive-response"
        )



# ======================================================================
# Self Test
# ======================================================================


def self_test() -> dict[str, Any]:

    engine = PlaybookEngine()


    result = engine.create(
        {
            "decision_id":
                "decision-test",

            "state_id":
                "state-test",

            "prediction_id":
                "prediction-test",

            "intent":
                "contain",

            "decision_score":
                0.89,

            "threat_probability":
                0.90,

            "confidence":
                0.95,

            "policy_allowed":
                True,
        }
    )


    passed = (

        result.success

        and result.playbook is not None

        and result.executes_security_actions
        is False

        and engine.verify_integrity(
            result.playbook
        )
    )


    return {

        "passed":
            passed,

        "module":
            "adie.playbook",

        "version":
            PLAYBOOK_VERSION,

        "executes_security_actions":
            False,
    }



if __name__ == "__main__":

    print(
        json.dumps(
            self_test(),
            indent=2,
            ensure_ascii=False,
        )
    )