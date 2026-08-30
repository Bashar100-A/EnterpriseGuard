"""
EnterpriseGuard ADIE - Rollback
================================

Rollback planning and state restoration contract for ADIE.

Responsibilities
----------------
- Represent rollback targets and restoration plans.
- Reference immutable ADIE checkpoints.
- Validate rollback requests.
- Verify checkpoint integrity before restoration planning.
- Prevent unauthorized or destructive rollback operations.
- Provide deterministic rollback planning.
- Preserve auditability and immutability.

Important Safety Boundary
-------------------------
This module DOES NOT execute security actions.

It only:
    1. validates rollback requests,
    2. resolves a checkpoint,
    3. verifies checkpoint integrity,
    4. creates an immutable rollback plan.

Actual restoration must be performed by a separate,
explicitly authorized execution layer.

Architecture
------------

    ADIE State
        |
        v
    Checkpoint
        |
        v
    RollbackRequest
        |
        v
    RollbackEngine
        |
        +---- validation
        +---- integrity verification
        +---- planning
        |
        v
    RollbackPlan
        |
        v
    Authorized Execution Layer

Security Principles
-------------------
- Fail closed.
- No arbitrary commands.
- No shell execution.
- No direct filesystem mutation.
- No destructive actions.
- Immutable results.
- Deterministic fingerprints.
- Explicit authorization boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Optional, Protocol, Tuple


__all__ = [
    "ROLLBACK_VERSION",
    "RollbackError",
    "RollbackValidationError",
    "RollbackIntegrityError",
    "RollbackAuthorizationError",
    "RollbackNotFoundError",
    "RollbackStatus",
    "RollbackScope",
    "RollbackRequest",
    "RollbackTarget",
    "RollbackPlan",
    "RollbackEngine",
]


ROLLBACK_VERSION = "1.0.0"


# ============================================================================
# Exceptions
# ============================================================================


class RollbackError(Exception):
    """Base exception for ADIE rollback errors."""


class RollbackValidationError(RollbackError):
    """Raised when a rollback request is invalid."""


class RollbackIntegrityError(RollbackError):
    """Raised when checkpoint integrity cannot be trusted."""


class RollbackAuthorizationError(RollbackError):
    """Raised when rollback authorization is insufficient."""


class RollbackNotFoundError(RollbackError):
    """Raised when the requested checkpoint does not exist."""


# ============================================================================
# Enums
# ============================================================================


class RollbackStatus(str, Enum):
    """Lifecycle state of a rollback plan."""

    PLANNED = "planned"
    BLOCKED = "blocked"
    INVALID = "invalid"


class RollbackScope(str, Enum):
    """Supported rollback scopes."""

    FULL_STATE = "full_state"
    NETWORK = "network"
    IDENTITY = "identity"
    CONFIGURATION = "configuration"
    DETECTION = "detection"
    RESPONSE = "response"


# ============================================================================
# Checkpoint Protocol
# ============================================================================


class CheckpointProvider(Protocol):
    """
    Minimal protocol required from a checkpoint provider.

    The actual checkpoint implementation remains decoupled from
    this module.
    """

    def get(self, checkpoint_id: str) -> Any:
        """Return a checkpoint or None."""

    def verify_integrity(self, checkpoint_id: str) -> bool:
        """Verify checkpoint integrity."""


# ============================================================================
# Immutable Data Structures
# ============================================================================


@dataclass(frozen=True)
class RollbackRequest:
    """
    Immutable rollback request.

    This is a request for planning only.
    """

    checkpoint_id: str
    scope: RollbackScope = RollbackScope.FULL_STATE
    requested_by: str = "adie"
    reason: str = ""
    authorization_token: Optional[str] = None
    dry_run: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        checkpoint_id = self.checkpoint_id.strip()

        if not checkpoint_id:
            raise RollbackValidationError(
                "checkpoint_id must not be empty."
            )

        if len(checkpoint_id) > 256:
            raise RollbackValidationError(
                "checkpoint_id exceeds maximum length."
            )

        requested_by = self.requested_by.strip()

        if not requested_by:
            raise RollbackValidationError(
                "requested_by must not be empty."
            )

        if len(requested_by) > 256:
            raise RollbackValidationError(
                "requested_by exceeds maximum length."
            )

        reason = self.reason.strip()

        if len(reason) > 2000:
            raise RollbackValidationError(
                "reason exceeds maximum length."
            )

        if not isinstance(self.scope, RollbackScope):
            raise RollbackValidationError(
                "scope must be a RollbackScope."
            )

        if not isinstance(self.dry_run, bool):
            raise RollbackValidationError(
                "dry_run must be boolean."
            )

        if self.authorization_token is not None:
            token = self.authorization_token.strip()

            if not token:
                raise RollbackValidationError(
                    "authorization_token cannot be empty."
                )

        object.__setattr__(
            self,
            "checkpoint_id",
            checkpoint_id,
        )

        object.__setattr__(
            self,
            "requested_by",
            requested_by,
        )

        object.__setattr__(
            self,
            "reason",
            reason,
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


@dataclass(frozen=True)
class RollbackTarget:
    """
    Immutable description of the state targeted by rollback.
    """

    checkpoint_id: str
    checkpoint_fingerprint: str
    scope: RollbackScope
    state_version: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self) -> None:
        checkpoint_id = self.checkpoint_id.strip()
        fingerprint = self.checkpoint_fingerprint.strip()

        if not checkpoint_id:
            raise RollbackValidationError(
                "RollbackTarget checkpoint_id is required."
            )

        if not fingerprint:
            raise RollbackValidationError(
                "RollbackTarget fingerprint is required."
            )

        if len(fingerprint) < 16:
            raise RollbackValidationError(
                "RollbackTarget fingerprint is invalid."
            )

        if not isinstance(self.scope, RollbackScope):
            raise RollbackValidationError(
                "RollbackTarget scope must be RollbackScope."
            )

        object.__setattr__(
            self,
            "checkpoint_id",
            checkpoint_id,
        )

        object.__setattr__(
            self,
            "checkpoint_fingerprint",
            fingerprint,
        )


@dataclass(frozen=True)
class RollbackPlan:
    """
    Immutable rollback plan.

    The plan describes WHAT would be restored, but never performs
    the restoration.
    """

    plan_id: str
    request: RollbackRequest
    target: RollbackTarget
    status: RollbackStatus
    created_at: str
    executes_security_actions: bool = False
    destructive_actions_allowed: bool = False
    requires_authorized_executor: bool = True
    integrity_verified: bool = False
    reason: str = ""
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.plan_id.strip():
            raise RollbackValidationError(
                "plan_id must not be empty."
            )

        if not isinstance(self.request, RollbackRequest):
            raise RollbackValidationError(
                "request must be RollbackRequest."
            )

        if not isinstance(self.target, RollbackTarget):
            raise RollbackValidationError(
                "target must be RollbackTarget."
            )

        if not isinstance(self.status, RollbackStatus):
            raise RollbackValidationError(
                "status must be RollbackStatus."
            )

        if self.executes_security_actions:
            raise RollbackValidationError(
                "RollbackPlan cannot execute security actions."
            )

        if self.destructive_actions_allowed:
            raise RollbackValidationError(
                "Destructive rollback actions are forbidden."
            )

        if not isinstance(self.integrity_verified, bool):
            raise RollbackValidationError(
                "integrity_verified must be boolean."
            )

        if not self.fingerprint:
            object.__setattr__(
                self,
                "fingerprint",
                _fingerprint_plan(self),
            )


# ============================================================================
# Rollback Engine
# ============================================================================


class RollbackEngine:
    """
    ADIE rollback planning engine.

    Safety boundary:
        This class NEVER executes rollback operations.

    It produces immutable RollbackPlan objects for a separate
    authorized executor.
    """

    VERSION = ROLLBACK_VERSION

    executes_security_actions = False
    destructive_actions_allowed = False

    def __init__(
        self,
        checkpoint_provider: CheckpointProvider,
        *,
        require_authorization: bool = True,
    ) -> None:
        if checkpoint_provider is None:
            raise RollbackValidationError(
                "checkpoint_provider is required."
            )

        if not callable(
            getattr(checkpoint_provider, "get", None)
        ):
            raise RollbackValidationError(
                "checkpoint_provider must provide get()."
            )

        if not callable(
            getattr(checkpoint_provider, "verify_integrity", None)
        ):
            raise RollbackValidationError(
                "checkpoint_provider must provide "
                "verify_integrity()."
            )

        if not isinstance(require_authorization, bool):
            raise RollbackValidationError(
                "require_authorization must be boolean."
            )

        self._checkpoint_provider = checkpoint_provider
        self._require_authorization = require_authorization

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan(
        self,
        request: RollbackRequest,
    ) -> RollbackPlan:
        """
        Validate a rollback request and create a rollback plan.

        No state is modified.
        No command is executed.
        No security action is performed.
        """

        if not isinstance(request, RollbackRequest):
            raise RollbackValidationError(
                "request must be RollbackRequest."
            )

        if self._require_authorization:
            self._validate_authorization(request)

        checkpoint = self._checkpoint_provider.get(
            request.checkpoint_id
        )

        if checkpoint is None:
            raise RollbackNotFoundError(
                f"Checkpoint not found: {request.checkpoint_id}"
            )

        integrity_verified = bool(
            self._checkpoint_provider.verify_integrity(
                request.checkpoint_id
            )
        )

        if not integrity_verified:
            raise RollbackIntegrityError(
                "Checkpoint integrity verification failed."
            )

        target = self._build_target(
            request,
            checkpoint,
        )

        plan_id = self._build_plan_id(
            request,
            target,
        )

        created_at = _utc_now()

        plan = RollbackPlan(
            plan_id=plan_id,
            request=request,
            target=target,
            status=RollbackStatus.PLANNED,
            created_at=created_at,
            executes_security_actions=False,
            destructive_actions_allowed=False,
            requires_authorized_executor=True,
            integrity_verified=True,
            reason=request.reason,
        )

        return plan

    def validate(
        self,
        request: RollbackRequest,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a rollback request without creating a plan.

        Returns:
            (True, None) when valid.
            (False, reason) when invalid.
        """

        try:
            if not isinstance(request, RollbackRequest):
                return (
                    False,
                    "request must be RollbackRequest",
                )

            if self._require_authorization:
                self._validate_authorization(request)

            checkpoint = self._checkpoint_provider.get(
                request.checkpoint_id
            )

            if checkpoint is None:
                return (
                    False,
                    "checkpoint_not_found",
                )

            if not self._checkpoint_provider.verify_integrity(
                request.checkpoint_id
            ):
                return (
                    False,
                    "checkpoint_integrity_failed",
                )

            return True, None

        except RollbackError as exc:
            return False, str(exc)

        except Exception:
            return (
                False,
                "rollback_validation_failed",
            )

    def can_rollback(
        self,
        request: RollbackRequest,
    ) -> bool:
        """
        Return whether a rollback request is safely planable.
        """

        valid, _ = self.validate(request)
        return valid

    def describe(
        self,
        plan: RollbackPlan,
    ) -> Mapping[str, Any]:
        """
        Return a safe, serializable representation of a plan.
        """

        if not isinstance(plan, RollbackPlan):
            raise RollbackValidationError(
                "plan must be RollbackPlan."
            )

        return {
            "plan_id": plan.plan_id,
            "status": plan.status.value,
            "checkpoint_id": plan.target.checkpoint_id,
            "checkpoint_fingerprint": (
                plan.target.checkpoint_fingerprint
            ),
            "scope": plan.target.scope.value,
            "state_version": plan.target.state_version,
            "created_at": plan.created_at,
            "integrity_verified": plan.integrity_verified,
            "executes_security_actions": (
                plan.executes_security_actions
            ),
            "destructive_actions_allowed": (
                plan.destructive_actions_allowed
            ),
            "requires_authorized_executor": (
                plan.requires_authorized_executor
            ),
            "reason": plan.reason,
            "fingerprint": plan.fingerprint,
        }

    def status(self) -> Mapping[str, Any]:
        """
        Return engine status.
        """

        return {
            "module": "adie.rollback",
            "version": self.VERSION,
            "requires_authorization": self._require_authorization,
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
            "planning_only": True,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_authorization(
        self,
        request: RollbackRequest,
    ) -> None:
        """
        Enforce the authorization boundary.

        For ADIE Foundation, a non-empty authorization token is
        required for rollback planning.

        The token is never persisted in the plan.
        """

        if request.authorization_token is None:
            raise RollbackAuthorizationError(
                "Rollback authorization is required."
            )

        if not request.authorization_token.strip():
            raise RollbackAuthorizationError(
                "Rollback authorization token is empty."
            )

    def _build_target(
        self,
        request: RollbackRequest,
        checkpoint: Any,
    ) -> RollbackTarget:
        fingerprint = _extract_checkpoint_fingerprint(
            checkpoint
        )

        state_version = _extract_optional_value(
            checkpoint,
            "state_version",
        )

        created_at = _extract_optional_value(
            checkpoint,
            "created_at",
        )

        return RollbackTarget(
            checkpoint_id=request.checkpoint_id,
            checkpoint_fingerprint=fingerprint,
            scope=request.scope,
            state_version=(
                str(state_version)
                if state_version is not None
                else None
            ),
            created_at=(
                str(created_at)
                if created_at is not None
                else None
            ),
        )

    def _build_plan_id(
        self,
        request: RollbackRequest,
        target: RollbackTarget,
    ) -> str:
        material = "|".join(
            [
                request.checkpoint_id,
                request.scope.value,
                request.requested_by,
                target.checkpoint_fingerprint,
            ]
        )

        digest = hashlib.sha256(
            material.encode("utf-8")
        ).hexdigest()

        return f"rb-{digest[:24]}"


# ============================================================================
# Serialization / Fingerprinting Helpers
# ============================================================================


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze_mapping(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise RollbackValidationError(
            "metadata must be a mapping."
        )

    # JSON round-trip provides a deterministic detached representation
    # for normal JSON-compatible metadata.
    try:
        normalized = json.loads(
            json.dumps(
                dict(value),
                sort_keys=True,
                default=str,
            )
        )
    except Exception as exc:
        raise RollbackValidationError(
            "metadata cannot be normalized."
        ) from exc

    return _ImmutableDict(normalized)


class _ImmutableDict(dict):
    """Minimal immutable dictionary implementation."""

    def _blocked(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "This mapping is immutable."
        )

    __setitem__ = _blocked
    __delitem__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked
    setdefault = _blocked
    update = _blocked


def _extract_optional_value(
    checkpoint: Any,
    key: str,
) -> Any:
    if isinstance(checkpoint, Mapping):
        return checkpoint.get(key)

    return getattr(
        checkpoint,
        key,
        None,
    )


def _extract_checkpoint_fingerprint(
    checkpoint: Any,
) -> str:
    candidates = (
        "fingerprint",
        "integrity_hash",
        "hash",
        "checkpoint_fingerprint",
    )

    for key in candidates:
        value = _extract_optional_value(
            checkpoint,
            key,
        )

        if value is not None:
            text = str(value).strip()

            if text:
                return text

    # If the checkpoint implementation does not expose a fingerprint,
    # derive a deterministic fingerprint from its public representation.
    try:
        if isinstance(checkpoint, Mapping):
            material = json.dumps(
                dict(checkpoint),
                sort_keys=True,
                default=str,
            )
        elif hasattr(checkpoint, "to_dict"):
            material = json.dumps(
                checkpoint.to_dict(),
                sort_keys=True,
                default=str,
            )
        else:
            material = repr(checkpoint)

    except Exception as exc:
        raise RollbackIntegrityError(
            "Unable to derive checkpoint fingerprint."
        ) from exc

    return hashlib.sha256(
        material.encode("utf-8")
    ).hexdigest()


def _fingerprint_plan(
    plan: RollbackPlan,
) -> str:
    material = {
        "plan_id": plan.plan_id,
        "checkpoint_id": plan.target.checkpoint_id,
        "checkpoint_fingerprint": (
            plan.target.checkpoint_fingerprint
        ),
        "scope": plan.target.scope.value,
        "status": plan.status.value,
        "integrity_verified": plan.integrity_verified,
        "executes_security_actions": (
            plan.executes_security_actions
        ),
        "destructive_actions_allowed": (
            plan.destructive_actions_allowed
        ),
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
# Self-Test
# ============================================================================


class _SelfTestCheckpointProvider:
    """Minimal deterministic checkpoint provider for self-test."""

    def __init__(self) -> None:
        self._checkpoints = {
            "cp-test-001": {
                "checkpoint_id": "cp-test-001",
                "state_version": "1",
                "created_at": "2026-01-01T00:00:00+00:00",
                "fingerprint": (
                    "0123456789abcdef"
                    "0123456789abcdef"
                ),
            }
        }

    def get(self, checkpoint_id: str) -> Any:
        return self._checkpoints.get(checkpoint_id)

    def verify_integrity(
        self,
        checkpoint_id: str,
    ) -> bool:
        return checkpoint_id in self._checkpoints


def self_test() -> Mapping[str, Any]:
    """
    Run a lightweight deterministic self-test.

    The self-test must never perform a security action.
    """

    tests = {
        "request_creation": False,
        "checkpoint_resolution": False,
        "integrity_verification": False,
        "rollback_planning": False,
        "immutable_plan": False,
        "authorization_boundary": False,
        "execution_safety": False,
        "destructive_action_block": False,
    }

    try:
        provider = _SelfTestCheckpointProvider()

        engine = RollbackEngine(
            provider,
            require_authorization=True,
        )

        request = RollbackRequest(
            checkpoint_id="cp-test-001",
            scope=RollbackScope.FULL_STATE,
            requested_by="self-test",
            reason="ADIE rollback self-test",
            authorization_token="test-authorization",
            dry_run=True,
        )

        tests["request_creation"] = True

        valid, reason = engine.validate(request)

        if valid and reason is None:
            tests["checkpoint_resolution"] = True
            tests["integrity_verification"] = True

        plan = engine.plan(request)

        tests["rollback_planning"] = (
            plan.status == RollbackStatus.PLANNED
            and plan.integrity_verified
        )

        try:
            plan.request.metadata["blocked"] = True
            tests["immutable_plan"] = False
        except (TypeError, AttributeError):
            tests["immutable_plan"] = True

        unauthorized = RollbackRequest(
            checkpoint_id="cp-test-001",
            scope=RollbackScope.FULL_STATE,
            requested_by="self-test",
            reason="unauthorized test",
            authorization_token=None,
            dry_run=True,
        )

        tests["authorization_boundary"] = (
            not engine.can_rollback(unauthorized)
        )

        tests["execution_safety"] = (
            engine.executes_security_actions is False
            and plan.executes_security_actions is False
        )

        tests["destructive_action_block"] = (
            engine.destructive_actions_allowed is False
            and plan.destructive_actions_allowed is False
        )

        passed = all(tests.values())

        return {
            "passed": passed,
            "module": "adie.rollback",
            "version": ROLLBACK_VERSION,
            "rollback_test_passed": passed,
            "tests": tests,
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    except Exception as exc:
        return {
            "passed": False,
            "module": "adie.rollback",
            "version": ROLLBACK_VERSION,
            "rollback_test_passed": False,
            "tests": tests,
            "error": str(exc),
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }


# ============================================================================
# Module Entry Point
# ============================================================================


if __name__ == "__main__":
    print(
        json.dumps(
            self_test(),
            indent=2,
            sort_keys=True,
        )
    )