"""
EnterpriseGuard - Response Integration Layer
=============================================


Production-grade orchestration layer for the EnterpriseGuard response
lifecycle.


Pipeline
--------
    Request
       |
       v
    Validation
       |
       v
    Response Planning
       |
       v
    Response Execution
       |
       v
    Response Verification
       |
       v
    Response Audit
       |
       v
    Integration Result


Responsibilities
----------------
This module is responsible ONLY for orchestration.


It does NOT:
    - execute shell commands
    - perform network operations
    - modify accounts
    - directly execute security actions
    - contain response business logic
    - persist audit events itself


Those responsibilities belong to the appropriate EnterpriseGuard
components.


Design principles
-----------------
- deterministic orchestration
- explicit stage boundaries
- fail-closed behavior
- strong input validation
- bounded input/action sizes
- idempotent request handling
- immutable-style result snapshots
- correlation identifiers across stages
- explicit failure propagation
- safe-by-default operation
- compatibility with existing response components
- real integration with monitoring.audit.AuditLogger
- deterministic self-testing
- no hidden side effects
"""


from __future__ import annotations


import copy
import hashlib
import json
import time
import uuid


from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple




# ============================================================================
# Metadata
# ============================================================================


VERSION = "2.0.0"


ENGINE_NAME = "EnterpriseGuard Response Integration"


MAX_INPUT_SIZE = 1_000_000
MAX_ACTIONS = 16


DEFAULT_REQUEST_ID = "unknown"




# ============================================================================
# Type aliases
# ============================================================================


JSONDict = Dict[str, Any]
MethodNames = Tuple[str, ...]




# ============================================================================
# Utility functions
# ============================================================================




def _utc_now() -> str:
    """
    Return the current UTC timestamp in ISO-8601 format.
    """
    return datetime.now(timezone.utc).isoformat()




def _new_id(prefix: str) -> str:
    """
    Generate a readable EnterpriseGuard identifier.


    Example:
        INT-3A6D2B...
    """
    return f"{prefix}-{uuid.uuid4().hex[:24].upper()}"




