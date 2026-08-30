"""
EnterpriseGuard - Response Audit Engine
=======================================


Purpose
-------
Provides an immutable, structured, security-focused audit layer for the
EnterpriseGuard Response subsystem.


Responsibilities
----------------
- Record response planning events.
- Record response execution events.
- Record verification results.
- Preserve correlation between request / response / execution / verification.
- Provide deterministic event identifiers.
- Provide tamper-evident event chaining.
- Support JSON serialization.
- Provide filtering and querying.
- Maintain operational statistics.
- Enforce input-size and event-count limits.
- Never execute security actions.
- Never execute shell commands.
- Never modify the operating system.
- Remain safe in DRY_RUN environments.


Architecture
------------
                    +----------------------+
                    | Response Engine      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Response Executor    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Verification Engine  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Response Audit       |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Structured Events    |
                    +----------------------+


Design Principles
-----------------
1. Audit is observational only.
2. Audit must never become an execution path.
3. Every event receives a unique event identifier.
4. Events are hash chained to provide tamper evidence.
5. Correlation identifiers are preserved.
6. Sensitive values are redacted before persistence.
7. Audit failures must not silently become successful security operations.
8. The subsystem is usable independently and through integration hooks.


This module intentionally uses only Python standard-library functionality.
"""


from __future__ import annotations


import hashlib
import json
import re
import threading
import time
import uuid


from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence




# ============================================================================
# Constants
# ============================================================================


ENGINE_NAME = "EnterpriseGuard Response Audit Engine"
ENGINE_VERSION = "1.0.0"


DEFAULT_MAX_INPUT_SIZE = 1_000_000
DEFAULT_MAX_EVENTS = 100_000


GENESIS_HASH = "0" * 64


SAFE_STRING_MAX_LENGTH = 4096


SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|passwd|pwd|secret|token|api[_-]?key|"
    r"access[_-]?key|private[_-]?key|authorization|cookie|"
    r"credential|session[_-]?id|refresh[_-]?token)",
    re.IGNORECASE,
)


ID_PATTERN = re.compile(
    r"^[A-Za-z0-9._:-]{1,256}$"
)




# ============================================================================
# Utility functions
# ============================================================================




def _utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()




def _generate_id(prefix: str) -> str:
    """Generate a compact enterprise identifier."""
    return f"{prefix}-{uuid.uuid4().hex.upper()}"




def _safe_text(value: Any, maximum: int = SAFE_STRING_MAX_LENGTH) -> str:
    """Convert arbitrary values into bounded text."""
    text = str(value)


    if len(text) <= maximum:
        return text


    return text[:maximum] + "...[TRUNCATED]"




def _validate_identifier(value: Any, field_name: str) -> str:
    """Validate correlation identifiers."""
    if value is None:
        raise ValueError(f"{field_name} cannot be empty.")


    text = _safe_text(value, 256)


    if not ID_PATTERN.fullmatch(text):
        raise ValueError(f"Invalid {field_name}.")


    return text




