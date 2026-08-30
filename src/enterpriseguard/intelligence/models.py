"""
EnterpriseGuard - Machine Learning Model Layer
================================================


Production-grade ML abstraction for EnterpriseGuard.


Responsibilities
----------------
- Canonical feature contract
- Feature validation and normalization
- Real ML training
- Optional validation evaluation
- Prediction
- Probability estimation
- Safe baseline fallback
- Model lifecycle management
- Atomic model persistence
- Model integrity hashing
- Metadata management
- Runtime statistics
- Thread-safe access
- Compatibility layer
- Self-test


Architecture
------------


    Dataset
       |
       v
    Validation
       |
       v
    EnterpriseGuardModel
       |
       +----------------------+
       |                      |
       v                      v
   Real ML Model        Baseline Fallback
       |                      |
       +----------+-----------+
                  |
                  v
             PredictionResult




Important
---------
- Baseline probability is NOT ML accuracy.
- Training accuracy is NOT validation/test accuracy.
- Validation accuracy is meaningful only when evaluated against
  a separate representative labelled dataset.
- Model persistence uses pickle because scikit-learn estimators
  are Python objects. Never load untrusted model files.
"""


from __future__ import annotations


import hashlib
import json
import math
import os
import pickle
import tempfile
import threading
import time


from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence




# ============================================================================
# Optional ML backend
# ============================================================================


try:
    from sklearn.linear_model import LogisticRegression
except ImportError:  # pragma: no cover
    LogisticRegression = None




# ============================================================================
# Constants
# ============================================================================


MODEL_NAME = "EnterpriseGuard Threat Intelligence Model"


MODEL_VERSION = "3.0.0"


MODEL_SCHEMA_VERSION = 1


FEATURE_NAMES: tuple[str, ...] = (
    "request_frequency",
    "failure_ratio",
    "unique_source_count",
    "unique_user_count",
    "failed_attempts",
    "anomaly_score",
    "outbound_data_volume",
)


FEATURE_COUNT = len(FEATURE_NAMES)


NORMALIZED_FEATURES = frozenset(
    {
        "request_frequency",
        "failure_ratio",
        "unique_source_count",
        "unique_user_count",
        "anomaly_score",
        "outbound_data_volume",
    }
)


MODEL_FILE_NAME = "enterpriseguard_model.pkl"


DEFAULT_MODEL_DIRECTORY = (
    Path(__file__).resolve().parents[3]
    / "assets"
    / "models"
)


PREDICTION_THRESHOLD = 0.50


MAX_FEATURE_VALUE = 1_000_000.0


BASELINE_FAILED_ATTEMPTS_NORMALIZER = 20.0


# Never load an absurdly large model file.
MAX_MODEL_FILE_SIZE = 100 * 1024 * 1024  # 100 MB




# ============================================================================
# Exceptions
# ============================================================================




class FeatureValidationError(ValueError):
    """Raised when input features violate the canonical feature contract."""




class ModelTrainingError(RuntimeError):
    """Raised when model training or evaluation fails."""




class ModelPersistenceError(RuntimeError):
    """Raised when model persistence or loading fails."""




# ============================================================================
# Data Structures
# ============================================================================




@dataclass(frozen=True)
class PredictionResult:
    """
    Immutable result returned by EnterpriseGuardModel.predict().
    """


    predicted_class: int


    threat_probability: float
    benign_probability: float


    anomaly_score: float


    confidence: float


    model_available: bool
    model_trained: bool


    model_version: str


    processing_time_ms: float


    error: str | None = None


    def to_dict(self) -> dict[str, Any]:
        return asdict(self)




@dataclass(frozen=True)
class ModelMetadata:
    """
    Immutable description of the current model state.
    """


    name: str
    version: str
    schema_version: int


    feature_count: int
    feature_names: tuple[str, ...]


    trained: bool
    training_samples: int


    model_type: str


    created_at: str | None
    updated_at: str | None


    model_hash: str | None


    # Training metrics
    training_accuracy: float | None = None
    training_correct: int | None = None
    training_incorrect: int | None = None


    # Validation metrics
    validation_accuracy: float | None = None
    validation_correct: int | None = None
    validation_incorrect: int | None = None
    validation_samples: int | None = None


    # Timing
    fit_time_ms: float | None = None
    metrics_time_ms: float | None = None
    persistence_time_ms: float | None = None
    training_time_ms: float | None = None


    # Backend
    ml_backend_available: bool = False


    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)


        data["feature_names"] = list(
            self.feature_names
        )


        return data




@dataclass
class ModelStatistics:
    """
    Runtime operational statistics.


    These are telemetry values, not model-quality metrics.
    """


    predictions: int = 0


    successful_predictions: int = 0


    failed_predictions: int = 0


    training_runs: int = 0


    total_training_samples: int = 0


    total_processing_ms: float = 0.0


    @property
    def average_processing_ms(self) -> float:
        if self.predictions <= 0:
            return 0.0


        return (
            self.total_processing_ms
            / self.predictions
        )


    def to_dict(self) -> dict[str, Any]:
        return {
            "predictions": self.predictions,
            "successful_predictions": (
                self.successful_predictions
            ),
            "failed_predictions": (
                self.failed_predictions
            ),
            "training_runs": self.training_runs,
            "total_training_samples": (
                self.total_training_samples
            ),
            "total_processing_ms": round(
                self.total_processing_ms,
                3,
            ),
            "average_processing_ms": round(
                self.average_processing_ms,
                3,
            ),
        }




