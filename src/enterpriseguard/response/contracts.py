"""
EnterpriseGuard ADIE - Response Contracts
========================================

Canonical Production Response Execution Domain.

Architecture Boundary
---------------------

Decision Contract (enterpriseguard.decision.contracts)
        |
        v
Response Engine Evaluation
        |
        v
Response Contract (Action Directive)
        |
        v
Enforcement Drivers / Security Integrations


Purpose
-------

The Response domain is the canonical enforcement contract bridge.
It converts evaluated and authorized Decision Contracts into bounded, 
immutable Response Contracts (Action Directives) ready for driver dispatch.

Response MUST NOT:
- execute raw infrastructure commands without a valid DecisionContract.
- bypass expired or unauthorized decision contracts.
- alter historical evaluation IDs or decision provenance hashes.


Security Boundary
-----------------

This module:

- consumes authorized DecisionContracts.
- maps DecisionActions to concrete EnforcementScopes and Response Modes.
- enforces response constraints, timeouts, and dry-run boundaries.
- guarantees cryptographic provenance linking decision to response.
- fails safely on invalid, expired, or non-authorized decision contracts.

This module does NOT:

- directly execute OS/API shell commands (relegated to enforcement drivers).
- override policy authorizations dynamically.


Design Principles
-----------------

1. Strict decision validation (Fail-Closed).
2. Immutable response contract directives.
3. Explicit scope and mode mapping.
4. Cryptographic provenance chaining.
5. Strict UTC datetime validation.
6. JSON-safe serialization.
7. Thread-safe execution tracking.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import Any

from enterpriseguard.decision.contracts import (
    DecisionAction,
    DecisionContract,
    DecisionStatus,
)

MODULE_NAME = "adie.response"
MODULE_VERSION = "2.0.0"


# ============================================================================
# Exceptions
# ============================================================================


class ResponseError(Exception):
    """Base ADIE response exception."""


class ResponseValidationError(ResponseError):
    """Invalid response contract or input decision contract."""


class ResponseExecutionError(ResponseError):
    """Response mapping or dispatch failure."""


# ============================================================================
# Enums
# ============================================================================


class ResponseMode(str, Enum):
    """
    Execution operating mode for security actions.
    """

    ENFORCE = "enforce"
    DRY_RUN = "dry_run"
    SIMULATION = "simulation"
    AUDIT_ONLY = "audit_only"


class ResponseStatus(str, Enum):
    """
    Lifecycle status of a response directive.
    """

    PENDING = "pending"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    REJECTED = "rejected"


class EnforcementScope(str, Enum):
    """
    Target infrastructure scope for defensive enforcement.
    """

    NONE = "none"
    HOST = "host"
    NETWORK = "network"
    IDENTITY = "identity"
    APPLICATION = "application"
    DATA = "data"


# ============================================================================
# Utility Functions
# ============================================================================


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _validate_utc(value: datetime, field_name: str) -> None:
    """Enforce datetime presence and explicit timezone awareness."""
    if not isinstance(value, datetime):
        raise ResponseValidationError(
            f"{field_name} must be a datetime instance"
        )

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ResponseValidationError(
            f"{field_name} must be timezone-aware (UTC)"
        )


def _iso(value: datetime) -> str:
    """Format datetime as strict UTC ISO-8601 string."""
    _validate_utc(value, "timestamp")
    return value.astimezone(timezone.utc).isoformat()


def _validate_str(value: Any, name: str) -> str:
    """Validate non-empty string identifier."""
    if not isinstance(value, str) or not value.strip():
        raise ResponseValidationError(
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
# Response Configuration
# ============================================================================


@dataclass(frozen=True)
class ResponseConfig:
    """
    Immutable response execution engine configuration contract.
    """

    engine_id: str
    engine_version: str
    default_mode: ResponseMode = ResponseMode.ENFORCE
    allowed_scopes: tuple[EnforcementScope, ...] = field(
        default_factory=lambda: (
            EnforcementScope.NONE,
            EnforcementScope.HOST,
            EnforcementScope.NETWORK,
            EnforcementScope.IDENTITY,
            EnforcementScope.APPLICATION,
            EnforcementScope.DATA,
        )
    )

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
        if not isinstance(self.default_mode, ResponseMode):
            raise ResponseValidationError("default_mode must be a valid ResponseMode enum")


# ============================================================================
# Response Contract
# ============================================================================


@dataclass(frozen=True)
class ResponseContract:
    """
    Immutable Response Enforcement Directive Contract.

    Represents a verified authorization directive ready for enforcement driver dispatch.
    """

    response_id: str
    decision_id: str
    evaluation_id: str
    target_resource_id: str
    action: DecisionAction
    scope: EnforcementScope
    mode: ResponseMode
    status: ResponseStatus
    created_at: datetime
    parameters: Mapping[str, Any] = field(default_factory=dict)
    provenance_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "response_id",
            _validate_str(self.response_id, "response_id"),
        )
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
            "target_resource_id",
            _validate_str(self.target_resource_id, "target_resource_id"),
        )

        _validate_utc(self.created_at, "created_at")

        if not isinstance(self.action, DecisionAction):
            raise ResponseValidationError("action must be a valid DecisionAction enum")

        if not isinstance(self.scope, EnforcementScope):
            raise ResponseValidationError("scope must be a valid EnforcementScope enum")

        if not isinstance(self.mode, ResponseMode):
            raise ResponseValidationError("mode must be a valid ResponseMode enum")

        if not isinstance(self.status, ResponseStatus):
            raise ResponseValidationError("status must be a valid ResponseStatus enum")

        object.__setattr__(self, "parameters", _freeze(self.parameters))

        if not self.provenance_hash:
            calculated_hash = self._compute_provenance()
            object.__setattr__(self, "provenance_hash", calculated_hash)

    def _compute_provenance(self) -> str:
        """Compute SHA-256 cryptographic provenance of response directive."""
        payload = {
            "response_id": self.response_id,
            "decision_id": self.decision_id,
            "evaluation_id": self.evaluation_id,
            "target_resource_id": self.target_resource_id,
            "action": self.action.value,
            "scope": self.scope.value,
            "mode": self.mode.value,
            "status": self.status.value,
            "created_at": _iso(self.created_at),
            "parameters": _unfreeze(self.parameters),
        }

        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert response contract to JSON-serializable dictionary."""
        return {
            "response_id": self.response_id,
            "decision_id": self.decision_id,
            "evaluation_id": self.evaluation_id,
            "target_resource_id": self.target_resource_id,
            "action": self.action.value,
            "scope": self.scope.value,
            "mode": self.mode.value,
            "status": self.status.value,
            "created_at": _iso(self.created_at),
            "parameters": _unfreeze(self.parameters),
            "provenance_hash": self.provenance_hash,
        }