def _canonical_json(value: Any) -> str:
    """Create deterministic JSON suitable for hashing."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )




def _sha256(value: Any) -> str:
    """Calculate SHA-256 over canonical JSON."""
    payload = _canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()




def _is_sensitive_key(key: Any) -> bool:
    """Determine whether a mapping key contains sensitive information."""
    return bool(SENSITIVE_KEY_PATTERN.search(str(key)))




def _redact(value: Any, depth: int = 0) -> Any:
    """
    Recursively redact sensitive information.


    The audit subsystem should preserve security-relevant structure while
    avoiding accidental storage of secrets.
    """


    if depth > 12:
        return "[MAX_DEPTH_REACHED]"


    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}


        for key, item in value.items():
            key_text = _safe_text(key, 256)


            if _is_sensitive_key(key_text):
                result[key_text] = "[REDACTED]"
            else:
                result[key_text] = _redact(item, depth + 1)


        return result


    if isinstance(value, (list, tuple, set)):
        return [_redact(item, depth + 1) for item in value]


    if isinstance(value, bytes):
        return "[BINARY_DATA_REDACTED]"


    if isinstance(value, str):
        return _safe_text(value)


    if isinstance(value, (int, float, bool)) or value is None:
        return value


    return _safe_text(value)




def _json_size(value: Any) -> int:
    """Return serialized UTF-8 size."""
    return len(
        _canonical_json(value).encode("utf-8")
    )




# ============================================================================
# Data model
# ============================================================================




@dataclass(frozen=True)
class AuditEvent:
    """
    Immutable representation of a single audit event.
    """


    event_id: str
    timestamp: str


    event_type: str
    event_category: str


    request_id: Optional[str]
    response_id: Optional[str]
    execution_id: Optional[str]
    verification_id: Optional[str]


    actor: str
    source: str


    outcome: str


    details: Dict[str, Any]


    previous_event_hash: str
    event_hash: str


    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


    schema_version: str = "1.0"




# ============================================================================
# Audit Engine
# ============================================================================




class ResponseAuditEngine:
    """
    Structured and tamper-evident audit engine.


    Important:
        This class records observations only. It does not execute response
        actions, shell commands, network operations, process operations, or
        account modifications.
    """


    def __init__(
        self,
        *,
        enabled: bool = True,
        audit_enabled: bool = True,
        max_input_size: int = DEFAULT_MAX_INPUT_SIZE,
        max_events: int = DEFAULT_MAX_EVENTS,
        persistent_path: Optional[str | Path] = None,
        redact_sensitive_data: bool = True,
    ) -> None:


        if max_input_size <= 0:
            raise ValueError("max_input_size must be greater than zero.")


        if max_events <= 0:
            raise ValueError("max_events must be greater than zero.")


        self.enabled = bool(enabled)
        self.audit_enabled = bool(audit_enabled)


        self.max_input_size = int(max_input_size)
        self.max_events = int(max_events)


        self.redact_sensitive_data = bool(redact_sensitive_data)


        self.persistent_path = (
            Path(persistent_path)
            if persistent_path is not None
            else None
        )


        self._lock = threading.RLock()


        self._events: List[AuditEvent] = []


        self._last_event_hash = GENESIS_HASH


        self._event_type_counts: Counter[str] = Counter()
        self._category_counts: Counter[str] = Counter()
        self._outcome_counts: Counter[str] = Counter()


        self._total_events = 0
        self._accepted_events = 0
        self._rejected_events = 0
        self._persistence_failures = 0


        self._total_processing_ms = 0.0
        self._max_processing_ms = 0.0


    # ---------------------------------------------------------------------
    # Safety properties
    # ---------------------------------------------------------------------


    @property
    def executes_security_actions(self) -> bool:
        return False


    @property
    def shell_execution_enabled(self) -> bool:
        return False


    @property
    def network_operations_enabled(self) -> bool:
        return False


    @property
    def process_operations_enabled(self) -> bool:
        return False


    @property
    def account_modification_enabled(self) -> bool:
        return False


    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------


    def _validate_payload(self, payload: Any) -> Any:
        """
        Validate and optionally redact an audit payload.
        """


        if payload is None:
            return {}


        prepared = (
            _redact(payload)
            if self.redact_sensitive_data
            else payload
        )


        size = _json_size(prepared)


        if size > self.max_input_size:
            raise ValueError(
                "Audit payload exceeds maximum allowed input size."
            )


        return prepared


    # ---------------------------------------------------------------------
    # Event hash
    # ---------------------------------------------------------------------


    def _calculate_event_hash(
        self,
        *,
        event_id: str,
        timestamp: str,
        event_type: str,
        event_category: str,
        request_id: Optional[str],
        response_id: Optional[str],
        execution_id: Optional[str],
        verification_id: Optional[str],
        actor: str,
        source: str,
        outcome: str,
        details: Mapping[str, Any],
        previous_event_hash: str,
    ) -> str:


        canonical_event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "event_category": event_category,
            "request_id": request_id,
            "response_id": response_id,
            "execution_id": execution_id,
            "verification_id": verification_id,
            "actor": actor,
            "source": source,
            "outcome": outcome,
            "details": details,
            "previous_event_hash": previous_event_hash,
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "schema_version": "1.0",
        }


        return _sha256(canonical_event)


    # ---------------------------------------------------------------------
    # Core recording
    # ---------------------------------------------------------------------


    def record_event(
        self,
        *,
        event_type: str,
        event_category: str,
        outcome: str,
        details: Optional[Mapping[str, Any]] = None,
        request_id: Optional[str] = None,
        response_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        actor: str = "system",
        source: str = "response",
        event_id: Optional[str] = None,
    ) -> Dict[str, Any]:


        started = time.perf_counter()


        try:
            if not self.enabled or not self.audit_enabled:
                return {
                    "success": False,
                    "recorded": False,
                    "reason": "Audit engine is disabled.",
                    "event": None,
                }


            event_type = _safe_text(event_type, 128).upper()
            event_category = _safe_text(event_category, 128).upper()
            outcome = _safe_text(outcome, 128).upper()
            actor = _safe_text(actor, 256)
            source = _safe_text(source, 256)


            if request_id is not None:
                request_id = _validate_identifier(
                    request_id,
                    "request_id",
                )


            if response_id is not None:
                response_id = _validate_identifier(
                    response_id,
                    "response_id",
                )


            if execution_id is not None:
                execution_id = _validate_identifier(
                    execution_id,
                    "execution_id",
                )


            if verification_id is not None:
                verification_id = _validate_identifier(
                    verification_id,
                    "verification_id",
                )


            prepared_details = self._validate_payload(details or {})


            with self._lock:


                if len(self._events) >= self.max_events:
                    self._rejected_events += 1


                    return {
                        "success": False,
                        "recorded": False,
                        "reason": "Maximum audit event capacity reached.",
                        "event": None,
                    }


                event_id = (
                    _safe_text(event_id, 128)
                    if event_id
                    else _generate_id("AE")
                )


                timestamp = _utc_now()


                previous_hash = self._last_event_hash


                event_hash = self._calculate_event_hash(
                    event_id=event_id,
                    timestamp=timestamp,
                    event_type=event_type,
                    event_category=event_category,
                    request_id=request_id,
                    response_id=response_id,
                    execution_id=execution_id,
                    verification_id=verification_id,
                    actor=actor,
                    source=source,
                    outcome=outcome,
                    details=prepared_details,
                    previous_event_hash=previous_hash,
                )


                event = AuditEvent(
                    event_id=event_id,
                    timestamp=timestamp,
                    event_type=event_type,
                    event_category=event_category,
                    request_id=request_id,
                    response_id=response_id,
                    execution_id=execution_id,
                    verification_id=verification_id,
                    actor=actor,
                    source=source,
                    outcome=outcome,
                    details=dict(prepared_details),
                    previous_event_hash=previous_hash,
                    event_hash=event_hash,
                )


                self._events.append(event)


                self._last_event_hash = event_hash


                self._accepted_events += 1
                self._event_type_counts[event_type] += 1
                self._category_counts[event_category] += 1
                self._outcome_counts[outcome] += 1


                persistence = self._persist_event(event)


                if not persistence["success"]:
                    self._persistence_failures += 1


                result = {
                    "success": True,
                    "recorded": True,
                    "event": self.event_to_dict(event),
                    "persistence": persistence,
                }


                return result


        except Exception as exc:
            self._rejected_events += 1


            return {
                "success": False,
                "recorded": False,
                "reason": _safe_text(exc),
                "event": None,
            }


        finally:
            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0


            with self._lock:
                self._total_processing_ms += elapsed_ms
                self._max_processing_ms = max(
                    self._max_processing_ms,
                    elapsed_ms,
                )


    # ---------------------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------------------


    def _persist_event(self, event: AuditEvent) -> Dict[str, Any]:
        """
        Append an event to a JSONL audit file.


        Persistence is intentionally append-only.
        """


        if self.persistent_path is None:
            return {
                "success": True,
                "persisted": False,
                "reason": "No persistent audit path configured.",
            }


        try:
            self.persistent_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )


            with self.persistent_path.open(
                "a",
                encoding="utf-8",
            ) as handle:


                handle.write(
                    json.dumps(
                        self.event_to_dict(event),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )


            return {
                "success": True,
                "persisted": True,
                "path": str(self.persistent_path),
            }


        except Exception as exc:


            return {
                "success": False,
                "persisted": False,
                "reason": _safe_text(exc),
            }


    # ---------------------------------------------------------------------
    # Convenience audit methods
    # ---------------------------------------------------------------------


    def record_response_planned(
        self,
        response: Mapping[str, Any],
        *,
        source: str = "response-engine",
    ) -> Dict[str, Any]:


        return self.record_event(
            event_type="RESPONSE_PLANNED",
            event_category="RESPONSE",
            outcome="PLANNED",
            request_id=response.get("request_id"),
            response_id=response.get("response_id"),
            source=source,
            details=response,
        )


    def record_response_rejected(
        self,
        response: Mapping[str, Any],
        *,
        source: str = "response-engine",
    ) -> Dict[str, Any]:


        return self.record_event(
            event_type="RESPONSE_REJECTED",
            event_category="RESPONSE",
            outcome="REJECTED",
            request_id=response.get("request_id"),
            response_id=response.get("response_id"),
            source=source,
            details=response,
        )


    def record_execution(
        self,
        execution: Mapping[str, Any],
        *,
        source: str = "response-executor",
    ) -> Dict[str, Any]:


        return self.record_event(
            event_type="RESPONSE_EXECUTION",
            event_category="EXECUTION",
            outcome=execution.get("status", "UNKNOWN"),
            request_id=execution.get("request_id"),
            response_id=execution.get("response_id"),
            execution_id=execution.get("execution_id"),
            source=source,
            details=execution,
        )


    def record_verification(
        self,
        verification: Mapping[str, Any],
        *,
        source: str = "response-verification",
    ) -> Dict[str, Any]:


        return self.record_event(
            event_type="RESPONSE_VERIFICATION",
            event_category="VERIFICATION",
            outcome=verification.get("status", "UNKNOWN"),
            request_id=verification.get("request_id"),
            response_id=verification.get("response_id"),
            execution_id=verification.get("execution_id"),
            verification_id=verification.get("verification_id"),
            source=source,
            details=verification,
        )


    def record_security_event(
        self,
        event: Mapping[str, Any],
        *,
        outcome: str = "OBSERVED",
        source: str = "enterpriseguard",
    ) -> Dict[str, Any]:


        return self.record_event(
            event_type="SECURITY_EVENT",
            event_category="SECURITY",
            outcome=outcome,
            request_id=event.get("request_id"),
            response_id=event.get("response_id"),
            execution_id=event.get("execution_id"),
            verification_id=event.get("verification_id"),
            source=source,
            details=event,
        )


    # ---------------------------------------------------------------------
    # Query
    # ---------------------------------------------------------------------


    def query(
        self,
        *,
        event_type: Optional[str] = None,
        event_category: Optional[str] = None,
        outcome: Optional[str] = None,
        request_id: Optional[str] = None,
        response_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:


        if limit <= 0:
            return []


        limit = min(limit, self.max_events)


        with self._lock:


            events: Iterable[AuditEvent] = reversed(self._events)


            result: List[Dict[str, Any]] = []


            for event in events:


                if event_type and event.event_type != event_type.upper():
                    continue


                if (
                    event_category
                    and event.event_category != event_category.upper()
                ):
                    continue


                if outcome and event.outcome != outcome.upper():
                    continue


                if request_id and event.request_id != request_id:
                    continue


                if response_id and event.response_id != response_id:
                    continue


                if execution_id and event.execution_id != execution_id:
                    continue


                if (
                    verification_id
                    and event.verification_id != verification_id
                ):
                    continue


                result.append(self.event_to_dict(event))


                if len(result) >= limit:
                    break


            return result


    # ---------------------------------------------------------------------
    # Correlation
    # ---------------------------------------------------------------------


    def get_correlation_chain(
        self,
        *,
        request_id: Optional[str] = None,
        response_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        verification_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:


        return self.query(
            request_id=request_id,
            response_id=response_id,
            execution_id=execution_id,
            verification_id=verification_id,
            limit=self.max_events,
        )


    # ---------------------------------------------------------------------
    # Integrity verification
    # ---------------------------------------------------------------------


    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify the complete in-memory audit chain.


        No external actions are performed.
        """


        with self._lock:


            previous_hash = GENESIS_HASH
            verified_events = 0


            for event in self._events:


                expected_hash = self._calculate_event_hash(
                    event_id=event.event_id,
                    timestamp=event.timestamp,
                    event_type=event.event_type,
                    event_category=event.event_category,
                    request_id=event.request_id,
                    response_id=event.response_id,
                    execution_id=event.execution_id,
                    verification_id=event.verification_id,
                    actor=event.actor,
                    source=event.source,
                    outcome=event.outcome,
                    details=event.details,
                    previous_event_hash=previous_hash,
                )


                if event.previous_event_hash != previous_hash:
                    return {
                        "valid": False,
                        "verified_events": verified_events,
                        "total_events": len(self._events),
                        "reason": (
                            f"Previous hash mismatch at {event.event_id}."
                        ),
                    }


                if event.event_hash != expected_hash:
                    return {
                        "valid": False,
                        "verified_events": verified_events,
                        "total_events": len(self._events),
                        "reason": (
                            f"Event hash mismatch at {event.event_id}."
                        ),
                    }


                previous_hash = event.event_hash
                verified_events += 1


            return {
                "valid": True,
                "verified_events": verified_events,
                "total_events": len(self._events),
                "root_hash": previous_hash,
                "reason": "Audit chain integrity verified.",
            }


    # ---------------------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------------------


    @staticmethod
    def event_to_dict(event: AuditEvent) -> Dict[str, Any]:
        return asdict(event)


    def export_events(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                self.event_to_dict(event)
                for event in self._events
            ]


    # ---------------------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------------------


    def statistics(self) -> Dict[str, Any]:


        with self._lock:


            average_ms = (
                self._total_processing_ms / self._accepted_events
                if self._accepted_events
                else 0.0
            )


            return {
                "total_events": self._total_events,
                "accepted_events": self._accepted_events,
                "rejected_events": self._rejected_events,
                "persistence_failures": self._persistence_failures,
                "event_type_counts": dict(
                    self._event_type_counts
                ),
                "category_counts": dict(
                    self._category_counts
                ),
                "outcome_counts": dict(
                    self._outcome_counts
                ),
                "average_processing_ms": round(
                    average_ms,
                    3,
                ),
                "max_processing_ms": round(
                    self._max_processing_ms,
                    3,
                ),
                "integrity": self.verify_integrity(),
            }


    # ---------------------------------------------------------------------
    # Status
    # ---------------------------------------------------------------------


    def status(self) -> Dict[str, Any]:


        with self._lock:


            return {
                "engine": ENGINE_NAME,
                "version": ENGINE_VERSION,
                "status": (
                    "active"
                    if self.enabled
                    else "disabled"
                ),
                "configuration": {
                    "enabled": self.enabled,
                    "audit_enabled": self.audit_enabled,
                    "max_input_size": self.max_input_size,
                    "max_events": self.max_events,
                    "redact_sensitive_data": (
                        self.redact_sensitive_data
                    ),
                    "persistent_storage": (
                        self.persistent_path is not None
                    ),
                },
                "statistics": self.statistics(),
                "safety": {
                    "executes_security_actions": False,
                    "shell_execution_enabled": False,
                    "network_operations_enabled": False,
                    "process_operations_enabled": False,
                    "account_modification_enabled": False,
                },
                "integrity": self.verify_integrity(),
                "notes": {
                    "purpose": (
                        "Provide structured, correlated and "
                        "tamper-evident audit records."
                    ),
                    "execution": (
                        "The Audit Engine never executes "
                        "security actions."
                    ),
                    "privacy": (
                        "Sensitive fields are redacted by default."
                    ),
                    "integrity": (
                        "Events are protected by a chained "
                        "SHA-256 integrity mechanism."
                    ),
                },
            }


    # ---------------------------------------------------------------------
    # Health
    # ---------------------------------------------------------------------


    def health_check(self) -> Dict[str, Any]:


        integrity = self.verify_integrity()


        healthy = (
            self.enabled
            and self.audit_enabled
            and integrity["valid"]
            and not self.executes_security_actions
            and not self.shell_execution_enabled
            and not self.network_operations_enabled
            and not self.process_operations_enabled
            and not self.account_modification_enabled
        )


        return {
            "healthy": healthy,
            "engine": {
                "enabled": self.enabled,
                "version": ENGINE_VERSION,
            },
            "audit": {
                "available": self.enabled
                and self.audit_enabled,
                "event_count": len(self._events),
                "persistent_storage": (
                    self.persistent_path is not None
                ),
            },
            "integrity": integrity,
            "safety": {
                "read_only": True,
                "executes_security_actions": False,
                "shell_execution": False,
                "network_operations": False,
                "process_operations": False,
                "account_modification": False,
            },
        }


    # ---------------------------------------------------------------------
    # Reset
    # ---------------------------------------------------------------------


    def clear_memory(self) -> Dict[str, Any]:
        """
        Clear in-memory events.


        This does not delete the persistent audit file.
        """


        with self._lock:


            count = len(self._events)


            self._events.clear()


            self._last_event_hash = GENESIS_HASH


            self._event_type_counts.clear()
            self._category_counts.clear()
            self._outcome_counts.clear()


            self._accepted_events = 0
            self._rejected_events = 0
            self._persistence_failures = 0


            self._total_processing_ms = 0.0
            self._max_processing_ms = 0.0


            return {
                "success": True,
                "cleared_events": count,
                "persistent_storage_modified": False,
            }


    # ---------------------------------------------------------------------
    # Self-test
    # ---------------------------------------------------------------------


    def self_test(self) -> Dict[str, Any]:


        test_engine = ResponseAuditEngine(
            enabled=True,
            audit_enabled=True,
            max_input_size=DEFAULT_MAX_INPUT_SIZE,
            max_events=100,
            persistent_path=None,
            redact_sensitive_data=True,
        )


        checks: Dict[str, bool] = {}


        # 1. Engine health.
        health = test_engine.health_check()


        checks["engine_healthy"] = bool(
            health.get("healthy")
        )


        # 2. Read-only safety.
        checks["read_only_safety"] = (
            test_engine.executes_security_actions is False
            and test_engine.shell_execution_enabled is False
            and test_engine.network_operations_enabled is False
            and test_engine.process_operations_enabled is False
            and test_engine.account_modification_enabled is False
        )


        # 3. Record response event.
        response_event = test_engine.record_response_planned(
            {
                "request_id": "EG-AUDIT-TEST",
                "response_id": "ER-AUDIT-TEST",
                "status": "PLANNED",
                "threat_type": "TEST_THREAT",
                "severity": "HIGH",
            }
        )


        checks["response_event_recorded"] = bool(
            response_event.get("recorded")
        )


        # 4. Record execution.
        execution_event = test_engine.record_execution(
            {
                "request_id": "EG-AUDIT-TEST",
                "response_id": "ER-AUDIT-TEST",
                "execution_id": "EX-AUDIT-TEST",
                "status": "SUCCESS",
                "actions_executed": 0,
                "actions_simulated": 1,
            }
        )


        checks["execution_event_recorded"] = bool(
            execution_event.get("recorded")
        )


        # 5. Record verification.
        verification_event = test_engine.record_verification(
            {
                "request_id": "EG-AUDIT-TEST",
                "response_id": "ER-AUDIT-TEST",
                "execution_id": "EX-AUDIT-TEST",
                "verification_id": "VF-AUDIT-TEST",
                "status": "VERIFIED",
                "verified": True,
            }
        )


        checks["verification_event_recorded"] = bool(
            verification_event.get("recorded")
        )


        # 6. Sensitive information must be redacted.
        sensitive_event = test_engine.record_event(
            event_type="SECURITY_TEST",
            event_category="SAFETY",
            outcome="OBSERVED",
            request_id="EG-AUDIT-SENSITIVE",
            details={
                "username": "test-user",
                "password": "super-secret-password",
                "api_token": "secret-token",
                "normal_value": "preserved",
            },
        )


        sensitive_recorded = sensitive_event.get("event") or {}
        sensitive_details = sensitive_recorded.get(
            "details",
            {},
        )


        checks["sensitive_data_redacted"] = (
            sensitive_details.get("password") == "[REDACTED]"
            and sensitive_details.get("api_token") == "[REDACTED]"
            and sensitive_details.get("normal_value")
            == "preserved"
        )


        # 7. Correlation chain.
        chain = test_engine.get_correlation_chain(
            request_id="EG-AUDIT-TEST"
        )


        checks["correlation_chain_available"] = (
            len(chain) == 3
        )


        # 8. Integrity.
        integrity = test_engine.verify_integrity()


        checks["integrity_valid"] = bool(
            integrity.get("valid")
        )


        # 9. Invalid input.
        invalid = test_engine.record_event(
            event_type="INVALID_TEST",
            event_category="TEST",
            outcome="TEST",
            request_id="invalid id with spaces",
        )


        checks["invalid_input_rejected"] = (
            invalid.get("recorded") is False
        )


        # 10. No shell execution surface.
        checks["no_shell_execution"] = (
            test_engine.shell_execution_enabled is False
        )


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
            "statistics": test_engine.statistics(),
        }




