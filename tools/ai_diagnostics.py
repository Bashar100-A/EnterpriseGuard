import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.time_utils import utc_now
from tools.audit_chain import append_activity as audit_append_activity

from tools.time_utils import utc_now
from typing import Any

from tools.audit_chain import append_activity as audit_append_activity

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
MODEL_ROOT = PROJECT_ROOT / "assets" / "models"
MODEL_REGISTRY_PATH = MODEL_ROOT / "registry" / "model_registry.json"
TRAINING_METADATA_PATH = MODEL_ROOT / "enterpriseguard_training_metadata.json"
MODEL_META_PATH = MODEL_ROOT / "enterpriseguard_model.json"
ACTIVITY_LOG_PATH = TOOLS_DIR / "activity_log.json"
ERROR_LOG_PATH = TOOLS_DIR / "errors.log"

def utc_timestamp() -> str:
    return utc_now().strftime("%Y-%m-%d %H:%M:%S %Z")

def ensure_tools_dir() -> None:
    TOOLS_DIR.mkdir(exist_ok=True, parents=True)

def append_activity(event: str, path: Path | str | None = None) -> None:
    ensure_tools_dir()
    target_path = Path(path) if path is not None else ACTIVITY_LOG_PATH
    try:
        audit_append_activity({
            "activity_type": "ai_diagnostics",
            "event": event,
            "details": event,
            "status": "success",
        }, target_path)
    except Exception:
        pass

def log_error(message: str) -> None:
    ensure_tools_dir()
    try:
        with ERROR_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"[{utc_timestamp()}] {message}\n")
    except Exception:
        pass

def read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        log_error(f"Read error on {path}: {exc}")
        return None

def iter_model_artifacts(root: Path) -> list[Path]:
    if not root.exists():
        return []
    files = []
    for item in sorted(root.iterdir()):
        if item.is_file():
            files.append(item)
    return files

def summarize_registry(registry_path: Path) -> dict[str, Any]:
    registry_data = read_json(registry_path)
    if registry_data is None:
        return {
            "status": "FAILURE",
            "label": "Model registry",
            "detail": "Unable to read registry metadata.",
            "version": "unknown",
            "model_count": 0,
        }

    models = registry_data.get("models", {})
    model_count = len(models) if isinstance(models, dict) else 0
    version = registry_data.get("version", "unknown")
    return {
        "status": "SUCCESS" if registry_path.exists() else "FAILURE",
        "label": "Model registry",
        "detail": f"Registry version {version}, model entries: {model_count}",
        "version": str(version),
        "model_count": model_count,
    }

def summarize_training_metadata(metadata_path: Path) -> dict[str, Any]:
    metadata = read_json(metadata_path)
    if metadata is None:
        return {
            "status": "FAILURE",
            "label": "Training metadata",
            "detail": "Unable to read training metadata.",
            "version": "unknown",
            "trained": False,
        }

    model_info = metadata.get("model", {}) if isinstance(metadata, dict) else {}
    status = metadata.get("result", {}).get("success") if isinstance(metadata.get("result"), dict) else None
    trained = bool(model_info.get("trained") or status)
    version = model_info.get("version", metadata.get("pipeline", {}).get("version", "unknown"))

    return {
        "status": "SUCCESS" if metadata_path.exists() else "FAILURE",
        "label": "Training metadata",
        "detail": f"Training metadata version {version}, trained={trained}",
        "version": str(version),
        "trained": trained,
    }

def summarize_model_meta(model_meta_path: Path) -> dict[str, Any]:
    model_data = read_json(model_meta_path)
    if model_data is None:
        return {
            "status": "FAILURE",
            "label": "Model metadata",
            "detail": "Unable to read model metadata.",
            "version": "unknown",
            "trained": False,
        }

    version = model_data.get("version", "unknown")
    trained = bool(model_data.get("trained"))
    return {
        "status": "SUCCESS" if model_meta_path.exists() else "FAILURE",
        "label": "Model metadata",
        "detail": f"Model metadata version {version}, trained={trained}",
        "version": str(version),
        "trained": trained,
    }

def summarize_artifacts(root: Path) -> dict[str, Any]:
    artifacts = iter_model_artifacts(root)
    if not artifacts:
        return {
            "status": "WARNING",
            "label": "Model artifacts",
            "detail": "No model artifacts found in assets/models.",
            "count": 0,
            "files": [],
        }

    files = [str(item.name) for item in artifacts]
    return {
        "status": "SUCCESS" if artifacts else "WARNING",
        "label": "Model artifacts",
        "detail": f"Found {len(artifacts)} artifact(s) in assets/models.",
        "count": len(artifacts),
        "files": files,
    }

def print_report(report: list[dict[str, Any]]) -> int:
    success_count = sum(1 for item in report if item["status"] == "SUCCESS")
    warning_count = sum(1 for item in report if item["status"] == "WARNING")
    failure_count = sum(1 for item in report if item["status"] == "FAILURE")

    print("\n=== EnterpriseGuard AI Diagnostics ===")
    print(f"SUCCESS: {success_count}")
    print(f"WARNING: {warning_count}")
    print(f"FAILURE: {failure_count}")
    print("--------------------------------------")

    for item in report:
        print(f"[{item['status']}] {item['label']} - {item['detail']}")

    print("======================================\n")
    return 0 if failure_count == 0 else 1

def main() -> int:
    ensure_tools_dir()

    report = []
    report.append(summarize_registry(MODEL_REGISTRY_PATH))
    report.append(summarize_training_metadata(TRAINING_METADATA_PATH))
    report.append(summarize_model_meta(MODEL_META_PATH))
    report.append(summarize_artifacts(MODEL_ROOT))

    append_activity("AI diagnostics run executed", ACTIVITY_LOG_PATH)
    exit_code = print_report(report)

    if exit_code != 0:
        log_error("AI diagnostics reported one or more critical failures.")
        return 1

    print("AI diagnostics completed successfully: model assets and metadata are readable.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        log_error(f"Unexpected AI diagnostics execution error: {exc}")
        append_activity("AI diagnostics run failed due to unexpected execution error", ACTIVITY_LOG_PATH)
        print(f"Unexpected error: {exc}")
        raise SystemExit(1)