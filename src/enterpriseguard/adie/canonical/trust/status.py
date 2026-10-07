"""Canonical TrustStatus axis (Stage 3C).

Distinct from AuthorizationStatus (3B axis A) and DecisionLifecycle
(3B axis L). Trust status answers: "Is this trust subject currently
trusted?" — independent of any specific decision or authorization.

Definitions (Commander Order §3):
    EXPIRED   != REVOKED
    SUPERSEDED != REVOKED
    SUSPENDED != REVOKED
"""
from __future__ import annotations

from enum import Enum


class TrustStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


# Semantics table (documented, not enforced by enum):
#
# ACTIVE      — trust subject is currently trustworthy within scope.
# SUSPENDED   — temporarily withheld; reversible; not revoked.
# REVOKED     — permanently terminated by explicit authority.
# EXPIRED     — temporal window ended; not revoked.
# SUPERSEDED  — replaced by a newer subject binding; not revoked.
#
# Terminal semantics:
#   REVOKED     = terminal
#   EXPIRED     = terminal (until a new window is asserted)
#   SUPERSEDED  = terminal
#   SUSPENDED   = non-terminal (reversible to ACTIVE)
#   ACTIVE      = non-terminal

TERMINAL: frozenset[TrustStatus] = frozenset({
    TrustStatus.REVOKED,
    TrustStatus.EXPIRED,
    TrustStatus.SUPERSEDED,
})

REVERSIBLE: frozenset[TrustStatus] = frozenset({
    TrustStatus.ACTIVE,
    TrustStatus.SUSPENDED,
})


__all__ = ["TrustStatus", "TERMINAL", "REVERSIBLE"]
