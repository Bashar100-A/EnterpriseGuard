"""
EnterpriseGuard - Response Verification Engine
==============================================


Purpose
-------
Verifies the result of a Response Executor operation without executing
security actions itself.


Design principles
-----------------
- Strictly read-only.
- Never executes shell commands.
- Never modifies the network.
- Never terminates processes.
- Never modifies accounts.
- EXECUTED != VERIFIED.
- SIMULATED may be VERIFIED as a simulation result.
- REJECTED / FAILED actions are never considered verified.
- EXECUTED actions without a registered verifier are NOT trusted.
- Supports registered verification hooks for future real integrations.
- Provides deterministic self-tests.
"""


from __future__ import annotations


import hashlib
import json
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional




# ============================================================================
# Constants
# ============================================================================


ENGINE_NAME = "EnterpriseGuard Response Verification Engine"
ENGINE_VERSION = "1.1.0"


MAX_INPUT_SIZE = 1_000_000
MAX_ACTIONS = 16
PROCESSING_TARGET_MS = 50.0


STATUS_VERIFIED = "VERIFIED"
STATUS_PARTIAL = "PARTIAL"
STATUS_FAILED = "FAILED"
STATUS_REJECTED = "REJECTED"
STATUS_SKIPPED = "SKIPPED"


ACTION_VERIFIED = "VERIFIED"
ACTION_FAILED = "FAILED"
ACTION_SKIPPED = "SKIPPED"
ACTION_UNSUPPORTED = "UNSUPPORTED"


EXECUTED = "EXECUTED"
SIMULATED = "SIMULATED"
REJECTED = "REJECTED"
FAILED = "FAILED"
SKIPPED = "SKIPPED"


KNOWN_ACTION_STATUSES = {
    EXECUTED,
    SIMULATED,
    REJECTED,
    FAILED,
    SKIPPED,
}


KNOWN_VERIFICATION_STATUSES = {
    ACTION_VERIFIED,
    ACTION_FAILED,
    ACTION_SKIPPED,
    ACTION_UNSUPPORTED,
}




# ============================================================================
# Utility functions
# ============================================================================


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()




def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:24].upper()}"




def _safe_json_size(value: Any) -> int:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return len(encoded)
    except Exception:
        return MAX_INPUT_SIZE + 1




