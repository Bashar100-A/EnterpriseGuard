import hashlib
import pickle
import pytest
from pathlib import Path

from enterpriseguard.intelligence.training.model_loader import (
    ModelLoader,
    ModelLoadError,
    ModelNotRegisteredError,
    ModelIntegrityError,
    ModelCompatibilityError,
    EXPECTED_MODEL_NAME,
    EXPECTED_MODEL_VERSION,
    EXPECTED_MODEL_SCHEMA_VERSION,
    EXPECTED_FEATURE_NAMES,
    EXPECTED_FEATURE_COUNT,
    _self_test,
)


class DummyModel:
    MODEL_VERSION = EXPECTED_MODEL_VERSION
    feature_names = EXPECTED_FEATURE_NAMES
    trained = True

    def __init__(self):
        self.model_type = "LogisticRegression"


class MockRegistry:
    def __init__(self, record):
        self._record = dict(record)

    def get(self, version):
        if version != self._record.get("version"):
            return None
        return dict(self._record)

    def get_latest(self):
        return dict(self._record)


@pytest.fixture
def valid_setup(tmp_path):
    model_path = tmp_path / "model.pkl"
    model = DummyModel()
    with model_path.open("wb") as f:
        pickle.dump(model, f)

    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    record = {
        "name": EXPECTED_MODEL_NAME,
        "version": EXPECTED_MODEL_VERSION,
        "schema_version": EXPECTED_MODEL_SCHEMA_VERSION,
        "feature_count": EXPECTED_FEATURE_COUNT,
        "feature_names": list(EXPECTED_FEATURE_NAMES),
        "model_type": "LogisticRegression",
        "trained": True,
        "baseline": False,
        "model_path": str(model_path),
        "model_hash": digest,
    }
    return record, model_path


def test_successful_load(valid_setup):
    record, _ = valid_setup
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    result = loader.load(EXPECTED_MODEL_VERSION)
    assert result.success is True
    assert result.model_version == EXPECTED_MODEL_VERSION


def test_unregistered_version(valid_setup):
    record, _ = valid_setup
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError) as exc_info:
        loader.load("9.9.9")
    assert "not registered" in str(exc_info.value)


def test_hash_mismatch(valid_setup):
    record, _ = valid_setup
    record["model_hash"] = "a" * 64
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError) as exc_info:
        loader.load(EXPECTED_MODEL_VERSION)
    assert "verification failed" in str(exc_info.value)


def test_untrained_model(valid_setup):
    record, _ = valid_setup
    record["trained"] = False
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError) as exc_info:
        loader.load(EXPECTED_MODEL_VERSION)
    assert "Untrained models cannot be loaded" in str(exc_info.value)


def test_invalid_schema_version(valid_setup):
    record, _ = valid_setup
    record["schema_version"] = 999
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError) as exc_info:
        loader.load(EXPECTED_MODEL_VERSION)
    assert "schema mismatch" in str(exc_info.value)


def test_missing_model_file(valid_setup):
    record, model_path = valid_setup
    model_path.unlink()
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)


def test_corrupted_model_file(valid_setup):
    record, model_path = valid_setup
    model_path.write_bytes(b"corrupted binary data")
    record["model_hash"] = hashlib.sha256(b"corrupted binary data").hexdigest()
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)


def test_baseline_model_rejected(valid_setup):
    record, _ = valid_setup
    record["baseline"] = True
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)


def test_feature_count_mismatch(valid_setup):
    record, _ = valid_setup
    record["feature_count"] = 5
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)


def test_feature_names_mismatch(valid_setup):
    record, _ = valid_setup
    record["feature_names"] = ["a", "b", "c", "d", "e", "f", "g"]
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)


def test_load_latest_version(valid_setup):
    record, _ = valid_setup
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    result = loader.load()
    assert result.success is True


def test_missing_record_keys(valid_setup):
    record, _ = valid_setup
    del record["model_path"]
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)


def test_model_type_mismatch(valid_setup):
    record, _ = valid_setup
    record["model_type"] = "RandomForest"
    registry = MockRegistry(record)
    loader = ModelLoader(registry=registry)

    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)


def test_empty_registry_latest():
    class EmptyRegistry:
        def get_latest(self):
            return None

    loader = ModelLoader(registry=EmptyRegistry())
    with pytest.raises(ModelLoadError):
        loader.load()


def test_registry_alternative_methods(valid_setup):
    record, _ = valid_setup

    class AltRegistry:
        def get_model(self, version):
            return dict(record) if version == EXPECTED_MODEL_VERSION else None

    loader = ModelLoader(registry=AltRegistry())
    result = loader.load(EXPECTED_MODEL_VERSION)
    assert result.success is True


def test_registry_raises_unexpected_exception():
    class BrokenRegistry:
        def get(self, version):
            raise RuntimeError("Database connection failed")

    loader = ModelLoader(registry=BrokenRegistry())
    with pytest.raises(ModelLoadError) as exc_info:
        loader.load(EXPECTED_MODEL_VERSION)
    assert "Failed to load" in str(exc_info.value)


def test_custom_exceptions_and_self_test():
    e1 = ModelNotRegisteredError("test")
    e2 = ModelIntegrityError("test")
    e3 = ModelCompatibilityError("test")
    assert str(e1) == "test"
    assert str(e2) == "test"
    assert str(e3) == "test"

    assert _self_test() is True


def test_loaded_model_instance_validation(valid_setup, tmp_path):
    record, _ = valid_setup

    class BadModel1:
        feature_names = EXPECTED_FEATURE_NAMES
        trained = True

    bad_path = tmp_path / "bad1.pkl"
    with bad_path.open("wb") as f:
        pickle.dump(BadModel1(), f)

    record["model_path"] = str(bad_path)
    record["model_hash"] = hashlib.sha256(bad_path.read_bytes()).hexdigest()

    loader = ModelLoader(registry=MockRegistry(record))
    with pytest.raises(ModelLoadError):
        loader.load(EXPECTED_MODEL_VERSION)
