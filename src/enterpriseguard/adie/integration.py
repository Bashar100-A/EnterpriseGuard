"""
EnterpriseGuard ADIE - Control Plane Integration Layer
=======================================================

Purpose
-------
Coordinates the ADIE foundation pipeline without executing security
actions.

Pipeline:

    Event
      |
      v
    State
      |
      v
    Prediction
      |
      v
    Policy
      |
      v
    Decision
      |
      +--------> Checkpoint
      |
      +--------> Playbook
      |
      +--------> Rollback Plan
      |
      v
    IntegrationResult


Security Boundary
-----------------
This module is a CONTROL-PLANE coordinator.

It MUST NOT:

- execute security actions
- execute shell commands
- isolate hosts
- terminate processes
- disable accounts
- modify firewall rules
- modify enterprise infrastructure
- perform destructive operations
- perform rollback itself

It MAY:

- collect state through the configured state component
- generate predictions
- evaluate policy
- produce decisions
- create immutable checkpoints
- generate response playbooks
- generate rollback plans
- validate contracts
- preserve lineage
- produce audit metadata
- calculate integrity fingerprints


Design Goals
------------
1. Real compatibility with native ADIE component contracts.
2. Explicit stage boundaries.
3. Deterministic orchestration.
4. Strong validation.
5. Failure isolation.
6. Decision lineage preservation.
7. Immutable integration results.
8. Safe serialization.
9. Audit-friendly fingerprints.
10. Zero security-action execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import copy
import json
import time
import uuid
from types import MappingProxyType
from typing import Any, Mapping, Optional


# ============================================================================
# Module metadata
# ============================================================================

MODULE_NAME = "adie.integration"
MODULE_VERSION = "1.1.0"

EXECUTES_SECURITY_ACTIONS = False
DESTRUCTIVE_ACTIONS_ALLOWED = False


# ============================================================================
# Exceptions
# ============================================================================


class ADIEIntegrationError(Exception):
    """Base exception for ADIE integration errors."""


class IntegrationValidationError(ADIEIntegrationError):
    """Raised when integration input is invalid."""


class IntegrationComponentError(ADIEIntegrationError):
    """Raised when an ADIE component fails."""


class IntegrationContractError(ADIEIntegrationError):
    """Raised when a component violates its expected contract."""


# ============================================================================
# Enums
# ============================================================================


class IntegrationStatus(str, Enum):
    """Lifecycle state of an integration operation."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrationStage(str, Enum):
    """Canonical ADIE processing stages."""

    STATE = "state"
    PREDICTION = "prediction"
    POLICY = "policy"
    DECISION = "decision"
    CHECKPOINT = "checkpoint"
    PLAYBOOK = "playbook"
    ROLLBACK = "rollback"


# ============================================================================
# Immutable result
# ============================================================================


