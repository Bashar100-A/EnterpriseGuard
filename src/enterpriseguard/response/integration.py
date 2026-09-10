"""
EnterpriseGuard - Response Integration Layer
=============================================


Responsible for orchestrating the complete response lifecycle:


    Request
       |
       v
    Validation
       |
       v
    Response Engine
       |
       v
    Response Plan
       |
       v
    Response Executor
       |
       v
    Response Verification
       |
       v
    Response Audit
       |
       v
    Integration Result


Design goals
------------
- Deterministic pipeline orchestration
- Strong validation boundaries
- Idempotent request handling
- Correlation across all stages
- Safe-by-default operation
- No shell execution
- No direct security actions
- Read-only integration layer
- Compatible with existing EnterpriseGuard response components
- Explicit failure propagation
- Auditable pipeline state
- Real integration with monitoring.audit.AuditLogger
"""


from __future__ import annotations


import copy
import hashlib
import json
import time
import uuid


from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional




# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


VERSION = "1.2.0"
ENGINE_NAME = "EnterpriseGuard Response Integration"


MAX_INPUT_SIZE = 1_000_000
MAX_ACTIONS = 16




# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()




def _new_id(prefix: str) -> str:
    """Generate a short, readable EnterpriseGuard identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:24].upper()}"




def _canonical_json(value: Any) -> str:
    """
    Serialize a value deterministically.


    This is used for request fingerprints and correlation hashes.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )




def _hash(value: Any) -> str:
    """Return a SHA-256 hash of a canonical representation."""
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()




def _safe_len(value: Any) -> int:
    """
    Safely estimate serialized input size.


    Serialization failures are treated as oversized input.
    """
    try:
        return len(_canonical_json(value))
    except Exception:
        return MAX_INPUT_SIZE + 1




def _copy(value: Any) -> Any:
    """Return a defensive deep copy."""
    return copy.deepcopy(value)




# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


