"""
EnterpriseGuard - Response Executor
====================================

Controlled Autonomous Response Architecture
--------------------------------------------

The Response Executor is the controlled execution boundary between:

    Intelligence Engine
            |
            v
      Response Engine
            |
            v
     Response Executor
            |
            v
     Registered Adapters
            |
            v
       External Systems

Design principles
-----------------

1. Never execute arbitrary shell commands.
2. Never execute destructive actions by default.
3. Require explicit authorization for high/critical actions.
4. Support DRY_RUN as the default execution mode.
5. Enforce action allow-lists through registered adapters.
6. Provide idempotent execution.
7. Provide verification hooks.
8. Provide audit hooks.
9. Reject malformed or unsafe plans.
10. Keep execution deterministic and auditable.
11. Maintain operational statistics.
12. Support future autonomous response without compromising safety.
13. Make security policy explicit and inspectable.
14. Keep the executor independent from the intelligence/model layer.
15. Make self-test validate the security guarantees themselves.

This module intentionally contains no arbitrary OS command execution.
Actual integrations must be implemented through explicitly registered
adapters.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional


# ============================================================================
# Constants
# ============================================================================

ENGINE_NAME = "EnterpriseGuard Response Executor"
ENGINE_VERSION = "2.0.0"

DEFAULT_MAX_INPUT_SIZE = 1_000_000
DEFAULT_MAX_ACTIONS = 16
DEFAULT_PROCESSING_TARGET_MS = 50.0


# ============================================================================
# Enums
# ============================================================================


class ExecutionMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    MANUAL_APPROVAL = "MANUAL_APPROVAL"
    AUTOMATIC = "AUTOMATIC"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ActionStatus(str, Enum):
    EXECUTED = "EXECUTED"
    SIMULATED = "SIMULATED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ApprovalLevel(str, Enum):
    NONE = "NONE"
    OPERATOR = "OPERATOR"
    SECURITY_ANALYST = "SECURITY_ANALYST"
    SECURITY_ADMIN = "SECURITY_ADMIN"


class ActionType(str, Enum):
    NONE = "NONE"
    CREATE_ALERT = "CREATE_ALERT"
    ESCALATE = "ESCALATE"
    MONITOR = "MONITOR"
    CONTAIN = "CONTAIN"
    ISOLATE = "ISOLATE"
    TERMINATE_PROCESS = "TERMINATE_PROCESS"
    MODIFY_ACCOUNT = "MODIFY_ACCOUNT"
    BLOCK_SOURCE = "BLOCK_SOURCE"


# ============================================================================
# Utility functions
# ============================================================================


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str, length: int = 24) -> str:
    """Generate a compact EnterpriseGuard identifier."""
    raw = uuid.uuid4().hex.upper()
    return f"{prefix}-{raw[:length]}"


def safe_json_size(value: Any) -> int:
    """Return serialized JSON size without allowing serialization errors to escape."""
    try:
        return len(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        )
    except Exception:
        return 0


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def normalize_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def action_type(value: Any) -> str:
    if isinstance(value, ActionType):
        return value.value
    return normalize_string(value).upper()


def severity(value: Any) -> str:
    return normalize_string(value).upper()


def approval_rank(value: Any) -> int:
    ranks = {
        ApprovalLevel.NONE.value: 0,
        ApprovalLevel.OPERATOR.value: 1,
        ApprovalLevel.SECURITY_ANALYST.value: 2,
        ApprovalLevel.SECURITY_ADMIN.value: 3,
    }
    return ranks.get(normalize_string(value).upper(), -1)


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


# ============================================================================
# Exceptions
# ============================================================================


class ExecutorError(Exception):
    """Base exception for Response Executor."""


class ValidationError(ExecutorError):
    """Raised when input validation fails."""


class SafetyPolicyError(ExecutorError):
    """Raised when an action violates the security policy."""


class AuthorizationError(ExecutorError):
    """Raised when authorization is insufficient."""


class AdapterError(ExecutorError):
    """Raised when an adapter fails."""


# ============================================================================
# Data models
# ============================================================================


@dataclass
class ExecutorConfig:
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN

    automatic_execution_enabled: bool = False

    allow_destructive_actions: bool = False
    allow_shell_execution: bool = False
    allow_network_isolation: bool = False
    allow_process_termination: bool = False
    allow_account_modification: bool = False

    require_approval_for_high: bool = True
    require_approval_for_critical: bool = True

    audit_enabled: bool = True
    idempotency_enabled: bool = True

    processing_target_ms: float = DEFAULT_PROCESSING_TARGET_MS
    max_input_size: int = DEFAULT_MAX_INPUT_SIZE
    max_actions_per_request: int = DEFAULT_MAX_ACTIONS


@dataclass
class ActionContext:
    response_id: str
    request_id: str
    action_id: str

    threat_type: str
    severity: str

    risk_score: float
    confidence: float

    parameters: Dict[str, Any] = field(default_factory=dict)

    approval_level: str = ApprovalLevel.NONE.value
    approval_granted: bool = False

    execution_mode: str = ExecutionMode.DRY_RUN.value

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterResult:
    success: bool
    executed: bool
    simulated: bool

    action_type: str

    message: str = ""

    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionExecutionResult:
    action_id: str
    action_type: str

    status: str
    simulated: bool

    started_at: str
    completed_at: str

    processing_time_ms: float

    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


# ============================================================================
# Default adapters
# ============================================================================


class BaseAdapter:
    """
    Base adapter.

    Adapters are intentionally explicit.
    An adapter may only be registered for a known action type.
    """

    name = "base"

    def execute(self, context: ActionContext) -> AdapterResult:
        raise NotImplementedError


class DryRunAdapter(BaseAdapter):
    """Safe adapter used for actions that have no execution integration."""

    name = "dry-run"

    def execute(self, context: ActionContext) -> AdapterResult:
        return AdapterResult(
            success=True,
            executed=False,
            simulated=True,
            action_type=context.parameters.get(
                "action_type",
                ActionType.NONE.value,
            ),
            message="Action simulated safely. No system modification occurred.",
            data={
                "execution_mode": ExecutionMode.DRY_RUN.value,
            },
        )


class AlertAdapter(BaseAdapter):
    """
    Non-destructive alert adapter.

    This implementation records the intent only.
    A production SIEM/SOC integration can replace this adapter later.
    """

    name = "alert"

    def execute(self, context: ActionContext) -> AdapterResult:
        return AdapterResult(
            success=True,
            executed=False,
            simulated=True,
            action_type=ActionType.CREATE_ALERT.value,
            message="Alert creation simulated safely.",
            data={
                "alert": {
                    "response_id": context.response_id,
                    "request_id": context.request_id,
                    "threat_type": context.threat_type,
                    "severity": context.severity,
                    "risk_score": context.risk_score,
                    "confidence": context.confidence,
                }
            },
        )


class EscalationAdapter(BaseAdapter):
    """
    Non-destructive escalation adapter.

    It creates an escalation intent but performs no external action.
    """

    name = "escalation"

    def execute(self, context: ActionContext) -> AdapterResult:
        return AdapterResult(
            success=True,
            executed=False,
            simulated=True,
            action_type=ActionType.ESCALATE.value,
            message="Escalation simulated safely.",
            data={
                "escalation": {
                    "response_id": context.response_id,
                    "request_id": context.request_id,
                    "approval_level": context.approval_level,
                }
            },
        )


# ============================================================================
# Response Executor
# ============================================================================


class ResponseExecutor:
    """
    EnterpriseGuard controlled response execution boundary.
    """

    def __init__(
        self,
        config: Optional[ExecutorConfig] = None,
        *,
        audit_logger: Optional[Any] = None,
        verification_hook: Optional[
            Callable[[Mapping[str, Any]], Mapping[str, Any]]
        ] = None,
    ) -> None:

        self.config = config or ExecutorConfig()

        self.audit_logger = audit_logger
        self.verification_hook = verification_hook

        self._lock = RLock()

        self._adapters: Dict[str, BaseAdapter] = {}
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}

        self._statistics: Dict[str, float] = {
            "total_requests": 0,
            "successful_requests": 0,
            "partial_requests": 0,
            "rejected_requests": 0,
            "failed_requests": 0,
            "actions_requested": 0,
            "actions_executed": 0,
            "actions_simulated": 0,
            "actions_rejected": 0,
            "actions_failed": 0,
            "approval_required": 0,
            "average_processing_ms": 0.0,
            "max_processing_ms": 0.0,
        }

        self._status_counts: Dict[str, int] = {
            ExecutionStatus.SUCCESS.value: 0,
            ExecutionStatus.PARTIAL.value: 0,
            ExecutionStatus.REJECTED.value: 0,
            ExecutionStatus.FAILED.value: 0,
            ExecutionStatus.SKIPPED.value: 0,
        }

        self._action_status_counts: Dict[str, int] = {
            ActionStatus.EXECUTED.value: 0,
            ActionStatus.SIMULATED.value: 0,
            ActionStatus.REJECTED.value: 0,
            ActionStatus.FAILED.value: 0,
            ActionStatus.SKIPPED.value: 0,
        }

        self._action_type_counts: Dict[str, int] = {}

        self._register_default_adapters()

    # ---------------------------------------------------------------------
    # Adapter registration
    # ---------------------------------------------------------------------

    def _register_default_adapters(self) -> None:
        self.register_adapter(ActionType.NONE.value, DryRunAdapter())
        self.register_adapter(ActionType.CREATE_ALERT.value, AlertAdapter())
        self.register_adapter(ActionType.ESCALATE.value, EscalationAdapter())

    def register_adapter(
        self,
        action: str,
        adapter: BaseAdapter,
    ) -> None:
        action_name = action_type(action)

        if not action_name:
            raise ValueError("Adapter action cannot be empty.")

        if not isinstance(adapter, BaseAdapter):
            raise TypeError("adapter must inherit from BaseAdapter.")

        with self._lock:
            self._adapters[action_name] = adapter

    def unregister_adapter(self, action: str) -> bool:
        action_name = action_type(action)

        with self._lock:
            if action_name in {
                ActionType.NONE.value,
                ActionType.CREATE_ALERT.value,
                ActionType.ESCALATE.value,
            }:
                return False

            return self._adapters.pop(action_name, None) is not None

    # ---------------------------------------------------------------------
    # Properties
    # ---------------------------------------------------------------------

    @property
    def execution_enabled(self) -> bool:
        return bool(
            self.config.automatic_execution_enabled
            and self.config.execution_mode == ExecutionMode.AUTOMATIC
        )

    # ---------------------------------------------------------------------
    # Status / health
    # ---------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        with self._lock:
            total = self._statistics["total_requests"]
            successful = self._statistics["successful_requests"]

            planning_success_rate = (
                (successful / total) * 100.0 if total else 0.0
            )

            return {
                "engine": ENGINE_NAME,
                "version": ENGINE_VERSION,
                "status": "active",
                "configuration": {
                    "execution_mode": self.config.execution_mode.value,
                    "automatic_execution_enabled":
                        self.config.automatic_execution_enabled,
                    "allow_destructive_actions":
                        self.config.allow_destructive_actions,
                    "allow_shell_execution":
                        self.config.allow_shell_execution,
                    "allow_network_isolation":
                        self.config.allow_network_isolation,
                    "allow_process_termination":
                        self.config.allow_process_termination,
                    "allow_account_modification":
                        self.config.allow_account_modification,
                    "require_approval_for_high":
                        self.config.require_approval_for_high,
                    "require_approval_for_critical":
                        self.config.require_approval_for_critical,
                    "audit_enabled": self.config.audit_enabled,
                    "idempotency_enabled":
                        self.config.idempotency_enabled,
                    "processing_target_ms":
                        self.config.processing_target_ms,
                    "max_input_size":
                        self.config.max_input_size,
                    "max_actions_per_request":
                        self.config.max_actions_per_request,
                },
                "statistics": {
                    **self._statistics,
                    "planning_success_rate":
                        round(planning_success_rate, 3),
                },
                "status_counts": dict(self._status_counts),
                "action_status_counts":
                    dict(self._action_status_counts),
                "action_type_counts":
                    dict(self._action_type_counts),
                "adapters": {
                    key: {
                        "adapter": adapter.name,
                        "action": key,
                        "destructive":
                            self._is_destructive_action(key),
                    }
                    for key, adapter in self._adapters.items()
                },
                "execution": {
                    "automatic_execution":
                        self.execution_enabled,
                    "executor_ready": True,
                    "note":
                        "Execution is controlled by explicit policy, "
                        "authorization, safety gates, and registered adapters.",
                },
                "safety": {
                    "destructive_actions_enabled":
                        self.config.allow_destructive_actions,
                    "shell_execution_enabled":
                        self.config.allow_shell_execution,
                    "network_isolation_enabled":
                        self.config.allow_network_isolation,
                    "process_termination_enabled":
                        self.config.allow_process_termination,
                    "account_modification_enabled":
                        self.config.allow_account_modification,
                },
                "notes": {
                    "execution":
                        "The executor never executes arbitrary commands.",
                    "authorization":
                        "High and critical actions require explicit "
                        "authorization by default.",
                    "verification":
                        "Verification is available through a dedicated hook.",
                },
            }

    def health_check(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "healthy": True,
                "engine": {
                    "enabled": True,
                    "version": ENGINE_VERSION,
                },
                "execution": {
                    "mode": self.config.execution_mode.value,
                    "automatic_execution": self.execution_enabled,
                },
                "adapters": {
                    "available": bool(self._adapters),
                    "count": len(self._adapters),
                },
                "verification": {
                    "attached": self.verification_hook is not None,
                },
                "audit": {
                    "enabled": self.config.audit_enabled,
                    "attached": self.audit_logger is not None,
                },
                "safety": {
                    "destructive_actions_enabled":
                        self.config.allow_destructive_actions,
                    "shell_execution_enabled":
                        self.config.allow_shell_execution,
                    "network_isolation_enabled":
                        self.config.allow_network_isolation,
                    "process_termination_enabled":
                        self.config.allow_process_termination,
                    "account_modification_enabled":
                        self.config.allow_account_modification,
                },
            }

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------

    def _validate_plan(
        self,
        plan: Mapping[str, Any],
    ) -> None:

        if not isinstance(plan, Mapping):
            raise ValidationError("Response plan must be a mapping.")

        if not plan:
            raise ValidationError("Response plan cannot be empty.")

        if safe_json_size(plan) > self.config.max_input_size:
            raise ValidationError(
                "Response plan exceeds maximum input size."
            )

        response_id = normalize_string(plan.get("response_id"))
        request_id = normalize_string(plan.get("request_id"))

        if not response_id:
            raise ValidationError("Response plan response_id is required.")

        if not request_id:
            raise ValidationError("Response plan request_id is required.")

        severity_value = severity(plan.get("severity", "LOW"))

        valid_severities = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }

        if severity_value not in valid_severities:
            raise ValidationError("Unknown threat severity.")

        actions = plan.get("actions", [])

        if not isinstance(actions, list):
            raise ValidationError("Response plan actions must be a list.")

        if len(actions) > self.config.max_actions_per_request:
            raise ValidationError(
                "Response plan contains too many actions."
            )

        for action in actions:
            if not isinstance(action, Mapping):
                raise ValidationError(
                    "Each response action must be a mapping."
                )

            if not normalize_string(action.get("action_id")):
                raise ValidationError(
                    "Each response action requires action_id."
                )

            if not action_type(action.get("action_type")):
                raise ValidationError(
                    "Each response action requires action_type."
                )

    # ---------------------------------------------------------------------
    # Security policy
    # ---------------------------------------------------------------------

    def _is_destructive_action(self, action: str) -> bool:
        return action_type(action) in {
            ActionType.CONTAIN.value,
            ActionType.ISOLATE.value,
            ActionType.TERMINATE_PROCESS.value,
            ActionType.MODIFY_ACCOUNT.value,
            ActionType.BLOCK_SOURCE.value,
        }

    def _action_policy_allowed(
        self,
        action: str,
        parameters: Mapping[str, Any],
    ) -> None:

        action_name = action_type(action)

        # --------------------------------------------------------------
        # Absolute protection against arbitrary command execution.
        # --------------------------------------------------------------

        forbidden_command_keys = {
            "command",
            "cmd",
            "shell",
            "shell_command",
            "powershell",
            "powershell_command",
            "os_command",
            "subprocess",
            "exec",
            "execute_command",
        }

        provided_keys = {
            normalize_string(key).lower()
            for key in parameters.keys()
        }

        if provided_keys.intersection(forbidden_command_keys):
            if not self.config.allow_shell_execution:
                raise SafetyPolicyError(
                    "Shell or command execution parameters are disabled by policy."
                )

            # Even when the future flag is enabled, the executor still
            # does not directly execute arbitrary commands.
            raise SafetyPolicyError(
                "Arbitrary shell execution is not supported by Response Executor."
            )

        # --------------------------------------------------------------
        # Destructive action gates.
        # --------------------------------------------------------------

        if self._is_destructive_action(action_name):

            if not self.config.allow_destructive_actions:
                raise SafetyPolicyError(
                    "Destructive response execution is disabled by safety policy."
                )

            if action_name == ActionType.ISOLATE.value:
                if not self.config.allow_network_isolation:
                    raise SafetyPolicyError(
                        "Network isolation is disabled by safety policy."
                    )

            if action_name == ActionType.TERMINATE_PROCESS.value:
                if not self.config.allow_process_termination:
                    raise SafetyPolicyError(
                        "Process termination is disabled by safety policy."
                    )

            if action_name == ActionType.MODIFY_ACCOUNT.value:
                if not self.config.allow_account_modification:
                    raise SafetyPolicyError(
                        "Account modification is disabled by safety policy."
                    )

        # --------------------------------------------------------------
        # Known action registry.
        # --------------------------------------------------------------

        if action_name not in self._adapters:
            raise SafetyPolicyError(
                f"No registered adapter exists for action: {action_name}."
            )

    # ---------------------------------------------------------------------
    # Authorization
    # ---------------------------------------------------------------------

    def _approval_required(
        self,
        plan: Mapping[str, Any],
    ) -> bool:

        severity_value = severity(plan.get("severity", "LOW"))

        if severity_value == "CRITICAL":
            return self.config.require_approval_for_critical

        if severity_value == "HIGH":
            return self.config.require_approval_for_high

        return False

    def _required_approval_level(
        self,
        plan: Mapping[str, Any],
    ) -> str:

        severity_value = severity(plan.get("severity", "LOW"))

        if severity_value == "CRITICAL":
            return ApprovalLevel.SECURITY_ADMIN.value

        if severity_value == "HIGH":
            return ApprovalLevel.SECURITY_ANALYST.value

        if severity_value == "MEDIUM":
            return ApprovalLevel.OPERATOR.value

        return ApprovalLevel.NONE.value

    def _authorization_granted(
        self,
        plan: Mapping[str, Any],
        approval: Optional[Mapping[str, Any]],
    ) -> bool:

        if not self._approval_required(plan):
            return True

        if not isinstance(approval, Mapping):
            return False

        granted = bool(approval.get("approved", False))

        if not granted:
            return False

        required = self._required_approval_level(plan)

        supplied = normalize_string(
            approval.get("approval_level"),
            ApprovalLevel.NONE.value,
        ).upper()

        return approval_rank(supplied) >= approval_rank(required)

    # ---------------------------------------------------------------------
    # Audit
    # ---------------------------------------------------------------------

    def _audit(
        self,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:

        if not self.config.audit_enabled:
            return {
                "enabled": False,
                "recorded": False,
                "reason": "Audit is disabled.",
            }

        if self.audit_logger is None:
            return {
                "enabled": True,
                "recorded": False,
                "reason": "Audit logger not attached.",
            }

        try:
            result = None

            if hasattr(self.audit_logger, "record"):
                result = self.audit_logger.record(
                    event_type=event_type,
                    payload=dict(payload),
                )

            elif callable(self.audit_logger):
                result = self.audit_logger(
                    event_type,
                    dict(payload),
                )

            else:
                return {
                    "enabled": True,
                    "recorded": False,
                    "reason": "Unsupported audit logger interface.",
                }

            return {
                "enabled": True,
                "recorded": True,
                "result": result,
            }

        except Exception as exc:
            return {
                "enabled": True,
                "recorded": False,
                "reason": str(exc),
            }

    # ---------------------------------------------------------------------
    # Action execution
    # ---------------------------------------------------------------------

    def _execute_action(
        self,
        *,
        plan: Mapping[str, Any],
        action: Mapping[str, Any],
        approval_granted: bool,
        required_approval_level: str,
    ) -> ActionExecutionResult:

        started = time.perf_counter()
        started_at = utc_now()

        action_id = normalize_string(action.get("action_id"))
        action_name = action_type(action.get("action_type"))

        parameters = action.get("parameters", {})

        if not isinstance(parameters, Mapping):
            parameters = {}

        severity_value = severity(plan.get("severity", "LOW"))

        context = ActionContext(
            response_id=normalize_string(plan.get("response_id")),
            request_id=normalize_string(plan.get("request_id")),
            action_id=action_id,
            threat_type=normalize_string(
                plan.get("threat_type"),
                "UNKNOWN",
            ),
            severity=severity_value,
            risk_score=clamp(
                float(plan.get("risk_score", 0.0))
            ),
            confidence=clamp(
                float(plan.get("confidence", 0.0))
            ),
            parameters=dict(parameters),
            approval_level=required_approval_level,
            approval_granted=approval_granted,
            execution_mode=self.config.execution_mode.value,
            metadata={
                "engine": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
            },
        )

        # Add action type to parameters for adapter observability.
        context.parameters.setdefault(
            "action_type",
            action_name,
        )

        try:
            # ----------------------------------------------------------
            # Safety gate.
            # ----------------------------------------------------------

            self._action_policy_allowed(
                action_name,
                context.parameters,
            )

            # ----------------------------------------------------------
            # Authorization gate.
            # ----------------------------------------------------------

            if self._is_destructive_action(action_name):

                if not approval_granted:
                    raise AuthorizationError(
                        "Explicit authorization is required for this action."
                    )

                if self.config.execution_mode != ExecutionMode.AUTOMATIC:
                    raise AuthorizationError(
                        "Destructive execution requires AUTOMATIC mode."
                    )

                if not self.config.automatic_execution_enabled:
                    raise AuthorizationError(
                        "Automatic execution is disabled."
                    )

            # ----------------------------------------------------------
            # DRY RUN.
            # ----------------------------------------------------------

            if self.config.execution_mode == ExecutionMode.DRY_RUN:
                adapter = self._adapters[action_name]

                result = adapter.execute(context)

                if not result.success:
                    raise AdapterError(
                        result.message or "Adapter execution failed."
                    )

                completed_at = utc_now()
                elapsed = (
                    time.perf_counter() - started
                ) * 1000.0

                status = (
                    ActionStatus.SIMULATED.value
                    if result.simulated
                    else ActionStatus.EXECUTED.value
                )

                return ActionExecutionResult(
                    action_id=action_id,
                    action_type=action_name,
                    status=status,
                    simulated=result.simulated,
                    started_at=started_at,
                    completed_at=completed_at,
                    processing_time_ms=round(elapsed, 3),
                    result={
                        "success": result.success,
                        "executed": result.executed,
                        "simulated": result.simulated,
                        "execution_mode":
                            self.config.execution_mode.value,
                        "reason": result.message,
                        "action_type": result.action_type,
                        **result.data,
                    },
                )

            # ----------------------------------------------------------
            # MANUAL APPROVAL mode.
            # ----------------------------------------------------------

            if self.config.execution_mode == ExecutionMode.MANUAL_APPROVAL:
                if not approval_granted:
                    raise AuthorizationError(
                        "Manual approval is required before execution."
                    )

                # Even with approval, destructive actions remain blocked
                # unless AUTOMATIC mode is explicitly enabled.
                if self._is_destructive_action(action_name):
                    raise SafetyPolicyError(
                        "Destructive execution is unavailable outside "
                        "AUTOMATIC mode."
                    )

                adapter = self._adapters[action_name]
                result = adapter.execute(context)

                if not result.success:
                    raise AdapterError(
                        result.message or "Adapter execution failed."
                    )

                elapsed = (
                    time.perf_counter() - started
                ) * 1000.0

                return ActionExecutionResult(
                    action_id=action_id,
                    action_type=action_name,
                    status=(
                        ActionStatus.SIMULATED.value
                        if result.simulated
                        else ActionStatus.EXECUTED.value
                    ),
                    simulated=result.simulated,
                    started_at=started_at,
                    completed_at=utc_now(),
                    processing_time_ms=round(elapsed, 3),
                    result={
                        "success": result.success,
                        "executed": result.executed,
                        "simulated": result.simulated,
                        "execution_mode":
                            self.config.execution_mode.value,
                        "reason": result.message,
                        "action_type": result.action_type,
                        **result.data,
                    },
                )

            # ----------------------------------------------------------
            # AUTOMATIC mode.
            # ----------------------------------------------------------

            if self.config.execution_mode == ExecutionMode.AUTOMATIC:

                if not self.config.automatic_execution_enabled:
                    raise SafetyPolicyError(
                        "Automatic execution is disabled."
                    )

                adapter = self._adapters[action_name]
                result = adapter.execute(context)

                if not result.success:
                    raise AdapterError(
                        result.message or "Adapter execution failed."
                    )

                elapsed = (
                    time.perf_counter() - started
                ) * 1000.0

                return ActionExecutionResult(
                    action_id=action_id,
                    action_type=action_name,
                    status=(
                        ActionStatus.SIMULATED.value
                        if result.simulated
                        else ActionStatus.EXECUTED.value
                    ),
                    simulated=result.simulated,
                    started_at=started_at,
                    completed_at=utc_now(),
                    processing_time_ms=round(elapsed, 3),
                    result={
                        "success": result.success,
                        "executed": result.executed,
                        "simulated": result.simulated,
                        "execution_mode":
                            self.config.execution_mode.value,
                        "reason": result.message,
                        "action_type": result.action_type,
                        **result.data,
                    },
                )

            raise SafetyPolicyError(
                f"Unsupported execution mode: "
                f"{self.config.execution_mode.value}"
            )

        except (SafetyPolicyError, AuthorizationError) as exc:

            elapsed = (
                time.perf_counter() - started
            ) * 1000.0

            return ActionExecutionResult(
                action_id=action_id,
                action_type=action_name,
                status=ActionStatus.REJECTED.value,
                simulated=False,
                started_at=started_at,
                completed_at=utc_now(),
                processing_time_ms=round(elapsed, 3),
                result={},
                error=str(exc),
            )

        except Exception as exc:

            elapsed = (
                time.perf_counter() - started
            ) * 1000.0

            return ActionExecutionResult(
                action_id=action_id,
                action_type=action_name,
                status=ActionStatus.FAILED.value,
                simulated=False,
                started_at=started_at,
                completed_at=utc_now(),
                processing_time_ms=round(elapsed, 3),
                result={},
                error=str(exc),
            )

    # ---------------------------------------------------------------------
    # Public execution API
    # ---------------------------------------------------------------------

    def execute(
        self,
        plan: Mapping[str, Any],
        *,
        approval: Optional[Mapping[str, Any]] = None,
        source: str = "unknown",
    ) -> Dict[str, Any]:

        started = time.perf_counter()

        response_id = normalize_string(
            plan.get("response_id")
            if isinstance(plan, Mapping)
            else None,
            "unknown",
        )

        request_id = normalize_string(
            plan.get("request_id")
            if isinstance(plan, Mapping)
            else None,
            "unknown",
        )

        execution_id = generate_id("EX")

        with self._lock:
            self._statistics["total_requests"] += 1

        try:
            self._validate_plan(plan)

            # ----------------------------------------------------------
            # Idempotency.
            # ----------------------------------------------------------

            idempotency_key = canonical_hash(
                {
                    "response_id": response_id,
                    "request_id": request_id,
                    "plan": plan,
                    "approval": approval,
                    "mode": self.config.execution_mode.value,
                }
            )

            if (
                self.config.idempotency_enabled
                and idempotency_key in self._idempotency_cache
            ):

                cached = dict(
                    self._idempotency_cache[idempotency_key]
                )

                cached["idempotent_replay"] = True
                cached.setdefault("metadata", {})
                cached["metadata"][
                    "idempotency_replay"
                ] = True

                return cached

            actions = plan.get("actions", [])

            required_approval = self._approval_required(plan)
            required_approval_level = (
                self._required_approval_level(plan)
            )

            if required_approval:
                with self._lock:
                    self._statistics["approval_required"] += 1

            approval_granted = self._authorization_granted(
                plan,
                approval,
            )

            action_results: List[ActionExecutionResult] = []

            for action in actions:
                result = self._execute_action(
                    plan=plan,
                    action=action,
                    approval_granted=approval_granted,
                    required_approval_level=required_approval_level,
                )

                action_results.append(result)

                with self._lock:
                    action_name = result.action_type

                    self._action_status_counts[
                        result.status
                    ] += 1

                    self._action_type_counts[
                        action_name
                    ] = (
                        self._action_type_counts.get(
                            action_name,
                            0,
                        )
                        + 1
                    )

                    if result.status == ActionStatus.EXECUTED.value:
                        self._statistics[
                            "actions_executed"
                        ] += 1

                    elif result.status == ActionStatus.SIMULATED.value:
                        self._statistics[
                            "actions_simulated"
                        ] += 1

                    elif result.status == ActionStatus.REJECTED.value:
                        self._statistics[
                            "actions_rejected"
                        ] += 1

                    elif result.status == ActionStatus.FAILED.value:
                        self._statistics[
                            "actions_failed"
                        ] += 1

            # ----------------------------------------------------------
            # Determine request-level status.
            # ----------------------------------------------------------

            statuses = {
                result.status
                for result in action_results
            }

            if not action_results:
                request_status = ExecutionStatus.SUCCESS.value

            elif statuses == {
                ActionStatus.REJECTED.value
            }:
                request_status = ExecutionStatus.PARTIAL.value

            elif statuses == {
                ActionStatus.FAILED.value
            }:
                request_status = ExecutionStatus.FAILED.value

            elif ActionStatus.FAILED.value in statuses:
                request_status = ExecutionStatus.PARTIAL.value

            elif ActionStatus.REJECTED.value in statuses:
                request_status = ExecutionStatus.PARTIAL.value

            else:
                request_status = ExecutionStatus.SUCCESS.value

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0

            result_payload = {
                "execution_id": execution_id,
                "response_id": response_id,
                "request_id": request_id,
                "timestamp": utc_now(),
                "status": request_status,
                "execution_mode":
                    self.config.execution_mode.value,
                "approval_required": required_approval,
                "approval_level": required_approval_level,
                "approval_granted": approval_granted,
                "actions_requested": len(actions),
                "actions_executed": sum(
                    r.status == ActionStatus.EXECUTED.value
                    for r in action_results
                ),
                "actions_simulated": sum(
                    r.status == ActionStatus.SIMULATED.value
                    for r in action_results
                ),
                "actions_rejected": sum(
                    r.status == ActionStatus.REJECTED.value
                    for r in action_results
                ),
                "actions_failed": sum(
                    r.status == ActionStatus.FAILED.value
                    for r in action_results
                ),
                "processing_time_ms": round(elapsed_ms, 3),
                "idempotent_replay": False,
                "actions": [
                    {
                        "action_id": r.action_id,
                        "action_type": r.action_type,
                        "status": r.status,
                        "simulated": r.simulated,
                        "started_at": r.started_at,
                        "completed_at": r.completed_at,
                        "processing_time_ms":
                            r.processing_time_ms,
                        "result": r.result,
                        "error": r.error,
                    }
                    for r in action_results
                ],
                "verification": self._verify(
                    plan,
                    action_results,
                ),
                "audit": {},
                "metadata": {
                    "source": source,
                    "automatic_execution_enabled":
                        self.config.automatic_execution_enabled,
                    "destructive_actions_enabled":
                        self.config.allow_destructive_actions,
                    "shell_execution_enabled":
                        self.config.allow_shell_execution,
                    "network_isolation_enabled":
                        self.config.allow_network_isolation,
                    "process_termination_enabled":
                        self.config.allow_process_termination,
                    "account_modification_enabled":
                        self.config.allow_account_modification,
                    "processing_target_ms":
                        self.config.processing_target_ms,
                    "within_processing_target":
                        elapsed_ms
                        <= self.config.processing_target_ms,
                },
                "engine_version": ENGINE_VERSION,
                "error": None,
            }

            # ----------------------------------------------------------
            # Audit.
            # ----------------------------------------------------------

            result_payload["audit"] = self._audit(
                "RESPONSE_EXECUTION",
                result_payload,
            )

            # ----------------------------------------------------------
            # Statistics.
            # ----------------------------------------------------------

            with self._lock:

                self._statistics[
                    "actions_requested"
                ] += len(actions)

                if request_status == ExecutionStatus.SUCCESS.value:
                    self._statistics[
                        "successful_requests"
                    ] += 1

                elif request_status == ExecutionStatus.PARTIAL.value:
                    self._statistics[
                        "partial_requests"
                    ] += 1

                elif request_status == ExecutionStatus.FAILED.value:
                    self._statistics[
                        "failed_requests"
                    ] += 1

                self._status_counts[
                    request_status
                ] += 1

                previous_total = (
                    self._statistics["total_requests"]
                )

                previous_average = (
                    self._statistics[
                        "average_processing_ms"
                    ]
                )

                # Exclude the current request from denominator
                # because total_requests already includes it.
                if previous_total <= 1:
                    new_average = elapsed_ms
                else:
                    new_average = (
                        (
                            previous_average
                            * (previous_total - 1)
                        )
                        + elapsed_ms
                    ) / previous_total

                self._statistics[
                    "average_processing_ms"
                ] = round(new_average, 3)

                self._statistics[
                    "max_processing_ms"
                ] = round(
                    max(
                        self._statistics[
                            "max_processing_ms"
                        ],
                        elapsed_ms,
                    ),
                    3,
                )

            # ----------------------------------------------------------
            # Store idempotent result.
            # ----------------------------------------------------------

            if self.config.idempotency_enabled:
                with self._lock:
                    self._idempotency_cache[
                        idempotency_key
                    ] = dict(result_payload)

            return result_payload

        except ValidationError as exc:

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0

            result = {
                "execution_id": execution_id,
                "response_id": response_id,
                "request_id": request_id,
                "timestamp": utc_now(),
                "status": ExecutionStatus.REJECTED.value,
                "execution_mode":
                    self.config.execution_mode.value,
                "approval_required": False,
                "approval_level":
                    ApprovalLevel.NONE.value,
                "actions_requested": 0,
                "actions_executed": 0,
                "actions_simulated": 0,
                "actions_rejected": 0,
                "actions_failed": 0,
                "processing_time_ms":
                    round(elapsed_ms, 3),
                "idempotent_replay": False,
                "actions": [],
                "verification": {},
                "audit": {},
                "metadata": {
                    "source": source,
                    "reason": str(exc),
                },
                "engine_version": ENGINE_VERSION,
                "error": str(exc),
            }

            with self._lock:
                self._statistics[
                    "rejected_requests"
                ] += 1

                self._status_counts[
                    ExecutionStatus.REJECTED.value
                ] += 1

            return result

        except Exception as exc:

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0

            result = {
                "execution_id": execution_id,
                "response_id": response_id,
                "request_id": request_id,
                "timestamp": utc_now(),
                "status": ExecutionStatus.FAILED.value,
                "execution_mode":
                    self.config.execution_mode.value,
                "approval_required": False,
                "approval_level":
                    ApprovalLevel.NONE.value,
                "actions_requested": 0,
                "actions_executed": 0,
                "actions_simulated": 0,
                "actions_rejected": 0,
                "actions_failed": 0,
                "processing_time_ms":
                    round(elapsed_ms, 3),
                "idempotent_replay": False,
                "actions": [],
                "verification": {},
                "audit": {},
                "metadata": {
                    "source": source,
                    "reason": str(exc),
                },
                "engine_version": ENGINE_VERSION,
                "error": str(exc),
            }

            with self._lock:
                self._statistics[
                    "failed_requests"
                ] += 1

                self._status_counts[
                    ExecutionStatus.FAILED.value
                ] += 1

            return result

    # ---------------------------------------------------------------------
    # Batch execution
    # ---------------------------------------------------------------------

    def execute_batch(
        self,
        plans: Iterable[Mapping[str, Any]],
        *,
        approval: Optional[Mapping[str, Any]] = None,
        source: str = "batch",
    ) -> Dict[str, Any]:

        started = time.perf_counter()

        results = []

        for plan in plans:
            results.append(
                self.execute(
                    plan,
                    approval=approval,
                    source=source,
                )
            )

        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000.0

        planned = sum(
            result["status"]
            in {
                ExecutionStatus.SUCCESS.value,
                ExecutionStatus.PARTIAL.value,
            }
            for result in results
        )

        rejected = sum(
            result["status"]
            == ExecutionStatus.REJECTED.value
            for result in results
        )

        failed = sum(
            result["status"]
            == ExecutionStatus.FAILED.value
            for result in results
        )

        approval_required = sum(
            bool(result.get("approval_required"))
            for result in results
        )

        return {
            "success": failed == 0 and rejected == 0,
            "processed": len(results),
            "planned": planned,
            "rejected": rejected,
            "failed": failed,
            "approval_required": approval_required,
            "processing_time_ms": round(elapsed_ms, 3),
            "results": results,
        }

    # ---------------------------------------------------------------------
    # Verification
    # ---------------------------------------------------------------------

    def _verify(
        self,
        plan: Mapping[str, Any],
        action_results: List[ActionExecutionResult],
    ) -> Dict[str, Any]:

        if self.verification_hook is None:
            return {
                "available": False,
                "verified": False,
                "reason": "Verification engine is not attached.",
            }

        try:
            payload = {
                "plan": dict(plan),
                "actions": [
                    {
                        "action_id": result.action_id,
                        "action_type": result.action_type,
                        "status": result.status,
                        "simulated": result.simulated,
                    }
                    for result in action_results
                ],
            }

            result = self.verification_hook(payload)

            return {
                "available": True,
                "verified": bool(result.get("verified", False)),
                "result": dict(result),
            }

        except Exception as exc:
            return {
                "available": True,
                "verified": False,
                "reason": str(exc),
            }

    # ---------------------------------------------------------------------
    # Self-test
    # ---------------------------------------------------------------------

    def self_test(self) -> Dict[str, Any]:
        """
        Execute a complete internal security/integration test.

        Important:
        A rejected destructive action is considered a SUCCESSFUL safety
        outcome when destructive execution is disabled.

        The self-test therefore verifies security guarantees rather than
        merely checking whether actions executed.
        """

        critical_plan = {
            "response_id": "ER-SELFTEST-CRITICAL",
            "request_id": "EG-SELFTEST-CRITICAL",
            "timestamp": utc_now(),
            "status": "PLANNED",
            "execution_mode": "MANUAL_APPROVAL",
            "threat_detected": True,
            "threat_type": "CREDENTIAL_STUFFING",
            "severity": "CRITICAL",
            "risk_score": 98.07,
            "confidence": 91.61,
            "recommended_action":
                "ISOLATE_AND_ESCALATE",
            "approval_required": True,
            "approval_level":
                ApprovalLevel.SECURITY_ADMIN.value,
            "actions": [
                {
                    "action_id": "EA-SELFTEST-ALERT",
                    "action_type":
                        ActionType.CREATE_ALERT.value,
                    "priority": 40,
                    "description":
                        "Create a critical security alert.",
                    "requires_approval": False,
                    "approval_level":
                        ApprovalLevel.NONE.value,
                    "parameters": {
                        "threat_type":
                            "CREDENTIAL_STUFFING",
                        "severity": "CRITICAL",
                    },
                },
                {
                    "action_id": "EA-SELFTEST-ISOLATE",
                    "action_type":
                        ActionType.ISOLATE.value,
                    "priority": 10,
                    "description":
                        "Prepare isolation.",
                    "requires_approval": True,
                    "approval_level":
                        ApprovalLevel.SECURITY_ADMIN.value,
                    "parameters": {
                        "threat_type":
                            "CREDENTIAL_STUFFING",
                        "severity": "CRITICAL",
                    },
                },
            ],
        }

        shell_plan = {
            "response_id": "ER-SELFTEST-SHELL",
            "request_id": "EG-SELFTEST-SHELL",
            "severity": "LOW",
            "threat_type": "TEST",
            "risk_score": 5.0,
            "confidence": 99.0,
            "actions": [
                {
                    "action_id": "EA-SELFTEST-SHELL",
                    "action_type":
                        ActionType.CONTAIN.value,
                    "parameters": {
                        "command":
                            "echo EnterpriseGuard"
                    },
                }
            ],
        }

        alert_plan = {
            "response_id": "ER-SELFTEST-ALERT",
            "request_id": "EG-SELFTEST-ALERT",
            "severity": "LOW",
            "threat_type": "TEST_ALERT",
            "risk_score": 5.0,
            "confidence": 99.0,
            "actions": [
                {
                    "action_id":
                        "EA-SELFTEST-ALERT-2",
                    "action_type":
                        ActionType.CREATE_ALERT.value,
                    "parameters": {
                        "message":
                            "EnterpriseGuard self-test"
                    },
                }
            ],
        }

        invalid_plan: Dict[str, Any] = {}

        critical_result = self.execute(
            critical_plan,
            source="self-test",
        )

        shell_result = self.execute(
            shell_plan,
            source="self-test-shell",
        )

        alert_result = self.execute(
            alert_plan,
            source="self-test-alert",
        )

        replay_result = self.execute(
            alert_plan,
            source="self-test-alert-replay",
        )

        invalid_result = self.execute(
            invalid_plan,
            source="self-test-invalid",
        )

        # --------------------------------------------------------------
        # Extract action states.
        # --------------------------------------------------------------

        critical_actions = critical_result.get(
            "actions",
            [],
        )

        isolation_actions = [
            action
            for action in critical_actions
            if action.get("action_type")
            == ActionType.ISOLATE.value
        ]

        isolation_not_executed = bool(
            isolation_actions
            and all(
                action.get("status")
                != ActionStatus.EXECUTED.value
                for action in isolation_actions
            )
        )

        critical_requires_approval = bool(
            critical_result.get(
                "approval_required",
                False,
            )
            and critical_result.get(
                "approval_level"
            )
            == ApprovalLevel.SECURITY_ADMIN.value
        )

        shell_actions = shell_result.get(
            "actions",
            [],
        )

        shell_rejected = bool(
            shell_actions
            and any(
                action.get("status")
                == ActionStatus.REJECTED.value
                for action in shell_actions
            )
        )

        shell_protection_active = bool(
            shell_rejected
            and any(
                "Shell or command execution parameters"
                in normalize_string(
                    action.get("error")
                )
                for action in shell_actions
            )
        )

        no_shell_execution = not any(
            action.get("status")
            == ActionStatus.EXECUTED.value
            for action in shell_actions
        )

        no_destructive_execution = not any(
            action.get("action_type")
            in {
                ActionType.CONTAIN.value,
                ActionType.ISOLATE.value,
                ActionType.TERMINATE_PROCESS.value,
                ActionType.MODIFY_ACCOUNT.value,
                ActionType.BLOCK_SOURCE.value,
            }
            and action.get("status")
            == ActionStatus.EXECUTED.value
            for action in critical_actions
        )

        alert_processed = (
            alert_result.get("status")
            == ExecutionStatus.SUCCESS.value
        )

        idempotency_replay_detected = bool(
            replay_result.get(
                "idempotent_replay",
                False,
            )
        )

        invalid_rejected = (
            invalid_result.get("status")
            == ExecutionStatus.REJECTED.value
        )

        critical_request_processed = (
            critical_result.get("status")
            in {
                ExecutionStatus.SUCCESS.value,
                ExecutionStatus.PARTIAL.value,
            }
        )

        checks = {
            "executor_active":
                self.status()["status"] == "active",

            "health_check_available":
                self.health_check()["healthy"] is True,

            "critical_request_processed":
                critical_request_processed,

            "critical_requires_approval":
                critical_requires_approval,

            "isolation_not_executed":
                isolation_not_executed,

            "no_shell_execution":
                no_shell_execution,

            "shell_protection_active":
                shell_protection_active,

            "no_destructive_execution":
                no_destructive_execution,

            "safe_alert_processed":
                alert_processed,

            "idempotency_replay_detected":
                idempotency_replay_detected,

            "invalid_input_rejected":
                invalid_rejected,

            "statistics_updated":
                self.status()["statistics"][
                    "total_requests"
                ] >= 5,
        }

        passed = all(checks.values())

        result = {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "healthy": passed,
            "checks": checks,
            "critical_result": critical_result,
            "shell_result": shell_result,
            "alert_result": alert_result,
            "replay_result": replay_result,
            "invalid_result": invalid_result,
            "status": self.status(),
        }

        if not passed:
            failed = [
                key
                for key, value in checks.items()
                if not value
            ]

            raise RuntimeError(
                "EnterpriseGuard Response Executor "
                "self-test failed. "
                f"Failed checks: {', '.join(failed)}"
            )

        return result


# ============================================================================
# Integration self-test
# ============================================================================


def _self_test() -> None:
    print()
    print("=" * 78)
    print("EnterpriseGuard Response Executor - Integration Self Test")
    print("=" * 78)
    print()

    executor = ResponseExecutor()

    print("[1] Response executor status")
    print(
        json.dumps(
            executor.status(),
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    print("[2] Health check")
    print(
        json.dumps(
            executor.health_check(),
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    # --------------------------------------------------------------
    # Critical response.
    # --------------------------------------------------------------

    critical_plan = {
        "response_id": "ER-SELFTEST-CRITICAL",
        "request_id": "EG-SELFTEST-CRITICAL",
        "severity": "CRITICAL",
        "threat_type": "CREDENTIAL_STUFFING",
        "risk_score": 98.07,
        "confidence": 91.61,
        "recommended_action":
            "ISOLATE_AND_ESCALATE",
        "approval_required": True,
        "approval_level":
            ApprovalLevel.SECURITY_ADMIN.value,
        "actions": [
            {
                "action_id": "EA-SELFTEST-ALERT",
                "action_type":
                    ActionType.CREATE_ALERT.value,
                "parameters": {
                    "threat_type":
                        "CREDENTIAL_STUFFING",
                    "severity":
                        "CRITICAL",
                },
            },
            {
                "action_id": "EA-SELFTEST-ISOLATE",
                "action_type":
                    ActionType.ISOLATE.value,
                "parameters": {
                    "threat_type":
                        "CREDENTIAL_STUFFING",
                    "severity":
                        "CRITICAL",
                },
            },
        ],
    }

    print("[3] Critical response execution safety")

    critical_result = executor.execute(
        critical_plan,
        source="self-test",
    )

    print(
        json.dumps(
            critical_result,
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    # --------------------------------------------------------------
    # Shell protection.
    # --------------------------------------------------------------

    shell_plan = {
        "response_id": "ER-SELFTEST-SHELL",
        "request_id": "EG-SELFTEST-SHELL",
        "severity": "LOW",
        "threat_type": "TEST",
        "risk_score": 5.0,
        "confidence": 99.0,
        "actions": [
            {
                "action_id": "EA-SELFTEST-SHELL",
                "action_type":
                    ActionType.CONTAIN.value,
                "parameters": {
                    "command":
                        "echo EnterpriseGuard"
                },
            }
        ],
    }

    print("[4] Arbitrary command execution protection")

    shell_result = executor.execute(
        shell_plan,
        source="self-test-shell",
    )

    print(
        json.dumps(
            shell_result,
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    # --------------------------------------------------------------
    # Safe alert.
    # --------------------------------------------------------------

    alert_plan = {
        "response_id": "ER-SELFTEST-ALERT",
        "request_id": "EG-SELFTEST-ALERT",
        "severity": "LOW",
        "threat_type": "TEST_ALERT",
        "risk_score": 5.0,
        "confidence": 99.0,
        "actions": [
            {
                "action_id":
                    "EA-SELFTEST-ALERT-2",
                "action_type":
                    ActionType.CREATE_ALERT.value,
                "parameters": {
                    "message":
                        "EnterpriseGuard self-test"
                },
            }
        ],
    }

    print("[5] Safe alert execution")

    alert_result = executor.execute(
        alert_plan,
        source="self-test-alert",
    )

    print(
        json.dumps(
            alert_result,
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    # --------------------------------------------------------------
    # Idempotency.
    # --------------------------------------------------------------

    print("[6] Idempotency protection")

    replay_result = executor.execute(
        alert_plan,
        source="self-test-alert-replay",
    )

    print(
        json.dumps(
            replay_result,
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    # --------------------------------------------------------------
    # Invalid input.
    # --------------------------------------------------------------

    print("[7] Invalid input safety")

    invalid_result = executor.execute(
        {},
        source="self-test-invalid",
    )

    print(
        json.dumps(
            invalid_result,
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    # --------------------------------------------------------------
    # Final status.
    # --------------------------------------------------------------

    print("[8] Final response executor status")

    print(
        json.dumps(
            executor.status(),
            indent=4,
            ensure_ascii=False,
        )
    )
    print()

    # --------------------------------------------------------------
    # Verification.
    # --------------------------------------------------------------

    critical_actions = critical_result.get(
        "actions",
        [],
    )

    isolation_actions = [
        action
        for action in critical_actions
        if action.get("action_type")
        == ActionType.ISOLATE.value
    ]

    isolation_not_executed = bool(
        isolation_actions
        and all(
            action.get("status")
            != ActionStatus.EXECUTED.value
            for action in isolation_actions
        )
    )

    critical_requires_approval = bool(
        critical_result.get("approval_required")
        is True
        and critical_result.get(
            "approval_level"
        )
        == ApprovalLevel.SECURITY_ADMIN.value
    )

    shell_actions = shell_result.get(
        "actions",
        [],
    )

    shell_protection_active = bool(
        shell_actions
        and any(
            action.get("status")
            == ActionStatus.REJECTED.value
            and
            "Shell or command execution parameters"
            in normalize_string(
                action.get("error")
            )
            for action in shell_actions
        )
    )

    no_shell_execution = not any(
        action.get("status")
        == ActionStatus.EXECUTED.value
        for action in shell_actions
    )

    no_destructive_execution = not any(
        action.get("action_type")
        in {
            ActionType.CONTAIN.value,
            ActionType.ISOLATE.value,
            ActionType.TERMINATE_PROCESS.value,
            ActionType.MODIFY_ACCOUNT.value,
            ActionType.BLOCK_SOURCE.value,
        }
        and action.get("status")
        == ActionStatus.EXECUTED.value
        for action in critical_actions
    )

    checks = {
        "executor_active":
            executor.status()["status"] == "active",

        "health_check_available":
            executor.health_check()["healthy"] is True,

        "critical_request_processed":
            critical_result["status"]
            in {
                ExecutionStatus.SUCCESS.value,
                ExecutionStatus.PARTIAL.value,
            },

        "critical_requires_approval":
            critical_requires_approval,

        "isolation_not_executed":
            isolation_not_executed,

        "no_shell_execution":
            no_shell_execution,

        "shell_protection_active":
            shell_protection_active,

        "no_destructive_execution":
            no_destructive_execution,

        "safe_alert_processed":
            alert_result["status"]
            == ExecutionStatus.SUCCESS.value,

        "idempotency_replay_detected":
            replay_result.get(
                "idempotent_replay",
                False,
            )
            is True,

        "invalid_input_rejected":
            invalid_result["status"]
            == ExecutionStatus.REJECTED.value,

        "statistics_updated":
            executor.status()["statistics"][
                "total_requests"
            ] >= 5,
    }

    print("[9] Final verification")

    print(
        json.dumps(
            checks,
            indent=4,
            ensure_ascii=False,
        )
    )

    print()

    if not all(checks.values()):

        failed_checks = [
            name
            for name, value in checks.items()
            if not value
        ]

        print("=" * 78)
        print("Response Executor self test FAILED.")
        print("=" * 78)

        raise RuntimeError(
            "EnterpriseGuard Response Executor "
            "self-test failed. "
            f"Failed checks: {', '.join(failed_checks)}"
        )

    print("=" * 78)
    print("Response Executor self test completed successfully.")
    print("=" * 78)
    print()


# ============================================================================
# Module entry point
# ============================================================================


if __name__ == "__main__":
    _self_test()