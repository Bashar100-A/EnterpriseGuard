"""
EnterpriseGuard ADIE - Governance
=================================

Adaptive Defense Intelligence Engine.

Governance and trust-boundary enforcement layer.

Responsibilities
-----------------
- Define ADIE component responsibilities.
- Validate security control-plane boundaries.
- Register module capabilities.
- Detect unauthorized execution authority.
- Preserve architectural contracts.
- Provide governance evidence.
- Generate immutable governance reports.

Important Safety Boundary
-------------------------
This module DOES NOT:

- execute security actions,
- modify system state,
- modify models,
- execute rollback,
- execute playbooks.

It only validates governance contracts.

Architecture
------------

              ADIE Control Plane

                    Governance
                        |
        +---------------+---------------+
        |               |               |
      State        Intelligence      Response Boundary
        |               |               |
        v               v               v

    Prediction ---> Policy ---> Decision ---> Playbook
                                  |
                                  v
                              Checkpoint
                                  |
                                  v
                          Rollback Planning
                                  |
                                  v
                              Feedback


Security Principles
-------------------
- Least authority.
- Explicit capability declaration.
- Fail closed.
- No hidden execution paths.
- Immutable governance results.
- Deterministic fingerprints.
- Audit-ready output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Optional


__all__ = [
    "GOVERNANCE_VERSION",
    "GovernanceError",
    "GovernanceValidationError",
    "Capability",
    "ComponentType",
    "ComponentContract",
    "GovernanceReport",
    "GovernanceEngine",
    "self_test",
]


GOVERNANCE_VERSION = "1.0.0"


# ============================================================================
# Exceptions
# ============================================================================


class GovernanceError(Exception):
    """Base governance exception."""


class GovernanceValidationError(GovernanceError):
    """Raised when a governance contract is invalid."""


# ============================================================================
# Enums
# ============================================================================


class Capability(str, Enum):
    """
    Allowed ADIE capabilities.
    """

    READ_STATE = "read_state"
    CREATE_PREDICTION = "create_prediction"
    EVALUATE_POLICY = "evaluate_policy"
    CREATE_DECISION = "create_decision"
    PLAN_PLAYBOOK = "plan_playbook"
    CREATE_CHECKPOINT = "create_checkpoint"
    PLAN_ROLLBACK = "plan_rollback"
    GENERATE_FEEDBACK = "generate_feedback"


class ComponentType(str, Enum):
    """
    ADIE component categories.
    """

    STATE = "state"
    PREDICTION = "prediction"
    POLICY = "policy"
    DECISION = "decision"
    PLAYBOOK = "playbook"
    CHECKPOINT = "checkpoint"
    ROLLBACK = "rollback"
    FEEDBACK = "feedback"
    ORCHESTRATOR = "orchestrator"


# ============================================================================
# Immutable Governance Contracts
# ============================================================================


@dataclass(frozen=True)
class ComponentContract:
    """
    Immutable declaration of an ADIE component.

    A component must explicitly declare:
    - identity,
    - type,
    - capabilities,
    - execution authority.
    """

    component_id: str
    component_type: ComponentType
    capabilities: tuple[Capability, ...]
    executes_security_actions: bool = False
    modifies_system_state: bool = False
    modifies_models: bool = False
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:

        if not self.component_id.strip():
            raise GovernanceValidationError(
                "component_id is required."
            )

        if not isinstance(
            self.component_type,
            ComponentType,
        ):
            raise GovernanceValidationError(
                "component_type must be ComponentType."
            )

        if not isinstance(
            self.capabilities,
            tuple,
        ):
            raise GovernanceValidationError(
                "capabilities must be tuple."
            )

        for capability in self.capabilities:
            if not isinstance(
                capability,
                Capability,
            ):
                raise GovernanceValidationError(
                    "Invalid capability."
                )

        if (
            self.component_type
            in {
                ComponentType.PLAYBOOK,
                ComponentType.CHECKPOINT,
                ComponentType.ROLLBACK,
                ComponentType.FEEDBACK,
            }
            and self.executes_security_actions
        ):
            raise GovernanceValidationError(
                "Component violates execution boundary."
            )

        if self.component_type == ComponentType.FEEDBACK:
            if self.modifies_models:
                raise GovernanceValidationError(
                    "Feedback cannot modify models."
                )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(
                self.metadata
            ),
        )
# ============================================================================
# Governance Report
# ============================================================================


@dataclass(frozen=True)
class GovernanceReport:
    """
    Immutable governance verification result.
    """

    report_id: str
    component_id: str
    compliant: bool
    violations: tuple[str, ...]
    created_at: str
    fingerprint: str = ""

    def __post_init__(self) -> None:

        if not self.report_id.strip():
            raise GovernanceValidationError(
                "report_id is required."
            )

        if not self.component_id.strip():
            raise GovernanceValidationError(
                "component_id is required."
            )

        if not isinstance(
            self.violations,
            tuple,
        ):
            raise GovernanceValidationError(
                "violations must be tuple."
            )

        if not self.fingerprint:
            object.__setattr__(
                self,
                "fingerprint",
                _fingerprint_report(self),
            )


# ============================================================================
# Governance Engine
# ============================================================================


class GovernanceEngine:
    """
    ADIE governance validation engine.

    Responsibility:
        Verify that ADIE components respect their
        security boundaries.

    This engine:
        - validates contracts,
        - produces governance reports.

    This engine NEVER:
        - executes actions,
        - changes state,
        - modifies models.
    """

    VERSION = GOVERNANCE_VERSION

    executes_security_actions = False
    modifies_system_state = False
    modifies_models = False

    def __init__(self) -> None:
        self._registry: dict[str, ComponentContract] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        contract: ComponentContract,
    ) -> None:
        """
        Register an ADIE component contract.
        """

        if not isinstance(
            contract,
            ComponentContract,
        ):
            raise GovernanceValidationError(
                "contract must be ComponentContract."
            )

        if contract.component_id in self._registry:
            raise GovernanceValidationError(
                "Component already registered."
            )

        self._registry[
            contract.component_id
        ] = contract

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self,
        component_id: str,
    ) -> GovernanceReport:
        """
        Validate a registered component.
        """

        if not component_id.strip():
            raise GovernanceValidationError(
                "component_id is required."
            )

        contract = self._registry.get(
            component_id
        )

        if contract is None:
            raise GovernanceValidationError(
                "Component not registered."
            )

        violations = []

        if contract.executes_security_actions:
            violations.append(
                "executes_security_actions_not_allowed"
            )

        if contract.component_type == ComponentType.FEEDBACK:
            if contract.modifies_models:
                violations.append(
                    "feedback_model_modification_forbidden"
                )

        if contract.component_type == ComponentType.PLAYBOOK:
            if contract.executes_security_actions:
                violations.append(
                    "playbook_execution_forbidden"
                )

        if contract.component_type == ComponentType.ROLLBACK:
            if contract.executes_security_actions:
                violations.append(
                    "rollback_execution_forbidden"
                )

        compliant = not violations

        return GovernanceReport(
            report_id=self._build_report_id(
                contract
            ),
            component_id=component_id,
            compliant=compliant,
            violations=tuple(violations),
            created_at=_utc_now(),
        )

    def validate_all(
        self,
    ) -> tuple[GovernanceReport, ...]:
        """
        Validate every registered component.
        """

        reports = []

        for component_id in sorted(
            self._registry.keys()
        ):
            reports.append(
                self.validate(component_id)
            )

        return tuple(reports)

    # ------------------------------------------------------------------
    # Description
    # ------------------------------------------------------------------

    def describe(
        self,
        report: GovernanceReport,
    ) -> Mapping[str, Any]:
        """
        Convert report into JSON-safe output.
        """

        if not isinstance(
            report,
            GovernanceReport,
        ):
            raise GovernanceValidationError(
                "report must be GovernanceReport."
            )

        return {
            "report_id": report.report_id,
            "component_id": report.component_id,
            "compliant": report.compliant,
            "violations": list(
                report.violations
            ),
            "created_at": report.created_at,
            "fingerprint": report.fingerprint,
        }

    def status(self) -> Mapping[str, Any]:
        """
        Return governance engine status.
        """

        return {
            "module": "adie.governance",
            "version": self.VERSION,
            "registered_components": len(
                self._registry
            ),
            "executes_security_actions": False,
            "modifies_system_state": False,
            "modifies_models": False,
            "governance_only": True,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_report_id(
        self,
        contract: ComponentContract,
    ) -> str:

        material = (
            f"{contract.component_id}:"
            f"{contract.component_type.value}"
        )

        digest = hashlib.sha256(
            material.encode("utf-8")
        ).hexdigest()

        return f"gov-{digest[:24]}"
# ============================================================================
# Helper Functions
# ============================================================================


def _utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _freeze_mapping(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """
    Create immutable deterministic mapping.
    """

    if value is None:
        return {}

    if not isinstance(
        value,
        Mapping,
    ):
        raise GovernanceValidationError(
            "metadata must be mapping."
        )

    normalized = json.loads(
        json.dumps(
            dict(value),
            sort_keys=True,
            default=str,
        )
    )

    return _ImmutableDict(normalized)


class _ImmutableDict(dict):
    """
    Immutable dictionary implementation.
    """

    def _blocked(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        raise TypeError(
            "Immutable mapping."
        )

    __setitem__ = _blocked
    __delitem__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked
    setdefault = _blocked
    update = _blocked


def _fingerprint_report(
    report: GovernanceReport,
) -> str:
    """
    Generate deterministic governance fingerprint.
    """

    material = {
        "report_id": report.report_id,
        "component_id": report.component_id,
        "compliant": report.compliant,
        "violations": list(
            report.violations
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
# Self Test
# ============================================================================


def self_test() -> Mapping[str, Any]:
    """
    Execute governance validation self-test.
    """

    tests = {
        "contract_creation": False,
        "component_registration": False,
        "boundary_validation": False,
        "immutable_report": False,
        "fingerprint_generation": False,
        "execution_safety": False,
    }

    try:
        engine = GovernanceEngine()

        contract = ComponentContract(
            component_id="playbook-test",
            component_type=ComponentType.PLAYBOOK,
            capabilities=(
                Capability.PLAN_PLAYBOOK,
            ),
            executes_security_actions=False,
        )

        tests["contract_creation"] = True

        engine.register(contract)

        tests["component_registration"] = True

        report = engine.validate(
            "playbook-test"
        )

        tests["boundary_validation"] = (
            report.compliant is True
        )

        tests["fingerprint_generation"] = bool(
            report.fingerprint
        )

        try:
            report.violations += (
                "blocked",
            )

            tests["immutable_report"] = False

        except Exception:
            tests["immutable_report"] = True

        tests["execution_safety"] = (
            engine.executes_security_actions is False
            and engine.modifies_system_state is False
            and engine.modifies_models is False
        )

        passed = all(
            tests.values()
        )

        return {
            "passed": passed,
            "module": "adie.governance",
            "version": GOVERNANCE_VERSION,
            "governance_test_passed": passed,
            "tests": tests,
            "executes_security_actions": False,
            "modifies_system_state": False,
            "modifies_models": False,
        }

    except Exception as exc:
        return {
            "passed": False,
            "module": "adie.governance",
            "version": GOVERNANCE_VERSION,
            "governance_test_passed": False,
            "tests": tests,
            "error": str(exc),
            "executes_security_actions": False,
            "modifies_system_state": False,
            "modifies_models": False,
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