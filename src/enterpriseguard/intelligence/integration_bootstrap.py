"""
EnterpriseGuard - Integration Model Bootstrap
==============================================


Purpose
-------
Prepare a real trained, registered, verified, and activated model
for the EnterpriseGuard integration pipeline.


This module creates and wires the existing architecture without
modifying any existing project source file.


Lifecycle:


    TrainingOrchestrator
            |
            v
      TrainingService
            |
            +---- Validator
            |
            +---- Trainer
            |
            +---- ModelRegistry
            |
            +---- ModelLoader
            |
            +---- ModelManager
            |
            v
       Active Model


Safety
------
- No existing source files are modified.
- No direct pickle access.
- No shell execution.
- No network operations.
- No security actions.
- No registry bypass.
- No loader bypass.
- ModelManager safety gates remain active.
"""


from __future__ import annotations


import json
from typing import Any


from enterpriseguard.intelligence.training.model_loader import (
    ModelLoader,
)
from enterpriseguard.intelligence.training.model_manager import (
    ModelManager,
)
from enterpriseguard.intelligence.training.model_registry import (
    ModelRegistry,
)
from enterpriseguard.intelligence.training.orchestrator import (
    TrainingOrchestrator,
)
from enterpriseguard.intelligence.training.training_service import (
    TrainingService,
)




FEATURE_NAMES = (
    "request_frequency",
    "failure_ratio",
    "unique_source_count",
    "unique_user_count",
    "failed_attempts",
    "anomaly_score",
    "outbound_data_volume",
)




def _to_dict(value: Any) -> dict[str, Any]:
    """
    Convert project result objects into dictionaries safely.
    """
    if isinstance(value, dict):
        return dict(value)


    to_dict = getattr(value, "to_dict", None)


    if callable(to_dict):
        result = to_dict()


        if isinstance(result, dict):
            return dict(result)


    data = getattr(value, "__dict__", None)


    if isinstance(data, dict):
        return dict(data)


    return {"value": value}




def _print_json(
    label: str,
    value: Any,
) -> None:
    """
    Pretty-print structured information.
    """
    print(f"{label}:")
    print(
        json.dumps(
            _to_dict(value),
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )




def _section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)




