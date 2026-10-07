"""TrustStatusAssertion — append-only status assertion (Stage 3C).

Each assertion records:
    subject_id          — WHAT is being asserted about
    status              — the new status
    kind                — SUSPEND/REVOKE/SUPERSEDE/EXPIRE
    asserted_at         — when the assertion was created
    effective_at        — when it takes effect (may be past)
    observed_at         — when this assertion entered the system
    authority_ref       — WHO asserted it (RevocationAuthority)
    policy_id           — optional policy reference
    reason              — free-text reason
    provenance          — free-form metadata

Historical integrity: assertions are immutable facts. Current status
is derived from the assertion history, never stored as mutable state.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .status import TrustStatus
from .authority_to_revoke import RevocationKind


class TrustStatusAssertionError(Exception):
    pass


class TrustStatusAssertionValidationError(TrustStatusAssertionError):
    pass


_KIND_TO_STATUS = {
    RevocationKind.SUSPEND: TrustStatus.SUSPENDED,
    RevocationKind.REVOKE: TrustStatus.REVOKED,
    RevocationKind.SUPERSEDE: TrustStatus.SUPERSEDED,
    RevocationKind.EXPIRE: TrustStatus.EXPIRED,
}


def _ensure_aware(v: datetime, name: str) -> datetime:
    if not isinstance(v, datetime):
        raise TrustStatusAssertionValidationError(f"{name} must be datetime")
    if v.tzinfo is None or v.utcoffset() is None:
        raise TrustStatusAssertionValidationError(f"{name} must be tz-aware")
    return v.astimezone(timezone.utc)


@dataclass(frozen=True)
class TrustStatusAssertion:
    assertion_id: str
    subject_id: str
    kind: RevocationKind
    asserted_at: datetime
    effective_at: datetime
    observed_at: datetime
    authority_ref: str
    authority_id: str
    policy_id: str | None = None
    reason: str = ""
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("assertion_id", "subject_id", "authority_ref", "authority_id"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise TrustStatusAssertionValidationError(f"{name} must be non-empty string")
        if not isinstance(self.kind, RevocationKind):
            raise TrustStatusAssertionValidationError("kind must be RevocationKind")
        for name in ("asserted_at", "effective_at", "observed_at"):
            object.__setattr__(self, name, _ensure_aware(getattr(self, name), name))
        if not isinstance(self.reason, str):
            raise TrustStatusAssertionValidationError("reason must be string")
        object.__setattr__(
            self,
            "provenance",
            MappingProxyType(dict(self.provenance)),
        )

    @property
    def asserted_status(self) -> TrustStatus:
        return _KIND_TO_STATUS[self.kind]

    def fingerprint(self) -> str:
        payload = {
            "assertion_id": self.assertion_id,
            "subject_id": self.subject_id,
            "kind": self.kind.value,
            "status": self.asserted_status.value,
            "asserted_at": self.asserted_at.isoformat(),
            "effective_at": self.effective_at.isoformat(),
            "observed_at": self.observed_at.isoformat(),
            "authority_ref": self.authority_ref,
            "authority_id": self.authority_id,
            "policy_id": self.policy_id,
            "reason": self.reason,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


__all__ = [
    "TrustStatusAssertion",
    "TrustStatusAssertionError",
    "TrustStatusAssertionValidationError",
]