# ============================================================================
# Validation Utilities
# ============================================================================




def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """
    Clamp a numeric value into a safe range.
    """


    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )




def _safe_float(
    value: Any,
    name: str,
) -> float:
    """
    Convert a value to a finite float.
    """


    try:
        result = float(value)


    except (TypeError, ValueError) as exc:
        raise FeatureValidationError(
            f"Feature '{name}' must be numeric."
        ) from exc


    if not math.isfinite(result):
        raise FeatureValidationError(
            f"Feature '{name}' must be finite."
        )


    return result




def validate_features(
    features: Mapping[str, Any],
) -> dict[str, float]:
    """
    Validate and normalize the canonical EnterpriseGuard feature set.


    Normalized features:
        [0, 1]


    failed_attempts:
        [0, MAX_FEATURE_VALUE]


    Returns
    -------
    dict[str, float]
        Canonical ordered feature mapping.
    """


    if not isinstance(features, Mapping):
        raise FeatureValidationError(
            "Features must be supplied as a mapping."
        )


    # Reject unexpected fields.


    unexpected = (
        set(features.keys())
        - set(FEATURE_NAMES)
    )


    if unexpected:
        raise FeatureValidationError(
            "Unexpected feature(s): "
            + ", ".join(
                sorted(
                    str(item)
                    for item in unexpected
                )
            )
        )


    normalized: dict[str, float] = {}


    for name in FEATURE_NAMES:


        if name not in features:
            raise FeatureValidationError(
                f"Missing required feature: '{name}'."
            )


        value = _safe_float(
            features[name],
            name,
        )


        if name in NORMALIZED_FEATURES:


            if value < 0.0 or value > 1.0:
                raise FeatureValidationError(
                    f"Feature '{name}' must be between 0 and 1."
                )


            value = _clamp(value)


        elif name == "failed_attempts":


            if value < 0.0:
                raise FeatureValidationError(
                    "'failed_attempts' cannot be negative."
                )


            value = min(
                value,
                MAX_FEATURE_VALUE,
            )


        normalized[name] = value


    return normalized




def features_to_vector(
    features: Mapping[str, Any],
) -> list[float]:
    """
    Convert canonical features into the exact ML vector order.
    """


    validated = validate_features(
        features
    )


    return [
        validated[name]
        for name in FEATURE_NAMES
    ]




def validate_labels(
    labels: Sequence[int],
) -> list[int]:
    """
    Validate binary labels.


    0 = benign
    1 = threat
    """


    if not isinstance(
        labels,
        Sequence,
    ):
        raise ModelTrainingError(
            "Labels must be a sequence."
        )


    result: list[int] = []


    for index, label in enumerate(labels):


        try:
            value = int(label)


        except (TypeError, ValueError) as exc:
            raise ModelTrainingError(
                f"Label at index {index} must be 0 or 1."
            ) from exc


        if value not in (0, 1):
            raise ModelTrainingError(
                "Labels must be binary: "
                "0=benign and 1=threat."
            )


        result.append(value)


    if not result:
        raise ModelTrainingError(
            "Labels cannot be empty."
        )


    return result




def validate_training_inputs(
    samples: Sequence[Mapping[str, Any]],
    labels: Sequence[int],
) -> tuple[list[list[float]], list[int]]:
    """
    Validate a complete labelled dataset.
    """


    if not samples:
        raise ModelTrainingError(
            "Training dataset cannot be empty."
        )


    if len(samples) != len(labels):
        raise ModelTrainingError(
            "Samples and labels must have equal lengths."
        )


    vectors = [
        features_to_vector(sample)
        for sample in samples
    ]


    validated_labels = validate_labels(
        labels
    )


    if len(set(validated_labels)) != 2:
        raise ModelTrainingError(
            "Training requires both classes: "
            "0=benign and 1=threat."
        )


    return (
        vectors,
        validated_labels,
    )




# ============================================================================
# EnterpriseGuard Model
# ============================================================================