# ============================================================================
# Compatibility aliases
# ============================================================================




ResponseAudit = ResponseAuditEngine
AuditEngine = ResponseAuditEngine




# ============================================================================
# Module-level factory
# ============================================================================




def create_audit_engine(
    *,
    enabled: bool = True,
    audit_enabled: bool = True,
    persistent_path: Optional[str | Path] = None,
) -> ResponseAuditEngine:
    """
    Create a standard EnterpriseGuard Response Audit Engine.
    """


    return ResponseAuditEngine(
        enabled=enabled,
        audit_enabled=audit_enabled,
        persistent_path=persistent_path,
    )




# ============================================================================
# Integration self-test
# ============================================================================




def _print_json(title: str, payload: Mapping[str, Any]) -> None:
    print()
    print(title)
    print(
        json.dumps(
            payload,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )




def _self_test() -> None:


    print()
    print("=" * 78)
    print(
        "EnterpriseGuard Response Audit Engine - Integration Self Test"
    )
    print("=" * 78)


    engine = ResponseAuditEngine()


    # ---------------------------------------------------------------------
    # 1. Status
    # ---------------------------------------------------------------------


    _print_json(
        "[1] Audit engine status",
        engine.status(),
    )


    # ---------------------------------------------------------------------
    # 2. Health
    # ---------------------------------------------------------------------


    health = engine.health_check()


    _print_json(
        "[2] Health check",
        health,
    )


    # ---------------------------------------------------------------------
    # 3. Record response
    # ---------------------------------------------------------------------


    response_result = engine.record_response_planned(
        {
            "request_id": "EG-SELFTEST-RESPONSE",
            "response_id": "ER-SELFTEST-RESPONSE",
            "status": "PLANNED",
            "response_level": "ISOLATE",
            "severity": "CRITICAL",
            "risk_score": 98.5,
            "confidence": 94.2,
            "recommended_action": "ISOLATE_AND_ESCALATE",
        },
        source="self-test",
    )


    _print_json(
        "[3] Response planning audit",
        response_result,
    )


    # ---------------------------------------------------------------------
    # 4. Record execution
    # ---------------------------------------------------------------------


    execution_result = engine.record_execution(
        {
            "request_id": "EG-SELFTEST-RESPONSE",
            "response_id": "ER-SELFTEST-RESPONSE",
            "execution_id": "EX-SELFTEST-RESPONSE",
            "status": "PARTIAL",
            "approval_required": True,
            "approval_level": "SECURITY_ADMIN",
            "actions_requested": 2,
            "actions_executed": 0,
            "actions_simulated": 1,
            "actions_rejected": 1,
            "actions": [
                {
                    "action_id": "EA-SELFTEST-ALERT",
                    "action_type": "CREATE_ALERT",
                    "status": "SIMULATED",
                },
                {
                    "action_id": "EA-SELFTEST-ISOLATE",
                    "action_type": "ISOLATE",
                    "status": "REJECTED",
                },
            ],
        },
        source="self-test",
    )


    _print_json(
        "[4] Response execution audit",
        execution_result,
    )


    # ---------------------------------------------------------------------
    # 5. Record verification
    # ---------------------------------------------------------------------


    verification_result = engine.record_verification(
        {
            "request_id": "EG-SELFTEST-RESPONSE",
            "response_id": "ER-SELFTEST-RESPONSE",
            "execution_id": "EX-SELFTEST-RESPONSE",
            "verification_id": "VF-SELFTEST-RESPONSE",
            "status": "PARTIAL",
            "verified": False,
            "actions_verified": 1,
            "actions_failed": 1,
            "reason": "Isolation action was not executed.",
        },
        source="self-test",
    )


    _print_json(
        "[5] Response verification audit",
        verification_result,
    )


    # ---------------------------------------------------------------------
    # 6. Sensitive-data protection
    # ---------------------------------------------------------------------


    sensitive_result = engine.record_security_event(
        {
            "request_id": "EG-SELFTEST-SENSITIVE",
            "event_type": "CREDENTIAL_EVENT",
            "username": "test-user",
            "password": "DO_NOT_STORE",
            "api_token": "DO_NOT_STORE",
            "severity": "HIGH",
        },
        outcome="OBSERVED",
        source="self-test",
    )


    _print_json(
        "[6] Sensitive data protection",
        sensitive_result,
    )


    # ---------------------------------------------------------------------
    # 7. Correlation
    # ---------------------------------------------------------------------


    correlation = engine.get_correlation_chain(
        request_id="EG-SELFTEST-RESPONSE"
    )


    _print_json(
        "[7] Correlation chain",
        {
            "request_id": "EG-SELFTEST-RESPONSE",
            "event_count": len(correlation),
            "events": correlation,
        },
    )


    # ---------------------------------------------------------------------
    # 8. Integrity
    # ---------------------------------------------------------------------


    integrity = engine.verify_integrity()


    _print_json(
        "[8] Audit chain integrity",
        integrity,
    )


    # ---------------------------------------------------------------------
    # 9. Full self-test
    # ---------------------------------------------------------------------


    test_result = engine.self_test()


    _print_json(
        "[9] Audit engine self test",
        test_result,
    )


    # ---------------------------------------------------------------------
    # 10. Final verification
    # ---------------------------------------------------------------------


    final_checks = {
        "engine_active": engine.status()["status"] == "active",
        "health_check_available": True,
        "health_check_healthy": bool(
            health.get("healthy")
        ),
        "response_audit_recorded": bool(
            response_result.get("recorded")
        ),
        "execution_audit_recorded": bool(
            execution_result.get("recorded")
        ),
        "verification_audit_recorded": bool(
            verification_result.get("recorded")
        ),
        "sensitive_data_redacted": (
            bool(
                (
                    sensitive_result.get("event") or {}
                ).get("details", {}).get("password")
                == "[REDACTED]"
            )
        ),
        "correlation_available": len(correlation) == 3,
        "integrity_valid": bool(
            integrity.get("valid")
        ),
        "read_only_safety": (
            engine.executes_security_actions is False
            and engine.shell_execution_enabled is False
            and engine.network_operations_enabled is False
            and engine.process_operations_enabled is False
            and engine.account_modification_enabled is False
        ),
        "self_test_passed": bool(
            test_result.get("passed")
        ),
    }


    _print_json(
        "[10] Final verification",
        final_checks,
    )


    if not all(final_checks.values()):
        print()
        print("=" * 78)
        print(
            "Response Audit Engine self test FAILED."
        )
        print("=" * 78)


        failed = [
            key
            for key, value in final_checks.items()
            if not value
        ]


        raise RuntimeError(
            "EnterpriseGuard Response Audit Engine "
            "self-test failed. "
            f"Failed checks: {', '.join(failed)}"
        )


    print()
    print("=" * 78)
    print(
        "Response Audit Engine self test completed successfully."
    )
    print("=" * 78)




# ============================================================================
# Module entry point
# ============================================================================




if __name__ == "__main__":
    _self_test()