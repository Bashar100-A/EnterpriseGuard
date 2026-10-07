"""Canonical Decision Lifecycle (Stage 3B).

Stage 3B separates two independent semantic axes that were previously
conflated:

  Axis L — Decision Lifecycle
      The artifact/process lifecycle of a decision.
      Does NOT express permission.

  Axis A — Authorization Status
      Whether the decision currently has authority for the governed
      mode (emission/acceptance).
      Does NOT express progression.

Invariants (Stage 3B):

  AUTHORIZED != EXECUTED_EXTERNAL
  EMITTED    != EXECUTED_EXTERNAL
  VALIDATED  != AUTHORIZED
  APPROVED   != AUTHORIZED

EXECUTES_SECURITY_ACTIONS = False
"""
from __future__ import annotations

from enum import Enum


class DecisionLifecycle(str, Enum):
    """Artifact/process lifecycle of a decision. NOT a permission axis."""

    PROPOSED = "proposed"
    VALIDATED = "validated"
    AUTHORIZED = "authorized"
    EMITTED = "emitted"
    EXECUTED_EXTERNAL = "executed_external"
    OBSERVED = "observed"
    ASSESSED = "assessed"
    CLOSED = "closed"


class AuthorizationStatus(str, Enum):
    """Whether a decision currently has authority for the governed mode.

    Independent of lifecycle. AUTHORIZED here does not mean the decision
    has progressed to DecisionLifecycle.EXECUTED_EXTERNAL.
    """

    PENDING = "pending"
    AUTHORIZED = "authorized"
    DENIED = "denied"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


EXECUTES_SECURITY_ACTIONS = False


__all__ = [
    "DecisionLifecycle",
    "AuthorizationStatus",
    "EXECUTES_SECURITY_ACTIONS",
]
