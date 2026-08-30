"""
EnterpriseGuard - Model Registry
=================================


Central registry for trained EnterpriseGuard models.


Responsibilities
----------------
- Register compatible trained models
- Track model versions
- Verify model integrity using SHA-256
- Verify schema compatibility
- Verify canonical feature names
- Distinguish trained models from baseline fallback
- Retrieve registered model versions
- List registered versions
- Remove registered versions
- Maintain a persistent registry manifest
- Provide independent self-test


Architecture
------------


    EnterpriseGuardModel
            |
            v
      Model Registry
            |
      +-----+------+
      |            |
      v            v
   Manifest    Versioned Model
      |            |
      +-----+------+
            |
            v
      Integrity Check


Security Notes
--------------
- No shell execution
- No network access
- No subprocess execution
- No dynamic code execution
- Model files use pickle because EnterpriseGuardModel does.
- Never register or load untrusted model files.
- SHA-256 verifies integrity, not authenticity.


Compatibility
-------------
This module imports EnterpriseGuardModel from:


    enterpriseguard.intelligence.models


It does NOT import from:


    enterpriseguard.intelligence.training.models


The registry is intentionally independent from the training pipeline.
"""


from __future__ import annotations


import hashlib
import json
import os
import shutil
import tempfile
import threading
import time


from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any




# ============================================================================
# EnterpriseGuard model import
# ============================================================================


try:
    from ..models import (
        EnterpriseGuardModel,
        FEATURE_COUNT,
        FEATURE_NAMES,
        MODEL_NAME,
        MODEL_SCHEMA_VERSION,
        MODEL_VERSION,
        MODEL_FILE_NAME,
    )
except ImportError:  # pragma: no cover
    from enterpriseguard.intelligence.models import (
        EnterpriseGuardModel,
        FEATURE_COUNT,
        FEATURE_NAMES,
        MODEL_NAME,
        MODEL_SCHEMA_VERSION,
        MODEL_VERSION,
        MODEL_FILE_NAME,
    )




# ============================================================================
# Registry constants
# ============================================================================


REGISTRY_NAME = "EnterpriseGuard Model Registry"


REGISTRY_VERSION = "1.0.0"


REGISTRY_SCHEMA_VERSION = 1


REGISTRY_DIRECTORY_NAME = "registry"


REGISTRY_MANIFEST_NAME = "model_registry.json"


DEFAULT_REGISTRY_DIRECTORY = (
    Path(__file__).resolve().parents[4]
    / "assets"
    / "models"
    / REGISTRY_DIRECTORY_NAME
)


MAX_MODEL_FILE_SIZE = 100 * 1024 * 1024  # 100 MB




# ============================================================================
# Exceptions
# ============================================================================




class ModelRegistryError(RuntimeError):
    """Base exception for model registry failures."""




class ModelCompatibilityError(ModelRegistryError):
    """Raised when a model is incompatible with EnterpriseGuard."""




class ModelNotFoundError(ModelRegistryError):
    """Raised when a requested registered model does not exist."""




class ModelIntegrityError(ModelRegistryError):
    """Raised when a model integrity check fails."""




class ModelRegistrationError(ModelRegistryError):
    """Raised when model registration fails."""




# ============================================================================
# Data structures
# ============================================================================




@dataclass(frozen=True)
class RegisteredModel:
    """
    Immutable description of a registered model version.
    """


    name: str
    version: str
    schema_version: int


    feature_count: int
    feature_names: tuple[str, ...]


    model_type: str


    trained: bool
    baseline: bool


    training_samples: int


    model_path: str
    model_hash: str


    created_at: str
    registered_at: str


    training_accuracy: float | None = None
    validation_accuracy: float | None = None


    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["feature_names"] = list(self.feature_names)
        return data




@dataclass(frozen=True)
class RegistryStatus:
    """
    Immutable registry status.
    """


    registry: str
    version: str
    schema_version: int


    model_count: int
    versions: tuple[str, ...]


    registry_path: str


    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["versions"] = list(self.versions)
        return data




# ============================================================================
# Utility functions
# ============================================================================




def _utc_now() -> str:
    """Return the current UTC timestamp."""


    return datetime.now(timezone.utc).isoformat()




