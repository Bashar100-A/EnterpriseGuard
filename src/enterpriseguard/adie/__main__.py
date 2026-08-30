"""
EnterpriseGuard ADIE Foundation - Package Entry Point
=======================================================

Executable entry point for the ADIE control-plane package.

Usage
-----

    python -m enterpriseguard.adie

The entry point executes the package-level ADIE self-test and returns
a process exit code suitable for automation, CI/CD, health validation,
and operational diagnostics.

Security Boundary
-----------------

This module performs validation only.

It does NOT:

- execute security actions
- execute destructive actions
- modify enterprise state
- activate response adapters
- perform rollback operations

The ADIE package remains a planning and control-plane subsystem.
"""

from __future__ import annotations

import json
import sys
from typing import Any


# ============================================================================
# Constants
# ============================================================================

MODULE_NAME = "adie"
EXECUTES_SECURITY_ACTIONS = False
DESTRUCTIVE_ACTIONS_ALLOWED = False


# ============================================================================
# Package self-test
# ============================================================================


def _run_package_self_test() -> dict[str, Any]:
    """
    Execute the official ADIE package-level self-test.

    The public ``self_test`` function from the package root is used
    intentionally. This keeps the executable entry point aligned with
    the package's public API and avoids coupling it to private symbols.
    """

    from . import self_test

    result = self_test()

    if not isinstance(result, dict):
        raise TypeError(
            "ADIE package self_test() must return dict[str, Any]"
        )

    return result


# ============================================================================
# Result normalization
# ============================================================================


def _normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize the package self-test result.

    The normalization reinforces the ADIE security boundary at the
    executable entry point without modifying the original test result.
    """

    normalized = dict(result)

    normalized.setdefault("module", MODULE_NAME)
    normalized.setdefault(
        "executes_security_actions",
        EXECUTES_SECURITY_ACTIONS,
    )
    normalized.setdefault(
        "destructive_actions_allowed",
        DESTRUCTIVE_ACTIONS_ALLOWED,
    )

    # The executable entry point must never report an unsafe boundary.
    if normalized["executes_security_actions"] is not False:
        normalized["passed"] = False

    if normalized["destructive_actions_allowed"] is not False:
        normalized["passed"] = False

    return normalized


# ============================================================================
# Main
# ============================================================================


def main() -> int:
    """
    Run the ADIE package self-test.

    Returns
    -------
    int
        ``0`` when the self-test passes.
        ``1`` when the self-test fails or an unexpected error occurs.
    """

    try:
        result = _run_package_self_test()
        result = _normalize_result(result)

    except Exception as exc:
        result = {
            "passed": False,
            "module": MODULE_NAME,
            "error": type(exc).__name__,
            "error_message": str(exc),
            "executes_security_actions": False,
            "destructive_actions_allowed": False,
        }

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            default=str,
        )
    )

    return 0 if result.get("passed") is True else 1


# ============================================================================
# Module execution
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())