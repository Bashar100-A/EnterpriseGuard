"""
EnterpriseGuard - Audit Logging Subsystem
==========================================


Central audit and security-event recording layer for EnterpriseGuard.


Responsibilities
-----------------
- Record structured security and system events.
- Persist events using JSON Lines (JSONL).
- Protect sensitive metadata through sanitization.
- Provide tamper-evident hash chaining.
- Verify audit-log integrity.
- Provide thread-safe writes.
- Expose operational statistics.
- Provide a compatibility API for the Intelligence Engine.
- Remain independent from detection, ML, and response execution.


Architecture
------------


    Intelligence Engine
            |
            v
       Audit Logger
            |
            +----> JSONL persistence
            |
            +----> Hash chain
            |
            +----> Integrity verification
            |
            +----> Operational telemetry


Security note
-------------
The hash chain provides tamper-evidence, not authenticity.


A SHA-256 hash does not prove who created the log or prevent an attacker
with write access from rewriting the entire chain. Stronger authenticity
can later be added through signed audit records or an external immutable
logging system.
"""


from __future__ import annotations


import hashlib
import json
import logging
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional




# ============================================================================
# MODULE METADATA
# ============================================================================


__all__ = [
    "AuditEvent",
    "AuditLogger",
    "audit_logger",
]




logger = logging.getLogger(__name__)




# ============================================================================
# AUDIT EVENT
# ============================================================================




