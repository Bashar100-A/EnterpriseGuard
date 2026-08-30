"""The immutable ADIE-to-execution boundary contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .execution_contract import (
    CONTRACT_VERSION,
    ContractValidationError,
    ExecutionAction,
    ExecutionIntent,
    freeze,
    normalize_datetime,
    require_id,
    thaw,
    utc_now,
)


MANIFEST_CONTRACT_VERSION = "1.0.0"
CANONICAL_DECISION_CONTRACT = "adie.decision.DecisionContract"
CANONICAL_DECISION_CONTRACT_VERSION = "3.0.1"


class ManifestStatus(str, Enum):
    DRAFT = "DRAFT"
    ELIGIBLE = "ELIGIBLE"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ExecutionEligibility(str, Enum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    ELIGIBLE = "ELIGIBLE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class DecisionReference:
    """Stable reference to the existing canonical ADIE decision contract."""

    decision_id: str
    contract_type: str = CANONICAL_DECISION_CONTRACT
    contract_version: str = CANONICAL_DECISION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", require_id(self.decision_id, "decision_id"))
        if self.contract_type != CANONICAL_DECISION_CONTRACT:
            raise ContractValidationError("contract_type must reference the canonical ADIE DecisionContract")
        object.__setattr__(self, "contract_version", require_id(self.contract_version, "contract_version"))

    def to_dict(self) -> dict[str, str]:
        return {
            "decision_id": self.decision_id,
            "contract_type": self.contract_type,
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True)
class ExecutionManifest:
    """Immutable structural boundary between ADIE and execution."""

    manifest_id: str
    manifest_version: str
    decision_id: str
    event_id: str
    policy_id: str
    policy_evaluation_id: str
    policy_version: str
    prediction_id: str
    model_id: str | None
    model_version: str | None
    model_fingerprint: str | None
    state_id: str
    state_version: str
    state_fingerprint: str | None
    playbook_id: str
    playbook_version: str
    execution_intent_id: str
    tenant_id: str
    environment_id: str
    resource_scope: Mapping[str, Any]
    decision_reference: DecisionReference
    decision_lifecycle: str
    decision_rationale: str
    decision_reason_codes: tuple[str, ...]
    actions: tuple[ExecutionAction, ...]
    action_constraints: Mapping[str, Any]
    required_approval_level: str
    capability: str
    adapter_reference: str
    status: ManifestStatus = ManifestStatus.DRAFT
    eligibility: ExecutionEligibility = ExecutionEligibility.NOT_ELIGIBLE
    checkpoint_id: str | None = None
    rollback_plan_id: str | None = None
    approval_id: str | None = None
    execution_authorization_id: str | None = None
    expires_at: datetime | None = None
    idempotency_key: str = ""
    correlation_id: str = ""
    lineage: Mapping[str, str] = field(default_factory=dict)
    lineage_fingerprint: str = ""
    governance_metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.status, ManifestStatus):
            raise ContractValidationError("status must be a ManifestStatus")
        if not isinstance(self.eligibility, ExecutionEligibility):
            raise ContractValidationError("eligibility must be an ExecutionEligibility")
        for field_name in (
            "manifest_id",
            "manifest_version",
            "decision_id",
            "event_id",
            "policy_id",
            "policy_evaluation_id",
            "policy_version",
            "prediction_id",
            "state_id",
            "state_version",
            "playbook_id",
            "playbook_version",
            "execution_intent_id",
            "tenant_id",
            "environment_id",
            "idempotency_key",
            "correlation_id",
            "decision_lifecycle",
            "required_approval_level",
            "capability",
            "adapter_reference",
        ):
            object.__setattr__(self, field_name, require_id(getattr(self, field_name), field_name))
        for field_name in ("checkpoint_id", "rollback_plan_id", "approval_id", "execution_authorization_id"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, require_id(value, field_name))
        if not isinstance(self.decision_reference, DecisionReference):
            raise ContractValidationError("decision_reference must be a DecisionReference")
        if self.decision_reference.decision_id != self.decision_id:
            raise ContractValidationError("decision_reference.decision_id must match decision_id")
        if not isinstance(self.resource_scope, Mapping):
            raise ContractValidationError("resource_scope must be a mapping")
        object.__setattr__(self, "resource_scope", freeze(self.resource_scope))
        object.__setattr__(self, "action_constraints", freeze(self.action_constraints))
        object.__setattr__(self, "lineage", freeze(self.lineage))
        object.__setattr__(self, "governance_metadata", freeze(self.governance_metadata))
        if self.model_id is not None:
            object.__setattr__(self, "model_id", require_id(self.model_id, "model_id"))
        if self.model_version is not None:
            object.__setattr__(self, "model_version", require_id(self.model_version, "model_version"))
        if self.model_fingerprint is not None:
            object.__setattr__(self, "model_fingerprint", require_id(self.model_fingerprint, "model_fingerprint"))
        if self.state_fingerprint is not None:
            object.__setattr__(self, "state_fingerprint", require_id(self.state_fingerprint, "state_fingerprint"))
        if not isinstance(self.actions, tuple):
            object.__setattr__(self, "actions", tuple(self.actions))
        if any(not isinstance(action, ExecutionAction) for action in self.actions):
            raise ContractValidationError("actions must contain ExecutionAction values")
        if not isinstance(self.decision_reason_codes, tuple):
            object.__setattr__(self, "decision_reason_codes", tuple(self.decision_reason_codes))
        if any(not isinstance(code, str) or not code.strip() for code in self.decision_reason_codes):
            raise ContractValidationError("decision_reason_codes must contain non-empty strings")
        created_at = normalize_datetime(self.created_at, "created_at")
        object.__setattr__(self, "created_at", created_at)
        if self.expires_at is not None:
            expires_at = normalize_datetime(self.expires_at, "expires_at")
            if expires_at <= created_at:
                raise ContractValidationError("expires_at must be later than created_at")
            object.__setattr__(self, "expires_at", expires_at)
        if self.eligibility is ExecutionEligibility.ELIGIBLE and not self.execution_authorization_id:
            raise ContractValidationError("eligible manifests require execution_authorization_id")
        if self.eligibility is ExecutionEligibility.ELIGIBLE and self.status is not ManifestStatus.ELIGIBLE:
            raise ContractValidationError("eligible manifests must have ELIGIBLE status")
        calculated_fingerprint = self._calculate_lineage_fingerprint()
        if self.lineage_fingerprint and self.lineage_fingerprint != calculated_fingerprint:
            raise ContractValidationError("lineage_fingerprint does not match manifest lineage")
        object.__setattr__(self, "lineage_fingerprint", calculated_fingerprint)

    def _calculate_lineage_fingerprint(self) -> str:
        payload = {
            "event_id": self.event_id,
            "state_id": self.state_id,
            "state_version": self.state_version,
            "prediction_id": self.prediction_id,
            "policy_evaluation_id": self.policy_evaluation_id,
            "decision_id": self.decision_id,
            "checkpoint_id": self.checkpoint_id,
            "playbook_id": self.playbook_id,
            "rollback_plan_id": self.rollback_plan_id,
            "execution_intent_id": self.execution_intent_id,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @classmethod
    def from_intent(
        cls,
        *,
        manifest_id: str,
        manifest_version: str,
        intent: ExecutionIntent,
        event_id: str,
        policy_id: str,
        policy_evaluation_id: str,
        policy_version: str,
        prediction_id: str,
        playbook_version: str,
        state_id: str,
        state_version: str,
        tenant_id: str,
        environment_id: str,
        resource_scope: Mapping[str, Any],
        decision_reference: DecisionReference,
        decision_lifecycle: str,
        model_id: str | None = None,
        model_version: str | None = None,
        model_fingerprint: str | None = None,
        state_fingerprint: str | None = None,
        decision_rationale: str = "",
        decision_reason_codes: tuple[str, ...] = (),
        required_approval_level: str = "NONE",
        capability: str = "UNSPECIFIED",
        adapter_reference: str = "UNSPECIFIED",
        checkpoint_id: str | None = None,
        rollback_plan_id: str | None = None,
        approval_id: str | None = None,
        execution_authorization_id: str | None = None,
        expires_at: datetime | None = None,
        idempotency_key: str = "manifest-idempotency",
        correlation_id: str = "manifest-correlation",
        lineage: Mapping[str, str] | None = None,
        governance_metadata: Mapping[str, Any] | None = None,
    ) -> "ExecutionManifest":
        if not isinstance(intent, ExecutionIntent):
            raise ContractValidationError("intent must be an ExecutionIntent")
        if intent.decision_id != decision_reference.decision_id:
            raise ContractValidationError("intent.decision_id must match decision_reference.decision_id")
        if intent.approval_requirement.value == "REQUIRED" and not approval_id:
            raise ContractValidationError("approval is required by the execution intent")
        return cls(
            manifest_id=manifest_id,
            manifest_version=manifest_version,
            decision_id=decision_reference.decision_id,
            event_id=event_id,
            policy_id=policy_id,
            policy_evaluation_id=policy_evaluation_id,
            policy_version=policy_version,
            prediction_id=prediction_id,
            model_id=model_id,
            model_version=model_version,
            model_fingerprint=model_fingerprint,
            state_id=state_id,
            state_version=state_version,
            state_fingerprint=state_fingerprint,
            playbook_id=intent.playbook_id,
            playbook_version=playbook_version,
            execution_intent_id=intent.execution_intent_id,
            tenant_id=tenant_id,
            environment_id=environment_id,
            resource_scope=resource_scope,
            decision_reference=decision_reference,
            decision_lifecycle=decision_lifecycle,
            decision_rationale=decision_rationale,
            decision_reason_codes=decision_reason_codes,
            actions=intent.actions,
            action_constraints={
                action.action_id: [constraint.to_dict() for constraint in action.constraints]
                for action in intent.actions
            },
            required_approval_level=required_approval_level,
            capability=capability,
            adapter_reference=adapter_reference,
            status=ManifestStatus.DRAFT,
            eligibility=ExecutionEligibility.NOT_ELIGIBLE,
            checkpoint_id=checkpoint_id,
            rollback_plan_id=rollback_plan_id,
            approval_id=approval_id,
            execution_authorization_id=execution_authorization_id,
            expires_at=expires_at,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            lineage=lineage or {},
            governance_metadata=governance_metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "manifest_version": self.manifest_version,
            "decision_id": self.decision_id,
            "decision_reference": self.decision_reference.to_dict(),
            "event_id": self.event_id,
            "policy_id": self.policy_id,
            "policy_evaluation_id": self.policy_evaluation_id,
            "policy_version": self.policy_version,
            "prediction_id": self.prediction_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "model_fingerprint": self.model_fingerprint,
            "state_id": self.state_id,
            "state_version": self.state_version,
            "state_fingerprint": self.state_fingerprint,
            "checkpoint_id": self.checkpoint_id,
            "playbook_id": self.playbook_id,
            "playbook_version": self.playbook_version,
            "rollback_plan_id": self.rollback_plan_id,
            "execution_intent_id": self.execution_intent_id,
            "decision_lifecycle": self.decision_lifecycle,
            "decision_rationale": self.decision_rationale,
            "decision_reason_codes": list(self.decision_reason_codes),
            "actions": [action.to_dict() for action in self.actions],
            "action_constraints": thaw(self.action_constraints),
            "required_approval_level": self.required_approval_level,
            "capability": self.capability,
            "adapter_reference": self.adapter_reference,
            "approval_id": self.approval_id,
            "execution_authorization_id": self.execution_authorization_id,
            "tenant_id": self.tenant_id,
            "environment_id": self.environment_id,
            "resource_scope": thaw(self.resource_scope),
            "status": self.status.value,
            "eligibility": self.eligibility.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "lineage": thaw(self.lineage),
            "lineage_fingerprint": self.lineage_fingerprint,
            "governance_metadata": thaw(self.governance_metadata),
            "created_at": self.created_at.isoformat(),
        }


__all__ = [
    "MANIFEST_CONTRACT_VERSION",
    "CANONICAL_DECISION_CONTRACT",
    "CANONICAL_DECISION_CONTRACT_VERSION",
    "ManifestStatus",
    "ExecutionEligibility",
    "DecisionReference",
    "ExecutionManifest",
]
