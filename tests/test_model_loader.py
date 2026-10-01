import hashlib
import pickle
import pytest
from pathlib import Path
from model_loader import (
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
        if version != self._record["version"]:
            raise KeyError(version)
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
    record["model_hash"] = "a" * 64  # Hash غير مطابق
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
