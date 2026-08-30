"""
EnterpriseGuard - Training Service
==================================

High-level model lifecycle orchestration for EnterpriseGuard.

Architecture
------------

    TrainingDataset
          |
          v
    TrainingOrchestrator
          |
          v
    TrainingService
       /    |      \
      v     v       v
 Validator Registry Loader
                    |
                    v
                 Manager


Lifecycle
---------

    validate
       |
       v
     train
       |
       v
   register
       |
       v
   verify
       |
       v
   activate


Additional lifecycle operations
--------------------------------

    reload
    deactivate
    switch_version
    status
    statistics


Design principles
-----------------

- The service is an orchestration layer.
- Dataset validation remains delegated to TrainingOrchestrator/Validator.
- ML training remains delegated to TrainingOrchestrator.
- Model persistence remains delegated to ModelRegistry.
- Model integrity verification remains delegated to ModelLoader.
- Runtime activation remains delegated to ModelManager.
- No direct pickle loading.
- No shell execution.
- No network operations.
- No security actions.
- No duplicated ML training logic.
- No duplicated dataset-validation logic.
- Baseline models cannot enter production.
- Untrained models cannot enter production.
- Feature-contract compatibility is mandatory.
- Schema compatibility is mandatory.
- A replacement model is verified before activation.
- Existing active models are never intentionally deactivated first.
- Lifecycle results are immutable.
- Status output is machine-readable.
- Self-test uses isolated in-memory fake components only.
"""

from __future__ import annotations

import copy
import json
import logging
import time
import uuid

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional


LOGGER = logging.getLogger(__name__)


# ============================================================================
# Project model contract
# ============================================================================

try:
    from enterpriseguard.intelligence.models import (
        FEATURE_NAMES,
        MODEL_NAME,
        MODEL_SCHEMA_VERSION,
        MODEL_VERSION,
    )
except ImportError:
    # Fallback values are intentionally limited to isolated-module testing.
    MODEL_NAME = "EnterpriseGuard Threat Intelligence Model"
    MODEL_VERSION = "3.0.0"
    MODEL_SCHEMA_VERSION = 1

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
# Service contract
# ============================================================================

SERVICE_NAME = "EnterpriseGuard Training Service"
SERVICE_VERSION = "1.1.0"
SCHEMA_VERSION = 1

# Must remain compatible with the canonical validator contract.
MINIMUM_SAMPLES = 4


# ============================================================================
# Exceptions
# ============================================================================


class TrainingServiceError(RuntimeError):
    """Base exception for TrainingService failures."""


class LifecycleValidationError(TrainingServiceError):
    """Raised when lifecycle input or validation fails."""


class TrainingExecutionError(TrainingServiceError):
    """Raised when model training fails."""


class ModelRegistrationError(TrainingServiceError):
    """Raised when model registration fails."""


class ModelVerificationError(TrainingServiceError):
    """Raised when model compatibility or integrity verification fails."""


class ModelActivationError(TrainingServiceError):
    """Raised when a model cannot safely become active."""


# ============================================================================
# Lifecycle result
# ============================================================================


