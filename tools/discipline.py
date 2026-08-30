from __future__ import annotations

import importlib.util
from pathlib import Path


DEFAULT_REQUIRED_ARTIFACTS = (
    "tools/activity_log.json",
    "tools/DECISIONS_LOG.md",
    "tools/command_center.py",
    "tools/errors.log",
)


def _artifact_path(project_root: Path, relative_path: str) -> Path:
    return (project_root / relative_path).resolve()


def _streamlit_ready() -> bool:
    return importlib.util.find_spec("streamlit") is not None


def validate_discipline(project_root: Path | str) -> dict:
    root = Path(project_root).resolve()
    checks = []
    for relative_path in DEFAULT_REQUIRED_ARTIFACTS:
        artifact = _artifact_path(root, relative_path)
        exists = artifact.exists()
        checks.append(
            {
                "name": relative_path,
                "exists": exists,
                "status": "OK" if exists else "MISSING",
                "message": "Found" if exists else "Missing required governance artifact",
            }
        )

    streamlit_state = _streamlit_ready()
    checks.append(
        {
            "name": "streamlit_runtime",
            "exists": streamlit_state,
            "status": "OK" if streamlit_state else "MISSING",
            "message": "Streamlit runtime detected" if streamlit_state else "Streamlit is not installed in the current environment",
        }
    )

    ready = all(item["exists"] for item in checks)
    return {
        "ready": ready,
        "checks": checks,
        "missing": [item["name"] for item in checks if not item["exists"]],
    }
