"""
EnterpriseGuard - Response Engine
=================================


Central response-planning layer for the EnterpriseGuard security platform.


Architecture
------------


    Security Event
          |
          v
    Intelligence Engine
          |
          |  DetectionResult / EngineResult
          v
    Response Engine
          |
          +--> Policy Validation
          |
          +--> Risk / Severity Evaluation
          |
          +--> Response Decision
          |
          +--> Response Plan
          |
          +--> Approval / Execution Policy
          |
          +--> Audit
          |
          v
    Future Response Executor
          |
          +--> Alerting
          +--> Containment
          +--> Isolation
          +--> Endpoint Response
          +--> Network Response




Design principles
-----------------


- The Response Engine does NOT detect threats.
- The Response Engine does NOT train ML models.
- The Response Engine does NOT execute destructive security actions.
- Intelligence remains responsible for detection and risk assessment.
- Response policy remains deterministic and auditable.
- Response planning is separated from response execution.
- Automatic execution is disabled by default.
- DRY_RUN is the default execution mode.
- Every response receives a unique response ID.
- Every response maintains the originating request/correlation ID.
- Invalid or incomplete intelligence results are rejected safely.
- Unknown threat types never trigger destructive actions.
- Unknown severities never escalate automatically.
- Critical responses require explicit policy authorization.
- Audit integration is optional and dependency-light.
- Operational statistics are separated from security/model accuracy.
- The engine is designed for future response executors.
- Internal implementation errors never leak implementation details.




Security posture
---------------


This component produces structured response intent.


It does not:


- kill processes
- disable accounts
- modify firewall rules
- terminate network connections
- isolate hosts
- delete files
- modify registry settings
- execute shell commands
- execute PowerShell commands
- contact external systems automatically


Actual security actions must be implemented by dedicated executor
subsystems with their own authorization, validation, logging and
rollback controls.
"""


from __future__ import annotations


import hashlib
import json
import logging
import math
import time
import uuid


from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence




logger = logging.getLogger(__name__)




# ============================================================================
# ENUMS
# ============================================================================




class ResponseStatus(str, Enum):
    """Final status of a response-engine request."""


    PLANNED = "PLANNED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"




class ResponseLevel(str, Enum):
    """Response intensity requested by the intelligence layer."""


    NONE = "NONE"
    MONITOR = "MONITOR"
    ALERT = "ALERT"
    CONTAIN = "CONTAIN"
    ISOLATE = "ISOLATE"




class ExecutionMode(str, Enum):
    """
    How the response plan is intended to be handled.


    DRY_RUN:
        Plan generated but never executed.


    DEFERRED:
        Plan generated for a future executor.


    MANUAL_APPROVAL:
        Human approval is required before execution.


    AUTOMATIC:
        Reserved for future explicitly authorized automation.
    """


    DRY_RUN = "DRY_RUN"
    DEFERRED = "DEFERRED"
    MANUAL_APPROVAL = "MANUAL_APPROVAL"
    AUTOMATIC = "AUTOMATIC"




class ActionType(str, Enum):
    """Supported response intents."""


    NONE = "NONE"
    MONITOR = "MONITOR"
    CREATE_ALERT = "CREATE_ALERT"
    ESCALATE = "ESCALATE"
    CONTAIN = "CONTAIN"
    ISOLATE = "ISOLATE"




class ApprovalLevel(str, Enum):
    """Required authorization level for a response."""


    NONE = "NONE"
    OPERATOR = "OPERATOR"
    SECURITY_ANALYST = "SECURITY_ANALYST"
    SECURITY_ADMIN = "SECURITY_ADMIN"




class ThreatSeverity(str, Enum):
    """
    Canonical severity values.


    Kept locally so the Response Engine does not depend on the detector
    implementation and remains usable with serialized intelligence results.
    """


    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"




# ============================================================================
# CONFIGURATION
# ============================================================================




@dataclass(frozen=True)
class ResponseEngineConfig:
    """
    Central Response Engine configuration.


    The defaults intentionally favor safety, observability and human control.
    """


    engine_version: str = "1.0.0"


    enabled: bool = True


    # Safety first: planning only.
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN


    # Actual automatic execution is prohibited by default.
    automatic_execution_enabled: bool = False


    # Critical actions require approval.
    critical_requires_approval: bool = True


    high_requires_approval: bool = True


    # Unknown inputs are handled conservatively.
    reject_unknown_severity: bool = True


    reject_unknown_response_level: bool = True


    # Event/plan bounds.
    max_input_size: int = 1_000_000


    max_actions_per_plan: int = 16


    max_metadata_items: int = 64


    # Response planning target.
    processing_target_ms: float = 25.0


    # Audit.
    audit_enabled: bool = True


    # Future compatibility.
    allow_future_response_levels: bool = False




# ============================================================================
# RESPONSE POLICY
# ============================================================================




@dataclass(frozen=True)
class ResponsePolicy:
    """
    Deterministic policy used to translate intelligence into response intent.


    The policy does not execute anything.
    """


    low_level: ResponseLevel = ResponseLevel.MONITOR


    medium_level: ResponseLevel = ResponseLevel.ALERT


    high_level: ResponseLevel = ResponseLevel.CONTAIN


    critical_level: ResponseLevel = ResponseLevel.ISOLATE


    low_approval: ApprovalLevel = ApprovalLevel.NONE


    medium_approval: ApprovalLevel = ApprovalLevel.OPERATOR


    high_approval: ApprovalLevel = ApprovalLevel.SECURITY_ANALYST


    critical_approval: ApprovalLevel = ApprovalLevel.SECURITY_ADMIN




# ============================================================================
# RESPONSE ACTION
# ============================================================================