def _calculate_file_hash(path: Path) -> str:
    """
    Calculate SHA-256 for a file.
    """


    if not path.exists():
        raise ModelIntegrityError(
            f"Model file does not exist: {path}"
        )


    if not path.is_file():
        raise ModelIntegrityError(
            f"Model path is not a regular file: {path}"
        )


    file_size = path.stat().st_size


    if file_size <= 0:
        raise ModelIntegrityError(
            f"Model file is empty: {path}"
        )


    if file_size > MAX_MODEL_FILE_SIZE:
        raise ModelIntegrityError(
            f"Model file exceeds maximum allowed size: {path}"
        )


    digest = hashlib.sha256()


    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)


    return digest.hexdigest()




def _atomic_write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    """
    Atomically write a JSON document.
    """


    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    temporary_path: Path | None = None


    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".registry_",
            suffix=".tmp",
            delete=False,
        ) as temporary:


            temporary_path = Path(
                temporary.name
            )


            json.dump(
                payload,
                temporary,
                indent=4,
                ensure_ascii=False,
            )


            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())


        os.replace(
            temporary_path,
            path,
        )


        temporary_path = None


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




# ============================================================================
# Model Registry
# ============================================================================




class ModelRegistry:
    """
    Persistent registry for EnterpriseGuard model versions.


    The registry stores:


        assets/models/registry/
            model_registry.json
            versions/
                <model-version>/
                    enterpriseguard_model.pkl


    A registered model is accepted only when:


    - It is an EnterpriseGuardModel
    - It is actually trained
    - It is not baseline-only
    - The model file exists
    - The model schema matches
    - The feature contract matches
    - The model version is valid
    - The model hash can be calculated
    - The copied model hash matches the source hash
    """


    def __init__(
        self,
        registry_directory: str | os.PathLike[str] | None = None,
    ) -> None:


        self._lock = threading.RLock()


        self.registry_directory = Path(
            registry_directory
            if registry_directory is not None
            else DEFAULT_REGISTRY_DIRECTORY
        )


        self.manifest_path = (
            self.registry_directory
            / REGISTRY_MANIFEST_NAME
        )


        self.versions_directory = (
            self.registry_directory
            / "versions"
        )


        self._ensure_directories()


        self._manifest = self._load_manifest()


    # ========================================================================
    # Filesystem
    # ========================================================================


    def _ensure_directories(self) -> None:
        """Create registry directories when required."""


        self.registry_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        self.versions_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


    # ========================================================================
    # Manifest
    # ========================================================================


    def _default_manifest(self) -> dict[str, Any]:
        """Return a new empty registry manifest."""


        return {
            "registry": REGISTRY_NAME,
            "version": REGISTRY_VERSION,
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "models": {},
        }


    def _load_manifest(self) -> dict[str, Any]:
        """
        Load the registry manifest.


        Invalid manifests are rejected rather than silently repaired.
        """


        if not self.manifest_path.exists():
            manifest = self._default_manifest()
            _atomic_write_json(
                self.manifest_path,
                manifest,
            )
            return manifest


        try:
            with self.manifest_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                manifest = json.load(file)


        except Exception as exc:
            raise ModelRegistryError(
                f"Failed to read registry manifest: {exc}"
            ) from exc


        if not isinstance(
            manifest,
            dict,
        ):
            raise ModelRegistryError(
                "Registry manifest must contain a JSON object."
            )


        if manifest.get(
            "registry"
        ) != REGISTRY_NAME:
            raise ModelRegistryError(
                "Registry manifest belongs to another registry."
            )


        if manifest.get(
            "version"
        ) != REGISTRY_VERSION:
            raise ModelRegistryError(
                "Registry version is incompatible."
            )


        if manifest.get(
            "schema_version"
        ) != REGISTRY_SCHEMA_VERSION:
            raise ModelRegistryError(
                "Registry schema version is incompatible."
            )


        models = manifest.get(
            "models"
        )


        if not isinstance(
            models,
            dict,
        ):
            raise ModelRegistryError(
                "Registry manifest contains an invalid models section."
            )


        return manifest


    def _save_manifest(self) -> None:
        """Persist the current registry manifest."""


        self._manifest["updated_at"] = _utc_now()


        _atomic_write_json(
            self.manifest_path,
            self._manifest,
        )


    # ========================================================================
    # Compatibility
    # ========================================================================


    @staticmethod
    def _validate_model_instance(
        model: EnterpriseGuardModel,
    ) -> None:
        """
        Verify that the supplied object is an EnterpriseGuardModel.
        """


        if not isinstance(
            model,
            EnterpriseGuardModel,
        ):
            raise ModelCompatibilityError(
                "model must be an EnterpriseGuardModel instance."
            )


    @staticmethod
    def _validate_model_metadata(
        model: EnterpriseGuardModel,
    ) -> dict[str, Any]:
        """
        Validate model metadata against the canonical EnterpriseGuard
        contract.
        """


        metadata = model.metadata()


        if metadata.name != MODEL_NAME:
            raise ModelCompatibilityError(
                "Model name is incompatible with EnterpriseGuard."
            )


        if metadata.version != MODEL_VERSION:
            raise ModelCompatibilityError(
                "Model version is incompatible with this EnterpriseGuard release."
            )


        if metadata.schema_version != MODEL_SCHEMA_VERSION:
            raise ModelCompatibilityError(
                "Model schema_version is incompatible."
            )


        if metadata.feature_count != FEATURE_COUNT:
            raise ModelCompatibilityError(
                "Model feature_count is incompatible."
            )


        if tuple(metadata.feature_names) != tuple(
            FEATURE_NAMES
        ):
            raise ModelCompatibilityError(
                "Model feature_names do not match the canonical feature contract."
            )


        if not metadata.trained:
            raise ModelCompatibilityError(
                "Baseline models cannot be registered."
            )


        if metadata.model_type == "baseline":
            raise ModelCompatibilityError(
                "Baseline model state cannot be registered."
            )


        if metadata.training_samples <= 0:
            raise ModelCompatibilityError(
                "A registered model must contain training samples."
            )


        if not metadata.model_hash:
            raise ModelIntegrityError(
                "Trained model does not contain a persisted model hash."
            )


        return metadata.to_dict()


    # ========================================================================
    # Registration
    # ========================================================================


    def register(
        self,
        model: EnterpriseGuardModel,
        *,
        overwrite: bool = False,
    ) -> RegisteredModel:
        """
        Register a trained EnterpriseGuard model.


        Parameters
        ----------
        model:
            EnterpriseGuardModel instance.


        overwrite:
            Replace an existing registered version when True.


        Returns
        -------
        RegisteredModel
            Immutable registration record.
        """


        started = time.perf_counter()


        try:
            self._validate_model_instance(
                model
            )


            metadata = self._validate_model_metadata(
                model
            )


            source_path = Path(
                model.model_path
            )


            if not source_path.exists():
                raise ModelRegistrationError(
                    "Model file does not exist."
                )


            source_hash = _calculate_file_hash(
                source_path
            )


            metadata_hash = metadata.get(
                "model_hash"
            )


            if source_hash != metadata_hash:
                raise ModelIntegrityError(
                    "Model file hash does not match model metadata hash."
                )


            version = str(
                metadata["version"]
            )


            with self._lock:


                models = self._manifest["models"]


                if (
                    version in models
                    and not overwrite
                ):
                    raise ModelRegistrationError(
                        f"Model version '{version}' is already registered."
                    )


                version_directory = (
                    self.versions_directory
                    / version
                )


                version_directory.mkdir(
                    parents=True,
                    exist_ok=True,
                )


                destination_path = (
                    version_directory
                    / MODEL_FILE_NAME
                )


                temporary_path: Path | None = None


                try:


                    with tempfile.NamedTemporaryFile(
                        mode="wb",
                        dir=version_directory,
                        prefix=".model_",
                        suffix=".tmp",
                        delete=False,
                    ) as temporary:


                        temporary_path = Path(
                            temporary.name
                        )


                    shutil.copy2(
                        source_path,
                        temporary_path,
                    )


                    copied_hash = _calculate_file_hash(
                        temporary_path
                    )


                    if copied_hash != source_hash:
                        raise ModelIntegrityError(
                            "Copied model hash does not match source model hash."
                        )


                    os.replace(
                        temporary_path,
                        destination_path,
                    )


                    temporary_path = None


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


                registered_at = _utc_now()


                record = RegisteredModel(
                    name=metadata["name"],
                    version=version,
                    schema_version=int(
                        metadata["schema_version"]
                    ),
                    feature_count=int(
                        metadata["feature_count"]
                    ),
                    feature_names=tuple(
                        metadata["feature_names"]
                    ),
                    model_type=str(
                        metadata["model_type"]
                    ),
                    trained=bool(
                        metadata["trained"]
                    ),
                    baseline=bool(
                        not metadata["trained"]
                    ),
                    training_samples=int(
                        metadata["training_samples"]
                    ),
                    model_path=str(
                        destination_path
                    ),
                    model_hash=source_hash,
                    created_at=str(
                        metadata["created_at"]
                    ),
                    registered_at=registered_at,
                    training_accuracy=metadata.get(
                        "training_accuracy"
                    ),
                    validation_accuracy=metadata.get(
                        "validation_accuracy"
                    ),
                )


                models[version] = record.to_dict()


                self._save_manifest()


                return record


        except ModelRegistryError:
            raise


        except Exception as exc:
            raise ModelRegistrationError(
                f"Model registration failed: {exc}"
            ) from exc


        finally:
            _ = (
                time.perf_counter()
                - started
            )


    # ========================================================================
    # Get
    # ========================================================================


    def get(
        self,
        version: str | None = None,
    ) -> EnterpriseGuardModel:
        """
        Load a registered model.


        If version is None, the newest registered version is used.


        The returned model is loaded from the registry copy, not the
        original training location.
        """


        with self._lock:


            models = self._manifest["models"]


            if not models:
                raise ModelNotFoundError(
                    "No models are registered."
                )


            selected_version = (
                version
                if version is not None
                else self._latest_version()
            )


            record = models.get(
                selected_version
            )


            if record is None:
                raise ModelNotFoundError(
                    f"Model version '{selected_version}' is not registered."
                )


            model_path = Path(
                record["model_path"]
            )


            if not model_path.exists():
                raise ModelNotFoundError(
                    f"Registered model file is missing: {model_path}"
                )


            actual_hash = _calculate_file_hash(
                model_path
            )


            expected_hash = record[
                "model_hash"
            ]


            if actual_hash != expected_hash:
                raise ModelIntegrityError(
                    f"Integrity check failed for model version '{selected_version}'."
                )


            version_directory = (
                model_path.parent
            )


            model = EnterpriseGuardModel(
                model_directory=version_directory,
                auto_load=True,
            )


            metadata = model.metadata()


            if not metadata.trained:
                raise ModelCompatibilityError(
                    "Registered model loaded as baseline."
                )


            if metadata.version != record[
                "version"
            ]:
                raise ModelCompatibilityError(
                    "Loaded model version does not match registry record."
                )


            if metadata.schema_version != record[
                "schema_version"
            ]:
                raise ModelCompatibilityError(
                    "Loaded model schema_version does not match registry record."
                )


            if tuple(
                metadata.feature_names
            ) != tuple(
                record["feature_names"]
            ):
                raise ModelCompatibilityError(
                    "Loaded model feature_names do not match registry record."
                )


            return model


    # ========================================================================
    # Get record
    # ========================================================================


    def get_record(
        self,
        version: str | None = None,
    ) -> RegisteredModel:
        """
        Return registry metadata without loading the estimator.
        """


        with self._lock:


            models = self._manifest["models"]


            if not models:
                raise ModelNotFoundError(
                    "No models are registered."
                )


            selected_version = (
                version
                if version is not None
                else self._latest_version()
            )


            record = models.get(
                selected_version
            )


            if record is None:
                raise ModelNotFoundError(
                    f"Model version '{selected_version}' is not registered."
                )


            return RegisteredModel(
                name=record["name"],
                version=record["version"],
                schema_version=int(
                    record["schema_version"]
                ),
                feature_count=int(
                    record["feature_count"]
                ),
                feature_names=tuple(
                    record["feature_names"]
                ),
                model_type=record[
                    "model_type"
                ],
                trained=bool(
                    record["trained"]
                ),
                baseline=bool(
                    record["baseline"]
                ),
                training_samples=int(
                    record["training_samples"]
                ),
                model_path=record[
                    "model_path"
                ],
                model_hash=record[
                    "model_hash"
                ],
                created_at=record[
                    "created_at"
                ],
                registered_at=record[
                    "registered_at"
                ],
                training_accuracy=record.get(
                    "training_accuracy"
                ),
                validation_accuracy=record.get(
                    "validation_accuracy"
                ),
            )


    # ========================================================================
    # List
    # ========================================================================


    def list_models(
        self,
    ) -> list[RegisteredModel]:
        """
        Return all registered models ordered by version.
        """


        with self._lock:


            records: list[
                RegisteredModel
            ] = []


            for version in sorted(
                self._manifest["models"]
            ):
                records.append(
                    self.get_record(
                        version
                    )
                )


            return records


    # ========================================================================
    # Version handling
    # ========================================================================


    def _latest_version(self) -> str:
        """
        Return the latest registered version.


        EnterpriseGuard versions currently follow semantic-version style,
        but this function intentionally performs a deterministic textual
        ordering so it does not depend on external packages.
        """


        versions = list(
            self._manifest["models"].keys()
        )


        if not versions:
            raise ModelNotFoundError(
                "No registered model versions exist."
            )


        def version_key(value: str) -> tuple[Any, ...]:


            parts = value.split(".")


            converted: list[Any] = []


            for part in parts:


                numeric = ""


                for character in part:
                    if character.isdigit():
                        numeric += character
                    else:
                        break


                if numeric:
                    converted.append(
                        int(numeric)
                    )
                else:
                    converted.append(
                        part
                    )


            return tuple(converted)


        return max(
            versions,
            key=version_key,
        )


    @property
    def latest_version(self) -> str | None:
        """Return the latest registered version."""


        with self._lock:


            if not self._manifest["models"]:
                return None


            return self._latest_version()


    # ========================================================================
    # Remove
    # ========================================================================


    def remove(
        self,
        version: str,
    ) -> bool:
        """
        Remove a registered model version.


        Returns True when the version existed and was removed.
        """


        with self._lock:


            models = self._manifest["models"]


            if version not in models:
                return False


            record = models[
                version
            ]


            model_path = Path(
                record["model_path"]
            )


            version_directory = (
                model_path.parent
            )


            try:


                if model_path.exists():
                    model_path.unlink()


                if (
                    version_directory.exists()
                    and not any(
                        version_directory.iterdir()
                    )
                ):
                    version_directory.rmdir()


                del models[
                    version
                ]


                self._save_manifest()


                return True


            except Exception as exc:


                raise ModelRegistryError(
                    f"Failed to remove model version '{version}': {exc}"
                ) from exc


    # ========================================================================
    # Status
    # ========================================================================


    def status(
        self,
    ) -> RegistryStatus:
        """
        Return registry status.
        """


        with self._lock:


            versions = tuple(
                sorted(
                    self._manifest["models"].keys()
                )
            )


            return RegistryStatus(
                registry=REGISTRY_NAME,
                version=REGISTRY_VERSION,
                schema_version=REGISTRY_SCHEMA_VERSION,
                model_count=len(
                    versions
                ),
                versions=versions,
                registry_path=str(
                    self.manifest_path
                ),
            )


    # ========================================================================
    # Integrity verification
    # ========================================================================


    def verify(
        self,
        version: str | None = None,
    ) -> bool:
        """
        Verify integrity and compatibility of a registered model.
        """


        record = self.get_record(
            version
        )


        model_path = Path(
            record.model_path
        )


        actual_hash = _calculate_file_hash(
            model_path
        )


        if actual_hash != record.model_hash:
            raise ModelIntegrityError(
                f"SHA-256 mismatch for model version '{record.version}'."
            )


        model = EnterpriseGuardModel(
            model_directory=model_path.parent,
            auto_load=True,
        )


        metadata = model.metadata()


        if not metadata.trained:
            raise ModelCompatibilityError(
                "Registered model is not trained."
            )


        if metadata.version != record.version:
            raise ModelCompatibilityError(
                "Model version mismatch."
            )


        if metadata.schema_version != (
            record.schema_version
        ):
            raise ModelCompatibilityError(
                "Model schema mismatch."
            )


        if metadata.feature_count != (
            record.feature_count
        ):
            raise ModelCompatibilityError(
                "Model feature count mismatch."
            )


        if tuple(
            metadata.feature_names
        ) != tuple(
            record.feature_names
        ):
            raise ModelCompatibilityError(
                "Model feature names mismatch."
            )


        return True




