"""Explicit Authority model (Stage 3B).

Invariant: Evidence != Authority.

An Authority object cannot be synthesized merely because evidence
exists. It requires explicit construction by a governance actor.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class AuthorityKind(str, Enum):
    MACHINE = "machine"
    HUMAN = "human"
    DUAL = "dual"


class AuthorityError(Exception):
    pass


class AuthorityValidationError(AuthorityError):
    pass


class AuthorityScopeMismatchError(AuthorityError):
    pass


@dataclass(frozen=True)
class Authority:
    """Explicit governance authority.

    Not derivable from evidence. Must be constructed by a governance
    actor with an explicit policy reference.
    """

    authority_id: str
    authority_kind: AuthorityKind
    policy_id: str
    policy_version: str
    scope: str
    valid_from: datetime
    valid_until: datetime
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("authority_id", "policy_id", "policy_version", "scope"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise AuthorityValidationError(f"{name} must be non-empty string")
        if not isinstance(self.authority_kind, AuthorityKind):
            raise AuthorityValidationError("authority_kind must be AuthorityKind")
        for name in ("valid_from", "valid_until"):
            v = getattr(self, name)
            if not isinstance(v, datetime):
                raise AuthorityValidationError(f"{name} must be datetime")
            if v.tzinfo is None or v.utcoffset() is None:
                raise AuthorityValidationError(f"{name} must be tz-aware")
        if self.valid_until <= self.valid_from:
            raise AuthorityValidationError("valid_until must be after valid_from")
        object.__setattr__(
            self,
            "provenance",
            MappingProxyType(dict(self.provenance)),
        )

    def is_active(self, at: datetime | None = None) -> bool:
        now = at if at is not None else datetime.now(timezone.utc)
        return self.valid_from <= now < self.valid_until

    def requires_scope(self, requested: str) -> None:
        if self.scope != requested:
            raise AuthorityScopeMismatchError(
                f"authority scope {self.scope!r} != requested {requested!r}"
            )

    def fingerprint(self) -> str:
        payload = {
            "authority_id": self.authority_id,
            "authority_kind": self.authority_kind.value,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "scope": self.scope,
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat(),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


__all__ = [
    "Authority",
    "AuthorityKind",
    "AuthorityError",
    "AuthorityValidationError",
    "AuthorityScopeMismatchError",
]
