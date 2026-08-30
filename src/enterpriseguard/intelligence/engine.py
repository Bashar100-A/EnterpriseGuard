"""
EnterpriseGuard - Intelligence Engine
======================================

Adaptive Defense Intelligence Engine (ADIE)
Control-Plane Orchestration Layer.

This module is the runtime boundary between:

    external security events
                |
                v
        DetectionService
                |
                v
       DecisionOrchestrator
                |
                v
        Response Intent
                |
                v
          Audit / Telemetry

Architectural Principles
-------------------------

1. IntelligenceEngine is an orchestrator, not a detector.

2. DetectionService owns:
       - feature extraction
       - detector invocation
       - detection semantics
       - initial security decision

3. DecisionOrchestrator owns:
       - decision orchestration
       - response recommendation
       - future policy integration

4. IntelligenceEngine owns:
       - request correlation
       - input boundary validation
       - event normalization
       - lifecycle
       - timing
       - telemetry
       - audit coordination
       - response-intent envelope
       - batch boundaries
       - safe failure handling
       - health reporting

5. Response execution is NEVER performed here.

6. The engine must remain deterministic, bounded, observable,
   testable, and safe under partial dependency failure.

7. Runtime detection rate is telemetry.
   It is NOT model accuracy.

8. No model training, model persistence, model registry,
   or model loading belongs in this module.

9. The engine must not duplicate detector inference.

10. Security decisions must not be silently redefined by the
    engine layer.

ADIE Direction
--------------

This module is deliberately designed as a control-plane boundary.

Future ADIE layers can be introduced behind this boundary:

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
      +----> Checkpoint
      |
      +----> Playbook
      |
      v
    Response Intent

The current implementation therefore favors explicit contracts
and extension points over hidden intelligence inside the engine.
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
from typing import Any, Dict, Mapping, Optional, Sequence

from ..monitoring.audit import audit_logger as default_audit_logger

from .decision_orchestrator import (
    ALERT,
    ESCALATE,
    IGNORE,
    DecisionOrchestrator,
)

from .detection_service import (
    DetectionService,
    DetectionServiceResult,
)


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = [
    "EngineStatus",
    "ResponseLevel",
    "EngineConfig",
    "EngineResult",
    "IntelligenceEngine",
    "intelligence_engine",
    "process_security_event",
    "get_intelligence_status",
    "intelligence_health_check",
    "self_test",
]


logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

ENGINE_NAME = "EnterpriseGuard Intelligence Engine"
ENGINE_VERSION = "5.0.0"

DEFAULT_SOURCE = "unknown"

UNKNOWN = "UNKNOWN"
BENIGN = "BENIGN"
THREAT = "THREAT"

NO_ACTION = "NO_ACTION"

SAFE_FAILURE = "safe_failure"


# ============================================================================
# ENUMS
# ============================================================================


class EngineStatus(str, Enum):
    """
    Lifecycle state of one engine request.
    """

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class ResponseLevel(str, Enum):
    """
    Non-executing response intent.

    IntelligenceEngine only describes the desired response
    level. It does not execute it.
    """

    NONE = "NONE"
    MONITOR = "MONITOR"
    ALERT = "ALERT"
    ESCALATE = "ESCALATE"


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass(frozen=True)
class EngineConfig:
    """
    Immutable runtime configuration.

    Safety-first defaults are intentional.
    """

    engine_version: str = ENGINE_VERSION

    enabled: bool = True

    processing_target_ms: float = 100.0

    automatic_response_enabled: bool = False

    audit_enabled: bool = True

    max_event_size: int = 1_000_000

    max_batch_size: int = 10_000

    max_source_length: int = 256

    include_event_metadata: bool = True

    include_response_intent: bool = True

    request_id_prefix: str = "eg"

    def validate(self) -> None:
        """
        Validate configuration invariants.
        """

        if not self.engine_version.strip():
            raise ValueError(
                "engine_version must not be empty"
            )

        if self.processing_target_ms < 0:
            raise ValueError(
                "processing_target_ms must not be negative"
            )

        if self.max_event_size <= 0:
            raise ValueError(
                "max_event_size must be greater than zero"
            )

        if self.max_batch_size <= 0:
            raise ValueError(
                "max_batch_size must be greater than zero"
            )

        if self.max_source_length <= 0:
            raise ValueError(
                "max_source_length must be greater than zero"
            )

        if not self.request_id_prefix.strip():
            raise ValueError(
                "request_id_prefix must not be empty"
            )


# ============================================================================
# RESULT MODEL
# ============================================================================


@dataclass
class EngineResult:
    """
    Canonical runtime result.

    This is the public contract of IntelligenceEngine.

    The result is deliberately structured so that future ADIE
    consumers can inspect:

        - processing state
        - detection state
        - risk signal
        - decision
        - response intent
        - audit state
        - operational metadata

    without requiring knowledge of the internal implementation.
    """

    request_id: str

    timestamp: str

    status: str

    processing_time_ms: float

    threat_detected: bool

    threat_type: str

    severity: str

    risk_score: float

    confidence: float

    recommended_action: str

    response_level: str

    detection: Dict[str, Any] = field(
        default_factory=dict
    )

    orchestration: Dict[str, Any] = field(
        default_factory=dict
    )

    audit: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    engine_version: str = ENGINE_VERSION

    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a JSON-compatible representation.
        """

        return asdict(self)


# ============================================================================
# INTELLIGENCE ENGINE
# ============================================================================


