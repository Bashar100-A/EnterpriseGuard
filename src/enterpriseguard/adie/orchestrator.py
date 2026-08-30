"""
EnterpriseGuard ADIE - Orchestrator
===================================

Adaptive Defense Intelligence Engine
Central Security Control-Plane Orchestrator.

Responsibilities
----------------
The orchestrator coordinates the ADIE decision pipeline:

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
      +------> Checkpoint planning
      |
      +------> Playbook planning
      |
      +------> Rollback planning
      |
      v
    Immutable Orchestration Result

Design principles
-----------------
- Control-plane only.
- Planning only.
- No security-action execution.
- No shell execution.
- No network execution.
- No account modification.
- No destructive operations.
- Fail closed.
- Explicit provider contracts.
- Backward-compatible provider invocation.
- Immutable result boundary.
- Deterministic serialization.
- Cryptographic result fingerprint.
- Failure isolation.
- Auditable lifecycle.
- No runtime monkey-patching.
- No hidden side effects.

Security boundary
-----------------
EXECUTES_SECURITY_ACTIONS = False
DESTRUCTIVE_ACTIONS_ALLOWED = False

Actual response execution remains outside ADIE.
The orchestrator produces decisions and execution plans only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import inspect
import json
import uuid
from typing import Any, Mapping, Optional, Protocol


# ============================================================================
# Module metadata
# ============================================================================

ORCHESTRATOR_VERSION = "2.0.0"

MODULE_NAME = "adie.orchestrator"

EXECUTES_SECURITY_ACTIONS = False
DESTRUCTIVE_ACTIONS_ALLOWED = False


__all__ = [
    "ORCHESTRATOR_VERSION",
    "MODULE_NAME",
    "EXECUTES_SECURITY_ACTIONS",
    "DESTRUCTIVE_ACTIONS_ALLOWED",
    "OrchestrationError",
    "OrchestrationValidationError",
    "OrchestrationComponentError",
    "OrchestrationStatus",
    "OrchestrationResult",
    "ADIEOrchestrator",
    "self_test",
]


# ============================================================================
# Exceptions
# ============================================================================


class OrchestrationError(Exception):
    """Base exception for ADIE orchestration errors."""


class OrchestrationValidationError(OrchestrationError):
    """Raised when orchestration input or configuration is invalid."""


class OrchestrationComponentError(OrchestrationError):
    """Raised when an ADIE component fails or violates its contract."""


# ============================================================================
# Enums
# ============================================================================


class OrchestrationStatus(str, Enum):
    """Lifecycle status of an orchestration operation."""

    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


# ============================================================================
# Provider protocols
# ============================================================================


class StateProvider(Protocol):
    """
    State provider.

    Supported contracts:

        collect(event)
        get_status()
    """

    ...


class PredictionProvider(Protocol):
    """
    Prediction provider.

    Supported contracts:

        predict(state)
        predict(state, event)
    """

    ...


class PolicyProvider(Protocol):
    """
    Policy provider.

    Supported contracts:

        evaluate(prediction)
        evaluate(prediction, state)
        evaluate(prediction, state, event)
    """

    ...


class DecisionProvider(Protocol):
    """
    Decision provider.

    Supported contracts:

        decide(policy)
        decide(prediction, policy)
        decide(prediction, policy, state)
        decide(prediction, policy, state, event)
    """

    ...


class CheckpointProvider(Protocol):
    """
    Checkpoint planning provider.

    Supported contracts are intentionally flexible because
    different ADIE checkpoint implementations may expose:

        create(...)
        create_checkpoint(...)
        plan(...)
    """

    ...


class PlaybookProvider(Protocol):
    """
    Playbook planning provider.

    Supported contracts:

        create(...)
        plan(...)
        build(...)
    """

    ...


class RollbackProvider(Protocol):
    """
    Rollback planning provider.

    Supported contracts:

        plan(...)
        create(...)
    """

    ...


# ============================================================================
# Immutable Result
# ============================================================================


@dataclass(frozen=True)
class OrchestrationResult:
    """
    Immutable result produced by ADIEOrchestrator.

    This object represents analysis and planning.

    It does NOT represent execution of a security action.
    """

    operation_id: str
    status: OrchestrationStatus

    state: Any = None
    prediction: Any = None
    policy: Any = None
    decision: Any = None

    checkpoint: Any = None
    playbook: Any = None
    rollback: Any = None

    created_at: str = ""
    completed_at: str = ""

    failed_stage: Optional[str] = None
    error: Optional[str] = None

    executes_security_actions: bool = False
    destructive_actions_allowed: bool = False

    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.operation_id, str):
            raise OrchestrationValidationError(
                "operation_id must be a string."
            )

        if not self.operation_id.strip():
            raise OrchestrationValidationError(
                "operation_id must not be empty."
            )

        if not isinstance(
            self.status,
            OrchestrationStatus,
        ):
            raise OrchestrationValidationError(
                "status must be OrchestrationStatus."
            )

        if self.executes_security_actions:
            raise OrchestrationValidationError(
                "ADIE orchestrator cannot execute security actions."
            )

        if self.destructive_actions_allowed:
            raise OrchestrationValidationError(
                "Destructive actions are forbidden."
            )

        if not self.fingerprint:
            object.__setattr__(
                self,
                "fingerprint",
                _fingerprint_result(self),
            )

    @property
    def successful(self) -> bool:
        """Return True when orchestration completed successfully."""

        return self.status == OrchestrationStatus.COMPLETED

    @property
    def duration_ms(self) -> float:
        """Return orchestration duration in milliseconds."""

        if not self.created_at or not self.completed_at:
            return 0.0

        try:
            start = datetime.fromisoformat(self.created_at)
            end = datetime.fromisoformat(self.completed_at)

            return round(
                max(
                    0.0,
                    (end - start).total_seconds() * 1000.0,
                ),
                3,
            )

        except Exception:
            return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe result representation."""

        return {
            "operation_id": self.operation_id,
            "status": self.status.value,
            "state": _safe_serialize(self.state),
            "prediction": _safe_serialize(self.prediction),
            "policy": _safe_serialize(self.policy),
            "decision": _safe_serialize(self.decision),
            "checkpoint": _safe_serialize(self.checkpoint),
            "playbook": _safe_serialize(self.playbook),
            "rollback": _safe_serialize(self.rollback),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "failed_stage": self.failed_stage,
            "error": self.error,
            "executes_security_actions": (
                self.executes_security_actions
            ),
            "destructive_actions_allowed": (
                self.destructive_actions_allowed
            ),
            "fingerprint": self.fingerprint,
            "successful": self.successful,
        }


