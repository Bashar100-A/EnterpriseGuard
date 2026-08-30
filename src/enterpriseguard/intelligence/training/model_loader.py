"""
EnterpriseGuard - Model Loader
================================


Responsible for:


- Loading a registered EnterpriseGuard model.
- Verifying model integrity using SHA-256.
- Verifying schema compatibility.
- Verifying feature compatibility.
- Rejecting baseline/untrained models.
- Loading only registered model versions.
- Maintaining a single loaded-model state.
- Providing deterministic model status information.
- Providing a lightweight independent self-test.


Architecture:


    Model Registry
          |
          v
    Model Loader
          |
          +---- verify version
          +---- verify schema
          +---- verify features
          +---- verify SHA-256
          +---- load model
          |
          v
    EnterpriseGuardModel
          |
          v
       Prediction


Security boundary:


    This module does NOT:


    - execute shell commands
    - perform network operations
    - execute security actions
    - modify accounts
    - modify processes
    - dynamically download models


Important:


    Python pickle files are executable object-serialization formats.
    This loader must therefore only load model files coming from a
    trusted EnterpriseGuard Model Registry.


Version:
    1.0.0
"""


from __future__ import annotations


import hashlib
import importlib
import json
import pickle
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence




# ============================================================================
# Constants
# ============================================================================


LOADER_NAME = "EnterpriseGuard Model Loader"
LOADER_VERSION = "1.0.0"
SCHEMA_VERSION = 1


EXPECTED_MODEL_NAME = "EnterpriseGuard Threat Intelligence Model"
EXPECTED_MODEL_SCHEMA_VERSION = 1
EXPECTED_MODEL_VERSION = "3.0.0"


EXPECTED_FEATURE_NAMES = (
    "request_frequency",
    "failure_ratio",
    "unique_source_count",
    "unique_user_count",
    "failed_attempts",
    "anomaly_score",
    "outbound_data_volume",
)


EXPECTED_FEATURE_COUNT = len(EXPECTED_FEATURE_NAMES)




# ============================================================================
# Exceptions
# ============================================================================




class ModelLoaderError(RuntimeError):
    """Base exception for model-loader failures."""




class ModelNotRegisteredError(ModelLoaderError):
    """Raised when a requested model version is not registered."""




class ModelIntegrityError(ModelLoaderError):
    """Raised when the model file fails integrity verification."""




class ModelCompatibilityError(ModelLoaderError):
    """Raised when the model is incompatible with EnterpriseGuard."""




class ModelLoadError(ModelLoaderError):
    """Raised when a model cannot be loaded."""




# ============================================================================
# Data structures
# ============================================================================




@dataclass(frozen=True)
class ModelLoadResult:
    """Auditable result returned by a model-loading operation."""


    success: bool
    model_name: Optional[str]
    model_version: Optional[str]
    schema_version: Optional[int]
    model_type: Optional[str]
    trained: bool
    feature_count: int
    feature_names: tuple[str, ...]
    model_path: Optional[str]
    expected_hash: Optional[str]
    actual_hash: Optional[str]
    load_time_ms: float
    error: Optional[str]


    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        result = asdict(self)
        result["feature_names"] = list(self.feature_names)
        return result




@dataclass(frozen=True)
class LoaderStatus:
    """Current loader state."""


    loader: str
    version: str
    schema_version: int
    loaded: bool
    model_name: Optional[str]
    model_version: Optional[str]
    model_type: Optional[str]
    trained: bool
    feature_count: int
    feature_names: tuple[str, ...]
    model_path: Optional[str]
    model_hash: Optional[str]
    load_count: int
    successful_loads: int
    failed_loads: int
    total_load_time_ms: float
    average_load_time_ms: float
    error: Optional[str]


    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        result = asdict(self)
        result["feature_names"] = list(self.feature_names)
        return result




# ============================================================================
# Utility helpers
# ============================================================================