def _normalise(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(k): _normalise(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }


    if isinstance(value, (list, tuple)):
        return [_normalise(v) for v in value]


    if isinstance(value, set):
        return sorted(_normalise(v) for v in value)


    return value




def _fingerprint(value: Any) -> str:
    payload = json.dumps(
        _normalise(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()




# ============================================================================
# Verification hook
# ============================================================================


VerifierHook = Callable[
    [Mapping[str, Any], Mapping[str, Any]],
    Mapping[str, Any],
]




@dataclass(frozen=True)
class VerificationHook:
    action_type: str
    verifier: VerifierHook
    description: str = ""




# ============================================================================
# Verification Engine
# ============================================================================


class ResponseVerificationEngine:
    """
    Read-only verification layer for EnterpriseGuard response execution.


    The engine verifies claims made by the executor. It does not execute
    security operations.
    """


    def __init__(
        self,
        *,
        enabled: bool = True,
        audit_enabled: bool = True,
        max_input_size: int = MAX_INPUT_SIZE,
        max_actions: int = MAX_ACTIONS,
        processing_target_ms: float = PROCESSING_TARGET_MS,
    ) -> None:
        self.enabled = bool(enabled)
        self.audit_enabled = bool(audit_enabled)
        self.max_input_size = int(max_input_size)
        self.max_actions = int(max_actions)
        self.processing_target_ms = float(processing_target_ms)


        self._hooks: Dict[str, VerificationHook] = {}
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}


        self._stats: Dict[str, int] = {
            "total_requests": 0,
            "verified_requests": 0,
            "partial_requests": 0,
            "failed_requests": 0,
            "rejected_requests": 0,
            "skipped_requests": 0,
            "actions_verified": 0,
            "actions_failed": 0,
            "actions_skipped": 0,
            "actions_unsupported": 0,
        }


        self._status_counts: Dict[str, int] = {
            STATUS_VERIFIED: 0,
            STATUS_PARTIAL: 0,
            STATUS_FAILED: 0,
            STATUS_REJECTED: 0,
            STATUS_SKIPPED: 0,
        }


        self._action_status_counts: Dict[str, int] = {
            ACTION_VERIFIED: 0,
            ACTION_FAILED: 0,
            ACTION_SKIPPED: 0,
            ACTION_UNSUPPORTED: 0,
        }


        self._action_type_counts: Dict[str, int] = {}


        self._processing_samples: List[float] = []


    # ---------------------------------------------------------------------
    # Registration
    # ---------------------------------------------------------------------


    def register_hook(
        self,
        action_type: str,
        verifier: VerifierHook,
        description: str = "",
    ) -> None:
        """
        Register a read-only verifier for an action type.
        """
        if not isinstance(action_type, str) or not action_type.strip():
            raise ValueError("action_type must be a non-empty string.")


        if not callable(verifier):
            raise TypeError("verifier must be callable.")


        key = action_type.strip().upper()


        self._hooks[key] = VerificationHook(
            action_type=key,
            verifier=verifier,
            description=description.strip(),
        )


    def unregister_hook(self, action_type: str) -> bool:
        key = str(action_type).strip().upper()
        return self._hooks.pop(key, None) is not None


    # ---------------------------------------------------------------------
    # Status
    # ---------------------------------------------------------------------


    def status(self) -> Dict[str, Any]:
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "status": "active" if self.enabled else "disabled",
            "configuration": {
                "enabled": self.enabled,
                "audit_enabled": self.audit_enabled,
                "max_input_size": self.max_input_size,
                "max_actions": self.max_actions,
                "processing_target_ms": self.processing_target_ms,
            },
            "verification": {
                "post_execution_verification": True,
                "hooks_registered": len(self._hooks),
                "registered_hooks": sorted(self._hooks.keys()),
                "execution": "READ_ONLY",
            },
            "statistics": self._statistics(),
            "status_counts": dict(self._status_counts),
            "action_status_counts": dict(self._action_status_counts),
            "action_type_counts": dict(self._action_type_counts),
            "safety": {
                "executes_security_actions": False,
                "shell_execution_enabled": False,
                "network_operations_enabled": False,
                "process_operations_enabled": False,
                "account_modification_enabled": False,
            },
            "notes": {
                "purpose": (
                    "Verify whether response execution results can be "
                    "trusted as verified state."
                ),
                "execution": (
                    "The Verification Engine never executes security actions."
                ),
                "verification": (
                    "EXECUTED does not automatically mean VERIFIED."
                ),
            },
        }


    def health_check(self) -> Dict[str, Any]:
        return {
            "healthy": bool(self.enabled),
            "engine": {
                "enabled": self.enabled,
                "version": ENGINE_VERSION,
            },
            "verification": {
                "available": self.enabled,
                "hook_count": len(self._hooks),
                "post_execution_verification": True,
            },
            "safety": {
                "executes_security_actions": False,
                "shell_execution": False,
                "network_operations": False,
                "process_operations": False,
                "account_modification": False,
            },
            "configuration": {
                "max_input_size": self.max_input_size,
                "max_actions": self.max_actions,
                "processing_target_ms": self.processing_target_ms,
                "audit_enabled": self.audit_enabled,
            },
        }


    # ---------------------------------------------------------------------
    # Verification
    # ---------------------------------------------------------------------


    def verify(
        self,
        execution_result: Mapping[str, Any],
        *,
        source: str = "response-executor",
    ) -> Dict[str, Any]:
        """
        Verify a Response Executor result.


        Important semantic rule:


            EXECUTED + no verifier = UNSUPPORTED / FAILED trust state


        It is never converted into VERIFIED merely because the executor
        reported EXECUTED.
        """
        started = time.perf_counter()


        self._stats["total_requests"] += 1


        verification_id = _new_id("VR")


        try:
            if not self.enabled:
                return self._reject(
                    verification_id,
                    source,
                    "Verification engine is disabled.",
                    started,
                )


            if not isinstance(execution_result, Mapping):
                return self._reject(
                    verification_id,
                    source,
                    "Execution result must be a mapping.",
                    started,
                )


            if _safe_json_size(execution_result) > self.max_input_size:
                return self._reject(
                    verification_id,
                    source,
                    "Execution result exceeds maximum input size.",
                    started,
                )


            actions = execution_result.get("actions")


            if actions is None:
                return self._reject(
                    verification_id,
                    source,
                    "Execution result must contain an actions collection.",
                    started,
                )


            if not isinstance(actions, list):
                return self._reject(
                    verification_id,
                    source,
                    "Execution result actions must be a list.",
                    started,
                )


            if len(actions) > self.max_actions:
                return self._reject(
                    verification_id,
                    source,
                    "Execution result exceeds maximum action count.",
                    started,
                )


            if len(actions) == 0:
                result = self._verify_empty_execution(
                    verification_id,
                    execution_result,
                    source,
                    started,
                )
                return result


            verified_actions: List[Dict[str, Any]] = []


            for action in actions:
                verified_actions.append(
                    self._verify_action(
                        action,
                        execution_result,
                    )
                )


            result = self._build_request_result(
                verification_id=verification_id,
                execution_result=execution_result,
                action_results=verified_actions,
                source=source,
                started=started,
            )


            return result


        except Exception as exc:
            elapsed = self._record_processing(started)


            self._stats["failed_requests"] += 1
            self._status_counts[STATUS_FAILED] += 1


            return {
                "verification_id": verification_id,
                "timestamp": _utc_now(),
                "status": STATUS_FAILED,
                "verified": False,
                "trusted": False,
                "source": source,
                "actions": [],
                "actions_verified": 0,
                "actions_failed": 0,
                "actions_skipped": 0,
                "actions_unsupported": 0,
                "processing_time_ms": round(elapsed, 3),
                "within_processing_target": (
                    elapsed <= self.processing_target_ms
                ),
                "audit": self._audit_record(
                    verification_id,
                    source,
                    STATUS_FAILED,
                ),
                "error": str(exc),
                "engine_version": ENGINE_VERSION,
            }


    # ---------------------------------------------------------------------
    # Action verification
    # ---------------------------------------------------------------------


    def _verify_action(
        self,
        action: Any,
        execution_result: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(action, Mapping):
            self._stats["actions_failed"] += 1
            self._action_status_counts[ACTION_FAILED] += 1


            return {
                "action_id": "unknown",
                "action_type": "UNKNOWN",
                "executor_status": "UNKNOWN",
                "verification_status": ACTION_FAILED,
                "verified": False,
                "trusted": False,
                "reason": "Action must be a mapping.",
            }


        action_id = str(action.get("action_id", "unknown"))
        action_type = str(
            action.get("action_type", "UNKNOWN")
        ).strip().upper()


        executor_status = str(
            action.get("status", action.get("execution_status", "UNKNOWN"))
        ).strip().upper()


        self._action_type_counts[action_type] = (
            self._action_type_counts.get(action_type, 0) + 1
        )


        if executor_status not in KNOWN_ACTION_STATUSES:
            self._stats["actions_failed"] += 1
            self._action_status_counts[ACTION_FAILED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": executor_status,
                "verification_status": ACTION_FAILED,
                "verified": False,
                "trusted": False,
                "reason": "Unknown executor action status.",
            }


        # -------------------------------------------------------------
        # Simulated actions
        # -------------------------------------------------------------
        if executor_status == SIMULATED:
            self._stats["actions_verified"] += 1
            self._action_status_counts[ACTION_VERIFIED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": SIMULATED,
                "verification_status": ACTION_VERIFIED,
                "verified": True,
                "trusted": True,
                "simulation": True,
                "reason": (
                    "Simulation result verified. No claim of real execution "
                    "has been made."
                ),
            }


        # -------------------------------------------------------------
        # Rejected actions
        # -------------------------------------------------------------
        if executor_status == REJECTED:
            self._stats["actions_failed"] += 1
            self._action_status_counts[ACTION_FAILED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": REJECTED,
                "verification_status": ACTION_FAILED,
                "verified": False,
                "trusted": False,
                "reason": (
                    "Rejected executor action cannot be considered verified."
                ),
            }


        # -------------------------------------------------------------
        # Failed actions
        # -------------------------------------------------------------
        if executor_status == FAILED:
            self._stats["actions_failed"] += 1
            self._action_status_counts[ACTION_FAILED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": FAILED,
                "verification_status": ACTION_FAILED,
                "verified": False,
                "trusted": False,
                "reason": (
                    "Failed executor action cannot be considered verified."
                ),
            }


        # -------------------------------------------------------------
        # Skipped actions
        # -------------------------------------------------------------
        if executor_status == SKIPPED:
            self._stats["actions_skipped"] += 1
            self._action_status_counts[ACTION_SKIPPED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": SKIPPED,
                "verification_status": ACTION_SKIPPED,
                "verified": False,
                "trusted": False,
                "reason": "Skipped action was not executed.",
            }


        # -------------------------------------------------------------
        # EXECUTED
        # -------------------------------------------------------------
        hook = self._hooks.get(action_type)


        if hook is None:
            # This is the critical security property.
            # EXECUTED without an independent verifier is NOT trusted.
            self._stats["actions_unsupported"] += 1
            self._action_status_counts[ACTION_UNSUPPORTED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": EXECUTED,
                "verification_status": ACTION_UNSUPPORTED,
                "verified": False,
                "trusted": False,
                "reason": (
                    "Action was reported EXECUTED, but no independent "
                    "verification hook is registered. Execution is therefore "
                    "not trusted as verified state."
                ),
            }


        # -------------------------------------------------------------
        # Registered independent verifier
        # -------------------------------------------------------------
        try:
            hook_result = hook.verifier(
                deepcopy(dict(action)),
                deepcopy(dict(execution_result)),
            )


            if not isinstance(hook_result, Mapping):
                raise TypeError(
                    "Verification hook must return a mapping."
                )


            verified = bool(hook_result.get("verified", False))


            if verified:
                self._stats["actions_verified"] += 1
                self._action_status_counts[ACTION_VERIFIED] += 1


                return {
                    "action_id": action_id,
                    "action_type": action_type,
                    "executor_status": EXECUTED,
                    "verification_status": ACTION_VERIFIED,
                    "verified": True,
                    "trusted": True,
                    "reason": str(
                        hook_result.get(
                            "reason",
                            "Independent verification succeeded.",
                        )
                    ),
                    "evidence": deepcopy(
                        hook_result.get("evidence", {})
                    ),
                }


            self._stats["actions_failed"] += 1
            self._action_status_counts[ACTION_FAILED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": EXECUTED,
                "verification_status": ACTION_FAILED,
                "verified": False,
                "trusted": False,
                "reason": str(
                    hook_result.get(
                        "reason",
                        "Independent verification failed.",
                    )
                ),
                "evidence": deepcopy(
                    hook_result.get("evidence", {})
                ),
            }


        except Exception as exc:
            self._stats["actions_failed"] += 1
            self._action_status_counts[ACTION_FAILED] += 1


            return {
                "action_id": action_id,
                "action_type": action_type,
                "executor_status": EXECUTED,
                "verification_status": ACTION_FAILED,
                "verified": False,
                "trusted": False,
                "reason": f"Verification hook failed: {exc}",
            }


    # ---------------------------------------------------------------------
    # Request result
    # ---------------------------------------------------------------------


    def _build_request_result(
        self,
        *,
        verification_id: str,
        execution_result: Mapping[str, Any],
        action_results: List[Dict[str, Any]],
        source: str,
        started: float,
    ) -> Dict[str, Any]:
        elapsed = self._record_processing(started)


        total = len(action_results)


        verified_count = sum(
            1 for item in action_results
            if item["verification_status"] == ACTION_VERIFIED
        )


        failed_count = sum(
            1 for item in action_results
            if item["verification_status"] == ACTION_FAILED
        )


        skipped_count = sum(
            1 for item in action_results
            if item["verification_status"] == ACTION_SKIPPED
        )


        unsupported_count = sum(
            1 for item in action_results
            if item["verification_status"] == ACTION_UNSUPPORTED
        )


        if verified_count == total:
            status = STATUS_VERIFIED
            trusted = True
            self._stats["verified_requests"] += 1


        elif verified_count > 0 and (
            failed_count > 0
            or skipped_count > 0
            or unsupported_count > 0
        ):
            status = STATUS_PARTIAL
            trusted = False
            self._stats["partial_requests"] += 1


        elif skipped_count == total:
            status = STATUS_SKIPPED
            trusted = False
            self._stats["skipped_requests"] += 1


        else:
            status = STATUS_FAILED
            trusted = False
            self._stats["failed_requests"] += 1


        self._status_counts[status] += 1


        response_id = execution_result.get(
            "response_id",
            "unknown",
        )


        request_id = execution_result.get(
            "request_id",
            "unknown",
        )


        result = {
            "verification_id": verification_id,
            "response_id": response_id,
            "request_id": request_id,
            "timestamp": _utc_now(),
            "status": status,
            "verified": status == STATUS_VERIFIED,
            "trusted": trusted,
            "execution_status": execution_result.get(
                "status",
                "UNKNOWN",
            ),
            "execution_id": execution_result.get(
                "execution_id",
                "unknown",
            ),
            "actions": action_results,
            "actions_total": total,
            "actions_verified": verified_count,
            "actions_failed": failed_count,
            "actions_skipped": skipped_count,
            "actions_unsupported": unsupported_count,
            "processing_time_ms": round(elapsed, 3),
            "within_processing_target": (
                elapsed <= self.processing_target_ms
            ),
            "source": source,
            "audit": self._audit_record(
                verification_id,
                source,
                status,
            ),
            "evidence": {
                "execution_result_fingerprint": _fingerprint(
                    execution_result
                ),
                "verification_result_fingerprint": _fingerprint(
                    action_results
                ),
            },
            "engine_version": ENGINE_VERSION,
            "error": None,
        }


        return result


    # ---------------------------------------------------------------------
    # Empty execution
    # ---------------------------------------------------------------------


    def _verify_empty_execution(
        self,
        verification_id: str,
        execution_result: Mapping[str, Any],
        source: str,
        started: float,
    ) -> Dict[str, Any]:
        """
        Empty execution is considered consistent only when the executor
        explicitly reports that no actions were requested/executed.
        """
        requested = execution_result.get("actions_requested", 0)
        executed = execution_result.get("actions_executed", 0)
        simulated = execution_result.get("actions_simulated", 0)
        rejected = execution_result.get("actions_rejected", 0)
        failed = execution_result.get("actions_failed", 0)


        if all(
            int(value or 0) == 0
            for value in (
                requested,
                executed,
                simulated,
                rejected,
                failed,
            )
        ):
            elapsed = self._record_processing(started)


            self._stats["verified_requests"] += 1
            self._status_counts[STATUS_VERIFIED] += 1


            return {
                "verification_id": verification_id,
                "response_id": execution_result.get(
                    "response_id",
                    "unknown",
                ),
                "request_id": execution_result.get(
                    "request_id",
                    "unknown",
                ),
                "timestamp": _utc_now(),
                "status": STATUS_VERIFIED,
                "verified": True,
                "trusted": True,
                "execution_status": execution_result.get(
                    "status",
                    "UNKNOWN",
                ),
                "actions": [],
                "actions_total": 0,
                "actions_verified": 0,
                "actions_failed": 0,
                "actions_skipped": 0,
                "actions_unsupported": 0,
                "processing_time_ms": round(elapsed, 3),
                "within_processing_target": (
                    elapsed <= self.processing_target_ms
                ),
                "source": source,
                "audit": self._audit_record(
                    verification_id,
                    source,
                    STATUS_VERIFIED,
                ),
                "evidence": {
                    "reason": (
                        "Execution result explicitly reports zero "
                        "requested and completed actions."
                    )
                },
                "engine_version": ENGINE_VERSION,
                "error": None,
            }


        return self._reject(
            verification_id,
            source,
            "Empty action list is inconsistent with execution counters.",
            started,
        )


    # ---------------------------------------------------------------------
    # Rejection
    # ---------------------------------------------------------------------


    def _reject(
        self,
        verification_id: str,
        source: str,
        reason: str,
        started: float,
    ) -> Dict[str, Any]:
        elapsed = self._record_processing(started)


        self._stats["rejected_requests"] += 1
        self._status_counts[STATUS_REJECTED] += 1


        return {
            "verification_id": verification_id,
            "timestamp": _utc_now(),
            "status": STATUS_REJECTED,
            "verified": False,
            "trusted": False,
            "source": source,
            "actions": [],
            "actions_total": 0,
            "actions_verified": 0,
            "actions_failed": 0,
            "actions_skipped": 0,
            "actions_unsupported": 0,
            "processing_time_ms": round(elapsed, 3),
            "within_processing_target": (
                elapsed <= self.processing_target_ms
            ),
            "audit": self._audit_record(
                verification_id,
                source,
                STATUS_REJECTED,
            ),
            "engine_version": ENGINE_VERSION,
            "error": reason,
        }


    # ---------------------------------------------------------------------
    # Audit
    # ---------------------------------------------------------------------


    def _audit_record(
        self,
        verification_id: str,
        source: str,
        status: str,
    ) -> Dict[str, Any]:
        if not self.audit_enabled:
            return {
                "enabled": False,
                "recorded": False,
            }


        # Local audit envelope only. No external write is performed.
        return {
            "enabled": True,
            "recorded": False,
            "mode": "LOCAL_ENVELOPE",
            "verification_id": verification_id,
            "source": source,
            "status": status,
        }


    # ---------------------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------------------


    def _record_processing(self, started: float) -> float:
        elapsed = (time.perf_counter() - started) * 1000.0
        self._processing_samples.append(elapsed)


        if len(self._processing_samples) > 1000:
            self._processing_samples.pop(0)


        return elapsed


    def _statistics(self) -> Dict[str, Any]:
        total = self._stats["total_requests"]
        successful = self._stats["verified_requests"]


        success_rate = (
            (successful / total) * 100.0
            if total
            else 0.0
        )


        return {
            **self._stats,
            "verification_success_rate": round(
                success_rate,
                3,
            ),
        }


    # ---------------------------------------------------------------------
    # Public self-test
    # ---------------------------------------------------------------------


    def self_test(self) -> Dict[str, Any]:
        checks: Dict[str, bool] = {}


        health = self.health_check()


        checks["engine_healthy"] = bool(
            health.get("healthy") is True
        )


        checks["verification_available"] = bool(
            health.get("verification", {}).get("available") is True
        )


        checks["read_only_safety"] = bool(
            health.get("safety", {}).get(
                "executes_security_actions"
            ) is False
            and health.get("safety", {}).get(
                "shell_execution"
            ) is False
            and health.get("safety", {}).get(
                "network_operations"
            ) is False
            and health.get("safety", {}).get(
                "process_operations"
            ) is False
            and health.get("safety", {}).get(
                "account_modification"
            ) is False
        )


        # -------------------------------------------------------------
        # 1. Simulated action
        # -------------------------------------------------------------
        simulated_result = self.verify(
            {
                "execution_id": "EX-SELFTEST-SIMULATED",
                "response_id": "ER-SELFTEST-SIMULATED",
                "request_id": "EG-SELFTEST-SIMULATED",
                "status": "SUCCESS",
                "actions_requested": 1,
                "actions_executed": 0,
                "actions_simulated": 1,
                "actions_rejected": 0,
                "actions_failed": 0,
                "actions": [
                    {
                        "action_id": "EA-SELFTEST-SIMULATED",
                        "action_type": "CREATE_ALERT",
                        "status": SIMULATED,
                        "simulated": True,
                        "result": {
                            "success": True,
                            "simulated": True,
                            "executed": False,
                        },
                    }
                ],
            },
            source="self-test-simulated",
        )


        checks["simulated_action_verified"] = bool(
            simulated_result.get("verified") is True
            and simulated_result.get("trusted") is True
        )


        simulated_action = simulated_result.get(
            "actions",
            [{}],
        )[0]


        checks["simulated_action_is_not_claimed_executed"] = bool(
            simulated_action.get("executor_status") == SIMULATED
            and simulated_action.get("verified") is True
            and simulated_action.get("simulation") is True
        )


        # -------------------------------------------------------------
        # 2. Rejected action
        # -------------------------------------------------------------
        rejected_result = self.verify(
            {
                "execution_id": "EX-SELFTEST-REJECTED",
                "response_id": "ER-SELFTEST-REJECTED",
                "request_id": "EG-SELFTEST-REJECTED",
                "status": "PARTIAL",
                "actions_requested": 1,
                "actions_executed": 0,
                "actions_simulated": 0,
                "actions_rejected": 1,
                "actions_failed": 0,
                "actions": [
                    {
                        "action_id": "EA-SELFTEST-REJECTED",
                        "action_type": "ISOLATE",
                        "status": REJECTED,
                        "error": "Safety policy.",
                    }
                ],
            },
            source="self-test-rejected",
        )


        rejected_action = rejected_result.get(
            "actions",
            [{}],
        )[0]


        checks["rejected_action_not_verified"] = bool(
            rejected_action.get("verified") is False
            and rejected_action.get("trusted") is False
        )


        checks["rejected_action_detected"] = bool(
            rejected_action.get("verification_status")
            == ACTION_FAILED
        )


        # -------------------------------------------------------------
        # 3. EXECUTED without verifier
        #
        # This is the critical regression test that previously failed.
        # -------------------------------------------------------------
        executed_result = self.verify(
            {
                "execution_id": "EX-SELFTEST-EXECUTED",
                "response_id": "ER-SELFTEST-EXECUTED",
                "request_id": "EG-SELFTEST-EXECUTED",
                "status": "SUCCESS",
                "actions_requested": 1,
                "actions_executed": 1,
                "actions_simulated": 0,
                "actions_rejected": 0,
                "actions_failed": 0,
                "actions": [
                    {
                        "action_id": "EA-SELFTEST-EXECUTED",
                        "action_type": "ISOLATE",
                        "status": EXECUTED,
                        "simulated": False,
                    }
                ],
            },
            source="self-test-executed",
        )


        executed_action = executed_result.get(
            "actions",
            [{}],
        )[0]


        # EXECUTED must NOT become VERIFIED without a verifier.
        checks["executed_without_verifier_not_trusted"] = bool(
            executed_result.get("trusted") is False
            and executed_result.get("verified") is False
            and executed_action.get(
                "verification_status"
            ) == ACTION_UNSUPPORTED
            and executed_action.get("verified") is False
        )


        # -------------------------------------------------------------
        # 4. Invalid input
        # -------------------------------------------------------------
        invalid_result = self.verify(
            {},
            source="self-test-invalid",
        )


        checks["invalid_input_rejected"] = bool(
            invalid_result.get("status") == STATUS_REJECTED
            and invalid_result.get("verified") is False
        )


        # -------------------------------------------------------------
        # 5. Empty execution consistency
        # -------------------------------------------------------------
        empty_result = self.verify(
            {
                "execution_id": "EX-SELFTEST-EMPTY",
                "response_id": "ER-SELFTEST-EMPTY",
                "request_id": "EG-SELFTEST-EMPTY",
                "status": "SUCCESS",
                "actions_requested": 0,
                "actions_executed": 0,
                "actions_simulated": 0,
                "actions_rejected": 0,
                "actions_failed": 0,
                "actions": [],
            },
            source="self-test-empty",
        )


        checks["empty_execution_consistent"] = bool(
            empty_result.get("status") == STATUS_VERIFIED
            and empty_result.get("verified") is True
            and empty_result.get("trusted") is True
        )


        # -------------------------------------------------------------
        # Final result
        # -------------------------------------------------------------
        passed_count = sum(
            1 for value in checks.values()
            if value
        )


        total_checks = len(checks)
        passed = passed_count == total_checks


        return {
            "passed": passed,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "checks": checks,
            "passed_count": passed_count,
            "total_checks": total_checks,
            "statistics": self._statistics(),
        }




# ============================================================================
# Factory
# ============================================================================


def create_verification_engine(
    **kwargs: Any,
) -> ResponseVerificationEngine:
    return ResponseVerificationEngine(**kwargs)




# ============================================================================
# Integration self-test
# ============================================================================


def _self_test() -> None:
    engine = create_verification_engine()


    print()
    print("=" * 78)
    print("EnterpriseGuard Response Verification Engine - Integration Self Test")
    print("=" * 78)
    print()


    print("[1] Verification engine status")
    print(json.dumps(
        engine.status(),
        indent=4,
        ensure_ascii=False,
    ))
    print()


    print("[2] Health check")
    health = engine.health_check()


    print(json.dumps(
        health,
        indent=4,
        ensure_ascii=False,
    ))
    print()


    print("[3] Verification self test")


    result = engine.self_test()


    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False,
    ))
    print()


    if not result["passed"]:
        failed = [
            name
            for name, value in result["checks"].items()
            if not value
        ]


        raise RuntimeError(
            "EnterpriseGuard Response Verification Engine "
            f"self-test failed. Failed checks: {', '.join(failed)}"
        )


    print("=" * 78)
    print("Response Verification Engine self test completed successfully")
    print("=" * 78)
    print()




if __name__ == "__main__":
    _self_test()