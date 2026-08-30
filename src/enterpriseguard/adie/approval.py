"""Immutable domain contract for human approval."""

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


APPROVAL_CONTRACT_VERSION = "1.0.0"


class ApprovalStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class Approval:
    """An approval record; it is not a policy decision or execution grant."""

    approval_id: str
    status: ApprovalStatus
    approver_identity_ref: str
    required_approval_level: str
    decision_id: str
    manifest_id: str | None = None
    scope: Mapping[str, Any] = field(default_factory=dict)
    issued_at: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None
    reason: str = ""
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, ApprovalStatus):
            raise ContractValidationError("status must be an ApprovalStatus")
        object.__setattr__(self, "approval_id", require_id(self.approval_id, "approval_id"))
        object.__setattr__(self, "approver_identity_ref", require_id(self.approver_identity_ref, "approver_identity_ref"))
        object.__setattr__(self, "required_approval_level", require_id(self.required_approval_level, "required_approval_level"))
        object.__setattr__(self, "decision_id", require_id(self.decision_id, "decision_id"))
        if self.manifest_id is not None:
            object.__setattr__(self, "manifest_id", require_id(self.manifest_id, "manifest_id"))
        issued_at = normalize_datetime(self.issued_at, "issued_at")
        object.__setattr__(self, "issued_at", issued_at)
        if self.expires_at is not None:
            expires_at = normalize_datetime(self.expires_at, "expires_at")
            if expires_at <= issued_at:
                raise ContractValidationError("expires_at must be later than issued_at")
            object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "scope", freeze(self.scope))
        object.__setattr__(self, "context", freeze(self.context))
        if not isinstance(self.reason, str):
            raise ContractValidationError("reason must be a string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "status": self.status.value,
            "approver_identity_ref": self.approver_identity_ref,
            "required_approval_level": self.required_approval_level,
            "decision_id": self.decision_id,
            "manifest_id": self.manifest_id,
            "scope": thaw(self.scope),
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "reason": self.reason,
            "context": thaw(self.context),
        }


__all__ = ["APPROVAL_CONTRACT_VERSION", "ApprovalStatus", "Approval"]
