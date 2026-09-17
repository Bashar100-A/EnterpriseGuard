"""
EnterpriseGuard ADIE - Decision Contracts
========================================

Canonical Production Decision Domain.

Architecture Boundary
---------------------

Policy Evaluation
        |
        v
Decision Engine Evaluation
        |
        v
Decision Contract
        |
        v
Response Execution / Enforcement Layer


Purpose
-------

The Decision domain is the canonical authorization contract bridge.
It converts evaluated policy intents into bounded, immutable Decision Contracts.

Decision MUST NOT:
- execute raw infrastructure commands directly.
- bypass policy evaluations.
- alter historical evidence or evaluation IDs.


Security Boundary
-----------------

This module:

- consumes PolicyEvaluation contracts.
- map policy intents to concrete authorization actions.
- enforces decision constraints and expiration timeouts.
- guarantees cryptographic audit provenance.
- fails safely on invalid or expired inputs.

This module does NOT:

- issue network/host remediation commands directly.
- modify underlying security policies dynamically.


Design Principles
-----------------

1. Strict policy compliance.
2. Immutable decision contracts.
3. Explicit action mapping.
4. Complete provenance and checksum tracking.
5. UTC-only datetime validation.
6. JSON-safe serialization.
7. Thread-safe evaluation counter and singleton instance.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import Any

MODULE_NAME = "adie.decision"
MODULE_VERSION = "2.0.0"


DEFAULT_DECISION_TTL_SECONDS = 300  # 5 minutes validity
MAX_DECISION_TTL_SECONDS = 3600    # 1 hour maximum validity


EXECUTES_SECURITY_ACTIONS = False
DESTRUCTIVE_ACTIONS_ALLOWED = False


# ============================================================================
# Exceptions
# ============================================================================


class DecisionError(Exception):
    """Base ADIE decision exception."""


class DecisionValidationError(DecisionError):
    """Invalid decision contract or input payload."""


class DecisionEvaluationError(DecisionError):
    """Decision mapping or evaluation failure."""


# ============================================================================
# Enums
# ============================================================================


class DecisionAction(str, Enum):
    """
    Concrete authorized defensive action scope.
    """

    NO_ACTION = "no_action"
    LOG_AND_MONITOR = "log_and_monitor"
    DISPATCH_ALERT = "dispatch_alert"
    CONTAIN_SESSION = "contain_session"
    ISOLATE_HOST = "isolate_host"
    REJECT_REQUEST = "reject_request"


class DecisionStatus(str, Enum):
    """
    Lifecycle status of a decision contract.
    """

    PENDING = "pending"
    AUTHORIZED = "authorized"
    DENIED = "denied"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


# ============================================================================
# Utility Functions
# ============================================================================


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _validate_utc(value: datetime, field_name: str) -> None:
    """Enforce datetime presence and explicit timezone awareness."""
    if not isinstance(value, datetime):
        raise DecisionValidationError(
            f"{field_name} must be a datetime instance"
        )

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise DecisionValidationError(
            f"{field_name} must be timezone-aware (UTC)"
        )


def _iso(value: datetime) -> str:
    """Format datetime as strict UTC ISO-8601 string."""
    _validate_utc(value, "timestamp")
    return value.astimezone(timezone.utc).isoformat()


def _validate_str(value: Any, name: str) -> str:
    """Validate non-empty string identifier."""
    if not isinstance(value, str) or not value.strip():
        raise DecisionValidationError(
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
        return tuple(_freeze(item) for item in sorted(value, key=lambda x: str(x)))

    return value


def _unfreeze(value: Any) -> Any:
    """Recursively convert immutable proxies into standard JSON-serializable types."""
    if isinstance(value, (Mapping, MappingProxyType)):
        return {key: _unfreeze(item) for key, item in value.items()}

    if isinstance(value, (tuple, list, frozenset, set)):
        return [_unfreeze(item) for item in value]

    return value


# ============================================================================
# Decision Configuration
# ============================================================================


@dataclass(frozen=True)
class DecisionConfig:
    """
    Immutable decision engine configuration contract.
    """

    engine_id: str
    engine_version: str
    ttl_seconds: int = DEFAULT_DECISION_TTL_SECONDS
    require_explicit_approval: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "engine_id",
            _validate_str(self.engine_id, "engine_id"),
        )
        object.__setattr__(
            self,
            "engine_version",
            _validate_str(self.engine_version, "engine_version"),
        )

        if not isinstance(self.ttl_seconds, int) or isinstance(self.ttl_seconds, bool):
            raise DecisionValidationError("ttl_seconds must be an integer")

        if not 1 <= self.ttl_seconds <= MAX_DECISION_TTL_SECONDS:
            raise DecisionValidationError(
                f"ttl_seconds must be between 1 and {MAX_DECISION_TTL_SECONDS}"
            )


# ============================================================================
# Decision Contract
# ============================================================================


@dataclass(frozen=True)
class DecisionContract:
    """
    Immutable authorized Decision Contract.

    This contract represents the final policy-backed decision statement.
    It does NOT execute actions directly.
    """

    decision_id: str
    evaluation_id: str
    policy_id: str
    action: DecisionAction
    status: DecisionStatus
    authorized: bool
    created_at: datetime
    expires_at: datetime
    target_resource_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    provenance_hash: str = ""
    executes_security_actions: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "decision_id",
            _validate_str(self.decision_id, "decision_id"),
        )
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
            "target_resource_id",
            _validate_str(self.target_resource_id, "target_resource_id"),
        )

        _validate_utc(self.created_at, "created_at")
        _validate_utc(self.expires_at, "expires_at")

        if self.expires_at <= self.created_at:
            raise DecisionValidationError("expires_at must be strictly after created_at")

        if self.executes_security_actions:
            raise DecisionValidationError("Decision domain cannot execute security actions directly")

        object.__setattr__(self, "parameters", _freeze(self.parameters))

        if not self.provenance_hash:
            calculated_hash = self._compute_provenance()
            object.__setattr__(self, "provenance_hash", calculated_hash)

    def _compute_provenance(self) -> str:
        """Compute cryptographic sha256 checksum of the contract payload."""
        payload = {
            "decision_id": self.decision_id,
            "evaluation_id": self.evaluation_id,
            "policy_id": self.policy_id,
            "action": self.action.value,
            "status": self.status.value,
            "authorized": self.authorized,
            "created_at": _iso(self.created_at),
            "expires_at": _iso(self.expires_at),
            "target_resource_id": self.target_resource_id,
            "parameters": _unfreeze(self.parameters),
        }

        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(serialized.encode("utf-8")).hexdigest()

    def is_expired(self, current_time: datetime | None = None) -> bool:
        """Check if contract has surpassed its validity timestamp."""
        now = current_time if current_time is not None else _utc_now()
        _validate_utc(now, "current_time")
        return now >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert contract to JSON-serializable dictionary."""
        return {
            "decision_id": self.decision_id,
            "evaluation_id": self.evaluation_id,
            "policy_id": self.policy_id,
            "action": self.action.value,
            "status": self.status.value,
            "authorized": self.authorized,
            "created_at": _iso(self.created_at),
            "expires_at": _iso(self.expires_at),
            "target_resource_id": self.target_resource_id,
            "parameters": _unfreeze(self.parameters),
            "provenance_hash": self.provenance_hash,
            "executes_security_actions": False,
        }


