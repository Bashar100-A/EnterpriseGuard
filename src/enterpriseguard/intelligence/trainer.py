"""
EnterpriseGuard - Machine Learning Training Pipeline
=====================================================


Production-oriented training orchestration layer.


Responsibilities:
    - Load and validate the EnterpriseGuard dataset
    - Convert dataset vectors to canonical feature mappings
    - Train EnterpriseGuardModel
    - Persist the trained model
    - Verify the resulting model
    - Provide operational status and self-test


Architecture:


    Dataset
       |
       v
    Validator
       |
       +---- invalid ----> STOP
       |
       v
    Feature Mapping
       |
       v
    EnterpriseGuardModel
       |
       v
    Persistence
       |
       v
    Verification
"""


from __future__ import annotations


import json
import logging
import time
from datetime import datetime, timezone
from typing import Any


from enterpriseguard.intelligence.training import dataset
from enterpriseguard.intelligence.training.validator import (
    validate_training_dataset,
)
from enterpriseguard.intelligence.models import (
    EnterpriseGuardModel,
    FEATURE_NAMES,
)




# ============================================================================
# Configuration
# ============================================================================


PIPELINE_NAME = "EnterpriseGuard ML Training Pipeline"
PIPELINE_VERSION = "2.1.0"


logger = logging.getLogger("enterpriseguard.trainer")


if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    )
    logger.addHandler(handler)


logger.setLevel(logging.INFO)




# ============================================================================
# Exceptions
# ============================================================================


class ModelTrainingError(RuntimeError):
    """Raised when model training fails."""




class DatasetValidationError(ModelTrainingError):
    """Raised when the training dataset fails validation."""




# ============================================================================
# Dataset helpers
# ============================================================================


def load_training_dataset() -> Any:
    """
    Build and return the EnterpriseGuard training dataset.


    The current dataset module exposes build_demo_dataset().
    """


    builder = getattr(
        dataset,
        "build_demo_dataset",
        None,
    )


    if not callable(builder):
        raise ModelTrainingError(
            "Training dataset builder 'build_demo_dataset' "
            "is unavailable."
        )


    training_dataset = builder()


    if training_dataset is None:
        raise ModelTrainingError(
            "Dataset builder returned None."
        )


    return training_dataset




def get_dataset_size(training_dataset: Any) -> int:
    """Safely obtain dataset size."""


    size = getattr(
        training_dataset,
        "size",
        0,
    )


    if callable(size):
        size = size()


    return int(size)




def extract_dataset_matrix(
    training_dataset: Any,
) -> tuple[list[list[float]], list[int]]:
    """
    Extract feature matrix and labels from TrainingDataset.


    The dataset exposes feature_matrix() and labels() methods.
    """


    feature_matrix_attr = getattr(
        training_dataset,
        "feature_matrix",
        None,
    )


    labels_attr = getattr(
        training_dataset,
        "labels",
        None,
    )


    if not callable(feature_matrix_attr):
        raise ModelTrainingError(
            "TrainingDataset.feature_matrix() is unavailable."
        )


    if not callable(labels_attr):
        raise ModelTrainingError(
            "TrainingDataset.labels() is unavailable."
        )


    matrix = feature_matrix_attr()
    labels = labels_attr()


    matrix = [
        [float(value) for value in row]
        for row in matrix
    ]


    labels = [
        int(label)
        for label in labels
    ]


    if not matrix:
        raise ModelTrainingError(
            "Training dataset contains no feature samples."
        )


    if len(matrix) != len(labels):
        raise ModelTrainingError(
            "Feature matrix and labels have different lengths."
        )


    for index, row in enumerate(matrix):
        if len(row) != len(FEATURE_NAMES):
            raise ModelTrainingError(
                f"Sample {index} contains {len(row)} features; "
                f"expected {len(FEATURE_NAMES)}."
            )


    return matrix, labels




def vector_to_feature_mapping(
    vector: list[float],
) -> dict[str, float]:
    """
    Convert the canonical dataset vector into the mapping expected
    by EnterpriseGuardModel.
    """


    if len(vector) != len(FEATURE_NAMES):
        raise ModelTrainingError(
            f"Feature vector contains {len(vector)} values; "
            f"expected {len(FEATURE_NAMES)}."
        )


    return {
        name: float(value)
        for name, value in zip(
            FEATURE_NAMES,
            vector,
        )
    }