class EnterpriseGuardModel:
    """
    Production-oriented EnterpriseGuard ML model.


    Primary backend
    ---------------


        scikit-learn LogisticRegression


    Fallback
    --------


        Deterministic baseline scoring.


    The fallback is intentionally NOT represented as a trained model.
    """


    def __init__(
        self,
        model_directory: str | os.PathLike[str] | None = None,
        auto_load: bool = True,
    ) -> None:


        self._lock = threading.RLock()


        self.model_directory = Path(
            model_directory
            if model_directory is not None
            else DEFAULT_MODEL_DIRECTORY
        )


        self.model_path = (
            self.model_directory
            / MODEL_FILE_NAME
        )


        self._model: Any = None


        self._trained = False


        self._training_samples = 0


        self._created_at: str | None = None


        self._updated_at: str | None = None


        self._model_hash: str | None = None


        # Training metrics


        self._training_accuracy: float | None = None


        self._training_correct: int | None = None


        self._training_incorrect: int | None = None


        # Validation metrics


        self._validation_accuracy: float | None = None


        self._validation_correct: int | None = None


        self._validation_incorrect: int | None = None


        self._validation_samples: int | None = None


        # Timing


        self._fit_time_ms: float | None = None


        self._metrics_time_ms: float | None = None


        self._persistence_time_ms: float | None = None


        self._training_time_ms: float | None = None


        self.statistics = ModelStatistics()


        self._ensure_model_directory()


        if auto_load:
            self.load()


    # ========================================================================
    # Filesystem
    # ========================================================================


    def _ensure_model_directory(self) -> None:
        self.model_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


    # ========================================================================
    # Properties
    # ========================================================================


    @property
    def available(self) -> bool:
        """
        True when the real ML backend is installed.
        """


        return LogisticRegression is not None


    @property
    def trained(self) -> bool:
        """
        True only when a real trained model is loaded.
        """


        with self._lock:
            return self._trained


    @property
    def training_samples(self) -> int:
        with self._lock:
            return self._training_samples


    @property
    def model_hash(self) -> str | None:
        with self._lock:
            return self._model_hash


    # ========================================================================
    # Baseline
    # ========================================================================


    @staticmethod
    def _baseline_probability(
        features: Mapping[str, float],
    ) -> float:
        """
        Deterministic fallback risk probability.


        IMPORTANT:
            This is NOT an ML prediction and must never be
            interpreted as model accuracy.
        """


        request_frequency = features[
            "request_frequency"
        ]


        failure_ratio = features[
            "failure_ratio"
        ]


        unique_sources = features[
            "unique_source_count"
        ]


        unique_users = features[
            "unique_user_count"
        ]


        failed_attempts = features[
            "failed_attempts"
        ]


        anomaly_score = features[
            "anomaly_score"
        ]


        outbound_volume = features[
            "outbound_data_volume"
        ]


        failed_attempt_score = _clamp(
            failed_attempts
            / BASELINE_FAILED_ATTEMPTS_NORMALIZER
        )


        multi_source_score = _clamp(
            (
                unique_sources
                + unique_users
            )
            / 2.0
        )


        score = (
            request_frequency * 0.16
            + failure_ratio * 0.24
            + multi_source_score * 0.12
            + failed_attempt_score * 0.16
            + anomaly_score * 0.24
            + outbound_volume * 0.08
        )


        return _clamp(score)


    # ========================================================================
    # Prediction
    # ========================================================================


    def predict(
        self,
        features: Mapping[str, Any],
    ) -> PredictionResult:
        """
        Predict threat probability.


        Uses the trained ML model when available.


        Otherwise uses the deterministic baseline.
        """


        started = time.perf_counter()


        try:


            normalized = validate_features(
                features
            )


            with self._lock:


                trained_model = (
                    self._trained
                    and self._model is not None
                )


                if trained_model:


                    probability = (
                        self._predict_trained_model(
                            normalized
                        )
                    )


                else:


                    probability = (
                        self._baseline_probability(
                            normalized
                        )
                    )


                model_trained = (
                    self._trained
                )


                model_available = (
                    self.available
                )


            probability = _clamp(
                probability
            )


            predicted_class = (
                1
                if probability
                >= PREDICTION_THRESHOLD
                else 0
            )


            benign_probability = (
                1.0 - probability
            )


            confidence = (
                max(
                    probability,
                    benign_probability,
                )
                * 100.0
            )


            anomaly_score = _clamp(
                normalized[
                    "anomaly_score"
                ]
            )


            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1000.0


            result = PredictionResult(
                predicted_class=predicted_class,


                threat_probability=round(
                    probability,
                    6,
                ),


                benign_probability=round(
                    benign_probability,
                    6,
                ),


                anomaly_score=round(
                    anomaly_score,
                    6,
                ),


                confidence=round(
                    confidence,
                    3,
                ),


                model_available=(
                    model_available
                ),


                model_trained=(
                    model_trained
                ),


                model_version=(
                    MODEL_VERSION
                ),


                processing_time_ms=round(
                    elapsed_ms,
                    3,
                ),
            )


            with self._lock:


                self.statistics.predictions += 1


                self.statistics.successful_predictions += 1


                self.statistics.total_processing_ms += (
                    elapsed_ms
                )


            return result


        except Exception as exc:


            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1000.0


            with self._lock:


                self.statistics.predictions += 1


                self.statistics.failed_predictions += 1


                self.statistics.total_processing_ms += (
                    elapsed_ms
                )


                model_trained = (
                    self._trained
                )


                model_available = (
                    self.available
                )


            return PredictionResult(
                predicted_class=0,


                threat_probability=0.0,


                benign_probability=1.0,


                anomaly_score=0.0,


                confidence=0.0,


                model_available=(
                    model_available
                ),


                model_trained=(
                    model_trained
                ),


                model_version=(
                    MODEL_VERSION
                ),


                processing_time_ms=round(
                    elapsed_ms,
                    3,
                ),


                error=str(exc),
            )


    # ========================================================================
    # Trained Prediction
    # ========================================================================


    def _predict_trained_model(
        self,
        features: Mapping[str, float],
    ) -> float:
        """
        Execute prediction against the trained estimator.
        """


        vector = [
            features[name]
            for name in FEATURE_NAMES
        ]


        model = self._model


        if model is None:
            raise RuntimeError(
                "Trained model is not available."
            )


        if hasattr(
            model,
            "predict_proba",
        ):


            probabilities = (
                model.predict_proba(
                    [vector]
                )
            )


            if len(probabilities) != 1:
                raise RuntimeError(
                    "Model returned an invalid probability matrix."
                )


            row = probabilities[0]


            if len(row) < 2:
                raise RuntimeError(
                    "Binary model must return two probabilities."
                )


            # Find class=1 explicitly.
            if hasattr(
                model,
                "classes_",
            ):


                classes = list(
                    model.classes_
                )


                if 1 not in classes:
                    raise RuntimeError(
                        "Trained model does not contain class 1."
                    )


                class_index = classes.index(
                    1
                )


                return float(
                    row[class_index]
                )


            return float(
                row[-1]
            )


        if callable(model):


            return float(
                model(vector)
            )


        raise RuntimeError(
            "Unsupported trained model interface."
        )


    # ========================================================================
    # Metrics
    # ========================================================================


    @staticmethod
    def _calculate_accuracy_metrics(
        model: Any,
        samples: Sequence[Sequence[float]],
        labels: Sequence[int],
        *,
        metric_prefix: str,
    ) -> dict[str, Any]:
        """
        Calculate classification accuracy.


        Accuracy is returned both as a ratio and percentage.
        """


        if not hasattr(
            model,
            "predict",
        ):
            raise ModelTrainingError(
                "Trained model does not support prediction."
            )


        predictions = model.predict(
            samples
        )


        if len(predictions) != len(labels):
            raise ModelTrainingError(
                "Model prediction count does not "
                "match label count."
            )


        correct = sum(
            int(prediction) == int(label)
            for prediction, label in zip(
                predictions,
                labels,
            )
        )


        total = len(labels)


        if total == 0:
            raise ModelTrainingError(
                "Cannot calculate accuracy "
                "for an empty dataset."
            )


        accuracy = (
            correct / total
        )


        return {
            f"{metric_prefix}_accuracy": round(
                float(accuracy),
                6,
            ),


            f"{metric_prefix}_accuracy_percent": round(
                float(accuracy) * 100.0,
                4,
            ),


            f"{metric_prefix}_correct": (
                correct
            ),


            f"{metric_prefix}_incorrect": (
                total - correct
            ),


            f"{metric_prefix}_evaluated_samples": (
                total
            ),
        }


    # ========================================================================
    # Training
    # ========================================================================


    def train(
        self,
        samples: Sequence[
            Mapping[str, Any]
        ],
        labels: Sequence[int],
        *,
        validation_samples: Sequence[
            Mapping[str, Any]
        ] | None = None,
        validation_labels: Sequence[int] | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """
        Train a real LogisticRegression model.


        Parameters
        ----------
        samples:
            Training feature mappings.


        labels:
            Binary training labels.


        validation_samples:
            Optional separate validation dataset.


        validation_labels:
            Labels corresponding to validation_samples.


        persist:
            Persist the resulting model when True.


        Returns
        -------
        dict
            Training metadata and metrics.
        """


        training_started = (
            time.perf_counter()
        )


        # --------------------------------------------------------------------
        # Backend validation
        # --------------------------------------------------------------------


        if LogisticRegression is None:


            raise ModelTrainingError(
                "scikit-learn is required for real model training. "
                "Install it with: "
                "python -m pip install scikit-learn"
            )


        # --------------------------------------------------------------------
        # Training dataset validation
        # --------------------------------------------------------------------


        (
            validated_samples,
            validated_labels,
        ) = validate_training_inputs(
            samples,
            labels,
        )


        # --------------------------------------------------------------------
        # Validation dataset validation
        # --------------------------------------------------------------------


        validated_validation_samples = None


        validated_validation_labels = None


        if (
            validation_samples is not None
            or validation_labels is not None
        ):


            if (
                validation_samples is None
                or validation_labels is None
            ):


                raise ModelTrainingError(
                    "validation_samples and "
                    "validation_labels must be "
                    "supplied together."
                )


            (
                validated_validation_samples,
                validated_validation_labels,
            ) = validate_training_inputs(
                validation_samples,
                validation_labels,
            )


        # --------------------------------------------------------------------
        # Model creation
        # --------------------------------------------------------------------


        model = LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
            solver="lbfgs",
        )


        # --------------------------------------------------------------------
        # Actual ML training
        # --------------------------------------------------------------------


        fit_started = (
            time.perf_counter()
        )


        try:


            model.fit(
                validated_samples,
                validated_labels,
            )


        except Exception as exc:


            raise ModelTrainingError(
                f"Model training failed: {exc}"
            ) from exc


        fit_time_ms = (
            time.perf_counter()
            - fit_started
        ) * 1000.0


        # --------------------------------------------------------------------
        # Metrics
        # --------------------------------------------------------------------


        metrics_started = (
            time.perf_counter()
        )


        training_metrics = (
            self._calculate_accuracy_metrics(
                model=model,
                samples=validated_samples,
                labels=validated_labels,
                metric_prefix="training",
            )
        )


        validation_metrics: dict[str, Any] = {}


        if (
            validated_validation_samples
            is not None
        ):


            validation_metrics = (
                self._calculate_accuracy_metrics(
                    model=model,
                    samples=validated_validation_samples,
                    labels=validated_validation_labels,
                    metric_prefix="validation",
                )
            )


        metrics_time_ms = (
            time.perf_counter()
            - metrics_started
        ) * 1000.0


        now = datetime.now(
            timezone.utc
        ).isoformat()


        # --------------------------------------------------------------------
        # State update
        # --------------------------------------------------------------------


        with self._lock:


            self._model = model


            self._trained = True


            self._training_samples = (
                len(validated_samples)
            )


            if self._created_at is None:


                self._created_at = now


            self._updated_at = now


            self._training_accuracy = (
                training_metrics[
                    "training_accuracy"
                ]
            )


            self._training_correct = (
                training_metrics[
                    "training_correct"
                ]
            )


            self._training_incorrect = (
                training_metrics[
                    "training_incorrect"
                ]
            )


            if validation_metrics:


                self._validation_accuracy = (
                    validation_metrics[
                        "validation_accuracy"
                    ]
                )


                self._validation_correct = (
                    validation_metrics[
                        "validation_correct"
                    ]
                )


                self._validation_incorrect = (
                    validation_metrics[
                        "validation_incorrect"
                    ]
                )


                self._validation_samples = (
                    validation_metrics[
                        "validation_evaluated_samples"
                    ]
                )


            else:


                self._validation_accuracy = None


                self._validation_correct = None


                self._validation_incorrect = None


                self._validation_samples = None


            self._fit_time_ms = round(
                fit_time_ms,
                3,
            )


            self._metrics_time_ms = round(
                metrics_time_ms,
                3,
            )


            # New training invalidates the old hash
            # until persistence completes.


            self._model_hash = None


            self.statistics.training_runs += 1


            self.statistics.total_training_samples += (
                len(validated_samples)
            )


        # --------------------------------------------------------------------
        # Persistence
        # --------------------------------------------------------------------


        persistence_time_ms = 0.0


        if persist:


            persistence_started = (
                time.perf_counter()
            )


            self.save()


            persistence_time_ms = (
                time.perf_counter()
                - persistence_started
            ) * 1000.0


            with self._lock:


                self._persistence_time_ms = round(
                    persistence_time_ms,
                    3,
                )


        # --------------------------------------------------------------------
        # Total training time
        # --------------------------------------------------------------------


        total_training_time_ms = (
            time.perf_counter()
            - training_started
        ) * 1000.0


        with self._lock:


            self._training_time_ms = round(
                total_training_time_ms,
                3,
            )


        # --------------------------------------------------------------------
        # Result
        # --------------------------------------------------------------------


        metrics: dict[str, Any] = {}


        metrics.update(
            training_metrics
        )


        metrics.update(
            validation_metrics
        )


        metadata = (
            self.metadata().to_dict()
        )


        metadata["training_status"] = (
            "SUCCESS"
        )


        metadata["training_metrics"] = (
            metrics
        )


        metadata["timing"] = {
            "total_training_time_ms": round(
                total_training_time_ms,
                3,
            ),


            "fit_time_ms": round(
                fit_time_ms,
                3,
            ),


            "metrics_time_ms": round(
                metrics_time_ms,
                3,
            ),


            "persistence_time_ms": round(
                persistence_time_ms,
                3,
            ),
        }


        return metadata


    # ========================================================================
    # Persistence
    # ========================================================================


    def _build_payload(self) -> dict[str, Any]:
        """
        Build the serializable model payload.
        """


        with self._lock:


            if (
                not self._trained
                or self._model is None
            ):


                raise ModelPersistenceError(
                    "Cannot persist an untrained model."
                )


            return {
                "schema_version": (
                    MODEL_SCHEMA_VERSION
                ),


                "name": MODEL_NAME,


                "version": MODEL_VERSION,


                "feature_names": (
                    FEATURE_NAMES
                ),


                "training_samples": (
                    self._training_samples
                ),


                "created_at": (
                    self._created_at
                ),


                "updated_at": (
                    self._updated_at
                ),


                "training_accuracy": (
                    self._training_accuracy
                ),


                "training_correct": (
                    self._training_correct
                ),


                "training_incorrect": (
                    self._training_incorrect
                ),


                "validation_accuracy": (
                    self._validation_accuracy
                ),


                "validation_correct": (
                    self._validation_correct
                ),


                "validation_incorrect": (
                    self._validation_incorrect
                ),


                "validation_samples": (
                    self._validation_samples
                ),


                "fit_time_ms": (
                    self._fit_time_ms
                ),


                "metrics_time_ms": (
                    self._metrics_time_ms
                ),


                "persistence_time_ms": (
                    self._persistence_time_ms
                ),


                "training_time_ms": (
                    self._training_time_ms
                ),


                "model": self._model,
            }


    def save(self) -> dict[str, Any]:
        """
        Persist the trained model atomically.


        The model is first written to a temporary file,
        flushed, fsynced, and finally replaced atomically.
        """


        payload = self._build_payload()


        self._ensure_model_directory()


        temporary_path: Path | None = None


        persistence_started = (
            time.perf_counter()
        )


        try:


            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=self.model_directory,
                prefix=".enterpriseguard_model_",
                suffix=".tmp",
                delete=False,
            ) as temporary:


                temporary_path = Path(
                    temporary.name
                )


                pickle.dump(
                    payload,
                    temporary,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )


                temporary.flush()


                os.fsync(
                    temporary.fileno()
                )


            os.replace(
                temporary_path,
                self.model_path,
            )


            temporary_path = None


            model_hash = (
                self._calculate_model_hash()
            )


            persistence_time_ms = (
                time.perf_counter()
                - persistence_started
            ) * 1000.0


            with self._lock:


                self._model_hash = model_hash


                self._persistence_time_ms = round(
                    persistence_time_ms,
                    3,
                )


            return self.metadata().to_dict()


        except Exception as exc:


            raise ModelPersistenceError(
                f"Failed to persist model: {exc}"
            ) from exc


        finally:


            if (
                temporary_path is not None
                and temporary_path.exists()
            ):


                try:


                    temporary_path.unlink(
                        missing_ok=True
                    )


                except OSError:
                    pass


    def load(self) -> bool:
        """
        Load a persisted model.


        Invalid, incompatible, corrupted, or oversized files
        are rejected and the model returns to baseline mode.


        WARNING
        -------
        pickle is not safe for untrusted files.
        Only load model files generated by EnterpriseGuard
        or another explicitly trusted source.
        """


        if not self.model_path.exists():
            return False


        try:


            file_size = (
                self.model_path.stat().st_size
            )


            if file_size <= 0:
                self._reset_model_state()
                return False


            if file_size > MAX_MODEL_FILE_SIZE:


                self._reset_model_state()


                return False


            with self.model_path.open(
                "rb"
            ) as file:


                payload = pickle.load(
                    file
                )


            if not isinstance(
                payload,
                dict,
            ):


                self._reset_model_state()


                return False


            if payload.get(
                "schema_version"
            ) != MODEL_SCHEMA_VERSION:


                self._reset_model_state()


                return False


            if payload.get(
                "name"
            ) != MODEL_NAME:


                self._reset_model_state()


                return False


            if payload.get(
                "version"
            ) != MODEL_VERSION:


                self._reset_model_state()


                return False


            stored_features = tuple(
                payload.get(
                    "feature_names",
                    (),
                )
            )


            if (
                stored_features
                != FEATURE_NAMES
            ):


                self._reset_model_state()


                return False


            model = payload.get(
                "model"
            )


            if model is None:


                self._reset_model_state()


                return False


            if not hasattr(
                model,
                "predict_proba",
            ):


                self._reset_model_state()


                return False


            if not hasattr(
                model,
                "predict",
            ):


                self._reset_model_state()


                return False


            # Verify the estimator contains both classes.
            classes = getattr(
                model,
                "classes_",
                None,
            )


            if classes is not None:


                classes_set = {
                    int(value)
                    for value in classes
                }


                if classes_set != {0, 1}:


                    self._reset_model_state()


                    return False


            with self._lock:


                self._model = model


                self._trained = True


                self._training_samples = int(
                    payload.get(
                        "training_samples",
                        0,
                    )
                )


                self._created_at = (
                    payload.get(
                        "created_at"
                    )
                )


                self._updated_at = (
                    payload.get(
                        "updated_at"
                    )
                )


                self._training_accuracy = (
                    payload.get(
                        "training_accuracy"
                    )
                )


                self._training_correct = (
                    payload.get(
                        "training_correct"
                    )
                )


                self._training_incorrect = (
                    payload.get(
                        "training_incorrect"
                    )
                )


                self._validation_accuracy = (
                    payload.get(
                        "validation_accuracy"
                    )
                )


                self._validation_correct = (
                    payload.get(
                        "validation_correct"
                    )
                )


                self._validation_incorrect = (
                    payload.get(
                        "validation_incorrect"
                    )
                )


                self._validation_samples = (
                    payload.get(
                        "validation_samples"
                    )
                )


                self._fit_time_ms = (
                    payload.get(
                        "fit_time_ms"
                    )
                )


                self._metrics_time_ms = (
                    payload.get(
                        "metrics_time_ms"
                    )
                )


                self._persistence_time_ms = (
                    payload.get(
                        "persistence_time_ms"
                    )
                )


                self._training_time_ms = (
                    payload.get(
                        "training_time_ms"
                    )
                )


                self._model_hash = (
                    self._calculate_model_hash()
                )


            return True


        except Exception:


            self._reset_model_state()


            return False


    def _reset_model_state(self) -> None:
        """
        Reset the model to safe baseline mode.
        """


        with self._lock:


            self._model = None


            self._trained = False


            self._training_samples = 0


            self._created_at = None


            self._updated_at = None


            self._model_hash = None


            self._training_accuracy = None


            self._training_correct = None


            self._training_incorrect = None


            self._validation_accuracy = None


            self._validation_correct = None


            self._validation_incorrect = None


            self._validation_samples = None


            self._fit_time_ms = None


            self._metrics_time_ms = None


            self._persistence_time_ms = None


            self._training_time_ms = None


    # ========================================================================
    # Integrity
    # ========================================================================


    def _calculate_model_hash(
        self,
    ) -> str | None:
        """
        Calculate SHA-256 of the persisted model file.


        This provides an integrity fingerprint.


        It does NOT constitute cryptographic authenticity.
        """


        if not self.model_path.exists():
            return None


        digest = hashlib.sha256()


        with self.model_path.open(
            "rb"
        ) as file:


            for chunk in iter(
                lambda: file.read(
                    1024 * 1024
                ),
                b"",
            ):


                digest.update(
                    chunk
                )


        return digest.hexdigest()


    # ========================================================================
    # Metadata
    # ========================================================================


    def metadata(
        self,
    ) -> ModelMetadata:


        with self._lock:


            return ModelMetadata(
                name=MODEL_NAME,


                version=MODEL_VERSION,


                schema_version=(
                    MODEL_SCHEMA_VERSION
                ),


                feature_count=(
                    FEATURE_COUNT
                ),


                feature_names=(
                    FEATURE_NAMES
                ),


                trained=(
                    self._trained
                ),


                training_samples=(
                    self._training_samples
                ),


                model_type=(
                    type(
                        self._model
                    ).__name__
                    if self._model is not None
                    else "baseline"
                ),


                created_at=(
                    self._created_at
                ),


                updated_at=(
                    self._updated_at
                ),


                model_hash=(
                    self._model_hash
                ),


                training_accuracy=(
                    self._training_accuracy
                ),


                training_correct=(
                    self._training_correct
                ),


                training_incorrect=(
                    self._training_incorrect
                ),


                validation_accuracy=(
                    self._validation_accuracy
                ),


                validation_correct=(
                    self._validation_correct
                ),


                validation_incorrect=(
                    self._validation_incorrect
                ),


                validation_samples=(
                    self._validation_samples
                ),


                fit_time_ms=(
                    self._fit_time_ms
                ),


                metrics_time_ms=(
                    self._metrics_time_ms
                ),


                persistence_time_ms=(
                    self._persistence_time_ms
                ),


                training_time_ms=(
                    self._training_time_ms
                ),


                ml_backend_available=(
                    self.available
                ),
            )


    def status(
        self,
    ) -> dict[str, Any]:


        metadata = self.metadata()


        return {
            "name": metadata.name,


            "version": metadata.version,


            "schema_version": (
                metadata.schema_version
            ),


            "available": (
                metadata.ml_backend_available
            ),


            "trained": (
                metadata.trained
            ),


            "model_type": (
                metadata.model_type
            ),


            "feature_count": (
                metadata.feature_count
            ),


            "feature_names": list(
                metadata.feature_names
            ),


            "training_samples": (
                metadata.training_samples
            ),


            "training_accuracy": (
                metadata.training_accuracy
            ),


            "training_correct": (
                metadata.training_correct
            ),


            "training_incorrect": (
                metadata.training_incorrect
            ),


            "validation_accuracy": (
                metadata.validation_accuracy
            ),


            "validation_correct": (
                metadata.validation_correct
            ),


            "validation_incorrect": (
                metadata.validation_incorrect
            ),


            "validation_samples": (
                metadata.validation_samples
            ),


            "fit_time_ms": (
                metadata.fit_time_ms
            ),


            "metrics_time_ms": (
                metadata.metrics_time_ms
            ),


            "persistence_time_ms": (
                metadata.persistence_time_ms
            ),


            "training_time_ms": (
                metadata.training_time_ms
            ),


            "ml_backend_available": (
                metadata.ml_backend_available
            ),


            "model_file": str(
                self.model_path
            ),


            "model_exists": (
                self.model_path.exists()
            ),


            "model_hash": (
                metadata.model_hash
            ),


            "statistics": (
                self.statistics.to_dict()
            ),


            "baseline_fallback": (
                not metadata.trained
            ),


            "accuracy_note": (
                "Training accuracy is measured "
                "on the training dataset. Validation "
                "accuracy is meaningful only when a "
                "separate representative labelled "
                "validation dataset is supplied."
            ),


            "integrity_note": (
                "SHA-256 is an integrity fingerprint, "
                "not proof of authenticity."
            ),


            "security_note": (
                "Do not load untrusted pickle files."
            ),
        }




