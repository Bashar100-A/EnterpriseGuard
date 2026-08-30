"""
EnterpriseGuard - Threat Detection / Inference Layer
======================================================

Explainable Detection Boundary.

Responsibilities
----------------

- Validate canonical inference features
- Delegate prediction to ModelManager
- Normalize model output
- Collect explainability information when available
- Collect model metadata when available
- Measure prediction latency
- Return stable DetectionResult contract

Architecture
------------

        Features
            |
            v
        Detector
            |
     +------+------+
     |             |
     v             v
 ModelManager   Explainability
     |
     v
 DetectionResult

"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any, Mapping, Optional, Protocol


# ============================================================================
# Canonical Feature Contract
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

FEATURE_COUNT = len(FEATURE_NAMES)


# ============================================================================
# Prediction Contracts
# ============================================================================


class ModelPredictor(Protocol):
    """
    Minimal prediction contract.
    """

    def predict(
        self,
        features: Mapping[str, Any],
    ) -> Any:
        ...


class ExplainablePredictor(Protocol):
    """
    Optional explainability contract.

    ModelManager may implement this.

    Detector will use it if available,
    otherwise continue normally.
    """

    def explain(
        self,
        features: Mapping[str, Any],
    ) -> Any:
        ...


class MetadataProvider(Protocol):
    """
    Optional model metadata contract.
    """

    def get_metadata(self) -> Any:
        ...


# ============================================================================
# Detection Result
# ============================================================================


@dataclass(frozen=True)
class DetectionResult:
    """
    Stable detection result contract.

    Backward compatible with previous
    EnterpriseGuard DetectionService consumers.
    """

    predicted_class: Optional[Any] = None

    threat_probability: Optional[float] = None

    benign_probability: Optional[float] = None

    anomaly_score: Optional[float] = None

    confidence: Optional[float] = None

    model_version: Optional[str] = None

    error: Optional[str] = None


    # ------------------------------------------------------------------
    # Explainability Extensions
    # ------------------------------------------------------------------

    feature_contribution: Optional[
        dict[str, float]
    ] = None

    shap_values: Optional[
        dict[str, float]
    ] = None


    # ------------------------------------------------------------------
    # Runtime Intelligence Extensions
    # ------------------------------------------------------------------

    model_metadata: Optional[
        dict[str, Any]
    ] = None


    prediction_latency_ms: Optional[
        float
    ] = None


    @property
    def success(self) -> bool:
        return self.error is None


    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================================
# Detector
# ============================================================================


class Detector:
    """
    EnterpriseGuard Detection Boundary.

    Detector owns inference orchestration only.

    It does NOT:

    - train models
    - load models
    - manage registry
    - persist models
    - execute actions
    - make policy decisions
    """

    def __init__(
        self,
        model_manager: ModelPredictor,
    ) -> None:

        if model_manager is None:
            raise TypeError(
                "model_manager must not be None"
            )


        predict_method = getattr(
            model_manager,
            "predict",
            None,
        )


        if not callable(predict_method):
            raise TypeError(
                "model_manager must provide callable predict()"
            )


        self._model_manager = model_manager


    # ------------------------------------------------------------------
    # Public Detection API
    # ------------------------------------------------------------------


    def detect(
        self,
        features: Mapping[str, Any],
    ) -> DetectionResult:
        """
        Execute inference pipeline.
        """


        validation_error = self.validate_features(
            features
        )


        if validation_error:
            return DetectionResult(
                error=validation_error
            )


        start_time = perf_counter()


        try:

            prediction = self._model_manager.predict(
                dict(features)
            )


        except Exception as exc:

            latency = (
                perf_counter()
                -
                start_time
            ) * 1000


            return DetectionResult(
                error=f"Model inference failed: {exc}",
                prediction_latency_ms=latency,
            )


        latency = (
            perf_counter()
            -
            start_time
        ) * 1000


        explainability = self._collect_explainability(
            features
        )


        metadata = self._collect_metadata()


        result = self._normalize_prediction(
            prediction,
            features,
        )


        return DetectionResult(
            **{
                **result.to_dict(),
                "feature_contribution":
                    explainability.get(
                        "feature_contribution"
                    ),

                "shap_values":
                    explainability.get(
                        "shap_values"
                    ),

                "model_metadata":
                    metadata,

                "prediction_latency_ms":
                    latency,
            }
        )
    # ------------------------------------------------------------------
    # Feature Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_features(
        features: Mapping[str, Any],
    ) -> Optional[str]:
        """
        Validate canonical inference contract.
        """

        if not isinstance(features, Mapping):
            return "features must be a mapping"


        missing_features = [
            name
            for name in FEATURE_NAMES
            if name not in features
        ]


        if missing_features:
            return (
                "Missing required features: "
                +
                ", ".join(missing_features)
            )


        return None


    # ------------------------------------------------------------------
    # Explainability Collection
    # ------------------------------------------------------------------

    def _collect_explainability(
        self,
        features: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Collect optional explainability data.

        Supports:

        - SHAP values
        - feature contribution

        Detector never requires explainability
        to complete inference.
        """

        result = {
            "feature_contribution": None,
            "shap_values": None,
        }


        explain_method = getattr(
            self._model_manager,
            "explain",
            None,
        )


        if not callable(explain_method):
            return result


        try:

            explanation = explain_method(
                dict(features)
            )


        except Exception:
            return result


        if explanation is None:
            return result


        if isinstance(explanation, Mapping):

            shap_values = explanation.get(
                "shap_values"
            )

            feature_contribution = explanation.get(
                "feature_contribution"
            )


            if isinstance(
                shap_values,
                Mapping,
            ):
                result[
                    "shap_values"
                ] = _normalize_contribution_map(
                    shap_values
                )


            if isinstance(
                feature_contribution,
                Mapping,
            ):
                result[
                    "feature_contribution"
                ] = _normalize_contribution_map(
                    feature_contribution
                )


        return result



    # ------------------------------------------------------------------
    # Metadata Collection
    # ------------------------------------------------------------------

    def _collect_metadata(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Collect model metadata if available.

        Metadata is informational only.
        """

        metadata_method = getattr(
            self._model_manager,
            "get_metadata",
            None,
        )


        if not callable(metadata_method):
            return None


        try:

            metadata = metadata_method()


        except Exception:

            return None



        if isinstance(
            metadata,
            Mapping,
        ):

            return dict(metadata)


        return None



    # ------------------------------------------------------------------
    # Prediction Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_prediction(
        prediction: Any,
        features: Mapping[str, Any],
    ) -> DetectionResult:
        """
        Normalize arbitrary ModelManager
        output into DetectionResult.
        """


        if prediction is None:

            return DetectionResult(
                anomaly_score=_safe_probability(
                    features.get(
                        "anomaly_score"
                    )
                ),

                error=(
                    "ModelManager.predict() "
                    "returned no result"
                ),
            )



        predicted_class = _extract_value(
            prediction,
            "predicted_class",
        )


        threat_probability = _safe_probability(
            _extract_value(
                prediction,
                "threat_probability",
            )
        )


        benign_probability = _safe_probability(
            _extract_value(
                prediction,
                "benign_probability",
            )
        )


        anomaly_score = _safe_probability(
            _extract_value(
                prediction,
                "anomaly_score",
            )
        )


        confidence = _normalize_confidence(
            _extract_value(
                prediction,
                "confidence",
            ),

            threat_probability=
                threat_probability,

            benign_probability=
                benign_probability,
        )


        model_version = _extract_value(
            prediction,
            "model_version",
        )


        error = _extract_value(
            prediction,
            "error",
        )


        if anomaly_score is None:

            anomaly_score = _safe_probability(
                features.get(
                    "anomaly_score"
                )
            )


        return DetectionResult(

            predicted_class=
                predicted_class,


            threat_probability=
                threat_probability,


            benign_probability=
                benign_probability,


            anomaly_score=
                anomaly_score,


            confidence=
                confidence,


            model_version=
                (
                    str(model_version)
                    if model_version is not None
                    else None
                ),


            error=
                (
                    str(error)
                    if error is not None
                    else None
                ),
        )



# ============================================================================
# Helper Functions
# ============================================================================


def _extract_value(
    source: Any,
    key: str,
) -> Any:
    """
    Extract value from mapping or object.
    """

    if isinstance(
        source,
        Mapping,
    ):

        return source.get(key)


    return getattr(
        source,
        key,
        None,
    )



def _safe_float(
    value: Any,
) -> Optional[float]:

    if value is None:
        return None


    try:

        return float(value)


    except (
        TypeError,
        ValueError,
    ):

        return None



def _safe_probability(
    value: Any,
) -> Optional[float]:
    """
    Normalize probability values.
    """

    number = _safe_float(
        value
    )


    if number is None:
        return None


    if not (
        0.0 <= number <= 1.0
    ):

        return None


    return number



def _normalize_confidence(
    value: Any,
    *,
    threat_probability: Optional[float],
    benign_probability: Optional[float],
) -> Optional[float]:
    """
    Normalize confidence values.

    Supports:

    0.93

    and

    93.0
    """


    number = _safe_float(
        value
    )


    if number is not None:


        if 0.0 <= number <= 1.0:

            return number



        if 1.0 < number <= 100.0:

            return number / 100.0



    candidates = [
        item
        for item in (
            threat_probability,
            benign_probability,
        )

        if item is not None
    ]



    if candidates:

        return max(candidates)



    return None



def _normalize_contribution_map(
    values: Mapping[str, Any],
) -> dict[str, float]:
    """
    Normalize explainability output.

    Used for:

    - SHAP values
    - feature contribution
    """

    result: dict[str, float] = {}


    for key, value in values.items():

        number = _safe_float(
            value
        )


        if number is not None:

            result[
                str(key)
            ] = number



    return result
# ============================================================================
# Self Test
# ============================================================================


def self_test() -> bool:
    """
    Detector isolated self-test.

    Validates:

    - inference
    - backward compatibility
    - latency collection
    - metadata collection
    - explainability support
    - SHAP values
    - validation failures
    """

    features = {
        "request_frequency": 12.0,
        "failure_ratio": 0.45,
        "unique_source_count": 4.0,
        "unique_user_count": 2.0,
        "failed_attempts": 9.0,
        "anomaly_score": 0.87,
        "outbound_data_volume": 1500.0,
    }


    class FakeModelManager:
        """
        Fake production-like ModelManager.
        """


        def predict(
            self,
            features: Mapping[str, Any],
        ) -> dict[str, Any]:

            return {

                "predicted_class":
                    "threat",

                "threat_probability":
                    0.91,

                "benign_probability":
                    0.09,

                "anomaly_score":
                    0.87,

                "confidence":
                    0.91,

                "model_version":
                    "self-test-v1",

                "error":
                    None,
            }



        def explain(
            self,
            features: Mapping[str, Any],
        ) -> dict[str, Any]:

            return {

                "feature_contribution": {

                    "failure_ratio":
                        0.42,

                    "anomaly_score":
                        0.31,

                    "outbound_data_volume":
                        0.18,
                },


                "shap_values": {

                    "failure_ratio":
                        0.40,

                    "anomaly_score":
                        0.35,

                    "request_frequency":
                        0.15,
                },
            }



        def get_metadata(
            self,
        ) -> dict[str, Any]:

            return {

                "algorithm":
                    "RandomForest",

                "framework":
                    "sklearn",

                "dataset_version":
                    "v1",

                "features":
                    7,

                "model_version":
                    "self-test-v1",
            }



    detector = Detector(
        FakeModelManager()
    )


    result = detector.detect(
        features
    )


    assert result.success is True


    assert result.predicted_class == (
        "threat"
    )


    assert result.threat_probability == (
        0.91
    )


    assert result.confidence == (
        0.91
    )


    assert result.model_version == (
        "self-test-v1"
    )


    # ---------------------------------------------------------
    # Explainability
    # ---------------------------------------------------------

    assert (
        result.feature_contribution
        is not None
    )


    assert (
        result.feature_contribution[
            "failure_ratio"
        ]
        ==
        0.42
    )


    assert (
        result.shap_values
        is not None
    )


    assert (
        result.shap_values[
            "anomaly_score"
        ]
        ==
        0.35
    )


    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    assert (
        result.model_metadata
        is not None
    )


    assert (
        result.model_metadata[
            "algorithm"
        ]
        ==
        "RandomForest"
    )


    # ---------------------------------------------------------
    # Latency
    # ---------------------------------------------------------

    assert (
        result.prediction_latency_ms
        is not None
    )


    assert (
        result.prediction_latency_ms
        >=
        0
    )


    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    data = result.to_dict()


    assert isinstance(
        data,
        dict,
    )


    assert (
        "shap_values"
        in data
    )


    assert (
        "model_metadata"
        in data
    )


    assert (
        "prediction_latency_ms"
        in data
    )


    # ---------------------------------------------------------
    # Missing feature test
    # ---------------------------------------------------------

    invalid_features = dict(
        features
    )


    del invalid_features[
        "request_frequency"
    ]


    invalid_result = detector.detect(
        invalid_features
    )


    assert (
        invalid_result.success
        is False
    )


    assert (
        "request_frequency"
        in invalid_result.error
    )


    # ---------------------------------------------------------
    # Invalid manager test
    # ---------------------------------------------------------

    try:

        Detector(
            None  # type: ignore
        )

        raise AssertionError(
            "None manager accepted"
        )


    except TypeError:

        pass



    class InvalidManager:
        pass



    try:

        Detector(
            InvalidManager()
        )

        raise AssertionError(
            "Invalid manager accepted"
        )


    except TypeError:

        pass



    return True



# ============================================================================
# Module Execution
# ============================================================================


if __name__ == "__main__":

    print("=" * 70)

    print(
        "EnterpriseGuard - Detector Self-Test"
    )

    print("=" * 70)



    try:

        self_test()


        print(
            "[PASS] Detector operational"
        )


        print(
            "[PASS] Explainability layer"
        )


        print(
            "[PASS] SHAP contract"
        )


        print(
            "[PASS] Model metadata"
        )


        print(
            "[PASS] Prediction latency"
        )


        print("=" * 70)

        print(
            "SELF-TEST PASSED"
        )

        print("=" * 70)



    except AssertionError as exc:


        print(
            "SELF-TEST FAILED"
        )


        print(
            exc
        )


        raise SystemExit(1)



    except Exception as exc:


        print(
            "SELF-TEST FAILED"
        )


        print(
            f"Unexpected error: {exc}"
        )


        raise SystemExit(1)
        