@dataclass(frozen=True)
class LifecycleResult:
    """
    Immutable result of a TrainingService lifecycle operation.

    details is exported as a detached dictionary so callers cannot mutate
    the service's internal state through the returned object.
    """

    operation: str
    success: bool
    status: str
    started_at: str
    completed_at: str
    duration_ms: float

    run_id: Optional[str] = None

    model_name: Optional[str] = None
    model_version: Optional[str] = None
    previous_version: Optional[str] = None

    error: Optional[str] = None

    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a detached JSON-friendly representation."""
        return copy.deepcopy(asdict(self))


# ============================================================================
# Time helpers
# ============================================================================


def _utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return _utc_now().isoformat()


def _elapsed_ms(started: float) -> float:
    """Return elapsed monotonic time in milliseconds."""
    return round(
        (time.perf_counter() - started) * 1000.0,
        3,
    )


# ============================================================================
# Generic result helpers
# ============================================================================


def _object_to_dict(value: Any) -> Dict[str, Any]:
    """
    Convert common result objects into a detached dictionary.

    Supported:
        - dict
        - Mapping
        - to_dict()
        - model_dump()
        - dataclass
        - ordinary Python objects
    """

    if value is None:
        return {}

    if isinstance(value, Mapping):
        return copy.deepcopy(dict(value))

    to_dict = getattr(value, "to_dict", None)

    if callable(to_dict):
        try:
            result = to_dict()
            if isinstance(result, Mapping):
                return copy.deepcopy(dict(result))
        except Exception:
            pass

    model_dump = getattr(value, "model_dump", None)

    if callable(model_dump):
        try:
            result = model_dump()
            if isinstance(result, Mapping):
                return copy.deepcopy(dict(result))
        except Exception:
            pass

    if hasattr(value, "__dataclass_fields__"):
        try:
            return copy.deepcopy(asdict(value))
        except Exception:
            pass

    try:
        return copy.deepcopy(dict(vars(value)))
    except Exception:
        return {}


def _get(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:
    """Safely retrieve a value from a mapping or object."""

    if value is None:
        return default

    if isinstance(value, Mapping):
        return value.get(key, default)

    return getattr(value, key, default)


def _normalize_status(value: Any) -> Dict[str, Any]:
    """
    Normalize arbitrary component results into a detached dictionary.
    """

    if value is None:
        return {}

    if isinstance(value, bool):
        return {
            "success": value,
            "status": "SUCCESS" if value else "FAILED",
        }

    result = _object_to_dict(value)

    if result:
        return result

    return {
        "result": value,
    }


def _is_success(value: Any) -> bool:
    """
    Determine whether a component result represents success.

    Supported successful representations:

        True
        success=True
        valid=True
        status="SUCCESS"
        state="ACTIVE"
        result=True
    """

    if value is True:
        return True

    if value is False or value is None:
        return False

    data = _object_to_dict(value)

    success = data.get("success")

    if isinstance(success, bool):
        return success

    valid = data.get("valid")

    if isinstance(valid, bool):
        return valid

    result = data.get("result")

    if isinstance(result, bool):
        return result

    for key in ("status", "state"):
        value_text = data.get(key)

        if not isinstance(value_text, str):
            continue

        normalized = value_text.upper().strip()

        if normalized in {
            "SUCCESS",
            "SUCCEEDED",
            "OK",
            "VALID",
            "ACTIVE",
        }:
            return True

        if normalized in {
            "FAILED",
            "FAILURE",
            "ERROR",
            "INVALID",
            "INACTIVE",
        }:
            return False

    return False


def _extract_error(
    result: Any,
    fallback: str,
) -> str:
    """Extract the best available error message."""

    error = _get(result, "error")

    if error:
        return str(error)

    errors = _get(result, "errors")

    if errors:
        if isinstance(errors, (list, tuple)):
            return "; ".join(str(item) for item in errors)

        return str(errors)

    message = _get(result, "message")

    if message:
        return str(message)

    return fallback


# ============================================================================
# Model contract
# ============================================================================


def _assert_model_contract(
    model_record: Mapping[str, Any],
) -> None:
    """
    Validate the production model metadata contract.

    Cryptographic integrity remains delegated to ModelLoader.
    """

    if not isinstance(model_record, Mapping):
        raise ModelVerificationError(
            "Model record must be a mapping."
        )

    name = model_record.get("name")

    if name != MODEL_NAME:
        raise ModelVerificationError(
            f"Incompatible model name: {name!r}. "
            f"Expected {MODEL_NAME!r}."
        )

    schema_version = model_record.get("schema_version")

    if schema_version != MODEL_SCHEMA_VERSION:
        raise ModelVerificationError(
            "Incompatible model schema version: "
            f"{schema_version!r}. "
            f"Expected {MODEL_SCHEMA_VERSION!r}."
        )

    feature_names = tuple(
        model_record.get("feature_names", ())
    )

    if feature_names != tuple(FEATURE_NAMES):
        raise ModelVerificationError(
            "Model feature contract is incompatible."
        )

    feature_count = model_record.get("feature_count")

    if feature_count != len(FEATURE_NAMES):
        raise ModelVerificationError(
            "Model feature count is incompatible."
        )

    version = model_record.get("version")

    if not isinstance(version, str) or not version.strip():
        raise ModelVerificationError(
            "Model version is required."
        )

    trained = model_record.get("trained")

    if trained is not True:
        raise ModelVerificationError(
            "Untrained models cannot enter the production lifecycle."
        )

    baseline = model_record.get("baseline", False)

    if baseline is True:
        raise ModelVerificationError(
            "Baseline models cannot enter the production lifecycle."
        )


# ============================================================================
# Training Service
# ============================================================================


class TrainingService:
    """
    High-level coordinator for the EnterpriseGuard model lifecycle.

    This class intentionally contains orchestration logic only.
    """

    def __init__(
        self,
        orchestrator: Any = None,
        registry: Any = None,
        loader: Any = None,
        manager: Any = None,
        *,
        minimum_samples: int = MINIMUM_SAMPLES,
    ) -> None:

        if isinstance(minimum_samples, bool):
            raise ValueError(
                "minimum_samples must be an integer, not bool."
            )

        if not isinstance(minimum_samples, int):
            raise ValueError(
                "minimum_samples must be an integer."
            )

        if minimum_samples < 1:
            raise ValueError(
                "minimum_samples must be >= 1."
            )

        self.orchestrator = orchestrator
        self.registry = registry
        self.loader = loader
        self.manager = manager

        self.minimum_samples = minimum_samples

        self._created_at = _iso_now()
        self._last_result: Optional[LifecycleResult] = None

        self._statistics: Dict[str, Any] = {
            "total_lifecycle_runs": 0,
            "successful_lifecycle_runs": 0,
            "failed_lifecycle_runs": 0,

            "validation_runs": 0,
            "successful_validations": 0,

            "training_runs": 0,
            "successful_trainings": 0,

            "registration_runs": 0,
            "successful_registrations": 0,

            "verification_runs": 0,
            "successful_verifications": 0,

            "activation_runs": 0,
            "successful_activations": 0,

            "reload_runs": 0,
            "successful_reloads": 0,

            "deactivation_runs": 0,
            "successful_deactivations": 0,

            "switch_runs": 0,
            "successful_switches": 0,

            "total_duration_ms": 0.0,
            "average_duration_ms": 0.0,

            "last_run_id": None,
            "last_model_version": None,
        }

    # ========================================================================
    # Dependency management
    # ========================================================================

    @staticmethod
    def _require(
        dependency: Any,
        name: str,
    ) -> Any:

        if dependency is None:
            raise TrainingServiceError(
                f"{name} dependency is not configured."
            )

        return dependency

    # ========================================================================
    # Dataset validation
    # ========================================================================

    def validate(
        self,
        dataset: Any,
    ) -> Dict[str, Any]:
        """
        Validate a TrainingDataset through TrainingOrchestrator.
        """

        self._statistics["validation_runs"] += 1

        if dataset is None:
            raise LifecycleValidationError(
                "Training dataset cannot be None."
            )

        orchestrator = self._require(
            self.orchestrator,
            "TrainingOrchestrator",
        )

        method_names = (
            "validate_dataset",
            "validate_training_dataset",
            "validate",
        )

        result = None
        method_found = False

        for method_name in method_names:
            method = getattr(
                orchestrator,
                method_name,
                None,
            )

            if not callable(method):
                continue

            method_found = True

            try:
                result = method(dataset)
                break
            except TypeError:
                try:
                    result = method(dataset=dataset)
                    break
                except TypeError:
                    continue

        if not method_found:
            raise LifecycleValidationError(
                "TrainingOrchestrator does not expose "
                "a supported dataset validation method."
            )

        if result is None:
            raise LifecycleValidationError(
                "Training dataset validation returned no result."
            )

        result_dict = _normalize_status(result)

        valid = result_dict.get("valid")

        if not isinstance(valid, bool):
            valid = _is_success(result)

        result_dict["valid"] = bool(valid)

        if not result_dict["valid"]:
            errors = result_dict.get("errors")

            if not errors:
                errors = [
                    "Training dataset validation failed."
                ]

            if not isinstance(errors, (list, tuple)):
                errors = [errors]

            raise LifecycleValidationError(
                "; ".join(str(error) for error in errors)
            )

        total_samples = result_dict.get("total_samples")

        if total_samples is not None:
            try:
                total_samples_int = int(total_samples)
            except (TypeError, ValueError) as exc:
                raise LifecycleValidationError(
                    "Validation result contains an invalid "
                    "total_samples value."
                ) from exc

            if total_samples_int < self.minimum_samples:
                raise LifecycleValidationError(
                    "Training dataset contains "
                    f"{total_samples_int} samples; "
                    f"minimum required is "
                    f"{self.minimum_samples}."
                )

        self._statistics[
            "successful_validations"
        ] += 1

        return result_dict

    # ========================================================================
    # Public training API
    # ========================================================================

    def train(
        self,
        dataset: Any,
        *,
        register: bool = True,
        activate: bool = True,
        version: Optional[str] = None,
    ) -> LifecycleResult:
        """Train a model and optionally register and activate it."""

        return self.run(
            dataset,
            register=register,
            activate=activate,
            version=version,
        )

    def run(
        self,
        dataset: Any,
        *,
        register: bool = True,
        activate: bool = True,
        version: Optional[str] = None,
    ) -> LifecycleResult:
        """
        Execute the complete model lifecycle.

        Pipeline:

            validate
                -> train
                -> contract validation
                -> register
                -> verify
                -> activate
        """

        run_id = self._new_run_id()
        started_at = _iso_now()
        started = time.perf_counter()

        self._statistics[
            "total_lifecycle_runs"
        ] += 1

        try:
            # ----------------------------------------------------------------
            # 1. Dataset validation
            # ----------------------------------------------------------------

            validation = self.validate(dataset)

            # ----------------------------------------------------------------
            # 2. Model training
            # ----------------------------------------------------------------

            self._statistics[
                "training_runs"
            ] += 1

            training_result = self._execute_training(
                dataset
            )

            training_dict = _normalize_status(
                training_result
            )

            if not self._training_succeeded(
                training_result
            ):
                raise TrainingExecutionError(
                    _extract_error(
                        training_result,
                        "Model training failed.",
                    )
                )

            self._statistics[
                "successful_trainings"
            ] += 1

            # ----------------------------------------------------------------
            # 3. Extract and validate model record
            # ----------------------------------------------------------------

            model_record = self._extract_model_record(
                training_result
            )

            if version is not None:
                if not isinstance(version, str):
                    raise LifecycleValidationError(
                        "Model version override must be a string."
                    )

                if not version.strip():
                    raise LifecycleValidationError(
                        "Model version override cannot be empty."
                    )

                model_record["version"] = version.strip()

            _assert_model_contract(model_record)

            model_version = str(
                model_record["version"]
            )

            # ----------------------------------------------------------------
            # 4. Register
            # ----------------------------------------------------------------

            registration_result = None

            if register:
                self._statistics[
                    "registration_runs"
                ] += 1

                registration_result = self._register_model(
                    model_record
                )

                if not self._registration_succeeded(
                    registration_result
                ):
                    raise ModelRegistrationError(
                        _extract_error(
                            registration_result,
                            "Model registration failed.",
                        )
                    )

                self._statistics[
                    "successful_registrations"
                ] += 1

                registered_dict = _normalize_status(
                    registration_result
                )

                if registered_dict:
                    candidate_record = {
                        **model_record,
                        **registered_dict,
                    }

                    _assert_model_contract(
                        candidate_record
                    )

                    model_record = candidate_record

            # ----------------------------------------------------------------
            # 5. Verification
            # ----------------------------------------------------------------

            verification = self.verify(
                model_record
            )

            # ----------------------------------------------------------------
            # 6. Activation
            # ----------------------------------------------------------------

            activation = None

            if activate:
                activation = self.activate(
                    model_version
                )

            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            previous_version = None

            if isinstance(activation, Mapping):
                previous_version = activation.get(
                    "previous_version"
                )

            result = LifecycleResult(
                operation="train",
                success=True,
                status="SUCCESS",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                run_id=run_id,
                model_name=MODEL_NAME,
                model_version=model_version,
                previous_version=previous_version,
                details={
                    "validation": validation,
                    "training": training_dict,
                    "registration": (
                        _normalize_status(
                            registration_result
                        )
                        if registration_result is not None
                        else None
                    ),
                    "verification": verification,
                    "activation": activation,
                },
            )

            self._record_success(
                result,
                model_version,
            )

            LOGGER.info(
                "Training lifecycle completed successfully: "
                "run_id=%s version=%s duration_ms=%s",
                run_id,
                model_version,
                duration_ms,
            )

            return result

        except Exception as exc:
            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            result = LifecycleResult(
                operation="train",
                success=False,
                status="FAILED",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                run_id=run_id,
                model_name=MODEL_NAME,
                model_version=None,
                error=str(exc),
            )

            self._record_failure(result)

            LOGGER.exception(
                "Training lifecycle failed: run_id=%s",
                run_id,
            )

            return result

    # ========================================================================
    # Training adapter
    # ========================================================================

    def _execute_training(
        self,
        dataset: Any,
    ) -> Any:

        orchestrator = self._require(
            self.orchestrator,
            "TrainingOrchestrator",
        )

        method_names = (
            "train",
            "execute_training_run",
            "run",
            "train_dataset",
        )

        method_found = False

        for method_name in method_names:
            method = getattr(
                orchestrator,
                method_name,
                None,
            )

            if not callable(method):
                continue

            method_found = True

            try:
                return method(dataset)
            except TypeError:
                try:
                    return method(dataset=dataset)
                except TypeError:
                    continue

        if not method_found:
            raise TrainingExecutionError(
                "TrainingOrchestrator does not expose "
                "a supported training execution method."
            )

        raise TrainingExecutionError(
            "TrainingOrchestrator training method "
            "could not be invoked with a supported signature."
        )

    # ========================================================================
    # Model extraction
    # ========================================================================

    def _extract_model_record(
        self,
        training_result: Any,
    ) -> Dict[str, Any]:

        result = _object_to_dict(
            training_result
        )

        if not result:
            raise TrainingExecutionError(
                "Training result does not contain a model record."
            )

        nested = result.get(
            "training_result"
        )

        if nested is not None:
            model_record = _object_to_dict(
                nested
            )
        else:
            model_record = dict(result)

        if not model_record.get("version"):
            model_status = result.get(
                "model_status"
            )

            if model_status:
                model_record.update(
                    _object_to_dict(model_status)
                )

        # Canonical metadata defaults.
        model_record.setdefault(
            "name",
            MODEL_NAME,
        )

        model_record.setdefault(
            "schema_version",
            MODEL_SCHEMA_VERSION,
        )

        model_record.setdefault(
            "feature_names",
            list(FEATURE_NAMES),
        )

        model_record.setdefault(
            "feature_count",
            len(FEATURE_NAMES),
        )

        model_record.setdefault(
            "trained",
            True,
        )

        model_record.setdefault(
            "baseline",
            False,
        )

        if not model_record.get("version"):
            model_record.setdefault(
                "version",
                MODEL_VERSION,
            )

        return model_record

    # ========================================================================
    # Registration
    # ========================================================================

    def _register_model(
        self,
        model_record: Dict[str, Any],
    ) -> Any:

        registry = self._require(
            self.registry,
            "ModelRegistry",
        )

        _assert_model_contract(
            model_record
        )

        method_names = (
            "register",
            "register_model",
        )

        method_found = False

        for method_name in method_names:
            method = getattr(
                registry,
                method_name,
                None,
            )

            if not callable(method):
                continue

            method_found = True

            attempts = (
                lambda: method(model_record),
                lambda: method(record=model_record),
                lambda: method(model=model_record),
            )

            for attempt in attempts:
                try:
                    return attempt()
                except TypeError:
                    continue

        if not method_found:
            raise ModelRegistrationError(
                "ModelRegistry does not expose "
                "a supported register method."
            )

        raise ModelRegistrationError(
            "ModelRegistry register method "
            "could not be invoked with a supported signature."
        )

    # ========================================================================
    # Verification
    # ========================================================================

    def verify(
        self,
        model_record: Any,
    ) -> Dict[str, Any]:
        """
        Validate model metadata and delegate integrity verification
        to ModelLoader.
        """

        self._statistics[
            "verification_runs"
        ] += 1

        record = _object_to_dict(
            model_record
        )

        _assert_model_contract(
            record
        )

        loader = self._require(
            self.loader,
            "ModelLoader",
        )

        path = record.get("model_path")

        if path is None:
            path = record.get("model_file")

        expected_hash = record.get(
            "model_hash"
        )

        method_names = (
            "verify",
            "verify_model",
            "verify_record",
        )

        verification_result = None
        method_found = False

        for method_name in method_names:
            method = getattr(
                loader,
                method_name,
                None,
            )

            if not callable(method):
                continue

            method_found = True

            attempts = []

            if (
                path is not None
                and expected_hash is not None
            ):
                attempts.extend(
                    [
                        lambda: method(
                            path,
                            expected_hash,
                        ),
                        lambda: method(
                            model_path=path,
                            expected_hash=expected_hash,
                        ),
                    ]
                )

            attempts.append(
                lambda: method(record)
            )

            for attempt in attempts:
                try:
                    verification_result = attempt()
                    break
                except TypeError:
                    continue

            if verification_result is not None:
                break

        if not method_found:
            raise ModelVerificationError(
                "ModelLoader does not expose "
                "a supported verification method."
            )

        if verification_result is None:
            raise ModelVerificationError(
                "ModelLoader verification method "
                "could not be invoked."
            )

        verification_dict = _normalize_status(
            verification_result
        )

        if not _is_success(
            verification_result
        ):
            raise ModelVerificationError(
                _extract_error(
                    verification_result,
                    "Model integrity verification failed.",
                )
            )

        self._statistics[
            "successful_verifications"
        ] += 1

        return verification_dict

    # ========================================================================
    # Activation
    # ========================================================================

    def activate(
        self,
        version: str,
    ) -> Dict[str, Any]:
        """
        Activate a registered model version.

        Safety order:

            registry lookup
                ->
            contract validation
                ->
            integrity verification
                ->
            manager activation
        """

        self._statistics[
            "activation_runs"
        ] += 1

        if not isinstance(version, str):
            raise ModelActivationError(
                "Model version must be a string."
            )

        version = version.strip()

        if not version:
            raise ModelActivationError(
                "A model version is required for activation."
            )

        record = self._registry_get(
            version
        )

        _assert_model_contract(
            record
        )

        self.verify(
            record
        )

        result = self._manager_activate(
            version
        )

        result_dict = _normalize_status(
            result
        )

        if not _is_success(result):
            raise ModelActivationError(
                _extract_error(
                    result,
                    (
                        "Failed to activate "
                        f"model version {version}."
                    ),
                )
            )

        self._statistics[
            "successful_activations"
        ] += 1

        self._statistics[
            "last_model_version"
        ] = version

        return result_dict

    # ========================================================================
    # Registry lookup
    # ========================================================================

    def _registry_get(
        self,
        version: str,
    ) -> Dict[str, Any]:

        registry = self._require(
            self.registry,
            "ModelRegistry",
        )

        method_names = (
            "get",
            "get_model",
            "get_record",
        )

        method_found = False

        for method_name in method_names:
            method = getattr(
                registry,
                method_name,
                None,
            )

            if not callable(method):
                continue

            method_found = True

            attempts = (
                lambda: method(version),
                lambda: method(version=version),
            )

            for attempt in attempts:
                try:
                    result = attempt()

                    if result is None:
                        continue

                    record = _object_to_dict(
                        result
                    )

                    if record:
                        return record

                except TypeError:
                    continue

        if not method_found:
            raise ModelActivationError(
                "ModelRegistry does not expose "
                "a supported lookup method."
            )

        raise ModelActivationError(
            f"Model version {version!r} "
            "was not found in Registry."
        )

    # ========================================================================
    # Manager activation
    # ========================================================================

    def _manager_activate(
        self,
        version: str,
    ) -> Any:

        manager = self._require(
            self.manager,
            "ModelManager",
        )

        method_names = (
            "activate",
            "activate_version",
            "activate_model",
        )

        method_found = False

        for method_name in method_names:
            method = getattr(
                manager,
                method_name,
                None,
            )

            if not callable(method):
                continue

            method_found = True

            attempts = (
                lambda: method(version),
                lambda: method(version=version),
            )

            for attempt in attempts:
                try:
                    return attempt()
                except TypeError:
                    continue

        if not method_found:
            raise ModelActivationError(
                "ModelManager does not expose "
                "a supported activation method."
            )

        raise ModelActivationError(
            "ModelManager activation method "
            "could not be invoked."
        )

    # ========================================================================
    # Reload
    # ========================================================================

    def reload(
        self,
        version: Optional[str] = None,
    ) -> LifecycleResult:

        started_at = _iso_now()
        started = time.perf_counter()

        self._statistics[
            "reload_runs"
        ] += 1

        try:
            manager = self._require(
                self.manager,
                "ModelManager",
            )

            if version is not None:
                if not isinstance(version, str):
                    raise ModelVerificationError(
                        "Reload version must be a string."
                    )

                version = version.strip()

                if not version:
                    raise ModelVerificationError(
                        "Reload version cannot be empty."
                    )

                record = self._registry_get(
                    version
                )

                _assert_model_contract(
                    record
                )

                self.verify(
                    record
                )

            method_names = (
                "reload",
                "reload_model",
            )

            method_found = False
            result = None

            for method_name in method_names:
                method = getattr(
                    manager,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                method_found = True

                attempts = []

                if version is not None:
                    attempts.extend(
                        [
                            lambda: method(version),
                            lambda: method(
                                version=version
                            ),
                        ]
                    )
                else:
                    attempts.append(
                        lambda: method()
                    )

                for attempt in attempts:
                    try:
                        result = attempt()
                        break
                    except TypeError:
                        continue

                if result is not None:
                    break

            if not method_found:
                raise TrainingServiceError(
                    "ModelManager does not expose "
                    "a supported reload method."
                )

            if result is None:
                raise TrainingServiceError(
                    "ModelManager reload method "
                    "could not be invoked."
                )

            result_dict = _normalize_status(
                result
            )

            if not _is_success(result):
                raise TrainingServiceError(
                    _extract_error(
                        result,
                        "Model reload failed.",
                    )
                )

            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            lifecycle_result = LifecycleResult(
                operation="reload",
                success=True,
                status="SUCCESS",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_name=MODEL_NAME,
                model_version=version,
                details=result_dict,
            )

            self._statistics[
                "successful_reloads"
            ] += 1

            self._last_result = lifecycle_result

            return lifecycle_result

        except Exception as exc:
            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            lifecycle_result = LifecycleResult(
                operation="reload",
                success=False,
                status="FAILED",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_name=MODEL_NAME,
                model_version=version,
                error=str(exc),
            )

            self._last_result = lifecycle_result

            LOGGER.exception(
                "Model reload failed."
            )

            return lifecycle_result

    # ========================================================================
    # Deactivation
    # ========================================================================

    def deactivate(self) -> LifecycleResult:

        started_at = _iso_now()
        started = time.perf_counter()

        self._statistics[
            "deactivation_runs"
        ] += 1

        try:
            manager = self._require(
                self.manager,
                "ModelManager",
            )

            method_names = (
                "deactivate",
                "deactivate_model",
            )

            method_found = False
            result = None

            for method_name in method_names:
                method = getattr(
                    manager,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                method_found = True

                try:
                    result = method()
                    break
                except TypeError:
                    continue

            if not method_found:
                raise TrainingServiceError(
                    "ModelManager does not expose "
                    "a supported deactivation method."
                )

            if result is None:
                raise TrainingServiceError(
                    "ModelManager deactivation method "
                    "could not be invoked."
                )

            result_dict = _normalize_status(
                result
            )

            if not _is_success(result):
                raise TrainingServiceError(
                    _extract_error(
                        result,
                        "Model deactivation failed.",
                    )
                )

            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            lifecycle_result = LifecycleResult(
                operation="deactivate",
                success=True,
                status="SUCCESS",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_name=MODEL_NAME,
                previous_version=result_dict.get(
                    "previous_version"
                ),
                details=result_dict,
            )

            self._statistics[
                "successful_deactivations"
            ] += 1

            self._last_result = lifecycle_result

            return lifecycle_result

        except Exception as exc:
            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            lifecycle_result = LifecycleResult(
                operation="deactivate",
                success=False,
                status="FAILED",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_name=MODEL_NAME,
                error=str(exc),
            )

            self._last_result = lifecycle_result

            LOGGER.exception(
                "Model deactivation failed."
            )

            return lifecycle_result

    # ========================================================================
    # Version switching
    # ========================================================================

    def switch_version(
        self,
        version: str,
    ) -> LifecycleResult:
        """
        Safely switch the active model version.

        The target model is verified before activation.
        """

        started_at = _iso_now()
        started = time.perf_counter()

        self._statistics[
            "switch_runs"
        ] += 1

        previous_version = None

        try:
            if not isinstance(version, str):
                raise ModelActivationError(
                    "Target model version must be a string."
                )

            version = version.strip()

            if not version:
                raise ModelActivationError(
                    "Target model version is required."
                )

            manager_status = self.status().get(
                "manager",
                {},
            )

            active_model = (
                manager_status.get(
                    "active_model"
                )
                or {}
            )

            previous_version = active_model.get(
                "version"
            )

            # --------------------------------------------------------------
            # 1. Resolve target
            # --------------------------------------------------------------

            target_record = self._registry_get(
                version
            )

            _assert_model_contract(
                target_record
            )

            # --------------------------------------------------------------
            # 2. Verify target
            # --------------------------------------------------------------

            verification = self.verify(
                target_record
            )

            # --------------------------------------------------------------
            # 3. Activate target
            # --------------------------------------------------------------

            activation = self._manager_activate(
                version
            )

            activation_dict = _normalize_status(
                activation
            )

            if not _is_success(
                activation
            ):
                raise ModelActivationError(
                    _extract_error(
                        activation,
                        (
                            "Failed to switch "
                            f"to model {version}."
                        ),
                    )
                )

            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            lifecycle_result = LifecycleResult(
                operation="switch_version",
                success=True,
                status="SUCCESS",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_name=MODEL_NAME,
                model_version=version,
                previous_version=previous_version,
                details={
                    "target_model": target_record,
                    "verification": verification,
                    "activation": activation_dict,
                },
            )

            self._statistics[
                "successful_switches"
            ] += 1

            self._statistics[
                "last_model_version"
            ] = version

            self._last_result = lifecycle_result

            return lifecycle_result

        except Exception as exc:
            completed_at = _iso_now()
            duration_ms = _elapsed_ms(started)

            lifecycle_result = LifecycleResult(
                operation="switch_version",
                success=False,
                status="FAILED",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                model_name=MODEL_NAME,
                model_version=version,
                previous_version=previous_version,
                error=str(exc),
            )

            self._last_result = lifecycle_result

            LOGGER.exception(
                "Model version switch failed."
            )

            return lifecycle_result

    # ========================================================================
    # Status
    # ========================================================================

    def status(self) -> Dict[str, Any]:
        """
        Return complete machine-readable service status.
        """

        total_runs = self._statistics[
            "total_lifecycle_runs"
        ]

        if total_runs > 0:
            average_duration = round(
                self._statistics[
                    "total_duration_ms"
                ] / total_runs,
                3,
            )
        else:
            average_duration = 0.0

        statistics = copy.deepcopy(
            self._statistics
        )

        statistics[
            "average_duration_ms"
        ] = average_duration

        manager_status: Dict[str, Any] = {}

        if self.manager is not None:
            manager_status = self._read_status(
                self.manager
            )

        return {
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "schema_version": SCHEMA_VERSION,

            "model": {
                "name": MODEL_NAME,
                "version": MODEL_VERSION,
                "schema_version": MODEL_SCHEMA_VERSION,
                "feature_count": len(FEATURE_NAMES),
                "feature_names": list(FEATURE_NAMES),
                "minimum_samples": self.minimum_samples,
            },

            "lifecycle": {
                "validation": True,
                "training": True,
                "registration": True,
                "verification": True,
                "activation": True,
                "reload": True,
                "deactivation": True,
                "version_switching": True,
            },

            "active_model": (
                manager_status.get("active_model")
                if manager_status
                else None
            ),

            "manager": manager_status,

            "last_result": (
                self._last_result.to_dict()
                if self._last_result is not None
                else None
            ),

            "statistics": statistics,

            "safety": {
                "baseline_production_allowed": False,
                "untrained_production_allowed": False,
                "schema_validation": True,
                "feature_contract_validation": True,
                "registry_required": True,
                "loader_verification_required": True,
                "direct_pickle_loading": False,
                "shell_execution": False,
                "network_operations": False,
                "security_actions": False,
            },

            "created_at": self._created_at,
        }

    def _read_status(
        self,
        component: Any,
    ) -> Dict[str, Any]:

        method = getattr(
            component,
            "status",
            None,
        )

        if not callable(method):
            return {}

        try:
            return _normalize_status(
                method()
            )
        except Exception as exc:
            return {
                "error": str(exc)
            }

    # ========================================================================
    # Statistics accounting
    # ========================================================================

    def _record_success(
        self,
        result: LifecycleResult,
        model_version: Optional[str],
    ) -> None:

        self._statistics[
            "successful_lifecycle_runs"
        ] += 1

        self._statistics[
            "total_duration_ms"
        ] += result.duration_ms

        self._statistics[
            "last_run_id"
        ] = result.run_id

        self._statistics[
            "last_model_version"
        ] = model_version

        self._last_result = result

    def _record_failure(
        self,
        result: LifecycleResult,
    ) -> None:

        self._statistics[
            "failed_lifecycle_runs"
        ] += 1

        self._statistics[
            "total_duration_ms"
        ] += result.duration_ms

        self._statistics[
            "last_run_id"
        ] = result.run_id

        self._last_result = result

    # ========================================================================
    # Result helpers
    # ========================================================================

    @staticmethod
    def _training_succeeded(
        result: Any,
    ) -> bool:

        result_dict = _object_to_dict(
            result
        )

        status = result_dict.get(
            "status"
        )

        if isinstance(status, str):
            if status.upper().strip() in {
                "SUCCESS",
                "SUCCEEDED",
                "OK",
            }:
                return True

            if status.upper().strip() in {
                "FAILED",
                "FAILURE",
                "ERROR",
            }:
                return False

        training_status = result_dict.get(
            "training_status"
        )

        if isinstance(training_status, str):
            return (
                training_status.upper().strip()
                in {
                    "SUCCESS",
                    "SUCCEEDED",
                    "OK",
                }
            )

        return _is_success(result)

    @staticmethod
    def _registration_succeeded(
        result: Any,
    ) -> bool:

        if result is None:
            return False

        return _is_success(result)

    @staticmethod
    def _new_run_id() -> str:

        timestamp = _utc_now().strftime(
            "%Y%m%d-%H%M%S"
        )

        suffix = uuid.uuid4().hex[:8]

        return (
            f"lifecycle-{timestamp}-{suffix}"
        )

    # ========================================================================
    # Self-test
    # ========================================================================

    @staticmethod
    def _self_test() -> None:
        """
        Complete isolated service-level self-test.

        No real registry, model file, shell, network, or production
        manager is touched.
        """

        print("=" * 78)
        print(
            "EnterpriseGuard Training Service - Self Test"
        )
        print("=" * 78)
        print()

        # --------------------------------------------------------------------
        # Demo dataset
        # --------------------------------------------------------------------

        dataset = {
            "dataset_type": "TrainingDataset",
            "total_samples": 8,
            "feature_count": 7,
            "feature_names": list(FEATURE_NAMES),
        }

        # --------------------------------------------------------------------
        # Canonical model record
        # --------------------------------------------------------------------

        model_record = {
            "name": MODEL_NAME,
            "version": "3.0.0",
            "schema_version": MODEL_SCHEMA_VERSION,
            "feature_count": len(FEATURE_NAMES),
            "feature_names": list(FEATURE_NAMES),
            "model_type": "LogisticRegression",
            "trained": True,
            "baseline": False,
            "training_samples": 8,
            "model_hash": "a" * 64,
            "model_path": "trusted-test-model.pkl",
        }

        # --------------------------------------------------------------------
        # Fake orchestrator
        # --------------------------------------------------------------------

        class FakeOrchestrator:

            def validate_dataset(
                self,
                value,
            ):
                return {
                    "valid": True,
                    "total_samples": 8,
                    "benign_samples": 4,
                    "threat_samples": 4,
                    "feature_count": 7,
                    "errors": [],
                    "warnings": [],
                }

            def train(
                self,
                value,
            ):
                return {
                    "status": "SUCCESS",
                    "training_result": dict(
                        model_record
                    ),
                }

        # --------------------------------------------------------------------
        # Fake registry
        # --------------------------------------------------------------------

        class FakeRegistry:

            def __init__(self):
                self.models = {
                    "3.0.0": dict(model_record)
                }

            def register(
                self,
                record,
            ):
                version = str(
                    record["version"]
                )

                self.models[
                    version
                ] = dict(record)

                return {
                    "success": True,
                    **record,
                }

            def get(
                self,
                version,
            ):
                return self.models.get(
                    str(version)
                )

        # --------------------------------------------------------------------
        # Fake loader
        # --------------------------------------------------------------------

        class FakeLoader:

            def verify(
                self,
                record,
            ):
                return {
                    "success": True,
                    "model_name": MODEL_NAME,
                    "model_version": record[
                        "version"
                    ],
                    "actual_hash": record[
                        "model_hash"
                    ],
                    "expected_hash": record[
                        "model_hash"
                    ],
                }

        # --------------------------------------------------------------------
        # Fake manager
        # --------------------------------------------------------------------

        class FakeManager:

            def __init__(self):
                self.active = False
                self.version = None

            def activate(
                self,
                version,
            ):
                previous = self.version

                self.version = str(version)
                self.active = True

                return {
                    "success": True,
                    "version": self.version,
                    "previous_version": previous,
                    "active": True,
                }

            def reload(
                self,
                version=None,
            ):
                target = (
                    version
                    if version is not None
                    else self.version
                )

                return {
                    "success": True,
                    "version": target,
                    "active": True,
                }

            def deactivate(self):
                previous = self.version

                self.version = None
                self.active = False

                return {
                    "success": True,
                    "previous_version": previous,
                    "active": False,
                }

            def status(self):
                return {
                    "active": self.active,
                    "active_model": (
                        {
                            "name": MODEL_NAME,
                            "version": self.version,
                            "trained": True,
                            "baseline": False,
                        }
                        if self.active
                        else None
                    ),
                }

        # --------------------------------------------------------------------
        # Service construction
        # --------------------------------------------------------------------

        service = TrainingService(
            orchestrator=FakeOrchestrator(),
            registry=FakeRegistry(),
            loader=FakeLoader(),
            manager=FakeManager(),
        )

        # --------------------------------------------------------------------
        # [1] Creation
        # --------------------------------------------------------------------

        print("[1] Service creation")

        status = service.status()

        assert status["service"] == SERVICE_NAME
        assert status["version"] == SERVICE_VERSION
        assert status["model"]["feature_count"] == 7
        assert status["model"]["minimum_samples"] == 4

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [2] Validation
        # --------------------------------------------------------------------

        print("[2] Dataset validation")

        validation = service.validate(
            dataset
        )

        assert validation["valid"] is True
        assert validation["total_samples"] == 8

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [3] Full lifecycle
        # --------------------------------------------------------------------

        print("[3] Full lifecycle")

        lifecycle = service.run(
            dataset,
            register=True,
            activate=True,
        )

        assert lifecycle.success is True
        assert lifecycle.status == "SUCCESS"
        assert lifecycle.operation == "train"
        assert lifecycle.model_version == "3.0.0"

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [4] Active model
        # --------------------------------------------------------------------

        print("[4] Active model")

        manager_status = service.manager.status()

        assert manager_status["active"] is True
        assert (
            manager_status[
                "active_model"
            ]["version"]
            == "3.0.0"
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [5] Result immutability
        # --------------------------------------------------------------------

        print("[5] LifecycleResult immutability")

        immutable_failed = False

        try:
            lifecycle.status = "MODIFIED"
        except Exception:
            immutable_failed = True

        assert immutable_failed is True

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [6] Detached result dictionary
        # --------------------------------------------------------------------

        print("[6] Detached result dictionary")

        exported = lifecycle.to_dict()

        exported["details"]["validation"]["valid"] = False

        assert (
            lifecycle.details["validation"]["valid"]
            is True
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [7] Baseline rejection
        # --------------------------------------------------------------------

        print("[7] Baseline rejection")

        baseline = dict(model_record)

        baseline["version"] = "2.0.0"
        baseline["trained"] = False
        baseline["baseline"] = True

        service.registry.models[
            "2.0.0"
        ] = baseline

        baseline_failed = False

        try:
            service.activate("2.0.0")
        except ModelVerificationError:
            baseline_failed = True

        assert baseline_failed is True

        assert (
            service.manager.status()[
                "active_model"
            ]["version"]
            == "3.0.0"
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [8] Schema rejection
        # --------------------------------------------------------------------

        print("[8] Schema rejection")

        incompatible = dict(model_record)

        incompatible["version"] = "2.1.0"
        incompatible["schema_version"] = 999

        service.registry.models[
            "2.1.0"
        ] = incompatible

        schema_failed = False

        try:
            service.activate("2.1.0")
        except ModelVerificationError:
            schema_failed = True

        assert schema_failed is True

        assert (
            service.manager.status()[
                "active_model"
            ]["version"]
            == "3.0.0"
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [9] Feature contract rejection
        # --------------------------------------------------------------------

        print(
            "[9] Feature contract rejection"
        )

        incompatible_features = dict(
            model_record
        )

        incompatible_features["version"] = "2.2.0"
        incompatible_features["feature_names"] = [
            "wrong_feature"
        ]

        service.registry.models[
            "2.2.0"
        ] = incompatible_features

        feature_failed = False

        try:
            service.activate("2.2.0")
        except ModelVerificationError:
            feature_failed = True

        assert feature_failed is True

        assert (
            service.manager.status()[
                "active_model"
            ]["version"]
            == "3.0.0"
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [10] Reload
        # --------------------------------------------------------------------

        print("[10] Reload")

        reload_result = service.reload(
            "3.0.0"
        )

        assert reload_result.success is True
        assert reload_result.status == "SUCCESS"

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [11] Version switch
        # --------------------------------------------------------------------

        print("[11] Version switch")

        second_model = dict(
            model_record
        )

        second_model["version"] = "3.1.0"
        second_model["model_hash"] = "b" * 64

        service.registry.models[
            "3.1.0"
        ] = second_model

        switch_result = service.switch_version(
            "3.1.0"
        )

        assert switch_result.success is True
        assert (
            switch_result.model_version
            == "3.1.0"
        )
        assert (
            switch_result.previous_version
            == "3.0.0"
        )

        assert (
            service.manager.status()[
                "active_model"
            ]["version"]
            == "3.1.0"
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [12] Deactivation
        # --------------------------------------------------------------------

        print("[12] Deactivation")

        deactivate_result = service.deactivate()

        assert deactivate_result.success is True
        assert (
            service.manager.status()[
                "active"
            ]
            is False
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # [13] Final accounting
        # --------------------------------------------------------------------

        print("[13] Final accounting")

        final_status = service.status()
        statistics = final_status["statistics"]

        assert (
            statistics[
                "successful_lifecycle_runs"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_validations"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_trainings"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_registrations"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_verifications"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_activations"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_reloads"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_switches"
            ]
            >= 1
        )

        assert (
            statistics[
                "successful_deactivations"
            ]
            >= 1
        )

        assert (
            statistics[
                "average_duration_ms"
            ]
            >= 0.0
        )

        print("PASS")
        print()

        # --------------------------------------------------------------------
        # Final machine-readable status
        # --------------------------------------------------------------------

        print("[14] Final status")

        print(
            json.dumps(
                final_status,
                indent=2,
                default=str,
            )
        )

        print()
        print("=" * 78)
        print(
            "Training Service self-test completed successfully."
        )
        print("=" * 78)


# ============================================================================
# Module entry point
# ============================================================================


if __name__ == "__main__":
    TrainingService._self_test()