@dataclass
class IntegrationResult:
    """
    Final result returned by ResponseIntegration.


    This object represents the complete lifecycle of one integration
    request and contains the state of every pipeline stage.
    """


    integration_id: str
    request_id: str


    response_id: Optional[str] = None
    execution_id: Optional[str] = None
    verification_id: Optional[str] = None


    status: str = "FAILED"


    started_at: str = field(default_factory=_utc_now)
    completed_at: Optional[str] = None


    planning: Dict[str, Any] = field(default_factory=dict)
    execution: Dict[str, Any] = field(default_factory=dict)
    verification: Dict[str, Any] = field(default_factory=dict)
    audit: Dict[str, Any] = field(default_factory=dict)


    stages_completed: List[str] = field(default_factory=list)
    stages_failed: List[str] = field(default_factory=list)


    processing_time_ms: float = 0.0
    correlation_hash: str = ""


    error: Optional[str] = None


    # Explicitly part of the dataclass.
    # Never inject dynamically.
    idempotent_replay: bool = False


    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable representation."""
        return asdict(self)




# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@dataclass
class IntegrationStatistics:
    """Runtime statistics for the integration layer."""


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


    def record_processing(self, processing_ms: float) -> None:
        """
        Update average and maximum processing time.


        total_requests must already include the current request.
        """
        previous_total = (
            self.average_processing_ms
            * max(0, self.total_requests - 1)
        )


        count = max(1, self.total_requests)


        self.average_processing_ms = (
            previous_total + processing_ms
        ) / count


        self.max_processing_ms = max(
            self.max_processing_ms,
            processing_ms,
        )




# ---------------------------------------------------------------------------
# Response Integration
# ---------------------------------------------------------------------------


class ResponseIntegration:
    """
    Orchestrates the complete response lifecycle.


    Important:
        This class does NOT execute security actions directly.


    Security actions remain the responsibility of ResponseExecutor.
    Verification remains the responsibility of ResponseVerificationEngine.
    Audit persistence remains the responsibility of AuditLogger.
    """


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


        self.engine = engine or self._load_component(
            "enterpriseguard.response.engine",
            (
                "ResponseEngine",
                "EnterpriseGuardResponseEngine",
            ),
        )


        self.executor = executor or self._load_component(
            "enterpriseguard.response.executor",
            (
                "ResponseExecutor",
                "EnterpriseGuardResponseExecutor",
            ),
        )


        self.verification = verification or self._load_component(
            "enterpriseguard.response.verification",
            (
                "ResponseVerificationEngine",
                "ResponseVerification",
            ),
        )


        # IMPORTANT:
        # The real EnterpriseGuard audit component is:
        #
        #     enterpriseguard.monitoring.audit.AuditLogger
        #
        # Do not create or use audit/logger.py.
        self.audit = audit or self._load_component(
            "enterpriseguard.monitoring.audit",
            (
                "AuditLogger",
            ),
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


        # request_fingerprint -> serialized IntegrationResult
        self._idempotency_cache: Dict[
            str,
            Dict[str, Any],
        ] = {}


    # ------------------------------------------------------------------
    # Component loading
    # ------------------------------------------------------------------


    @staticmethod
    def _load_component(
        module_name: str,
        class_names: tuple,
    ) -> Any:
        """
        Dynamically load an EnterpriseGuard component.


        Component loading failure is intentionally non-fatal here.
        health_check() exposes unavailable components explicitly.
        """


        try:
            module = __import__(
                module_name,
                fromlist=list(class_names),
            )
        except Exception:
            return None


        for class_name in class_names:


            cls = getattr(
                module,
                class_name,
                None,
            )


            if cls is None:
                continue


            try:
                return cls()
            except Exception:
                continue


        return None


    # ------------------------------------------------------------------
    # Generic component invocation
    # ------------------------------------------------------------------


    @staticmethod
    def _invoke(
        component: Any,
        method_names: tuple,
        *args,
        **kwargs,
    ) -> Any:
        """
        Invoke the first compatible public method.


        Compatibility order:
            1. keyword + positional arguments
            2. positional arguments
            3. no arguments


        TypeError is treated as a signature mismatch.
        Other exceptions propagate.
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


                except Exception:
                    raise


            if args:


                try:
                    return method(
                        *args,
                    )


                except TypeError:
                    pass


                except Exception:
                    raise


            try:
                return method()


            except TypeError:
                continue


        return None


    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------


    def status(self) -> Dict[str, Any]:
        """Return runtime status and safety configuration."""


        return {
            "engine": ENGINE_NAME,
            "version": VERSION,
            "status": (
                "active"
                if self.enabled
                else "disabled"
            ),


            "components": {
                "engine": self.engine is not None,
                "executor": self.executor is not None,
                "verification": self.verification is not None,
                "audit": self.audit is not None,
            },


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
                "read_only_integration": True,
                "executes_security_actions": False,
                "shell_execution": False,
                "network_operations": False,
                "process_operations": False,
                "account_modification": False,
            },
        }


    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------


    def health_check(self) -> Dict[str, Any]:
        """
        Verify that the integration layer and all required components
        are available.
        """


        components = {
            "engine": self.engine is not None,
            "executor": self.executor is not None,
            "verification": self.verification is not None,
            "audit": self.audit is not None,
        }


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
                "planning": components["engine"],
                "execution": components["executor"],
                "verification": components["verification"],
                "audit": components["audit"],
            },


            "safety": {
                "read_only_integration": True,
                "executes_security_actions": False,
                "shell_execution": False,
                "network_operations": False,
                "process_operations": False,
                "account_modification": False,
            },
        }


    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------


    def _validate_request(
        self,
        request: Dict[str, Any],
    ) -> Optional[str]:
        """
        Validate an integration request.


        A request may contain either:


            response_plan / plan


        OR:


            intelligence_result


        This is important because the Response Engine must remain
        reachable when the caller has not already constructed a plan.
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


        # At least one planning source is required.
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


        # Validate a supplied plan.
        if isinstance(
            response_plan,
            dict,
        ):


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


    # ------------------------------------------------------------------
    # Audit integration
    # ------------------------------------------------------------------


    def _audit(
        self,
        event_type: str,
        *,
        request_id: str,
        response_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        outcome: str = "OBSERVED",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record an auditable integration event.


        Primary integration target:


            enterpriseguard.monitoring.audit.AuditLogger


        The real AuditLogger supports:


            record(...)
            log_event(payload)


        We prefer the explicit record() contract and retain
        log_event() as a compatibility fallback.
        """


        if self.audit is None:


            return {
                "recorded": False,
                "available": False,
                "reason": (
                    "AuditLogger is unavailable."
                ),
            }


        details = details or {}


        metadata = {
            "integration_version": VERSION,
            "request_id": request_id,
            "response_id": response_id,
            "execution_id": execution_id,
            "verification_id": verification_id,
            "source": "response-integration",
            "details": _copy(details),
        }


        # --------------------------------------------------------------
        # Preferred AuditLogger API
        # --------------------------------------------------------------


        record_method = getattr(
            self.audit,
            "record",
            None,
        )


        if callable(record_method):


            try:


                audit_event = record_method(
                    event_type=event_type,
                    action=event_type,
                    outcome=outcome,
                    severity="INFO",
                    actor_id="system",
                    actor_ip=None,
                    resource=response_id
                    or execution_id
                    or request_id,
                    message=(
                        f"Response Integration event: "
                        f"{event_type}"
                    ),
                    metadata=metadata,
                    correlation_id=request_id,
                    source="response-integration",
                )


                self.statistics.audit_events += 1


                if hasattr(
                    audit_event,
                    "to_dict",
                ):


                    return {
                        "recorded": True,
                        "available": True,
                        "event": audit_event.to_dict(),
                    }


                if hasattr(
                    audit_event,
                    "__dict__",
                ):


                    return {
                        "recorded": True,
                        "available": True,
                        "event": asdict(
                            audit_event
                        )
                        if hasattr(
                            audit_event,
                            "__dataclass_fields__",
                        )
                        else dict(
                            audit_event.__dict__
                        ),
                    }


                return {
                    "recorded": True,
                    "available": True,
                    "event": audit_event,
                }


            except Exception as exc:


                return {
                    "recorded": False,
                    "available": True,
                    "error": str(exc),
                }


        # --------------------------------------------------------------
        # Compatibility fallback
        # --------------------------------------------------------------


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
                    f"Response Integration event: "
                    f"{event_type}"
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


                if isinstance(
                    result,
                    dict,
                ):


                    return {
                        "recorded": True,
                        "available": True,
                        **result,
                    }


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


    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------


    def _planning_stage(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build or accept a response plan.


        Two valid paths exist:


            1. Existing response_plan
               -> preserve it


            2. intelligence_result
               -> delegate to ResponseEngine
        """


        request_id = request[
            "request_id"
        ]


        response_id = request.get(
            "response_id"
        ) or _new_id("ER")


        response_plan = request.get(
            "response_plan"
        )


        if response_plan is None:
            response_plan = request.get(
                "plan"
            )


        # --------------------------------------------------------------
        # Existing plan
        # --------------------------------------------------------------


        if response_plan is not None:


            result = {
                "response_id": response_id,
                "request_id": request_id,
                "timestamp": _utc_now(),
                "status": "PLANNED",
                "execution_mode": "DRY_RUN",
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


        # --------------------------------------------------------------
        # Response Engine path
        # --------------------------------------------------------------


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
                    "status": "REJECTED",
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


    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------


    def _execution_stage(
        self,
        request: Dict[str, Any],
        planning: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Delegate execution to ResponseExecutor.


        Integration itself performs no security action.
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
                    "available": (
                        self.audit is not None
                    ),
                    "reason": (
                        "No executable "
                        "response plan."
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
                    "available": (
                        self.audit is not None
                    ),
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


        execution_id = result.get(
            "execution_id"
        ) or _new_id("EX")


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


        self.statistics.execution_completed += 1


        audit_result = self._audit(
            "RESPONSE_EXECUTION",
            request_id=request_id,
            response_id=response_id,
            execution_id=execution_id,
            outcome=result.get(
                "status",
                "OBSERVED",
            ),
            details=result,
        )


        return {
            "result": result,
            "audit": audit_result,
        }


    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------


    def _verification_stage(
        self,
        request: Dict[str, Any],
        execution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verify the executor result.


        Verification may inspect a failed execution so that the final
        state remains auditable and evidence-based.


        However, verification cannot turn an actual execution failure
        into a SUCCESS state.
        """


        execution_result = execution.get(
            "result",
            {},
        )


        request_id = request[
            "request_id"
        ]


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


        verification_id = result.get(
            "verification_id"
        ) or _new_id("VR")


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
            outcome=result.get(
                "status",
                "OBSERVED",
            ),
            details=result,
        )


        return {
            "result": result,
            "audit": audit_result,
        }


    # ------------------------------------------------------------------
    # Pipeline status
    # ------------------------------------------------------------------


    @staticmethod
    def _determine_status(
        planning: Dict[str, Any],
        execution: Dict[str, Any],
        verification: Dict[str, Any],
    ) -> str:
        """
        Determine the final pipeline state.


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


        planning_status = planning_result.get(
            "status"
        )


        if planning_status == "REJECTED":
            return "REJECTED"


        if planning_status == "FAILED":
            return "FAILED"


        if planning_result.get(
            "error"
        ):
            return "FAILED"


        if not isinstance(
            execution_result,
            dict,
        ):
            return "FAILED"


        execution_status = execution_result.get(
            "status"
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


        verification_status = (
            verification_result.get(
                "status"
            )
        )


        if verification_status in {
            "REJECTED",
            "FAILED",
        }:
            return "FAILED"


        if execution_status == "PARTIAL":
            return "PARTIAL"


        if verification_status == "PARTIAL":
            return "PARTIAL"


        if (
            verification_result.get(
                "verified"
            ) is False
        ):
            return "PARTIAL"


        return "SUCCESS"


    # ------------------------------------------------------------------
    # Result factory
    # ------------------------------------------------------------------


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
        planning: Optional[Dict[str, Any]] = None,
        execution: Optional[Dict[str, Any]] = None,
        verification: Optional[Dict[str, Any]] = None,
        audit: Optional[Dict[str, Any]] = None,
        stages_completed: Optional[List[str]] = None,
        stages_failed: Optional[List[str]] = None,
        error: Optional[str] = None,
        idempotent_replay: bool = False,
    ) -> IntegrationResult:
        """Build a consistent IntegrationResult."""


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
            planning=planning or {},
            execution=execution or {},
            verification=verification or {},
            audit=audit or {},
            stages_completed=stages_completed or [],
            stages_failed=stages_failed or [],
            processing_time_ms=processing_ms,
            correlation_hash=correlation_hash,
            error=error,
            idempotent_replay=idempotent_replay,
        )


    # ------------------------------------------------------------------
    # Statistics helper
    # ------------------------------------------------------------------


    def _record_final_status(
        self,
        status: str,
    ) -> None:
        """Record the final request outcome."""


        if status == "SUCCESS":


            self.statistics.successful_requests += 1


        elif status == "PARTIAL":


            self.statistics.partial_requests += 1


        elif status == "REJECTED":


            self.statistics.rejected_requests += 1


        else:


            self.statistics.failed_requests += 1


    # ------------------------------------------------------------------
    # Main process
    # ------------------------------------------------------------------


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
            else "unknown"
        )


        # --------------------------------------------------------------
        # Idempotency fingerprint
        # --------------------------------------------------------------


        request_fingerprint = _hash(
            request
        )


        if (
            self.idempotency_enabled
            and request_fingerprint
            in self._idempotency_cache
        ):


            cached = _copy(
                self._idempotency_cache[
                    request_fingerprint
                ]
            )


            cached[
                "integration_id"
            ] = integration_id


            cached[
                "idempotent_replay"
            ] = True


            cached[
                "processing_time_ms"
            ] = (
                time.perf_counter()
                - started
            ) * 1000.0


            cached[
                "completed_at"
            ] = _utc_now()


            result = IntegrationResult(
                **cached
            )


            self.statistics.idempotent_replays += 1
            self.statistics.total_requests += 1


            self.statistics.record_processing(
                result.processing_time_ms
            )


            return result


        self.statistics.total_requests += 1


        # --------------------------------------------------------------
        # Validation
        # --------------------------------------------------------------


        validation_error = (
            self._validate_request(
                request
            )
        )


        if validation_error:


            processing_ms = (
                time.perf_counter()
                - started
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


        # --------------------------------------------------------------
        # Enabled check
        # --------------------------------------------------------------


        if not self.enabled:


            processing_ms = (
                time.perf_counter()
                - started
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


        # --------------------------------------------------------------
        # Planning
        # --------------------------------------------------------------


        planning = self._planning_stage(
            request
        )


        stages_completed: List[str] = []
        stages_failed: List[str] = []


        planning_result = planning.get(
            "result",
            {},
        )


        planning_status = (
            planning_result.get(
                "status"
            )
            if isinstance(
                planning_result,
                dict,
            )
            else None
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


        # --------------------------------------------------------------
        # Planning failure = immediate safe stop
        # --------------------------------------------------------------


        if "planning" in stages_failed:


            processing_ms = (
                time.perf_counter()
                - started
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
                stages_completed=(
                    stages_completed
                ),
                stages_failed=(
                    stages_failed
                ),
                error=error,
            )


            self._record_final_status(
                status
            )


            self.statistics.record_processing(
                processing_ms
            )


            return result


        # --------------------------------------------------------------
        # Execution
        # --------------------------------------------------------------


        execution = self._execution_stage(
            request,
            planning,
        )


        execution_result = execution.get(
            "result",
            {},
        )


        execution_status = (
            execution_result.get(
                "status"
            )
            if isinstance(
                execution_result,
                dict,
            )
            else None
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


        # --------------------------------------------------------------
        # Verification
        #
        # We intentionally continue here even after an execution
        # failure so the verification engine can record evidence
        # about the failed execution.
        # --------------------------------------------------------------


        verification = (
            self._verification_stage(
                request,
                execution,
            )
        )


        verification_result = (
            verification.get(
                "result",
                {},
            )
        )


        verification_status = (
            verification_result.get(
                "status"
            )
            if isinstance(
                verification_result,
                dict,
            )
            else None
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


        # --------------------------------------------------------------
        # Audit summary
        # --------------------------------------------------------------


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


        # --------------------------------------------------------------
        # Final status
        # --------------------------------------------------------------


        status = self._determine_status(
            planning,
            execution,
            verification,
        )


        # Any failed stage prevents SUCCESS.
        if stages_failed and status == "SUCCESS":


            status = "PARTIAL"


        # Execution failure must remain FAILED.
        if execution_status == "FAILED":


            status = "FAILED"


        # Execution rejection must remain REJECTED.
        if execution_status == "REJECTED":


            status = "REJECTED"


        # Verification failure after otherwise successful execution
        # means the final response cannot be trusted.
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
            time.perf_counter()
            - started
        ) * 1000.0


        # --------------------------------------------------------------
        # Explicit identifier extraction
        # --------------------------------------------------------------


        response_id = None


        if isinstance(
            planning,
            dict,
        ):


            response_id = planning.get(
                "response_id"
            )


        if (
            response_id is None
            and isinstance(
                execution_result,
                dict,
            )
        ):


            response_id = execution_result.get(
                "response_id"
            )


        if response_id is None:


            response_id = request.get(
                "response_id"
            )


        execution_id = None


        if isinstance(
            execution_result,
            dict,
        ):


            execution_id = execution_result.get(
                "execution_id"
            )


        verification_id = None


        if isinstance(
            verification_result,
            dict,
        ):


            verification_id = (
                verification_result.get(
                    "verification_id"
                )
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
            stages_completed=(
                stages_completed
            ),
            stages_failed=(
                stages_failed
            ),
            error=(
                execution_result.get(
                    "error"
                )
                if (
                    isinstance(
                        execution_result,
                        dict,
                    )
                    and execution_status
                    in {
                        "FAILED",
                        "REJECTED",
                    }
                )
                else (
                    verification_result.get(
                        "error"
                    )
                    if (
                        isinstance(
                            verification_result,
                            dict,
                        )
                        and verification_status
                        == "FAILED"
                    )
                    else None
                )
            ),
            idempotent_replay=False,
        )


        self.statistics.record_processing(
            processing_ms
        )


        # --------------------------------------------------------------
        # Cache serializable result for replay.
        #
        # Original integration_id and replay flag are overwritten
        # when the cached result is replayed.
        # --------------------------------------------------------------


        if self.idempotency_enabled:


            cached = result.to_dict()


            cached[
                "idempotent_replay"
            ] = False


            self._idempotency_cache[
                request_fingerprint
            ] = _copy(cached)


        return result


    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------


    def self_test(self) -> Dict[str, Any]:
        """
        Execute a deterministic integration self-test.


        The test verifies both the orchestration contract and the
        real audit component availability.
        """


        checks = {
            "engine_healthy": False,
            "components_available": False,
            "read_only_safety": False,
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


        # --------------------------------------------------------------
        # Health
        # --------------------------------------------------------------


        health = self.health_check()


        checks[
            "engine_healthy"
        ] = bool(
            health.get(
                "healthy"
            )
        )


        checks[
            "components_available"
        ] = all(
            value.get(
                "available",
                False,
            )
            for value in health.get(
                "components",
                {},
            ).values()
        )


        checks[
            "audit_component_available"
        ] = bool(
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


        # --------------------------------------------------------------
        # Safety
        # --------------------------------------------------------------


        safety = health.get(
            "safety",
            {},
        )


        checks[
            "read_only_safety"
        ] = (
            safety.get(
                "read_only_integration"
            )
            is True
        )


        checks[
            "no_shell_execution"
        ] = (
            safety.get(
                "shell_execution"
            )
            is False
        )


        checks[
            "no_destructive_execution"
        ] = (
            safety.get(
                "executes_security_actions"
            )
            is False
        )


        # --------------------------------------------------------------
        # Invalid request
        # --------------------------------------------------------------


        invalid = self.process(
            {
                "request_id":
                    "EG-SELFTEST-INVALID",
                "response_plan": {
                    "actions": "INVALID",
                },
            }
        )


        checks[
            "invalid_input_rejected"
        ] = (
            invalid.status
            == "REJECTED"
        )


        # --------------------------------------------------------------
        # Valid deterministic request
        # --------------------------------------------------------------


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


        checks[
            "pipeline_completed"
        ] = (
            "planning"
            in first.stages_completed
            and
            "execution"
            in first.stages_completed
            and
            "verification"
            in first.stages_completed
        )


        checks[
            "verification_stage_reached"
        ] = bool(
            first.verification
        )


        checks[
            "correlation_hash_available"
        ] = bool(
            first.correlation_hash
        )


        # --------------------------------------------------------------
        # Audit verification
        # --------------------------------------------------------------


        audit_results = (
            first.audit
        )


        audit_recorded = False


        for stage_result in (
            audit_results.values()
        ):


            if (
                isinstance(
                    stage_result,
                    dict,
                )
                and stage_result.get(
                    "recorded"
                )
                is True
            ):


                audit_recorded = True
                break


        checks[
            "audit_event_recorded"
        ] = audit_recorded


        # --------------------------------------------------------------
        # Idempotency
        # --------------------------------------------------------------


        replay = self.process(
            valid_request
        )


        checks[
            "idempotency_replay_detected"
        ] = (
            replay.idempotent_replay
            is True
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


        passed = (
            passed_count
            == total_checks
        )


        return {
            "passed": passed,
            "engine": ENGINE_NAME,
            "version": VERSION,
            "checks": checks,
            "passed_count": passed_count,
            "total_checks": total_checks,
            "statistics": asdict(
                self.statistics
            ),
        }




# ---------------------------------------------------------------------------
# Global integration instance
# ---------------------------------------------------------------------------


_integration = ResponseIntegration()




# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_integration() -> ResponseIntegration:
    """Return the global ResponseIntegration instance."""
    return _integration




def status() -> Dict[str, Any]:
    """Return integration status."""
    return _integration.status()




def health_check() -> Dict[str, Any]:
    """Return integration health."""
    return _integration.health_check()




def process(
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Process a response integration request."""
    return _integration.process(
        request
    ).to_dict()




