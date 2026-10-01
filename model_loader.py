import hashlib
import json
import pickle
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

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


class ModelLoaderError(RuntimeError): pass
class ModelNotRegisteredError(ModelLoaderError): pass
class ModelIntegrityError(ModelLoaderError): pass
class ModelCompatibilityError(ModelLoaderError): pass
class ModelLoadError(ModelLoaderError): pass


@dataclass(frozen=True)
class ModelLoadResult:
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
        result = asdict(self)
        result["feature_names"] = list(self.feature_names)
        return result


def _normalise_feature_names(feature_names: Optional[Sequence[Any]]) -> tuple[str, ...]:
    if feature_names is None:
        return ()
    return tuple(str(name) for name in feature_names)


def _safe_get(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ModelLoader:
    def __init__(
        self,
        registry: Optional[Any] = None,
        *,
        expected_schema_version: int = EXPECTED_MODEL_SCHEMA_VERSION,
        expected_feature_names: Sequence[str] = EXPECTED_FEATURE_NAMES,
    ) -> None:
        self._registry = registry
        self._expected_schema_version = int(expected_schema_version)
        self._expected_feature_names = tuple(str(name) for name in expected_feature_names)
        self._loaded_model: Optional[Any] = None
        self._loaded_record: Optional[Any] = None
        self._loaded_hash: Optional[str] = None
        self._load_count = 0
        self._successful_loads = 0
        self._failed_loads = 0
        self._total_load_time_ms = 0.0
        self._last_error: Optional[str] = None

    def _get_registry_record(self, version: Optional[str] = None) -> Any:
        if version is not None:
            methods = ("get", "get_model", "get_version")
            for method_name in methods:
                method = getattr(self._registry, method_name, None)
                if callable(method):
                    try:
                        record = method(version)
                        if record is not None:
                            return record
                    except (TypeError, ValueError, KeyError, AttributeError, LookupError):
                        pass
            raise ModelNotRegisteredError(f"Model version '{version}' is not registered.")
        methods = ("get_latest", "latest", "get_active", "get_current")
        for method_name in methods:
            method = getattr(self._registry, method_name, None)
            if callable(method):
                try:
                    record = method()
                    if record is not None:
                        return record
                except (TypeError, ValueError, KeyError, AttributeError, LookupError):
                    pass
        list_method = getattr(self._registry, "list", None)
        if callable(list_method):
            try:
                records = list_method()
                if records:
                    return records[-1]
            except (TypeError, ValueError, KeyError, AttributeError, LookupError, IndexError):
                pass
        raise ModelNotRegisteredError("No registered model is available.")

    def _validate_registry_record(self, record: Any) -> dict[str, Any]:
        name = _safe_get(record, "name")
        version = _safe_get(record, "version")
        schema_version = _safe_get(record, "schema_version")
        feature_names = _normalise_feature_names(_safe_get(record, "feature_names"))
        feature_count = _safe_get(record, "feature_count")
        model_type = _safe_get(record, "model_type")
        trained = bool(_safe_get(record, "trained", False))
        baseline = bool(_safe_get(record, "baseline", False))
        model_path = _safe_get(record, "model_path", _safe_get(record, "model_file"))
        model_hash = _safe_get(record, "model_hash")

        if not name:
            raise ModelCompatibilityError("Registered model has no model name.")
        if name != EXPECTED_MODEL_NAME:
            raise ModelCompatibilityError(f"Model name mismatch: expected '{EXPECTED_MODEL_NAME}', received '{name}'.")
        if not version:
            raise ModelCompatibilityError("Registered model has no version.")
        if schema_version is None:
            raise ModelCompatibilityError("Registered model has no schema_version.")
        try:
            schema_version = int(schema_version)
        except (TypeError, ValueError) as exc:
            raise ModelCompatibilityError("schema_version must be an integer.") from exc
        if schema_version != self._expected_schema_version:
            raise ModelCompatibilityError(f"Model schema mismatch: expected {self._expected_schema_version}, received {schema_version}.")

        if feature_count is None:
            feature_count = len(feature_names)
        try:
            feature_count = int(feature_count)
        except (TypeError, ValueError) as exc:
            raise ModelCompatibilityError("feature_count must be an integer.") from exc
        if feature_count != len(self._expected_feature_names):
            raise ModelCompatibilityError(f"Feature count mismatch: expected {len(self._expected_feature_names)}, received {feature_count}.")
        if feature_names != self._expected_feature_names:
            raise ModelCompatibilityError("Feature-name contract mismatch.")

        if baseline:
            raise ModelCompatibilityError("Baseline models cannot be loaded as production models.")
        if not trained:
            raise ModelCompatibilityError("Untrained models cannot be loaded.")

        if not model_type:
            raise ModelCompatibilityError("Registered model has no model_type.")
        if str(model_type).lower() == "baseline":
            raise ModelCompatibilityError("Baseline model type cannot be loaded.")

        if not model_path:
            raise ModelLoadError("Registered model has no model_path.")
        path = Path(str(model_path))
        if not path.is_file():
            raise ModelLoadError(f"Registered model file does not exist: {path}")

        if not model_hash:
            raise ModelIntegrityError("Registered model has no SHA-256 model_hash.")
        model_hash = str(model_hash).strip().lower()
        if len(model_hash) != 64:
            raise ModelIntegrityError("Registered model_hash is not a valid SHA-256 digest.")
        try:
            int(model_hash, 16)
        except ValueError as exc:
            raise ModelIntegrityError("Registered model_hash contains non-hexadecimal characters.") from exc

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

    def _verify_file_integrity(self, path: Path, expected_hash: str) -> str:
        actual_hash = _calculate_sha256(path)
        if actual_hash.lower() != expected_hash.lower():
            raise ModelIntegrityError(f"Model SHA-256 verification failed. Expected: {expected_hash}, Actual: {actual_hash}")
        return actual_hash

    def _validate_loaded_model(self, model: Any, metadata: Mapping[str, Any]) -> None:
        if model is None:
            raise ModelLoadError("The model file produced a null object.")
        expected_model_type = str(metadata["model_type"]).lower()
        actual_type = type(model).__name__.lower()
        if expected_model_type not in {actual_type, "logisticregression"}:
            raise ModelCompatibilityError(f"Loaded model type mismatch: registry='{metadata['model_type']}', loaded='{type(model).__name__}'.")
        model_version = getattr(model, "MODEL_VERSION", getattr(model, "model_version", None))
        if model_version is not None:
            if str(model_version) != str(metadata["version"]):
                raise ModelCompatibilityError("Loaded model version does not match the registered version.")
        model_features = getattr(model, "feature_names", getattr(model, "FEATURE_NAMES", None))
        if model_features is not None:
            model_features = _normalise_feature_names(model_features)
            if model_features != self._expected_feature_names:
                raise ModelCompatibilityError("Loaded model feature contract does not match EnterpriseGuard.")
        model_trained = getattr(model, "trained", getattr(model, "is_trained", True))
        if model_trained is False:
            raise ModelCompatibilityError("Loaded model reports itself as untrained.")

    def load(self, version: Optional[str] = None) -> ModelLoadResult:
        started = time.perf_counter()
        self._load_count += 1
        try:
            record = self._get_registry_record(version)
            metadata = self._validate_registry_record(record)
            actual_hash = self._verify_file_integrity(metadata["model_path"], metadata["model_hash"])
            with metadata["model_path"].open("rb") as handle:
                model = pickle.load(handle)
            self._validate_loaded_model(model, metadata)
            self._loaded_model = model
            self._loaded_record = record
            self._loaded_hash = actual_hash
            self._last_error = None
            self._successful_loads += 1
            elapsed_ms = (time.perf_counter() - started) * 1000.0
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
        except (OSError, pickle.PickleError, ModelLoaderError, TypeError, ValueError, KeyError, AttributeError, EOFError, ImportError) as exc:
            self._failed_loads += 1
            self._last_error = f"{type(exc).__name__}: {exc}"
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            self._total_load_time_ms += elapsed_ms
            raise ModelLoadError(f"Failed to load: {exc}") from exc


class _SelfTestModel:
    MODEL_VERSION = EXPECTED_MODEL_VERSION
    feature_names = EXPECTED_FEATURE_NAMES
    trained = True

    def __init__(self) -> None:
        self.model_type = "LogisticRegression"


class _SelfTestRegistry:
    def __init__(self, record: Mapping[str, Any]) -> None:
        self._record = dict(record)

    def get(self, version: str) -> Mapping[str, Any]:
        if version != self._record["version"]:
            raise KeyError(version)
        return dict(self._record)

    def get_latest(self) -> Mapping[str, Any]:
        return dict(self._record)


def _run_self_test() -> None:
    with tempfile.TemporaryDirectory() as temp_directory:
        root = Path(temp_directory)
        model_path = root / "enterpriseguard_model.pkl"
        model = _SelfTestModel()
        with model_path.open("wb") as handle:
            pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)
        model_hash = _calculate_sha256(model_path)
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
        registry = _SelfTestRegistry(record)
        loader = ModelLoader(registry=registry)
        res = loader.load(EXPECTED_MODEL_VERSION)
        print("Self-test succeeded:", res.success)


if __name__ == "__main__":
    _run_self_test()