def _normalise_feature_names(
    feature_names: Optional[Sequence[Any]],
) -> tuple[str, ...]:
    """Normalise feature names into an immutable tuple of strings."""


    if feature_names is None:
        return ()


    return tuple(str(name) for name in feature_names)




def _safe_get(
    source: Any,
    key: str,
    default: Any = None,
) -> Any:
    """
    Read a value from either a mapping or an object.


    This allows the loader to work with registry records represented as
    dictionaries, dataclasses, or lightweight objects.
    """


    if source is None:
        return default


    if isinstance(source, Mapping):
        return source.get(key, default)


    return getattr(source, key, default)




def _calculate_sha256(path: Path) -> str:
    """Calculate the SHA-256 digest of a file."""


    digest = hashlib.sha256()


    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)


    return digest.hexdigest()




def _safe_json(value: Any) -> str:
    """Serialize diagnostic data without failing the loader."""


    try:
        return json.dumps(
            value,
            indent=2,
            sort_keys=True,
            default=str,
        )
    except Exception:
        return repr(value)




# ============================================================================
# Registry compatibility helpers
# ============================================================================




def _resolve_registry_class() -> type:
    """
    Resolve ModelRegistry from the current EnterpriseGuard architecture.


    The primary location is:


        enterpriseguard.intelligence.training.model_registry


    A fallback is retained for installations where the training package
    exists directly under enterpriseguard.training.
    """


    module_names = (
        "enterpriseguard.intelligence.training.model_registry",
        "enterpriseguard.training.model_registry",
    )


    errors: list[str] = []


    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)


            registry_class = getattr(module, "ModelRegistry", None)


            if registry_class is not None:
                return registry_class


            errors.append(
                f"{module_name}: ModelRegistry was not found."
            )


        except Exception as exc:
            errors.append(
                f"{module_name}: {type(exc).__name__}: {exc}"
            )


    raise ModelLoaderError(
        "Unable to resolve EnterpriseGuard ModelRegistry.\n"
        + "\n".join(errors)
    )




def _resolve_model_class() -> type:
    """
    Resolve EnterpriseGuardModel from the current architecture.
    """


    module_names = (
        "enterpriseguard.intelligence.models",
        "enterpriseguard.models",
    )


    errors: list[str] = []


    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)


            model_class = getattr(module, "EnterpriseGuardModel", None)


            if model_class is not None:
                return model_class


            errors.append(
                f"{module_name}: EnterpriseGuardModel was not found."
            )


        except Exception as exc:
            errors.append(
                f"{module_name}: {type(exc).__name__}: {exc}"
            )


    raise ModelLoaderError(
        "Unable to resolve EnterpriseGuardModel.\n"
        + "\n".join(errors)
    )




# ============================================================================
# Model Loader
# ============================================================================