# ============================================================================
# Compatibility alias
# ============================================================================


EnterpriseGuardModelRegistry = ModelRegistry




# ============================================================================
# Self-Test
# ============================================================================




def _self_test() -> None:
    """
    Independent Model Registry self-test.


    The test uses a temporary registry directory and therefore does not
    modify the production registry.
    """


    print("=" * 78)
    print(
        "EnterpriseGuard Model Registry - Self Test"
    )
    print("=" * 78)


    temporary_root = Path(
        tempfile.mkdtemp(
            prefix="enterpriseguard_registry_test_"
        )
    )


    model_directory = (
        temporary_root
        / "source_model"
    )


    registry_directory = (
        temporary_root
        / "registry"
    )


    try:


        # --------------------------------------------------------------------
        # 1. Create source model
        # --------------------------------------------------------------------


        print("\n[1] Creating model")


        source_model = EnterpriseGuardModel(
            model_directory=model_directory,
            auto_load=False,
        )


        print(
            json.dumps(
                source_model.status(),
                indent=4,
                ensure_ascii=False,
            )
        )


        # --------------------------------------------------------------------
        # 2. Verify baseline cannot be registered
        # --------------------------------------------------------------------


        print(
            "\n[2] Baseline registration rejection"
        )


        registry = ModelRegistry(
            registry_directory=registry_directory
        )


        try:
            registry.register(
                source_model
            )


            raise AssertionError(
                "Baseline model was incorrectly accepted."
            )


        except ModelCompatibilityError:


            print(
                "PASS - baseline model rejected."
            )


        # --------------------------------------------------------------------
        # 3. Train model
        # --------------------------------------------------------------------


        print(
            "\n[3] Training test model"
        )


        samples = [
            {
                "request_frequency": 0.10,
                "failure_ratio": 0.05,
                "unique_source_count": 0.10,
                "unique_user_count": 0.10,
                "failed_attempts": 1,
                "anomaly_score": 0.05,
                "outbound_data_volume": 0.05,
            },
            {
                "request_frequency": 0.15,
                "failure_ratio": 0.10,
                "unique_source_count": 0.15,
                "unique_user_count": 0.10,
                "failed_attempts": 2,
                "anomaly_score": 0.10,
                "outbound_data_volume": 0.10,
            },
            {
                "request_frequency": 0.90,
                "failure_ratio": 0.85,
                "unique_source_count": 0.80,
                "unique_user_count": 0.85,
                "failed_attempts": 15,
                "anomaly_score": 0.90,
                "outbound_data_volume": 0.80,
            },
            {
                "request_frequency": 0.95,
                "failure_ratio": 0.90,
                "unique_source_count": 0.90,
                "unique_user_count": 0.95,
                "failed_attempts": 18,
                "anomaly_score": 0.95,
                "outbound_data_volume": 0.90,
            },
        ]


        labels = [
            0,
            0,
            1,
            1,
        ]


        training_result = source_model.train(
            samples,
            labels,
            persist=True,
        )


        print(
            json.dumps(
                {
                    "training_status": training_result.get(
                        "training_status"
                    ),
                    "trained": source_model.trained,
                    "model_version": source_model.metadata().version,
                    "training_samples": source_model.training_samples,
                    "model_hash": source_model.model_hash,
                },
                indent=4,
                ensure_ascii=False,
            )
        )


        if not source_model.trained:
            raise AssertionError(
                "Test model was not trained."
            )


        # --------------------------------------------------------------------
        # 4. Register
        # --------------------------------------------------------------------


        print(
            "\n[4] Registering trained model"
        )


        registered = registry.register(
            source_model
        )


        print(
            json.dumps(
                registered.to_dict(),
                indent=4,
                ensure_ascii=False,
            )
        )


        if not registered.trained:
            raise AssertionError(
                "Registered model is not marked as trained."
            )


        if registered.baseline:
            raise AssertionError(
                "Registered trained model is incorrectly marked as baseline."
            )


        # --------------------------------------------------------------------
        # 5. Registry status
        # --------------------------------------------------------------------


        print(
            "\n[5] Registry status"
        )


        status = registry.status()


        print(
            json.dumps(
                status.to_dict(),
                indent=4,
                ensure_ascii=False,
            )
        )


        if status.model_count != 1:
            raise AssertionError(
                "Registry should contain exactly one model."
            )


        # --------------------------------------------------------------------
        # 6. Get record
        # --------------------------------------------------------------------


        print(
            "\n[6] Reading registered record"
        )


        record = registry.get_record(
            registered.version
        )


        print(
            json.dumps(
                record.to_dict(),
                indent=4,
                ensure_ascii=False,
            )
        )


        # --------------------------------------------------------------------
        # 7. Integrity verification
        # --------------------------------------------------------------------


        print(
            "\n[7] Verifying model integrity"
        )


        verified = registry.verify(
            registered.version
        )


        if not verified:
            raise AssertionError(
                "Model integrity verification failed."
            )


        print(
            "PASS - model integrity verified."
        )


        # --------------------------------------------------------------------
        # 8. Load registered model
        # --------------------------------------------------------------------


        print(
            "\n[8] Loading registered model"
        )


        loaded_model = registry.get(
            registered.version
        )


        loaded_metadata = (
            loaded_model.metadata()
        )


        print(
            json.dumps(
                loaded_metadata.to_dict(),
                indent=4,
                ensure_ascii=False,
            )
        )


        if not loaded_model.trained:
            raise AssertionError(
                "Loaded registry model is not trained."
            )


        if (
            loaded_metadata.version
            != registered.version
        ):
            raise AssertionError(
                "Loaded model version mismatch."
            )


        if (
            loaded_metadata.schema_version
            != MODEL_SCHEMA_VERSION
        ):
            raise AssertionError(
                "Loaded model schema mismatch."
            )


        if tuple(
            loaded_metadata.feature_names
        ) != tuple(
            FEATURE_NAMES
        ):
            raise AssertionError(
                "Loaded model feature contract mismatch."
            )


        # --------------------------------------------------------------------
        # 9. Prediction
        # --------------------------------------------------------------------


        print(
            "\n[9] Prediction using registered model"
        )


        prediction_features = samples[0]


        prediction = loaded_model.predict(
            prediction_features
        )


        print(
            json.dumps(
                prediction.to_dict(),
                indent=4,
                ensure_ascii=False,
            )
        )


        if prediction.error is not None:
            raise AssertionError(
                "Registered model prediction failed."
            )


        if not prediction.model_trained:
            raise AssertionError(
                "Prediction did not report trained model."
            )


        # --------------------------------------------------------------------
        # 10. List models
        # --------------------------------------------------------------------


        print(
            "\n[10] Listing registered models"
        )


        models = registry.list_models()


        print(
            json.dumps(
                [
                    item.to_dict()
                    for item in models
                ],
                indent=4,
                ensure_ascii=False,
            )
        )


        if len(models) != 1:
            raise AssertionError(
                "Expected exactly one registered model."
            )


        # --------------------------------------------------------------------
        # 11. Duplicate registration rejection
        # --------------------------------------------------------------------


        print(
            "\n[11] Duplicate registration rejection"
        )


        try:


            registry.register(
                source_model
            )


            raise AssertionError(
                "Duplicate registration was incorrectly accepted."
            )


        except ModelRegistrationError:


            print(
                "PASS - duplicate version rejected."
            )


        # --------------------------------------------------------------------
        # 12. Remove
        # --------------------------------------------------------------------


        print(
            "\n[12] Removing registered model"
        )


        removed = registry.remove(
            registered.version
        )


        if not removed:
            raise AssertionError(
                "Registered model was not removed."
            )


        if registry.status().model_count != 0:
            raise AssertionError(
                "Registry should be empty after removal."
            )


        print(
            "PASS - model removed."
        )


        # --------------------------------------------------------------------
        # Complete
        # --------------------------------------------------------------------


        print(
            "\n" + "=" * 78
        )


        print(
            "Model Registry self-test completed successfully."
        )


        print(
            "=" * 78
        )


    finally:


        shutil.rmtree(
            temporary_root,
            ignore_errors=True,
        )




# ============================================================================
# Entry Point
# ============================================================================




if __name__ == "__main__":
    _self_test()