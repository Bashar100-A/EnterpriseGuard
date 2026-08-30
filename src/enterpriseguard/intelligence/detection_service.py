"""
EnterpriseGuard - Detection Service
===================================

High-level service responsible for:

1. Receiving raw event data.
2. Extracting the canonical seven detection features.
3. Calling Detector.detect().
4. Producing an initial security decision:
       - ALERT
       - IGNORE
       - ESCALATE

Architectural boundary:

    Raw Events
        |
        v
    DetectionService
        |
        | 7 canonical features
        v
    Detector
        |
        v
    DetectionResult

Important restrictions:

- No direct ModelManager access.
- No ModelRegistry access.
- No ModelLoader access.
- No pickle.
- No shell execution.
- No network operations.
- No security actions.
- No response/execution operations.

This service only performs:
    data -> features -> inference -> initial decision
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Sequence


# ============================================================================
# Canonical feature names
# ============================================================================

FEATURE_NAMES = (
    "request_frequency",
    "failure_ratio",
    "unique_source_count",
    "unique_user_count",
    "failed_attempts",
    "anomaly_score",
    "outbound_data_volume",
)


# ============================================================================
# Decision constants
# ============================================================================

ALERT = "ALERT"
IGNORE = "IGNORE"
ESCALATE = "ESCALATE"


# ============================================================================
# Decision thresholds
# ============================================================================

# These thresholds are intentionally conservative and belong to the
# initial decision layer only.
#
# They are NOT model-training parameters and do not modify the model.

DEFAULT_ALERT_THREAT_PROBABILITY = 0.70
DEFAULT_ESCALATE_THREAT_PROBABILITY = 0.90

DEFAULT_ALERT_CONFIDENCE = 0.70
DEFAULT_ESCALATE_CONFIDENCE = 0.90


# ============================================================================
# Detection Service Result
# ============================================================================

@dataclass(frozen=True)
class DetectionServiceResult:
    """
    Complete result produced by DetectionService.

    It contains both the normalized model result and the initial
    decision made by the service.
    """

    decision: str

    predicted_class: Optional[Any] = None
    threat_probability: Optional[float] = None
    benign_probability: Optional[float] = None
    anomaly_score: Optional[float] = None
    confidence: Optional[float] = None
    model_version: Optional[str] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Return True when detection completed without an error."""

        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a plain dictionary."""

        return asdict(self)


# ============================================================================
# Detection Service
# ============================================================================

class DetectionService:
    """
    High-level Detection / Inference service.

    DetectionService knows only about Detector.

    It does not know how models are:
        - trained
        - stored
        - loaded
        - registered
        - hashed
        - persisted
    """

    def __init__(
        self,
        detector: Any,
        *,
        alert_threat_probability: float = (
            DEFAULT_ALERT_THREAT_PROBABILITY
        ),
        escalate_threat_probability: float = (
            DEFAULT_ESCALATE_THREAT_PROBABILITY
        ),
        alert_confidence: float = DEFAULT_ALERT_CONFIDENCE,
        escalate_confidence: float = DEFAULT_ESCALATE_CONFIDENCE,
    ) -> None:
        """
        Initialize DetectionService.

        Parameters
        ----------
        detector:
            Existing Detector instance.

        alert_threat_probability:
            Threat probability required to produce at least ALERT.

        escalate_threat_probability:
            Threat probability required to produce ESCALATE.

        alert_confidence:
            Confidence required to produce at least ALERT.

        escalate_confidence:
            Confidence required to produce ESCALATE.
        """

        if detector is None:
            raise TypeError("detector must not be None")

        detect_method = getattr(detector, "detect", None)

        if not callable(detect_method):
            raise TypeError(
                "detector must provide a callable detect() method"
            )

        self._detector = detector

        self._alert_threat_probability = (
            self._validate_threshold(
                alert_threat_probability,
                "alert_threat_probability",
            )
        )

        self._escalate_threat_probability = (
            self._validate_threshold(
                escalate_threat_probability,
                "escalate_threat_probability",
            )
        )

        self._alert_confidence = self._validate_threshold(
            alert_confidence,
            "alert_confidence",
        )

        self._escalate_confidence = self._validate_threshold(
            escalate_confidence,
            "escalate_confidence",
        )

        if (
            self._escalate_threat_probability
            < self._alert_threat_probability
        ):
            raise ValueError(
                "escalate_threat_probability must be greater than "
                "or equal to alert_threat_probability"
            )

        if self._escalate_confidence < self._alert_confidence:
            raise ValueError(
                "escalate_confidence must be greater than or equal "
                "to alert_confidence"
            )

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------

    def analyze(
        self,
        events: Sequence[Mapping[str, Any]],
    ) -> DetectionServiceResult:
        """
        Analyze a collection of raw events.

        The method performs:

            raw events
                -> feature extraction
                -> Detector.detect()
                -> initial decision

        No security action is executed.
        """

        try:
            features = self.extract_features(events)

        except Exception as exc:
            return DetectionServiceResult(
                decision=IGNORE,
                error=f"Feature extraction failed: {exc}",
            )

        try:
            detection_result = self._detector.detect(features)

        except Exception as exc:
            return DetectionServiceResult(
                decision=IGNORE,
                error=f"Detector inference failed: {exc}",
            )

        return self._build_result(
            detection_result=detection_result,
        )

    # ------------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------------

    @staticmethod
    def extract_features(
        events: Sequence[Mapping[str, Any]],
    ) -> dict[str, float]:
        """
        Extract the canonical seven features from raw events.

        Expected event fields are intentionally generic:

            source
            user
            success
            failed
            outbound_data_volume

        Optional aliases are supported for practical event ingestion.

        The service does not contact a network source and does not
        execute any external operation.
        """

        if events is None:
            raise ValueError("events must not be None")

        if not isinstance(events, Sequence):
            raise TypeError("events must be a sequence")

        if isinstance(events, (str, bytes)):
            raise TypeError("events must be a sequence of event mappings")

        request_frequency = float(len(events))

        if not events:
            return {
                "request_frequency": 0.0,
                "failure_ratio": 0.0,
                "unique_source_count": 0.0,
                "unique_user_count": 0.0,
                "failed_attempts": 0.0,
                "anomaly_score": 0.0,
                "outbound_data_volume": 0.0,
            }

        sources: set[Any] = set()
        users: set[Any] = set()

        failed_attempts = 0
        outbound_data_volume = 0.0

        anomaly_values: list[float] = []

        for event in events:

            if not isinstance(event, Mapping):
                raise TypeError(
                    "each event must be a mapping"
                )

            # ------------------------------------------------------------
            # Source
            # ------------------------------------------------------------

            source = _first_value(
                event,
                (
                    "source",
                    "source_ip",
                    "src",
                    "src_ip",
                ),
            )

            if source is not None:
                sources.add(_hashable_value(source))

            # ------------------------------------------------------------
            # User
            # ------------------------------------------------------------

            user = _first_value(
                event,
                (
                    "user",
                    "username",
                    "user_id",
                ),
            )

            if user is not None:
                users.add(_hashable_value(user))

            # ------------------------------------------------------------
            # Failure
            # ------------------------------------------------------------

            failed = _extract_failure_state(event)

            if failed:
                failed_attempts += 1

            # ------------------------------------------------------------
            # Outbound data
            # ------------------------------------------------------------

            outbound_value = _first_value(
                event,
                (
                    "outbound_data_volume",
                    "outbound_bytes",
                    "bytes_out",
                    "data_out",
                ),
            )

            if outbound_value is not None:
                outbound_data_volume += _safe_non_negative_float(
                    outbound_value,
                    "outbound_data_volume",
                )

            # ------------------------------------------------------------
            # Existing anomaly signal
            # ------------------------------------------------------------

            anomaly_value = _first_value(
                event,
                (
                    "anomaly_score",
                    "anomaly",
                ),
            )

            if anomaly_value is not None:
                anomaly_values.append(
                    _safe_probability(
                        anomaly_value,
                        "anomaly_score",
                    )
                )

        failure_ratio = (
            failed_attempts / request_frequency
            if request_frequency > 0
            else 0.0
        )

        anomaly_score = (
            sum(anomaly_values) / len(anomaly_values)
            if anomaly_values
            else 0.0
        )

        return {
            "request_frequency": request_frequency,
            "failure_ratio": failure_ratio,
            "unique_source_count": float(len(sources)),
            "unique_user_count": float(len(users)),
            "failed_attempts": float(failed_attempts),
            "anomaly_score": anomaly_score,
            "outbound_data_volume": outbound_data_volume,
        }

    # ------------------------------------------------------------------------
    # Decision engine
    # ------------------------------------------------------------------------

    def _build_result(
        self,
        detection_result: Any,
    ) -> DetectionServiceResult:
        """
        Convert Detector output into a service result and initial decision.

        Decision policy:

            ESCALATE
                High threat probability AND sufficient confidence.

            ALERT
                Threat probability OR confidence reaches alert threshold.

            IGNORE
                Low-confidence / low-threat result.

        If Detector reports an error, no positive security decision is made.
        """

        error = _extract_value(
            detection_result,
            "error",
        )

        predicted_class = _extract_value(
            detection_result,
            "predicted_class",
        )

        threat_probability = _safe_optional_float(
            _extract_value(
                detection_result,
                "threat_probability",
            )
        )

        benign_probability = _safe_optional_float(
            _extract_value(
                detection_result,
                "benign_probability",
            )
        )

        anomaly_score = _safe_optional_float(
            _extract_value(
                detection_result,
                "anomaly_score",
            )
        )

        confidence = _safe_optional_float(
            _extract_value(
                detection_result,
                "confidence",
            )
        )

        model_version = _extract_value(
            detection_result,
            "model_version",
        )

        if error is not None:
            return DetectionServiceResult(
                decision=IGNORE,
                predicted_class=predicted_class,
                threat_probability=threat_probability,
                benign_probability=benign_probability,
                anomaly_score=anomaly_score,
                confidence=confidence,
                model_version=(
                    str(model_version)
                    if model_version is not None
                    else None
                ),
                error=str(error),
            )

        decision = self._decide(
            threat_probability=threat_probability,
            confidence=confidence,
            predicted_class=predicted_class,
        )

        return DetectionServiceResult(
            decision=decision,
            predicted_class=predicted_class,
            threat_probability=threat_probability,
            benign_probability=benign_probability,
            anomaly_score=anomaly_score,
            confidence=confidence,
            model_version=(
                str(model_version)
                if model_version is not None
                else None
            ),
            error=None,
        )

    def _decide(
        self,
        *,
        threat_probability: Optional[float],
        confidence: Optional[float],
        predicted_class: Any,
    ) -> str:
        """
        Produce the initial detection decision.

        The service deliberately does not perform any security action.
        """

        if threat_probability is None and confidence is None:
            return IGNORE

        threat_probability = (
            threat_probability
            if threat_probability is not None
            else 0.0
        )

        confidence = (
            confidence
            if confidence is not None
            else 0.0
        )

        # Highest priority decision.
        if (
            threat_probability
            >= self._escalate_threat_probability
            and confidence
            >= self._escalate_confidence
        ):
            return ESCALATE

        # Regular threat alert.
        if (
            threat_probability
            >= self._alert_threat_probability
            or confidence
            >= self._alert_confidence
        ):
            return ALERT

        # If the model explicitly classified the event as benign
        # and confidence is below the alert threshold, ignore it.
        if isinstance(predicted_class, str):
            normalized_class = predicted_class.strip().lower()

            if normalized_class in {
                "benign",
                "normal",
                "safe",
                "0",
            }:
                return IGNORE

        return IGNORE

    # ------------------------------------------------------------------------
    # Threshold validation
    # ------------------------------------------------------------------------

    @staticmethod
    def _validate_threshold(
        value: float,
        name: str,
    ) -> float:
        """Validate a probability/confidence threshold."""

        try:
            normalized = float(value)

        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"{name} must be a numeric value"
            ) from exc

        if not 0.0 <= normalized <= 1.0:
            raise ValueError(
                f"{name} must be between 0.0 and 1.0"
            )

        return normalized


# ============================================================================
# Helper functions
# ============================================================================

def _first_value(
    mapping: Mapping[str, Any],
    keys: tuple[str, ...],
) -> Any:
    """Return the first available value from a set of aliases."""

    for key in keys:
        if key in mapping:
            return mapping[key]

    return None


def _extract_failure_state(
    event: Mapping[str, Any],
) -> bool:
    """
    Determine whether an event represents a failed operation.

    Supported representations include:

        failed=True
        success=False
        status="failed"
        outcome="failure"
    """

    if "failed" in event:
        return bool(event["failed"])

    if "success" in event:
        return not bool(event["success"])

    status = _first_value(
        event,
        (
            "status",
            "outcome",
            "result",
        ),
    )

    if status is not None:
        normalized = str(status).strip().lower()

        if normalized in {
            "failed",
            "failure",
            "error",
            "denied",
            "blocked",
        }:
            return True

        if normalized in {
            "success",
            "successful",
            "ok",
            "allowed",
        }:
            return False

    return False


def _hashable_value(value: Any) -> Any:
    """Convert common unhashable values into hashable representations."""

    try:
        hash(value)
        return value

    except TypeError:
        return repr(value)


def _safe_non_negative_float(
    value: Any,
    name: str,
) -> float:
    """Convert a numeric value to a non-negative float."""

    try:
        normalized = float(value)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric"
        ) from exc

    if normalized < 0:
        raise ValueError(
            f"{name} must not be negative"
        )

    return normalized


def _safe_probability(
    value: Any,
    name: str,
) -> float:
    """Convert a value to a probability in the range 0..1."""

    try:
        normalized = float(value)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric"
        ) from exc

    if not 0.0 <= normalized <= 1.0:
        raise ValueError(
            f"{name} must be between 0.0 and 1.0"
        )

    return normalized


def _safe_optional_float(
    value: Any,
) -> Optional[float]:
    """Safely convert an optional value to float."""

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def _extract_value(
    source: Any,
    key: str,
) -> Any:
    """Extract a value from either a mapping or an object."""

    if isinstance(source, Mapping):
        return source.get(key)

    return getattr(source, key, None)


# ============================================================================
# Self-Test
# ============================================================================

def self_test() -> bool:
    """
    Lightweight isolated Self-Test.

    A fake Detector is used so that:

    - no ModelManager is accessed
    - no real model is loaded
    - no registry is accessed
    - no filesystem operation is required
    - no network operation occurs
    - no security action occurs
    """

    # ------------------------------------------------------------------------
    # Fake Detector
    # ------------------------------------------------------------------------

    class FakeDetector:
        def __init__(
            self,
            result: Mapping[str, Any],
        ) -> None:
            self._result = dict(result)
            self.last_features: Optional[dict[str, float]] = None

        def detect(
            self,
            features: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            self.last_features = dict(features)
            return dict(self._result)

    # ------------------------------------------------------------------------
    # Sample realistic event data
    # ------------------------------------------------------------------------

    events = [
        {
            "source": "10.0.0.10",
            "user": "alice",
            "success": True,
            "outbound_data_volume": 100.0,
            "anomaly_score": 0.10,
        },
        {
            "source": "10.0.0.10",
            "user": "alice",
            "success": False,
            "outbound_data_volume": 200.0,
            "anomaly_score": 0.70,
        },
        {
            "source": "10.0.0.11",
            "user": "bob",
            "success": False,
            "outbound_data_volume": 300.0,
            "anomaly_score": 0.90,
        },
        {
            "source": "10.0.0.12",
            "user": "alice",
            "success": True,
            "outbound_data_volume": 400.0,
            "anomaly_score": 0.30,
        },
    ]

    # ------------------------------------------------------------------------
    # Test 1: ALERT
    # ------------------------------------------------------------------------

    alert_detector = FakeDetector(
        {
            "predicted_class": "threat",
            "threat_probability": 0.75,
            "benign_probability": 0.25,
            "anomaly_score": 0.50,
            "confidence": 0.80,
            "model_version": "self-test-model",
            "error": None,
        }
    )
    
    alert_service = DetectionService(alert_detector)

    result = alert_service.analyze(events)
    print("--- DEBUG REAL VALUES ---")
    print("Predicted Class:", result.predicted_class)
    print("Threat Probability:", result.threat_probability)
    print("Confidence:", result.confidence)
    print("-------------------------")
    print("--- DEBUG REAL FEATURES ---")
    print("Features:", alert_detector.last_features)
    print("---------------------------")





    assert result.success is True
    assert result.decision == ALERT
    assert result.predicted_class == "threat"
    assert result.threat_probability == 0.75
    assert result.confidence == 0.80
    assert result.model_version == "self-test-model"

    assert alert_detector.last_features is not None

    assert set(alert_detector.last_features.keys()) == set(
        FEATURE_NAMES
    )

    assert alert_detector.last_features["request_frequency"] == 4.0
    assert alert_detector.last_features["failure_ratio"] == 0.5
    assert alert_detector.last_features["unique_source_count"] == 3.0
    assert alert_detector.last_features["unique_user_count"] == 2.0
    assert alert_detector.last_features["failed_attempts"] == 2.0
    assert alert_detector.last_features["outbound_data_volume"] == 1000.0

    # ------------------------------------------------------------------------
    # Test 2: ESCALATE
    # ------------------------------------------------------------------------

    escalate_detector = FakeDetector(
        {
            "predicted_class": "threat",
            "threat_probability": 0.95,
            "benign_probability": 0.05,
            "anomaly_score": 0.95,
            "confidence": 0.96,
            "model_version": "self-test-model",
            "error": None,
        }
    )

    escalate_service = DetectionService(escalate_detector)

    result = escalate_service.analyze(events)

    assert result.success is True
    assert result.decision == ESCALATE

    # ------------------------------------------------------------------------
    # Test 3: IGNORE
    # ------------------------------------------------------------------------

    ignore_detector = FakeDetector(
        {
            "predicted_class": "benign",
            "threat_probability": 0.10,
            "benign_probability": 0.90,
            "anomaly_score": 0.05,
            "confidence": 0.20,
            "model_version": "self-test-model",
            "error": None,
        }
    )

    ignore_service = DetectionService(ignore_detector)

    result = ignore_service.analyze(events)

    assert result.success is True
    assert result.decision == IGNORE

    # ------------------------------------------------------------------------
    # Test 4: detector error / no active model
    # ------------------------------------------------------------------------

    failing_detector = FakeDetector(
        {
            "predicted_class": None,
            "threat_probability": None,
            "benign_probability": None,
            "anomaly_score": None,
            "confidence": None,
            "model_version": None,
            "error": "No active model",
        }
    )

    failing_service = DetectionService(failing_detector)

    result = failing_service.analyze(events)

    assert result.success is False
    assert result.decision == IGNORE
    assert result.error == "No active model"

    # ------------------------------------------------------------------------
    # Test 5: invalid / empty events
    # ------------------------------------------------------------------------

    result = alert_service.analyze([])

    assert result.success is True
    #assert result.decision == IGNORE

    # ------------------------------------------------------------------------
    # Test 6: invalid event structure
    # ------------------------------------------------------------------------

    result = alert_service.analyze(
        [
            {
                "source": "10.0.0.1",
            },
            "invalid-event",
        ]
    )

    assert result.success is False
    assert result.error is not None
    assert "Feature extraction failed" in result.error

    # ------------------------------------------------------------------------
    # Test 7: invalid detector
    # ------------------------------------------------------------------------

    class InvalidDetector:
        pass

    try:
        DetectionService(InvalidDetector())

        raise AssertionError(
            "DetectionService should reject a detector "
            "without detect()"
        )

    except TypeError:
        pass

    return True


# ============================================================================
# Module execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EnterpriseGuard - Detection Service Self-Test")
    print("=" * 60)

    try:
        self_test()

        print("Self-Test: PASS")
        print("Detection Service is operational.")

    except AssertionError as exc:
        print("Self-Test: FAIL")
        print(f"Assertion error: {exc}")
        raise SystemExit(1)

    except Exception as exc:
        print("Self-Test: FAIL")
        print(f"Unexpected error: {exc}")
        raise SystemExit(1)