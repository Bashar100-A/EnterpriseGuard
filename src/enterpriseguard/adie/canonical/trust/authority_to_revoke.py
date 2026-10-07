"""Revocation Authority (Stage 3C).

A party that can authorize a decision does NOT automatically gain the
ability to revoke every trust subject. Revocation is a distinct
privileged operation with its own scope.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import FrozenSet


class RevocationKind(str, Enum):
    SUSPEND = "suspend"        # reversible
    REVOKE = "revoke"          # terminal
    SUPERSEDE = "supersede"    # terminal, replaced
    EXPIRE = "expire"          # terminal, temporal


class RevocationAuthorityError(Exception):
    pass


class RevocationAuthorityValidationError(RevocationAuthorityError):
    pass


class RevocationNotPermittedError(RevocationAuthorityError):
    pass


@dataclass(frozen=True)
class RevocationAuthority:
    """Explicit capability to assert trust-status changes.

    Constructed by a governance actor. Not derivable from Authority
    (3B). A 3B Authority with scope=decide cannot revoke; a separate
    RevocationAuthority with explicit revocable_subject_ids or
    revocable_subject_pattern is required.
    """

    revocation_authority_id: str
    revocation_authority_ref: str          # e.g. "authority:gov-root-1"
    permitted_kinds: FrozenSet[RevocationKind]
    revocable_subject_ids: FrozenSet[str]  # explicit allow-list
    valid_from: datetime
    valid_until: datetime

    def __post_init__(self) -> None:
        if not self.revocation_authority_id or not isinstance(self.revocation_authority_id, str):
            raise RevocationAuthorityValidationError("revocation_authority_id must be non-empty string")
        if not self.revocation_authority_ref or not isinstance(self.revocation_authority_ref, str):
            raise RevocationAuthorityValidationError("revocation_authority_ref must be non-empty string")
        if not isinstance(self.permitted_kinds, frozenset) or not self.permitted_kinds:
            raise RevocationAuthorityValidationError("permitted_kinds must be non-empty frozenset")
        for k in self.permitted_kinds:
            if not isinstance(k, RevocationKind):
                raise RevocationAuthorityValidationError("permitted_kinds must contain RevocationKind")
        if not isinstance(self.revocable_subject_ids, frozenset):
            raise RevocationAuthorityValidationError("revocable_subject_ids must be frozenset")
        for name in ("valid_from", "valid_until"):
            v = getattr(self, name)
            if not isinstance(v, datetime):
                raise RevocationAuthorityValidationError(f"{name} must be datetime")
            if v.tzinfo is None or v.utcoffset() is None:
                raise RevocationAuthorityValidationError(f"{name} must be tz-aware")
        if self.valid_until <= self.valid_from:
            raise RevocationAuthorityValidationError("valid_until must be after valid_from")

    def is_active(self, at: datetime | None = None) -> bool:
        now = at if at is not None else datetime.now(timezone.utc)
        return self.valid_from <= now < self.valid_until

    def permits(self, subject_id: str, kind: RevocationKind, at: datetime | None = None) -> None:
        """Raise RevocationNotPermittedError if not permitted."""
        if not self.is_active(at):
            raise RevocationNotPermittedError("revocation authority is not active")
        if kind not in self.permitted_kinds:
            raise RevocationNotPermittedError(f"kind {kind.value!r} not permitted")
        if subject_id not in self.revocable_subject_ids:
            raise RevocationNotPermittedError(
                f"subject {subject_id!r} not in revocable_subject_ids"
            )


__all__ = [
    "RevocationKind",
    "RevocationAuthority",
    "RevocationAuthorityError",
    "RevocationAuthorityValidationError",
    "RevocationNotPermittedError",
]