def prepare_integration_model() -> bool:
    """
    Train, register, verify, and activate a real EnterpriseGuard model.


    Returns
    -------
    bool
        True only if the complete lifecycle succeeds.
    """


    _section(
        "EnterpriseGuard - Integration Model Bootstrap"
    )


    print()
    print("Architecture:")
    print("TrainingOrchestrator")
    print("      ↓")
    print("TrainingService")
    print("      ↓")
    print("Validator")
    print("      ↓")
    print("Trainer")
    print("      ↓")
    print("ModelRegistry")
    print("      ↓")
    print("ModelLoader")
    print("      ↓")
    print("ModelManager")
    print("      ↓")
    print("Active Model")


    # ============================================================
    # 1. Model Registry
    # ============================================================


    print()
    print("[1] Model Registry")
    print("-" * 60)


    registry = ModelRegistry()


    print("    registry: READY")


    registry_status = registry.status()


    _print_json(
        "    initial status",
        registry_status,
    )


    # ============================================================
    # 2. Model Loader
    # ============================================================


    print()
    print("[2] Model Loader")
    print("-" * 60)


    loader = ModelLoader(
        registry=registry,
        expected_schema_version=1,
        expected_feature_names=FEATURE_NAMES,
    )


    print("    loader: READY")


    # ============================================================
    # 3. Model Manager
    # ============================================================


    print()
    print("[3] Model Manager")
    print("-" * 60)


    manager = ModelManager(
        registry=registry,
        loader=loader,
        expected_schema_version=1,
        expected_feature_names=FEATURE_NAMES,
        auto_activate=False,
    )


    print("    manager: READY")


    manager_status = manager.status()


    _print_json(
        "    initial status",
        manager_status,
    )


    # ============================================================
    # 4. Training Orchestrator
    # ============================================================


    print()
    print("[4] Training Orchestrator")
    print("-" * 60)


    orchestrator = TrainingOrchestrator(
        minimum_samples=4,
    )


    print("    orchestrator: READY")


    # ============================================================
    # 5. Demo Dataset
    # ============================================================


    print()
    print("[5] Load Demo Dataset")
    print("-" * 60)


    dataset = orchestrator.load_demo_dataset()


    if dataset is None:
        print()
        print("[FAIL] Demo dataset is None.")
        return False


    size = None


    size_method = getattr(
        dataset,
        "size",
        None,
    )


    if callable(size_method):
        try:
            size = size_method()
        except Exception:
            size = None


    if size is None:
        try:
            size = len(dataset)
        except Exception:
            size = "unknown"


    print(f"    dataset size: {size}")
    print("    dataset: READY")


    # ============================================================
    # 6. Training Service
    # ============================================================


    print()
    print("[6] Training Service")
    print("-" * 60)


    training_service = TrainingService(
        orchestrator=orchestrator,
        registry=registry,
        loader=loader,
        manager=manager,
        minimum_samples=4,
    )


    print("    training service: READY")


    # ============================================================
    # 7. Real Training Lifecycle
    # ============================================================


    print()
    print("[7] Real Training Lifecycle")
    print("-" * 60)


    result = training_service.run(
        dataset,
        register=True,
        activate=True,
    )


    result_dict = _to_dict(result)


    _print_json(
        "    lifecycle result",
        result_dict,
    )


    # ============================================================
    # 8. Validate Training Result
    # ============================================================


    print()
    print("[8] Lifecycle Validation")
    print("-" * 60)


    success = bool(
        result_dict.get("success", False)
    )


    status = result_dict.get(
        "status"
    )


    model_version = result_dict.get(
        "model_version"
    )


    error = result_dict.get(
        "error"
    )


    print(
        f"    success:       {success}"
    )


    print(
        f"    status:        {status}"
    )


    print(
        f"    model_version: {model_version}"
    )


    print(
        f"    error:         {error}"
    )


    if not success:
        print()
        print(
            "[FAIL] Training lifecycle failed."
        )


        return False


    if not model_version:
        print()
        print(
            "[FAIL] Training succeeded but "
            "returned no model version."
        )


        return False


    # ============================================================
    # 9. Registration Verification
    # ============================================================


    print()
    print("[9] Registry Verification")
    print("-" * 60)


    registered_record = registry.get_record(
        str(model_version)
    )


    if registered_record is None:
        print()
        print(
            "[FAIL] Model was reported as registered "
            "but cannot be retrieved from Registry."
        )


        return False


    _print_json(
        "    registered model",
        registered_record,
    )


    print(
        f"    registered version: {model_version}"
    )


    # ============================================================
    # 10. Registry State
    # ============================================================


    print()
    print("[10] Registry State")
    print("-" * 60)


    registry_state = registry.status()


    _print_json(
        "    status",
        registry_state,
    )


    # ============================================================
    # 11. Activation Result
    # ============================================================


    print()
    print("[11] Activation")
    print("-" * 60)


    details = result_dict.get(
        "details"
    )


    activation = None


    if isinstance(details, dict):
        activation = details.get(
            "activation"
        )


    if activation is None:
        print()
        print(
            "[FAIL] No activation result was returned."
        )


        return False


    activation_dict = _to_dict(
        activation
    )


    _print_json(
        "    activation",
        activation_dict,
    )


    activation_success = bool(
        activation_dict.get(
            "success",
            False,
        )
    )


    if not activation_success:
        print()
        print(
            "[FAIL] Model activation failed."
        )


        return False


    # ============================================================
    # 12. Direct Manager State Verification
    # ============================================================


    print()
    print("[12] Model Manager Verification")
    print("-" * 60)


    active = manager.is_active()


    active_version = manager.active_version()


    print(
        f"    active:         {active}"
    )


    print(
        f"    active_version: {active_version}"
    )


    if not active:
        print()
        print(
            "[FAIL] ModelManager reports that "
            "no model is active."
        )


        return False


    if active_version is None:
        print()
        print(
            "[FAIL] ModelManager reports active state "
            "but no active version."
        )


        return False


    if str(active_version) != str(
        model_version
    ):
        print()
        print(
            "[FAIL] Active version mismatch."
        )


        print(
            f"    expected: {model_version}"
        )


        print(
            f"    actual:   {active_version}"
        )


        return False


    # ============================================================
    # 13. Loader Verification
    # ============================================================


    print()
    print("[13] Model Loader Verification")
    print("-" * 60)


    loaded_model = loader.get_loaded_model()


    loaded_record = loader.get_loaded_record()


    print(
        f"    loaded: "
        f"{loaded_model is not None}"
    )


    print(
        f"    loaded_record: "
        f"{loaded_record is not None}"
    )


    if loaded_model is None:
        print()
        print(
            "[FAIL] ModelManager reports successful "
            "activation but Loader has no loaded model."
        )


        return False


    if loaded_record is None:
        print()
        print(
            "[FAIL] ModelManager reports successful "
            "activation but Loader has no loaded record."
        )


        return False


    # ============================================================
    # 14. Final Status
    # ============================================================


    print()
    print("[14] Final Model State")
    print("-" * 60)


    final_manager_status = manager.status()


    _print_json(
        "    manager status",
        final_manager_status,
    )


    # ============================================================
    # SUCCESS
    # ============================================================


    _section(
        "INTEGRATION MODEL BOOTSTRAP: PASS"
    )


    print()
    print(
        "A real model has successfully completed:"
    )


    print()
    print("    Training        PASS")
    print("    Registration    PASS")
    print("    Verification    PASS")
    print("    Loading         PASS")
    print("    Activation      PASS")


    print()
    print(
        f"Active model version: {active_version}"
    )


    print()
    print(
        "The EnterpriseGuard detection pipeline "
        "is now ready for the real integration test."
    )


    return True




def main() -> int:
    """
    CLI entry point.
    """


    try:
        return (
            0
            if prepare_integration_model()
            else 1
        )


    except Exception as exc:
        print()
        print("=" * 60)
        print(
            "INTEGRATION MODEL BOOTSTRAP: FAIL"
        )
        print("=" * 60)
        print()
        print(
            f"{type(exc).__name__}: {exc}"
        )


        return 1




if __name__ == "__main__":
    raise SystemExit(
        main()
    )