@dataclass(frozen=True)
class AuditEvent:
    """
    Immutable structured audit event.


    Every persisted event contains an event hash which is calculated from
    the event payload and the hash of the immediately preceding event.
    """


    event_id: str
    timestamp: str
    event_type: str
    action: str
    outcome: str
    severity: str


    actor_id: Optional[str]
    actor_ip: Optional[str]
    resource: Optional[str]


    message: str


    metadata: Dict[str, Any]


    event_hash: str = ""


    previous_hash: str = ""


    correlation_id: Optional[str] = None


    source: Optional[str] = None


    schema_version: int = 1


    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-compatible dictionary representation."""


        return asdict(self)




# ============================================================================
# AUDIT LOGGER
# ============================================================================




class AuditLogger:
    """
    EnterpriseGuard audit logging subsystem.


    Features
    --------
    - Structured JSONL persistence
    - UTC timestamps
    - SHA-256 tamper-evident hash chaining
    - Thread-safe writes
    - Sensitive-data sanitization
    - Intelligence Engine compatibility API
    - Integrity verification
    - Operational statistics
    - Event retrieval
    """


    VERSION = "2.0.0"


    SCHEMA_VERSION = 1


    DEFAULT_EVENT_TYPE = "system"


    SENSITIVE_KEYS = {
        "password",
        "passwd",
        "passphrase",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "authorization",
        "proxy_authorization",
        "cookie",
        "set_cookie",
        "api_key",
        "apikey",
        "private_key",
        "master_key",
        "client_secret",
        "credential",
        "credentials",
    }


    # ------------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------------


    def __init__(
        self,
        log_directory: str = "logs",
        filename: str = "audit.jsonl",
    ) -> None:


        self.log_directory = Path(log_directory)


        self.log_file = self.log_directory / filename


        self._lock = threading.RLock()


        self._last_hash = ""


        self._events_written = 0


        self._events_failed = 0


        self._severity_counts: Dict[str, int] = {}


        self._event_type_counts: Dict[str, int] = {}


        self.log_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        self.logger = logging.getLogger(
            "enterpriseguard.audit"
        )


        self._configure_logger()


        # Recover the last hash from an existing audit log.
        self._recover_chain_state()


        logger.info(
            "EnterpriseGuard Audit Logger initialized | "
            "version=%s | file=%s",
            self.VERSION,
            self.log_file,
        )


    # ------------------------------------------------------------------------
    # LOGGER CONFIGURATION
    # ------------------------------------------------------------------------


    def _configure_logger(self) -> None:
        """
        Configure the standard-library logger without duplicating handlers.
        """


        if not self.logger.handlers:


            handler = logging.StreamHandler()


            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | "
                "%(name)s | %(message)s"
            )


            handler.setFormatter(formatter)


            self.logger.addHandler(handler)


        self.logger.setLevel(logging.INFO)


        self.logger.propagate = False


    # ------------------------------------------------------------------------
    # PUBLIC API - GENERIC RECORD
    # ------------------------------------------------------------------------


    def record(
        self,
        event_type: str,
        action: str,
        outcome: str,
        severity: str = "INFO",
        actor_id: Optional[str] = None,
        actor_ip: Optional[str] = None,
        resource: Optional[str] = None,
        message: str = "",
        metadata: Optional[Mapping[str, Any]] = None,
        *,
        correlation_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> AuditEvent:
        """
        Record one structured audit event.


        Parameters are deliberately explicit so callers can produce
        semantically meaningful audit records.
        """


        sanitized_metadata = self._sanitize(
            dict(metadata or {})
        )


        normalized_event_type = self._normalize_text(
            event_type,
            default=self.DEFAULT_EVENT_TYPE,
        )


        normalized_action = self._normalize_text(
            action,
            default="UNKNOWN_ACTION",
        )


        normalized_outcome = self._normalize_text(
            outcome,
            default="UNKNOWN",
        )


        normalized_severity = self._normalize_severity(
            severity
        )


        timestamp = self._utc_now()


        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            event_type=normalized_event_type,
            action=normalized_action,
            outcome=normalized_outcome,
            severity=normalized_severity,
            actor_id=actor_id,
            actor_ip=actor_ip,
            resource=resource,
            message=str(message or ""),
            metadata=sanitized_metadata,
            event_hash="",
            previous_hash=self._last_hash,
            correlation_id=correlation_id,
            source=source,
            schema_version=self.SCHEMA_VERSION,
        )


        event_hash = self._calculate_hash(
            event,
            previous_hash=self._last_hash,
        )


        event = AuditEvent(
            **{
                **event.to_dict(),
                "event_hash": event_hash,
            }
        )


        try:


            self._write(event)


        except Exception:


            with self._lock:
                self._events_failed += 1


            raise


        return event


    # ------------------------------------------------------------------------
    # PUBLIC API - INTELLIGENCE ENGINE COMPATIBILITY
    # ------------------------------------------------------------------------


    def log_event(
        self,
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Compatibility interface for IntelligenceEngine.


        The Intelligence Engine can provide a single structured payload:


            {
                "request_id": "...",
                "source": "...",
                "event_type": "THREAT_DETECTION",
                "threat_detected": True,
                "threat_type": "CREDENTIAL_STUFFING",
                "severity": "CRITICAL",
                "risk_score": 98.07,
                "confidence": 91.61,
                "recommended_action": "ISOLATE_AND_ESCALATE"
            }


        This method converts that payload into a durable AuditEvent.
        """


        if not isinstance(payload, Mapping):


            raise TypeError(
                "Audit event payload must be a mapping."
            )


        metadata = dict(payload)


        event_type = str(
            payload.get(
                "event_type",
                "SECURITY_EVENT",
            )
        )


        action = str(
            payload.get(
                "recommended_action",
                payload.get(
                    "action",
                    "DETECTION",
                ),
            )
        )


        threat_detected = bool(
            payload.get(
                "threat_detected",
                False,
            )
        )


        outcome = (
            "THREAT_DETECTED"
            if threat_detected
            else "NO_THREAT"
        )


        severity = str(
            payload.get(
                "severity",
                "INFO",
            )
        )


        message = (
            f"EnterpriseGuard detection event: "
            f"{payload.get('threat_type', 'UNKNOWN')}"
        )


        event = self.record(
            event_type=event_type,
            action=action,
            outcome=outcome,
            severity=severity,
            actor_id=payload.get("actor_id"),
            actor_ip=payload.get("actor_ip"),
            resource=payload.get("resource"),
            message=message,
            metadata=metadata,
            correlation_id=payload.get(
                "request_id"
            ),
            source=payload.get(
                "source",
                "intelligence-engine",
            ),
        )


        return {
            "success": True,
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "event_hash": event.event_hash,
            "previous_hash": event.previous_hash,
            "event_type": event.event_type,
            "severity": event.severity,
        }


    # ------------------------------------------------------------------------
    # PUBLIC API - SECURITY EVENTS
    # ------------------------------------------------------------------------


    def security_event(
        self,
        action: str,
        outcome: str,
        severity: str = "HIGH",
        message: str = "",
        actor_id: Optional[str] = None,
        actor_ip: Optional[str] = None,
        resource: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> AuditEvent:


        return self.record(
            event_type="security",
            action=action,
            outcome=outcome,
            severity=severity,
            actor_id=actor_id,
            actor_ip=actor_ip,
            resource=resource,
            message=message,
            metadata=metadata,
        )


    # ------------------------------------------------------------------------
    # PUBLIC API - AUTHENTICATION EVENTS
    # ------------------------------------------------------------------------


    def authentication_event(
        self,
        action: str,
        outcome: str,
        actor_id: Optional[str] = None,
        actor_ip: Optional[str] = None,
        message: str = "",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> AuditEvent:


        severity = (
            "INFO"
            if str(outcome).lower() == "success"
            else "WARNING"
        )


        return self.record(
            event_type="authentication",
            action=action,
            outcome=outcome,
            severity=severity,
            actor_id=actor_id,
            actor_ip=actor_ip,
            message=message,
            metadata=metadata,
        )


    # ------------------------------------------------------------------------
    # PUBLIC API - SYSTEM EVENTS
    # ------------------------------------------------------------------------


    def system_event(
        self,
        action: str,
        outcome: str = "success",
        severity: str = "INFO",
        message: str = "",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> AuditEvent:


        return self.record(
            event_type="system",
            action=action,
            outcome=outcome,
            severity=severity,
            message=message,
            metadata=metadata,
        )


    # ------------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------------


    def _write(
        self,
        event: AuditEvent,
    ) -> None:


        serialized = json.dumps(
            event.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )


        with self._lock:


            with self.log_file.open(
                "a",
                encoding="utf-8",
                newline="\n",
            ) as file:


                file.write(
                    serialized + "\n"
                )


                file.flush()


            self._last_hash = event.event_hash


            self._events_written += 1


            self._severity_counts[
                event.severity
            ] = (
                self._severity_counts.get(
                    event.severity,
                    0,
                )
                + 1
            )


            self._event_type_counts[
                event.event_type
            ] = (
                self._event_type_counts.get(
                    event.event_type,
                    0,
                )
                + 1
            )


        log_level = self._severity_to_level(
            event.severity
        )


        self.logger.log(
            log_level,
            "%s | %s | %s | %s",
            event.event_type,
            event.action,
            event.outcome,
            event.message,
        )


    # ------------------------------------------------------------------------
    # HASHING
    # ------------------------------------------------------------------------


    def _calculate_hash(
        self,
        event: AuditEvent,
        *,
        previous_hash: str,
    ) -> str:


        payload = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "action": event.action,
            "outcome": event.outcome,
            "severity": event.severity,
            "actor_id": event.actor_id,
            "actor_ip": event.actor_ip,
            "resource": event.resource,
            "message": event.message,
            "metadata": event.metadata,
            "previous_hash": previous_hash,
            "correlation_id": event.correlation_id,
            "source": event.source,
            "schema_version": event.schema_version,
        }


        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")


        return hashlib.sha256(
            canonical
        ).hexdigest()


    # ------------------------------------------------------------------------
    # CHAIN RECOVERY
    # ------------------------------------------------------------------------


    def _recover_chain_state(self) -> None:
        """
        Recover the last persisted hash after application restart.


        Without this step, a new application process would start a new
        chain with an empty previous hash and break continuity.
        """


        if not self.log_file.exists():


            self._last_hash = ""


            return


        try:


            last_non_empty_line = None


            with self.log_file.open(
                "r",
                encoding="utf-8",
            ) as file:


                for line in file:


                    if line.strip():
                        last_non_empty_line = line


            if not last_non_empty_line:


                self._last_hash = ""


                return


            data = json.loads(
                last_non_empty_line
            )


            self._last_hash = str(
                data.get(
                    "event_hash",
                    "",
                )
            )


        except Exception as exc:


            logger.warning(
                "Unable to recover audit chain state: %s",
                exc,
            )


            self._last_hash = ""


    # ------------------------------------------------------------------------
    # SANITIZATION
    # ------------------------------------------------------------------------


    def _sanitize(
        self,
        value: Any,
    ) -> Any:


        if isinstance(value, Mapping):


            result: Dict[str, Any] = {}


            for key, item in value.items():


                normalized_key = str(
                    key
                ).strip().lower()


                if normalized_key in self.SENSITIVE_KEYS:


                    result[str(key)] = "[REDACTED]"


                else:


                    result[str(key)] = (
                        self._sanitize(item)
                    )


            return result


        if isinstance(value, list):


            return [
                self._sanitize(item)
                for item in value
            ]


        if isinstance(value, tuple):


            return [
                self._sanitize(item)
                for item in value
            ]


        if isinstance(value, set):


            return [
                self._sanitize(item)
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
        ) or value is None:


            return value


        return str(value)


    # ------------------------------------------------------------------------
    # NORMALIZATION
    # ------------------------------------------------------------------------


    @staticmethod
    def _normalize_text(
        value: Any,
        *,
        default: str,
    ) -> str:


        text = str(
            value
            if value is not None
            else ""
        ).strip()


        return text or default


    @staticmethod
    def _normalize_severity(
        severity: Any,
    ) -> str:


        normalized = str(
            severity
            if severity is not None
            else "INFO"
        ).strip().upper()


        allowed = {
            "DEBUG",
            "INFO",
            "LOW",
            "WARNING",
            "MEDIUM",
            "ERROR",
            "HIGH",
            "CRITICAL",
        }


        return (
            normalized
            if normalized in allowed
            else "INFO"
        )


    # ------------------------------------------------------------------------
    # SEVERITY MAPPING
    # ------------------------------------------------------------------------


    @staticmethod
    def _severity_to_level(
        severity: str,
    ) -> int:


        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "LOW": logging.INFO,
            "WARNING": logging.WARNING,
            "MEDIUM": logging.WARNING,
            "ERROR": logging.ERROR,
            "HIGH": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }


        return levels.get(
            severity.upper(),
            logging.INFO,
        )


    # ------------------------------------------------------------------------
    # INTEGRITY VERIFICATION
    # ------------------------------------------------------------------------


    def verify_integrity(
        self,
    ) -> Dict[str, Any]:
        """
        Verify the complete audit hash chain.


        Returns
        -------
        dict
            {
                "valid": bool,
                "events_checked": int,
                "error": Optional[str]
            }
        """


        if not self.log_file.exists():


            return {
                "valid": True,
                "events_checked": 0,
                "error": None,
            }


        previous_hash = ""


        events_checked = 0


        try:


            with self._lock:


                with self.log_file.open(
                    "r",
                    encoding="utf-8",
                ) as file:


                    for line_number, line in enumerate(
                        file,
                        start=1,
                    ):


                        if not line.strip():
                            continue


                        data = json.loads(line)


                        stored_hash = str(
                            data.get(
                                "event_hash",
                                "",
                            )
                        )


                        data_without_hash = dict(
                            data
                        )


                        data_without_hash[
                            "event_hash"
                        ] = ""


                        event = AuditEvent(
                            **data_without_hash
                        )


                        expected_hash = (
                            self._calculate_hash(
                                event,
                                previous_hash=previous_hash,
                            )
                        )


                        if stored_hash != expected_hash:


                            return {
                                "valid": False,
                                "events_checked": events_checked,
                                "error": (
                                    "Audit chain integrity "
                                    f"failure at line "
                                    f"{line_number}"
                                ),
                            }


                        previous_hash = stored_hash


                        events_checked += 1


            return {
                "valid": True,
                "events_checked": events_checked,
                "error": None,
            }


        except Exception as exc:


            return {
                "valid": False,
                "events_checked": events_checked,
                "error": str(exc),
            }


    # ------------------------------------------------------------------------
    # EVENT READING
    # ------------------------------------------------------------------------


    def read_events(
        self,
        limit: Optional[int] = None,
    ) -> list[Dict[str, Any]]:
        """
        Read persisted audit events.


        Newest events are returned first.
        """


        if not self.log_file.exists():


            return []


        events: list[Dict[str, Any]] = []


        with self._lock:


            with self.log_file.open(
                "r",
                encoding="utf-8",
            ) as file:


                for line in file:


                    if not line.strip():
                        continue


                    try:


                        events.append(
                            json.loads(line)
                        )


                    except json.JSONDecodeError:


                        continue


        events.reverse()


        if limit is not None:


            if limit < 0:


                raise ValueError(
                    "limit cannot be negative."
                )


            events = events[:limit]


        return events


    # ------------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------------


    def get_status(
        self,
    ) -> Dict[str, Any]:
        """Return operational audit subsystem status."""


        with self._lock:


            return {
                "logger": (
                    "EnterpriseGuard Audit Logger"
                ),
                "version": self.VERSION,
                "schema_version": self.SCHEMA_VERSION,
                "status": "active",
                "log_directory": str(
                    self.log_directory
                ),
                "log_file": str(
                    self.log_file
                ),
                "log_exists": (
                    self.log_file.exists()
                ),
                "events_written": (
                    self._events_written
                ),
                "events_failed": (
                    self._events_failed
                ),
                "last_hash_available": bool(
                    self._last_hash
                ),
                "severity_counts": dict(
                    self._severity_counts
                ),
                "event_type_counts": dict(
                    self._event_type_counts
                ),
            }


    # ------------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------------


    @staticmethod
    def _utc_now() -> str:


        return datetime.now(
            timezone.utc
        ).isoformat()


    # ------------------------------------------------------------------------
    # SELF TEST
    # ------------------------------------------------------------------------


    def self_test(
        self,
    ) -> Dict[str, Any]:
        """
        Execute a focused audit subsystem self-test.


        The test writes a temporary-style operational event into the
        configured audit stream, verifies sanitization, verifies the hash
        chain, and confirms the event can be read back.
        """


        test_event = self.record(
            event_type="SELF_TEST",
            action="AUDIT_SELF_TEST",
            outcome="SUCCESS",
            severity="INFO",
            actor_id="enterpriseguard-self-test",
            message="Audit subsystem self-test.",
            metadata={
                "test": True,
                "password": "this-must-not-be-stored",
                "token": "this-must-not-be-stored",
                "nested": {
                    "api_key": "this-must-not-be-stored",
                },
            },
            source="audit-self-test",
        )


        integrity = self.verify_integrity()


        recent_events = self.read_events(
            limit=1
        )


        latest = (
            recent_events[0]
            if recent_events
            else {}
        )


        sanitized = (
            latest.get(
                "metadata",
                {}
            ).get("password")
            == "[REDACTED]"
        )


        token_sanitized = (
            latest.get(
                "metadata",
                {}
            ).get("token")
            == "[REDACTED]"
        )


        return {
            "success": (
                integrity["valid"]
                and test_event.event_hash != ""
                and latest.get(
                    "event_id"
                )
                == test_event.event_id
                and sanitized
                and token_sanitized
            ),
            "event_written": True,
            "event_id": test_event.event_id,
            "hash_available": bool(
                test_event.event_hash
            ),
            "sanitization_successful": (
                sanitized
                and token_sanitized
            ),
            "integrity": integrity,
        }




# ============================================================================
# DEFAULT LOGGER INSTANCE
# ============================================================================




audit_logger = AuditLogger(
    log_directory=os.getenv(
        "ENTERPRISEGUARD_AUDIT_DIR",
        "logs",
    )
)




# ============================================================================
# MODULE SELF TEST
# ============================================================================




def _self_test() -> None:
    """Run the standalone Audit Logger self-test."""


    print()
    print("=" * 78)
    print(
        "EnterpriseGuard Audit Logger - "
        "Integration Self Test"
    )
    print("=" * 78)


    print()
    print("[1] Audit status")


    print(
        json.dumps(
            audit_logger.get_status(),
            indent=4,
            ensure_ascii=False,
        )
    )


    print()
    print("[2] Recording security event")


    event = audit_logger.security_event(
        action="THREAT_DETECTED",
        outcome="DETECTED",
        severity="CRITICAL",
        message=(
            "EnterpriseGuard detected a simulated "
            "credential-stuffing event."
        ),
        actor_id="self-test",
        actor_ip="127.0.0.1",
        resource="authentication-service",
        metadata={
            "threat_type": "CREDENTIAL_STUFFING",
            "risk_score": 98.07,
            "password": "REDACTED_TEST_VALUE",
            "token": "REDACTED_TEST_VALUE",
        },
    )


    print(
        json.dumps(
            event.to_dict(),
            indent=4,
            ensure_ascii=False,
        )
    )


    print()
    print("[3] Integrity verification")


    integrity = (
        audit_logger.verify_integrity()
    )


    print(
        json.dumps(
            integrity,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()
    print("[4] Reading latest audit event")


    latest = audit_logger.read_events(
        limit=1
    )


    print(
        json.dumps(
            latest,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()
    print("[5] Sanitization verification")


    latest_metadata = (
        latest[0].get(
            "metadata",
            {},
        )
        if latest
        else {}
    )


    sanitization_result = {
        "password_redacted": (
            latest_metadata.get(
                "password"
            )
            == "[REDACTED]"
        ),
        "token_redacted": (
            latest_metadata.get(
                "token"
            )
            == "[REDACTED]"
        ),
    }


    print(
        json.dumps(
            sanitization_result,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()
    print("[6] Compatibility API")


    compatibility = audit_logger.log_event(
        {
            "request_id": "AUDIT-SELFTEST-001",
            "source": "self-test",
            "event_type": "THREAT_DETECTION",
            "threat_detected": True,
            "threat_type": "CREDENTIAL_STUFFING",
            "severity": "CRITICAL",
            "risk_score": 98.07,
            "confidence": 91.61,
            "recommended_action": (
                "ISOLATE_AND_ESCALATE"
            ),
        }
    )


    print(
        json.dumps(
            compatibility,
            indent=4,
            ensure_ascii=False,
        )
    )


    print()
    print("[7] Final verification")


    final_integrity = (
        audit_logger.verify_integrity()
    )


    status = audit_logger.get_status()


    verification = {
        "audit_logger_active": (
            status["status"] == "active"
        ),
        "log_file_exists": (
            status["log_exists"]
        ),
        "event_written": (
            status["events_written"] > 0
        ),
        "hash_chain_active": (
            status["last_hash_available"]
        ),
        "integrity_valid": (
            final_integrity["valid"]
        ),
        "events_checked": (
            final_integrity["events_checked"]
        ),
        "compatibility_api_successful": (
            compatibility["success"]
        ),
        "sanitization_successful": (
            sanitization_result[
                "password_redacted"
            ]
            and sanitization_result[
                "token_redacted"
            ]
        ),
    }


    print(
        json.dumps(
            verification,
            indent=4,
            ensure_ascii=False,
        )
    )


    success = all(
        verification.values()
    )


    print()


    print("=" * 78)


    if success:


        print(
            "Audit Logger self test "
            "completed successfully."
        )


    else:


        print(
            "Audit Logger self test FAILED."
        )


    print("=" * 78)


    if not success:


        raise RuntimeError(
            "EnterpriseGuard Audit Logger "
            "self-test failed."
        )




# ============================================================================
# ENTRY POINT
# ============================================================================




if __name__ == "__main__":
    _self_test()