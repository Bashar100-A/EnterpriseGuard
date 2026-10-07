"""Deterministic trust-status resolver (Stage 3C).

Resolves the current / historical trust status of a subject from its
assertion history. Never mutates history. Never rewrites artifacts.

Determinism rules:
  - Only assertions with effective_at <= query_time are relevant.
  - Ties broken by (effective_at, observed_at, assertion_id).
  - Two assertions with same (effective_at, observed_at) but DIFFERENT
    kinds produce a CONFLICT outcome -> fail closed.
  - If no assertion applies -> UNKNOWN outcome (fail closed).
  - "UNKNOWN -> ACTIVE" is explicitly forbidden.

Historical vs current:
  - resolve_at(T) answers "what was the status at T?"
  - resolve_current() == resolve_at(now)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .status import TrustStatus
from .assertion import TrustStatusAssertion


# Stage 3D, DEFECT-043: explicit domain invariant reason code.
GOVERNED_INITIAL_STATE = "GOVERNED_INITIAL_STATE"


class ResolutionOutcome(str, Enum):
    RESOLVED = "resolved"
    UNKNOWN = "unknown"       # no applicable assertion
    CONFLICT = "conflict"     # contradictory authoritative assertions


@dataclass(frozen=True)
class ResolvedStatus:
    outcome: ResolutionOutcome
    status: TrustStatus | None
    at: datetime
    subject_id: str
    source_assertion_id: str | None = None
    reason: str = ""

    @property
    def is_resolved(self) -> bool:
        return self.outcome is ResolutionOutcome.RESOLVED

    @property
    def is_fail_closed(self) -> bool:
        return self.outcome in (ResolutionOutcome.UNKNOWN, ResolutionOutcome.CONFLICT)


def _ensure_aware(v: datetime) -> datetime:
    if v.tzinfo is None or v.utcoffset() is None:
        raise ValueError("query time must be tz-aware")
    return v.astimezone(timezone.utc)


class TrustStatusResolver:
    """Deterministic resolver. Stateless; caller supplies assertions."""

    def resolve_at(
        self,
        subject_id: str,
        query_time: datetime,
        assertions: list[TrustStatusAssertion],
        *,
        known_authority_ids: frozenset[str] | None = None,
    ) -> ResolvedStatus:
        qt = _ensure_aware(query_time)

        # Defensive (DEFECT-043): any non-assertion object in history is
        # treated as malformed -> fail closed.
        for a in assertions:
            if not isinstance(a, TrustStatusAssertion):
                return ResolvedStatus(
                    outcome=ResolutionOutcome.UNKNOWN,
                    status=None,
                    at=qt,
                    subject_id=subject_id,
                    reason="malformed_assertion_input",
                )

        relevant = [
            a for a in assertions
            if a.subject_id == subject_id and a.effective_at <= qt
        ]
        if not relevant:
            # DEFECT-043 governed initial state:
            # A KNOWN authority with no applicable assertion is ACTIVE.
            # This is an explicit domain invariant, NOT a fallback.
            # An UNKNOWN authority still fails closed.
            if (
                known_authority_ids is not None
                and subject_id in known_authority_ids
            ):
                return ResolvedStatus(
                    outcome=ResolutionOutcome.RESOLVED,
                    status=TrustStatus.ACTIVE,
                    at=qt,
                    subject_id=subject_id,
                    source_assertion_id=None,
                    reason=GOVERNED_INITIAL_STATE,
                )
            return ResolvedStatus(
                outcome=ResolutionOutcome.UNKNOWN,
                status=None,
                at=qt,
                subject_id=subject_id,
                reason="no_assertion_effective_at_or_before_query_time",
            )
        relevant.sort(key=lambda a: (a.effective_at, a.observed_at, a.assertion_id))
        last = relevant[-1]
        # Check for conflicting assertions at the same (effective_at, observed_at)
        peers = [
            a for a in relevant
            if a.effective_at == last.effective_at and a.observed_at == last.observed_at
        ]
        kinds = {a.kind for a in peers}
        if len(kinds) > 1:
            return ResolvedStatus(
                outcome=ResolutionOutcome.CONFLICT,
                status=None,
                at=qt,
                subject_id=subject_id,
                reason=(
                    f"conflicting assertions at effective_at="
                    f"{last.effective_at.isoformat()} observed_at="
                    f"{last.observed_at.isoformat()}: "
                    f"{sorted(k.value for k in kinds)}"
                ),
            )
        return ResolvedStatus(
            outcome=ResolutionOutcome.RESOLVED,
            status=last.asserted_status,
            at=qt,
            subject_id=subject_id,
            source_assertion_id=last.assertion_id,
            reason=f"resolved via assertion {last.assertion_id}",
        )

    def resolve_current(
        self,
        subject_id: str,
        assertions: list[TrustStatusAssertion],
        *,
        now: datetime | None = None,
        known_authority_ids: frozenset[str] | None = None,
    ) -> ResolvedStatus:
        n = now if now is not None else datetime.now(timezone.utc)
        return self.resolve_at(
            subject_id, n, assertions,
            known_authority_ids=known_authority_ids,
        )


__all__ = [
    "GOVERNED_INITIAL_STATE",
    "ResolutionOutcome",
    "ResolvedStatus",
    "TrustStatusResolver",
]
