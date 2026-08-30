"""
EnterpriseGuard Response Package
================================


Public package interface for the EnterpriseGuard response subsystem.


The response subsystem is intentionally separated into four stages:


    Response Engine
          |
          v
    Response Executor
          |
          v
    Response Verification
          |
          v
    Response Audit


Design principles:
    - Explicit separation of planning, execution, verification, and audit.
    - No arbitrary shell execution.
    - No destructive execution by default.
    - Verification never performs security actions.
    - Audit never performs security actions.
    - Components remain independently usable and testable.
"""


from __future__ import annotations


from typing import Any, Dict




# ---------------------------------------------------------------------------
# Package metadata
# ---------------------------------------------------------------------------


__title__ = "EnterpriseGuard Response Subsystem"
__version__ = "1.0.0"
__author__ = "EnterpriseGuard"
__description__ = (
    "Policy-driven response planning, controlled execution, "
    "post-execution verification, and tamper-evident auditing."
)




# ---------------------------------------------------------------------------
# Lazy component access
# ---------------------------------------------------------------------------


def get_response_engine() -> Any:
    """
    Return the Response Engine class.


    Lazy import prevents unnecessary initialization and keeps package
    imports lightweight.
    """
    from .engine import ResponseEngine


    return ResponseEngine




def get_response_executor() -> Any:
    """
    Return the Response Executor class.
    """
    from .executor import ResponseExecutor


    return ResponseExecutor




def get_response_verification_engine() -> Any:
    """
    Return the Response Verification Engine class.
    """
    from .verification import ResponseVerificationEngine


    return ResponseVerificationEngine




def get_response_audit_engine() -> Any:
    """
    Return the Response Audit Engine class.
    """
    from .audit import ResponseAuditEngine


    return ResponseAuditEngine




# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def create_response_engine(*args: Any, **kwargs: Any) -> Any:
    """
    Create a Response Engine instance.
    """
    engine_class = get_response_engine()
    return engine_class(*args, **kwargs)




def create_response_executor(*args: Any, **kwargs: Any) -> Any:
    """
    Create a Response Executor instance.
    """
    executor_class = get_response_executor()
    return executor_class(*args, **kwargs)




def create_response_verification_engine(*args: Any, **kwargs: Any) -> Any:
    """
    Create a Response Verification Engine instance.
    """
    verification_class = get_response_verification_engine()
    return verification_class(*args, **kwargs)




def create_response_audit_engine(*args: Any, **kwargs: Any) -> Any:
    """
    Create a Response Audit Engine instance.
    """
    audit_class = get_response_audit_engine()
    return audit_class(*args, **kwargs)




# ---------------------------------------------------------------------------
# Package health
# ---------------------------------------------------------------------------


def health_check() -> Dict[str, Any]:
    """
    Return a lightweight package-level health report.


    This function does not execute security actions and does not instantiate
    the response components. It only confirms that the response subsystem
    package is importable.
    """


    components = {}


    component_loaders = {
        "engine": get_response_engine,
        "executor": get_response_executor,
        "verification": get_response_verification_engine,
        "audit": get_response_audit_engine,
    }


    for name, loader in component_loaders.items():
        try:
            component = loader()


            components[name] = {
                "available": True,
                "component": getattr(
                    component,
                    "__name__",
                    str(component),
                ),
            }


        except Exception as exc:
            components[name] = {
                "available": False,
                "component": None,
                "error": str(exc),
            }


    healthy = all(
        component.get("available", False)
        for component in components.values()
    )


    return {
        "healthy": healthy,
        "package": __title__,
        "version": __version__,
        "components": components,
        "safety": {
            "executes_security_actions": False,
            "shell_execution": False,
            "network_operations": False,
            "process_operations": False,
            "account_modification": False,
        },
    }




# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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