class IntelligenceEngine:
    """
    EnterpriseGuard runtime intelligence control plane.

    Responsibility boundary:

        External Event
             |
             v
        IntelligenceEngine
             |
             v
        DetectionService
             |
             v
        DetectionServiceResult
             |
             v
        DecisionOrchestrator
             |
             v
        Response Intent
             |
             +----> Audit
             |
             +----> Telemetry

    No enforcement action is executed here.
    """

    VERSION = ENGINE_VERSION

    def __init__(
        self,
        *,
        detector_instance: Optional[Any] = None,
        detection_service_instance: Optional[
            DetectionService
        ] = None,
        decision_orchestrator_instance: Optional[
            DecisionOrchestrator
        ] = None,
        config: Optional[EngineConfig] = None,
        audit_logger_instance: Optional[Any] = None,
    ) -> None:
        """
        Initialize the engine.

        Dependency injection is supported to keep the engine:

            - testable
            - replaceable
            - integration-friendly
            - independent of concrete implementations
        """

        self.config = config or EngineConfig()

        self.config.validate()

        self.detector = detector_instance

        self.detection_service = (
            detection_service_instance
            if detection_service_instance is not None
            else self._build_detection_service(
                detector_instance
            )
        )

        self.decision_orchestrator = (
            decision_orchestrator_instance
            if decision_orchestrator_instance is not None
            else DecisionOrchestrator()
        )

        self.audit_logger = (
            audit_logger_instance
            if audit_logger_instance is not None
            else default_audit_logger
        )

        self._lock = RLock()

        self.created_at = self._utc_now()

        self._reset_telemetry()

    # ======================================================================
    # LIFECYCLE
    # ======================================================================

    def _reset_telemetry(self) -> None:
        """
        Initialize runtime telemetry.

        This method does not touch dependencies or external state.
        """

        with self._lock:
            self.total_events = 0

            self.successful_events = 0

            self.failed_events = 0

            self.rejected_events = 0

            self.detected_threats = 0

            self.alert_decisions = 0

            self.escalate_decisions = 0

            self.ignore_decisions = 0

            self.monitor_decisions = 0

            self.total_processing_ms = 0.0

            self.max_processing_ms = 0.0

            self.threat_types: Dict[
                str,
                int,
            ] = {}

            self.severity_counts: Dict[
                str,
                int,
            ] = {}

            self.error_types: Dict[
                str,
                int,
            ] = {}

    # ======================================================================
    # PUBLIC PROCESSING API
    # ======================================================================

    def process_event(
        self,
        event: Mapping[str, Any],
        *,
        request_id: Optional[str] = None,
        source: str = DEFAULT_SOURCE,
    ) -> EngineResult:
        """
        Process one security event.

        Processing stages:

            1. Correlation
            2. Availability validation
            3. Input validation
            4. Normalization
            5. DetectionService
            6. DecisionOrchestrator
            7. Response intent
            8. Audit
            9. Telemetry
            10. Canonical result
        """

        started = time.perf_counter()

        with self._lock:
            self.total_events += 1

        normalized_source = self._normalize_source(
            source
        )

        correlation_id = (
            request_id
            if request_id is not None
            else self._generate_request_id(event)
        )

        try:
            # --------------------------------------------------------------
            # ENGINE AVAILABILITY
            # --------------------------------------------------------------

            if not self.config.enabled:
                result = self._build_rejected_result(
                    request_id=correlation_id,
                    started=started,
                    reason=(
                        "Intelligence engine is disabled."
                    ),
                    source=normalized_source,
                )

                self._record_rejected(result)

                return result

            # --------------------------------------------------------------
            # DEPENDENCY VALIDATION
            # --------------------------------------------------------------

            dependency_error = (
                self._validate_dependencies()
            )

            if dependency_error is not None:
                result = self._build_failed_result(
                    request_id=correlation_id,
                    started=started,
                    reason=dependency_error,
                    source=normalized_source,
                )

                self._record_failure(result)

                return result

            # --------------------------------------------------------------
            # INPUT VALIDATION
            # --------------------------------------------------------------

            validation_error = self._validate_event(
                event
            )

            if validation_error is not None:
                result = self._build_rejected_result(
                    request_id=correlation_id,
                    started=started,
                    reason=validation_error,
                    source=normalized_source,
                )

                self._record_rejected(result)

                return result

            # --------------------------------------------------------------
            # NORMALIZATION
            # --------------------------------------------------------------

            normalized_event = self._normalize_event(
                event
            )

            # --------------------------------------------------------------
            # DETECTION
            # --------------------------------------------------------------

            detection_result = (
                self.detection_service.analyze(
                    [normalized_event]
                )
            )

            detection_result = (
                self._coerce_detection_result(
                    detection_result
                )
            )

            # --------------------------------------------------------------
            # DETECTION FAILURE
            # --------------------------------------------------------------

            if not self._detection_succeeded(
                detection_result
            ):
                return self._handle_detection_failure(
                    request_id=correlation_id,
                    source=normalized_source,
                    detection=detection_result,
                    started=started,
                    event=normalized_event,
                )

            # --------------------------------------------------------------
            # DECISION ORCHESTRATION
            # --------------------------------------------------------------

            orchestration_result = (
                self.decision_orchestrator.handle(
                    detection_result
                )
            )

            orchestration_payload = (
                self._safe_json(
                    orchestration_result
                )
            )

            # --------------------------------------------------------------
            # RESPONSE INTENT
            # --------------------------------------------------------------

            response_level = (
                self._response_level_from_decision(
                    detection_result.decision
                )
            )

            response_intent = (
                self._build_response_intent(
                    detection=detection_result,
                    response_level=response_level,
                )
            )

            # --------------------------------------------------------------
            # SECURITY SEMANTICS
            # --------------------------------------------------------------

            threat_detected = self._is_threat(
                detection_result
            )

            threat_type = (
                THREAT
                if threat_detected
                else BENIGN
            )

            severity = self._derive_severity(
                detection_result
            )

            risk_score = self._derive_risk_score(
                detection_result
            )

            confidence = self._safe_score(
                detection_result.confidence
            )

            recommended_action = (
                self._recommended_action(
                    detection_result.decision
                )
            )

            # --------------------------------------------------------------
            # TIMING
            # --------------------------------------------------------------

            elapsed_ms = self._elapsed_ms(
                started
            )

            within_target = (
                elapsed_ms
                <= self.config.processing_target_ms
            )

            # --------------------------------------------------------------
            # AUDIT
            # --------------------------------------------------------------

            audit_result = self._audit_detection(
                request_id=correlation_id,
                source=normalized_source,
                detection=detection_result,
                orchestration=orchestration_payload,
                response_level=response_level,
            )

            # --------------------------------------------------------------
            # RESULT
            # --------------------------------------------------------------

            result = EngineResult(
                request_id=correlation_id,
                timestamp=self._utc_now(),
                status=EngineStatus.SUCCESS.value,
                processing_time_ms=round(
                    elapsed_ms,
                    3,
                ),
                threat_detected=threat_detected,
                threat_type=threat_type,
                severity=severity,
                risk_score=risk_score,
                confidence=confidence,
                recommended_action=recommended_action,
                response_level=response_level.value,
                detection=self._safe_dict(
                    detection_result.to_dict()
                ),
                orchestration=(
                    orchestration_payload
                    if isinstance(
                        orchestration_payload,
                        dict,
                    )
                    else {
                        "value": orchestration_payload
                    }
                ),
                audit=audit_result,
                metadata=self._build_metadata(
                    source=normalized_source,
                    event=normalized_event,
                    within_target=within_target,
                    response_intent=(
                        response_intent
                        if self.config.include_response_intent
                        else None
                    ),
                ),
                engine_version=self.VERSION,
            )

            self._record_success(result)

            return result

        except Exception as exc:
            return self._handle_internal_failure(
                request_id=correlation_id,
                source=normalized_source,
                started=started,
                exception=exc,
            )

    # ======================================================================
    # BATCH PROCESSING
    # ======================================================================

    def process_batch(
        self,
        events: Sequence[
            Mapping[str, Any]
        ],
        *,
        source: str = "batch",
    ) -> Dict[str, Any]:
        """
        Process a bounded batch sequentially.

        Sequential processing is intentional at this layer.

        Parallelism can be introduced later behind a dedicated
        execution boundary without changing the public result contract.
        """

        started = time.perf_counter()

        validation_error = self._validate_batch(
            events
        )

        if validation_error is not None:
            return {
                "status": EngineStatus.REJECTED.value,
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "rejected": 0,
                "threats_detected": 0,
                "processing_time_ms": round(
                    self._elapsed_ms(started),
                    3,
                ),
                "results": [],
                "error": validation_error,
                "engine_version": self.VERSION,
            }

        results = []

        for event in events:
            results.append(
                self.process_event(
                    event,
                    source=source,
                )
            )

        successful = [
            result
            for result in results
            if result.status
            == EngineStatus.SUCCESS.value
        ]

        failed = [
            result
            for result in results
            if result.status
            == EngineStatus.FAILED.value
        ]

        rejected = [
            result
            for result in results
            if result.status
            == EngineStatus.REJECTED.value
        ]

        threats = [
            result
            for result in results
            if result.threat_detected
        ]

        if not results:
            batch_status = EngineStatus.SUCCESS.value

        elif failed:
            batch_status = EngineStatus.FAILED.value

        elif rejected:
            batch_status = EngineStatus.REJECTED.value

        else:
            batch_status = EngineStatus.SUCCESS.value

        return {
            "status": batch_status,
            "processed": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "rejected": len(rejected),
            "threats_detected": len(threats),
            "processing_time_ms": round(
                self._elapsed_ms(started),
                3,
            ),
            "results": [
                result.to_dict()
                for result in results
            ],
            "engine_version": self.VERSION,
        }

    # ======================================================================
    # DEPENDENCY CONSTRUCTION
    # ======================================================================

    @staticmethod
    def _build_detection_service(
        detector_instance: Optional[Any],
    ) -> Optional[DetectionService]:
        """
        Construct DetectionService only when a detector exists.

        Lazy default engine construction is handled separately.
        """

        if detector_instance is None:
            return None

        return DetectionService(
            detector_instance
        )

    def _validate_dependencies(
        self,
    ) -> Optional[str]:
        """
        Validate required runtime dependencies.
        """

        if self.detection_service is None:
            return (
                "DetectionService dependency is unavailable."
            )

        if self.decision_orchestrator is None:
            return (
                "DecisionOrchestrator dependency is unavailable."
            )

        analyze = getattr(
            self.detection_service,
            "analyze",
            None,
        )

        if not callable(analyze):
            return (
                "DetectionService does not expose analyze()."
            )

        handle = getattr(
            self.decision_orchestrator,
            "handle",
            None,
        )

        if not callable(handle):
            return (
                "DecisionOrchestrator does not expose handle()."
            )

        return None

    # ======================================================================
    # VALIDATION
    # ======================================================================

    def _validate_event(
        self,
        event: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Validate an untrusted event at the engine boundary.
        """

        if not isinstance(
            event,
            Mapping,
        ):
            return "event must be a mapping"

        try:
            serialized = json.dumps(
                dict(event),
                default=str,
                ensure_ascii=False,
            )
        except Exception:
            return (
                "event cannot be serialized safely"
            )

        try:
            encoded_size = len(
                serialized.encode("utf-8")
            )
        except Exception:
            return (
                "event size could not be determined"
            )

        if (
            encoded_size
            > self.config.max_event_size
        ):
            return (
                "event exceeds configured maximum size"
            )

        return None

    def _validate_batch(
        self,
        events: Any,
    ) -> Optional[str]:
        """
        Validate a batch before processing.
        """

        if events is None:
            return "events must not be None"

        if isinstance(
            events,
            (
                str,
                bytes,
                bytearray,
            ),
        ):
            return (
                "events must be a sequence "
                "of event mappings"
            )

        if not isinstance(
            events,
            Sequence,
        ):
            return "events must be a sequence"

        if (
            len(events)
            > self.config.max_batch_size
        ):
            return (
                "batch exceeds configured maximum size"
            )

        for index, event in enumerate(events):
            error = self._validate_event(
                event
            )

            if error is not None:
                return (
                    f"event at index {index}: "
                    f"{error}"
                )

        return None

    # ======================================================================
    # NORMALIZATION
    # ======================================================================

    @staticmethod
    def _normalize_event(
        event: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Normalize only the structural boundary.

        DetectionService remains responsible for semantic
        interpretation and feature extraction.

        Unknown fields are preserved.
        """

        normalized: Dict[str, Any] = {}

        for key, value in event.items():
            try:
                normalized_key = str(
                    key
                ).strip()
            except Exception:
                continue

            if not normalized_key:
                continue

            normalized[
                normalized_key
            ] = value

        return normalized

    def _normalize_source(
        self,
        source: Any,
    ) -> str:
        """
        Normalize an external source label.
        """

        if source is None:
            return DEFAULT_SOURCE

        try:
            normalized = str(
                source
            ).strip()
        except Exception:
            return DEFAULT_SOURCE

        if not normalized:
            return DEFAULT_SOURCE

        return normalized[
            : self.config.max_source_length
        ]

    # ======================================================================
    # DETECTION RESULT BOUNDARY
    # ======================================================================

    @staticmethod
    def _coerce_detection_result(
        result: Any,
    ) -> DetectionServiceResult:
        """
        Convert compatible result implementations into the
        canonical DetectionServiceResult contract.

        This adapter exists at the integration boundary only.
        """

        if isinstance(
            result,
            DetectionServiceResult,
        ):
            return result

        decision = IntelligenceEngine._extract_value(
            result,
            "decision",
        )

        if decision is None:
            decision = IGNORE

        return DetectionServiceResult(
            decision=str(decision),
            predicted_class=(
                IntelligenceEngine._extract_value(
                    result,
                    "predicted_class",
                )
            ),
            threat_probability=(
                IntelligenceEngine._optional_float(
                    IntelligenceEngine._extract_value(
                        result,
                        "threat_probability",
                    )
                )
            ),
            benign_probability=(
                IntelligenceEngine._optional_float(
                    IntelligenceEngine._extract_value(
                        result,
                        "benign_probability",
                    )
                )
            ),
            anomaly_score=(
                IntelligenceEngine._optional_float(
                    IntelligenceEngine._extract_value(
                        result,
                        "anomaly_score",
                    )
                )
            ),
            confidence=(
                IntelligenceEngine._optional_float(
                    IntelligenceEngine._extract_value(
                        result,
                        "confidence",
                    )
                )
            ),
            model_version=(
                IntelligenceEngine._string_or_none(
                    IntelligenceEngine._extract_value(
                        result,
                        "model_version",
                    )
                )
            ),
            error=(
                IntelligenceEngine._string_or_none(
                    IntelligenceEngine._extract_value(
                        result,
                        "error",
                    )
                )
            ),
        )

    @staticmethod
    def _detection_succeeded(
        detection: DetectionServiceResult,
    ) -> bool:
        """
        Determine whether DetectionService produced
        a usable result.

        DetectionService owns the meaning of its error state.
        """

        error = getattr(
            detection,
            "error",
            None,
        )

        return not bool(error)

    # ======================================================================
    # RESPONSE INTENT
    # ======================================================================

    @staticmethod
    def _response_level_from_decision(
        decision: Any,
    ) -> ResponseLevel:
        """
        Convert a decision into a response intent.

        No action is executed.
        """

        normalized = (
            str(decision)
            .strip()
            .upper()
            if decision is not None
            else IGNORE
        )

        if normalized == ESCALATE:
            return ResponseLevel.ESCALATE

        if normalized == ALERT:
            return ResponseLevel.ALERT

        if normalized == IGNORE:
            return ResponseLevel.NONE

        return ResponseLevel.MONITOR

    def _build_response_intent(
        self,
        *,
        detection: DetectionServiceResult,
        response_level: ResponseLevel,
    ) -> Dict[str, Any]:
        """
        Build a deferred response intent.

        This method NEVER executes a response.
        """

        return {
            "enabled": (
                self.config.automatic_response_enabled
            ),
            "executed": False,
            "execution_mode": "DEFERRED",
            "response_level": (
                response_level.value
            ),
            "decision": detection.decision,
            "recommended_action": (
                self._recommended_action(
                    detection.decision
                )
            ),
            "reason": (
                "IntelligenceEngine generates response "
                "intent only. Execution belongs to a "
                "dedicated response subsystem."
            ),
        }

    # ======================================================================
    # AUDIT
    # ======================================================================

    def _audit_detection(
        self,
        *,
        request_id: str,
        source: str,
        detection: DetectionServiceResult,
        orchestration: Any,
        response_level: ResponseLevel,
    ) -> Dict[str, Any]:
        """
        Record a successful detection-stage audit event.

        Audit failure is isolated from security processing.
        """

        if not self.config.audit_enabled:
            return {
                "enabled": False,
                "written": False,
                "reason": (
                    "Audit disabled by configuration."
                ),
            }

        payload = {
            "event_type": (
                "INTELLIGENCE_DETECTION"
            ),
            "request_id": request_id,
            "source": source,
            "timestamp": self._utc_now(),
            "decision": detection.decision,
            "response_level": (
                response_level.value
            ),
            "predicted_class": (
                detection.predicted_class
            ),
            "threat_probability": (
                detection.threat_probability
            ),
            "benign_probability": (
                detection.benign_probability
            ),
            "anomaly_score": (
                detection.anomaly_score
            ),
            "confidence": (
                detection.confidence
            ),
            "model_version": (
                detection.model_version
            ),
            "error": detection.error,
            "orchestration": orchestration,
        }

        return self._write_audit(
            payload
        )

    def _audit_failure(
        self,
        *,
        request_id: str,
        source: str,
        detection: DetectionServiceResult,
    ) -> Dict[str, Any]:
        """
        Record a detection failure.
        """

        if not self.config.audit_enabled:
            return {
                "enabled": False,
                "written": False,
                "reason": (
                    "Audit disabled by configuration."
                ),
            }

        payload = {
            "event_type": (
                "INTELLIGENCE_DETECTION_FAILURE"
            ),
            "request_id": request_id,
            "source": source,
            "timestamp": self._utc_now(),
            "decision": detection.decision,
            "error": detection.error,
        }

        return self._write_audit(
            payload
        )

    def _write_audit(
        self,
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Write an audit payload through a compatibility boundary.

        The audit subsystem must never be allowed to crash
        the intelligence pipeline.
        """

        try:
            if self.audit_logger is None:
                return {
                    "enabled": True,
                    "written": False,
                    "reason": (
                        "No audit logger configured."
                    ),
                }

            for method_name in (
                "log_event",
                "record",
                "write",
                "log",
                "audit",
            ):
                method = getattr(
                    self.audit_logger,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                try:
                    result = method(
                        dict(payload)
                    )

                except TypeError:
                    result = method(
                        event_type=payload.get(
                            "event_type"
                        ),
                        data=dict(payload),
                    )

                return {
                    "enabled": True,
                    "written": True,
                    "method": method_name,
                    "result": self._safe_json(
                        result
                    ),
                }

            return {
                "enabled": True,
                "written": False,
                "reason": (
                    "Audit logger does not expose "
                    "a supported interface."
                ),
            }

        except Exception:
            logger.exception(
                "Audit operation failed."
            )

            self._record_error(
                "audit_failure"
            )

            return {
                "enabled": True,
                "written": False,
                "reason": (
                    "Audit subsystem failed safely."
                ),
            }

    # ======================================================================
    # SECURITY SEMANTICS
    # ======================================================================

    @staticmethod
    def _is_threat(
        detection: DetectionServiceResult,
    ) -> bool:
        """
        Determine threat state from DetectionService decision.

        DetectionService remains the primary security decision
        authority.
        """

        decision = (
            str(
                detection.decision
            )
            .strip()
            .upper()
        )

        return decision in {
            ALERT,
            ESCALATE,
        }

    @staticmethod
    def _derive_severity(
        detection: DetectionServiceResult,
    ) -> str:
        """
        Derive presentation-level severity.

        This does not redefine DetectionService policy.
        """

        decision = (
            str(
                detection.decision
            )
            .strip()
            .upper()
        )

        if decision == ESCALATE:
            return "CRITICAL"

        if decision == ALERT:
            probability = (
                detection.threat_probability
            )

            if (
                probability is not None
                and probability >= 0.90
            ):
                return "HIGH"

            return "MEDIUM"

        return "LOW"

    @staticmethod
    def _derive_risk_score(
        detection: DetectionServiceResult,
    ) -> float:
        """
        Produce an orchestration-level normalized risk signal.

        Important:

        This is not model accuracy.

        This is not probability calibration.

        This is not a confidence interval.

        It is simply a bounded runtime signal used by
        the control-plane result.
        """

        probability = (
            IntelligenceEngine._safe_score(
                detection.threat_probability
            )
        )

        anomaly = (
            IntelligenceEngine._safe_score(
                detection.anomaly_score
            )
        )

        confidence = (
            IntelligenceEngine._safe_score(
                detection.confidence
            )
        )

        score = max(
            probability,
            anomaly,
            confidence,
        )

        return round(
            score,
            4,
        )

    @staticmethod
    def _recommended_action(
        decision: Any,
    ) -> str:
        """
        Translate a decision into deferred action intent.
        """

        normalized = (
            str(decision)
            .strip()
            .upper()
            if decision is not None
            else IGNORE
        )

        if normalized == ESCALATE:
            return "ESCALATE_FOR_REVIEW"

        if normalized == ALERT:
            return "ALERT_SECURITY_OPERATOR"

        return NO_ACTION

    # ======================================================================
    # METADATA
    # ======================================================================

    def _build_metadata(
        self,
        *,
        source: str,
        event: Mapping[str, Any],
        within_target: bool,
        response_intent: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Build operational metadata without duplicating
        the raw event.
        """

        metadata: Dict[str, Any] = {
            "source": source,
            "processing_target_ms": (
                self.config.processing_target_ms
            ),
            "within_processing_target": (
                within_target
            ),
            "automatic_response_enabled": (
                self.config.automatic_response_enabled
            ),
            "response_execution": (
                "DISABLED_BY_ENGINE"
            ),
            "detection_service": (
                type(
                    self.detection_service
                ).__name__
                if self.detection_service
                is not None
                else None
            ),
            "decision_orchestrator": (
                type(
                    self.decision_orchestrator
                ).__name__
                if self.decision_orchestrator
                is not None
                else None
            ),
        }

        if self.config.include_event_metadata:
            metadata[
                "event_field_count"
            ] = len(event)

        if response_intent is not None:
            metadata[
                "response_intent"
            ] = dict(
                response_intent
            )

        return metadata

    # ======================================================================
    # TELEMETRY
    # ======================================================================

    def _record_success(
        self,
        result: EngineResult,
    ) -> None:
        """
        Record successful processing telemetry.
        """

        with self._lock:
            self.successful_events += 1

            self._record_timing(
                result.processing_time_ms
            )

            if result.threat_detected:
                self.detected_threats += 1

            response_level = (
                result.response_level
            )

            if response_level == (
                ResponseLevel.ALERT.value
            ):
                self.alert_decisions += 1

            elif response_level == (
                ResponseLevel.ESCALATE.value
            ):
                self.escalate_decisions += 1

            elif response_level == (
                ResponseLevel.NONE.value
            ):
                self.ignore_decisions += 1

            elif response_level == (
                ResponseLevel.MONITOR.value
            ):
                self.monitor_decisions += 1

            self.threat_types[
                result.threat_type
            ] = (
                self.threat_types.get(
                    result.threat_type,
                    0,
                )
                + 1
            )

            self.severity_counts[
                result.severity
            ] = (
                self.severity_counts.get(
                    result.severity,
                    0,
                )
                + 1
            )

    def _record_failure(
        self,
        result: EngineResult,
    ) -> None:
        """
        Record failed processing telemetry.
        """

        with self._lock:
            self.failed_events += 1

            self._record_timing(
                result.processing_time_ms
            )

    def _record_rejected(
        self,
        result: EngineResult,
    ) -> None:
        """
        Record rejected input telemetry.
        """

        with self._lock:
            self.rejected_events += 1

            self._record_timing(
                result.processing_time_ms
            )

    def _record_timing(
        self,
        processing_ms: float,
    ) -> None:
        """
        Update runtime timing telemetry.
        """

        self.total_processing_ms += (
            processing_ms
        )

        self.max_processing_ms = max(
            self.max_processing_ms,
            processing_ms,
        )

    def _record_error(
        self,
        error_type: str,
    ) -> None:
        """
        Record a categorized internal error.
        """

        with self._lock:
            self.error_types[
                error_type
            ] = (
                self.error_types.get(
                    error_type,
                    0,
                )
                + 1
            )

    # ======================================================================
    # STATUS
    # ======================================================================

    def get_status(
        self,
    ) -> Dict[str, Any]:
        """
        Return operational status.

        Observed detection rate is runtime telemetry only.
        """

        with self._lock:
            total = self.total_events

            detection_rate = (
                self.detected_threats / total
                if total
                else 0.0
            )

            success_rate = (
                self.successful_events / total
                if total
                else 0.0
            )

            average_processing_ms = (
                self.total_processing_ms / total
                if total
                else 0.0
            )

            telemetry = {
                "total_events": (
                    self.total_events
                ),
                "successful_events": (
                    self.successful_events
                ),
                "failed_events": (
                    self.failed_events
                ),
                "rejected_events": (
                    self.rejected_events
                ),
                "detected_threats": (
                    self.detected_threats
                ),
                "observed_detection_rate": round(
                    detection_rate,
                    6,
                ),
                "processing_success_rate": round(
                    success_rate,
                    6,
                ),
                "average_processing_ms": round(
                    average_processing_ms,
                    3,
                ),
                "max_processing_ms": round(
                    self.max_processing_ms,
                    3,
                ),
                "alert_decisions": (
                    self.alert_decisions
                ),
                "escalate_decisions": (
                    self.escalate_decisions
                ),
                "ignore_decisions": (
                    self.ignore_decisions
                ),
                "monitor_decisions": (
                    self.monitor_decisions
                ),
                "threat_types": dict(
                    self.threat_types
                ),
                "severity_counts": dict(
                    self.severity_counts
                ),
                "error_types": dict(
                    self.error_types
                ),
            }

        return {
            "engine": ENGINE_NAME,
            "version": self.VERSION,
            "enabled": self.config.enabled,
            "created_at": self.created_at,
            "configuration": {
                "processing_target_ms": (
                    self.config.processing_target_ms
                ),
                "automatic_response_enabled": (
                    self.config.automatic_response_enabled
                ),
                "audit_enabled": (
                    self.config.audit_enabled
                ),
                "max_event_size": (
                    self.config.max_event_size
                ),
                "max_batch_size": (
                    self.config.max_batch_size
                ),
            },
            "dependencies": {
                "detection_service_available": (
                    self.detection_service
                    is not None
                ),
                "decision_orchestrator_available": (
                    self.decision_orchestrator
                    is not None
                ),
                "detector_available": (
                    self._detector_available()
                ),
            },
            "telemetry": telemetry,
            "semantic_notes": {
                "observed_detection_rate": (
                    "Runtime event telemetry; "
                    "not ML model accuracy."
                ),
                "model_accuracy": (
                    "Owned by the training and "
                    "evaluation layer."
                ),
                "automatic_response": (
                    "Execution is not performed "
                    "by IntelligenceEngine."
                ),
                "detector_inference": (
                    "Owned by DetectionService."
                ),
            },
        }

    # ======================================================================
    # HEALTH
    # ======================================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:
        """
        Return compact control-plane health.
        """

        detection_service_available = (
            self.detection_service
            is not None
        )

        orchestrator_available = (
            self.decision_orchestrator
            is not None
        )

        detector_available = (
            self._detector_available()
        )

        healthy = bool(
            self.config.enabled
            and detection_service_available
            and orchestrator_available
            and detector_available
        )

        return {
            "healthy": healthy,
            "status": (
                "HEALTHY"
                if healthy
                else "DEGRADED"
            ),
            "engine": {
                "name": ENGINE_NAME,
                "available": True,
                "enabled": self.config.enabled,
                "version": self.VERSION,
            },
            "dependencies": {
                "detector": {
                    "available": (
                        detector_available
                    ),
                },
                "detection_service": {
                    "available": (
                        detection_service_available
                    ),
                },
                "decision_orchestrator": {
                    "available": (
                        orchestrator_available
                    ),
                },
            },
            "automatic_response": {
                "enabled": (
                    self.config.automatic_response_enabled
                ),
                "executed_by_engine": False,
            },
        }

    def _detector_available(
        self,
    ) -> bool:
        """
        Determine whether a detector is available.

        DetectionService may encapsulate the detector.
        """

        if self.detector is not None:
            return True

        service = self.detection_service

        if service is None:
            return False

        for attribute_name in (
            "_detector",
            "detector",
        ):
            internal_detector = getattr(
                service,
                attribute_name,
                None,
            )

            if internal_detector is not None:
                return True

        return False

    # ======================================================================
    # FAILURE HANDLING
    # ======================================================================

    def _handle_detection_failure(
        self,
        *,
        request_id: str,
        source: str,
        detection: DetectionServiceResult,
        started: float,
        event: Mapping[str, Any],
    ) -> EngineResult:
        """
        Convert DetectionService failure into a safe result.
        """

        elapsed_ms = self._elapsed_ms(
            started
        )

        audit_result = self._audit_failure(
            request_id=request_id,
            source=source,
            detection=detection,
        )

        result = EngineResult(
            request_id=request_id,
            timestamp=self._utc_now(),
            status=EngineStatus.FAILED.value,
            processing_time_ms=round(
                elapsed_ms,
                3,
            ),
            threat_detected=False,
            threat_type=UNKNOWN,
            severity=UNKNOWN,
            risk_score=0.0,
            confidence=self._safe_score(
                detection.confidence
            ),
            recommended_action=NO_ACTION,
            response_level=ResponseLevel.NONE.value,
            detection=self._safe_dict(
                detection.to_dict()
            ),
            orchestration={},
            audit=audit_result,
            metadata=self._build_metadata(
                source=source,
                event=event,
                within_target=(
                    elapsed_ms
                    <= self.config.processing_target_ms
                ),
            ),
            engine_version=self.VERSION,
            error=(
                detection.error
                or "Detection service failed."
            ),
        )

        self._record_error(
            "detection_failure"
        )

        self._record_failure(
            result
        )

        return result

    def _handle_internal_failure(
        self,
        *,
        request_id: str,
        source: str,
        started: float,
        exception: Exception,
    ) -> EngineResult:
        """
        Convert unexpected exceptions into a safe result.

        Internal exception details are logged server-side but
        are intentionally not exposed through the public error
        field.
        """

        elapsed_ms = self._elapsed_ms(
            started
        )

        logger.exception(
            "IntelligenceEngine internal failure | "
            "request_id=%s",
            request_id,
        )

        self._record_error(
            "internal_processing_error"
        )

        result = EngineResult(
            request_id=request_id,
            timestamp=self._utc_now(),
            status=EngineStatus.FAILED.value,
            processing_time_ms=round(
                elapsed_ms,
                3,
            ),
            threat_detected=False,
            threat_type=UNKNOWN,
            severity=UNKNOWN,
            risk_score=0.0,
            confidence=0.0,
            recommended_action=NO_ACTION,
            response_level=ResponseLevel.NONE.value,
            detection={},
            orchestration={},
            audit={},
            metadata={
                "source": source,
                "failure_mode": SAFE_FAILURE,
            },
            engine_version=self.VERSION,
            error=(
                "Internal intelligence processing error."
            ),
        )

        self._record_failure(
            result
        )

        return result

    # ======================================================================
    # RESULT BUILDERS
    # ======================================================================

    def _build_rejected_result(
        self,
        *,
        request_id: str,
        started: float,
        reason: str,
        source: str,
    ) -> EngineResult:
        """
        Build a safe rejected-input result.
        """

        elapsed_ms = self._elapsed_ms(
            started
        )

        return EngineResult(
            request_id=request_id,
            timestamp=self._utc_now(),
            status=EngineStatus.REJECTED.value,
            processing_time_ms=round(
                elapsed_ms,
                3,
            ),
            threat_detected=False,
            threat_type=UNKNOWN,
            severity=UNKNOWN,
            risk_score=0.0,
            confidence=0.0,
            recommended_action=NO_ACTION,
            response_level=ResponseLevel.NONE.value,
            detection={},
            orchestration={},
            audit={},
            metadata={
                "source": source,
                "failure_mode": "input_rejected",
            },
            engine_version=self.VERSION,
            error=reason,
        )

    def _build_failed_result(
        self,
        *,
        request_id: str,
        started: float,
        reason: str,
        source: str,
    ) -> EngineResult:
        """
        Build a safe dependency-failure result.
        """

        elapsed_ms = self._elapsed_ms(
            started
        )

        return EngineResult(
            request_id=request_id,
            timestamp=self._utc_now(),
            status=EngineStatus.FAILED.value,
            processing_time_ms=round(
                elapsed_ms,
                3,
            ),
            threat_detected=False,
            threat_type=UNKNOWN,
            severity=UNKNOWN,
            risk_score=0.0,
            confidence=0.0,
            recommended_action=NO_ACTION,
            response_level=ResponseLevel.NONE.value,
            detection={},
            orchestration={},
            audit={},
            metadata={
                "source": source,
                "failure_mode": (
                    "dependency_failure"
                ),
            },
            engine_version=self.VERSION,
            error=reason,
        )

    # ======================================================================
    # REQUEST CORRELATION
    # ======================================================================

    def _generate_request_id(
        self,
        event: Any,
    ) -> str:
        """
        Generate a correlation identifier.

        Format:

            <prefix>-<event-digest>-<random>

        The digest provides deterministic context while the UUID
        component prevents collisions between identical events.
        """

        try:
            if isinstance(
                event,
                Mapping,
            ):
                payload = json.dumps(
                    dict(event),
                    sort_keys=True,
                    default=str,
                    ensure_ascii=False,
                ).encode("utf-8")

            else:
                payload = str(
                    event
                ).encode("utf-8")

            digest = hashlib.sha256(
                payload
            ).hexdigest()[:16]

        except Exception:
            digest = "unavailable"

        return (
            f"{self.config.request_id_prefix}-"
            f"{digest}-"
            f"{uuid.uuid4().hex[:12]}"
        )

    # ======================================================================
    # SAFE HELPERS
    # ======================================================================

    @staticmethod
    def _safe_score(
        value: Any,
    ) -> float:
        """
        Normalize a score to [0, 1].

        Invalid, non-finite, and boolean values become 0.
        """

        if value is None:
            return 0.0

        if isinstance(
            value,
            bool,
        ):
            return 0.0

        try:
            numeric = float(
                value
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0

        if not math.isfinite(
            numeric
        ):
            return 0.0

        return round(
            max(
                0.0,
                min(
                    1.0,
                    numeric,
                ),
            ),
            6,
        )

    @staticmethod
    def _optional_float(
        value: Any,
    ) -> Optional[float]:
        """
        Safely convert a value to finite float.
        """

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            return None

        try:
            numeric = float(
                value
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None

        if not math.isfinite(
            numeric
        ):
            return None

        return numeric

    @staticmethod
    def _string_or_none(
        value: Any,
    ) -> Optional[str]:
        """
        Safely convert optional values to strings.
        """

        if value is None:
            return None

        try:
            return str(
                value
            )
        except Exception:
            return None

    @staticmethod
    def _extract_value(
        source: Any,
        key: str,
    ) -> Any:
        """
        Extract a value from either mapping or object.
        """

        if isinstance(
            source,
            Mapping,
        ):
            return source.get(
                key
            )

        return getattr(
            source,
            key,
            None,
        )

    @staticmethod
    def _safe_json(
        value: Any,
    ) -> Any:
        """
        Convert arbitrary values into JSON-safe data.
        """

        try:
            json.dumps(
                value,
                ensure_ascii=False,
            )

            return value

        except (
            TypeError,
            ValueError,
        ):
            try:
                return json.loads(
                    json.dumps(
                        value,
                        default=str,
                        ensure_ascii=False,
                    )
                )

            except Exception:
                return str(
                    value
                )

    @staticmethod
    def _safe_dict(
        value: Any,
    ) -> Dict[str, Any]:
        """
        Convert arbitrary structured data into a dictionary.
        """

        safe = IntelligenceEngine._safe_json(
            value
        )

        if isinstance(
            safe,
            dict,
        ):
            return safe

        return {
            "value": safe
        }

    @staticmethod
    def _elapsed_ms(
        started: float,
    ) -> float:
        """
        Return elapsed wall-clock processing time in milliseconds.
        """

        return (
            time.perf_counter()
            - started
        ) * 1000.0

    @staticmethod
    def _utc_now() -> str:
        """
        Return an ISO-8601 UTC timestamp.
        """

        return datetime.now(
            timezone.utc
        ).isoformat()


# ============================================================================
# DEFAULT ENGINE CONSTRUCTION
# ============================================================================


def _build_default_engine() -> IntelligenceEngine:
    """
    Construct the process-level default engine.


    Detector initialization is intentionally defensive.


    Supports detector implementations exposed as:


        - detector instance
        - Detector class
        - ThreatDetector class
        - factory function


    The engine must remain import-safe.
    """


    default_detector = None


    try:
        from . import detector as detector_module


        # Existing instance style
        if hasattr(
            detector_module,
            "detector",
        ):
            default_detector = (
                detector_module.detector
            )


        # Class style
        elif hasattr(
            detector_module,
            "Detector",
        ):
            detector_class = (
                detector_module.Detector
            )


            default_detector = (
                detector_class()
            )


        # Alternative naming
        elif hasattr(
            detector_module,
            "ThreatDetector",
        ):
            detector_class = (
                detector_module.ThreatDetector
            )


            default_detector = (
                detector_class()
            )


    except Exception:
        logger.exception(
            "Unable to initialize default Detector."
        )


        default_detector = None


    return IntelligenceEngine(
        detector_instance=default_detector
    )

# ============================================================================
# SELF TEST
# ============================================================================


def self_test() -> bool:
    """
    Execute an isolated integration self-test.

    The test uses fake dependencies and therefore requires:

        - no real model
        - no model registry
        - no filesystem persistence
        - no network
        - no security action

    Returns:

        True  -> all assertions passed
        False -> test failure
    """

    print("=" * 72)
    print(
        "EnterpriseGuard - Intelligence Engine Self-Test"
    )
    print("=" * 72)

    # ======================================================================
    # Fake Detection Service
    # ======================================================================

    class FakeDetectionService:

        def __init__(self) -> None:
            self.calls = 0

        def analyze(
            self,
            events: Sequence[
                Mapping[str, Any]
            ],
        ) -> DetectionServiceResult:

            self.calls += 1

            assert isinstance(
                events,
                Sequence,
            )

            assert len(events) == 1

            assert isinstance(
                events[0],
                Mapping,
            )

            return DetectionServiceResult(
                decision=ESCALATE,
                predicted_class="threat",
                threat_probability=0.95,
                benign_probability=0.05,
                anomaly_score=0.90,
                confidence=0.96,
                model_version="self-test-model",
                error=None,
            )

    # ======================================================================
    # Fake Orchestrator
    # ======================================================================

    class FakeDecisionOrchestrator:

        def __init__(self) -> None:
            self.calls = 0

        def handle(
            self,
            detection: DetectionServiceResult,
        ) -> Mapping[str, Any]:

            self.calls += 1

            assert (
                detection.decision
                == ESCALATE
            )

            return {
                "decision": ESCALATE,
                "approved": True,
                "execution": "DEFERRED",
            }

    # ======================================================================
    # Fake Audit
    # ======================================================================

    class FakeAuditLogger:

        def __init__(self) -> None:
            self.events = []

        def log_event(
            self,
            payload: Mapping[str, Any],
        ) -> Mapping[str, Any]:

            self.events.append(
                dict(payload)
            )

            return {
                "recorded": True
            }

    # ======================================================================
    # Build Test Engine
    # ======================================================================

    fake_detection = (
        FakeDetectionService()
    )

    fake_orchestrator = (
        FakeDecisionOrchestrator()
    )

    fake_audit = (
        FakeAuditLogger()
    )

    engine = IntelligenceEngine(
        detection_service_instance=(
            fake_detection
        ),
        decision_orchestrator_instance=(
            fake_orchestrator
        ),
        audit_logger_instance=(
            fake_audit
        ),
    )

    # ======================================================================
    # Single Event
    # ======================================================================

    result = engine.process_event(
        {
            "event_type": "authentication",
            "user": "self-test-user",
            "source_ip": "192.0.2.10",
            "failed_attempts": 12,
        },
        source="self-test",
    )

    assert (
        result.status
        == EngineStatus.SUCCESS.value
    )

    assert result.threat_detected is True

    assert (
        result.threat_type
        == THREAT
    )

    assert (
        result.severity
        == "CRITICAL"
    )

    assert (
        result.response_level
        == ResponseLevel.ESCALATE.value
    )

    assert (
        result.recommended_action
        == "ESCALATE_FOR_REVIEW"
    )

    assert (
        result.risk_score
        == 0.96
    )

    assert (
        result.metadata[
            "response_intent"
        ]["executed"]
        is False
    )

    assert (
        fake_detection.calls
        == 1
    )

    assert (
        fake_orchestrator.calls
        == 1
    )

    assert (
        len(fake_audit.events)
        == 1
    )

    # ======================================================================
    # Batch
    # ======================================================================

    batch = engine.process_batch(
        [
            {
                "event_type": "authentication",
                "user": "user-a",
            },
            {
                "event_type": "authentication",
                "user": "user-b",
            },
        ],
        source="self-test-batch",
    )

    assert (
        batch["processed"]
        == 2
    )

    assert (
        batch["successful"]
        == 2
    )

    assert (
        batch["failed"]
        == 0
    )

    assert (
        batch["rejected"]
        == 0
    )

    assert (
        batch["threats_detected"]
        == 2
    )

    # ======================================================================
    # Invalid Event
    # ======================================================================

    rejected = engine.process_event(
        None,  # type: ignore[arg-type]
        source="self-test",
    )

    assert (
        rejected.status
        == EngineStatus.REJECTED.value
    )

    assert (
        rejected.threat_detected
        is False
    )

    # ======================================================================
    # Health
    # ======================================================================

    health = engine.health_check()

    assert health["healthy"] is False

    # The fake detection service does not expose an internal
    # detector. That is intentional: health must distinguish
    # the detector dependency from the detection-service dependency.

    # ======================================================================
    # Status
    # ======================================================================

    status = engine.get_status()

    assert (
        status["telemetry"][
            "total_events"
        ]
        == 4
    )

    assert (
        status["telemetry"][
            "successful_events"
        ]
        == 3
    )

    assert (
        status["telemetry"][
            "rejected_events"
        ]
        == 1
    )

    print(
        "[PASS] Single-event processing"
    )

    print(
        "[PASS] DetectionService boundary"
    )

    print(
        "[PASS] DecisionOrchestrator boundary"
    )

    print(
        "[PASS] Deferred response intent"
    )

    print(
        "[PASS] Audit isolation"
    )

    print(
        "[PASS] Batch processing"
    )

    print(
        "[PASS] Input rejection"
    )

    print(
        "[PASS] Runtime telemetry"
    )

    print(
        "[PASS] Health reporting"
    )

    print("=" * 72)
    print(
        "SELF-TEST PASSED"
    )
    print("=" * 72)

    return True


# ============================================================================
# DIRECT EXECUTION
# ============================================================================


if __name__ == "__main__":
    self_test()