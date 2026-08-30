"""
EnterpriseGuard - Training Orchestrator
========================================


Production-grade orchestration layer for the EnterpriseGuard ML
training lifecycle.


Pipeline
--------


    TrainingDataset
          |
          v
    Dataset Validation
          |
          v
    Canonical Feature Mapping
          |
          v
    EnterpriseGuardModel.train()
          |
          v
    Model Persistence
          |
          v
    Post-Training Verification
          |
          v
    Auditable Training Run




Responsibilities
----------------
- Load or accept a TrainingDataset.
- Validate the dataset before training.
- Convert TrainingSample feature vectors into canonical mappings.
- Delegate ML training to EnterpriseGuardModel.
- Persist the trained model through the model layer.
- Verify the resulting model.
- Produce deterministic machine-readable training reports.
- Maintain training-run metadata and statistics.
- Prevent invalid datasets from reaching the model layer.
- Preserve strict separation of responsibilities.
- Never execute security actions.
- Never execute shell commands.
- Never perform network operations.
- Provide a complete integration self-test.




Important architectural rule
----------------------------
TrainingDataset owns dataset representation.


Training Validator owns dataset validation.


Training Orchestrator owns lifecycle coordination and
canonical data transformation.


EnterpriseGuardModel owns ML training, prediction and
model persistence.


The orchestrator MUST NOT modify the model layer just to
accommodate TrainingSample objects. It converts dataset
samples into the Mapping[str, float] contract required by
EnterpriseGuardModel.train().
"""


from __future__ import annotations


import hashlib
import json
import logging
import time
import uuid


from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


from enterpriseguard.intelligence.models import (
    EnterpriseGuardModel,
    FEATURE_COUNT,
    FEATURE_NAMES,
)


from enterpriseguard.intelligence.training import dataset as dataset_module


from enterpriseguard.intelligence.training.validator import (
    ValidationResult,
    validate_training_dataset,
)




# ============================================================================
# Metadata
# ============================================================================


ORCHESTRATOR_NAME = "EnterpriseGuard Training Orchestrator"
ORCHESTRATOR_VERSION = "2.0.0"
SCHEMA_VERSION = 2


MINIMUM_SAMPLES = 4


LOGGER_NAME = "enterpriseguard.training.orchestrator"




# ============================================================================
# Logging
# ============================================================================


logger = logging.getLogger(LOGGER_NAME)


if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    logger.addHandler(handler)


logger.setLevel(logging.INFO)
logger.propagate = False




# ============================================================================
# Exceptions
# ============================================================================




class TrainingOrchestratorError(RuntimeError):
    """Base exception for Training Orchestrator failures."""




class TrainingDatasetError(TrainingOrchestratorError):
    """Raised when the training dataset contract is invalid."""




class TrainingRunError(TrainingOrchestratorError):
    """Raised when a training run fails."""




class TrainingVerificationError(TrainingOrchestratorError):
    """Raised when post-training verification fails."""




# ============================================================================
# Utilities
# ============================================================================




def _utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()




def _new_run_id() -> str:
    """Generate a readable unique training-run identifier."""
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d-%H%M%S"
    )


    suffix = uuid.uuid4().hex[:8]


    return f"train-{timestamp}-{suffix}"