# ============================================================================
# Response Engine
# ============================================================================


class ADIEResponse:
    """
    Canonical ADIE Response Execution Engine.

    Responsibilities:
    - Validate decision contract legitimacy and non-expiration.
    - Map decision action to concrete enforcement scope.
    - Emit cryptographically bound ResponseContracts for enforcement drivers.
    """

    def __init__(self, config: ResponseConfig | None = None) -> None:
        self._config = (
            config
            if config is not None
            else ResponseConfig(
                engine_id="default-response-engine",
                engine_version="1.0.0",
            )
        )

        self._counter = 0
        self._lock = threading.Lock()

    def create_response_directive(
        self,
        decision_contract: DecisionContract,
        override_mode: ResponseMode | None = None,
        extra_parameters: Mapping[str, Any] | None = None,
    ) -> ResponseContract:
        """
        Validate decision contract and build an enforcement ResponseContract.
        """
        if not isinstance(decision_contract, DecisionContract):
            raise ResponseValidationError("Input must be a valid DecisionContract instance")

        # Security Invariant Check: Fail-Closed Validation
        if not decision_contract.authorized:
            raise ResponseExecutionError(
                f"Cannot create response directive for unauthorized decision '{decision_contract.decision_id}'"
            )

        if decision_contract.status != DecisionStatus.AUTHORIZED:
            raise ResponseExecutionError(
                f"Decision status must be AUTHORIZED, got '{decision_contract.status.value}'"
            )

        if decision_contract.is_expired():
            raise ResponseExecutionError(
                f"Cannot execute expired decision contract '{decision_contract.decision_id}'"
            )

        scope = self._map_action_to_scope(decision_contract.action)
        mode = override_mode if override_mode is not None else self._config.default_mode

        if scope not in self._config.allowed_scopes:
            raise ResponseExecutionError(
                f"Enforcement scope '{scope.value}' is disallowed by engine configuration"
            )

        with self._lock:
            self._counter += 1
            count = self._counter

        created_at = _utc_now()
        response_id = self._generate_response_id(
            decision_contract.decision_id,
            decision_contract.action.value,
            count,
        )

        params = dict(extra_parameters) if extra_parameters else {}
        params["decision_provenance"] = decision_contract.provenance_hash
        params["original_parameters"] = _unfreeze(decision_contract.parameters)

        initial_status = ResponseStatus.PENDING if mode == ResponseMode.ENFORCE else ResponseStatus.SKIPPED

        return ResponseContract(
            response_id=response_id,
            decision_id=decision_contract.decision_id,
            evaluation_id=decision_contract.evaluation_id,
            target_resource_id=decision_contract.target_resource_id,
            action=decision_contract.action,
            scope=scope,
            mode=mode,
            status=initial_status,
            created_at=created_at,
            parameters=params,
        )

    @staticmethod
    def _map_action_to_scope(action: DecisionAction) -> EnforcementScope:
        """Map Decision Action to concrete Enforcement Scope (Fail-Closed)."""
        mapping = {
            DecisionAction.NO_ACTION: EnforcementScope.NONE,
            DecisionAction.LOG_AND_MONITOR: EnforcementScope.APPLICATION,
            DecisionAction.DISPATCH_ALERT: EnforcementScope.APPLICATION,
            DecisionAction.CONTAIN_SESSION: EnforcementScope.IDENTITY,
            DecisionAction.ISOLATE_HOST: EnforcementScope.NETWORK,
            DecisionAction.REJECT_REQUEST: EnforcementScope.APPLICATION,
        }
        if action not in mapping:
            raise ResponseExecutionError(f"Unmapped decision action: '{action}'")
        return mapping[action]

    def _generate_response_id(
        self,
        decision_id: str,
        action: str,
        counter: int,
    ) -> str:
        """Create deterministic SHA-256 backed response contract ID."""
        payload = {
            "counter": counter,
            "decision_id": decision_id,
            "action": action,
            "engine_id": self._config.engine_id,
            "engine_version": self._config.engine_version,
        }

        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = sha256(serialized.encode("utf-8")).hexdigest()
        return f"resp-{digest[:24]}"

    def status(self) -> dict[str, Any]:
        """Return engine status snapshot."""
        with self._lock:
            count = self._counter

        return {
            "module": MODULE_NAME,
            "version": MODULE_VERSION,
            "engine_id": self._config.engine_id,
            "engine_version": self._config.engine_version,
            "default_mode": self._config.default_mode.value,
            "responses_created": count,
        }

    def self_test(self) -> dict[str, Any]:
        """Validate response domain invariants and contracts."""
        tests: dict[str, bool] = {}

        try:
            from datetime import timedelta

            now = _utc_now()
            mock_decision = DecisionContract(
                decision_id="dec-test-1234567890abcdef",
                evaluation_id="eval-test-1234567890abcdef",
                policy_id="pol-test-01",
                action=DecisionAction.ISOLATE_HOST,
                status=DecisionStatus.AUTHORIZED,
                authorized=True,
                created_at=now,
                expires_at=now + timedelta(seconds=300),
                target_resource_id="srv-prod-01",
            )

            directive = self.create_response_directive(mock_decision)

            tests["directive_created"] = isinstance(directive, ResponseContract)
            tests["scope_mapped"] = directive.scope == EnforcementScope.NETWORK
            tests["provenance_hash_valid"] = len(directive.provenance_hash) == 64
            tests["decision_linked"] = directive.decision_id == mock_decision.decision_id

            # Verify immutability
            tests["immutable_contract"] = False
            try:
                directive.status = ResponseStatus.COMPLETED  # type: ignore
            except Exception:
                tests["immutable_contract"] = True

            serialized = directive.to_dict()
            tests["json_serializable"] = isinstance(serialized, dict) and serialized["action"] == "isolate_host"

            passed = all(tests.values())

            return {
                "passed": passed,
                "module": MODULE_NAME,
                "version": MODULE_VERSION,
                "tests": tests,
            }

        except Exception as exc:
            return {
                "passed": False,
                "module": MODULE_NAME,
                "version": MODULE_VERSION,
                "tests": tests,
                "error": type(exc).__name__,
                "error_message": str(exc),
            }


# ============================================================================
# Default Response Engine Instance (Thread-Safe Singleton)
# ============================================================================


_default_response_engine: ADIEResponse | None = None
_response_lock = threading.Lock()


def get_response_engine() -> ADIEResponse:
    """Return process-local default ADIE response engine (Thread-Safe)."""
    global _default_response_engine

    if _default_response_engine is None:
        with _response_lock:
            if _default_response_engine is None:
                _default_response_engine = ADIEResponse()

    return _default_response_engine


def self_test() -> dict[str, Any]:
    """Module-level self test."""
    return ADIEResponse().self_test()


# ============================================================================
# Public API
# ============================================================================


__all__ = [
    "MODULE_NAME",
    "MODULE_VERSION",
    "ADIEResponse",
    "EnforcementScope",
    "ResponseConfig",
    "ResponseContract",
    "ResponseError",
    "ResponseExecutionError",
    "ResponseMode",
    "ResponseStatus",
    "ResponseValidationError",
    "get_response_engine",
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
