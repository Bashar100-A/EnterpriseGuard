"""Append-only trust-status assertion history (Stage 3C).

The store is append-only. Current status is NEVER stored; it is
derived via the resolver. Persistence mirrors monitoring/audit.py
(hash chain, JSONL) so we do not build a second mutable database.

API:
    store.append(assertion)      -> adds an assertion
    store.assertions_for(subject)-> list of assertions (copy)
    store.all_assertions()       -> list (copy)
    store.verify_integrity()     -> {"valid": bool, ...}

The store does NOT execute security actions, does NOT mutate any
certificate/decision artifact, and does NOT own trust authority.
"""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .assertion import TrustStatusAssertion, TrustStatusAssertionValidationError
from .authority_to_revoke import RevocationAuthority, RevocationKind
from .resolver import TrustStatusResolver, ResolvedStatus


class TrustHistoryError(Exception):
    pass


class TrustHistoryIntegrityError(TrustHistoryError):
    pass


def _assertion_to_dict(a: TrustStatusAssertion) -> dict[str, Any]:
    return {
        "assertion_id": a.assertion_id,
        "subject_id": a.subject_id,
        "kind": a.kind.value,
        "status": a.asserted_status.value,
        "asserted_at": a.asserted_at.isoformat(),
        "effective_at": a.effective_at.isoformat(),
        "observed_at": a.observed_at.isoformat(),
        "authority_ref": a.authority_ref,
        "authority_id": a.authority_id,
        "policy_id": a.policy_id,
        "reason": a.reason,
        "provenance": dict(a.provenance),
    }


def _dict_to_assertion(d: dict[str, Any]) -> TrustStatusAssertion:
    return TrustStatusAssertion(
        assertion_id=d["assertion_id"],
        subject_id=d["subject_id"],
        kind=RevocationKind(d["kind"]),
        asserted_at=datetime.fromisoformat(d["asserted_at"]),
        effective_at=datetime.fromisoformat(d["effective_at"]),
        observed_at=datetime.fromisoformat(d["observed_at"]),
        authority_ref=d["authority_ref"],
        authority_id=d["authority_id"],
        policy_id=d.get("policy_id"),
        reason=d.get("reason", ""),
        provenance=d.get("provenance", {}),
    )


class TrustStatusStore:
    """Append-only trust-status history.

    Persistence is optional (in-memory when log_path is None). When a
    path is provided, each assertion is appended as one JSONL line with
    a hash chain identical in shape to monitoring/audit.py.
    """

    def __init__(self, log_path: str | Path | None = None) -> None:
        self._log_path: Path | None = Path(log_path) if log_path else None
        self._assertions: list[TrustStatusAssertion] = []
        self._lock = threading.RLock()
        self._last_hash: str = ""
        self._resolver = TrustStatusResolver()
        if self._log_path is not None:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            self._recover()

    # ── mutation ──────────────────────────────────────────────

    def append(
        self,
        assertion: TrustStatusAssertion,
        *,
        revocation_authority: RevocationAuthority | None = None,
        authorization_time: datetime | None = None,
    ) -> None:
        """Append an assertion. If a RevocationAuthority is supplied,
        the authority is verified against the assertion's subject/kind
        before the assertion enters the store.
        """
        if revocation_authority is not None:
            revocation_authority.permits(
                assertion.subject_id,
                assertion.kind,
                at=authorization_time,
            )
        with self._lock:
            for existing in self._assertions:
                if existing.assertion_id == assertion.assertion_id:
                    raise TrustHistoryError(
                        f"duplicate assertion_id {assertion.assertion_id!r}"
                    )
            self._assertions.append(assertion)
            if self._log_path is not None:
                self._write_line(assertion)

    # ── queries ───────────────────────────────────────────────

    def assertions_for(self, subject_id: str) -> list[TrustStatusAssertion]:
        with self._lock:
            return [a for a in self._assertions if a.subject_id == subject_id]

    def all_assertions(self) -> list[TrustStatusAssertion]:
        with self._lock:
            return list(self._assertions)

    def resolve_current(self, subject_id: str, *, now: datetime | None = None) -> ResolvedStatus:
        return self._resolver.resolve_current(subject_id, self.assertions_for(subject_id), now=now)

    def resolve_at(self, subject_id: str, query_time: datetime) -> ResolvedStatus:
        return self._resolver.resolve_at(subject_id, query_time, self.assertions_for(subject_id))

    # ── persistence ───────────────────────────────────────────

    def _line_payload(self, assertion: TrustStatusAssertion, previous_hash: str) -> dict[str, Any]:
        return {
            "assertion": _assertion_to_dict(assertion),
            "previous_hash": previous_hash,
        }

    def _hash_of(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _write_line(self, assertion: TrustStatusAssertion) -> None:
        payload = self._line_payload(assertion, self._last_hash)
        event_hash = self._hash_of(payload)
        line = {**payload, "event_hash": event_hash}
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")
        self._last_hash = event_hash

    def _recover(self) -> None:
        if self._log_path is None or not self._log_path.exists():
            self._last_hash = ""
            return
        with self._log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                a = _dict_to_assertion(d["assertion"])
                self._assertions.append(a)
                self._last_hash = d.get("event_hash", "")

    def verify_integrity(self) -> dict[str, Any]:
        if self._log_path is None or not self._log_path.exists():
            return {"valid": True, "assertions_checked": 0, "error": None}
        prev = ""
        n = 0
        try:
            with self._log_path.open("r", encoding="utf-8") as f:
                for ln, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    stored = d.get("event_hash", "")
                    body = {k: v for k, v in d.items() if k != "event_hash"}
                    expected = self._hash_of(body)
                    if stored != expected:
                        return {
                            "valid": False,
                            "assertions_checked": n,
                            "error": f"hash mismatch at line {ln}",
                        }
                    if body.get("previous_hash", "") != prev:
                        return {
                            "valid": False,
                            "assertions_checked": n,
                            "error": f"chain break at line {ln}",
                        }
                    prev = stored
                    n += 1
            return {"valid": True, "assertions_checked": n, "error": None}
        except Exception as e:
            return {"valid": False, "assertions_checked": n, "error": str(e)}


__all__ = [
    "TrustStatusStore",
    "TrustHistoryError",
    "TrustHistoryIntegrityError",
]
