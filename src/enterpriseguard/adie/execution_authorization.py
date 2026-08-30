"""Immutable domain contract for execution authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from .execution_contract import (
    ContractValidationError,
    freeze,
    normalize_datetime,
    require_id,
    thaw,
    utc_now,
)


EXECUTION_AUTHORIZATION_CONTRACT_VERSION = "1.0.0"


class ExecutionAuthorizationStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class ExecutionAuthorization:
    """Structural authorization evidence; it grants no process privilege."""

    execution_authorization_id: str
    status: ExecutionAuthorizationStatus
    decision_id: str
    tenant_id: str
    environment_id: str
    resource_id: str
    capability: str
    action_type: str
    authorized_by_identity_ref: str
    issued_at: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None
    approval_id: str | None = None
    constraints: Mapping[str, Any] = field(default_factory=dict)
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.status, ExecutionAuthorizationStatus):
            raise ContractValidationError("status must be an ExecutionAuthorizationStatus")
        for field_name in (
            "execution_authorization_id",
            "decision_id",
            "tenant_id",
            "environment_id",
            "resource_id",
            "capability",
            "action_type",
            "authorized_by_identity_ref",
        ):
            object.__setattr__(self, field_name, require_id(getattr(self, field_name), field_name))
        if self.approval_id is not None:
            object.__setattr__(self, "approval_id", require_id(self.approval_id, "approval_id"))
        issued_at = normalize_datetime(self.issued_at, "issued_at")
        object.__setattr__(self, "issued_at", issued_at)
        if self.expires_at is not None:
            expires_at = normalize_datetime(self.expires_at, "expires_at")
            if expires_at <= issued_at:
                raise ContractValidationError("expires_at must be later than issued_at")
            object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "constraints", freeze(self.constraints))
        if not isinstance(self.reason, str):
            raise ContractValidationError("reason must be a string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_authorization_id": self.execution_authorization_id,
            "status": self.status.value,
            "decision_id": self.decision_id,
            "tenant_id": self.tenant_id,
            "environment_id": self.environment_id,
            "resource_id": self.resource_id,
            "capability": self.capability,
            "action_type": self.action_type,
            "authorized_by_identity_ref": self.authorized_by_identity_ref,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "approval_id": self.approval_id,
            "constraints": thaw(self.constraints),
            "reason": self.reason,
        }


__all__ = [
    "EXECUTION_AUTHORIZATION_CONTRACT_VERSION",
    "ExecutionAuthorizationStatus",
    "ExecutionAuthorization",
]
