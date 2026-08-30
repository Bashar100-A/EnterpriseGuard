"""
EnterpriseGuard - Model Manager
================================

Production-facing orchestration layer above:

    ModelRegistry
          |
          v
      ModelLoader
          |
          v
    EnterpriseGuardModel

Responsibilities
----------------
- Select a compatible model version from the registry.
- Load models exclusively through ModelLoader.
- Enforce schema and feature-contract compatibility.
- Reject baseline models for production activation.
- Maintain the active production model.
- Perform safe model activation and version switching.
- Preserve the previous active model when activation fails.
- Provide a stable prediction API to higher layers.
- Expose manager status without leaking registry/loader internals.
- Support activate / deactivate / reload operations.
- Maintain operational statistics.
- Provide an isolated self-test.

Design principles
-----------------
- No shell execution.
- No network access.
- No security actions.
- No direct pickle loading.
- No direct filesystem model loading.
- No duplicated cryptographic integrity logic.
- ModelLoader remains the only component responsible for loading
  serialized model artifacts.
- ModelRegistry remains the source of registered model metadata.
- A baseline model can never become an active production model.
- Failed activation must not replace a healthy active model.
- Manager state must remain coherent with the model it publishes.

Version:
    1.1.1
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


# ============================================================================
# Canonical EnterpriseGuard model contract
# ============================================================================

MANAGER_NAME = "EnterpriseGuard Model Manager"
MANAGER_VERSION = "1.1.1"
MANAGER_SCHEMA_VERSION = 1

MODEL_NAME = "EnterpriseGuard Threat Intelligence Model"
MODEL_VERSION = "3.0.0"
MODEL_SCHEMA_VERSION = 1

FEATURE_NAMES: Tuple[str, ...] = (
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
# Exceptions
# ============================================================================

class ModelManagerError(RuntimeError):
    """Base exception for Model Manager failures."""


class ModelNotActiveError(ModelManagerError):
    """Raised when prediction is requested without an active model."""


class ModelActivationError(ModelManagerError):
    """Raised when a model cannot be safely activated."""


class ModelCompatibilityError(ModelManagerError):
    """Raised when a model violates the canonical model contract."""


class ModelPredictionError(ModelManagerError):
    """Raised when prediction cannot be completed."""


# ============================================================================
# Result types
# ============================================================================

@dataclass(frozen=True)
class ActivationResult:
    """Structured result of an activation operation."""

    success: bool
    version: Optional[str]
    previous_version: Optional[str]
    active: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionResult:
    """Normalized prediction result returned by the manager."""

    success: bool
    result: Dict[str, Any]
    model_version: Optional[str]
    processing_time_ms: float
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": dict(self.result),
            "model_version": self.model_version,
            "processing_time_ms": self.processing_time_ms,
            "error": self.error,
        }


# ============================================================================
# Model Manager
# ============================================================================

class ModelManager:
    """
    EnterpriseGuard production model orchestration layer.

    Registry:
        registration, versions and metadata.

    Loader:
        verification, integrity checking and model loading.

    Manager:
        selection, activation, switching, prediction and lifecycle state.
    """

    def __init__(
        self,
        registry: Optional[Any] = None,
        loader: Optional[Any] = None,
        *,
        expected_model_name: str = MODEL_NAME,
        expected_schema_version: int = MODEL_SCHEMA_VERSION,
        expected_feature_names: Sequence[str] = FEATURE_NAMES,
        auto_activate: bool = False,
    ) -> None:

        self._registry = registry
        self._loader = loader

        self._expected_model_name = str(expected_model_name)
        self._expected_schema_version = int(expected_schema_version)
        self._expected_feature_names = tuple(
            str(name)
            for name in expected_feature_names
        )

        if not self._expected_feature_names:
            raise ValueError(
                "expected_feature_names must not be empty."
            )

        self._validate_contract_definition()

        self._active_model: Optional[Any] = None
        self._active_record: Optional[Dict[str, Any]] = None
        self._active_version: Optional[str] = None

        self._created_at = self._utc_now()

        self._statistics: Dict[str, Any] = {
            "activation_attempts": 0,
            "successful_activations": 0,
            "failed_activations": 0,
            "deactivation_count": 0,
            "reload_attempts": 0,
            "successful_reloads": 0,
            "failed_reloads": 0,
            "prediction_count": 0,
            "successful_predictions": 0,
            "failed_predictions": 0,
            "total_prediction_ms": 0.0,
            "successful_prediction_ms": 0.0,
            "average_prediction_ms": 0.0,
            "average_successful_prediction_ms": 0.0,
            "model_switches": 0,
        }

        if self._registry is None or self._loader is None:
            self._build_default_dependencies()

        if auto_activate:
            self.activate()

    # ------------------------------------------------------------------
    # Dependency construction
    # ------------------------------------------------------------------

    def _build_default_dependencies(self) -> None:
        """Construct the real Registry and Loader."""

        from .model_registry import ModelRegistry
        from .model_loader import ModelLoader

        if self._registry is None:
            self._registry = ModelRegistry()

        if self._loader is None:
            self._loader = ModelLoader(
                registry=self._registry
            )

    # ------------------------------------------------------------------
    # Contract validation
    # ------------------------------------------------------------------

    def _validate_contract_definition(self) -> None:

        if self._expected_schema_version <= 0:
            raise ValueError(
                "expected_schema_version must be positive."
            )

        unique_features = tuple(
            dict.fromkeys(
                self._expected_feature_names
            )
        )

        if len(self._expected_feature_names) != len(
            unique_features
        ):
            raise ValueError(
                "expected_feature_names contains duplicates."
            )

        for name in self._expected_feature_names:
            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    "Every expected feature name must be "
                    "a non-empty string."
                )

    # ------------------------------------------------------------------
    # Registry record normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _record_value(
        record: Any,
        key: str,
        default: Any = None,
    ) -> Any:

        if record is None:
            return default

        if isinstance(record, Mapping):
            return record.get(key, default)

        return getattr(record, key, default)

    def _record_to_mapping(
        self,
        record: Any,
    ) -> Dict[str, Any]:

        if record is None:
            raise ModelCompatibilityError(
                "Model registry record is empty."
            )

        if isinstance(record, Mapping):
            return dict(record)

        try:
            values = vars(record)

            if isinstance(values, dict):
                return dict(values)

        except TypeError:
            pass

        fields = (
            "name",
            "version",
            "schema_version",
            "feature_count",
            "feature_names",
            "model_type",
            "trained",
            "baseline",
            "training_samples",
            "model_path",
            "model_hash",
        )

        normalized: Dict[str, Any] = {}

        for field in fields:
            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:
                normalized[field] = value

        if normalized:
            return normalized

        raise ModelCompatibilityError(
            "Unable to normalize the model registry record."
        )

    # ------------------------------------------------------------------
    # Model contract validation
    # ------------------------------------------------------------------

    def _validate_model_record(
        self,
        record: Any,
    ) -> Dict[str, Any]:

        normalized = self._record_to_mapping(record)

        name = normalized.get("name")

        if name != self._expected_model_name:
            raise ModelCompatibilityError(
                f"Incompatible model name: {name!r}. "
                f"Expected {self._expected_model_name!r}."
            )

        version = normalized.get("version")

        if not isinstance(version, str) or not version.strip():
            raise ModelCompatibilityError(
                "Registered model has no valid version."
            )

        normalized["version"] = version.strip()

        schema_version = normalized.get(
            "schema_version"
        )

        try:
            schema_version = int(schema_version)
        except (TypeError, ValueError) as exc:
            raise ModelCompatibilityError(
                "Registered model schema_version must be an integer."
            ) from exc

        if schema_version != self._expected_schema_version:
            raise ModelCompatibilityError(
                f"Incompatible schema_version: "
                f"{schema_version!r}. "
                f"Expected {self._expected_schema_version}."
            )

        normalized["schema_version"] = schema_version

        trained = bool(
            normalized.get("trained", False)
        )

        baseline = bool(
            normalized.get("baseline", False)
        )

        if not trained:
            raise ModelCompatibilityError(
                "Baseline or untrained models cannot be activated."
            )

        if baseline:
            raise ModelCompatibilityError(
                "Baseline models are prohibited as "
                "production models."
            )

        normalized["trained"] = trained
        normalized["baseline"] = baseline

        feature_names = tuple(
            str(name)
            for name in (
                normalized.get("feature_names")
                or ()
            )
        )

        if feature_names != self._expected_feature_names:
            raise ModelCompatibilityError(
                "Model feature contract is incompatible. "
                f"Expected {list(self._expected_feature_names)!r}, "
                f"received {list(feature_names)!r}."
            )

        normalized["feature_names"] = feature_names

        feature_count = normalized.get(
            "feature_count"
        )

        try:
            feature_count = int(feature_count)
        except (TypeError, ValueError) as exc:
            raise ModelCompatibilityError(
                "Registered model feature_count must be an integer."
            ) from exc

        if feature_count != len(
            self._expected_feature_names
        ):
            raise ModelCompatibilityError(
                f"Incompatible feature_count: "
                f"{feature_count!r}. "
                f"Expected {len(self._expected_feature_names)}."
            )

        normalized["feature_count"] = feature_count

        model_hash = normalized.get(
            "model_hash"
        )

        if (
            not isinstance(model_hash, str)
            or len(model_hash.strip()) != 64
        ):
            raise ModelCompatibilityError(
                "Registered trained model must contain "
                "a valid SHA-256 hash."
            )

        model_hash = model_hash.strip().lower()

        try:
            int(model_hash, 16)
        except ValueError as exc:
            raise ModelCompatibilityError(
                "Registered model hash contains "
                "non-hexadecimal characters."
            ) from exc

        normalized["model_hash"] = model_hash

        return normalized

    # ------------------------------------------------------------------
    # Registry adapters
    # ------------------------------------------------------------------

    def _registry_get(
        self,
        version: Optional[str] = None,
    ) -> Any:

        registry = self._registry

        if registry is None:
            raise ModelManagerError(
                "Model registry is not configured."
            )

        if version is not None:

            for method_name in (
                "get",
                "get_model",
                "get_version",
            ):
                method = getattr(
                    registry,
                    method_name,
                    None,
                )

                if callable(method):

                    try:
                        record = method(version)

                    except KeyError:
                        continue

                    if record is not None:
                        return record

            return None

        for method_name in (
            "get_latest",
            "latest",
            "get_active",
            "get_current",
            "get",
        ):
            method = getattr(
                registry,
                method_name,
                None,
            )

            if callable(method):

                try:
                    record = method()

                except TypeError:
                    continue

                if record is not None:
                    return record

        return None

    def _registry_list(self) -> Iterable[Any]:

        registry = self._registry

        if registry is None:
            raise ModelManagerError(
                "Model registry is not configured."
            )

        for method_name in (
            "list",
            "list_models",
        ):
            method = getattr(
                registry,
                method_name,
                None,
            )

            if callable(method):
                return method()

        raise ModelManagerError(
            "Configured registry does not provide "
            "list() or list_models()."
        )

    def _select_version(
        self,
        version: Optional[str],
    ) -> str:

        if version is not None:

            record = self._registry_get(
                version
            )

            if record is None:
                raise ModelActivationError(
                    f"Model version {version!r} "
                    "is not registered."
                )

            normalized = self._validate_model_record(
                record
            )

            return str(
                normalized["version"]
            )

        records = list(
            self._registry_list()
        )

        if not records:
            raise ModelActivationError(
                "No registered models are available."
            )

        compatible: list[Dict[str, Any]] = []

        for record in records:

            try:
                normalized = self._validate_model_record(
                    record
                )

            except ModelCompatibilityError:
                continue

            compatible.append(normalized)

        if not compatible:
            raise ModelActivationError(
                "No compatible trained non-baseline "
                "model is registered."
            )

        compatible.sort(
            key=lambda item: self._version_sort_key(
                str(item["version"])
            ),
            reverse=True,
        )

        return str(
            compatible[0]["version"]
        )

    @staticmethod
    def _version_sort_key(
        version: str,
    ) -> Tuple[Any, ...]:

        parts = version.strip().split(".")

        result: list[Any] = []

        for part in parts:

            try:
                result.append(
                    (0, int(part))
                )

            except ValueError:
                result.append(
                    (1, part.lower())
                )

        return tuple(result)

    # ------------------------------------------------------------------
    # Loader adapters
    # ------------------------------------------------------------------

    def _loader_load(
        self,
        version: str,
    ) -> Any:

        loader = self._loader

        if loader is None:
            raise ModelManagerError(
                "Model loader is not configured."
            )

        load = getattr(
            loader,
            "load",
            None,
        )

        if not callable(load):
            raise ModelManagerError(
                "Configured loader does not provide load()."
            )

        return load(version)

    def _loader_verify(
        self,
        version: str,
    ) -> Any:

        loader = self._loader

        if loader is None:
            raise ModelManagerError(
                "Model loader is not configured."
            )

        verify = getattr(
            loader,
            "verify",
            None,
        )

        if not callable(verify):
            raise ModelManagerError(
                "Configured loader does not provide verify()."
            )

        return verify(version)

    def _loader_get_model(self) -> Any:

        loader = self._loader

        if loader is None:
            raise ModelManagerError(
                "Model loader is not configured."
            )

        getter = getattr(
            loader,
            "get_loaded_model",
            None,
        )

        if not callable(getter):
            raise ModelManagerError(
                "Configured loader does not provide "
                "get_loaded_model()."
            )

        return getter()

    def _loader_get_record(self) -> Any:

        loader = self._loader

        if loader is None:
            raise ModelManagerError(
                "Model loader is not configured."
            )

        getter = getattr(
            loader,
            "get_loaded_record",
            None,
        )

        if not callable(getter):
            raise ModelManagerError(
                "Configured loader does not provide "
                "get_loaded_record()."
            )

        return getter()

    def _loader_unload(self) -> None:

        loader = self._loader

        if loader is None:
            return

        unload = getattr(
            loader,
            "unload",
            None,
        )

        if not callable(unload):
            raise ModelManagerError(
                "Configured loader does not provide unload()."
            )

        unload()

    # ------------------------------------------------------------------
    # Loader state
    # ------------------------------------------------------------------

    def _capture_loader_state(self) -> Dict[str, Any]:

        loader = self._loader

        if loader is None:
            return {
                "loaded": False,
                "model": None,
                "record": None,
            }

        loaded = bool(
            getattr(
                loader,
                "loaded",
                False,
            )
        )

        if not loaded:
            return {
                "loaded": False,
                "model": None,
                "record": None,
            }

        try:
            model = self._loader_get_model()
            record = self._loader_get_record()

        except Exception:
            return {
                "loaded": False,
                "model": None,
                "record": None,
            }

        return {
            "loaded": model is not None,
            "model": model,
            "record": record,
        }

    # ------------------------------------------------------------------
    # Active model management
    # ------------------------------------------------------------------

    def activate(
        self,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:

        self._statistics[
            "activation_attempts"
        ] += 1

        previous_version = self._active_version

        previous_manager_state = {
            "model": self._active_model,
            "record": self._active_record,
            "version": self._active_version,
        }

        previous_loader_state = (
            self._capture_loader_state()
        )

        try:

            # ----------------------------------------------------------
            # 1. Select version
            # ----------------------------------------------------------

            selected_version = self._select_version(
                version
            )

            # ----------------------------------------------------------
            # 2. Validate registry metadata
            # ----------------------------------------------------------

            registry_record = self._registry_get(
                selected_version
            )

            if registry_record is None:
                raise ModelActivationError(
                    f"Model version {selected_version!r} "
                    "is no longer available in the registry."
                )

            self._validate_model_record(
                registry_record
            )

            # ----------------------------------------------------------
            # 3. Verify artifact through Loader
            # ----------------------------------------------------------

            verification = self._loader_verify(
                selected_version
            )

            if not self._operation_succeeded(
                verification
            ):
                raise ModelActivationError(
                    self._extract_operation_error(
                        verification,
                        "Model verification failed.",
                    )
                )

            # ----------------------------------------------------------
            # 4. Load through Loader
            # ----------------------------------------------------------

            loaded_result = self._loader_load(
                selected_version
            )

            if not self._operation_succeeded(
                loaded_result
            ):
                raise ModelActivationError(
                    self._extract_operation_error(
                        loaded_result,
                        "Model loading failed.",
                    )
                )

            # ----------------------------------------------------------
            # 5. Read loaded state
            # ----------------------------------------------------------

            loaded_model = self._loader_get_model()
            loaded_record = self._loader_get_record()

            if loaded_model is None:
                raise ModelActivationError(
                    "Loader reported success but no model "
                    "is available."
                )

            if loaded_record is None:
                raise ModelActivationError(
                    "Loader reported success but no model "
                    "record is available."
                )

            # ----------------------------------------------------------
            # 6. Validate loaded record
            # ----------------------------------------------------------

            normalized_record = (
                self._validate_model_record(
                    loaded_record
                )
            )

            loaded_version = str(
                normalized_record["version"]
            )

            if loaded_version != selected_version:
                raise ModelActivationError(
                    "Loaded model version does not match "
                    "the requested version."
                )

            # ----------------------------------------------------------
            # 7. Publish manager state
            # ----------------------------------------------------------

            self._active_model = loaded_model
            self._active_record = normalized_record
            self._active_version = loaded_version

            self._statistics[
                "successful_activations"
            ] += 1

            if (
                previous_version is not None
                and previous_version != loaded_version
            ):
                self._statistics[
                    "model_switches"
                ] += 1

            return ActivationResult(
                success=True,
                version=loaded_version,
                previous_version=previous_version,
                active=True,
            ).to_dict()

        except Exception as exc:

            self._statistics[
                "failed_activations"
            ] += 1

            # ----------------------------------------------------------
            # Restore Manager state.
            # ----------------------------------------------------------

            self._active_model = (
                previous_manager_state["model"]
            )

            self._active_record = (
                previous_manager_state["record"]
            )

            self._active_version = (
                previous_manager_state["version"]
            )

            # ----------------------------------------------------------
            # Important safety rule:
            #
            # If a failed activation caused the Loader to load another
            # model, unload that model.
            #
            # If the Loader was already holding the previous model,
            # leave it untouched.
            # ----------------------------------------------------------

            try:
                current_loader_model = (
                    self._loader_get_model()
                )
            except Exception:
                current_loader_model = None

            previous_loader_model = (
                previous_loader_state["model"]
            )

            if (
                current_loader_model is not None
                and current_loader_model
                is not previous_loader_model
            ):
                try:
                    self._loader_unload()
                except Exception:
                    pass

            return ActivationResult(
                success=False,
                version=version,
                previous_version=previous_version,
                active=self.is_active(),
                error=str(exc),
            ).to_dict()

    def deactivate(self) -> Dict[str, Any]:

        previous_version = self._active_version

        try:
            self._loader_unload()

        except Exception as exc:
            return {
                "success": False,
                "active": self.is_active(),
                "previous_version": previous_version,
                "error": str(exc),
            }

        self._active_model = None
        self._active_record = None
        self._active_version = None

        self._statistics[
            "deactivation_count"
        ] += 1

        return {
            "success": True,
            "active": False,
            "previous_version": previous_version,
            "error": None,
        }

    def reload(self) -> Dict[str, Any]:

        self._statistics[
            "reload_attempts"
        ] += 1

        version = self._active_version

        try:

            if version is not None:
                result = self.activate(version)

            else:
                result = self.activate()

            if result.get("success"):
                self._statistics[
                    "successful_reloads"
                ] += 1
            else:
                self._statistics[
                    "failed_reloads"
                ] += 1

            return {
                "success": bool(
                    result.get("success")
                ),
                "version": result.get("version"),
                "active": self.is_active(),
                "error": result.get("error"),
            }

        except Exception as exc:

            self._statistics[
                "failed_reloads"
            ] += 1

            return {
                "success": False,
                "version": version,
                "active": self.is_active(),
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Prediction API
    # ------------------------------------------------------------------

    def predict(
        self,
        features: Mapping[str, Any],
    ) -> Dict[str, Any]:

        started = time.perf_counter()

        self._statistics[
            "prediction_count"
        ] += 1

        try:

            if not self.is_active():
                raise ModelNotActiveError(
                    "No active production model is available."
                )

            canonical_features = (
                self._normalize_features(
                    features
                )
            )

            model = self._active_model

            if model is None:
                raise ModelNotActiveError(
                    "Active model reference is unavailable."
                )

            predict_method = getattr(
                model,
                "predict",
                None,
            )

            if not callable(predict_method):
                raise ModelPredictionError(
                    "Active model does not provide predict()."
                )

            raw_result = predict_method(
                canonical_features
            )

            normalized_result = (
                self._normalize_prediction_result(
                    raw_result
                )
            )

            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1000.0

            self._statistics[
                "successful_predictions"
            ] += 1

            self._statistics[
                "total_prediction_ms"
            ] += elapsed_ms

            self._statistics[
                "successful_prediction_ms"
            ] += elapsed_ms

            successful_count = (
                self._statistics[
                    "successful_predictions"
                ]
            )

            total_count = (
                self._statistics[
                    "prediction_count"
                ]
            )

            self._statistics[
                "average_successful_prediction_ms"
            ] = (
                self._statistics[
                    "successful_prediction_ms"
                ]
                / successful_count
            )

            self._statistics[
                "average_prediction_ms"
            ] = (
                self._statistics[
                    "total_prediction_ms"
                ]
                / total_count
            )

            normalized_result.setdefault(
                "model_version",
                self._active_version,
            )

            normalized_result.setdefault(
                "processing_time_ms",
                round(
                    elapsed_ms,
                    3,
                ),
            )

            normalized_result.setdefault(
                "error",
                None,
            )

            return normalized_result

        except Exception as exc:

            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1000.0

            self._statistics[
                "failed_predictions"
            ] += 1

            self._statistics[
                "total_prediction_ms"
            ] += elapsed_ms

            total_count = (
                self._statistics[
                    "prediction_count"
                ]
            )

            if total_count:
                self._statistics[
                    "average_prediction_ms"
                ] = (
                    self._statistics[
                        "total_prediction_ms"
                    ]
                    / total_count
                )

            return {
                "predicted_class": None,
                "threat_probability": None,
                "benign_probability": None,
                "anomaly_score": None,
                "confidence": None,
                "model_available": self.is_active(),
                "model_trained": self.is_active(),
                "model_version": self._active_version,
                "processing_time_ms": round(
                    elapsed_ms,
                    3,
                ),
                "error": str(exc),
            }

    def _normalize_features(
        self,
        features: Mapping[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(
            features,
            Mapping,
        ):
            raise ModelPredictionError(
                "Features must be supplied as a mapping."
            )

        received = set(
            features.keys()
        )

        expected = set(
            self._expected_feature_names
        )

        missing = expected - received
        unexpected = received - expected

        if missing:
            raise ModelPredictionError(
                "Missing required features: "
                + ", ".join(
                    sorted(missing)
                )
            )

        if unexpected:
            raise ModelPredictionError(
                "Unexpected features supplied: "
                + ", ".join(
                    sorted(unexpected)
                )
            )

        return {
            name: features[name]
            for name in self._expected_feature_names
        }

    @staticmethod
    def _normalize_prediction_result(
        result: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            result,
            Mapping,
        ):
            return dict(result)

        raise ModelPredictionError(
            "EnterpriseGuardModel.predict() "
            "must return a mapping."
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_active(self) -> bool:

        return (
            self._active_model is not None
            and self._active_record is not None
            and self._active_version is not None
        )

    def active_version(self) -> Optional[str]:
        return self._active_version

    def status(self) -> Dict[str, Any]:

        active_record = self._active_record

        return {
            "manager": MANAGER_NAME,
            "version": MANAGER_VERSION,
            "schema_version": MANAGER_SCHEMA_VERSION,
            "expected_model": {
                "name": self._expected_model_name,
                "schema_version": (
                    self._expected_schema_version
                ),
                "feature_count": len(
                    self._expected_feature_names
                ),
                "feature_names": list(
                    self._expected_feature_names
                ),
            },
            "active": self.is_active(),
            "active_model": (
                {
                    "name": active_record.get("name"),
                    "version": active_record.get("version"),
                    "schema_version": active_record.get(
                        "schema_version"
                    ),
                    "model_type": active_record.get(
                        "model_type"
                    ),
                    "trained": bool(
                        active_record.get(
                            "trained"
                        )
                    ),
                    "baseline": bool(
                        active_record.get(
                            "baseline"
                        )
                    ),
                    "feature_count": active_record.get(
                        "feature_count"
                    ),
                    "feature_names": list(
                        active_record.get(
                            "feature_names"
                        )
                        or []
                    ),
                    "training_samples": active_record.get(
                        "training_samples"
                    ),
                    "model_hash": active_record.get(
                        "model_hash"
                    ),
                }
                if active_record is not None
                else None
            ),
            "statistics": dict(
                self._statistics
            ),
            "safety": {
                "baseline_activation_allowed": False,
                "requires_trained_model": True,
                "schema_validation": True,
                "feature_contract_validation": True,
                "loader_integrity_verification": True,
                "activation_state_preservation": True,
                "shell_execution": False,
                "network_operations": False,
                "security_actions": False,
                "direct_pickle_loading": False,
            },
            "created_at": self._created_at,
        }

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _operation_succeeded(
        result: Any,
    ) -> bool:

        if result is None:
            return False

        if isinstance(
            result,
            bool,
        ):
            return result

        if isinstance(
            result,
            Mapping,
        ):

            if "success" in result:
                return bool(
                    result["success"]
                )

            if "valid" in result:
                return bool(
                    result["valid"]
                )

            status = result.get(
                "status"
            )

            if isinstance(
                status,
                str,
            ):
                return status.upper() in {
                    "SUCCESS",
                    "OK",
                    "VALID",
                    "LOADED",
                }

        success_attr = getattr(
            result,
            "success",
            None,
        )

        if success_attr is not None:
            return bool(
                success_attr
            )

        valid_attr = getattr(
            result,
            "valid",
            None,
        )

        if valid_attr is not None:
            return bool(
                valid_attr
            )

        status_attr = getattr(
            result,
            "status",
            None,
        )

        if isinstance(
            status_attr,
            str,
        ):
            return status_attr.upper() in {
                "SUCCESS",
                "OK",
                "VALID",
                "LOADED",
            }

        return False

    @staticmethod
    def _extract_operation_error(
        result: Any,
        fallback: str,
    ) -> str:

        if isinstance(
            result,
            Mapping,
        ):

            error = result.get(
                "error"
            )

            if error:
                return str(error)

            errors = result.get(
                "errors"
            )

            if errors:
                return "; ".join(
                    str(item)
                    for item in errors
                )

        error_attr = getattr(
            result,
            "error",
            None
        )

        if error_attr:
            return str(
                error_attr
            )

        errors_attr = getattr(
            result,
            "errors",
            None
        )

        if errors_attr:
            return "; ".join(
                str(item)
                for item in errors_attr
            )

        return fallback

    # ------------------------------------------------------------------
    # Independent self-test
    # ------------------------------------------------------------------

    @staticmethod
    def _self_test() -> None:

        print("=" * 78)
        print(
            "EnterpriseGuard Model Manager - Self Test"
        )
        print("=" * 78)
        print()

        # ==============================================================
        # Fake model
        # ==============================================================

        class FakeModel:

            def predict(
                self,
                features: Mapping[str, Any],
            ) -> Dict[str, Any]:

                if tuple(features.keys()) != FEATURE_NAMES:
                    raise ValueError(
                        "Feature contract mismatch."
                    )

                return {
                    "predicted_class": 0,
                    "threat_probability": 0.03,
                    "benign_probability": 0.97,
                    "anomaly_score": 0.05,
                    "confidence": 97.0,
                    "model_available": True,
                    "model_trained": True,
                    "model_version": MODEL_VERSION,
                    "processing_time_ms": 0.1,
                    "error": None,
                }

        # ==============================================================
        # Records
        # ==============================================================

        good_record = {
            "name": MODEL_NAME,
            "version": MODEL_VERSION,
            "schema_version": MODEL_SCHEMA_VERSION,
            "feature_count": FEATURE_COUNT,
            "feature_names": list(
                FEATURE_NAMES
            ),
            "model_type": "LogisticRegression",
            "trained": True,
            "baseline": False,
            "training_samples": 8,
            "model_hash": "a" * 64,
        }

        baseline_record = {
            **good_record,
            "version": "2.0.0",
            "trained": False,
            "baseline": True,
            "training_samples": 0,
            "model_hash": "b" * 64,
        }

        incompatible_schema = {
            **good_record,
            "version": "2.1.0",
            "schema_version": 999,
        }

        incompatible_features = {
            **good_record,
            "version": "2.2.0",
            "feature_names": [
                "wrong_feature"
            ],
            "feature_count": 1,
        }

        # ==============================================================
        # Fake Registry
        # ==============================================================

        class FakeRegistry:

            def __init__(self) -> None:

                self.records = {
                    "2.0.0": baseline_record,
                    "2.1.0": incompatible_schema,
                    "2.2.0": incompatible_features,
                    "3.0.0": good_record,
                }

            def get(
                self,
                version: Optional[str] = None,
            ) -> Any:

                if version is None:
                    return self.records.get(
                        MODEL_VERSION
                    )

                return self.records.get(
                    version
                )

            def list(
                self,
            ) -> list[Dict[str, Any]]:

                return list(
                    self.records.values()
                )

        # ==============================================================
        # Fake Loader
        # ==============================================================

        class FakeLoader:

            def __init__(
                self,
                registry: FakeRegistry,
            ) -> None:

                self.registry = registry

                self.model: Optional[
                    FakeModel
                ] = None

                self.record: Optional[
                    Dict[str, Any]
                ] = None

            @property
            def loaded(self) -> bool:
                return self.model is not None

            def verify(
                self,
                version: str,
            ) -> Dict[str, Any]:

                record = self.registry.get(
                    version
                )

                if record is None:
                    return {
                        "success": False,
                        "error": "Model not found.",
                    }

                # Test loader allows all registry records to reach
                # the Manager so Manager-level compatibility gates
                # are actually exercised.

                return {
                    "success": True,
                    "model_version": version,
                }

            def load(
                self,
                version: str,
            ) -> Dict[str, Any]:

                record = self.registry.get(
                    version
                )

                if record is None:
                    return {
                        "success": False,
                        "error": "Model not found.",
                    }

                self.record = dict(
                    record
                )

                self.model = FakeModel()

                return {
                    "success": True,
                    "model_version": version,
                }

            def get_loaded_model(
                self,
            ) -> Any:

                if self.model is None:
                    raise ModelManagerError(
                        "No model loaded."
                    )

                return self.model

            def get_loaded_record(
                self,
            ) -> Any:

                if self.record is None:
                    raise ModelManagerError(
                        "No record loaded."
                    )

                return self.record

            def unload(
                self,
            ) -> None:

                self.model = None
                self.record = None

        # ==============================================================
        # Test setup
        # ==============================================================

        print(
            "[1] Creating manager"
        )

        registry = FakeRegistry()

        loader = FakeLoader(
            registry
        )

        manager = ModelManager(
            registry=registry,
            loader=loader,
        )

        status = manager.status()

        assert (
            status["manager"]
            == MANAGER_NAME
        )

        assert (
            status["active"]
            is False
        )

        assert (
            status["expected_model"][
                "feature_count"
            ]
            == FEATURE_COUNT
        )

        print(
            json.dumps(
                status,
                indent=2,
            )
        )

        print(
            "PASS - manager created."
        )
        print()

        # ==============================================================
        # Automatic version selection
        # ==============================================================

        print(
            "[2] Testing automatic version selection"
        )

        result = manager.activate()

        assert (
            result["success"]
            is True
        )

        assert (
            result["version"]
            == MODEL_VERSION
        )

        assert manager.is_active()

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

        print(
            "PASS - compatible version selected and activated."
        )
        print()

        # ==============================================================
        # Active model state
        # ==============================================================

        print(
            "[3] Testing active model status"
        )

        active_status = manager.status()

        assert (
            active_status["active"]
            is True
        )

        assert (
            active_status[
                "active_model"
            ]["version"]
            == MODEL_VERSION
        )

        assert (
            active_status[
                "active_model"
            ]["feature_names"]
            == list(FEATURE_NAMES)
        )

        print(
            json.dumps(
                active_status,
                indent=2,
            )
        )

        print(
            "PASS - active model state verified."
        )
        print()

        # ==============================================================
        # Prediction
        # ==============================================================

        print(
            "[4] Testing prediction API"
        )

        prediction = manager.predict(
            {
                "request_frequency": 10.0,
                "failure_ratio": 0.05,
                "unique_source_count": 2,
                "unique_user_count": 1,
                "failed_attempts": 1,
                "anomaly_score": 0.05,
                "outbound_data_volume": 100.0,
            }
        )

        assert (
            prediction[
                "predicted_class"
            ]
            == 0
        )

        assert (
            prediction[
                "model_version"
            ]
            == MODEL_VERSION
        )

        assert (
            prediction["error"]
            is None
        )

        print(
            json.dumps(
                prediction,
                indent=2,
            )
        )

        print(
            "PASS - prediction succeeded."
        )
        print()

        # ==============================================================
        # Feature rejection
        # ==============================================================

        print(
            "[5] Testing feature contract rejection"
        )

        bad_prediction = manager.predict(
            {
                "request_frequency": 10.0,
            }
        )

        assert (
            bad_prediction["error"]
            is not None
        )

        print(
            json.dumps(
                bad_prediction,
                indent=2,
            )
        )

        print(
            "PASS - incompatible features rejected."
        )
        print()

        # ==============================================================
        # Baseline rejection
        # ==============================================================

        print(
            "[6] Testing baseline rejection"
        )

        baseline_result = manager.activate(
            "2.0.0"
        )

        assert (
            baseline_result["success"]
            is False
        )

        assert (
            manager.active_version()
            == MODEL_VERSION
        )

        assert (
            loader.loaded
            is True
        )

        print(
            json.dumps(
                baseline_result,
                indent=2,
            )
        )

        print(
            "PASS - baseline activation rejected without "
            "destroying active state."
        )
        print()

        # ==============================================================
        # Schema rejection
        # ==============================================================

        print(
            "[7] Testing schema rejection"
        )

        schema_result = manager.activate(
            "2.1.0"
        )

        assert (
            schema_result["success"]
            is False
        )

        assert (
            manager.active_version()
            == MODEL_VERSION
        )

        assert loader.loaded is True

        print(
            json.dumps(
                schema_result,
                indent=2,
            )
        )

        print(
            "PASS - incompatible schema rejected."
        )
        print()

        # ==============================================================
        # Feature rejection
        # ==============================================================

        print(
            "[8] Testing feature contract rejection"
        )

        feature_result = manager.activate(
            "2.2.0"
        )

        assert (
            feature_result["success"]
            is False
        )

        assert (
            manager.active_version()
            == MODEL_VERSION
        )

        assert loader.loaded is True

        print(
            json.dumps(
                feature_result,
                indent=2,
            )
        )

        print(
            "PASS - incompatible feature contract rejected."
        )
        print()

        # ==============================================================
        # Reload
        # ==============================================================

        print(
            "[9] Testing safe reload"
        )

        reload_result = manager.reload()

        assert (
            reload_result["success"]
            is True
        )

        assert (
            manager.active_version()
            == MODEL_VERSION
        )

        assert loader.loaded is True

        print(
            json.dumps(
                reload_result,
                indent=2,
            )
        )

        print(
            "PASS - active model reloaded."
        )
        print()

        # ==============================================================
        # Deactivation
        # ==============================================================

        print(
            "[10] Testing deactivation"
        )

        deactivate_result = manager.deactivate()

        assert (
            deactivate_result["success"]
            is True
        )

        assert (
            manager.is_active()
            is False
        )

        assert (
            loader.loaded
            is False
        )

        print(
            json.dumps(
                deactivate_result,
                indent=2,
            )
        )

        print(
            "PASS - model deactivated."
        )
        print()

        # ==============================================================
        # Prediction without active model
        # ==============================================================

        print(
            "[11] Testing prediction without active model"
        )

        inactive_prediction = manager.predict(
            {
                "request_frequency": 10.0,
                "failure_ratio": 0.05,
                "unique_source_count": 2,
                "unique_user_count": 1,
                "failed_attempts": 1,
                "anomaly_score": 0.05,
                "outbound_data_volume": 100.0,
            }
        )

        assert (
            inactive_prediction["error"]
            is not None
        )

        assert (
            inactive_prediction[
                "model_available"
            ]
            is False
        )

        print(
            json.dumps(
                inactive_prediction,
                indent=2,
            )
        )

        print(
            "PASS - inactive prediction rejected."
        )
        print()

        # ==============================================================
        # Statistics
        # ==============================================================

        print(
            "[12] Testing operational statistics"
        )

        final_statistics = manager.status()[
            "statistics"
        ]

        assert (
            final_statistics[
                "prediction_count"
            ]
            == 3
        )

        assert (
            final_statistics[
                "successful_predictions"
            ]
            == 1
        )

        assert (
            final_statistics[
                "failed_predictions"
            ]
            == 2
        )

        assert (
            final_statistics[
                "average_prediction_ms"
            ]
            >= 0.0
        )

        assert (
            final_statistics[
                "average_successful_prediction_ms"
            ]
            >= 0.0
        )

        print(
            json.dumps(
                final_statistics,
                indent=2,
            )
        )

        print(
            "PASS - prediction statistics verified."
        )
        print()

        # ==============================================================
        # Final safety state
        # ==============================================================

        print(
            "[13] Final manager status"
        )

        final_status = manager.status()

        assert (
            final_status["active"]
            is False
        )

        assert (
            final_status[
                "safety"
            ][
                "baseline_activation_allowed"
            ]
            is False
        )

        assert (
            final_status[
                "safety"
            ][
                "shell_execution"
            ]
            is False
        )

        assert (
            final_status[
                "safety"
            ][
                "network_operations"
            ]
            is False
        )

        assert (
            final_status[
                "safety"
            ][
                "direct_pickle_loading"
            ]
            is False
        )

        assert (
            final_status[
                "safety"
            ][
                "activation_state_preservation"
            ]
            is True
        )

        print(
            json.dumps(
                final_status,
                indent=2,
            )
        )

        print(
            "PASS - final safety and state checks passed."
        )
        print()

        print("=" * 78)
        print(
            "Model Manager self-test completed successfully."
        )
        print("=" * 78)


# ============================================================================
# Module entry point
# ============================================================================

if __name__ == "__main__":
    ModelManager._self_test()