# ============================================================================
# Decision Engine
# ============================================================================


class ADIEDecision:
    """
    Canonical ADIE Decision Engine.

    Responsibilities:
    - consume PolicyEvaluation outputs.
    - map intentions to concrete DecisionAction authorizations.
    - generate cryptographically signed DecisionContracts.

    Non-responsibilities:
    - direct command execution.
    - raw evidence parsing.
    """

    def __init__(self, config: DecisionConfig | None = None) -> None:
        self._config = (
            config
            if config is not None
            else DecisionConfig(
                engine_id="default-decision-engine",
                engine_version="1.0.0",
            )
        )

        self._counter = 0
        self._lock = threading.Lock()

    def evaluate_policy_result(
        self,
        policy_evaluation: Any,
        target_resource_id: str,
        extra_parameters: Mapping[str, Any] | None = None,
    ) -> DecisionContract:
        """
        Evaluate PolicyEvaluation output and build an authorized DecisionContract.
        """
        if not hasattr(policy_evaluation, "evaluation_id") or not hasattr(policy_evaluation, "intent"):
            raise DecisionValidationError("Invalid PolicyEvaluation object provided")

        if not getattr(policy_evaluation, "allowed", False):
            return self._build_denied_contract(policy_evaluation, target_resource_id)

        intent_value = getattr(policy_evaluation.intent, "value", str(policy_evaluation.intent))
        action = self._map_intent_to_action(intent_value)

        with self._lock:
            self._counter += 1
            count = self._counter

        created_at = _utc_now()
        expires_at = created_at + timedelta(seconds=self._config.ttl_seconds)

        decision_id = self._generate_decision_id(
            policy_evaluation.evaluation_id,
            action.value,
            count,
        )

        params = dict(extra_parameters) if extra_parameters else {}
        params["mapped_intent"] = intent_value
        params["decision_score"] = getattr(policy_evaluation, "decision_score", 0.0)

        return DecisionContract(
            decision_id=decision_id,
            evaluation_id=policy_evaluation.evaluation_id,
            policy_id=getattr(policy_evaluation, "policy_id", "unknown"),
            action=action,
            status=DecisionStatus.AUTHORIZED,
            authorized=True,
            created_at=created_at,
            expires_at=expires_at,
            target_resource_id=target_resource_id,
            parameters=params,
            executes_security_actions=False,
        )

    def _build_denied_contract(
        self,
        policy_evaluation: Any,
        target_resource_id: str,
    ) -> DecisionContract:
        """Construct a safely denied DecisionContract."""
        with self._lock:
            self._counter += 1
            count = self._counter

        created_at = _utc_now()
        expires_at = created_at + timedelta(seconds=self._config.ttl_seconds)

        decision_id = self._generate_decision_id(
            policy_evaluation.evaluation_id,
            "denied",
            count,
        )

        return DecisionContract(
            decision_id=decision_id,
            evaluation_id=policy_evaluation.evaluation_id,
            policy_id=getattr(policy_evaluation, "policy_id", "unknown"),
            action=DecisionAction.NO_ACTION,
            status=DecisionStatus.DENIED,
            authorized=False,
            created_at=created_at,
            expires_at=expires_at,
            target_resource_id=target_resource_id,
            parameters={"denial_reason": "Policy explicitly disallowed intent"},
            executes_security_actions=False,
        )

    @staticmethod
    def _map_intent_to_action(intent: str) -> DecisionAction:
        """Map Policy Intent string to concrete DecisionAction (Fail-Closed)."""
        mapping = {
            "allow": DecisionAction.NO_ACTION,
            "monitor": DecisionAction.LOG_AND_MONITOR,
            "alert": DecisionAction.DISPATCH_ALERT,
            "contain": DecisionAction.CONTAIN_SESSION,
            "isolate": DecisionAction.ISOLATE_HOST,
            "deny": DecisionAction.REJECT_REQUEST,
        }
        normalized = intent.lower().strip()
        if normalized not in mapping:
            raise DecisionEvaluationError(f"Unrecognized policy evaluation intent: '{intent}'")
        return mapping[normalized]

    def _generate_decision_id(
        self,
        evaluation_id: str,
        action: str,
        counter: int,
    ) -> str:
        """Create a deterministic SHA-256 backed decision contract ID."""
        payload = {
            "counter": counter,
            "evaluation_id": evaluation_id,
            "action": action,
            "engine_id": self._config.engine_id,
            "engine_version": self._config.engine_version,
        }

        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = sha256(serialized.encode("utf-8")).hexdigest()
        return f"dec-{digest[:24]}"

    def status(self) -> dict[str, Any]:
        """Return engine status snapshot."""
        with self._lock:
            count = self._counter

        return {
            "module": MODULE_NAME,
            "version": MODULE_VERSION,
            "engine_id": self._config.engine_id,
            "engine_version": self._config.engine_version,
            "decisions_evaluated": count,
            "executes_security_actions": False,
        }

    def self_test(self) -> dict[str, Any]:
        """Validate decision domain contracts and invariants."""
        tests: dict[str, bool] = {}

        try:
            # Fake mock class mirroring PolicyEvaluation contract
            class DummyPolicyEval:
                evaluation_id = "peval-1234567890abcdef12345678"
                policy_id = "test-policy"
                policy_version = "1.0.0"
                intent = "isolate"
                allowed = True
                decision_score = 0.96

            mock_eval = DummyPolicyEval()
            contract = self.evaluate_policy_result(
                policy_evaluation=mock_eval,
                target_resource_id="host-srv-01",
            )

            tests["contract_created"] = isinstance(contract, DecisionContract)
            tests["intent_mapping"] = contract.action == DecisionAction.ISOLATE_HOST
            tests["provenance_hash_valid"] = len(contract.provenance_hash) == 64
            tests["utc_dates"] = contract.created_at.tzinfo is not None
            tests["expiration_valid"] = not contract.is_expired()

            # Verify immutability
            tests["immutable_contract"] = False
            try:
                contract.authorized = False  # type: ignore
            except Exception:
                tests["immutable_contract"] = True

            serialized = contract.to_dict()
            tests["json_serializable"] = isinstance(serialized, dict) and serialized["authorized"] is True

            passed = all(tests.values())

            return {
                "passed": passed,
                "module": MODULE_NAME,
                "version": MODULE_VERSION,
                "tests": tests,
                "executes_security_actions": False,
            }

        except Exception as exc:
            return {
                "passed": False,
                "module": MODULE_NAME,
                "version": MODULE_VERSION,
                "tests": tests,
                "error": type(exc).__name__,
                "error_message": str(exc),
                "executes_security_actions": False,
            }


# ============================================================================
# Default Decision Engine Instance (Thread-Safe Singleton)
# ============================================================================


_default_decision_engine: ADIEDecision | None = None
_decision_lock = threading.Lock()


def get_decision_engine() -> ADIEDecision:
    """Return process-local default ADIE decision engine (Thread-Safe)."""
    global _default_decision_engine

    if _default_decision_engine is None:
        with _decision_lock:
            if _default_decision_engine is None:
                _default_decision_engine = ADIEDecision()

    return _default_decision_engine


def self_test() -> dict[str, Any]:
    """Module-level self test."""
    return ADIEDecision().self_test()


# ============================================================================
# Public API
# ============================================================================


__all__ = [
    "MODULE_NAME",
    "MODULE_VERSION",
    "ADIEDecision",
    "DecisionAction",
    "DecisionConfig",
    "DecisionContract",
    "DecisionError",
    "DecisionEvaluationError",
    "DecisionStatus",
    "DecisionValidationError",
    "get_decision_engine",
    "self_test",
]


# ============================================================================
# Module Execution
# ============================================================================


def _main() -> int:
    result = self_test()
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