@dataclass
class ResponseAction:
    """
    One planned response action.


    This is intent only.


    An executor may later interpret:


        ISOLATE -> host isolation
        CREATE_ALERT -> alert subsystem
        ESCALATE -> SOC escalation
        CONTAIN -> containment subsystem


    The Response Engine itself does not perform those operations.
    """


    action_id: str


    action_type: str


    priority: int


    description: str


    requires_approval: bool


    approval_level: str


    executable: bool = False


    execution_status: str = "NOT_EXECUTED"


    parameters: Dict[str, Any] = field(default_factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary."""


        return asdict(self)




# ============================================================================
# RESPONSE PLAN
# ============================================================================




@dataclass
class ResponsePlan:
    """
    Complete response plan generated by the Response Engine.
    """


    response_id: str


    request_id: str


    timestamp: str


    status: str


    response_level: str


    execution_mode: str


    threat_detected: bool


    threat_type: str


    severity: str


    risk_score: float


    confidence: float


    recommended_action: str


    approval_required: bool


    approval_level: str


    actions: List[ResponseAction] = field(default_factory=list)


    rationale: List[str] = field(default_factory=list)


    metadata: Dict[str, Any] = field(default_factory=dict)


    audit: Dict[str, Any] = field(default_factory=dict)


    engine_version: str = "1.0.0"


    error: Optional[str] = None


    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary."""


        return asdict(self)




# ============================================================================
# RESPONSE RESULT
# ============================================================================




@dataclass
class ResponseResult:
    """
    Public result returned by the Response Engine.


    ``plan`` contains the structured response intent.
    """


    response_id: str


    request_id: str


    timestamp: str


    status: str


    execution_mode: str


    plan: Dict[str, Any] = field(default_factory=dict)


    audit: Dict[str, Any] = field(default_factory=dict)


    metadata: Dict[str, Any] = field(default_factory=dict)


    engine_version: str = "1.0.0"


    error: Optional[str] = None


    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary."""


        return asdict(self)




# ============================================================================
# RESPONSE ENGINE
# ============================================================================




class ResponseEngine:
    """
    EnterpriseGuard Response Engine.


    Responsibilities
    ----------------


    1. Accept intelligence decisions.
    2. Validate intelligence input.
    3. Normalize response information.
    4. Apply deterministic response policy.
    5. Build a structured response plan.
    6. Determine approval requirements.
    7. Prepare future executor intent.
    8. Record audit information.
    9. Maintain operational telemetry.
    10. Support batch response planning.
    11. Expose status and health information.


    The engine intentionally does NOT:


    - detect threats
    - train ML models
    - execute isolation
    - execute containment
    - kill processes
    - modify firewalls
    - disable accounts
    - delete files
    - execute operating-system commands
    """


    VERSION = "1.0.0"


    def __init__(
        self,
        *,
        config: Optional[ResponseEngineConfig] = None,
        policy: Optional[ResponsePolicy] = None,
        audit_logger: Optional[Any] = None,
    ) -> None:


        self.config = config or ResponseEngineConfig()


        self.policy = policy or ResponsePolicy()


        self.audit_logger = audit_logger


        self._lock = RLock()


        # ------------------------------------------------------------------
        # Operational counters
        # ------------------------------------------------------------------


        self.total_requests = 0


        self.planned_requests = 0


        self.rejected_requests = 0


        self.failed_requests = 0


        self.approval_required_count = 0


        self.monitor_actions = 0


        self.alert_actions = 0


        self.contain_actions = 0


        self.isolate_actions = 0


        # ------------------------------------------------------------------
        # Timing telemetry
        # ------------------------------------------------------------------


        self.total_processing_ms = 0.0


        self.max_processing_ms = 0.0


        # ------------------------------------------------------------------
        # Classification telemetry
        # ------------------------------------------------------------------


        self.severity_counts: Dict[str, int] = {
            ThreatSeverity.LOW.value: 0,
            ThreatSeverity.MEDIUM.value: 0,
            ThreatSeverity.HIGH.value: 0,
            ThreatSeverity.CRITICAL.value: 0,
        }


        self.response_level_counts: Dict[str, int] = {
            ResponseLevel.NONE.value: 0,
            ResponseLevel.MONITOR.value: 0,
            ResponseLevel.ALERT.value: 0,
            ResponseLevel.CONTAIN.value: 0,
            ResponseLevel.ISOLATE.value: 0,
        }


        self.status_counts: Dict[str, int] = {
            ResponseStatus.PLANNED.value: 0,
            ResponseStatus.REJECTED.value: 0,
            ResponseStatus.FAILED.value: 0,
        }


        self.threat_type_counts: Dict[str, int] = {}


        logger.info(
            "EnterpriseGuard Response Engine initialized | "
            "version=%s | enabled=%s | execution_mode=%s",
            self.VERSION,
            self.config.enabled,
            self.config.execution_mode.value,
        )


    # ========================================================================
    # PUBLIC PROCESSING API
    # ========================================================================


    def process(
        self,
        intelligence_result: Any,
        *,
        request_id: Optional[str] = None,
        source: str = "intelligence",
    ) -> ResponseResult:
        """
        Process one intelligence result.


        Accepted input:


        - EngineResult-like object exposing ``to_dict()``
        - mapping/dictionary
        - serialized dictionary containing the standard Intelligence Engine
          fields


        The method never executes security actions.
        """


        started = time.perf_counter()


        with self._lock:
            self.total_requests += 1


        normalized_source = self._normalize_source(source)


        try:


            # --------------------------------------------------------------
            # 1. Engine availability
            # --------------------------------------------------------------


            if not self.config.enabled:
                response_id = self._generate_response_id(
                    request_id=request_id
                )


                result = self._build_rejected_result(
                    response_id=response_id,
                    request_id=request_id or "UNKNOWN",
                    started=started,
                    reason="Response engine is disabled.",
                    source=normalized_source,
                )


                self._record_rejected(result)


                return result


            # --------------------------------------------------------------
            # 2. Normalize incoming intelligence result
            # --------------------------------------------------------------


            normalized = self._normalize_intelligence_result(
                intelligence_result
            )


            if normalized is None:
                response_id = self._generate_response_id(
                    request_id=request_id
                )


                result = self._build_rejected_result(
                    response_id=response_id,
                    request_id=request_id or "UNKNOWN",
                    started=started,
                    reason="Invalid intelligence result.",
                    source=normalized_source,
                )


                self._record_rejected(result)


                return result


            # --------------------------------------------------------------
            # 3. Resolve request ID
            # --------------------------------------------------------------


            resolved_request_id = self._extract_request_id(
                normalized,
                request_id,
            )


            response_id = self._generate_response_id(
                request_id=resolved_request_id
            )


            # --------------------------------------------------------------
            # 4. Validate intelligence decision
            # --------------------------------------------------------------


            validation_error = self._validate_intelligence_result(
                normalized
            )


            if validation_error:
                result = self._build_rejected_result(
                    response_id=response_id,
                    request_id=resolved_request_id,
                    started=started,
                    reason=validation_error,
                    source=normalized_source,
                )


                self._record_rejected(result)


                return result


            # --------------------------------------------------------------
            # 5. Extract decision fields
            # --------------------------------------------------------------


            threat_detected = bool(
                normalized.get(
                    "threat_detected",
                    False,
                )
            )


            threat_type = self._normalize_text(
                normalized.get(
                    "threat_type",
                    "UNKNOWN",
                ),
                default="UNKNOWN",
                maximum=128,
            )


            severity = self._normalize_severity(
                normalized.get(
                    "severity",
                    ThreatSeverity.LOW.value,
                )
            )


            risk_score = self._safe_score(
                normalized.get(
                    "risk_score",
                    0.0,
                )
            )


            confidence = self._safe_score(
                normalized.get(
                    "confidence",
                    0.0,
                )
            )


            recommended_action = self._normalize_text(
                normalized.get(
                    "recommended_action",
                    "MONITOR",
                ),
                default="MONITOR",
                maximum=128,
            )


            requested_response_level = (
                self._normalize_response_level(
                    normalized.get(
                        "response_level",
                        ResponseLevel.NONE.value,
                    )
                )
            )


            # --------------------------------------------------------------
            # 6. Calculate response decision
            # --------------------------------------------------------------


            response_level = self._determine_response_level(
                threat_detected=threat_detected,
                severity=severity,
                risk_score=risk_score,
                requested_level=requested_response_level,
            )


            # --------------------------------------------------------------
            # 7. Determine approval
            # --------------------------------------------------------------


            approval_level = self._determine_approval_level(
                severity=severity,
                response_level=response_level,
            )


            approval_required = (
                approval_level != ApprovalLevel.NONE
            )


            # --------------------------------------------------------------
            # 8. Build response actions
            # --------------------------------------------------------------


            actions = self._build_actions(
                threat_detected=threat_detected,
                threat_type=threat_type,
                severity=severity,
                response_level=response_level,
                recommended_action=recommended_action,
                approval_required=approval_required,
                approval_level=approval_level,
            )


            # --------------------------------------------------------------
            # 9. Enforce action limit
            # --------------------------------------------------------------


            if len(actions) > self.config.max_actions_per_plan:
                result = self._build_rejected_result(
                    response_id=response_id,
                    request_id=resolved_request_id,
                    started=started,
                    reason="Response plan exceeds action limit.",
                    source=normalized_source,
                )


                self._record_rejected(result)


                return result


            # --------------------------------------------------------------
            # 10. Build rationale
            # --------------------------------------------------------------


            rationale = self._build_rationale(
                threat_detected=threat_detected,
                threat_type=threat_type,
                severity=severity,
                risk_score=risk_score,
                confidence=confidence,
                response_level=response_level,
                approval_required=approval_required,
            )


            # --------------------------------------------------------------
            # 11. Determine execution mode
            # --------------------------------------------------------------


            execution_mode = self._determine_execution_mode(
                response_level=response_level,
                approval_required=approval_required,
            )


            # --------------------------------------------------------------
            # 12. Audit
            # --------------------------------------------------------------


            audit_result = self._audit_response(
                response_id=response_id,
                request_id=resolved_request_id,
                source=normalized_source,
                threat_detected=threat_detected,
                threat_type=threat_type,
                severity=severity,
                risk_score=risk_score,
                confidence=confidence,
                response_level=response_level,
                execution_mode=execution_mode,
                approval_required=approval_required,
            )


            # --------------------------------------------------------------
            # 13. Timing
            # --------------------------------------------------------------


            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0


            within_target = (
                elapsed_ms
                <= self.config.processing_target_ms
            )


            # --------------------------------------------------------------
            # 14. Build plan
            # --------------------------------------------------------------


            plan = ResponsePlan(
                response_id=response_id,
                request_id=resolved_request_id,
                timestamp=self._utc_now(),
                status=ResponseStatus.PLANNED.value,
                response_level=response_level.value,
                execution_mode=execution_mode.value,
                threat_detected=threat_detected,
                threat_type=threat_type,
                severity=severity.value,
                risk_score=risk_score,
                confidence=confidence,
                recommended_action=recommended_action,
                approval_required=approval_required,
                approval_level=approval_level.value,
                actions=actions,
                rationale=rationale,
                metadata={
                    "source": normalized_source,
                    "processing_target_ms": (
                        self.config.processing_target_ms
                    ),
                    "within_processing_target": (
                        within_target
                    ),
                    "automatic_execution_enabled": (
                        self.config.automatic_execution_enabled
                    ),
                    "executor_attached": False,
                    "execution_note": (
                        "No response executor is attached. "
                        "This engine only creates response intent."
                    ),
                },
                audit=audit_result,
                engine_version=self.VERSION,
            )


            result = ResponseResult(
                response_id=response_id,
                request_id=resolved_request_id,
                timestamp=self._utc_now(),
                status=ResponseStatus.PLANNED.value,
                execution_mode=execution_mode.value,
                plan=plan.to_dict(),
                audit=audit_result,
                metadata={
                    "source": normalized_source,
                    "action_count": len(actions),
                    "approval_required": approval_required,
                    "within_processing_target": (
                        within_target
                    ),
                },
                engine_version=self.VERSION,
            )


            self._record_planned(
                result=result,
                severity=severity,
                response_level=response_level,
                threat_type=threat_type,
                approval_required=approval_required,
            )


            return result


        except Exception:


            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0


            logger.exception(
                "Response engine processing failed | request_id=%s",
                request_id,
            )


            response_id = self._generate_response_id(
                request_id=request_id
            )


            result = ResponseResult(
                response_id=response_id,
                request_id=request_id or "UNKNOWN",
                timestamp=self._utc_now(),
                status=ResponseStatus.FAILED.value,
                execution_mode=(
                    ExecutionMode.DRY_RUN.value
                ),
                plan={},
                audit={},
                metadata={
                    "source": normalized_source,
                    "processing_time_ms": round(
                        elapsed_ms,
                        3,
                    ),
                },
                engine_version=self.VERSION,
                error="Internal response processing error.",
            )


            self._record_failed(result)


            return result


    # ========================================================================
    # COMPATIBILITY API
    # ========================================================================


    def process_intelligence_result(
        self,
        intelligence_result: Any,
        *,
        request_id: Optional[str] = None,
        source: str = "intelligence",
    ) -> ResponseResult:
        """
        Explicit alias for integrations that prefer semantic naming.
        """


        return self.process(
            intelligence_result,
            request_id=request_id,
            source=source,
        )


    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================


    def process_batch(
        self,
        intelligence_results: Sequence[Any],
        *,
        source: str = "batch",
    ) -> Dict[str, Any]:
        """
        Process a bounded collection of intelligence results.


        No response action is executed.
        """


        started = time.perf_counter()


        if not isinstance(
            intelligence_results,
            Sequence,
        ):
            return {
                "success": False,
                "processed": 0,
                "planned": 0,
                "rejected": 0,
                "failed": 0,
                "approval_required": 0,
                "processing_time_ms": 0.0,
                "results": [],
                "error": "Results must be a sequence.",
            }


        if isinstance(
            intelligence_results,
            (str, bytes),
        ):
            return {
                "success": False,
                "processed": 0,
                "planned": 0,
                "rejected": 0,
                "failed": 0,
                "approval_required": 0,
                "processing_time_ms": 0.0,
                "results": [],
                "error": (
                    "Results must be a collection of "
                    "intelligence decisions."
                ),
            }


        if len(intelligence_results) > 10_000:
            return {
                "success": False,
                "processed": 0,
                "planned": 0,
                "rejected": 0,
                "failed": 0,
                "approval_required": 0,
                "processing_time_ms": 0.0,
                "results": [],
                "error": (
                    "Batch exceeds the maximum supported size."
                ),
            }


        results: List[ResponseResult] = []


        for item in intelligence_results:
            results.append(
                self.process(
                    item,
                    source=source,
                )
            )


        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000.0


        planned = [
            result
            for result in results
            if result.status
            == ResponseStatus.PLANNED.value
        ]


        rejected = [
            result
            for result in results
            if result.status
            == ResponseStatus.REJECTED.value
        ]


        failed = [
            result
            for result in results
            if result.status
            == ResponseStatus.FAILED.value
        ]


        approval_required = [
            result
            for result in planned
            if bool(
                result.plan.get(
                    "approval_required",
                    False,
                )
            )
        ]


        return {
            "success": True,
            "processed": len(results),
            "planned": len(planned),
            "rejected": len(rejected),
            "failed": len(failed),
            "approval_required": len(
                approval_required
            ),
            "processing_time_ms": round(
                elapsed_ms,
                3,
            ),
            "results": [
                result.to_dict()
                for result in results
            ],
        }


    # ========================================================================
    # RESPONSE LEVEL
    # ========================================================================


    def _determine_response_level(
        self,
        *,
        threat_detected: bool,
        severity: ThreatSeverity,
        risk_score: float,
        requested_level: ResponseLevel,
    ) -> ResponseLevel:
        """
        Determine final response level.


        Safety rule:


        The engine never escalates an unknown or unsafe request merely
        because a caller requested a stronger action.


        The deterministic policy remains authoritative.
        """


        if not threat_detected:
            return ResponseLevel.NONE


        policy_level = {
            ThreatSeverity.LOW: self.policy.low_level,
            ThreatSeverity.MEDIUM: self.policy.medium_level,
            ThreatSeverity.HIGH: self.policy.high_level,
            ThreatSeverity.CRITICAL: self.policy.critical_level,
        }[severity]


        # --------------------------------------------------------------
        # Policy is authoritative.
        # --------------------------------------------------------------


        selected = policy_level


        # --------------------------------------------------------------
        # Risk-based minimum escalation.
        #
        # This is intentionally conservative.
        # --------------------------------------------------------------


        if risk_score >= 95.0:
            if severity == ThreatSeverity.CRITICAL:
                selected = self._max_response_level(
                    selected,
                    ResponseLevel.ISOLATE,
                )


        elif risk_score >= 85.0:
            if severity in (
                ThreatSeverity.HIGH,
                ThreatSeverity.CRITICAL,
            ):
                selected = self._max_response_level(
                    selected,
                    ResponseLevel.CONTAIN,
                )


        elif risk_score >= 70.0:
            if severity in (
                ThreatSeverity.MEDIUM,
                ThreatSeverity.HIGH,
                ThreatSeverity.CRITICAL,
            ):
                selected = self._max_response_level(
                    selected,
                    ResponseLevel.ALERT,
                )


        # --------------------------------------------------------------
        # A caller cannot silently downgrade a policy-mandated response.
        # --------------------------------------------------------------


        if requested_level != ResponseLevel.NONE:
            selected = self._max_response_level(
                selected,
                requested_level,
            )


        return selected


    @staticmethod
    def _max_response_level(
        first: ResponseLevel,
        second: ResponseLevel,
    ) -> ResponseLevel:
        """Return the stronger of two response levels."""


        priority = {
            ResponseLevel.NONE: 0,
            ResponseLevel.MONITOR: 1,
            ResponseLevel.ALERT: 2,
            ResponseLevel.CONTAIN: 3,
            ResponseLevel.ISOLATE: 4,
        }


        return (
            first
            if priority[first] >= priority[second]
            else second
        )


    # ========================================================================
    # APPROVAL
    # ========================================================================


    def _determine_approval_level(
        self,
        *,
        severity: ThreatSeverity,
        response_level: ResponseLevel,
    ) -> ApprovalLevel:
        """Determine authorization required for the planned response."""


        if response_level in (
            ResponseLevel.NONE,
            ResponseLevel.MONITOR,
        ):
            return ApprovalLevel.NONE


        if severity == ThreatSeverity.CRITICAL:
            if self.config.critical_requires_approval:
                return self.policy.critical_approval


        if severity == ThreatSeverity.HIGH:
            if self.config.high_requires_approval:
                return self.policy.high_approval


        if severity == ThreatSeverity.MEDIUM:
            return self.policy.medium_approval


        return ApprovalLevel.NONE


    # ========================================================================
    # EXECUTION MODE
    # ========================================================================


    def _determine_execution_mode(
        self,
        *,
        response_level: ResponseLevel,
        approval_required: bool,
    ) -> ExecutionMode:
        """
        Determine how the plan should be consumed.


        Automatic execution can never be enabled merely by a caller
        requesting it.
        """


        if response_level == ResponseLevel.NONE:
            return ExecutionMode.DRY_RUN


        if not self.config.automatic_execution_enabled:
            if approval_required:
                return ExecutionMode.MANUAL_APPROVAL


            return self.config.execution_mode


        if approval_required:
            return ExecutionMode.MANUAL_APPROVAL


        # Even when the configuration requests automatic execution,
        # the current engine still produces a plan only.
        #
        # This deliberate restriction prevents accidental destructive
        # behavior before a dedicated executor and authorization layer
        # exist.
        return ExecutionMode.DEFERRED


    # ========================================================================
    # ACTION GENERATION
    # ========================================================================


    def _build_actions(
        self,
        *,
        threat_detected: bool,
        threat_type: str,
        severity: ThreatSeverity,
        response_level: ResponseLevel,
        recommended_action: str,
        approval_required: bool,
        approval_level: ApprovalLevel,
    ) -> List[ResponseAction]:
        """
        Build deterministic response actions.


        Actions are plans, not executions.
        """


        if not threat_detected:
            return [
                self._create_action(
                    action_type=ActionType.NONE,
                    priority=100,
                    description=(
                        "No threat detected; no security "
                        "response is required."
                    ),
                    requires_approval=False,
                    approval_level=ApprovalLevel.NONE,
                    parameters={
                        "reason": "NO_THREAT_DETECTED",
                    },
                )
            ]


        actions: List[ResponseAction] = []


        if response_level == ResponseLevel.MONITOR:


            actions.append(
                self._create_action(
                    action_type=ActionType.MONITOR,
                    priority=80,
                    description=(
                        "Continue monitoring the affected "
                        "security context."
                    ),
                    requires_approval=False,
                    approval_level=ApprovalLevel.NONE,
                    parameters={
                        "threat_type": threat_type,
                        "severity": severity.value,
                    },
                )
            )


        elif response_level == ResponseLevel.ALERT:


            actions.append(
                self._create_action(
                    action_type=ActionType.CREATE_ALERT,
                    priority=70,
                    description=(
                        "Create a security alert for "
                        "analyst review."
                    ),
                    requires_approval=False,
                    approval_level=ApprovalLevel.NONE,
                    parameters={
                        "threat_type": threat_type,
                        "severity": severity.value,
                    },
                )
            )


            actions.append(
                self._create_action(
                    action_type=ActionType.ESCALATE,
                    priority=60,
                    description=(
                        "Escalate the security event to "
                        "the designated monitoring workflow."
                    ),
                    requires_approval=approval_required,
                    approval_level=approval_level,
                    parameters={
                        "recommended_action": (
                            recommended_action
                        ),
                    },
                )
            )


        elif response_level == ResponseLevel.CONTAIN:


            actions.append(
                self._create_action(
                    action_type=ActionType.CREATE_ALERT,
                    priority=50,
                    description=(
                        "Create a high-priority security alert "
                        "before containment."
                    ),
                    requires_approval=False,
                    approval_level=ApprovalLevel.NONE,
                    parameters={
                        "threat_type": threat_type,
                        "severity": severity.value,
                    },
                )
            )


            actions.append(
                self._create_action(
                    action_type=ActionType.CONTAIN,
                    priority=30,
                    description=(
                        "Prepare containment of the affected "
                        "security context."
                    ),
                    requires_approval=approval_required,
                    approval_level=approval_level,
                    parameters={
                        "threat_type": threat_type,
                        "severity": severity.value,
                        "execution": "DEFERRED",
                    },
                )
            )


            actions.append(
                self._create_action(
                    action_type=ActionType.ESCALATE,
                    priority=40,
                    description=(
                        "Escalate the containment decision "
                        "for security review."
                    ),
                    requires_approval=approval_required,
                    approval_level=approval_level,
                    parameters={
                        "recommended_action": (
                            recommended_action
                        ),
                    },
                )
            )


        elif response_level == ResponseLevel.ISOLATE:


            actions.append(
                self._create_action(
                    action_type=ActionType.CREATE_ALERT,
                    priority=40,
                    description=(
                        "Create a critical security alert "
                        "for the detected threat."
                    ),
                    requires_approval=False,
                    approval_level=ApprovalLevel.NONE,
                    parameters={
                        "threat_type": threat_type,
                        "severity": severity.value,
                    },
                )
            )


            actions.append(
                self._create_action(
                    action_type=ActionType.ISOLATE,
                    priority=10,
                    description=(
                        "Prepare isolation of the affected "
                        "security context."
                    ),
                    requires_approval=True,
                    approval_level=(
                        approval_level
                        if approval_level
                        != ApprovalLevel.NONE
                        else ApprovalLevel.SECURITY_ADMIN
                    ),
                    parameters={
                        "threat_type": threat_type,
                        "severity": severity.value,
                        "execution": "DEFERRED",
                        "destructive_execution": False,
                    },
                )
            )


            actions.append(
                self._create_action(
                    action_type=ActionType.ESCALATE,
                    priority=20,
                    description=(
                        "Escalate the critical security event "
                        "to the security administration workflow."
                    ),
                    requires_approval=True,
                    approval_level=(
                        approval_level
                        if approval_level
                        != ApprovalLevel.NONE
                        else ApprovalLevel.SECURITY_ADMIN
                    ),
                    parameters={
                        "recommended_action": (
                            recommended_action
                        ),
                    },
                )
            )


        return actions


    def _create_action(
        self,
        *,
        action_type: ActionType,
        priority: int,
        description: str,
        requires_approval: bool,
        approval_level: ApprovalLevel,
        parameters: Optional[Mapping[str, Any]] = None,
    ) -> ResponseAction:
        """Create a safe response action."""


        return ResponseAction(
            action_id=self._generate_action_id(),
            action_type=action_type.value,
            priority=max(
                0,
                min(
                    int(priority),
                    100,
                ),
            ),
            description=description,
            requires_approval=requires_approval,
            approval_level=approval_level.value,
            executable=False,
            execution_status="NOT_EXECUTED",
            parameters=dict(
                parameters or {}
            ),
        )


    # ========================================================================
    # RATIONALE
    # ========================================================================


    @staticmethod
    def _build_rationale(
        *,
        threat_detected: bool,
        threat_type: str,
        severity: ThreatSeverity,
        risk_score: float,
        confidence: float,
        response_level: ResponseLevel,
        approval_required: bool,
    ) -> List[str]:
        """Build a human-readable decision rationale."""


        if not threat_detected:
            return [
                "Intelligence result indicates no detected threat.",
                "No security response action is required.",
            ]


        rationale = [
            (
                f"Threat detected: {threat_type}."
            ),
            (
                f"Severity classified as {severity.value}."
            ),
            (
                f"Risk score evaluated at {risk_score:.3f}."
            ),
            (
                f"Detection confidence evaluated at "
                f"{confidence:.3f}."
            ),
            (
                f"Response policy selected "
                f"{response_level.value}."
            ),
        ]


        if approval_required:
            rationale.append(
                "The selected response requires authorization "
                "before any future executor may act."
            )


        rationale.append(
            "The Response Engine does not execute security actions."
        )


        return rationale


    # ========================================================================
    # INPUT NORMALIZATION
    # ========================================================================


    def _normalize_intelligence_result(
        self,
        intelligence_result: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Convert supported intelligence-result representations into a dict.
        """


        if intelligence_result is None:
            return None


        try:


            if isinstance(
                intelligence_result,
                Mapping,
            ):
                result = dict(
                    intelligence_result
                )


            elif hasattr(
                intelligence_result,
                "to_dict",
            ):
                converted = (
                    intelligence_result.to_dict()
                )


                if not isinstance(
                    converted,
                    Mapping,
                ):
                    return None


                result = dict(converted)


            elif hasattr(
                intelligence_result,
                "__dict__",
            ):
                result = dict(
                    vars(
                        intelligence_result
                    )
                )


            else:
                return None


        except Exception:
            logger.exception(
                "Unable to normalize intelligence result."
            )
            return None


        try:
            encoded = json.dumps(
                result,
                default=str,
                ensure_ascii=False,
            ).encode("utf-8")


        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None


        if len(encoded) > self.config.max_input_size:
            return None


        return result


    def _validate_intelligence_result(
        self,
        result: Mapping[str, Any],
    ) -> Optional[str]:
        """Validate the minimum intelligence contract."""


        required_fields = (
            "threat_detected",
            "severity",
            "risk_score",
            "confidence",
        )


        for field_name in required_fields:
            if field_name not in result:
                return (
                    f"Intelligence result is missing "
                    f"required field: {field_name}."
                )


        severity_value = result.get(
            "severity"
        )


        if self._normalize_severity(
            severity_value
        ) is None:


            if self.config.reject_unknown_severity:
                return "Unknown threat severity."


        risk_score = self._safe_score(
            result.get(
                "risk_score",
                0.0,
            )
        )


        confidence = self._safe_score(
            result.get(
                "confidence",
                0.0,
            )
        )


        if not (
            0.0
            <= risk_score
            <= 100.0
        ):
            return (
                "Risk score must be within "
                "the range 0..100."
            )


        if not (
            0.0
            <= confidence
            <= 100.0
        ):
            return (
                "Confidence must be within "
                "the range 0..100."
            )


        response_level = result.get(
            "response_level",
            ResponseLevel.NONE.value,
        )


        if (
            self._normalize_response_level(
                response_level
            )
            is None
            and self.config.reject_unknown_response_level
        ):
            return "Unknown response level."


        return None


    @staticmethod
    def _extract_request_id(
        result: Mapping[str, Any],
        explicit_request_id: Optional[str],
    ) -> str:
        """Resolve the correlation/request ID."""


        if explicit_request_id:
            value = str(
                explicit_request_id
            ).strip()


            if value:
                return value[:128]


        value = result.get(
            "request_id"
        )


        if value is not None:


            normalized = str(
                value
            ).strip()


            if normalized:
                return normalized[:128]


        return "UNKNOWN"


    @staticmethod
    def _normalize_severity(
        value: Any,
    ) -> Optional[ThreatSeverity]:
        """Normalize a severity value."""


        try:
            normalized = str(
                value
            ).strip().upper()


            return ThreatSeverity(
                normalized
            )


        except (
            ValueError,
            TypeError,
        ):
            return None


    @staticmethod
    def _normalize_response_level(
        value: Any,
    ) -> Optional[ResponseLevel]:
        """Normalize a response-level value."""


        try:
            normalized = str(
                value
            ).strip().upper()


            return ResponseLevel(
                normalized
            )


        except (
            ValueError,
            TypeError,
        ):
            return None


    @staticmethod
    def _normalize_text(
        value: Any,
        *,
        default: str,
        maximum: int,
    ) -> str:
        """Normalize bounded textual input."""


        if value is None:
            return default


        try:
            normalized = str(
                value
            ).strip()


        except Exception:
            return default


        if not normalized:
            return default


        return normalized[:maximum]


    @staticmethod
    def _normalize_source(
        source: Any,
    ) -> str:
        """Normalize a source identifier."""


        if source is None:
            return "unknown"


        try:
            value = str(
                source
            ).strip()


        except Exception:
            return "unknown"


        if not value:
            return "unknown"


        return value[:256]


    # ========================================================================
    # SAFE NUMERIC VALUES
    # ========================================================================


    @staticmethod
    def _safe_score(
        value: Any,
    ) -> float:
        """Return a finite bounded score in the range 0..100."""


        try:
            numeric = float(
                value
            )


            if not math.isfinite(
                numeric
            ):
                return 0.0


            numeric = max(
                0.0,
                min(
                    100.0,
                    numeric,
                ),
            )


            return round(
                numeric,
                3,
            )


        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0


    # ========================================================================
    # AUDIT
    # ========================================================================


    def _audit_response(
        self,
        *,
        response_id: str,
        request_id: str,
        source: str,
        threat_detected: bool,
        threat_type: str,
        severity: ThreatSeverity,
        risk_score: float,
        confidence: float,
        response_level: ResponseLevel,
        execution_mode: ExecutionMode,
        approval_required: bool,
    ) -> Dict[str, Any]:
        """
        Write a structured response-planning event to the audit subsystem.
        """


        if not self.config.audit_enabled:
            return {
                "enabled": False,
                "recorded": False,
            }


        if self.audit_logger is None:
            return {
                "enabled": True,
                "recorded": False,
                "reason": (
                    "Audit logger not attached."
                ),
            }


        payload = {
            "response_id": response_id,
            "request_id": request_id,
            "timestamp": self._utc_now(),
            "source": source,
            "event_type": "RESPONSE_PLAN",
            "threat_detected": threat_detected,
            "threat_type": threat_type,
            "severity": severity.value,
            "risk_score": risk_score,
            "confidence": confidence,
            "response_level": response_level.value,
            "execution_mode": execution_mode.value,
            "approval_required": approval_required,
            "executed": False,
            "engine_version": self.VERSION,
        }


        try:


            if hasattr(
                self.audit_logger,
                "log_event",
            ):


                audit_result = (
                    self.audit_logger.log_event(
                        payload
                    )
                )


            elif hasattr(
                self.audit_logger,
                "record",
            ):


                audit_result = (
                    self.audit_logger.record(
                        payload
                    )
                )


            else:


                return {
                    "enabled": True,
                    "recorded": False,
                    "reason": (
                        "Attached audit logger does not expose "
                        "a supported interface."
                    ),
                }


            return {
                "enabled": True,
                "recorded": True,
                "result": audit_result,
            }


        except Exception:


            logger.exception(
                "Failed to write response audit event | "
                "response_id=%s",
                response_id,
            )


            return {
                "enabled": True,
                "recorded": False,
                "reason": (
                    "Audit operation failed."
                ),
            }


    # ========================================================================
    # STATISTICS
    # ========================================================================


    def _record_planned(
        self,
        *,
        result: ResponseResult,
        severity: ThreatSeverity,
        response_level: ResponseLevel,
        threat_type: str,
        approval_required: bool,
    ) -> None:
        """Record a successful response plan."""


        with self._lock:


            self.planned_requests += 1


            self.status_counts[
                ResponseStatus.PLANNED.value
            ] += 1


            self._record_timing(
                self._extract_processing_time(
                    result
                )
            )


            self.severity_counts[
                severity.value
            ] += 1


            self.response_level_counts[
                response_level.value
            ] += 1


            self.threat_type_counts[
                threat_type
            ] = (
                self.threat_type_counts.get(
                    threat_type,
                    0,
                )
                + 1
            )


            if approval_required:
                self.approval_required_count += 1


            if response_level == ResponseLevel.MONITOR:
                self.monitor_actions += 1


            elif response_level == ResponseLevel.ALERT:
                self.alert_actions += 1


            elif response_level == ResponseLevel.CONTAIN:
                self.contain_actions += 1


            elif response_level == ResponseLevel.ISOLATE:
                self.isolate_actions += 1


    def _record_rejected(
        self,
        result: ResponseResult,
    ) -> None:
        """Record a rejected request."""


        with self._lock:


            self.rejected_requests += 1


            self.status_counts[
                ResponseStatus.REJECTED.value
            ] += 1


            self._record_timing(
                self._extract_processing_time(
                    result
                )
            )


    def _record_failed(
        self,
        result: ResponseResult,
    ) -> None:
        """Record a failed request."""


        with self._lock:


            self.failed_requests += 1


            self.status_counts[
                ResponseStatus.FAILED.value
            ] += 1


            self._record_timing(
                self._extract_processing_time(
                    result
                )
            )


    def _record_timing(
        self,
        processing_ms: float,
    ) -> None:
        """Update timing telemetry."""


        self.total_processing_ms += processing_ms


        self.max_processing_ms = max(
            self.max_processing_ms,
            processing_ms,
        )


    @staticmethod
    def _extract_processing_time(
        result: ResponseResult,
    ) -> float:
        """Extract processing timing safely."""


        try:


            value = (
                result.metadata.get(
                    "processing_time_ms",
                    0.0,
                )
            )


            numeric = float(
                value
            )


            if not math.isfinite(
                numeric
            ):
                return 0.0


            return max(
                0.0,
                numeric,
            )


        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0


    # ========================================================================
    # STATUS
    # ========================================================================


    def get_status(self) -> Dict[str, Any]:
        """
        Return operational Response Engine status.


        These metrics describe engine operation and response planning.
        They are NOT ML accuracy metrics.
        """


        with self._lock:


            total = self.total_requests


            planning_success_rate = (
                (
                    self.planned_requests
                    / total
                )
                * 100.0
                if total
                else 0.0
            )


            average_processing_ms = (
                self.total_processing_ms
                / total
                if total
                else 0.0
            )


            return {
                "engine": (
                    "EnterpriseGuard Response Engine"
                ),
                "version": self.VERSION,
                "status": (
                    "active"
                    if self.config.enabled
                    else "disabled"
                ),
                "configuration": {
                    "execution_mode": (
                        self.config.execution_mode.value
                    ),
                    "automatic_execution_enabled": (
                        self.config.automatic_execution_enabled
                    ),
                    "critical_requires_approval": (
                        self.config.critical_requires_approval
                    ),
                    "high_requires_approval": (
                        self.config.high_requires_approval
                    ),
                    "audit_enabled": (
                        self.config.audit_enabled
                    ),
                    "processing_target_ms": (
                        self.config.processing_target_ms
                    ),
                    "max_input_size": (
                        self.config.max_input_size
                    ),
                    "max_actions_per_plan": (
                        self.config.max_actions_per_plan
                    ),
                },
                "policy": {
                    "low": (
                        self.policy.low_level.value
                    ),
                    "medium": (
                        self.policy.medium_level.value
                    ),
                    "high": (
                        self.policy.high_level.value
                    ),
                    "critical": (
                        self.policy.critical_level.value
                    ),
                    "low_approval": (
                        self.policy.low_approval.value
                    ),
                    "medium_approval": (
                        self.policy.medium_approval.value
                    ),
                    "high_approval": (
                        self.policy.high_approval.value
                    ),
                    "critical_approval": (
                        self.policy.critical_approval.value
                    ),
                },
                "statistics": {
                    "total_requests": total,
                    "planned_requests": (
                        self.planned_requests
                    ),
                    "rejected_requests": (
                        self.rejected_requests
                    ),
                    "failed_requests": (
                        self.failed_requests
                    ),
                    "approval_required": (
                        self.approval_required_count
                    ),
                    "monitor_actions": (
                        self.monitor_actions
                    ),
                    "alert_actions": (
                        self.alert_actions
                    ),
                    "contain_actions": (
                        self.contain_actions
                    ),
                    "isolate_actions": (
                        self.isolate_actions
                    ),
                    "planning_success_rate": round(
                        planning_success_rate,
                        2,
                    ),
                    "average_processing_ms": round(
                        average_processing_ms,
                        3,
                    ),
                    "max_processing_ms": round(
                        self.max_processing_ms,
                        3,
                    ),
                },
                "status_counts": dict(
                    self.status_counts
                ),
                "severity_counts": dict(
                    self.severity_counts
                ),
                "response_level_counts": dict(
                    self.response_level_counts
                ),
                "threat_type_counts": dict(
                    self.threat_type_counts
                ),
                "audit": {
                    "enabled": (
                        self.config.audit_enabled
                    ),
                    "attached": (
                        self.audit_logger is not None
                    ),
                },
                "execution": {
                    "executor_attached": False,
                    "automatic_execution": False,
                    "note": (
                        "Response Engine creates plans only. "
                        "Actual execution belongs to a dedicated "
                        "Response Executor subsystem."
                    ),
                },
                "notes": {
                    "planning_rate": (
                        "Operational telemetry, not model accuracy."
                    ),
                    "response_execution": (
                        "No security action is executed by this engine."
                    ),
                    "approval": (
                        "High and critical responses may require "
                        "explicit authorization."
                    ),
                },
            }


    # ========================================================================
    # HEALTH CHECK
    # ========================================================================


    def health_check(self) -> Dict[str, Any]:
        """
        Return a lightweight health assessment.
        """


        return {
            "healthy": bool(
                self.config.enabled
            ),
            "engine": {
                "enabled": self.config.enabled,
                "version": self.VERSION,
            },
            "policy": {
                "available": self.policy is not None,
            },
            "executor": {
                "attached": False,
                "available": False,
                "execution_enabled": False,
            },
            "audit": {
                "enabled": (
                    self.config.audit_enabled
                ),
                "attached": (
                    self.audit_logger is not None
                ),
            },
            "safety": {
                "destructive_actions_enabled": False,
                "shell_execution_enabled": False,
                "network_isolation_enabled": False,
                "process_termination_enabled": False,
            },
        }


    # ========================================================================
    # IDENTIFIERS
    # ========================================================================


    @staticmethod
    def _generate_response_id(
        request_id: Optional[str],
    ) -> str:
        """
        Generate a unique response correlation identifier.


        No event contents are included in the identifier.
        """


        timestamp = datetime.now(
            timezone.utc
        ).isoformat()


        seed = (
            timestamp
            + str(
                request_id or "UNKNOWN"
            )
            + uuid.uuid4().hex
        )


        digest = hashlib.sha256(
            seed.encode("utf-8")
        ).hexdigest()


        return (
            f"ER-{digest[:24].upper()}"
        )


    @staticmethod
    def _generate_action_id() -> str:
        """Generate a unique action identifier."""


        return (
            "EA-"
            + uuid.uuid4().hex[:24].upper()
        )


    # ========================================================================
    # TIME
    # ========================================================================


    @staticmethod
    def _utc_now() -> str:
        """Return current UTC timestamp."""


        return datetime.now(
            timezone.utc
        ).isoformat()


    # ========================================================================
    # REJECTED RESULT
    # ========================================================================


    def _build_rejected_result(
        self,
        *,
        response_id: str,
        request_id: str,
        started: float,
        reason: str,
        source: str,
    ) -> ResponseResult:
        """Build a safe rejected result."""


        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000.0


        return ResponseResult(
            response_id=response_id,
            request_id=request_id,
            timestamp=self._utc_now(),
            status=ResponseStatus.REJECTED.value,
            execution_mode=(
                ExecutionMode.DRY_RUN.value
            ),
            plan={},
            audit={},
            metadata={
                "source": source,
                "processing_time_ms": round(
                    elapsed_ms,
                    3,
                ),
                "reason": reason,
            },
            engine_version=self.VERSION,
            error=reason,
        )




# ============================================================================
# DEFAULT ENGINE INSTANCE
# ============================================================================




response_engine = ResponseEngine()




# ============================================================================
# SIMPLE PUBLIC API
# ============================================================================




def process_response(
    intelligence_result: Any,
    *,
    source: str = "api",
) -> Dict[str, Any]:
    """
    Convenience API for callers that do not need ResponseResult directly.
    """


    return response_engine.process(
        intelligence_result,
        source=source,
    ).to_dict()




def get_response_status() -> Dict[str, Any]:
    """Return status of the default Response Engine."""


    return response_engine.get_status()




def response_health_check() -> Dict[str, Any]:
    """Return health state of the default Response Engine."""


    return response_engine.health_check()




# ============================================================================
# SELF TEST
# ============================================================================




def _self_test() -> None:
    """
    Run a complete Response Engine integration self-test.


    Verifies:


    - engine availability
    - health check
    - critical response planning
    - approval requirement
    - isolation intent
    - no actual execution
    - benign event handling
    - invalid input rejection
    - batch processing
    - statistics
    """


    print()
    print("=" * 78)
    print(
        "EnterpriseGuard Response Engine - Integration Self Test"
    )
    print("=" * 78)


    # ----------------------------------------------------------------------
    # 1. Engine status
    # ----------------------------------------------------------------------


    print()
    print("[1] Response engine status")


    status_before = response_engine.get_status()


    print(
        json.dumps(
            status_before,
            indent=4,
            ensure_ascii=False,
        )
    )


    # ----------------------------------------------------------------------
    # 2. Health check
    # ----------------------------------------------------------------------


    print()
    print("[2] Health check")


    health = response_engine.health_check()


    print(
        json.dumps(
            health,
            indent=4,
            ensure_ascii=False,
        )
    )


    # ----------------------------------------------------------------------
    # 3. Critical intelligence result
    # ----------------------------------------------------------------------


    print()
    print(
        "[3] Critical threat response planning"
    )


    critical_intelligence = {
        "request_id": "EG-SELFTEST-CRITICAL",
        "timestamp": (
            "2026-01-01T00:00:00+00:00"
        ),
        "status": "SUCCESS",
        "threat_detected": True,
        "threat_type": "CREDENTIAL_STUFFING",
        "severity": "CRITICAL",
        "risk_score": 98.07,
        "confidence": 91.61,
        "recommended_action": (
            "ISOLATE_AND_ESCALATE"
        ),
        "response_level": "ISOLATE",
        "detection": {
            "detector_version": "3.0.0",
        },
    }


    critical_result = response_engine.process(
        critical_intelligence,
        source="self-test",
    )


    print(
        json.dumps(
            critical_result.to_dict(),
            indent=4,
            ensure_ascii=False,
        )
    )


    # ----------------------------------------------------------------------
    # 4. Benign intelligence result
    # ----------------------------------------------------------------------


    print()
    print(
        "[4] Benign event response planning"
    )


    benign_intelligence = {
        "request_id": "EG-SELFTEST-BENIGN",
        "status": "SUCCESS",
        "threat_detected": False,
        "threat_type": "UNKNOWN",
        "severity": "LOW",
        "risk_score": 2.5,
        "confidence": 99.0,
        "recommended_action": "MONITOR",
        "response_level": "NONE",
    }


    benign_result = response_engine.process(
        benign_intelligence,
        source="self-test",
    )


    print(
        json.dumps(
            benign_result.to_dict(),
            indent=4,
            ensure_ascii=False,
        )
    )


    # ----------------------------------------------------------------------
    # 5. Invalid input
    # ----------------------------------------------------------------------


    print()
    print(
        "[5] Invalid intelligence input safety"
    )


    invalid_result = response_engine.process(
        {
            "request_id": "EG-SELFTEST-INVALID",
            "threat_detected": True,
            "severity": "UNKNOWN",
            "risk_score": 90,
            "confidence": 80,
        },
        source="self-test-invalid",
    )


    print(
        json.dumps(
            invalid_result.to_dict(),
            indent=4,
            ensure_ascii=False,
        )
    )


    # ----------------------------------------------------------------------
    # 6. Batch processing
    # ----------------------------------------------------------------------


    print()
    print(
        "[6] Batch response planning"
    )


    batch_result = response_engine.process_batch(
        [
            critical_intelligence,
            benign_intelligence,
        ],
        source="self-test-batch",
    )


    print(
        json.dumps(
            batch_result,
            indent=4,
            ensure_ascii=False,
        )
    )


    # ----------------------------------------------------------------------
    # 7. Final status
    # ----------------------------------------------------------------------


    print()
    print(
        "[7] Final response engine status"
    )


    final_status = response_engine.get_status()


    print(
        json.dumps(
            final_status,
            indent=4,
            ensure_ascii=False,
        )
    )


    # ----------------------------------------------------------------------
    # 8. Verification
    # ----------------------------------------------------------------------


    print()
    print(
        "[8] Final verification"
    )


    critical_plan = (
        critical_result.plan
    )


    critical_actions = (
        critical_plan.get(
            "actions",
            [],
        )
    )


    isolation_action_found = any(
        action.get(
            "action_type"
        )
        == ActionType.ISOLATE.value
        for action in critical_actions
    )


    no_action_executed = all(
        action.get(
            "executable"
        )
        is False
        and action.get(
            "execution_status"
        )
        == "NOT_EXECUTED"
        for action in critical_actions
    )


    verification = {
        "engine_active": (
            final_status["status"]
            == "active"
        ),
        "health_check_available": (
            "healthy" in health
        ),
        "health_check_healthy": (
            health["healthy"]
        ),
        "critical_plan_created": (
            critical_result.status
            == ResponseStatus.PLANNED.value
        ),
        "critical_response_is_isolate": (
            critical_plan.get(
                "response_level"
            )
            == ResponseLevel.ISOLATE.value
        ),
        "critical_requires_approval": (
            critical_plan.get(
                "approval_required"
            )
            is True
        ),
        "security_admin_approval": (
            critical_plan.get(
                "approval_level"
            )
            == ApprovalLevel.SECURITY_ADMIN.value
        ),
        "isolation_action_present": (
            isolation_action_found
        ),
        "no_security_action_executed": (
            no_action_executed
        ),
        "benign_event_planned": (
            benign_result.status
            == ResponseStatus.PLANNED.value
        ),
        "benign_response_is_none": (
            benign_result.plan.get(
                "response_level"
            )
            == ResponseLevel.NONE.value
        ),
        "invalid_input_rejected": (
            invalid_result.status
            == ResponseStatus.REJECTED.value
        ),
        "batch_processed": (
            batch_result["processed"]
            == 2
        ),
        "statistics_updated": (
            final_status["statistics"][
                "total_requests"
            ]
            >= 4
        ),
        "execution_disabled": (
            health["safety"][
                "destructive_actions_enabled"
            ]
            is False
        ),
    }


    all_passed = all(
        verification.values()
    )


    print(
        json.dumps(
            verification,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()
    print("=" * 78)


    if all_passed:


        print(
            "Response Engine self test completed successfully."
        )


    else:


        print(
            "Response Engine self test FAILED."
        )


    print("=" * 78)


    if not all_passed:


        raise RuntimeError(
            "EnterpriseGuard Response Engine self-test failed."
        )




# ============================================================================
# MODULE ENTRY POINT
# ============================================================================




if __name__ == "__main__":
    _self_test()