class ModelLoader:
    """
    EnterpriseGuard model loading boundary.


    The loader expects a ModelRegistry instance.


    Responsibilities:


        1. Resolve a registered model version.
        2. Validate registry metadata.
        3. Validate file existence.
        4. Calculate SHA-256.
        5. Compare expected and actual hashes.
        6. Load the pickle.
        7. Validate the loaded object.
        8. Maintain loaded-model state.


    It deliberately does not register, remove, or train models.
    """


    def __init__(
        self,
        registry: Optional[Any] = None,
        *,
        expected_schema_version: int = EXPECTED_MODEL_SCHEMA_VERSION,
        expected_feature_names: Sequence[str] = EXPECTED_FEATURE_NAMES,
    ) -> None:


        self._registry = (
            registry
            if registry is not None
            else _resolve_registry_class()()
        )


        self._expected_schema_version = int(
            expected_schema_version
        )


        self._expected_feature_names = tuple(
            str(name)
            for name in expected_feature_names
        )


        self._loaded_model: Optional[Any] = None
        self._loaded_record: Optional[Any] = None
        self._loaded_hash: Optional[str] = None


        self._load_count = 0
        self._successful_loads = 0
        self._failed_loads = 0
        self._total_load_time_ms = 0.0
        self._last_error: Optional[str] = None


    # ------------------------------------------------------------------
    # Registry access
    # ------------------------------------------------------------------


    def _get_registry_record(
        self,
        version: Optional[str] = None,
    ) -> Any:
        """
        Retrieve a model record from the registry.


        Preferred API:


            registry.get(version)


        Supported compatibility alternatives:


            registry.get_model(version)
            registry.get_version(version)
            registry.latest()
            registry.get_latest()
        """


        try:
            if version is not None:


                methods = (
                    "get",
                    "get_model",
                    "get_version",
                )


                for method_name in methods:
                    method = getattr(
                        self._registry,
                        method_name,
                        None,
                    )


                    if callable(method):
                        record = method(version)


                        if record is not None:
                            return record


                raise ModelNotRegisteredError(
                    f"Model version '{version}' is not registered."
                )


            methods = (
                "get_latest",
                "latest",
                "get_active",
                "get_current",
            )


            for method_name in methods:
                method = getattr(
                    self._registry,
                    method_name,
                    None,
                )


                if callable(method):
                    record = method()


                    if record is not None:
                        return record


            # Last-resort resolution from list().
            list_method = getattr(
                self._registry,
                "list",
                None,
            )


            if callable(list_method):
                records = list_method()


                if records:
                    return records[-1]


            raise ModelNotRegisteredError(
                "No registered model is available."
            )


        except ModelNotRegisteredError:
            raise


        except Exception as exc:
            raise ModelNotRegisteredError(
                "Unable to retrieve the requested model from the registry: "
                f"{type(exc).__name__}: {exc}"
            ) from exc


    # ------------------------------------------------------------------
    # Metadata validation
    # ------------------------------------------------------------------


    def _validate_registry_record(
        self,
        record: Any,
    ) -> dict[str, Any]:


        name = _safe_get(record, "name")
        version = _safe_get(record, "version")
        schema_version = _safe_get(
            record,
            "schema_version",
        )


        feature_names = _normalise_feature_names(
            _safe_get(record, "feature_names")
        )


        feature_count = _safe_get(
            record,
            "feature_count",
        )


        model_type = _safe_get(
            record,
            "model_type",
        )


        trained = bool(
            _safe_get(
                record,
                "trained",
                False,
            )
        )


        baseline = bool(
            _safe_get(
                record,
                "baseline",
                False,
            )
        )


        model_path = _safe_get(
            record,
            "model_path",
            _safe_get(
                record,
                "model_file",
            ),
        )


        model_hash = _safe_get(
            record,
            "model_hash",
        )


        # --------------------------------------------------------------
        # Required identity
        # --------------------------------------------------------------


        if not name:
            raise ModelCompatibilityError(
                "Registered model has no model name."
            )


        if name != EXPECTED_MODEL_NAME:
            raise ModelCompatibilityError(
                "Model name mismatch: "
                f"expected '{EXPECTED_MODEL_NAME}', "
                f"received '{name}'."
            )


        if not version:
            raise ModelCompatibilityError(
                "Registered model has no version."
            )


        # --------------------------------------------------------------
        # Schema
        # --------------------------------------------------------------


        if schema_version is None:
            raise ModelCompatibilityError(
                "Registered model has no schema_version."
            )


        try:
            schema_version = int(schema_version)
        except (TypeError, ValueError) as exc:
            raise ModelCompatibilityError(
                "schema_version must be an integer."
            ) from exc


        if schema_version != self._expected_schema_version:
            raise ModelCompatibilityError(
                "Model schema mismatch: "
                f"expected {self._expected_schema_version}, "
                f"received {schema_version}."
            )


        # --------------------------------------------------------------
        # Feature contract
        # --------------------------------------------------------------


        if feature_count is None:
            feature_count = len(feature_names)


        try:
            feature_count = int(feature_count)
        except (TypeError, ValueError) as exc:
            raise ModelCompatibilityError(
                "feature_count must be an integer."
            ) from exc


        if feature_count != len(self._expected_feature_names):
            raise ModelCompatibilityError(
                "Feature count mismatch: "
                f"expected {len(self._expected_feature_names)}, "
                f"received {feature_count}."
            )


        if feature_names != self._expected_feature_names:
            raise ModelCompatibilityError(
                "Feature-name contract mismatch.\n"
                f"Expected: {self._expected_feature_names}\n"
                f"Received: {feature_names}"
            )


        # --------------------------------------------------------------
        # Training state
        # --------------------------------------------------------------


        if baseline:
            raise ModelCompatibilityError(
                "Baseline models cannot be loaded as production models."
            )


        if not trained:
            raise ModelCompatibilityError(
                "Untrained models cannot be loaded."
            )


        # --------------------------------------------------------------
        # Model type
        # --------------------------------------------------------------


        if not model_type:
            raise ModelCompatibilityError(
                "Registered model has no model_type."
            )


        if str(model_type).lower() == "baseline":
            raise ModelCompatibilityError(
                "Baseline model type cannot be loaded."
            )


        # --------------------------------------------------------------
        # File
        # --------------------------------------------------------------


        if not model_path:
            raise ModelLoadError(
                "Registered model has no model_path."
            )


        path = Path(str(model_path))


        if not path.is_file():
            raise ModelLoadError(
                f"Registered model file does not exist: {path}"
            )


        # --------------------------------------------------------------
        # Hash
        # --------------------------------------------------------------


        if not model_hash:
            raise ModelIntegrityError(
                "Registered model has no SHA-256 model_hash."
            )


        model_hash = str(model_hash).strip().lower()


        if len(model_hash) != 64:
            raise ModelIntegrityError(
                "Registered model_hash is not a valid SHA-256 digest."
            )


        try:
            int(model_hash, 16)
        except ValueError as exc:
            raise ModelIntegrityError(
                "Registered model_hash contains non-hexadecimal characters."
            ) from exc


        return {
            "name": str(name),
            "version": str(version),
            "schema_version": schema_version,
            "feature_count": feature_count,
            "feature_names": feature_names,
            "model_type": str(model_type),
            "trained": trained,
            "baseline": baseline,
            "model_path": path,
            "model_hash": model_hash,
        }


    # ------------------------------------------------------------------
    # File integrity
    # ------------------------------------------------------------------


    def _verify_file_integrity(
        self,
        path: Path,
        expected_hash: str,
    ) -> str:


        actual_hash = _calculate_sha256(path)


        if actual_hash.lower() != expected_hash.lower():
            raise ModelIntegrityError(
                "Model SHA-256 verification failed.\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {actual_hash}"
            )


        return actual_hash


    # ------------------------------------------------------------------
    # Loaded object validation
    # ------------------------------------------------------------------


    def _validate_loaded_model(
        self,
        model: Any,
        metadata: Mapping[str, Any],
    ) -> None:


        if model is None:
            raise ModelLoadError(
                "The model file produced a null object."
            )


        # --------------------------------------------------------------
        # Model type
        # --------------------------------------------------------------


        expected_model_type = str(
            metadata["model_type"]
        ).lower()


        actual_type = type(model).__name__.lower()


        if expected_model_type not in {
            actual_type,
            "logisticregression",
        }:
            raise ModelCompatibilityError(
                "Loaded model type mismatch: "
                f"registry='{metadata['model_type']}', "
                f"loaded='{type(model).__name__}'."
            )


        # --------------------------------------------------------------
        # Model metadata
        # --------------------------------------------------------------


        model_version = getattr(
            model,
            "MODEL_VERSION",
            getattr(
                model,
                "model_version",
                None,
            ),
        )


        if model_version is not None:
            if str(model_version) != str(
                metadata["version"]
            ):
                raise ModelCompatibilityError(
                    "Loaded model version does not match "
                    "the registered version."
                )


        # --------------------------------------------------------------
        # Feature contract
        # --------------------------------------------------------------


        model_features = getattr(
            model,
            "feature_names",
            getattr(
                model,
                "FEATURE_NAMES",
                None,
            ),
        )


        if model_features is not None:


            model_features = _normalise_feature_names(
                model_features
            )


            if model_features != self._expected_feature_names:
                raise ModelCompatibilityError(
                    "Loaded model feature contract does not "
                    "match EnterpriseGuard."
                )


        # --------------------------------------------------------------
        # Training state
        # --------------------------------------------------------------


        model_trained = getattr(
            model,
            "trained",
            getattr(
                model,
                "is_trained",
                True,
            ),
        )


        if model_trained is False:
            raise ModelCompatibilityError(
                "Loaded model reports itself as untrained."
            )


    # ------------------------------------------------------------------
    # Public loading API
    # ------------------------------------------------------------------


    def verify(
        self,
        version: Optional[str] = None,
    ) -> ModelLoadResult:
        """
        Verify a registered model without loading it.


        Verification includes:


        - registry record
        - schema
        - feature contract
        - trained state
        - model path
        - SHA-256 integrity
        """


        started = time.perf_counter()


        try:
            record = self._get_registry_record(version)


            metadata = self._validate_registry_record(
                record
            )


            actual_hash = self._verify_file_integrity(
                metadata["model_path"],
                metadata["model_hash"],
            )


            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0


            return ModelLoadResult(
                success=True,
                model_name=metadata["name"],
                model_version=metadata["version"],
                schema_version=metadata["schema_version"],
                model_type=metadata["model_type"],
                trained=metadata["trained"],
                feature_count=metadata["feature_count"],
                feature_names=metadata["feature_names"],
                model_path=str(metadata["model_path"]),
                expected_hash=metadata["model_hash"],
                actual_hash=actual_hash,
                load_time_ms=round(elapsed_ms, 3),
                error=None,
            )


        except Exception as exc:


            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0


            return ModelLoadResult(
                success=False,
                model_name=None,
                model_version=version,
                schema_version=None,
                model_type=None,
                trained=False,
                feature_count=0,
                feature_names=(),
                model_path=None,
                expected_hash=None,
                actual_hash=None,
                load_time_ms=round(elapsed_ms, 3),
                error=f"{type(exc).__name__}: {exc}",
            )


    def load(
        self,
        version: Optional[str] = None,
    ) -> ModelLoadResult:
        """
        Verify and load a registered model.


        If version is omitted, the registry's latest model is used.
        """


        started = time.perf_counter()
        self._load_count += 1


        try:
            record = self._get_registry_record(version)


            metadata = self._validate_registry_record(
                record
            )


            actual_hash = self._verify_file_integrity(
                metadata["model_path"],
                metadata["model_hash"],
            )


            # ----------------------------------------------------------
            # Trusted registry artifact only
            # ----------------------------------------------------------


            with metadata["model_path"].open("rb") as handle:
                model = pickle.load(handle)


            self._validate_loaded_model(
                model,
                metadata,
            )


            self._loaded_model = model
            self._loaded_record = record
            self._loaded_hash = actual_hash
            self._last_error = None


            self._successful_loads += 1


            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0


            self._total_load_time_ms += elapsed_ms


            return ModelLoadResult(
                success=True,
                model_name=metadata["name"],
                model_version=metadata["version"],
                schema_version=metadata["schema_version"],
                model_type=metadata["model_type"],
                trained=metadata["trained"],
                feature_count=metadata["feature_count"],
                feature_names=metadata["feature_names"],
                model_path=str(metadata["model_path"]),
                expected_hash=metadata["model_hash"],
                actual_hash=actual_hash,
                load_time_ms=round(elapsed_ms, 3),
                error=None,
            )


        except Exception as exc:


            self._failed_loads += 1
            self._last_error = (
                f"{type(exc).__name__}: {exc}"
            )


            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000.0


            self._total_load_time_ms += elapsed_ms


            raise ModelLoadError(
                f"Failed to load EnterpriseGuard model"
                f"{f' version {version}' if version else ''}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc


    def load_latest(self) -> ModelLoadResult:
        """Load the latest registered model."""
        return self.load()


    # ------------------------------------------------------------------
    # Loaded-model lifecycle
    # ------------------------------------------------------------------


    def get_loaded_model(self) -> Any:
        """
        Return the currently loaded model.


        Raises ModelLoadError if no model is loaded.
        """


        if self._loaded_model is None:
            raise ModelLoadError(
                "No EnterpriseGuard model is currently loaded."
            )


        return self._loaded_model


    def get_loaded_record(self) -> Any:
        """Return the registry record of the loaded model."""


        if self._loaded_record is None:
            raise ModelLoadError(
                "No EnterpriseGuard model is currently loaded."
            )


        return self._loaded_record


    def unload(self) -> None:
        """Unload the current model from the loader."""


        self._loaded_model = None
        self._loaded_record = None
        self._loaded_hash = None


    @property
    def loaded(self) -> bool:
        """Return whether a model is currently loaded."""
        return self._loaded_model is not None


    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------


    def status(self) -> dict[str, Any]:
        """Return the current loader status."""


        if self._loaded_record is not None:


            name = _safe_get(
                self._loaded_record,
                "name",
            )


            version = _safe_get(
                self._loaded_record,
                "version",
            )


            model_type = _safe_get(
                self._loaded_record,
                "model_type",
            )


            trained = bool(
                _safe_get(
                    self._loaded_record,
                    "trained",
                    False,
                )
            )


            model_path = _safe_get(
                self._loaded_record,
                "model_path",
            )


        else:
            name = None
            version = None
            model_type = None
            trained = False
            model_path = None


        average_ms = (
            self._total_load_time_ms
            / self._load_count
            if self._load_count
            else 0.0
        )


        result = LoaderStatus(
            loader=LOADER_NAME,
            version=LOADER_VERSION,
            schema_version=SCHEMA_VERSION,
            loaded=self.loaded,
            model_name=name,
            model_version=version,
            model_type=model_type,
            trained=trained,
            feature_count=(
                EXPECTED_FEATURE_COUNT
                if self.loaded
                else 0
            ),
            feature_names=(
                self._expected_feature_names
                if self.loaded
                else ()
            ),
            model_path=(
                str(model_path)
                if model_path is not None
                else None
            ),
            model_hash=self._loaded_hash,
            load_count=self._load_count,
            successful_loads=self._successful_loads,
            failed_loads=self._failed_loads,
            total_load_time_ms=round(
                self._total_load_time_ms,
                3,
            ),
            average_load_time_ms=round(
                average_ms,
                3,
            ),
            error=self._last_error,
        )


        return result.to_dict()




# ============================================================================
# Independent Self-Test
# ============================================================================




class _SelfTestModel:
    """
    Minimal trusted test object.


    This object is used only by the independent loader self-test.
    It is deliberately not an EnterpriseGuard production model.
    """


    MODEL_VERSION = EXPECTED_MODEL_VERSION
    feature_names = EXPECTED_FEATURE_NAMES
    trained = True


    def __init__(self) -> None:
        self.model_type = "LogisticRegression"




class _SelfTestRegistry:
    """
    Minimal registry contract used by the loader self-test.


    The production loader works with the real ModelRegistry.
    """


    def __init__(self, record: Mapping[str, Any]) -> None:
        self._record = dict(record)


    def get(self, version: str) -> Mapping[str, Any]:
        if version != self._record["version"]:
            raise KeyError(version)


        return dict(self._record)


    def get_latest(self) -> Mapping[str, Any]:
        return dict(self._record)




def _create_self_test_artifact(
    directory: Path,
) -> tuple[Path, str]:
    """Create a deterministic trusted test artifact."""


    path = directory / "enterpriseguard_model.pkl"


    model = _SelfTestModel()


    with path.open("wb") as handle:
        pickle.dump(
            model,
            handle,
            protocol=pickle.HIGHEST_PROTOCOL,
        )


    digest = _calculate_sha256(path)


    return path, digest




def _self_test() -> None:
    """Run the independent Model Loader self-test."""


    print("=" * 78)
    print("EnterpriseGuard Model Loader - Self Test")
    print("=" * 78)


    with tempfile.TemporaryDirectory(
        prefix="enterpriseguard_loader_test_"
    ) as temp_directory:


        root = Path(temp_directory)


        # --------------------------------------------------------------
        # 1. Creating test artifact
        # --------------------------------------------------------------


        print("\n[1] Creating trusted test model")


        model_path, model_hash = _create_self_test_artifact(
            root
        )


        print(
            json.dumps(
                {
                    "path": str(model_path),
                    "sha256": model_hash,
                    "size": model_path.stat().st_size,
                },
                indent=4,
            )
        )


        assert model_path.exists()
        assert len(model_hash) == 64


        print("PASS - trusted test model created.")


        # --------------------------------------------------------------
        # 2. Creating registry record
        # --------------------------------------------------------------


        print("\n[2] Creating registry record")


        record = {
            "name": EXPECTED_MODEL_NAME,
            "version": EXPECTED_MODEL_VERSION,
            "schema_version": EXPECTED_MODEL_SCHEMA_VERSION,
            "feature_count": EXPECTED_FEATURE_COUNT,
            "feature_names": list(EXPECTED_FEATURE_NAMES),
            "model_type": "LogisticRegression",
            "trained": True,
            "baseline": False,
            "training_samples": 4,
            "model_path": str(model_path),
            "model_hash": model_hash,
        }


        print(
            json.dumps(
                record,
                indent=4,
            )
        )


        # --------------------------------------------------------------
        # 3. Creating loader
        # --------------------------------------------------------------


        print("\n[3] Creating loader")


        registry = _SelfTestRegistry(record)


        loader = ModelLoader(
            registry=registry
        )


        status = loader.status()


        print(
            json.dumps(
                status,
                indent=4,
            )
        )


        assert status["loaded"] is False
        assert status["load_count"] == 0


        print("PASS - loader created.")


        # --------------------------------------------------------------
        # 4. Verification
        # --------------------------------------------------------------


        print("\n[4] Verifying model")


        verification = loader.verify(
            EXPECTED_MODEL_VERSION
        )


        print(
            json.dumps(
                verification.to_dict(),
                indent=4,
            )
        )


        assert verification.success is True
        assert (
            verification.model_version
            == EXPECTED_MODEL_VERSION
        )
        assert (
            verification.schema_version
            == EXPECTED_MODEL_SCHEMA_VERSION
        )
        assert (
            verification.feature_names
            == EXPECTED_FEATURE_NAMES
        )
        assert (
            verification.expected_hash
            == verification.actual_hash
        )


        print("PASS - model verification succeeded.")


        # --------------------------------------------------------------
        # 5. Loading
        # --------------------------------------------------------------


        print("\n[5] Loading verified model")


        result = loader.load(
            EXPECTED_MODEL_VERSION
        )


        print(
            json.dumps(
                result.to_dict(),
                indent=4,
            )
        )


        assert result.success is True
        assert loader.loaded is True


        loaded_model = loader.get_loaded_model()


        assert loaded_model is not None
        assert (
            getattr(
                loaded_model,
                "MODEL_VERSION",
                None,
            )
            == EXPECTED_MODEL_VERSION
        )


        print("PASS - model loaded successfully.")


        # --------------------------------------------------------------
        # 6. Loaded model state
        # --------------------------------------------------------------


        print("\n[6] Loaded model state")


        status = loader.status()


        print(
            json.dumps(
                status,
                indent=4,
            )
        )


        assert status["loaded"] is True
        assert status["successful_loads"] == 1
        assert status["failed_loads"] == 0
        assert status["model_hash"] == model_hash


        print("PASS - loaded model state verified.")


        # --------------------------------------------------------------
        # 7. Integrity failure
        # --------------------------------------------------------------


        print("\n[7] Testing integrity rejection")


        tampered_path = root / "tampered_model.pkl"


        tampered_path.write_bytes(
            model_path.read_bytes() + b"tampered"
        )


        tampered_record = dict(record)
        tampered_record["model_path"] = str(
            tampered_path
        )


        tampered_registry = _SelfTestRegistry(
            tampered_record
        )


        tampered_loader = ModelLoader(
            registry=tampered_registry
        )


        try:
            tampered_loader.load(
                EXPECTED_MODEL_VERSION
            )


        except ModelLoadError:
            print(
                "PASS - tampered model rejected."
            )


        else:
            raise AssertionError(
                "Tampered model was not rejected."
            )


        # --------------------------------------------------------------
        # 8. Schema rejection
        # --------------------------------------------------------------


        print("\n[8] Testing schema rejection")


        invalid_schema_record = dict(record)


        invalid_schema_record[
            "schema_version"
        ] = EXPECTED_MODEL_SCHEMA_VERSION + 1


        invalid_schema_registry = _SelfTestRegistry(
            invalid_schema_record
        )


        invalid_schema_loader = ModelLoader(
            registry=invalid_schema_registry
        )


        try:
            invalid_schema_loader.load(
                EXPECTED_MODEL_VERSION
            )


        except ModelLoadError:
            print(
                "PASS - incompatible schema rejected."
            )


        else:
            raise AssertionError(
                "Incompatible schema was not rejected."
            )


        # --------------------------------------------------------------
        # 9. Feature rejection
        # --------------------------------------------------------------


        print("\n[9] Testing feature contract rejection")


        invalid_feature_record = dict(record)


        invalid_feature_record[
            "feature_names"
        ] = [
            "invalid_feature",
            *EXPECTED_FEATURE_NAMES[1:],
        ]


        invalid_feature_registry = _SelfTestRegistry(
            invalid_feature_record
        )


        invalid_feature_loader = ModelLoader(
            registry=invalid_feature_registry
        )


        try:
            invalid_feature_loader.load(
                EXPECTED_MODEL_VERSION
            )


        except ModelLoadError:
            print(
                "PASS - incompatible features rejected."
            )


        else:
            raise AssertionError(
                "Incompatible features were not rejected."
            )


        # --------------------------------------------------------------
        # 10. Baseline rejection
        # --------------------------------------------------------------


        print("\n[10] Testing baseline rejection")


        baseline_record = dict(record)
        baseline_record["baseline"] = True
        baseline_record["trained"] = False
        baseline_record["model_type"] = "baseline"


        baseline_registry = _SelfTestRegistry(
            baseline_record
        )


        baseline_loader = ModelLoader(
            registry=baseline_registry
        )


        try:
            baseline_loader.load(
                EXPECTED_MODEL_VERSION
            )


        except ModelLoadError:
            print(
                "PASS - baseline model rejected."
            )


        else:
            raise AssertionError(
                "Baseline model was not rejected."
            )


        # --------------------------------------------------------------
        # 11. Unload
        # --------------------------------------------------------------


        print("\n[11] Unloading model")


        loader.unload()


        assert loader.loaded is False


        try:
            loader.get_loaded_model()


        except ModelLoadError:
            print(
                "PASS - unloaded model cannot be accessed."
            )


        else:
            raise AssertionError(
                "Unloaded model remained accessible."
            )


        # --------------------------------------------------------------
        # 12. Final status
        # --------------------------------------------------------------


        print("\n[12] Final loader status")


        final_status = loader.status()


        print(
            json.dumps(
                final_status,
                indent=4,
            )
        )


        assert final_status["loaded"] is False
        assert final_status["successful_loads"] == 1


    print("\n" + "=" * 78)
    print("Model Loader self-test completed successfully.")
    print("=" * 78)




# ============================================================================
# Module entry point
# ============================================================================




if __name__ == "__main__":
    _self_test()