def _canonical_json(value: Any) -> str:
    """Serialize a value deterministically."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )




def _sha256(value: Any) -> str:
    """Return a deterministic SHA-256 fingerprint."""
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()




def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default




def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default




def _deep_copy(value: Any) -> Any:
    """Return a defensive copy using JSON-compatible semantics where possible."""
    try:
        import copy


        return copy.deepcopy(value)
    except Exception:
        return value




# ============================================================================
# Training Run Data Model
# ============================================================================




@dataclass
class TrainingRun:
    """
    Immutable-style machine-readable description of one training run.


    The object is intentionally independent from EnterpriseGuardModel so
    training lifecycle state cannot become coupled to model implementation.
    """


    run_id: str
    orchestrator: str
    orchestrator_version: str
    schema_version: int


    status: str


    started_at: str
    completed_at: str | None
    duration_ms: float


    dataset_type: str
    dataset_samples: int


    feature_count: int
    feature_names: list[str]


    benign_samples: int
    threat_samples: int
    class_balance: float


    dataset_validation: dict[str, Any]


    training_result: dict[str, Any]
    verification: dict[str, Any]


    model_status: dict[str, Any]


    dataset_fingerprint: str | None = None
    training_fingerprint: str | None = None


    error: str | None = None


    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return asdict(self)




# ============================================================================
# Statistics
# ============================================================================




@dataclass
class TrainingOrchestratorStatistics:
    """Operational statistics for the orchestrator."""


    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0


    total_samples_trained: int = 0


    total_duration_ms: float = 0.0
    max_duration_ms: float = 0.0


    last_run_id: str | None = None


    @property
    def average_duration_ms(self) -> float:
        if self.total_runs <= 0:
            return 0.0


        return (
            self.total_duration_ms
            / self.total_runs
        )


    def record(
        self,
        *,
        success: bool,
        samples: int,
        duration_ms: float,
        run_id: str,
    ) -> None:
        self.total_runs += 1


        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1


        self.total_samples_trained += max(
            0,
            samples,
        )


        self.total_duration_ms += max(
            0.0,
            duration_ms,
        )


        self.max_duration_ms = max(
            self.max_duration_ms,
            duration_ms,
        )


        self.last_run_id = run_id


    def to_dict(self) -> dict[str, Any]:
        return {
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "total_samples_trained": (
                self.total_samples_trained
            ),
            "total_duration_ms": round(
                self.total_duration_ms,
                3,
            ),
            "average_duration_ms": round(
                self.average_duration_ms,
                3,
            ),
            "max_duration_ms": round(
                self.max_duration_ms,
                3,
            ),
            "last_run_id": self.last_run_id,
        }




# ============================================================================
# Training Orchestrator
# ============================================================================




class TrainingOrchestrator:
    """
    EnterpriseGuard ML Training Orchestrator.


    The orchestrator deliberately accepts TrainingDataset objects,
    validates them through Training Validator, converts each
    TrainingSample into the canonical feature mapping required by
    EnterpriseGuardModel, and delegates actual ML work to the model layer.
    """


    def __init__(
        self,
        *,
        model: EnterpriseGuardModel | None = None,
        minimum_samples: int = MINIMUM_SAMPLES,
    ) -> None:


        if minimum_samples < 1:
            raise ValueError(
                "minimum_samples must be greater than zero."
            )


        self.minimum_samples = int(
            minimum_samples
        )


        self.model = (
            model
            if model is not None
            else EnterpriseGuardModel()
        )


        self.statistics = (
            TrainingOrchestratorStatistics()
        )


        self._last_run: TrainingRun | None = None


    # ========================================================================
    # Dataset Loading
    # ========================================================================


    @staticmethod
    def load_demo_dataset() -> Any:
        """
        Load the canonical EnterpriseGuard demo dataset.


        The orchestrator intentionally uses the public builder exposed by
        training.dataset rather than constructing TrainingSample objects
        itself.
        """


        builder = getattr(
            dataset_module,
            "build_demo_dataset",
            None,
        )


        if not callable(builder):
            raise TrainingDatasetError(
                "Training dataset builder "
                "'build_demo_dataset' is unavailable."
            )


        try:
            result = builder()
        except Exception as exc:
            raise TrainingDatasetError(
                "Failed to build training dataset: "
                f"{type(exc).__name__}: {exc}"
            ) from exc


        if result is None:
            raise TrainingDatasetError(
                "Training dataset builder returned None."
            )


        return result


    # ========================================================================
    # Dataset Inspection
    # ========================================================================


    @staticmethod
    def _dataset_type_name(
        training_dataset: Any,
    ) -> str:
        return type(
            training_dataset
        ).__name__


    @staticmethod
    def _get_dataset_samples(
        training_dataset: Any,
    ) -> list[Any]:
        """
        Return dataset samples safely.


        The canonical TrainingDataset exposes a samples collection.
        """


        samples = getattr(
            training_dataset,
            "samples",
            None,
        )


        if samples is None:
            raise TrainingDatasetError(
                "TrainingDataset does not expose "
                "a 'samples' collection."
            )


        try:
            result = list(samples)
        except TypeError as exc:
            raise TrainingDatasetError(
                "TrainingDataset.samples is not iterable."
            ) from exc


        return result


    @staticmethod
    def _get_dataset_size(
        training_dataset: Any,
    ) -> int:
        """Return the canonical dataset size."""


        size = getattr(
            training_dataset,
            "size",
            None,
        )


        if callable(size):
            try:
                size = size()
            except Exception as exc:
                raise TrainingDatasetError(
                    "TrainingDataset.size() failed: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc


        if size is None:
            return len(
                TrainingOrchestrator._get_dataset_samples(
                    training_dataset
                )
            )


        try:
            return int(size)
        except (TypeError, ValueError) as exc:
            raise TrainingDatasetError(
                "TrainingDataset.size is not numeric."
            ) from exc


    # ========================================================================
    # Validation
    # ========================================================================


    def validate_dataset(
        self,
        training_dataset: Any,
    ) -> ValidationResult:
        """
        Validate the complete training dataset before model training.
        """


        if training_dataset is None:
            raise TrainingDatasetError(
                "Training dataset cannot be None."
            )


        validation = validate_training_dataset(
            training_dataset,
            minimum_samples=self.minimum_samples,
        )


        if not isinstance(
            validation,
            ValidationResult,
        ):
            raise TrainingDatasetError(
                "Dataset validator returned an invalid result."
            )


        return validation


    # ========================================================================
    # Canonical Feature Conversion
    # ========================================================================


    @staticmethod
    def _vector_to_feature_mapping(
        vector: Sequence[Any],
    ) -> dict[str, float]:
        """
        Convert a canonical feature vector into the mapping expected
        by EnterpriseGuardModel.


        This is the critical boundary between TrainingDataset and
        EnterpriseGuardModel.
        """


        if isinstance(
            vector,
            (str, bytes, bytearray),
        ):
            raise TrainingDatasetError(
                "Feature vector cannot be a string or bytes object."
            )


        try:
            values = list(vector)
        except TypeError as exc:
            raise TrainingDatasetError(
                "Feature vector must be a sequence."
            ) from exc


        if len(values) != FEATURE_COUNT:
            raise TrainingDatasetError(
                "Feature vector contains "
                f"{len(values)} values; expected "
                f"{FEATURE_COUNT}."
            )


        mapping: dict[str, float] = {}


        for name, value in zip(
            FEATURE_NAMES,
            values,
        ):


            try:
                numeric_value = float(value)
            except (
                TypeError,
                ValueError,
            ) as exc:


                raise TrainingDatasetError(
                    f"Feature '{name}' must be numeric."
                ) from exc


            mapping[name] = numeric_value


        return mapping


    @classmethod
    def _sample_to_feature_mapping(
        cls,
        sample: Any,
    ) -> dict[str, float]:
        """
        Convert one TrainingSample into a canonical feature mapping.


        Supported representations:
            - Mapping[str, numeric]
            - Sequence[numeric]


        TrainingSample.features is expected by the current dataset
        contract and is handled explicitly.
        """


        if sample is None:
            raise TrainingDatasetError(
                "Training sample cannot be None."
            )


        features = getattr(
            sample,
            "features",
            None,
        )


        if features is None:


            # Compatibility path for possible dictionary-style samples.
            if isinstance(
                sample,
                Mapping,
            ):
                features = sample.get(
                    "features"
                )


            if features is None:
                raise TrainingDatasetError(
                    "Training sample does not expose "
                    "a 'features' field."
                )


        # --------------------------------------------------------------
        # Mapping input
        # --------------------------------------------------------------


        if isinstance(
            features,
            Mapping,
        ):


            unexpected = (
                set(features.keys())
                - set(FEATURE_NAMES)
            )


            if unexpected:
                raise TrainingDatasetError(
                    "Training sample contains unexpected "
                    f"feature(s): {', '.join(map(str, sorted(unexpected)))}"
                )


            missing = [
                name
                for name in FEATURE_NAMES
                if name not in features
            ]


            if missing:
                raise TrainingDatasetError(
                    "Training sample is missing "
                    "feature(s): "
                    + ", ".join(missing)
                )


            result: dict[str, float] = {}


            for name in FEATURE_NAMES:


                try:
                    result[name] = float(
                        features[name]
                    )
                except (
                    TypeError,
                    ValueError,
                ) as exc:


                    raise TrainingDatasetError(
                        f"Feature '{name}' must be numeric."
                    ) from exc


            return result


        # --------------------------------------------------------------
        # Vector input
        # --------------------------------------------------------------


        if isinstance(
            features,
            Sequence,
        ) and not isinstance(
            features,
            (str, bytes, bytearray),
        ):


            return cls._vector_to_feature_mapping(
                features
            )


        raise TrainingDatasetError(
            "Training sample features must be either "
            "a mapping or a feature vector."
        )


    @classmethod
    def _samples_to_feature_mappings(
        cls,
        samples: Sequence[Any],
    ) -> list[dict[str, float]]:
        """
        Convert every TrainingSample into the canonical mapping contract.
        """


        feature_mappings: list[
            dict[str, float]
        ] = []


        for index, sample in enumerate(
            samples
        ):


            try:
                mapping = (
                    cls._sample_to_feature_mapping(
                        sample
                    )
                )


            except Exception as exc:


                if isinstance(
                    exc,
                    TrainingOrchestratorError,
                ):
                    raise TrainingDatasetError(
                        f"Sample {index}: {exc}"
                    ) from exc


                raise TrainingDatasetError(
                    f"Sample {index}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc


            feature_mappings.append(
                mapping
            )


        return feature_mappings


    # ========================================================================
    # Label Extraction
    # ========================================================================


    @staticmethod
    def _sample_to_label(
        sample: Any,
        index: int,
    ) -> int:
        """
        Extract and validate one binary label from a TrainingSample.
        """


        label = getattr(
            sample,
            "label",
            None,
        )


        if label is None and isinstance(
            sample,
            Mapping,
        ):
            label = sample.get(
                "label"
            )


        if label is None:
            raise TrainingDatasetError(
                f"Sample {index}: missing label."
            )


        try:
            normalized = int(label)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TrainingDatasetError(
                f"Sample {index}: label must be 0 or 1."
            ) from exc


        if normalized not in (
            0,
            1,
        ):
            raise TrainingDatasetError(
                f"Sample {index}: label must be 0 or 1."
            )


        return normalized


    @classmethod
    def _extract_labels(
        cls,
        samples: Sequence[Any],
    ) -> list[int]:
        """Extract canonical binary labels from the dataset."""


        labels: list[int] = []


        for index, sample in enumerate(
            samples
        ):
            labels.append(
                cls._sample_to_label(
                    sample,
                    index,
                )
            )


        return labels


    # ========================================================================
    # Dataset Statistics
    # ========================================================================


    @classmethod
    def _calculate_dataset_statistics(
        cls,
        samples: Sequence[Any],
    ) -> dict[str, Any]:
        """Calculate deterministic class-distribution statistics."""


        labels = cls._extract_labels(
            samples
        )


        total = len(labels)


        benign = labels.count(0)
        threat = labels.count(1)


        class_balance = (
            benign / total
            if total > 0
            else 0.0
        )


        return {
            "samples": total,
            "features": FEATURE_COUNT,
            "feature_names": list(
                FEATURE_NAMES
            ),
            "benign_samples": benign,
            "threat_samples": threat,
            "class_balance": round(
                class_balance,
                6,
            ),
        }


    # ========================================================================
    # Dataset Fingerprint
    # ========================================================================


    @classmethod
    def _dataset_fingerprint(
        cls,
        samples: Sequence[Any],
    ) -> str:
        """
        Generate a deterministic fingerprint for the exact training
        data used by the orchestrator.
        """


        feature_mappings = (
            cls._samples_to_feature_mappings(
                samples
            )
        )


        labels = cls._extract_labels(
            samples
        )


        payload = {
            "feature_names": list(
                FEATURE_NAMES
            ),
            "samples": feature_mappings,
            "labels": labels,
        }


        return _sha256(
            payload
        )


    # ========================================================================
    # Model Training
    # ========================================================================


    def _train_model(
        self,
        feature_mappings: Sequence[
            Mapping[str, Any]
        ],
        labels: Sequence[int],
    ) -> dict[str, Any]:
        """
        Delegate actual ML training to EnterpriseGuardModel.
        """


        if not feature_mappings:
            raise TrainingRunError(
                "No feature mappings were prepared for training."
            )


        if len(feature_mappings) != len(
            labels
        ):
            raise TrainingRunError(
                "Feature mappings and labels "
                "have different lengths."
            )


        logger.info(
            "Training model with %d samples and %d features.",
            len(feature_mappings),
            FEATURE_COUNT,
        )


        try:


            result = self.model.train(
                samples=list(
                    feature_mappings
                ),
                labels=list(
                    labels
                ),
                persist=True,
            )


        except Exception as exc:


            raise TrainingRunError(
                "EnterpriseGuardModel training failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc


        if not isinstance(
            result,
            Mapping,
        ):


            raise TrainingRunError(
                "EnterpriseGuardModel.train() "
                "returned an invalid result."
            )


        return dict(
            result
        )


    # ========================================================================
    # Model Verification
    # ========================================================================


    def _verify_model(
        self,
        feature_mappings: Sequence[
            Mapping[str, Any]
        ],
    ) -> dict[str, Any]:
        """
        Verify the trained model using a deterministic post-training sample.


        This does not claim model accuracy. It only proves the trained model
        can accept canonical features and produce a structurally valid result.
        """


        if not self.model.trained:
            raise TrainingVerificationError(
                "Model reports trained=False after training."
            )


        if not feature_mappings:
            raise TrainingVerificationError(
                "No verification feature mapping is available."
            )


        verification_features = dict(
            feature_mappings[0]
        )


        prediction = self.model.predict(
            verification_features
        )


        result = prediction.to_dict()


        if result.get("error"):
            raise TrainingVerificationError(
                "Post-training prediction failed: "
                f"{result['error']}"
            )


        if result.get(
            "model_trained"
        ) is not True:
            raise TrainingVerificationError(
                "Post-training prediction did not "
                "confirm model_trained=True."
            )


        threat_probability = result.get(
            "threat_probability"
        )


        benign_probability = result.get(
            "benign_probability"
        )


        if not isinstance(
            threat_probability,
            (int, float),
        ):
            raise TrainingVerificationError(
                "Threat probability is not numeric."
            )


        if not isinstance(
            benign_probability,
            (int, float),
        ):
            raise TrainingVerificationError(
                "Benign probability is not numeric."
            )


        probability_sum = (
            float(threat_probability)
            + float(benign_probability)
        )


        if abs(
            probability_sum - 1.0
        ) > 1e-5:
            raise TrainingVerificationError(
                "Threat and benign probabilities "
                "do not sum to approximately 1."
            )


        return result


    # ========================================================================
    # Model Status
    # ========================================================================


    def _model_status(self) -> dict[str, Any]:
        """Return current model-layer status."""
        try:
            status = self.model.status()


            if isinstance(
                status,
                Mapping,
            ):
                return dict(status)


        except Exception as exc:


            return {
                "status": "ERROR",
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            }


        return {
            "status": "UNAVAILABLE"
        }


    # ========================================================================
    # Training Run
    # ========================================================================


    def run(
        self,
        training_dataset: Any | None = None,
    ) -> TrainingRun:
        """
        Execute one complete training run.


        When no dataset is supplied, the canonical demo dataset is loaded.
        """


        started_perf = time.perf_counter()
        started_at = _utc_now()
        run_id = _new_run_id()


        self.statistics.last_run_id = run_id


        validation_dict: dict[str, Any] = {}
        training_result: dict[str, Any] = {}
        verification: dict[str, Any] = {}
        model_status: dict[str, Any] = (
            self._model_status()
        )


        dataset_type = "UNKNOWN"
        dataset_samples = 0


        dataset_stats = {
            "samples": 0,
            "features": FEATURE_COUNT,
            "feature_names": list(
                FEATURE_NAMES
            ),
            "benign_samples": 0,
            "threat_samples": 0,
            "class_balance": 0.0,
        }


        dataset_fingerprint: str | None = None


        try:


            logger.info(
                "Starting training run %s.",
                run_id,
            )


            # --------------------------------------------------------------
            # 1. Dataset
            # --------------------------------------------------------------


            if training_dataset is None:
                training_dataset = (
                    self.load_demo_dataset()
                )


            dataset_type = (
                self._dataset_type_name(
                    training_dataset
                )
            )


            samples = (
                self._get_dataset_samples(
                    training_dataset
                )
            )


            dataset_samples = len(
                samples
            )


            declared_size = (
                self._get_dataset_size(
                    training_dataset
                )
            )


            if declared_size != dataset_samples:
                raise TrainingDatasetError(
                    "TrainingDataset size does not match "
                    "the number of samples."
                )


            logger.info(
                "Dataset loaded: %d samples.",
                dataset_samples,
            )


            # --------------------------------------------------------------
            # 2. Validation
            # --------------------------------------------------------------


            logger.info(
                "Validating training dataset."
            )


            validation = (
                self.validate_dataset(
                    training_dataset
                )
            )


            validation_dict = {
                "valid": validation.valid,
                "total_samples": (
                    validation.total_samples
                ),
                "benign_samples": (
                    validation.benign_samples
                ),
                "threat_samples": (
                    validation.threat_samples
                ),
                "feature_count": (
                    validation.feature_count
                ),
                "errors": list(
                    validation.errors
                ),
                "warnings": list(
                    validation.warnings
                ),
            }


            logger.info(
                "Dataset validation result: valid=%s, "
                "samples=%d, features=%d.",
                validation.valid,
                validation.total_samples,
                validation.feature_count,
            )


            if not validation.valid:
                raise TrainingDatasetError(
                    "Training dataset validation failed: "
                    + " | ".join(
                        validation.errors
                    )
                )


            # --------------------------------------------------------------
            # 3. Canonical dataset statistics
            # --------------------------------------------------------------


            dataset_stats = (
                self._calculate_dataset_statistics(
                    samples
                )
            )


            # --------------------------------------------------------------
            # 4. Dataset fingerprint
            # --------------------------------------------------------------


            dataset_fingerprint = (
                self._dataset_fingerprint(
                    samples
                )
            )


            # --------------------------------------------------------------
            # 5. Feature transformation
            # --------------------------------------------------------------


            logger.info(
                "Converting TrainingSample objects "
                "to canonical feature mappings."
            )


            feature_mappings = (
                self._samples_to_feature_mappings(
                    samples
                )
            )


            labels = self._extract_labels(
                samples
            )


            if len(
                feature_mappings
            ) != dataset_samples:
                raise TrainingDatasetError(
                    "Feature-mapping count does not "
                    "match dataset sample count."
                )


            if len(
                labels
            ) != dataset_samples:
                raise TrainingDatasetError(
                    "Label count does not match "
                    "dataset sample count."
                )


            # --------------------------------------------------------------
            # 6. Training
            # --------------------------------------------------------------


            training_result = (
                self._train_model(
                    feature_mappings,
                    labels,
                )
            )


            # --------------------------------------------------------------
            # 7. Verification
            # --------------------------------------------------------------


            verification = (
                self._verify_model(
                    feature_mappings
                )
            )


            # --------------------------------------------------------------
            # 8. Model status
            # --------------------------------------------------------------


            model_status = (
                self._model_status()
            )


            # --------------------------------------------------------------
            # 9. Fingerprint of the run
            # --------------------------------------------------------------


            training_fingerprint = _sha256(
                {
                    "dataset_fingerprint": (
                        dataset_fingerprint
                    ),
                    "model_hash": (
                        model_status.get(
                            "model_hash"
                        )
                    ),
                    "training_result": (
                        training_result
                    ),
                    "verification": (
                        verification
                    ),
                }
            )


            duration_ms = (
                time.perf_counter()
                - started_perf
            ) * 1000.0


            run = TrainingRun(
                run_id=run_id,
                orchestrator=ORCHESTRATOR_NAME,
                orchestrator_version=(
                    ORCHESTRATOR_VERSION
                ),
                schema_version=SCHEMA_VERSION,
                status="SUCCESS",
                started_at=started_at,
                completed_at=_utc_now(),
                duration_ms=round(
                    duration_ms,
                    3,
                ),
                dataset_type=dataset_type,
                dataset_samples=dataset_samples,
                feature_count=FEATURE_COUNT,
                feature_names=list(
                    FEATURE_NAMES
                ),
                benign_samples=dataset_stats[
                    "benign_samples"
                ],
                threat_samples=dataset_stats[
                    "threat_samples"
                ],
                class_balance=dataset_stats[
                    "class_balance"
                ],
                dataset_validation=(
                    validation_dict
                ),
                training_result=(
                    training_result
                ),
                verification=(
                    verification
                ),
                model_status=(
                    model_status
                ),
                dataset_fingerprint=(
                    dataset_fingerprint
                ),
                training_fingerprint=(
                    training_fingerprint
                ),
                error=None,
            )


            self._last_run = run


            self.statistics.record(
                success=True,
                samples=dataset_samples,
                duration_ms=duration_ms,
                run_id=run_id,
            )


            logger.info(
                "Training run %s completed successfully.",
                run_id,
            )


            return run


        except Exception as exc:


            duration_ms = (
                time.perf_counter()
                - started_perf
            ) * 1000.0


            model_status = (
                self._model_status()
            )


            error_message = (
                f"{type(exc).__name__}: {exc}"
            )


            logger.error(
                "Training run %s failed: %s",
                run_id,
                error_message,
            )


            run = TrainingRun(
                run_id=run_id,
                orchestrator=ORCHESTRATOR_NAME,
                orchestrator_version=(
                    ORCHESTRATOR_VERSION
                ),
                schema_version=SCHEMA_VERSION,
                status="FAILED",
                started_at=started_at,
                completed_at=_utc_now(),
                duration_ms=round(
                    duration_ms,
                    3,
                ),
                dataset_type=dataset_type,
                dataset_samples=dataset_samples,
                feature_count=FEATURE_COUNT,
                feature_names=list(
                    FEATURE_NAMES
                ),
                benign_samples=dataset_stats[
                    "benign_samples"
                ],
                threat_samples=dataset_stats[
                    "threat_samples"
                ],
                class_balance=dataset_stats[
                    "class_balance"
                ],
                dataset_validation=(
                    validation_dict
                ),
                training_result=(
                    training_result
                ),
                verification=(
                    verification
                ),
                model_status=(
                    model_status
                ),
                dataset_fingerprint=(
                    dataset_fingerprint
                ),
                training_fingerprint=None,
                error=error_message,
            )


            self._last_run = run


            self.statistics.record(
                success=False,
                samples=dataset_samples,
                duration_ms=duration_ms,
                run_id=run_id,
            )


            return run


    # ========================================================================
    # Status
    # ========================================================================


    def status(self) -> dict[str, Any]:
        """Return orchestrator operational status."""


        model_status = self._model_status()


        return {
            "orchestrator": ORCHESTRATOR_NAME,
            "version": ORCHESTRATOR_VERSION,
            "schema_version": SCHEMA_VERSION,
            "minimum_samples": (
                self.minimum_samples
            ),
            "feature_count": FEATURE_COUNT,
            "feature_names": list(
                FEATURE_NAMES
            ),
            "model": model_status,
            "has_last_run": (
                self._last_run is not None
            ),
            "last_run": (
                self._last_run.to_dict()
                if self._last_run is not None
                else None
            ),
            "statistics": (
                self.statistics.to_dict()
            ),
            "safety": {
                "executes_security_actions": False,
                "shell_execution": False,
                "network_operations": False,
                "process_operations": False,
                "account_modification": False,
            },
        }


    # ========================================================================
    # Last Run
    # ========================================================================


    def last_run(
        self,
    ) -> dict[str, Any] | None:
        """Return the latest training run."""
        if self._last_run is None:
            return None


        return self._last_run.to_dict()


    # ========================================================================
    # Self-Test Helpers
    # ========================================================================


    def _self_test_mapping_conversion(
        self,
        training_dataset: Any,
    ) -> dict[str, Any]:
        """
        Explicitly test the critical TrainingSample -> Mapping boundary.
        """


        samples = self._get_dataset_samples(
            training_dataset
        )


        mappings = (
            self._samples_to_feature_mappings(
                samples
            )
        )


        labels = self._extract_labels(
            samples
        )


        if len(mappings) != len(samples):
            raise AssertionError(
                "Feature mapping count mismatch."
            )


        if len(labels) != len(samples):
            raise AssertionError(
                "Label count mismatch."
            )


        for index, mapping in enumerate(
            mappings
        ):


            if not isinstance(
                mapping,
                Mapping,
            ):
                raise AssertionError(
                    f"Sample {index} did not "
                    "produce a feature mapping."
                )


            if list(
                mapping.keys()
            ) != list(
                FEATURE_NAMES
            ):
                raise AssertionError(
                    f"Sample {index} feature ordering "
                    "does not match FEATURE_NAMES."
                )


        return {
            "status": "SUCCESS",
            "samples": len(samples),
            "mappings": len(mappings),
            "labels": len(labels),
            "feature_count": FEATURE_COUNT,
        }




# ============================================================================
# Global Orchestrator
# ============================================================================


_default_orchestrator: TrainingOrchestrator | None = None




def get_orchestrator() -> TrainingOrchestrator:
    """Return the process-wide TrainingOrchestrator."""
    global _default_orchestrator


    if _default_orchestrator is None:
        _default_orchestrator = (
            TrainingOrchestrator()
        )


    return _default_orchestrator




# ============================================================================
# Public Module API
# ============================================================================




def run_training(
    training_dataset: Any | None = None,
) -> dict[str, Any]:
    """
    Run one complete training lifecycle.
    """


    return get_orchestrator().run(
        training_dataset
    ).to_dict()




def orchestrator_status() -> dict[str, Any]:
    """Return global orchestrator status."""
    return get_orchestrator().status()




def last_training_run() -> dict[str, Any] | None:
    """Return the global orchestrator's last training run."""
    return get_orchestrator().last_run()