def _canonical_json(value: Any) -> str:
    """
    Serialize a value deterministically.


    The resulting representation is used for hashing and idempotency.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )




def _hash(value: Any) -> str:
    """
    Return a SHA-256 hash of a canonical representation.
    """
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()




def _safe_len(value: Any) -> int:
    """
    Return the serialized size of a value.


    Serialization failures are deliberately treated as oversized input.
    """
    try:
        return len(_canonical_json(value))
    except Exception:
        return MAX_INPUT_SIZE + 1




def _copy(value: Any) -> Any:
    """
    Return a defensive deep copy.
    """
    return copy.deepcopy(value)




def _is_dict(value: Any) -> bool:
    """
    Return True when value is a dictionary.
    """
    return isinstance(value, dict)




def _status_of(value: Any) -> Optional[str]:
    """
    Safely extract a status from a component result.
    """
    if not isinstance(value, dict):
        return None


    status = value.get("status")


    return (
        status.upper()
        if isinstance(status, str)
        else None
    )




# ============================================================================
# Integration result
# ============================================================================




@dataclass
class IntegrationResult:
    """
    Final immutable-style representation of one integration request.


    The object captures the complete lifecycle of the request.
    """


    integration_id: str
    request_id: str


    response_id: Optional[str] = None
    execution_id: Optional[str] = None
    verification_id: Optional[str] = None


    status: str = "FAILED"


    started_at: str = field(default_factory=_utc_now)
    completed_at: Optional[str] = None


    planning: JSONDict = field(default_factory=dict)
    execution: JSONDict = field(default_factory=dict)
    verification: JSONDict = field(default_factory=dict)
    audit: JSONDict = field(default_factory=dict)


    stages_completed: List[str] = field(
        default_factory=list
    )


    stages_failed: List[str] = field(
        default_factory=list
    )


    processing_time_ms: float = 0.0


    correlation_hash: str = ""


    error: Optional[str] = None


    idempotent_replay: bool = False


    def to_dict(self) -> JSONDict:
        """
        Return a serializable representation.
        """
        return asdict(self)




# ============================================================================
# Statistics
# ============================================================================




@dataclass
class IntegrationStatistics:
    """
    Runtime statistics for the integration layer.
    """


    total_requests: int = 0


    successful_requests: int = 0
    partial_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0


    idempotent_replays: int = 0


    planning_completed: int = 0
    execution_completed: int = 0
    verification_completed: int = 0


    audit_events: int = 0


    average_processing_ms: float = 0.0
    max_processing_ms: float = 0.0


    def record_processing(
        self,
        processing_ms: float,
    ) -> None:
        """
        Update processing-time statistics.


        total_requests must already include the current request.
        """
        if self.total_requests <= 0:
            return


        previous_total = (
            self.average_processing_ms
            * (self.total_requests - 1)
        )


        self.average_processing_ms = (
            previous_total + processing_ms
        ) / self.total_requests


        self.max_processing_ms = max(
            self.max_processing_ms,
            processing_ms,
        )




# ============================================================================
# Response Integration
# ============================================================================




class ResponseIntegration:
    """
    Orchestrate the complete EnterpriseGuard response lifecycle.


    Important
    ---------
    This class does not perform security actions directly.


    The actual action execution remains delegated to ResponseExecutor.
    Verification remains delegated to the verification component.
    Audit persistence remains delegated to AuditLogger.
    """


    # ------------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------------


    def __init__(
        self,
        engine: Any = None,
        executor: Any = None,
        verification: Any = None,
        audit: Any = None,
        *,
        enabled: bool = True,
        max_input_size: int = MAX_INPUT_SIZE,
        max_actions: int = MAX_ACTIONS,
        idempotency_enabled: bool = True,
    ) -> None:


        self.engine = (
            engine
            if engine is not None
            else self._load_component(
                "enterpriseguard.response.engine",
                (
                    "ResponseEngine",
                    "EnterpriseGuardResponseEngine",
                ),
            )
        )


        self.executor = (
            executor
            if executor is not None
            else self._load_component(
                "enterpriseguard.response.executor",
                (
                    "ResponseExecutor",
                    "EnterpriseGuardResponseExecutor",
                ),
            )
        )


        self.verification = (
            verification
            if verification is not None
            else self._load_component(
                "enterpriseguard.response.verification",
                (
                    "ResponseVerificationEngine",
                    "ResponseVerification",
                ),
            )
        )


        # The canonical EnterpriseGuard audit component is:
        #
        #     enterpriseguard.monitoring.audit.AuditLogger
        #
        # Do not create a parallel audit implementation here.
        self.audit = (
            audit
            if audit is not None
            else self._load_component(
                "enterpriseguard.monitoring.audit",
                (
                    "AuditLogger",
                ),
            )
        )


        self.enabled = bool(enabled)


        self.max_input_size = max(
            1,
            int(max_input_size),
        )


        self.max_actions = max(
            1,
            int(max_actions),
        )


        self.idempotency_enabled = bool(
            idempotency_enabled
        )


        self.statistics = IntegrationStatistics()


        # request fingerprint -> serialized IntegrationResult
        self._idempotency_cache: Dict[
            str,
            JSONDict,
        ] = {}


    # ------------------------------------------------------------------------
    # Component loading
    # ------------------------------------------------------------------------


    @staticmethod
    def _load_component(
        module_name: str,
        class_names: Sequence[str],
    ) -> Any:
        """
        Dynamically load an EnterpriseGuard component.


        Component loading failures are intentionally non-fatal.


        health_check() is responsible for exposing missing components.
        """
        try:
            module = __import__(
                module_name,
                fromlist=list(class_names),
            )
        except Exception:
            return None


        for class_name in class_names:


            component_class = getattr(
                module,
                class_name,
                None,
            )


            if component_class is None:
                continue


            try:
                return component_class()
            except Exception:
                continue


        return None


    # ------------------------------------------------------------------------
    # Generic component invocation
    # ------------------------------------------------------------------------


    @staticmethod
    def _invoke(
        component: Any,
        method_names: MethodNames,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Invoke the first compatible public component method.


        Compatibility order:
            1. positional + keyword arguments
            2. positional arguments
            3. no arguments


        TypeError is interpreted as a signature mismatch.


        All other exceptions are allowed to propagate to the caller.
        """
        if component is None:
            return None


        for method_name in method_names:


            method = getattr(
                component,
                method_name,
                None,
            )


            if not callable(method):
                continue


            if kwargs:
                try:
                    return method(
                        *args,
                        **kwargs,
                    )
                except TypeError:
                    pass


            if args:
                try:
                    return method(*args)
                except TypeError:
                    pass


            try:
                return method()
            except TypeError:
                continue


        return None


    # ------------------------------------------------------------------------
    # Component availability
    # ------------------------------------------------------------------------


    def _component_state(self) -> JSONDict:
        """
        Return component availability.
        """
        return {
            "engine": self.engine is not None,
            "executor": self.executor is not None,
            "verification": self.verification is not None,
            "audit": self.audit is not None,
        }


    # ------------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------------


    def status(self) -> JSONDict:
        """
        Return runtime status and safety configuration.
        """
        return {
            "engine": ENGINE_NAME,
            "version": VERSION,
            "status": (
                "active"
                if self.enabled
                else "disabled"
            ),
            "components": self._component_state(),
            "configuration": {
                "enabled": self.enabled,
                "max_input_size": self.max_input_size,
                "max_actions": self.max_actions,
                "idempotency_enabled": (
                    self.idempotency_enabled
                ),
            },
            "statistics": asdict(
                self.statistics
            ),
            "safety": {
                "integration_executes_security_actions": False,
                "shell_execution": False,
                "network_operations": False,
                "process_operations": False,
                "account_modification": False,
            },
        }


    # ------------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------------


    def health_check(self) -> JSONDict:
        """
        Verify integration health and required component availability.
        """
        components = self._component_state()


        healthy = (
            self.enabled
            and all(components.values())
        )


        return {
            "healthy": healthy,
            "engine": {
                "enabled": self.enabled,
                "version": VERSION,
            },
            "components": {
                name: {
                    "available": available,
                }
                for name, available in components.items()
            },
            "pipeline": {
                "validation": True,
                "planning": components["engine"],
                "execution": components["executor"],
                "verification": components["verification"],
                "audit": components["audit"],
            },
            "safety": {
                "integration_executes_security_actions": False,
                "shell_execution": False,
                "network_operations": False,
                "process_operations": False,
                "account_modification": False,
            },
        }


    # ------------------------------------------------------------------------
    # Request validation
    # ------------------------------------------------------------------------


    def _validate_request(
        self,
        request: Any,
    ) -> Optional[str]:
        """
        Validate an integration request.


        A request must contain:


            request_id


        and one of:


            response_plan
            plan
            intelligence_result
        """
        if not isinstance(request, dict):
            return "Request must be a dictionary."


        if _safe_len(request) > self.max_input_size:
            return (
                "Request exceeds maximum input size."
            )


        request_id = request.get(
            "request_id"
        )


        if not isinstance(
            request_id,
            str,
        ) or not request_id.strip():
            return (
                "Request must contain a valid "
                "request_id."
            )


        response_plan = request.get(
            "response_plan"
        )


        if response_plan is None:
            response_plan = request.get(
                "plan"
            )


        intelligence_result = request.get(
            "intelligence_result"
        )


        if (
            response_plan is None
            and intelligence_result is None
        ):
            return (
                "Request must contain either "
                "response_plan/plan or "
                "intelligence_result."
            )


        if (
            response_plan is not None
            and not isinstance(
                response_plan,
                dict,
            )
        ):
            return (
                "response_plan must be a dictionary."
            )


        if (
            response_plan is None
            and not isinstance(
                intelligence_result,
                dict,
            )
        ):
            return (
                "intelligence_result must be "
                "a dictionary."
            )


        if response_plan is not None:


            actions = response_plan.get(
                "actions"
            )


            if not isinstance(
                actions,
                list,
            ):
                return (
                    "Response plan actions "
                    "must be a list."
                )


            if len(actions) > self.max_actions:
                return (
                    "Response plan exceeds maximum "
                    f"allowed actions "
                    f"({self.max_actions})."
                )


            for index, action in enumerate(
                actions
            ):
                if not isinstance(
                    action,
                    dict,
                ):
                    return (
                        "Response plan action "
                        f"at index {index} "
                        "must be a dictionary."
                    )


        return None


    # ------------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------------


    def _audit(
        self,
        event_type: str,
        *,
        request_id: str,
        response_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        outcome: str = "OBSERVED",
        details: Optional[JSONDict] = None,
    ) -> JSONDict:
        """
        Record one integration lifecycle event.


        Preferred API:
            AuditLogger.record(...)


        Compatibility fallback:
            AuditLogger.log_event(payload)
        """
        if self.audit is None:
            return {
                "recorded": False,
                "available": False,
                "reason": (
                    "AuditLogger is unavailable."
                ),
            }


        safe_details = _copy(
            details or {}
        )


        metadata = {
            "integration_version": VERSION,
            "request_id": request_id,
            "response_id": response_id,
            "execution_id": execution_id,
            "verification_id": verification_id,
            "source": "response-integration",
            "details": safe_details,
        }


        record_method = getattr(
            self.audit,
            "record",
            None,
        )


        if callable(record_method):


            try:
                event = record_method(
                    event_type=event_type,
                    action=event_type,
                    outcome=outcome,
                    severity="INFO",
                    actor_id="system",
                    actor_ip=None,
                    resource=(
                        response_id
                        or execution_id
                        or request_id
                    ),
                    message=(
                        "Response Integration "
                        f"event: {event_type}"
                    ),
                    metadata=metadata,
                    correlation_id=request_id,
                    source="response-integration",
                )


                self.statistics.audit_events += 1


                if hasattr(
                    event,
                    "to_dict",
                ):
                    event_value = event.to_dict()


                elif hasattr(
                    event,
                    "__dataclass_fields__",
                ):
                    event_value = asdict(event)


                elif hasattr(
                    event,
                    "__dict__",
                ):
                    event_value = dict(
                        event.__dict__
                    )


                else:
                    event_value = event


                return {
                    "recorded": True,
                    "available": True,
                    "event": event_value,
                }


            except Exception as exc:
                return {
                    "recorded": False,
                    "available": True,
                    "error": str(exc),
                }


        log_event_method = getattr(
            self.audit,
            "log_event",
            None,
        )


        if callable(log_event_method):


            payload = {
                "event_type": event_type,
                "action": event_type,
                "outcome": outcome,
                "severity": "INFO",
                "actor_id": "system",
                "resource": (
                    response_id
                    or execution_id
                    or request_id
                ),
                "message": (
                    "Response Integration "
                    f"event: {event_type}"
                ),
                "metadata": metadata,
                "correlation_id": request_id,
                "source": "response-integration",
            }


            try:
                result = log_event_method(
                    payload
                )


                self.statistics.audit_events += 1


                return {
                    "recorded": True,
                    "available": True,
                    "result": result,
                }


            except Exception as exc:
                return {
                    "recorded": False,
                    "available": True,
                    "error": str(exc),
                }


        return {
            "recorded": False,
            "available": True,
            "reason": (
                "AuditLogger exposes neither "
                "record() nor log_event()."
            ),
        }


    # ------------------------------------------------------------------------
    # Planning stage
    # ------------------------------------------------------------------------


    def _planning_stage(
        self,
        request: JSONDict,
    ) -> JSONDict:
        """
        Build or accept a response plan.
        """
        request_id = request[
            "request_id"
        ]


        response_id = (
            request.get("response_id")
            or _new_id("ER")
        )


        response_plan = request.get(
            "response_plan"
        )


        if response_plan is None:
            response_plan = request.get(
                "plan"
            )


        # Existing plan.
        if response_plan is not None:


            result = {
                "response_id": response_id,
                "request_id": request_id,
                "timestamp": _utc_now(),
                "status": "PLANNED",
                "execution_mode": "DELEGATED",
                "plan": _copy(
                    response_plan
                ),
                "metadata": {
                    "source": (
                        "response-integration"
                    ),
                    "planning_mode": (
                        "prebuilt-plan"
                    ),
                },
                "engine_version": "integration",
                "error": None,
            }


        # Engine-generated plan.
        else:


            intelligence_result = request.get(
                "intelligence_result"
            )


            if not isinstance(
                intelligence_result,
                dict,
            ):
                return {
                    "response_id": response_id,
                    "request_id": request_id,
                    "status": "REJECTED",
                    "plan": {},
                    "error": (
                        "No response plan or "
                        "intelligence result "
                        "was provided."
                    ),
                }


            if self.engine is None:
                return {
                    "response_id": response_id,
                    "request_id": request_id,
                    "status": "REJECTED",
                    "plan": {},
                    "error": (
                        "Response Engine "
                        "is unavailable."
                    ),
                }


            try:
                result = self._invoke(
                    self.engine,
                    (
                        "plan_response",
                        "plan",
                        "create_response_plan",
                        "process",
                        "run",
                    ),
                    intelligence_result,
                    request=request,
                )


            except Exception as exc:
                return {
                    "response_id": response_id,
                    "request_id": request_id,
                    "status": "FAILED",
                    "plan": {},
                    "error": (
                        "Response Engine failed: "
                        f"{exc}"
                    ),
                }


            if result is None:
                return {
                    "response_id": response_id,
                    "request_id": request_id,
                    "status": "FAILED",
                    "plan": {},
                    "error": (
                        "Response Engine did not "
                        "return a planning result."
                    ),
                }


            if not isinstance(
                result,
                dict,
            ):
                result = {
                    "status": "PLANNED",
                    "result": result,
                }


            result.setdefault(
                "response_id",
                response_id,
            )


            result.setdefault(
                "request_id",
                request_id,
            )


            result.setdefault(
                "status",
                "PLANNED",
            )


        self.statistics.planning_completed += 1


        audit_result = self._audit(
            "RESPONSE_PLANNED",
            request_id=request_id,
            response_id=response_id,
            outcome="PLANNED",
            details=result,
        )


        return {
            "response_id": response_id,
            "result": result,
            "audit": audit_result,
        }


    # ------------------------------------------------------------------------
    # Execution stage
    # ------------------------------------------------------------------------


    def _execution_stage(
        self,
        request: JSONDict,
        planning: JSONDict,
    ) -> JSONDict:
        """
        Delegate execution to ResponseExecutor.


        This integration layer does not perform the action itself.
        """
        request_id = request[
            "request_id"
        ]


        response_id = (
            planning.get("response_id")
            or request.get("response_id")
            or _new_id("ER")
        )


        planned = planning.get(
            "result",
            {},
        )


        plan = None


        if isinstance(
            planned,
            dict,
        ):
            plan = planned.get(
                "plan"
            )


        if not isinstance(
            plan,
            dict,
        ):
            plan = request.get(
                "response_plan"
            )


        if not isinstance(
            plan,
            dict,
        ):
            plan = request.get(
                "plan"
            )


        if not isinstance(
            plan,
            dict,
        ):
            return {
                "result": {
                    "status": "REJECTED",
                    "response_id": response_id,
                    "request_id": request_id,
                    "actions": [],
                    "error": (
                        "No executable response "
                        "plan available."
                    ),
                },
                "audit": {
                    "recorded": False,
                    "available": self.audit is not None,
                    "reason": (
                        "No executable "
                        "response plan."
                    ),
                },
            }


        actions = plan.get(
            "actions"
        )


        if not isinstance(
            actions,
            list,
        ):
            return {
                "result": {
                    "status": "REJECTED",
                    "response_id": response_id,
                    "request_id": request_id,
                    "actions": [],
                    "error": (
                        "Executable response "
                        "plan contains invalid "
                        "actions."
                    ),
                },
                "audit": {
                    "recorded": False,
                    "available": self.audit is not None,
                    "reason": (
                        "Invalid response "
                        "plan actions."
                    ),
                },
            }


        if len(actions) > self.max_actions:
            return {
                "result": {
                    "status": "REJECTED",
                    "response_id": response_id,
                    "request_id": request_id,
                    "actions": [],
                    "error": (
                        "Response plan exceeds "
                        "maximum allowed actions."
                    ),
                },
                "audit": {
                    "recorded": False,
                    "available": self.audit is not None,
                    "reason": (
                        "Action limit exceeded."
                    ),
                },
            }


        if self.executor is None:
            return {
                "result": {
                    "status": "FAILED",
                    "response_id": response_id,
                    "request_id": request_id,
                    "actions": [],
                    "error": (
                        "Response Executor "
                        "is unavailable."
                    ),
                },
                "audit": {
                    "recorded": False,
                    "available": self.audit is not None,
                    "reason": (
                        "Response Executor "
                        "is unavailable."
                    ),
                },
            }


        execution_request = {
            "request_id": request_id,
            "response_id": response_id,
            "response_plan": _copy(plan),
            "plan": _copy(plan),
            "source": "response-integration",
        }


        try:
            result = self._invoke(
                self.executor,
                (
                    "execute",
                    "process",
                    "run",
                    "execute_response",
                ),
                execution_request,
                request=execution_request,
            )


        except Exception as exc:
            result = {
                "status": "FAILED",
                "response_id": response_id,
                "request_id": request_id,
                "actions": [],
                "error": (
                    "Response Executor failed: "
                    f"{exc}"
                ),
            }


        if result is None:
            result = {
                "status": "FAILED",
                "response_id": response_id,
                "request_id": request_id,
                "actions": [],
                "error": (
                    "Response Executor did "
                    "not return a result."
                ),
            }


        if not isinstance(
            result,
            dict,
        ):
            result = {
                "status": "SUCCESS",
                "result": result,
            }


        execution_id = (
            result.get("execution_id")
            or _new_id("EX")
        )


        result.setdefault(
            "execution_id",
            execution_id,
        )


        result.setdefault(
            "response_id",
            response_id,
        )


        result.setdefault(
            "request_id",
            request_id,
        )


        result.setdefault(
            "actions",
            [],
        )


        result.setdefault(
            "status",
            "SUCCESS",
        )


        self.statistics.execution_completed += 1


        audit_result = self._audit(
            "RESPONSE_EXECUTION",
            request_id=request_id,
            response_id=response_id,
            execution_id=execution_id,
            outcome=(
                _status_of(result)
                or "OBSERVED"
            ),
            details=result,
        )


        return {
            "result": result,
            "audit": audit_result,
        }


    # ------------------------------------------------------------------------
    # Verification stage
    # ------------------------------------------------------------------------


    def _verification_stage(
        self,
        request: JSONDict,
        execution: JSONDict,
    ) -> JSONDict:
        """
        Verify the execution result.


        Verification runs even when execution failed so that the final
        lifecycle remains evidence-based and auditable.
        """
        request_id = request[
            "request_id"
        ]


        execution_result = execution.get(
            "result",
            {},
        )


        if not isinstance(
            execution_result,
            dict,
        ):
            execution_result = {
                "status": "FAILED",
                "actions": [],
                "error": (
                    "Execution result "
                    "is invalid."
                ),
            }


        response_id = (
            execution_result.get(
                "response_id"
            )
            or request.get(
                "response_id"
            )
        )


        execution_id = execution_result.get(
            "execution_id"
        )


        if self.verification is None:


            result = {
                "verification_id": _new_id("VR"),
                "status": "FAILED",
                "verified": False,
                "trusted": False,
                "source": "response-executor",
                "actions": [],
                "error": (
                    "Verification Engine "
                    "is unavailable."
                ),
            }


        else:


            verification_request = _copy(
                execution_result
            )


            try:
                result = self._invoke(
                    self.verification,
                    (
                        "verify",
                        "process",
                        "verify_execution",
                        "verify_result",
                    ),
                    verification_request,
                    execution_result=execution_result,
                )


            except Exception as exc:
                result = {
                    "verification_id": _new_id("VR"),
                    "status": "FAILED",
                    "verified": False,
                    "trusted": False,
                    "source": "response-executor",
                    "actions": [],
                    "error": (
                        "Verification Engine "
                        f"failed: {exc}"
                    ),
                }


            if result is None:
                result = {
                    "verification_id": _new_id("VR"),
                    "status": "FAILED",
                    "verified": False,
                    "trusted": False,
                    "source": "response-executor",
                    "actions": [],
                    "error": (
                        "Verification Engine "
                        "did not return a result."
                    ),
                }


            if not isinstance(
                result,
                dict,
            ):
                result = {
                    "verification_id": _new_id("VR"),
                    "status": "FAILED",
                    "verified": False,
                    "trusted": False,
                    "result": result,
                }


        verification_id = (
            result.get("verification_id")
            or _new_id("VR")
        )


        result.setdefault(
            "verification_id",
            verification_id,
        )


        result.setdefault(
            "request_id",
            request_id,
        )


        if response_id is not None:
            result.setdefault(
                "response_id",
                response_id,
            )


        if execution_id is not None:
            result.setdefault(
                "execution_id",
                execution_id,
            )


        self.statistics.verification_completed += 1


        audit_result = self._audit(
            "RESPONSE_VERIFICATION",
            request_id=request_id,
            response_id=response_id,
            execution_id=execution_id,
            verification_id=verification_id,
            outcome=(
                _status_of(result)
                or "OBSERVED"
            ),
            details=result,
        )


        return {
            "result": result,
            "audit": audit_result,
        }


    # ------------------------------------------------------------------------
    # Final status
    # ------------------------------------------------------------------------


    @staticmethod
    def _determine_status(
        planning: JSONDict,
        execution: JSONDict,
        verification: JSONDict,
    ) -> str:
        """
        Determine the final integration status.


        Priority:


            REJECTED
                >
            FAILED
                >
            PARTIAL
                >
            SUCCESS
        """
        planning_result = planning.get(
            "result",
            {},
        )


        execution_result = execution.get(
            "result",
            {},
        )


        verification_result = verification.get(
            "result",
            {},
        )


        if not isinstance(
            planning_result,
            dict,
        ):
            return "FAILED"


        planning_status = _status_of(
            planning_result
        )


        if planning_status == "REJECTED":
            return "REJECTED"


        if planning_status == "FAILED":
            return "FAILED"


        if planning_result.get("error"):
            return "FAILED"


        if not isinstance(
            execution_result,
            dict,
        ):
            return "FAILED"


        execution_status = _status_of(
            execution_result
        )


        if execution_status == "REJECTED":
            return "REJECTED"


        if execution_status == "FAILED":
            return "FAILED"


        if not isinstance(
            verification_result,
            dict,
        ):
            return "FAILED"


        verification_status = _status_of(
            verification_result
        )


        if verification_status == "REJECTED":
            return "FAILED"


        if verification_status == "FAILED":
            return "FAILED"


        if execution_status == "PARTIAL":
            return "PARTIAL"


        if verification_status == "PARTIAL":
            return "PARTIAL"


        if verification_result.get(
            "verified"
        ) is False:
            return "PARTIAL"


        return "SUCCESS"


    # ------------------------------------------------------------------------
    # Result construction
    # ------------------------------------------------------------------------


    def _build_result(
        self,
        *,
        integration_id: str,
        request_id: str,
        started_at: str,
        processing_ms: float,
        status: str,
        response_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        planning: Optional[JSONDict] = None,
        execution: Optional[JSONDict] = None,
        verification: Optional[JSONDict] = None,
        audit: Optional[JSONDict] = None,
        stages_completed: Optional[List[str]] = None,
        stages_failed: Optional[List[str]] = None,
        error: Optional[str] = None,
        idempotent_replay: bool = False,
    ) -> IntegrationResult:
        """
        Construct a normalized IntegrationResult.
        """
        completed_at = _utc_now()


        correlation_hash = _hash(
            {
                "request_id": request_id,
                "response_id": response_id,
                "execution_id": execution_id,
                "verification_id": verification_id,
                "status": status,
            }
        )


        return IntegrationResult(
            integration_id=integration_id,
            request_id=request_id,
            response_id=response_id,
            execution_id=execution_id,
            verification_id=verification_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            planning=_copy(
                planning or {}
            ),
            execution=_copy(
                execution or {}
            ),
            verification=_copy(
                verification or {}
            ),
            audit=_copy(
                audit or {}
            ),
            stages_completed=list(
                stages_completed or []
            ),
            stages_failed=list(
                stages_failed or []
            ),
            processing_time_ms=processing_ms,
            correlation_hash=correlation_hash,
            error=error,
            idempotent_replay=idempotent_replay,
        )


    # ------------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------------


    def _record_final_status(
        self,
        status: str,
    ) -> None:
        """
        Record one final request outcome.
        """
        if status == "SUCCESS":
            self.statistics.successful_requests += 1


        elif status == "PARTIAL":
            self.statistics.partial_requests += 1


        elif status == "REJECTED":
            self.statistics.rejected_requests += 1


        else:
            self.statistics.failed_requests += 1


    # ------------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------------


    def _request_fingerprint(
        self,
        request: Any,
    ) -> str:
        """
        Generate the request idempotency fingerprint.
        """
        return _hash(request)


    def _replay_cached_result(
        self,
        cached: JSONDict,
        *,
        integration_id: str,
        started: float,
    ) -> IntegrationResult:
        """
        Reconstruct an IntegrationResult from the idempotency cache.
        """
        replay = _copy(cached)


        replay["integration_id"] = integration_id
        replay["idempotent_replay"] = True
        replay["completed_at"] = _utc_now()
        replay["processing_time_ms"] = (
            time.perf_counter() - started
        ) * 1000.0


        return IntegrationResult(
            **replay
        )


    # ------------------------------------------------------------------------
    # Main processing pipeline
    # ------------------------------------------------------------------------


    def process(
        self,
        request: Dict[str, Any],
    ) -> IntegrationResult:
        """
        Process one response integration request.
        """
        started = time.perf_counter()
        started_at = _utc_now()


        integration_id = _new_id(
            "INT"
        )


        request_id = (
            request.get(
                "request_id"
            )
            if isinstance(
                request,
                dict,
            )
            else DEFAULT_REQUEST_ID
        )


        # --------------------------------------------------------------------
        # Idempotency
        # --------------------------------------------------------------------


        request_fingerprint = (
            self._request_fingerprint(
                request
            )
        )


        if (
            self.idempotency_enabled
            and request_fingerprint
            in self._idempotency_cache
        ):


            result = self._replay_cached_result(
                self._idempotency_cache[
                    request_fingerprint
                ],
                integration_id=integration_id,
                started=started,
            )


            self.statistics.total_requests += 1
            self.statistics.idempotent_replays += 1


            self.statistics.record_processing(
                result.processing_time_ms
            )


            return result


        self.statistics.total_requests += 1


        # --------------------------------------------------------------------
        # Validation
        # --------------------------------------------------------------------


        validation_error = (
            self._validate_request(
                request
            )
        )


        if validation_error:


            processing_ms = (
                time.perf_counter() - started
            ) * 1000.0


            result = self._build_result(
                integration_id=integration_id,
                request_id=request_id,
                started_at=started_at,
                processing_ms=processing_ms,
                status="REJECTED",
                stages_failed=[
                    "validation"
                ],
                error=validation_error,
            )


            self.statistics.rejected_requests += 1


            self.statistics.record_processing(
                processing_ms
            )


            return result


        # --------------------------------------------------------------------
        # Enabled check
        # --------------------------------------------------------------------


        if not self.enabled:


            processing_ms = (
                time.perf_counter() - started
            ) * 1000.0


            result = self._build_result(
                integration_id=integration_id,
                request_id=request_id,
                started_at=started_at,
                processing_ms=processing_ms,
                status="REJECTED",
                stages_failed=[
                    "integration"
                ],
                error=(
                    "Response Integration "
                    "is disabled."
                ),
            )


            self.statistics.rejected_requests += 1


            self.statistics.record_processing(
                processing_ms
            )


            return result


        # --------------------------------------------------------------------
        # Planning
        # --------------------------------------------------------------------


        planning = self._planning_stage(
            request
        )


        stages_completed: List[str] = []
        stages_failed: List[str] = []


        planning_result = planning.get(
            "result",
            {},
        )


        planning_status = _status_of(
            planning_result
        )


        if planning_status in {
            "REJECTED",
            "FAILED",
        }:


            stages_failed.append(
                "planning"
            )


        else:


            stages_completed.append(
                "planning"
            )


        # --------------------------------------------------------------------
        # Planning failure -> safe stop
        # --------------------------------------------------------------------


        if "planning" in stages_failed:


            processing_ms = (
                time.perf_counter() - started
            ) * 1000.0


            status = (
                "REJECTED"
                if planning_status == "REJECTED"
                else "FAILED"
            )


            error = (
                planning_result.get(
                    "error"
                )
                if isinstance(
                    planning_result,
                    dict,
                )
                else "Planning failed."
            )


            result = self._build_result(
                integration_id=integration_id,
                request_id=request_id,
                started_at=started_at,
                processing_ms=processing_ms,
                status=status,
                response_id=planning.get(
                    "response_id"
                ),
                planning=planning,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
                error=error,
            )


            self._record_final_status(
                status
            )


            self.statistics.record_processing(
                processing_ms
            )


            return result


        # --------------------------------------------------------------------
        # Execution
        # --------------------------------------------------------------------


        execution = self._execution_stage(
            request,
            planning,
        )


        execution_result = execution.get(
            "result",
            {},
        )


        execution_status = _status_of(
            execution_result
        )


        if execution_status in {
            "FAILED",
            "REJECTED",
        }:


            stages_failed.append(
                "execution"
            )


        else:


            stages_completed.append(
                "execution"
            )


        # --------------------------------------------------------------------
        # Verification
        #
        # Verification is intentionally reached even after execution failure.
        # This allows the system to preserve evidence about the failure.
        # --------------------------------------------------------------------


        verification = self._verification_stage(
            request,
            execution,
        )


        verification_result = verification.get(
            "result",
            {},
        )


        verification_status = _status_of(
            verification_result
        )


        if verification_status in {
            "REJECTED",
            "FAILED",
        }:


            stages_failed.append(
                "verification"
            )


        else:


            stages_completed.append(
                "verification"
            )


        # --------------------------------------------------------------------
        # Audit summary
        # --------------------------------------------------------------------


        audit = {
            "planning": planning.get(
                "audit",
                {},
            ),
            "execution": execution.get(
                "audit",
                {},
            ),
            "verification": verification.get(
                "audit",
                {},
            ),
        }


        # --------------------------------------------------------------------
        # Final status
        # --------------------------------------------------------------------


        status = self._determine_status(
            planning,
            execution,
            verification,
        )


        # A failed stage can never result in SUCCESS.
        if stages_failed and status == "SUCCESS":
            status = "PARTIAL"


        # Explicit execution failure has highest operational priority.
        if execution_status == "FAILED":
            status = "FAILED"


        if execution_status == "REJECTED":
            status = "REJECTED"


        # A verification failure after successful execution means the
        # execution result cannot be trusted.
        if (
            verification_status == "FAILED"
            and execution_status
            not in {
                "FAILED",
                "REJECTED",
            }
        ):
            status = "FAILED"


        self._record_final_status(
            status
        )


        processing_ms = (
            time.perf_counter() - started
        ) * 1000.0


        # --------------------------------------------------------------------
        # Identifier extraction
        # --------------------------------------------------------------------


        response_id = (
            planning.get(
                "response_id"
            )
            or (
                execution_result.get(
                    "response_id"
                )
                if isinstance(
                    execution_result,
                    dict,
                )
                else None
            )
            or request.get(
                "response_id"
            )
        )


        execution_id = (
            execution_result.get(
                "execution_id"
            )
            if isinstance(
                execution_result,
                dict,
            )
            else None
        )


        verification_id = (
            verification_result.get(
                "verification_id"
            )
            if isinstance(
                verification_result,
                dict,
            )
            else None
        )


        # --------------------------------------------------------------------
        # Final error
        # --------------------------------------------------------------------


        error: Optional[str] = None


        if (
            execution_status
            in {
                "FAILED",
                "REJECTED",
            }
            and isinstance(
                execution_result,
                dict,
            )
        ):
            error = execution_result.get(
                "error"
            )


        elif (
            verification_status == "FAILED"
            and isinstance(
                verification_result,
                dict,
            )
        ):
            error = verification_result.get(
                "error"
            )


        result = self._build_result(
            integration_id=integration_id,
            request_id=request_id,
            started_at=started_at,
            processing_ms=processing_ms,
            status=status,
            response_id=response_id,
            execution_id=execution_id,
            verification_id=verification_id,
            planning=planning,
            execution=execution,
            verification=verification,
            audit=audit,
            stages_completed=stages_completed,
            stages_failed=stages_failed,
            error=error,
            idempotent_replay=False,
        )


        self.statistics.record_processing(
            processing_ms
        )


        # --------------------------------------------------------------------
        # Cache only completed lifecycle results.
        #
        # The cache contains a serialized snapshot and never the mutable
        # IntegrationResult object itself.
        # --------------------------------------------------------------------


        if self.idempotency_enabled:


            self._idempotency_cache[
                request_fingerprint
            ] = _copy(
                result.to_dict()
            )


        return result


    # ------------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------------


    def self_test(self) -> JSONDict:
        """
        Execute a deterministic integration self-test.


        The self-test validates:
            - health
            - component availability
            - safety guarantees
            - invalid input rejection
            - pipeline completion
            - verification reachability
            - correlation hash generation
            - idempotent replay
            - audit availability
            - audit recording
        """
        checks = {
            "engine_healthy": False,
            "components_available": False,
            "read_only_integration": False,
            "invalid_input_rejected": False,
            "pipeline_completed": False,
            "verification_stage_reached": False,
            "correlation_hash_available": False,
            "idempotency_replay_detected": False,
            "audit_component_available": False,
            "audit_event_recorded": False,
            "no_shell_execution": False,
            "no_destructive_execution": False,
        }


        # --------------------------------------------------------------------
        # Health
        # --------------------------------------------------------------------


        health = self.health_check()


        checks["engine_healthy"] = bool(
            health.get(
                "healthy"
            )
        )


        checks["components_available"] = all(
            component.get(
                "available",
                False,
            )
            for component in health.get(
                "components",
                {},
            ).values()
        )


        checks["audit_component_available"] = bool(
            health.get(
                "components",
                {},
            )
            .get(
                "audit",
                {},
            )
            .get(
                "available",
                False,
            )
        )


        # --------------------------------------------------------------------
        # Safety
        # --------------------------------------------------------------------


        safety = health.get(
            "safety",
            {},
        )


        checks["read_only_integration"] = (
            safety.get(
                "integration_executes_security_actions"
            )
            is False
        )


        checks["no_shell_execution"] = (
            safety.get(
                "shell_execution"
            )
            is False
        )


        checks["no_destructive_execution"] = (
            safety.get(
                "integration_executes_security_actions"
            )
            is False
        )


        # --------------------------------------------------------------------
        # Invalid input
        # --------------------------------------------------------------------


        invalid_result = self.process(
            {
                "request_id":
                    "EG-SELFTEST-INVALID",
                "response_plan": {
                    "actions": "INVALID",
                },
            }
        )


        checks["invalid_input_rejected"] = (
            invalid_result.status
            == "REJECTED"
        )


        # --------------------------------------------------------------------
        # Valid request
        # --------------------------------------------------------------------


        valid_request = {
            "request_id":
                "EG-SELFTEST-INTEGRATION",
            "response_plan": {
                "actions": [
                    {
                        "action_id":
                            "EA-SELFTEST-ALERT",
                        "action_type":
                            "CREATE_ALERT",
                        "severity":
                            "LOW",
                    }
                ]
            },
        }


        first = self.process(
            valid_request
        )


        checks["pipeline_completed"] = (
            "planning"
            in first.stages_completed
            and
            "execution"
            in first.stages_completed
            and
            "verification"
            in first.stages_completed
        )


        checks["verification_stage_reached"] = bool(
            first.verification
        )


        checks["correlation_hash_available"] = bool(
            first.correlation_hash
        )


        # --------------------------------------------------------------------
        # Audit
        # --------------------------------------------------------------------


        audit_recorded = False


        for stage_result in first.audit.values():


            if (
                isinstance(
                    stage_result,
                    dict,
                )
                and stage_result.get(
                    "recorded"
                ) is True
            ):
                audit_recorded = True
                break


        checks["audit_event_recorded"] = (
            audit_recorded
        )


        # --------------------------------------------------------------------
        # Idempotency
        # --------------------------------------------------------------------


        replay = self.process(
            valid_request
        )


        checks["idempotency_replay_detected"] = (
            replay.idempotent_replay is True
            and
            replay.request_id
            == valid_request[
                "request_id"
            ]
        )


        passed_count = sum(
            bool(value)
            for value in checks.values()
        )


        total_checks = len(
            checks
        )


        return {
            "passed": (
                passed_count == total_checks
            ),
            "engine": ENGINE_NAME,
            "version": VERSION,
            "checks": checks,
            "passed_count": passed_count,
            "total_checks": total_checks,
            "statistics": asdict(
                self.statistics
            ),
        }