# ============================================================================
# Orchestrator
# ============================================================================


class ADIEOrchestrator:
    """
    Central ADIE control-plane orchestrator.

    The orchestrator coordinates intelligence and planning components.
    It does not execute security actions.
    """

    VERSION = ORCHESTRATOR_VERSION

    executes_security_actions = False
    destructive_actions_allowed = False

    _STAGES = (
        "state",
        "prediction",
        "policy",
        "decision",
        "checkpoint",
        "playbook",
        "rollback",
    )

    def __init__(
        self,
        state_provider: StateProvider,
        prediction_provider: PredictionProvider,
        policy_provider: PolicyProvider,
        decision_provider: DecisionProvider,
        *,
        checkpoint_provider: Optional[CheckpointProvider] = None,
        playbook_provider: Optional[PlaybookProvider] = None,
        rollback_provider: Optional[RollbackProvider] = None,
    ) -> None:

        self._validate_component(
            state_provider,
            "state_provider",
            ("collect", "get_status"),
        )

        self._validate_component(
            prediction_provider,
            "prediction_provider",
            ("predict",),
        )

        self._validate_component(
            policy_provider,
            "policy_provider",
            ("evaluate",),
        )

        self._validate_component(
            decision_provider,
            "decision_provider",
            ("decide",),
        )

        if checkpoint_provider is not None:
            self._validate_component(
                checkpoint_provider,
                "checkpoint_provider",
                (
                    "create",
                    "create_checkpoint",
                    "plan",
                ),
            )

        if playbook_provider is not None:
            self._validate_component(
                playbook_provider,
                "playbook_provider",
                (
                    "create",
                    "plan",
                    "build",
                ),
            )

        if rollback_provider is not None:
            self._validate_component(
                rollback_provider,
                "rollback_provider",
                (
                    "plan",
                    "create",
                ),
            )

        self._state_provider = state_provider
        self._prediction_provider = prediction_provider
        self._policy_provider = policy_provider
        self._decision_provider = decision_provider

        self._checkpoint_provider = checkpoint_provider
        self._playbook_provider = playbook_provider
        self._rollback_provider = rollback_provider

        self._total_runs = 0
        self._successful_runs = 0
        self._blocked_runs = 0
        self._failed_runs = 0

        self._last_result: Optional[
            OrchestrationResult
        ] = None

    # ========================================================================
    # Public API
    # ========================================================================

    def orchestrate(
        self,
        event: Mapping[str, Any],
        *,
        create_checkpoint: bool = True,
        create_playbook: bool = True,
        create_rollback: bool = True,
    ) -> OrchestrationResult:
        """
        Execute the ADIE control-plane pipeline.

        No security action is executed.
        """

        self._validate_event(event)

        self._total_runs += 1

        operation_id = self._create_operation_id()
        created_at = _utc_now()

        state = None
        prediction = None
        policy = None
        decision = None
        checkpoint = None
        playbook = None
        rollback = None

        current_stage = "state"

        try:
            # ================================================================
            # 1. State
            # ================================================================

            current_stage = "state"

            state = self._collect_state(event)

            # ================================================================
            # 2. Prediction
            # ================================================================

            current_stage = "prediction"

            prediction = self._predict(
                state,
                event,
            )

            # ================================================================
            # 3. Policy
            # ================================================================

            current_stage = "policy"

            policy = self._evaluate_policy(
                prediction,
                state,
                event,
            )

            # ================================================================
            # 4. Decision
            # ================================================================

            current_stage = "decision"

            decision = self._make_decision(
                prediction,
                policy,
                state,
                event,
            )

            # ================================================================
            # Policy enforcement boundary
            # ================================================================

            if _is_policy_blocked(policy):
                self._blocked_runs += 1

                result = OrchestrationResult(
                    operation_id=operation_id,
                    status=OrchestrationStatus.BLOCKED,
                    state=state,
                    prediction=prediction,
                    policy=policy,
                    decision=decision,
                    created_at=created_at,
                    completed_at=_utc_now(),
                    failed_stage=None,
                    error=None,
                    executes_security_actions=False,
                    destructive_actions_allowed=False,
                )

                self._last_result = result

                return result

            # ================================================================
            # 5. Checkpoint planning
            # ================================================================

            if create_checkpoint:
                current_stage = "checkpoint"

                checkpoint = self._create_checkpoint(
                    state=state,
                    decision=decision,
                    operation_id=operation_id,
                )

            # ================================================================
            # 6. Playbook planning
            # ================================================================

            if create_playbook:
                current_stage = "playbook"

                playbook = self._create_playbook(
                    decision=decision,
                    state=state,
                    prediction=prediction,
                    operation_id=operation_id,
                )

            # ================================================================
            # 7. Rollback planning
            # ================================================================

            if create_rollback:
                current_stage = "rollback"

                rollback = self._create_rollback(
                    decision=decision,
                    checkpoint=checkpoint,
                    state=state,
                    operation_id=operation_id,
                )

            # ================================================================
            # Completed
            # ================================================================

            self._successful_runs += 1

            result = OrchestrationResult(
                operation_id=operation_id,
                status=OrchestrationStatus.COMPLETED,
                state=state,
                prediction=prediction,
                policy=policy,
                decision=decision,
                checkpoint=checkpoint,
                playbook=playbook,
                rollback=rollback,
                created_at=created_at,
                completed_at=_utc_now(),
                failed_stage=None,
                error=None,
                executes_security_actions=False,
                destructive_actions_allowed=False,
            )

            self._last_result = result

            return result

        except OrchestrationError:
            self._failed_runs += 1

            result = OrchestrationResult(
                operation_id=operation_id,
                status=OrchestrationStatus.FAILED,
                state=state,
                prediction=prediction,
                policy=policy,
                decision=decision,
                checkpoint=checkpoint,
                playbook=playbook,
                rollback=rollback,
                created_at=created_at,
                completed_at=_utc_now(),
                failed_stage=current_stage,
                error="orchestration component failure",
                executes_security_actions=False,
                destructive_actions_allowed=False,
            )

            self._last_result = result

            return result

        except Exception as exc:
            self._failed_runs += 1

            result = OrchestrationResult(
                operation_id=operation_id,
                status=OrchestrationStatus.FAILED,
                state=state,
                prediction=prediction,
                policy=policy,
                decision=decision,
                checkpoint=checkpoint,
                playbook=playbook,
                rollback=rollback,
                created_at=created_at,
                completed_at=_utc_now(),
                failed_stage=current_stage,
                error=_safe_exception_message(exc),
                executes_security_actions=False,
                destructive_actions_allowed=False,
            )

            self._last_result = result

            return result

    def process(
        self,
        event: Mapping[str, Any],
    ) -> OrchestrationResult:
        """
        Convenience API for the complete standard ADIE pipeline.
        """

        return self.orchestrate(
            event,
            create_checkpoint=True,
            create_playbook=True,
            create_rollback=True,
        )

    # ========================================================================
    # Status / health
    # ========================================================================

    def status(self) -> dict[str, Any]:
        """Return orchestrator runtime status."""

        total_terminal_runs = (
            self._successful_runs
            + self._blocked_runs
            + self._failed_runs
        )

        success_rate = (
            round(
                self._successful_runs
                / total_terminal_runs,
                4,
            )
            if total_terminal_runs
            else 0.0
        )

        return {
            "module": MODULE_NAME,
            "version": self.VERSION,
            "planning_only": True,
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
            "total_runs": self._total_runs,
            "successful_runs": self._successful_runs,
            "blocked_runs": self._blocked_runs,
            "failed_runs": self._failed_runs,
            "success_rate": success_rate,
            "has_last_result": (
                self._last_result is not None
            ),
            "providers": {
                "state": (
                    self._state_provider.__class__.__name__
                ),
                "prediction": (
                    self._prediction_provider.__class__.__name__
                ),
                "policy": (
                    self._policy_provider.__class__.__name__
                ),
                "decision": (
                    self._decision_provider.__class__.__name__
                ),
                "checkpoint": (
                    self._checkpoint_provider is not None
                ),
                "playbook": (
                    self._playbook_provider is not None
                ),
                "rollback": (
                    self._rollback_provider is not None
                ),
            },
        }

    def health_check(self) -> dict[str, Any]:
        """Return component health information."""

        components = {
            "state": self._component_has_any_method(
                self._state_provider,
                ("collect", "get_status"),
            ),
            "prediction": self._component_has_method(
                self._prediction_provider,
                "predict",
            ),
            "policy": self._component_has_method(
                self._policy_provider,
                "evaluate",
            ),
            "decision": self._component_has_method(
                self._decision_provider,
                "decide",
            ),
            "checkpoint": (
                self._checkpoint_provider is None
                or self._component_has_any_method(
                    self._checkpoint_provider,
                    (
                        "create",
                        "create_checkpoint",
                        "plan",
                    ),
                )
            ),
            "playbook": (
                self._playbook_provider is None
                or self._component_has_any_method(
                    self._playbook_provider,
                    (
                        "create",
                        "plan",
                        "build",
                    ),
                )
            ),
            "rollback": (
                self._rollback_provider is None
                or self._component_has_any_method(
                    self._rollback_provider,
                    (
                        "plan",
                        "create",
                    ),
                )
            ),
        }

        return {
            "healthy": all(components.values()),
            "module": MODULE_NAME,
            "version": self.VERSION,
            "components": components,
            "planning_only": True,
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    # ========================================================================
    # State
    # ========================================================================

    def _collect_state(
        self,
        event: Mapping[str, Any],
    ) -> Any:
        """
        Collect enterprise state using the native provider contract.

        Preferred contract:
            collect(event)

        Fallback contract:
            get_status()
        """

        provider = self._state_provider

        collect = getattr(
            provider,
            "collect",
            None,
        )

        if callable(collect):
            try:
                signature = inspect.signature(collect)

                if _can_bind(
                    signature,
                    dict(event),
                ):
                    result = collect(dict(event))

                    if result is None:
                        raise OrchestrationComponentError(
                            "State collection returned None."
                        )

                    return _safe_serialize(result)

            except (ValueError, TypeError):
                pass

            except OrchestrationComponentError:
                raise

            except Exception as exc:
                raise OrchestrationComponentError(
                    "State collection failed."
                ) from exc

        get_status = getattr(
            provider,
            "get_status",
            None,
        )

        if callable(get_status):
            try:
                result = get_status()

                if result is None:
                    raise OrchestrationComponentError(
                        "State provider returned None."
                    )

                serialized = _safe_serialize(result)

                if isinstance(serialized, Mapping):
                    merged = dict(serialized)
                    merged.setdefault(
                        "event",
                        dict(event),
                    )
                    return merged

                return {
                    "state": serialized,
                    "event": dict(event),
                }

            except OrchestrationComponentError:
                raise

            except Exception as exc:
                raise OrchestrationComponentError(
                    "State status retrieval failed."
                ) from exc

        raise OrchestrationComponentError(
            "State provider has no compatible contract."
        )

    # ========================================================================
    # Prediction
    # ========================================================================

    def _predict(
        self,
        state: Any,
        event: Mapping[str, Any],
    ) -> Any:
        """Generate prediction using the native prediction contract."""

        method = getattr(
            self._prediction_provider,
            "predict",
            None,
        )

        if not callable(method):
            raise OrchestrationComponentError(
                "Prediction provider has no predict()."
            )

        state_dict = _as_mapping(state)

        attempts = (
            (
                (state_dict, dict(event)),
                {},
            ),
            (
                (state_dict,),
                {},
            ),
            (
                (state,),
                {},
            ),
        )

        return _invoke_compatible(
            method,
            attempts,
            "Prediction",
        )

    # ========================================================================
    # Policy
    # ========================================================================

    def _evaluate_policy(
        self,
        prediction: Any,
        state: Any,
        event: Mapping[str, Any],
    ) -> Any:
        """Evaluate policy using the native policy contract."""

        method = getattr(
            self._policy_provider,
            "evaluate",
            None,
        )

        if not callable(method):
            raise OrchestrationComponentError(
                "Policy provider has no evaluate()."
            )

        prediction_dict = _as_mapping(prediction)
        state_dict = _as_mapping(state)

        attempts = (
            (
                (
                    prediction_dict,
                    state_dict,
                    dict(event),
                ),
                {},
            ),
            (
                (
                    prediction_dict,
                    state_dict,
                ),
                {},
            ),
            (
                (prediction_dict,),
                {},
            ),
            (
                (prediction,),
                {},
            ),
        )

        return _invoke_compatible(
            method,
            attempts,
            "Policy evaluation",
        )

    # ========================================================================
    # Decision
    # ========================================================================

    def _make_decision(
        self,
        prediction: Any,
        policy: Any,
        state: Any,
        event: Mapping[str, Any],
    ) -> Any:
        """Generate decision using the native decision contract."""

        method = getattr(
            self._decision_provider,
            "decide",
            None,
        )

        if not callable(method):
            raise OrchestrationComponentError(
                "Decision provider has no decide()."
            )

        prediction_dict = _as_mapping(prediction)
        policy_dict = _as_mapping(policy)
        state_dict = _as_mapping(state)

        attempts = (
            (
                (
                    prediction_dict,
                    policy_dict,
                    state_dict,
                    dict(event),
                ),
                {},
            ),
            (
                (
                    prediction_dict,
                    policy_dict,
                    state_dict,
                ),
                {},
            ),
            (
                (
                    prediction_dict,
                    policy_dict,
                ),
                {},
            ),
            (
                (policy_dict,),
                {},
            ),
            (
                (policy,),
                {},
            ),
        )

        return _invoke_compatible(
            method,
            attempts,
            "Decision generation",
        )

    # ========================================================================
    # Checkpoint planning
    # ========================================================================

    def _create_checkpoint(
        self,
        *,
        state: Any,
        decision: Any,
        operation_id: str,
    ) -> Any:
        """
        Create a checkpoint plan.

        This method never creates or mutates a real system checkpoint
        by itself. It delegates only to the supplied planning provider.
        """

        provider = self._checkpoint_provider

        if provider is None:
            return None

        state_dict = _as_mapping(state)
        decision_dict = _as_mapping(decision)

        metadata = {
            "operation_id": operation_id,
            "source": MODULE_NAME,
            "planning_only": True,
        }

        candidates = (
            (
                (state_dict,),
                {
                    "metadata": metadata,
                },
            ),
            (
                (),
                {
                    "state": state_dict,
                    "metadata": metadata,
                },
            ),
            (
                (
                    state_dict,
                    metadata,
                ),
                {},
            ),
            (
                (),
                {
                    "state": state_dict,
                    "decision": decision_dict,
                    "metadata": metadata,
                },
            ),
        )

        return _dispatch_provider_candidates(
            provider,
            (
                "create",
                "create_checkpoint",
                "plan",
            ),
            candidates,
            "Checkpoint planning",
        )

    # ========================================================================
    # Playbook planning
    # ========================================================================

    def _create_playbook(
        self,
        *,
        decision: Any,
        state: Any,
        prediction: Any,
        operation_id: str,
    ) -> Any:
        """
        Create a playbook plan.

        The resulting object is a plan only.
        It is not executed by the orchestrator.
        """

        provider = self._playbook_provider

        if provider is None:
            return None

        decision_dict = _as_mapping(decision)
        state_dict = _as_mapping(state)
        prediction_dict = _as_mapping(prediction)

        decision_id = _extract_id(
            decision,
            (
                "decision_id",
                "id",
            ),
        )

        state_id = _extract_id(
            state,
            (
                "state_id",
                "id",
            ),
        )

        metadata = {
            "operation_id": operation_id,
            "source": MODULE_NAME,
            "planning_only": True,
        }

        candidates = (
            (
                (decision_dict,),
                {
                    "decision_id": decision_id,
                    "state_id": state_id,
                },
            ),
            (
                (decision_dict,),
                {
                    "decision_id": decision_id,
                },
            ),
            (
                (decision_dict,),
                {},
            ),
            (
                (),
                {
                    "decision": decision_dict,
                    "decision_id": decision_id,
                    "state_id": state_id,
                    "metadata": metadata,
                },
            ),
            (
                (
                    decision_dict,
                    state_dict,
                    prediction_dict,
                ),
                {},
            ),
        )

        return _dispatch_provider_candidates(
            provider,
            (
                "create",
                "plan",
                "build",
            ),
            candidates,
            "Playbook planning",
        )

    # ========================================================================
    # Rollback planning
    # ========================================================================

    def _create_rollback(
        self,
        *,
        decision: Any,
        checkpoint: Any,
        state: Any,
        operation_id: str,
    ) -> Any:
        """
        Create a rollback plan.

        No rollback operation is executed here.
        """

        provider = self._rollback_provider

        if provider is None:
            return None

        request = {
            "operation_id": operation_id,
            "decision": _as_mapping(decision),
            "checkpoint": _as_mapping(checkpoint),
            "state": _as_mapping(state),
            "planning_only": True,
            "source": MODULE_NAME,
        }

        candidates = (
            (
                (request,),
                {},
            ),
            (
                (),
                {
                    "request": request,
                },
            ),
            (
                (
                    _as_mapping(decision),
                    _as_mapping(checkpoint),
                ),
                {},
            ),
            (
                (
                    _as_mapping(decision),
                ),
                {},
            ),
        )

        return _dispatch_provider_candidates(
            provider,
            (
                "plan",
                "create",
            ),
            candidates,
            "Rollback planning",
        )

    # ========================================================================
    # Validation
    # ========================================================================

    @staticmethod
    def _validate_event(
        event: Mapping[str, Any],
    ) -> None:
        """Validate orchestration event."""

        if not isinstance(event, Mapping):
            raise OrchestrationValidationError(
                "event must be a mapping."
            )

        if not event:
            raise OrchestrationValidationError(
                "event must not be empty."
            )

    @staticmethod
    def _validate_component(
        component: Any,
        name: str,
        methods: tuple[str, ...],
    ) -> None:
        """Validate that a provider exposes at least one supported method."""

        if component is None:
            raise OrchestrationValidationError(
                f"{name} is required."
            )

        if not any(
            callable(
                getattr(
                    component,
                    method,
                    None,
                )
            )
            for method in methods
        ):
            raise OrchestrationValidationError(
                f"{name} does not implement a supported contract."
            )

    @staticmethod
    def _component_has_method(
        component: Any,
        method: str,
    ) -> bool:
        """Return whether component exposes a callable method."""

        return callable(
            getattr(
                component,
                method,
                None,
            )
        )

    @staticmethod
    def _component_has_any_method(
        component: Any,
        methods: tuple[str, ...],
    ) -> bool:
        """Return whether component exposes any supported method."""

        return any(
            ADIEOrchestrator._component_has_method(
                component,
                method,
            )
            for method in methods
        )

    # ========================================================================
    # Operation identity
    # ========================================================================

    @staticmethod
    def _create_operation_id() -> str:
        """
        Generate a globally unique orchestration operation identifier.

        UUID4 is intentionally used because two identical observations
        must still represent two independent orchestration operations.
        """

        return "adie-op-" + uuid.uuid4().hex


# ============================================================================
# Invocation helpers
# ============================================================================


def _invoke_compatible(
    method: Any,
    attempts: tuple[
        tuple[
            tuple[Any, ...],
            dict[str, Any],
        ],
        ...,
    ],
    label: str,
) -> Any:
    """
    Invoke a provider using the first compatible contract.

    Compatibility is determined with inspect.signature() before
    invocation whenever possible.

    Important:
    A TypeError raised from inside a successfully-bound provider
    is treated as a provider failure, not as a compatibility signal.
    """

    signature = None

    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        signature = None

    last_bind_error: Optional[Exception] = None

    for args, kwargs in attempts:
        if signature is not None:
            try:
                signature.bind(
                    *args,
                    **kwargs,
                )
            except TypeError as exc:
                last_bind_error = exc
                continue

        try:
            result = method(
                *args,
                **kwargs,
            )

        except Exception as exc:
            raise OrchestrationComponentError(
                f"{label} failed."
            ) from exc

        if result is None:
            raise OrchestrationComponentError(
                f"{label} returned None."
            )

        return _safe_serialize(result)

    raise OrchestrationComponentError(
        f"{label} contract is incompatible."
    ) from last_bind_error


def _dispatch_provider_candidates(
    provider: Any,
    method_names: tuple[str, ...],
    candidates: tuple[
        tuple[
            tuple[Any, ...],
            dict[str, Any],
        ],
        ...,
    ],
    label: str,
) -> Any:
    """
    Dispatch a provider operation through supported method names.

    Method precedence is explicit and deterministic.

    No monkey-patching is used.
    """

    found_method = False
    last_bind_error: Optional[Exception] = None

    for method_name in method_names:
        method = getattr(
            provider,
            method_name,
            None,
        )

        if not callable(method):
            continue

        found_method = True

        signature = None

        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            signature = None

        for args, kwargs in candidates:
            if signature is not None:
                try:
                    signature.bind(
                        *args,
                        **kwargs,
                    )
                except TypeError as exc:
                    last_bind_error = exc
                    continue

            try:
                result = method(
                    *args,
                    **kwargs,
                )

            except Exception as exc:
                raise OrchestrationComponentError(
                    f"{label} failed."
                ) from exc

            if result is None:
                raise OrchestrationComponentError(
                    f"{label} returned None."
                )

            return _safe_serialize(result)

    if not found_method:
        raise OrchestrationComponentError(
            f"{label} provider has no supported method."
        )

    raise OrchestrationComponentError(
        f"{label} contract is incompatible."
    ) from last_bind_error


def _can_bind(
    signature: inspect.Signature,
    *args: Any,
    **kwargs: Any,
) -> bool:
    """Return whether a signature accepts the supplied arguments."""

    try:
        signature.bind(
            *args,
            **kwargs,
        )
        return True

    except TypeError:
        return False


# ============================================================================
# Serialization
# ============================================================================


def _safe_serialize(
    value: Any,
) -> Any:
    """
    Convert an arbitrary provider result into JSON-safe structures.

    The function is deliberately defensive and never executes arbitrary
    callables other than a conventional object's to_dict() serializer.
    """

    if value is None:
        return None

    if isinstance(value, Enum):
        return _safe_serialize(value.value)

    if isinstance(value, Mapping):
        return {
            str(key): _safe_serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            _safe_serialize(item)
            for item in value
        ]

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

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

    if hasattr(value, "__dict__"):
        try:
            return _safe_serialize(
                dict(value.__dict__)
            )
        except Exception:
            return {
                "type": type(value).__name__,
            }

    return str(value)


def _as_mapping(
    value: Any,
) -> Mapping[str, Any]:
    """Normalize arbitrary values into mapping form."""

    serialized = _safe_serialize(value)

    if isinstance(serialized, Mapping):
        return serialized

    return {
        "value": serialized,
    }


def _extract_id(
    value: Any,
    names: tuple[str, ...],
) -> Optional[str]:
    """Extract a stable identifier from a serialized provider object."""

    serialized = _safe_serialize(value)

    if not isinstance(serialized, Mapping):
        return None

    for name in names:
        candidate = serialized.get(name)

        if candidate is not None:
            return str(candidate)

    return None


# ============================================================================
# Policy helpers
# ============================================================================


def _is_policy_blocked(
    policy: Any,
) -> bool:
    """
    Determine whether policy explicitly blocks the proposed operation.

    Fail-closed semantics are intentionally NOT applied to missing
    fields here. A malformed policy is handled as a component failure
    by explicit validation in the policy stage rather than silently
    interpreting an incomplete object as allowed.
    """

    data = _as_mapping(policy)

    for key in (
        "blocked",
        "is_blocked",
    ):
        if data.get(key) is True:
            return True

    if data.get("allowed") is False:
        return True

    status = str(
        data.get(
            "status",
            "",
        )
    ).strip().lower()

    if status in {
        "blocked",
        "denied",
        "rejected",
    }:
        return True

    return False


# ============================================================================
# Fingerprint
# ============================================================================


def _fingerprint_result(
    result: OrchestrationResult,
) -> str:
    """
    Calculate a SHA-256 fingerprint over the immutable result payload.

    Timestamps and the fingerprint itself are intentionally excluded
    from the material so the fingerprint represents the orchestration
    content rather than wall-clock metadata.
    """

    material = {
        "operation_id": result.operation_id,
        "status": result.status.value,
        "state": _safe_serialize(result.state),
        "prediction": _safe_serialize(result.prediction),
        "policy": _safe_serialize(result.policy),
        "decision": _safe_serialize(result.decision),
        "checkpoint": _safe_serialize(result.checkpoint),
        "playbook": _safe_serialize(result.playbook),
        "rollback": _safe_serialize(result.rollback),
        "failed_stage": result.failed_stage,
        "error": result.error,
        "executes_security_actions": (
            result.executes_security_actions
        ),
        "destructive_actions_allowed": (
            result.destructive_actions_allowed
        ),
    }

    canonical = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ============================================================================
# Miscellaneous helpers
# ============================================================================


def _utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def _safe_exception_message(
    exc: Exception,
) -> str:
    """
    Return a safe external error representation.

    Arbitrary exception text is deliberately not exposed because
    provider exceptions may contain internal implementation details,
    paths, credentials, hostnames, or other sensitive information.
    """

    return (
        f"{type(exc).__name__}: "
        "orchestration failed."
    )


# ============================================================================
# Self-test providers
# ============================================================================


class _TestState:
    """Deterministic state provider for self-test."""

    def collect(
        self,
        event: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "state_id": "state-test-001",
            "state_version": 1,
            "system": "test",
            "event": dict(event),
        }


class _TestPrediction:
    """Deterministic prediction provider for self-test."""

    def predict(
        self,
        state: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "prediction_id": "prediction-test-001",
            "predicted_class": "threat",
            "threat_probability": 0.91,
            "benign_probability": 0.09,
        }


class _TestPolicy:
    """Deterministic policy provider for self-test."""

    def evaluate(
        self,
        prediction: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "policy_id": "policy-test-001",
            "allowed": True,
            "risk_level": "high",
        }


class _TestDecision:
    """Deterministic decision provider for self-test."""

    def decide(
        self,
        prediction: Mapping[str, Any],
        policy: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "decision_id": "decision-test-001",
            "action": "alert",
            "authorized": True,
            "risk_level": "high",
        }


class _TestCheckpoint:
    """Deterministic checkpoint planning provider."""

    def create(
        self,
        state: Mapping[str, Any],
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> Mapping[str, Any]:
        return {
            "checkpoint_id": "checkpoint-test-001",
            "created": True,
            "metadata": dict(
                metadata or {}
            ),
        }


class _TestPlaybook:
    """Deterministic playbook planning provider."""

    def create(
        self,
        decision: Mapping[str, Any],
        *,
        decision_id: Optional[str] = None,
        state_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        return {
            "playbook_id": "playbook-test-001",
            "planned": True,
            "decision_id": decision_id,
            "state_id": state_id,
        }


class _TestRollback:
    """Deterministic rollback planning provider."""

    def plan(
        self,
        request: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "rollback_id": "rollback-test-001",
            "planned": True,
            "operation_id": request.get(
                "operation_id"
            ),
        }


class _FailingPlaybook:
    """Intentional failure provider for failure-isolation testing."""

    def create(
        self,
        decision: Mapping[str, Any],
        **kwargs: Any,
    ) -> Mapping[str, Any]:
        raise RuntimeError(
            "intentional self-test failure"
        )


class _BlockedPolicy:
    """Deterministic blocked policy provider."""

    def evaluate(
        self,
        prediction: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "policy_id": "policy-blocked",
            "allowed": False,
            "status": "blocked",
        }


# ============================================================================
# Self-test
# ============================================================================


def self_test() -> dict[str, Any]:
    """
    Execute deterministic orchestrator tests.

    No real security component is executed.
    """

    tests = {
        "provider_validation": False,
        "event_validation": False,
        "state_collection": False,
        "prediction_stage": False,
        "policy_stage": False,
        "decision_stage": False,
        "checkpoint_planning": False,
        "playbook_planning": False,
        "rollback_planning": False,
        "blocked_policy": False,
        "failure_isolation": False,
        "immutable_result": False,
        "operation_identity": False,
        "fingerprint_contract": False,
        "fingerprint_stability": False,
        "json_export": False,
        "metadata_contract": False,
        "health_contract": False,
        "status_contract": False,
        "execution_safety": False,
        "destructive_action_block": False,
        "no_monkey_patch_contract": False,
    }

    # ========================================================================
    # Provider validation
    # ========================================================================

    try:
        ADIEOrchestrator(
            None,
            _TestPrediction(),
            _TestPolicy(),
            _TestDecision(),
        )

    except OrchestrationValidationError:
        tests["provider_validation"] = True

    # ========================================================================
    # Event validation
    # ========================================================================

    try:
        ADIEOrchestrator(
            _TestState(),
            _TestPrediction(),
            _TestPolicy(),
            _TestDecision(),
        ).orchestrate({})

    except OrchestrationValidationError:
        tests["event_validation"] = True

    # ========================================================================
    # Main pipeline
    # ========================================================================

    orchestrator = ADIEOrchestrator(
        _TestState(),
        _TestPrediction(),
        _TestPolicy(),
        _TestDecision(),
        checkpoint_provider=_TestCheckpoint(),
        playbook_provider=_TestPlaybook(),
        rollback_provider=_TestRollback(),
    )

    event = {
        "event_type": "self_test",
        "source": MODULE_NAME,
        "value": 1,
    }

    result = orchestrator.orchestrate(
        event,
        create_checkpoint=True,
        create_playbook=True,
        create_rollback=True,
    )

    tests["state_collection"] = (
        isinstance(result.state, Mapping)
        and result.state.get("state_id")
        == "state-test-001"
    )

    tests["prediction_stage"] = (
        isinstance(result.prediction, Mapping)
        and result.prediction.get("predicted_class")
        == "threat"
    )

    tests["policy_stage"] = (
        isinstance(result.policy, Mapping)
        and result.policy.get("allowed") is True
    )

    tests["decision_stage"] = (
        isinstance(result.decision, Mapping)
        and result.decision.get("action")
        == "alert"
    )

    tests["checkpoint_planning"] = (
        isinstance(result.checkpoint, Mapping)
        and result.checkpoint.get("created") is True
    )

    tests["playbook_planning"] = (
        isinstance(result.playbook, Mapping)
        and result.playbook.get("planned") is True
        and result.playbook.get("decision_id")
        == "decision-test-001"
        and result.playbook.get("state_id")
        == "state-test-001"
    )

    tests["rollback_planning"] = (
        isinstance(result.rollback, Mapping)
        and result.rollback.get("planned") is True
    )

    # ========================================================================
    # Blocked policy
    # ========================================================================

    blocked_orchestrator = ADIEOrchestrator(
        _TestState(),
        _TestPrediction(),
        _BlockedPolicy(),
        _TestDecision(),
    )

    blocked = blocked_orchestrator.orchestrate(
        {
            "event_type": "blocked-test",
        },
        create_checkpoint=False,
        create_playbook=False,
        create_rollback=False,
    )

    tests["blocked_policy"] = (
        blocked.status
        == OrchestrationStatus.BLOCKED
        and isinstance(
            blocked.policy,
            Mapping,
        )
        and blocked.policy.get("allowed") is False
        and blocked.failed_stage is None
    )

    # ========================================================================
    # Failure isolation
    # ========================================================================

    failing_orchestrator = ADIEOrchestrator(
        _TestState(),
        _TestPrediction(),
        _TestPolicy(),
        _TestDecision(),
        playbook_provider=_FailingPlaybook(),
    )

    failed = failing_orchestrator.orchestrate(
        {
            "event_type": "failure-test",
        },
        create_checkpoint=False,
        create_playbook=True,
        create_rollback=False,
    )

    tests["failure_isolation"] = (
        failed.status
        == OrchestrationStatus.FAILED
        and failed.failed_stage
        == "playbook"
        and failed.executes_security_actions
        is False
    )

    # ========================================================================
    # Immutability
    # ========================================================================

    try:
        result.status = OrchestrationStatus.FAILED
        tests["immutable_result"] = False

    except (TypeError, AttributeError):
        tests["immutable_result"] = True

    # ========================================================================
    # Operation identity
    # ========================================================================

    second = orchestrator.orchestrate(
        event,
        create_checkpoint=False,
        create_playbook=False,
        create_rollback=False,
    )

    tests["operation_identity"] = (
        result.operation_id != second.operation_id
        and result.operation_id.startswith("adie-op-")
        and second.operation_id.startswith("adie-op-")
    )

    # ========================================================================
    # Fingerprint contract
    # ========================================================================

    tests["fingerprint_contract"] = (
        isinstance(
            result.fingerprint,
            str,
        )
        and len(result.fingerprint) == 64
        and all(
            character in "0123456789abcdef"
            for character in result.fingerprint
        )
    )

    # ========================================================================
    # Fingerprint stability
    # ========================================================================

    reconstructed = OrchestrationResult(
        operation_id=result.operation_id,
        status=result.status,
        state=result.state,
        prediction=result.prediction,
        policy=result.policy,
        decision=result.decision,
        checkpoint=result.checkpoint,
        playbook=result.playbook,
        rollback=result.rollback,
        created_at="different-created-at",
        completed_at="different-completed-at",
        failed_stage=result.failed_stage,
        error=result.error,
        executes_security_actions=False,
        destructive_actions_allowed=False,
    )

    tests["fingerprint_stability"] = (
        reconstructed.fingerprint
        == result.fingerprint
    )

    # ========================================================================
    # JSON export
    # ========================================================================

    try:
        encoded = json.dumps(
            result.to_dict(),
            sort_keys=True,
        )

        decoded = json.loads(encoded)

        tests["json_export"] = (
            isinstance(decoded, dict)
            and decoded.get("operation_id")
            == result.operation_id
            and decoded.get("fingerprint")
            == result.fingerprint
        )

    except Exception:
        tests["json_export"] = False

    # ========================================================================
    # Metadata
    # ========================================================================

    status = orchestrator.status()

    tests["metadata_contract"] = (
        status.get("module") == MODULE_NAME
        and status.get("version")
        == ORCHESTRATOR_VERSION
        and status.get("planning_only") is True
    )

    # ========================================================================
    # Health
    # ========================================================================

    health = orchestrator.health_check()

    tests["health_contract"] = (
        health.get("healthy") is True
        and health.get("module") == MODULE_NAME
        and health.get("executes_security_actions")
        is False
    )

    # ========================================================================
    # Status
    # ========================================================================

    tests["status_contract"] = (
        status.get("total_runs") >= 2
        and status.get("successful_runs") >= 2
        and status.get("blocked_runs") == 0
        and status.get("failed_runs") == 0
    )

    # ========================================================================
    # Security boundary
    # ========================================================================

    tests["execution_safety"] = (
        EXECUTES_SECURITY_ACTIONS is False
        and orchestrator.executes_security_actions is False
        and result.executes_security_actions is False
    )

    tests["destructive_action_block"] = (
        DESTRUCTIVE_ACTIONS_ALLOWED is False
        and orchestrator.destructive_actions_allowed is False
        and result.destructive_actions_allowed is False
    )

    # ========================================================================
    # Architecture integrity
    # ========================================================================

    tests["no_monkey_patch_contract"] = (
        ADIEOrchestrator._create_checkpoint.__module__
        == __name__
        and ADIEOrchestrator._create_playbook.__module__
        == __name__
        and ADIEOrchestrator._create_rollback.__module__
        == __name__
    )

    passed = all(tests.values())

    return {
        "passed": passed,
        "module": MODULE_NAME,
        "version": ORCHESTRATOR_VERSION,
        "orchestration_test_passed": passed,
        "tests": tests,
        "executes_security_actions": False,
        "destructive_actions_allowed": False,
    }


# ============================================================================
# Module entry point
# ============================================================================


if __name__ == "__main__":
    print(
        json.dumps(
            self_test(),
            indent=2,
            sort_keys=True,
        )
    )