def self_test() -> dict[str, Any]:
    """Return the orchestrator self-test report."""
    return _run_self_test()




# ============================================================================
# Self-Test
# ============================================================================




def _run_self_test() -> dict[str, Any]:
    """
    Comprehensive deterministic orchestrator self-test.


    The most important assertion verifies that TrainingSample.features
    are transformed into Mapping[str, float] before reaching the model.
    """


    print("=" * 78)
    print(
        "EnterpriseGuard Training Orchestrator - Self Test"
    )
    print("=" * 78)


    checks: dict[str, bool] = {
        "orchestrator_created": False,
        "demo_dataset_loaded": False,
        "dataset_validation_passed": False,
        "feature_mapping_conversion_passed": False,
        "label_conversion_passed": False,
        "training_completed": False,
        "model_trained": False,
        "post_training_verification_passed": False,
        "model_persisted": False,
        "run_metadata_complete": False,
        "no_security_actions": False,
        "no_shell_execution": False,
    }


    orchestrator = TrainingOrchestrator()


    print("\n[1] Creating orchestrator")


    status = orchestrator.status()


    print(
        json.dumps(
            status,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    checks[
        "orchestrator_created"
    ] = (
        status.get(
            "orchestrator"
        )
        == ORCHESTRATOR_NAME
    )


    if not checks[
        "orchestrator_created"
    ]:
        raise AssertionError(
            "Training Orchestrator was not created correctly."
        )


    print("\n[2] Loading demo dataset")


    training_dataset = (
        orchestrator.load_demo_dataset()
    )


    samples = (
        orchestrator._get_dataset_samples(
            training_dataset
        )
    )


    dataset_info = {
        "dataset_type": type(
            training_dataset
        ).__name__,
        "samples": len(samples),
        "feature_count": FEATURE_COUNT,
        "feature_names": list(
            FEATURE_NAMES
        ),
    }


    print(
        json.dumps(
            dataset_info,
            indent=4,
            ensure_ascii=False,
        )
    )


    checks[
        "demo_dataset_loaded"
    ] = (
        len(samples) >= orchestrator.minimum_samples
    )


    if not checks[
        "demo_dataset_loaded"
    ]:
        raise AssertionError(
            "Demo dataset did not meet minimum size."
        )


    print("\n[3] Validating dataset")


    validation = (
        orchestrator.validate_dataset(
            training_dataset
        )
    )


    validation_dict = {
        "valid": validation.valid,
        "total_samples": (
            validation.total_samples
        ),
        "benign_samples": (
            validation.benign_samples
        ),
        "threat_samples": (
            validation.threat_samples
        ),
        "feature_count": (
            validation.feature_count
        ),
        "errors": list(
            validation.errors
        ),
        "warnings": list(
            validation.warnings
        ),
    }


    print(
        json.dumps(
            validation_dict,
            indent=4,
            ensure_ascii=False,
        )
    )


    checks[
        "dataset_validation_passed"
    ] = validation.valid


    if not validation.valid:
        raise AssertionError(
            "Demo dataset failed validation."
        )


    print(
        "\n[4] Testing TrainingSample -> "
        "Feature Mapping conversion"
    )


    mapping_test = (
        orchestrator._self_test_mapping_conversion(
            training_dataset
        )
    )


    print(
        json.dumps(
            mapping_test,
            indent=4,
            ensure_ascii=False,
        )
    )


    checks[
        "feature_mapping_conversion_passed"
    ] = (
        mapping_test.get(
            "status"
        )
        == "SUCCESS"
    )


    checks[
        "label_conversion_passed"
    ] = (
        mapping_test.get(
            "labels"
        )
        == mapping_test.get(
            "samples"
        )
    )


    if not checks[
        "feature_mapping_conversion_passed"
    ]:
        raise AssertionError(
            "TrainingSample -> feature mapping "
            "conversion failed."
        )


    if not checks[
        "label_conversion_passed"
    ]:
        raise AssertionError(
            "TrainingSample label conversion failed."
        )


    print(
        "\n[5] Executing training run"
    )


    run = orchestrator.run(
        training_dataset
    )


    run_dict = run.to_dict()


    print(
        json.dumps(
            run_dict,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    checks[
        "training_completed"
    ] = (
        run.status
        == "SUCCESS"
    )


    if not checks[
        "training_completed"
    ]:
        raise AssertionError(
            "Training orchestrator self-test failed "
            "during the training run: "
            f"{run.error}"
        )


    checks[
        "model_trained"
    ] = (
        run.model_status.get(
            "trained"
        )
        is True
    )


    checks[
        "post_training_verification_passed"
    ] = (
        bool(run.verification)
        and run.verification.get(
            "error"
        )
        is None
    )


    checks[
        "model_persisted"
    ] = (
        run.model_status.get(
            "model_exists"
        )
        is True
        and bool(
            run.model_status.get(
                "model_hash"
            )
        )
    )


    required_run_fields = (
        "run_id",
        "started_at",
        "completed_at",
        "dataset_samples",
        "feature_count",
        "dataset_validation",
        "training_result",
        "verification",
        "model_status",
    )


    checks[
        "run_metadata_complete"
    ] = all(
        field_name in run_dict
        for field_name in required_run_fields
    )


    checks[
        "no_security_actions"
    ] = (
        status.get(
            "safety",
            {},
        ).get(
            "executes_security_actions"
        )
        is False
    )


    checks[
        "no_shell_execution"
    ] = (
        status.get(
            "safety",
            {},
        ).get(
            "shell_execution"
        )
        is False
    )


    print(
        "\n[6] Final verification"
    )


    final_checks = {
        key: bool(value)
        for key, value in checks.items()
    }


    print(
        json.dumps(
            final_checks,
            indent=4,
            ensure_ascii=False,
        )
    )


    passed_count = sum(
        1
        for value in final_checks.values()
        if value
    )


    total_checks = len(
        final_checks
    )


    passed = (
        passed_count
        == total_checks
    )


    print(
        "\n[7] Orchestrator summary"
    )


    summary = {
        "passed": passed,
        "orchestrator": ORCHESTRATOR_NAME,
        "version": ORCHESTRATOR_VERSION,
        "checks": final_checks,
        "passed_count": passed_count,
        "total_checks": total_checks,
        "statistics": orchestrator.statistics.to_dict(),
        "last_run_id": (
            run.run_id
        ),
        "model_hash": (
            run.model_status.get(
                "model_hash"
            )
        ),
    }


    print(
        json.dumps(
            summary,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print("\n" + "=" * 78)


    if not passed:
        failed = [
            name
            for name, value
            in final_checks.items()
            if not value
        ]


        print(
            "Training Orchestrator self test FAILED."
        )


        print(
            "Failed checks: "
            + ", ".join(failed)
        )


        print("=" * 78)


        raise AssertionError(
            "Training orchestrator self-test failed."
        )


    print(
        "Training Orchestrator self test "
        "completed successfully."
    )


    print("=" * 78)


    return summary




# ============================================================================
# Entry Point
# ============================================================================




if __name__ == "__main__":
    _run_self_test()