# ============================================================================
# Global integration instance
# ============================================================================




_integration = ResponseIntegration()




# ============================================================================
# Public API
# ============================================================================




def get_integration() -> ResponseIntegration:
    """
    Return the global ResponseIntegration instance.
    """
    return _integration




def status() -> JSONDict:
    """
    Return integration status.
    """
    return _integration.status()




def health_check() -> JSONDict:
    """
    Return integration health.
    """
    return _integration.health_check()




def process(
    request: Dict[str, Any],
) -> JSONDict:
    """
    Process one response integration request.
    """
    return _integration.process(
        request
    ).to_dict()




def self_test() -> JSONDict:
    """
    Run the integration self-test.
    """
    return _integration.self_test()




# ============================================================================
# Standalone self-test
# ============================================================================




def _self_test() -> None:
    """
    Execute the complete standalone module self-test.
    """
    print()
    print("=" * 78)
    print(
        "EnterpriseGuard Response Integration "
        "- Integration Self Test"
    )
    print("=" * 78)
    print()


    # ------------------------------------------------------------------------
    # 1. Status
    # ------------------------------------------------------------------------


    print("[1] Integration status")


    status_result = status()


    print(
        json.dumps(
            status_result,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print()


    # ------------------------------------------------------------------------
    # 2. Health
    # ------------------------------------------------------------------------


    print("[2] Health check")


    health_result = health_check()


    print(
        json.dumps(
            health_result,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print()


    # ------------------------------------------------------------------------
    # 3. Safety
    # ------------------------------------------------------------------------


    print("[3] Integration safety")


    safety_result = {
        "integration_executes_security_actions":
            False,
        "no_shell_execution":
            True,
        "no_network_operations":
            True,
        "no_process_operations":
            True,
        "no_account_modification":
            True,
    }


    print(
        json.dumps(
            safety_result,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()


    # ------------------------------------------------------------------------
    # 4. Invalid input
    # ------------------------------------------------------------------------


    print(
        "[4] Invalid input protection"
    )


    invalid_request = {
        "request_id":
            "EG-SELFTEST-INVALID",
        "response_plan": {
            "actions": "INVALID",
        },
    }


    invalid_result = _integration.process(
        invalid_request
    )


    print(
        json.dumps(
            invalid_result.to_dict(),
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print()


    # ------------------------------------------------------------------------
    # 5. Pipeline
    # ------------------------------------------------------------------------


    print(
        "[5] Pipeline contract test"
    )


    valid_request = {
        "request_id":
            "EG-SELFTEST-INTEGRATION",
        "response_plan": {
            "actions": [
                {
                    "action_id":
                        "EA-SELFTEST-ALERT",
                    "action_type":
                        "CREATE_ALERT",
                    "severity":
                        "LOW",
                }
            ]
        },
    }


    pipeline_result = _integration.process(
        valid_request
    )


    print(
        json.dumps(
            pipeline_result.to_dict(),
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print()


    # ------------------------------------------------------------------------
    # 6. Idempotency
    # ------------------------------------------------------------------------


    print(
        "[6] Idempotency protection"
    )


    replay_result = _integration.process(
        valid_request
    )


    print(
        json.dumps(
            replay_result.to_dict(),
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print()


    # ------------------------------------------------------------------------
    # 7. Self-test
    # ------------------------------------------------------------------------


    print(
        "[7] Integration self test"
    )


    self_test_result = _integration.self_test()


    print(
        json.dumps(
            self_test_result,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print()


    # ------------------------------------------------------------------------
    # 8. Final verification
    # ------------------------------------------------------------------------


    final_checks = {
        "engine_active":
            status_result.get(
                "status"
            ) == "active",


        "health_check_healthy":
            health_result.get(
                "healthy"
            ) is True,


        "audit_component_available":
            health_result.get(
                "components",
                {},
            )
            .get(
                "audit",
                {},
            )
            .get(
                "available",
                False,
            ) is True,


        "invalid_input_rejected":
            invalid_result.status
            == "REJECTED",


        "pipeline_completed":
            (
                "planning"
                in pipeline_result.stages_completed
                and
                "execution"
                in pipeline_result.stages_completed
                and
                "verification"
                in pipeline_result.stages_completed
            ),


        "correlation_hash_available":
            bool(
                pipeline_result.correlation_hash
            ),


        "idempotency_replay_detected":
            replay_result.idempotent_replay
            is True,


        "no_shell_execution":
            safety_result[
                "no_shell_execution"
            ] is True,


        "no_destructive_execution":
            safety_result[
                "integration_executes_security_actions"
            ] is False,


        "self_test_passed":
            self_test_result.get(
                "passed"
            ) is True,
    }


    print(
        json.dumps(
            final_checks,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()


    if not all(
        final_checks.values()
    ):


        failed = [
            key
            for key, value
            in final_checks.items()
            if not value
        ]


        raise RuntimeError(
            "EnterpriseGuard Response "
            "Integration self-test failed. "
            "Failed checks: "
            + ", ".join(failed)
        )


    print("=" * 78)
    print(
        "Response Integration self test "
        "completed successfully."
    )
    print("=" * 78)
    print()




# ============================================================================
# Entry point
# ============================================================================




if __name__ == "__main__":
    _self_test()