# ============================================================================
# Compatibility Layer
# ============================================================================


ThreatIntelligenceModel = EnterpriseGuardModel




# ============================================================================
# Singleton
# ============================================================================


_default_model: EnterpriseGuardModel | None = None


_default_model_lock = threading.Lock()




def get_model() -> EnterpriseGuardModel:
    """
    Return the process-wide EnterpriseGuard model instance.
    """


    global _default_model


    if _default_model is None:


        with _default_model_lock:


            if _default_model is None:


                _default_model = (
                    EnterpriseGuardModel()
                )


    return _default_model




# ============================================================================
# Self Test
# ============================================================================




def _self_test() -> None:
    """
    Comprehensive local self-test.


    The self-test verifies:


    1. Feature validation
    2. Vector generation
    3. Baseline prediction
    4. Model status
    5. Metadata
    6. Backend availability
    7. Compatibility alias
    """


    print("=" * 78)


    print(
        "EnterpriseGuard ML Model Layer - Self Test"
    )


    print("=" * 78)


    sample_features = {
        "request_frequency": 0.95,
        "failure_ratio": 0.80,
        "unique_source_count": 0.60,
        "unique_user_count": 0.70,
        "failed_attempts": 8,
        "anomaly_score": 0.75,
        "outbound_data_volume": 0.10,
    }


    model = EnterpriseGuardModel(
        auto_load=True
    )


    # ------------------------------------------------------------------------
    # 1. Feature validation
    # ------------------------------------------------------------------------


    print("\n[1] Feature validation")


    validated = validate_features(
        sample_features
    )


    print(
        json.dumps(
            validated,
            indent=4,
            ensure_ascii=False,
        )
    )


    # ------------------------------------------------------------------------
    # 2. Feature vector
    # ------------------------------------------------------------------------


    print("\n[2] Feature vector")


    print(
        json.dumps(
            features_to_vector(
                sample_features
            ),
            indent=4,
        )
    )


    # ------------------------------------------------------------------------
    # 3. Model status
    # ------------------------------------------------------------------------


    print("\n[3] Model status")


    print(
        json.dumps(
            model.status(),
            indent=4,
            ensure_ascii=False,
        )
    )


    # ------------------------------------------------------------------------
    # 4. Prediction
    # ------------------------------------------------------------------------


    print("\n[4] Prediction")


    prediction = model.predict(
        sample_features
    )


    print(
        json.dumps(
            prediction.to_dict(),
            indent=4,
            ensure_ascii=False,
        )
    )


    # ------------------------------------------------------------------------
    # 5. Metadata
    # ------------------------------------------------------------------------


    print("\n[5] Metadata")


    print(
        json.dumps(
            model.metadata().to_dict(),
            indent=4,
            ensure_ascii=False,
        )
    )


    # ------------------------------------------------------------------------
    # 6. Backend
    # ------------------------------------------------------------------------


    print("\n[6] ML backend")


    print(
        json.dumps(
            {
                "scikit_learn_available": (
                    LogisticRegression
                    is not None
                ),


                "model_available": (
                    model.available
                ),


                "model_trained": (
                    model.trained
                ),


                "model_type": (
                    model.metadata().model_type
                ),


                "model_version": (
                    MODEL_VERSION
                ),


                "feature_count": (
                    FEATURE_COUNT
                ),
            },
            indent=4,
            ensure_ascii=False,
        )
    )


    # ------------------------------------------------------------------------
    # 7. Compatibility
    # ------------------------------------------------------------------------


    print("\n[7] Compatibility check")


    print(
        json.dumps(
            {
                "ThreatIntelligenceModel": (
                    ThreatIntelligenceModel
                    is EnterpriseGuardModel
                ),


                "EnterpriseGuardModel": (
                    EnterpriseGuardModel
                    is not None
                ),


                "get_model_available": (
                    get_model()
                    is not None
                ),
            },
            indent=4,
            ensure_ascii=False,
        )
    )


    # ------------------------------------------------------------------------
    # 8. Validation failure test
    # ------------------------------------------------------------------------


    print(
        "\n[8] Invalid feature rejection"
    )


    try:


        validate_features(
            {
                "request_frequency": 2.0,
                "failure_ratio": 0.80,
                "unique_source_count": 0.60,
                "unique_user_count": 0.70,
                "failed_attempts": 8,
                "anomaly_score": 0.75,
                "outbound_data_volume": 0.10,
            }
        )


        raise AssertionError(
            "Invalid feature was not rejected."
        )


    except FeatureValidationError:


        print(
            "PASS - invalid feature rejected."
        )


    # ------------------------------------------------------------------------
    # 9. Baseline sanity
    # ------------------------------------------------------------------------


    print(
        "\n[9] Baseline sanity"
    )


    baseline = (
        model._baseline_probability(
            validated
        )
    )


    print(
        json.dumps(
            {
                "baseline_probability": round(
                    baseline,
                    6,
                ),


                "baseline_percentage": round(
                    baseline * 100.0,
                    2,
                ),


                "is_ml_accuracy": False,
            },
            indent=4,
            ensure_ascii=False,
        )
    )


    # ------------------------------------------------------------------------
    # Complete
    # ------------------------------------------------------------------------


    print("\n" + "=" * 78)


    print(
        "EnterpriseGuard ML Model Layer self-test completed successfully."
    )


    print("=" * 78)




# ============================================================================
# Entry Point
# ============================================================================


if __name__ == "__main__":
    _self_test()