@dataclass(frozen=True)
class IntegrationResult:
    """
    Immutable result of one ADIE control-plane operation.

    The result contains planning/control information only.

    No security action is executed by this object.
    """

    operation_id: str
    status: IntegrationStatus

    state: Any = None
    prediction: Any = None
    policy: Any = None
    decision: Any = None

    checkpoint: Any = None
    playbook: Any = None
    rollback: Any = None

    stages_completed: tuple[str, ...] = ()
    failed_stage: Optional[str] = None
    error: Optional[str] = None

    started_at: str = ""
    completed_at: str = ""

    executes_security_actions: bool = False
    destructive_actions_allowed: bool = False

    lineage: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    fingerprint: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "stages_completed",
            tuple(self.stages_completed),
        )

        object.__setattr__(
            self,
            "lineage",
            MappingProxyType(
                copy.deepcopy(dict(self.lineage))
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                copy.deepcopy(dict(self.metadata))
            ),
        )

    @property
    def successful(self) -> bool:
        """Return True when the operation completed successfully."""

        return self.status == IntegrationStatus.COMPLETED

    @property
    def duration_ms(self) -> float:
        """Return operation duration in milliseconds."""

        if not self.started_at or not self.completed_at:
            return 0.0

        try:
            started = datetime.fromisoformat(
                self.started_at
            )
            completed = datetime.fromisoformat(
                self.completed_at
            )

            return max(
                0.0,
                (
                    completed - started
                ).total_seconds()
                * 1000.0,
            )

        except Exception:
            return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return a detached JSON-safe representation."""

        return {
            "operation_id": self.operation_id,
            "status": self.status.value,

            "state": _safe_serialize(self.state),
            "prediction": _safe_serialize(self.prediction),
            "policy": _safe_serialize(self.policy),
            "decision": _safe_serialize(self.decision),

            "checkpoint": _safe_serialize(
                self.checkpoint
            ),
            "playbook": _safe_serialize(
                self.playbook
            ),
            "rollback": _safe_serialize(
                self.rollback
            ),

            "stages_completed": list(
                self.stages_completed
            ),
            "failed_stage": self.failed_stage,
            "error": self.error,

            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,

            "executes_security_actions": (
                self.executes_security_actions
            ),
            "destructive_actions_allowed": (
                self.destructive_actions_allowed
            ),

            "lineage": _safe_serialize(
                self.lineage
            ),
            "metadata": _safe_serialize(
                self.metadata
            ),

            "fingerprint": self.fingerprint,
            "successful": self.successful,
        }


# ============================================================================
# Integration engine
# ============================================================================


class ADIEIntegration:
    """
    ADIE Control Plane integration coordinator.

    The engine adapts to the native ADIE component contracts already
    established in the project.

    Expected native components
    ---------------------------
    State:
        create_initial_state()
        OR provider.collect(...)
        OR compatible callable

    Prediction:
        PredictionService.predict(state)

    Policy:
        ADIEPolicy.evaluate(prediction)

    Decision:
        DecisionEngine.decide(decision_input)

    Checkpoint:
        CheckpointManager.create(state, ...)

    Playbook:
        PlaybookEngine.create(decision, ...)

    Rollback:
        Optional rollback planner.
    """

    VERSION = MODULE_VERSION

    def __init__(
        self,
        *,
        state_provider: Any,
        prediction_provider: Any,
        policy_provider: Any,
        decision_provider: Any,
        checkpoint_provider: Optional[Any] = None,
        playbook_provider: Optional[Any] = None,
        rollback_provider: Optional[Any] = None,
    ) -> None:

        self._validate_provider(
            state_provider,
            "state_provider",
        )

        self._validate_provider(
            prediction_provider,
            "prediction_provider",
        )

        self._validate_provider(
            policy_provider,
            "policy_provider",
        )

        self._validate_provider(
            decision_provider,
            "decision_provider",
        )

        self._state_provider = state_provider
        self._prediction_provider = prediction_provider
        self._policy_provider = policy_provider
        self._decision_provider = decision_provider

        self._checkpoint_provider = (
            checkpoint_provider
        )

        self._playbook_provider = (
            playbook_provider
        )

        self._rollback_provider = (
            rollback_provider
        )

        self._operations = 0
        self._successful_operations = 0
        self._failed_operations = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        event: Mapping[str, Any],
        *,
        create_checkpoint: bool = True,
        plan_playbook: bool = True,
        plan_rollback: bool = True,
    ) -> IntegrationResult:
        """
        Process one event through the ADIE control plane.

        No security action is executed.
        """

        self._validate_event(event)

        operation_id = self._create_operation_id()

        started_at = self._utc_now()

        self._operations += 1

        completed_stages: list[str] = []

        state = None
        prediction = None
        policy = None
        decision = None
        checkpoint = None
        playbook = None
        rollback = None

        current_stage: Optional[str] = None

        try:
            # ==========================================================
            # STATE
            # ==========================================================

            current_stage = (
                IntegrationStage.STATE.value
            )

            state = self._collect_state(
                event
            )

            self._require_result(
                state,
                current_stage,
            )

            completed_stages.append(
                current_stage
            )

            # ==========================================================
            # PREDICTION
            # ==========================================================

            current_stage = (
                IntegrationStage.PREDICTION.value
            )

            prediction = self._predict(
                state,
                event,
            )

            self._require_result(
                prediction,
                current_stage,
            )

            completed_stages.append(
                current_stage
            )

            # ==========================================================
            # POLICY
            # ==========================================================

            current_stage = (
                IntegrationStage.POLICY.value
            )

            policy = self._evaluate_policy(
                state,
                prediction,
                event,
            )

            self._require_result(
                policy,
                current_stage,
            )

            completed_stages.append(
                current_stage
            )

            # ==========================================================
            # DECISION
            # ==========================================================

            current_stage = (
                IntegrationStage.DECISION.value
            )

            decision = self._decide(
                state,
                prediction,
                policy,
                event,
            )

            self._require_result(
                decision,
                current_stage,
            )

            completed_stages.append(
                current_stage
            )

            # ==========================================================
            # CHECKPOINT
            # ==========================================================

            if (
                create_checkpoint
                and self._checkpoint_provider
                is not None
            ):
                current_stage = (
                    IntegrationStage.CHECKPOINT.value
                )

                checkpoint = (
                    self._create_checkpoint(
                        state=state,
                        state_id=self._extract_value(
                            state,
                            "state_id",
                        ),
                        operation_id=operation_id,
                    )
                )

                self._require_result(
                    checkpoint,
                    current_stage,
                )

                completed_stages.append(
                    current_stage
                )

            # ==========================================================
            # PLAYBOOK
            # ==========================================================

            if (
                plan_playbook
                and self._playbook_provider
                is not None
            ):
                current_stage = (
                    IntegrationStage.PLAYBOOK.value
                )

                playbook = self._create_playbook(
                    decision=decision,
                    decision_id=self._extract_value(
                        decision,
                        "decision_id",
                    ),
                    state_id=self._extract_value(
                        state,
                        "state_id",
                    ),
                )

                self._require_result(
                    playbook,
                    current_stage,
                )

                completed_stages.append(
                    current_stage
                )

            # ==========================================================
            # ROLLBACK PLAN
            # ==========================================================

            if (
                plan_rollback
                and self._rollback_provider
                is not None
            ):
                current_stage = (
                    IntegrationStage.ROLLBACK.value
                )

                rollback = self._plan_rollback(
                    decision=decision,
                    checkpoint=checkpoint,
                )

                self._require_result(
                    rollback,
                    current_stage,
                )

                completed_stages.append(
                    current_stage
                )

            # ==========================================================
            # SUCCESS
            # ==========================================================

            completed_at = self._utc_now()

            self._successful_operations += 1

            lineage = self._build_lineage(
                operation_id=operation_id,
                state=state,
                prediction=prediction,
                policy=policy,
                decision=decision,
                checkpoint=checkpoint,
                playbook=playbook,
                rollback=rollback,
            )

            result = IntegrationResult(
                operation_id=operation_id,
                status=IntegrationStatus.COMPLETED,

                state=state,
                prediction=prediction,
                policy=policy,
                decision=decision,

                checkpoint=checkpoint,
                playbook=playbook,
                rollback=rollback,

                stages_completed=tuple(
                    completed_stages
                ),

                started_at=started_at,
                completed_at=completed_at,

                executes_security_actions=False,
                destructive_actions_allowed=False,

                lineage=lineage,

                metadata={
                    "module": MODULE_NAME,
                    "version": MODULE_VERSION,
                    "pipeline_complete": True,
                },
            )

            return self._finalize_result(
                result
            )

        except Exception as exc:
            self._failed_operations += 1

            completed_at = self._utc_now()

            error = self._safe_error_message(
                exc
            )

            lineage = self._build_lineage(
                operation_id=operation_id,
                state=state,
                prediction=prediction,
                policy=policy,
                decision=decision,
                checkpoint=checkpoint,
                playbook=playbook,
                rollback=rollback,
            )

            result = IntegrationResult(
                operation_id=operation_id,
                status=IntegrationStatus.FAILED,

                state=state,
                prediction=prediction,
                policy=policy,
                decision=decision,

                checkpoint=checkpoint,
                playbook=playbook,
                rollback=rollback,

                stages_completed=tuple(
                    completed_stages
                ),

                failed_stage=current_stage,

                error=error,

                started_at=started_at,
                completed_at=completed_at,

                executes_security_actions=False,
                destructive_actions_allowed=False,

                lineage=lineage,

                metadata={
                    "module": MODULE_NAME,
                    "version": MODULE_VERSION,
                    "pipeline_complete": False,
                },
            )

            return self._finalize_result(
                result
            )

    # ------------------------------------------------------------------
    # Native component adapters
    # ------------------------------------------------------------------

    def _collect_state(
        self,
        event: Mapping[str, Any],
    ) -> Any:
        """
        Collect state using the project's native state contract.

        Supported forms:

        1. provider.collect(event)
        2. provider.create(event)
        3. provider(event)
        """

        provider = self._state_provider

        method = getattr(
            provider,
            "collect",
            None,
        )

        if callable(method):
            return self._invoke(
                method,
                "state.collect",
                event,
            )

        method = getattr(
            provider,
            "create",
            None,
        )

        if callable(method):
            return self._invoke(
                method,
                "state.create",
                event,
            )

        if callable(provider):
            return self._invoke(
                provider,
                "state.provider",
                event,
            )

        raise IntegrationContractError(
            "State provider must implement "
            "collect(), create(), or be callable."
        )

    def _predict(
        self,
        state: Any,
        event: Mapping[str, Any],
    ) -> Any:
        """
        Execute the native PredictionService contract.

        Preferred:

            predict(state)

        Compatibility fallback:

            predict(state, event)
        """

        provider = self._prediction_provider

        method = getattr(
            provider,
            "predict",
            None,
        )

        if not callable(method):
            raise IntegrationContractError(
                "Prediction provider must implement predict()."
            )

        state_payload = self._as_payload(
            state
        )

        try:
            return method(
                state_payload
            )
        except TypeError:
            return self._invoke(
                method,
                "prediction.predict",
                state_payload,
                event,
            )
        except Exception as exc:
            raise IntegrationComponentError(
                "prediction.predict() failed."
            ) from exc

    def _evaluate_policy(
        self,
        state: Any,
        prediction: Any,
        event: Mapping[str, Any],
    ) -> Any:
        """
        Execute the native ADIEPolicy contract.

        Preferred:

            evaluate(prediction)

        Compatibility fallbacks are supported for older adapters.
        """

        provider = self._policy_provider

        method = getattr(
            provider,
            "evaluate",
            None,
        )

        if not callable(method):
            raise IntegrationContractError(
                "Policy provider must implement evaluate()."
            )

        prediction_payload = self._as_payload(
            prediction
        )

        try:
            return method(
                prediction_payload
            )

        except TypeError:
            try:
                return method(
                    state=self._as_payload(state),
                    prediction=prediction_payload,
                    event=event,
                )

            except TypeError:
                return self._invoke(
                    method,
                    "policy.evaluate",
                    self._as_payload(state),
                    prediction_payload,
                    event,
                )

            except Exception as exc:
                raise IntegrationComponentError(
                    "policy.evaluate() failed."
                ) from exc

        except Exception as exc:
            raise IntegrationComponentError(
                "policy.evaluate() failed."
            ) from exc

    def _decide(
        self,
        state: Any,
        prediction: Any,
        policy: Any,
        event: Mapping[str, Any],
    ) -> Any:
        """
        Execute the native DecisionEngine contract.

        Preferred:

            DecisionEngine.decide(policy_dict)

        This is compatible with the verified current implementation.
        """

        provider = self._decision_provider

        method = getattr(
            provider,
            "decide",
            None,
        )

        if not callable(method):
            raise IntegrationContractError(
                "Decision provider must implement decide()."
            )

        policy_payload = self._as_payload(
            policy
        )

        try:
            return method(
                policy_payload
            )

        except TypeError:
            try:
                return method(
                    self._build_decision_input(
                        state=state,
                        prediction=prediction,
                        policy=policy,
                        event=event,
                    )
                )

            except Exception as exc:
                raise IntegrationComponentError(
                    "decision.decide() failed."
                ) from exc

        except Exception as exc:
            raise IntegrationComponentError(
                "decision.decide() failed."
            ) from exc

    def _create_checkpoint(
        self,
        *,
        state: Any,
        state_id: Optional[str],
        operation_id: str,
    ) -> Any:
        """
        Execute the native CheckpointManager contract.

        Preferred:

            manager.create(
                state,
                state_id=...,
                metadata=...
            )
        """

        provider = self._checkpoint_provider

        method = getattr(
            provider,
            "create",
            None,
        )

        if not callable(method):
            method = getattr(
                provider,
                "create_checkpoint",
                None,
            )

        if not callable(method):
            raise IntegrationContractError(
                "Checkpoint provider must implement "
                "create() or create_checkpoint()."
            )

        state_payload = self._as_payload(
            state
        )

        metadata = {
            "source": MODULE_NAME,
            "operation_id": operation_id,
            "purpose": "adie-control-plane",
        }

        try:
            return method(
                state_payload,
                state_id=state_id,
                metadata=metadata,
            )

        except TypeError:
            try:
                return method(
                    state_payload,
                    metadata=metadata,
                )

            except TypeError:
                return method(
                    state_payload
                )

            except Exception as exc:
                raise IntegrationComponentError(
                    "checkpoint.create() failed."
                ) from exc

        except Exception as exc:
            raise IntegrationComponentError(
                "checkpoint.create() failed."
            ) from exc

    def _create_playbook(
        self,
        *,
        decision: Any,
        decision_id: Optional[str],
        state_id: Optional[str],
    ) -> Any:
        """
        Execute the native PlaybookEngine contract.

        Preferred:

            engine.create(
                decision_dict,
                decision_id=...
            )

        State ID is retained as lineage metadata rather than passed
        to create(), because the verified PlaybookEngine contract does
        not accept state_id.
        """

        provider = self._playbook_provider

        method = getattr(
            provider,
            "create",
            None,
        )

        if not callable(method):
            method = getattr(
                provider,
                "plan",
                None,
            )

        if not callable(method):
            raise IntegrationContractError(
                "Playbook provider must implement "
                "create() or plan()."
            )

        decision_payload = self._as_payload(
            decision
        )

        try:
            return method(
                decision_payload,
                decision_id=decision_id,
            )

        except TypeError:
            try:
                return method(
                    decision_payload
                )

            except Exception as exc:
                raise IntegrationComponentError(
                    "playbook.create() failed."
                ) from exc

        except Exception as exc:
            raise IntegrationComponentError(
                "playbook.create() failed."
            ) from exc

    def _plan_rollback(
        self,
        *,
        decision: Any,
        checkpoint: Any,
    ) -> Any:
        """
        Request rollback planning only.

        No rollback is ever executed.
        """

        provider = self._rollback_provider

        method = getattr(
            provider,
            "plan",
            None,
        )

        if not callable(method):
            raise IntegrationContractError(
                "Rollback provider must implement plan()."
            )

        decision_payload = self._as_payload(
            decision
        )

        checkpoint_payload = (
            self._as_payload(checkpoint)
            if checkpoint is not None
            else None
        )

        try:
            return method(
                decision_payload,
                checkpoint_payload,
            )

        except Exception as exc:
            raise IntegrationComponentError(
                "rollback.plan() failed."
            ) from exc

    # ------------------------------------------------------------------
    # Decision compatibility
    # ------------------------------------------------------------------

    @staticmethod
    def _build_decision_input(
        *,
        state: Any,
        prediction: Any,
        policy: Any,
        event: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Build a compatibility decision mapping.

        The current DecisionEngine can consume the policy output
        directly. This helper exists only for compatibility with
        older decision adapters.
        """

        prediction_payload = (
            ADIEIntegration._as_payload(
                prediction
            )
        )

        policy_payload = (
            ADIEIntegration._as_payload(
                policy
            )
        )

        state_payload = (
            ADIEIntegration._as_payload(
                state
            )
        )

        merged: dict[str, Any] = {}

        if isinstance(
            prediction_payload,
            Mapping,
        ):
            merged.update(
                prediction_payload
            )

        if isinstance(
            policy_payload,
            Mapping,
        ):
            merged.update(
                policy_payload
            )

        merged.setdefault(
            "context",
            {},
        )

        if isinstance(
            merged["context"],
            Mapping,
        ):
            context = dict(
                merged["context"]
            )
        else:
            context = {}

        context["event"] = copy.deepcopy(
            dict(event)
        )

        if isinstance(
            state_payload,
            Mapping,
        ):
            if "state_id" in state_payload:
                context["state_id"] = (
                    state_payload["state_id"]
                )

        merged["context"] = context

        return merged

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_provider(
        provider: Any,
        name: str,
    ) -> None:
        if provider is None:
            raise IntegrationValidationError(
                f"{name} is required."
            )

    @staticmethod
    def _validate_event(
        event: Mapping[str, Any],
    ) -> None:
        if not isinstance(
            event,
            Mapping,
        ):
            raise IntegrationValidationError(
                "event must be a mapping."
            )

        if not event:
            raise IntegrationValidationError(
                "event must not be empty."
            )

    @staticmethod
    def _require_result(
        result: Any,
        stage: str,
    ) -> None:
        if result is None:
            raise IntegrationContractError(
                f"{stage} stage returned None."
            )

    # ------------------------------------------------------------------
    # Invocation
    # ------------------------------------------------------------------

    @staticmethod
    def _invoke(
        method: Any,
        operation: str,
        *args: Any,
    ) -> Any:
        try:
            result = method(*args)

        except Exception as exc:
            raise IntegrationComponentError(
                f"{operation} failed."
            ) from exc

        if result is None:
            raise IntegrationContractError(
                f"{operation} returned None."
            )

        return result

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------

    @classmethod
    def _build_lineage(
        cls,
        *,
        operation_id: str,
        state: Any,
        prediction: Any,
        policy: Any,
        decision: Any,
        checkpoint: Any,
        playbook: Any,
        rollback: Any,
    ) -> dict[str, Any]:
        """
        Build explicit cross-component lineage.
        """

        return {
            "operation_id": operation_id,

            "state_id": cls._extract_value(
                state,
                "state_id",
            ),

            "prediction_id": cls._extract_value(
                prediction,
                "prediction_id",
            ),

            "decision_id": cls._extract_value(
                decision,
                "decision_id",
            ),

            "checkpoint_id": cls._extract_value(
                checkpoint,
                "checkpoint_id",
            ),

            "playbook_id": cls._extract_value(
                playbook,
                "playbook_id",
            ),

            "rollback_id": cls._extract_value(
                rollback,
                "rollback_id",
            ),
        }

    @staticmethod
    def _extract_value(
        value: Any,
        key: str,
    ) -> Optional[Any]:
        if value is None:
            return None

        if isinstance(
            value,
            Mapping,
        ):
            return value.get(key)

        attribute = getattr(
            value,
            key,
            None,
        )

        return attribute

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _as_payload(
        value: Any,
    ) -> Any:
        """
        Convert an ADIE object to a detached mapping when possible.
        """

        if value is None:
            return None

        if isinstance(
            value,
            Mapping,
        ):
            return copy.deepcopy(
                dict(value)
            )

        to_dict = getattr(
            value,
            "to_dict",
            None,
        )

        if callable(to_dict):
            try:
                return copy.deepcopy(
                    to_dict()
                )
            except Exception as exc:
                raise IntegrationContractError(
                    f"{type(value).__name__}.to_dict() failed."
                ) from exc

        return value

    @staticmethod
    def _safe_serialize(
        value: Any,
    ) -> Any:
        return _safe_serialize(value)

    # ------------------------------------------------------------------
    # Result fingerprint
    # ------------------------------------------------------------------

    @classmethod
    def _finalize_result(
        cls,
        result: IntegrationResult,
    ) -> IntegrationResult:
        """
        Calculate an integrity fingerprint over the complete
        integration result payload.
        """

        payload = {
            "operation_id": result.operation_id,
            "status": result.status.value,

            "state": _safe_serialize(
                result.state
            ),
            "prediction": _safe_serialize(
                result.prediction
            ),
            "policy": _safe_serialize(
                result.policy
            ),
            "decision": _safe_serialize(
                result.decision
            ),

            "checkpoint": _safe_serialize(
                result.checkpoint
            ),
            "playbook": _safe_serialize(
                result.playbook
            ),
            "rollback": _safe_serialize(
                result.rollback
            ),

            "stages_completed": (
                result.stages_completed
            ),

            "failed_stage": result.failed_stage,
            "error": result.error,

            "started_at": result.started_at,
            "completed_at": result.completed_at,

            "executes_security_actions": (
                result.executes_security_actions
            ),

            "destructive_actions_allowed": (
                result.destructive_actions_allowed
            ),

            "lineage": _safe_serialize(
                result.lineage
            ),

            "metadata": _safe_serialize(
                result.metadata
            ),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

        fingerprint = sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return IntegrationResult(
            operation_id=result.operation_id,
            status=result.status,

            state=result.state,
            prediction=result.prediction,
            policy=result.policy,
            decision=result.decision,

            checkpoint=result.checkpoint,
            playbook=result.playbook,
            rollback=result.rollback,

            stages_completed=(
                result.stages_completed
            ),

            failed_stage=result.failed_stage,
            error=result.error,

            started_at=result.started_at,
            completed_at=result.completed_at,

            executes_security_actions=False,
            destructive_actions_allowed=False,

            lineage=result.lineage,
            metadata=result.metadata,

            fingerprint=fingerprint,
        )

    # ------------------------------------------------------------------
    # Identity / time
    # ------------------------------------------------------------------

    @staticmethod
    def _create_operation_id() -> str:
        return (
            "adie-op-"
            + uuid.uuid4().hex
        )

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_error_message(
        exc: Exception,
    ) -> str:
        """
        Do not expose arbitrary exception strings.

        This avoids accidentally leaking sensitive values.
        """

        return (
            f"{type(exc).__name__}: "
            "integration stage failed."
        )

    # ------------------------------------------------------------------
    # Status / health
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Return integration engine status."""

        total = (
            self._successful_operations
            + self._failed_operations
        )

        success_rate = (
            round(
                self._successful_operations
                / total,
                4,
            )
            if total
            else 0.0
        )

        return {
            "module": MODULE_NAME,
            "version": MODULE_VERSION,

            "operations": self._operations,
            "successful_operations": (
                self._successful_operations
            ),
            "failed_operations": (
                self._failed_operations
            ),

            "success_rate": success_rate,

            "checkpoint_provider": (
                self._checkpoint_provider
                is not None
            ),

            "playbook_provider": (
                self._playbook_provider
                is not None
            ),

            "rollback_provider": (
                self._rollback_provider
                is not None
            ),

            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    def health_check(self) -> dict[str, Any]:
        """Return a lightweight health report."""

        required = (
            self._state_provider,
            self._prediction_provider,
            self._policy_provider,
            self._decision_provider,
        )

        healthy = all(
            provider is not None
            for provider in required
        )

        return {
            "healthy": healthy,
            "module": MODULE_NAME,
            "version": MODULE_VERSION,

            "required_components_available": (
                healthy
            ),

            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------

    def self_test(self) -> dict[str, Any]:
        """
        Run structural and behavioral integration tests.

        The test uses local fake providers only.
        """

        tests: dict[str, bool] = {}

        tests[
            "provider_validation"
        ] = self._test_provider_validation()

        tests[
            "event_validation"
        ] = self._test_event_validation()

        tests[
            "operation_identity"
        ] = self._test_operation_identity()

        tests[
            "immutable_result"
        ] = self._test_immutable_result()

        tests[
            "native_pipeline"
        ] = self._test_native_pipeline()

        tests[
            "lineage_contract"
        ] = self._test_lineage_contract()

        tests[
            "failure_isolation"
        ] = self._test_failure_isolation()

        tests[
            "fingerprint_contract"
        ] = self._test_fingerprint_contract()

        tests[
            "execution_safety"
        ] = self._test_execution_safety()

        tests[
            "status_contract"
        ] = self._test_status_contract()

        tests[
            "json_export"
        ] = self._test_json_export()

        passed = all(
            tests.values()
        )

        return {
            "passed": passed,
            "module": MODULE_NAME,
            "version": MODULE_VERSION,

            "integration_test_passed": passed,

            "tests": tests,

            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    # ------------------------------------------------------------------
    # Self-test helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _test_provider_validation() -> bool:
        try:
            ADIEIntegration(
                state_provider=None,
                prediction_provider=_TestPrediction(),
                policy_provider=_TestPolicy(),
                decision_provider=_TestDecision(),
            )

        except IntegrationValidationError:
            return True

        return False

    @staticmethod
    def _test_event_validation() -> bool:
        try:
            ADIEIntegration._validate_event(
                {}
            )

        except IntegrationValidationError:
            return True

        return False

    @staticmethod
    def _test_operation_identity() -> bool:
        first = (
            ADIEIntegration._create_operation_id()
        )

        second = (
            ADIEIntegration._create_operation_id()
        )

        return (
            first.startswith("adie-op-")
            and second.startswith("adie-op-")
            and first != second
        )

    @staticmethod
    def _test_immutable_result() -> bool:
        result = IntegrationResult(
            operation_id="test",
            status=IntegrationStatus.COMPLETED,
        )

        try:
            result.status = (
                IntegrationStatus.FAILED
            )

        except Exception:
            return True

        return False

    def _test_native_pipeline(self) -> bool:
        engine = ADIEIntegration(
            state_provider=_TestState(),
            prediction_provider=_TestPrediction(),
            policy_provider=_TestPolicy(),
            decision_provider=_TestDecision(),
            checkpoint_provider=_TestCheckpoint(),
            playbook_provider=_TestPlaybook(),
            rollback_provider=_TestRollback(),
        )

        result = engine.process(
            {
                "event_type": "self_test",
                "source": MODULE_NAME,
            }
        )

        expected = [
            "state",
            "prediction",
            "policy",
            "decision",
            "checkpoint",
            "playbook",
            "rollback",
        ]

        return (
            result.successful
            and list(
                result.stages_completed
            ) == expected
            and result.state is not None
            and result.prediction is not None
            and result.policy is not None
            and result.decision is not None
            and result.checkpoint is not None
            and result.playbook is not None
            and result.rollback is not None
        )

    @staticmethod
    def _test_lineage_contract() -> bool:
        engine = ADIEIntegration(
            state_provider=_TestState(),
            prediction_provider=_TestPrediction(),
            policy_provider=_TestPolicy(),
            decision_provider=_TestDecision(),
            checkpoint_provider=_TestCheckpoint(),
            playbook_provider=_TestPlaybook(),
            rollback_provider=_TestRollback(),
        )

        result = engine.process(
            {
                "event_type": "lineage_test",
            }
        )

        lineage = dict(
            result.lineage
        )

        return (
            result.successful
            and lineage["state_id"]
            == "state-test"
            and lineage["prediction_id"]
            == "prediction-test"
            and lineage["decision_id"]
            == "decision-test"
            and lineage["checkpoint_id"]
            == "checkpoint-test"
            and lineage["playbook_id"]
            == "playbook-test"
            and lineage["rollback_id"]
            == "rollback-test"
        )

    @staticmethod
    def _test_failure_isolation() -> bool:
        engine = ADIEIntegration(
            state_provider=_TestState(),
            prediction_provider=_FailingPrediction(),
            policy_provider=_TestPolicy(),
            decision_provider=_TestDecision(),
        )

        result = engine.process(
            {
                "event_type": "failure_test",
            }
        )

        status = engine.status()

        return (
            result.status
            == IntegrationStatus.FAILED
            and result.failed_stage
            == "prediction"
            and result.error is not None
            and status["failed_operations"]
            == 1
            and status["successful_operations"]
            == 0
        )

    def _test_fingerprint_contract(self) -> bool:
        engine = ADIEIntegration(
            state_provider=_TestState(),
            prediction_provider=_TestPrediction(),
            policy_provider=_TestPolicy(),
            decision_provider=_TestDecision(),
        )

        result = engine.process(
            {
                "event_type": "fingerprint_test",
            },
            create_checkpoint=False,
            plan_playbook=False,
            plan_rollback=False,
        )

        return (
            result.successful
            and len(result.fingerprint) == 64
        )

    @staticmethod
    def _test_execution_safety() -> bool:
        return (
            EXECUTES_SECURITY_ACTIONS is False
            and DESTRUCTIVE_ACTIONS_ALLOWED is False
        )

    def _test_status_contract(self) -> bool:
        status = self.status()

        return (
            status["module"]
            == MODULE_NAME
            and status["version"]
            == MODULE_VERSION
            and (
                status[
                    "executes_security_actions"
                ]
                is False
            )
            and (
                status[
                    "destructive_actions_allowed"
                ]
                is False
            )
        )

    def _test_json_export(self) -> bool:
        engine = ADIEIntegration(
            state_provider=_TestState(),
            prediction_provider=_TestPrediction(),
            policy_provider=_TestPolicy(),
            decision_provider=_TestDecision(),
        )

        result = engine.process(
            {
                "event_type": "json_test",
            },
            create_checkpoint=False,
            plan_playbook=False,
            plan_rollback=False,
        )

        try:
            encoded = json.dumps(
                result.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            )

            decoded = json.loads(
                encoded
            )

            return (
                decoded["operation_id"]
                == result.operation_id
                and decoded["fingerprint"]
                == result.fingerprint
            )

        except Exception:
            return False


# ============================================================================
# Test providers
# ============================================================================


class _TestState:
    """Test state provider."""

    def collect(
        self,
        event: Mapping[str, Any],
    ) -> dict[str, Any]:

        return {
            "state_id": "state-test",
            "event": dict(event),
        }


class _TestPrediction:
    """Test prediction provider."""

    def predict(
        self,
        state: Mapping[str, Any],
    ) -> dict[str, Any]:

        return {
            "prediction_id": "prediction-test",
            "predicted_class": "benign",
            "threat_probability": 0.10,
            "confidence": 0.90,
        }


class _FailingPrediction:
    """Prediction provider used to test failure isolation."""

    def predict(
        self,
        state: Mapping[str, Any],
    ) -> dict[str, Any]:

        raise RuntimeError(
            "intentional self-test failure"
        )


class _TestPolicy:
    """Test policy provider."""

    def evaluate(
        self,
        prediction: Mapping[str, Any],
    ) -> dict[str, Any]:

        return {
            "policy_allowed": True,
            "allowed": True,
            "level": "low",
            "risk_score": 0.10,
            "threat_probability": 0.10,
            "prediction_confidence": 0.90,
            "state_risk": 0.05,
            "predicted_class": "benign",
        }


class _TestDecision:
    """Test decision provider."""

    def decide(
        self,
        decision_input: Mapping[str, Any],
    ) -> dict[str, Any]:

        return {
            "decision_id": "decision-test",
            "action": "allow",
            "risk_score": 0.10,
        }


class _TestCheckpoint:
    """Test checkpoint provider."""

    def create(
        self,
        state: Mapping[str, Any],
        *,
        state_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:

        return {
            "checkpoint_id": "checkpoint-test",
            "state_id": state_id,
            "metadata": dict(
                metadata or {}
            ),
        }


class _TestPlaybook:
    """Test playbook provider."""

    def create(
        self,
        decision: Mapping[str, Any],
        *,
        decision_id: Optional[str] = None,
    ) -> dict[str, Any]:

        return {
            "playbook_id": "playbook-test",
            "decision_id": decision_id,
        }


class _TestRollback:
    """Test rollback planner."""

    def plan(
        self,
        decision: Mapping[str, Any],
        checkpoint: Any,
    ) -> dict[str, Any]:

        return {
            "rollback_id": "rollback-test",
            "planned": checkpoint is not None,
        }


# ============================================================================
# Safe serialization
# ============================================================================


def _safe_serialize(
    value: Any,
) -> Any:
    """
    Convert ADIE objects into JSON-compatible structures.

    Serialization is detached from the original object graph.
    """

    if value is None:
        return None

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _safe_serialize(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _safe_serialize(item)
            for item in value
        ]

    to_dict = getattr(
        value,
        "to_dict",
        None,
    )

    if callable(to_dict):
        try:
            return _safe_serialize(
                to_dict()
            )

        except Exception:
            return {
                "type": type(value).__name__,
            }

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    return str(value)


# ============================================================================
# Module self-test
# ============================================================================


def _run_self_test() -> dict[str, Any]:
    """
    Run the complete local integration self-test.
    """

    engine = ADIEIntegration(
        state_provider=_TestState(),
        prediction_provider=_TestPrediction(),
        policy_provider=_TestPolicy(),
        decision_provider=_TestDecision(),
        checkpoint_provider=_TestCheckpoint(),
        playbook_provider=_TestPlaybook(),
        rollback_provider=_TestRollback(),
    )

    result = engine.self_test()

    return result


# ============================================================================
# Module entry point
# ============================================================================


if __name__ == "__main__":
    print(
        json.dumps(
            _run_self_test(),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    )