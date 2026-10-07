"""Canonical end-to-end integration (Stage 3D).

This package wires 3A (wire/proof) + 3B (governance/authority/decision)
+ 3C (trust/revocation) into a single governed decision path.

It introduces NO new authority. It is a thin, deterministic orchestrator
that fails closed at the earliest detectable boundary.
"""
from .e2e import (
    E2EOutcome, E2EResult, evaluate_end_to_end,
    E2EIntegrationError,
)

__all__ = [
    "E2EOutcome", "E2EResult", "evaluate_end_to_end", "E2EIntegrationError",
]
