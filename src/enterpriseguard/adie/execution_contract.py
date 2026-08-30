"""Dependency-light contracts for the ADIE-to-execution boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping


CONTRACT_VERSION = "1.0.0"


class ContractValidationError(ValueError):
    """Raised when a contract contains invalid structural data."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ContractValidationError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ContractValidationError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def require_id(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def require_non_negative(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractValidationError(f"{field_name} must be a non-negative integer")
    return value


def require_probability(value: float, field_name: str) -> float:
    if isinstance(value, bool):
        raise ContractValidationError(f"{field_name} cannot be boolean")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(f"{field_name} must be numeric") from exc
    if not isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ContractValidationError(f"{field_name} must be finite and between 0 and 1")
    return numeric


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(freeze(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, frozenset, set)):
        return [thaw(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


class ExecutionMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    MANUAL_APPROVAL = "MANUAL_APPROVAL"
    AUTOMATIC = "AUTOMATIC"


class ApprovalRequirement(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"


@dataclass(frozen=True)
class ActionConstraint:
    """Declarative constraint; it grants no authorization."""

    name: str
    value: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", require_id(self.name, "name"))
        object.__setattr__(self, "value", freeze(self.value))

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": thaw(self.value)}


@dataclass(frozen=True)
class ExecutionAction:
    """One declarative action requested by an execution intent."""

    action_id: str
    action_type: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    constraints: tuple[ActionConstraint, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_id", require_id(self.action_id, "action_id"))
        object.__setattr__(self, "action_type", require_id(self.action_type, "action_type"))
        object.__setattr__(self, "parameters", freeze(self.parameters))
        if not isinstance(self.constraints, tuple):
            object.__setattr__(self, "constraints", tuple(self.constraints))
        if any(not isinstance(item, ActionConstraint) for item in self.constraints):
            raise ContractValidationError("constraints must contain ActionConstraint values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "parameters": thaw(self.parameters),
            "constraints": [item.to_dict() for item in self.constraints],
        }


@dataclass(frozen=True)
class ExecutionIntent:
    """Declarative downstream intent derived from an ADIE decision and playbook."""

    execution_intent_id: str
    decision_id: str
    playbook_id: str
    mode: ExecutionMode = ExecutionMode.DRY_RUN
    approval_requirement: ApprovalRequirement = ApprovalRequirement.REQUIRED
    actions: tuple[ExecutionAction, ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ExecutionMode):
            raise ContractValidationError("mode must be an ExecutionMode")
        if not isinstance(self.approval_requirement, ApprovalRequirement):
            raise ContractValidationError("approval_requirement must be an ApprovalRequirement")
        object.__setattr__(self, "execution_intent_id", require_id(self.execution_intent_id, "execution_intent_id"))
        object.__setattr__(self, "decision_id", require_id(self.decision_id, "decision_id"))
        object.__setattr__(self, "playbook_id", require_id(self.playbook_id, "playbook_id"))
        object.__setattr__(self, "created_at", normalize_datetime(self.created_at, "created_at"))
        if self.expires_at is not None:
            expires_at = normalize_datetime(self.expires_at, "expires_at")
            if expires_at <= self.created_at:
                raise ContractValidationError("expires_at must be later than created_at")
            object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "metadata", freeze(self.metadata))
        if not isinstance(self.actions, tuple):
            object.__setattr__(self, "actions", tuple(self.actions))
        if any(not isinstance(item, ExecutionAction) for item in self.actions):
            raise ContractValidationError("actions must contain ExecutionAction values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_intent_id": self.execution_intent_id,
            "decision_id": self.decision_id,
            "playbook_id": self.playbook_id,
            "mode": self.mode.value,
            "approval_requirement": self.approval_requirement.value,
            "actions": [item.to_dict() for item in self.actions],
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": thaw(self.metadata),
        }


__all__ = [
    "CONTRACT_VERSION",
    "ContractValidationError",
    "ExecutionMode",
    "ApprovalRequirement",
    "ActionConstraint",
    "ExecutionAction",
    "ExecutionIntent",
]