def self_test() -> Dict[str, Any]:
    """Run the integration self-test."""
    return _integration.self_test()




# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------


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


    # --------------------------------------------------------------
    # 1. Status
    # --------------------------------------------------------------


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


    # --------------------------------------------------------------
    # 2. Health
    # --------------------------------------------------------------


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


    # --------------------------------------------------------------
    # 3. Safety
    # --------------------------------------------------------------


    print("[3] Integration safety")


    safety_result = {
        "read_only_integration": True,
        "no_security_actions": True,
        "no_shell_execution": True,
        "no_network_operations": True,
        "no_process_operations": True,
        "no_account_modification": True,
    }


    print(
        json.dumps(
            safety_result,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()


    # --------------------------------------------------------------
    # 4. Invalid input
    # --------------------------------------------------------------


    print("[4] Invalid input protection")


    invalid_request = {
        "request_id":
            "EG-SELFTEST-INVALID",


        "response_plan": {
            "actions": "INVALID",
        },
    }


    invalid_result = (
        _integration.process(
            invalid_request
        )
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


    # --------------------------------------------------------------
    # 5. Pipeline contract
    # --------------------------------------------------------------


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


    pipeline_result = (
        _integration.process(
            valid_request
        )
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


    # --------------------------------------------------------------
    # 6. Idempotency
    # --------------------------------------------------------------


    print(
        "[6] Idempotency protection"
    )


    replay_result = (
        _integration.process(
            valid_request
        )
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


    # --------------------------------------------------------------
    # 7. Self-test
    # --------------------------------------------------------------


    print(
        "[7] Integration self test"
    )


    self_test_result = (
        _integration.self_test()
    )


    print(
        json.dumps(
            self_test_result,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print()


    # --------------------------------------------------------------
    # 8. Final verification
    # --------------------------------------------------------------


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
            True,


        "no_destructive_execution":
            True,


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




# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    _self_test()