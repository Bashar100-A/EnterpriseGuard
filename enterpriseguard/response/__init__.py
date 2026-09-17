"""Compatibility boundary for the canonical response package.

The authoritative implementation lives under src/enterpriseguard/response.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

__root__ = Path(__file__).resolve().parent
__repo_root__ = __root__.parent.parent
__canonical_root__ = (__repo_root / "src" / "enterpriseguard" / "response").resolve()
__fallback_root__ = __root__.resolve()
__path__ = [str(__canonical_root__), str(__fallback_root__)]

__title__ = "EnterpriseGuard Response Subsystem"
__version__ = "1.0.0"
__author__ = "EnterpriseGuard"
__description__ = (
    "Policy-driven response planning, controlled execution, "
    "post-execution verification, and tamper-evident auditing."
)


def get_response_engine() -> Any:
    """Return the canonical Response Engine class."""
    from .engine import ResponseEngine

    return ResponseEngine


def get_response_executor() -> Any:
    """Return the canonical Response Executor class."""
    from .executor import ResponseExecutor

    return ResponseExecutor


def get_response_verification_engine() -> Any:
    """Return the canonical Response Verification Engine class."""
    from .verification import ResponseVerificationEngine

    return ResponseVerificationEngine


def get_response_audit_engine() -> Any:
    """Return the canonical Response Audit Engine class."""
    from .audit import ResponseAuditEngine

    return ResponseAuditEngine


def create_response_engine(*args: Any, **kwargs: Any) -> Any:
    """Create a canonical Response Engine instance."""
    return get_response_engine()(*args, **kwargs)


def create_response_executor(*args: Any, **kwargs: Any) -> Any:
    """Create a canonical Response Executor instance."""
    return get_response_executor()(*args, **kwargs)


def create_response_verification_engine(*args: Any, **kwargs: Any) -> Any:
    """Create a canonical Response Verification Engine instance."""
    return get_response_verification_engine()(*args, **kwargs)


def create_response_audit_engine(*args: Any, **kwargs: Any) -> Any:
    """Create a canonical Response Audit Engine instance."""
    return get_response_audit_engine()(*args, **kwargs)


def health_check() -> Dict[str, Any]:
    """Return a package-level health report."""
    components: Dict[str, Dict[str, Any]] = {}
    loaders = {
        "engine": get_response_engine,
        "executor": get_response_executor,
        "verification": get_response_verification_engine,
        "audit": get_response_audit_engine,
    }

    for name, loader in loaders.items():
        try:
            component = loader()
            components[name] = {
                "available": True,
                "component": getattr(component, "__name__", str(component)),
            }
        except Exception as exc:  # pragma: no cover - compatibility boundary only
            components[name] = {
                "available": False,
                "component": None,
                "error": str(exc),
            }

    healthy = all(info["available"] for info in components.values())
    return {
        "healthy": healthy,
        "package": __title__,
        "version": __version__,
        "components": components,
        "safety": {
            "read_only_package_check": True,
            "executes_security_actions": False,
            "shell_execution": False,
            "network_operations": False,
            "process_operations": False,
            "account_modification": False,
        },
    }


__all__ = [
    "__title__",
    "__version__",
    "__author__",
    "__description__",
    "get_response_engine",
    "get_response_executor",
    "get_response_verification_engine",
    "get_response_audit_engine",
    "create_response_engine",
    "create_response_executor",
    "create_response_verification_engine",
    "create_response_audit_engine",
    "health_check",
]