def matrix_to_feature_mappings(
    matrix: list[list[float]],
) -> list[dict[str, float]]:
    """Convert the entire feature matrix to model-ready mappings."""


    return [
        vector_to_feature_mapping(vector)
        for vector in matrix
    ]




# ============================================================================
# Dataset validation
# ============================================================================


def validate_training_dataset_or_raise(
    training_dataset: Any,
) -> dict[str, Any]:
    """
    Validate the dataset using the canonical training validator.


    This function is the mandatory validation gate before training.


    Returns
    -------
    dict[str, Any]
        Machine-readable validation report.


    Raises
    ------
    DatasetValidationError
        If the dataset is invalid.
    """


    try:
        validation_result = validate_training_dataset(
            training_dataset
        )


    except Exception as exc:
        raise DatasetValidationError(
            "Training dataset validation could not be completed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


    if hasattr(
        validation_result,
        "valid",
    ):
        valid = bool(
            validation_result.valid
        )
    else:
        valid = bool(
            validation_result.get(
                "valid",
                False,
            )
        )


    if hasattr(
        validation_result,
        "errors",
    ):
        errors = list(
            validation_result.errors
        )
    else:
        errors = list(
            validation_result.get(
                "errors",
                [],
            )
        )


    if hasattr(
        validation_result,
        "warnings",
    ):
        warnings = list(
            validation_result.warnings
        )
    else:
        warnings = list(
            validation_result.get(
                "warnings",
                [],
            )
        )


    if hasattr(
        validation_result,
        "total_samples",
    ):
        total_samples = int(
            validation_result.total_samples
        )
    else:
        total_samples = int(
            validation_result.get(
                "total_samples",
                get_dataset_size(
                    training_dataset
                ),
            )
        )


    if hasattr(
        validation_result,
        "benign_samples",
    ):
        benign_samples = int(
            validation_result.benign_samples
        )
    else:
        benign_samples = int(
            validation_result.get(
                "benign_samples",
                0,
            )
        )


    if hasattr(
        validation_result,
        "threat_samples",
    ):
        threat_samples = int(
            validation_result.threat_samples
        )
    else:
        threat_samples = int(
            validation_result.get(
                "threat_samples",
                0,
            )
        )


    if hasattr(
        validation_result,
        "feature_count",
    ):
        feature_count = int(
            validation_result.feature_count
        )
    else:
        feature_count = int(
            validation_result.get(
                "feature_count",
                len(FEATURE_NAMES),
            )
        )


    report = {
        "valid": valid,
        "total_samples": total_samples,
        "benign_samples": benign_samples,
        "threat_samples": threat_samples,
        "feature_count": feature_count,
        "errors": errors,
        "warnings": warnings,
    }


    if not valid:
        message = (
            "Training dataset validation failed."
        )


        if errors:
            message += " " + " | ".join(
                str(error)
                for error in errors
            )


        raise DatasetValidationError(
            message
        )


    return report




def dataset_status(
    training_dataset: Any,
) -> dict[str, Any]:
    """
    Return operational dataset status.


    This receives the dataset instance because the current
    dataset_status() API requires it.
    """


    status_function = getattr(
        dataset,
        "dataset_status",
        None,
    )


    if not callable(status_function):
        return {
            "status": "UNAVAILABLE",
            "error": "dataset_status() is unavailable.",
        }


    try:
        result = status_function(
            training_dataset
        )


        if isinstance(result, dict):
            return result


        return {
            "status": "SUCCESS",
            "result": str(result),
        }


    except Exception as exc:
        return {
            "status": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }




# ============================================================================
# Training
# ============================================================================


def train_model(
    feature_mappings: list[dict[str, float]],
    labels: list[int],
    model: EnterpriseGuardModel,
) -> dict[str, Any]:
    """
    Train and persist the EnterpriseGuard model.
    """


    if not feature_mappings:
        raise ModelTrainingError(
            "No training samples were supplied."
        )


    if len(feature_mappings) != len(labels):
        raise ModelTrainingError(
            "Feature mappings and labels have different lengths."
        )


    logger.info(
        "Training model with %d samples and %d features.",
        len(feature_mappings),
        len(FEATURE_NAMES),
    )


    try:
        metadata = model.train(
            feature_mappings,
            labels,
        )


        # model.train() persists by default.
        return metadata


    except Exception as exc:
        raise ModelTrainingError(
            "Model training failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc




# ============================================================================
# Model verification
# ============================================================================


def verify_trained_model(
    model: EnterpriseGuardModel,
    feature_mapping: dict[str, float],
) -> dict[str, Any]:
    """
    Perform a post-training prediction to ensure the model is usable.
    """


    if not model.trained:
        raise ModelTrainingError(
            "Model reports trained=False after training."
        )


    prediction = model.predict(
        feature_mapping
    )


    if prediction.error is not None:
        raise ModelTrainingError(
            "Post-training prediction failed: "
            f"{prediction.error}"
        )


    return prediction.to_dict()




# ============================================================================
# Pipeline
# ============================================================================


def run_training_pipeline() -> dict[str, Any]:
    """
    Execute the complete EnterpriseGuard ML training pipeline.


    Validation is a mandatory gate. Training cannot proceed when
    the canonical validator reports an invalid dataset.
    """


    started = time.perf_counter()


    result: dict[str, Any] = {
        "status": "FAILED",
        "trainer": PIPELINE_NAME,
        "version": PIPELINE_VERSION,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "samples": 0,
        "features": len(FEATURE_NAMES),
        "benign_samples": 0,
        "threat_samples": 0,
        "class_balance": 0.0,
        "model_trained": False,
        "training_time_ms": 0.0,
        "model_path": None,
        "model_hash": None,
        "dataset_validation": None,
        "dataset_status": None,
        "verification": None,
        "error": None,
    }


    try:
        # --------------------------------------------------------------------
        # 1. Dataset
        # --------------------------------------------------------------------


        logger.info(
            "Loading training dataset."
        )


        training_dataset = (
            load_training_dataset()
        )


        size = get_dataset_size(
            training_dataset
        )


        logger.info(
            "Dataset loaded: %d samples.",
            size,
        )


        # --------------------------------------------------------------------
        # 2. Dataset status
        # --------------------------------------------------------------------


        result["dataset_status"] = (
            dataset_status(
                training_dataset
            )
        )


        # --------------------------------------------------------------------
        # 3. Mandatory validation gate
        # --------------------------------------------------------------------


        logger.info(
            "Validating training dataset."
        )


        validation = (
            validate_training_dataset_or_raise(
                training_dataset
            )
        )


        result["dataset_validation"] = (
            validation
        )


        logger.info(
            "Dataset validation passed: "
            "%d samples, %d features.",
            validation["total_samples"],
            validation["feature_count"],
        )


        # --------------------------------------------------------------------
        # 4. Dataset statistics
        # --------------------------------------------------------------------


        matrix, labels = (
            extract_dataset_matrix(
                training_dataset
            )
        )


        result["samples"] = len(matrix)


        benign_samples = labels.count(0)
        threat_samples = labels.count(1)
        total_samples = len(labels)


        result["benign_samples"] = (
            benign_samples
        )


        result["threat_samples"] = (
            threat_samples
        )


        if total_samples:
            result["class_balance"] = round(
                benign_samples / total_samples,
                4,
            )


        # --------------------------------------------------------------------
        # 5. Convert vectors to model mappings
        # --------------------------------------------------------------------


        feature_mappings = (
            matrix_to_feature_mappings(
                matrix
            )
        )


        # --------------------------------------------------------------------
        # 6. Create model
        # --------------------------------------------------------------------


        model = EnterpriseGuardModel()


        # --------------------------------------------------------------------
        # 7. Train
        # --------------------------------------------------------------------


        metadata = train_model(
            feature_mappings,
            labels,
            model,
        )


        result["model_trained"] = (
            model.trained
        )


        result["model_path"] = str(
            model.model_path
        )


        result["model_hash"] = (
            metadata.get("model_hash")
        )


        # --------------------------------------------------------------------
        # 8. Verify
        # --------------------------------------------------------------------


        verification = (
            verify_trained_model(
                model,
                feature_mappings[0],
            )
        )


        result["verification"] = (
            verification
        )


        # --------------------------------------------------------------------
        # 9. Success
        # --------------------------------------------------------------------


        result["status"] = "SUCCESS"


        logger.info(
            "Model training completed successfully."
        )


    except Exception as exc:
        result["status"] = "FAILED"


        result["error"] = (
            f"{type(exc).__name__}: {exc}"
        )


        logger.exception(
            "Training pipeline failed."
        )


    finally:
        result["training_time_ms"] = round(
            (
                time.perf_counter()
                - started
            )
            * 1000.0,
            3,
        )


    return result




# ============================================================================
# Pipeline status
# ============================================================================


def pipeline_status(
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Return normalized pipeline status.
    """


    if result is None:
        return {
            "pipeline": PIPELINE_NAME,
            "version": PIPELINE_VERSION,
            "status": "READY",
            "feature_count": len(FEATURE_NAMES),
            "model_trained": False,
        }


    return {
        "pipeline": PIPELINE_NAME,
        "version": PIPELINE_VERSION,
        "status": result.get(
            "status",
            "UNKNOWN",
        ),
        "dataset_samples": result.get(
            "samples",
            0,
        ),
        "feature_count": result.get(
            "features",
            len(FEATURE_NAMES),
        ),
        "benign_samples": result.get(
            "benign_samples",
            0,
        ),
        "threat_samples": result.get(
            "threat_samples",
            0,
        ),
        "class_balance": result.get(
            "class_balance",
            0.0,
        ),
        "dataset_valid": (
            result.get(
                "dataset_validation",
                {},
            ) or {}
        ).get(
            "valid",
            False,
        ),
        "model_trained": result.get(
            "model_trained",
            False,
        ),
        "training_time_ms": result.get(
            "training_time_ms",
            0.0,
        ),
        "model_path": result.get(
            "model_path",
        ),
        "model_hash": result.get(
            "model_hash",
        ),
        "error": result.get(
            "error",
        ),
    }




# ============================================================================
# Self Test
# ============================================================================


def _self_test() -> None:
    """
    Run the complete training pipeline self-test.
    """


    print("=" * 78)
    print(
        "EnterpriseGuard ML Training Pipeline - Self Test"
    )
    print("=" * 78)


    # ------------------------------------------------------------------------
    # Dataset
    # ------------------------------------------------------------------------


    print("\n[1] Loading dataset...")


    try:
        training_dataset = (
            load_training_dataset()
        )


        print(
            json.dumps(
                {
                    "status": "SUCCESS",
                    "dataset_type": type(
                        training_dataset
                    ).__name__,
                    "size": get_dataset_size(
                        training_dataset
                    ),
                },
                indent=4,
                ensure_ascii=False,
            )
        )


    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "stage": "dataset_loading",
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                },
                indent=4,
                ensure_ascii=False,
            )
        )


        return


    # ------------------------------------------------------------------------
    # Dataset status
    # ------------------------------------------------------------------------


    print("\n[2] Dataset status")


    print(
        json.dumps(
            dataset_status(
                training_dataset
            ),
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    # ------------------------------------------------------------------------
    # Matrix
    # ------------------------------------------------------------------------


    print(
        "\n[3] Extracting training matrix..."
    )


    try:
        matrix, labels = (
            extract_dataset_matrix(
                training_dataset
            )
        )


        print(
            json.dumps(
                {
                    "status": "SUCCESS",
                    "samples": len(matrix),
                    "features": (
                        len(matrix[0])
                        if matrix
                        else 0
                    ),
                    "labels": len(labels),
                },
                indent=4,
            )
        )


    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "stage": "matrix_extraction",
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                },
                indent=4,
            )
        )


        return


    # ------------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------------


    print(
        "\n[4] Dataset validation..."
    )


    try:
        validation = (
            validate_training_dataset_or_raise(
                training_dataset
            )
        )


        print(
            json.dumps(
                validation,
                indent=4,
                ensure_ascii=False,
                default=str,
            )
        )


    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "stage": "dataset_validation",
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                },
                indent=4,
                ensure_ascii=False,
            )
        )


        return


    # ------------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------------


    print("\n[5] Training model...")


    result = run_training_pipeline()


    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    # ------------------------------------------------------------------------
    # Final status
    # ------------------------------------------------------------------------


    print(
        "\n[6] Final pipeline status"
    )


    print(
        json.dumps(
            pipeline_status(result),
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


    print("\n")
    print("=" * 78)


    if result["status"] == "SUCCESS":
        print(
            "Training pipeline completed successfully."
        )
    else:
        print(
            "Training pipeline completed with errors."
        )


    print("=" * 78)




# ============================================================================
# Entry Point
# ============================================================================


if __name__ == "__main__":
    _self_test()