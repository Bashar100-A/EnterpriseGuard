"""ADIE vΩ — Registry subsystem (Phase 1.9).

Implements spec/REGISTRY-0.1.md:
- Namespace:local_id identity (E-META-23)
- Entry lifecycle: PROPOSED → ACTIVE → DEPRECATED → REVOKED (E-META-16c/E-META-24)
- Effective/expiry windows (E-META-25)
- Compatibility relations with scope and expiry (E-META-26/E-META-27)
- No transitive inference (E-META-17)
- Intra-snapshot fork (E-META-13) and inter-snapshot fork detection
- Snapshot replay detection (E-META-28)
"""
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from protocol.core.domain_hash import H_A
from protocol.core.jcs import canonical_bytes


# ─── constants ─────────────────────────────────────────────────────
NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
LOCAL_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,128}$")
ID_RE = re.compile(r"^([a-z][a-z0-9_]{0,31}):([A-Za-z0-9_.\-]{1,128})$")

ALLOWED_ENTRY_TYPES = frozenset({"template", "rewrite_rule"})
ALLOWED_STATUSES = frozenset({"PROPOSED", "ACTIVE", "DEPRECATED", "REVOKED"})
ALLOWED_RELATIONS = frozenset({"EXACT", "ENCODING", "SEMANTIC", "INCOMPATIBLE"})

VALID_TRANSITIONS = frozenset({
    ("PROPOSED", "ACTIVE"),
    ("ACTIVE", "DEPRECATED"),
    ("DEPRECATED", "REVOKED"),
    ("ACTIVE", "REVOKED"),
})


class RegistryError(Exception):
    def __init__(self, code, msg=""):
        self.code = code
        super().__init__(f"{code}: {msg}")


# ─── helpers ───────────────────────────────────────────────────────
def parse_id(id_str):
    if not isinstance(id_str, str):
        raise RegistryError("E-META-23",
            f"id must be str, got {type(id_str).__name__}")
    m = ID_RE.match(id_str)
    if not m:
        raise RegistryError("E-META-23", f"malformed id {id_str!r}")
    return m.group(1), m.group(2)


def _validate_ts(ts, field_name):
    if ts is None:
        return
    if not isinstance(ts, str) or not ts.endswith("Z"):
        raise RegistryError("E-META-16a",
            f"{field_name} must be RFC3339 UTC Z, got {ts!r}")
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception as e:
        raise RegistryError("E-META-16a", f"{field_name} unparseable: {e}")


def _now_z():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _cmp_time(ts, now):
    """Return -1 if ts < now, 0 if ==, 1 if >."""
    t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    n = datetime.fromisoformat(now.replace("Z", "+00:00"))
    return (t > n) - (t < n)


# ─── Entry ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Entry:
    type: str
    id: str
    version: str
    payload: dict
    status: str
    effective: str | None
    expiry: str | None
    issuer: str

    def __post_init__(self):
        if self.type not in ALLOWED_ENTRY_TYPES:
            raise RegistryError("E-META-16a",
                f"unknown entry type {self.type!r}")
        parse_id(self.id)
        if not isinstance(self.version, str) or not self.version:
            raise RegistryError("E-META-16a", "version must be non-empty str")
        if not isinstance(self.payload, dict):
            raise RegistryError("E-META-16a", "payload must be dict")
        if self.status not in ALLOWED_STATUSES:
            raise RegistryError("E-META-24",
                f"invalid status {self.status!r}")
        _validate_ts(self.effective, "effective")
        _validate_ts(self.expiry, "expiry")
        if not isinstance(self.issuer, str) or not self.issuer:
            raise RegistryError("E-META-16a", "issuer must be non-empty str")
        object.__setattr__(self, "_digest", self._compute_digest())

    def _compute_digest(self):
        body = {
            "type": self.type,
            "id": self.id,
            "version": self.version,
            "payload": self.payload,
            "status": self.status,
            "effective": self.effective,
            "expiry": self.expiry,
            "issuer": self.issuer,
        }
        return "sha256:" + H_A(
            "registry-entry", canonical_bytes(body)).hex()

    @property
    def digest(self):
        return self._digest

    @property
    def namespace(self):
        return self.id.split(":", 1)[0]

    @property
    def local_id(self):
        return self.id.split(":", 1)[1]


# ─── CompatibilityRecord ───────────────────────────────────────────
@dataclass(frozen=True)
class CompatibilityRecord:
    from_id: str
    to_id: str
    relation: str
    scope: tuple
    constraints: dict
    proof_digest: str | None
    authority: str
    effective: str
    expiry: str | None
    issuer: str

    def __post_init__(self):
        parse_id(self.from_id)
        parse_id(self.to_id)
        if self.relation not in ALLOWED_RELATIONS:
            raise RegistryError("E-META-17",
                f"unknown relation {self.relation!r}")
        if self.relation == "SEMANTIC" and not self.proof_digest:
            raise RegistryError("E-META-17",
                "SEMANTIC requires proof_digest")
        if not isinstance(self.scope, tuple):
            raise RegistryError("E-META-16a",
                "scope must be tuple")
        for s in self.scope:
            if not isinstance(s, str):
                raise RegistryError("E-META-16a", "scope entries must be str")
        if not isinstance(self.constraints, dict):
            raise RegistryError("E-META-16a", "constraints must be dict")
        if not isinstance(self.effective, str) or not self.effective.endswith("Z"):
            raise RegistryError("E-META-16a",
                "effective must be RFC3339 UTC Z")
        _validate_ts(self.effective, "effective")
        _validate_ts(self.expiry, "expiry")
        if not isinstance(self.authority, str) or not self.authority:
            raise RegistryError("E-META-16a", "authority must be non-empty str")
        if not isinstance(self.issuer, str) or not self.issuer:
            raise RegistryError("E-META-16a", "issuer must be non-empty str")
        object.__setattr__(self, "_digest", self._compute_digest())

    def _compute_digest(self):
        body = {
            "type": "compatibility",
            "from": self.from_id,
            "to": self.to_id,
            "relation": self.relation,
            "scope": list(self.scope),
            "constraints": self.constraints,
            "proof_digest": self.proof_digest,
            "authority": self.authority,
            "effective": self.effective,
            "expiry": self.expiry,
            "issuer": self.issuer,
        }
        return "sha256:" + H_A(
            "registry-compat", canonical_bytes(body)).hex()

    @property
    def digest(self):
        return self._digest


# ─── RegistrySnapshot ──────────────────────────────────────────────
class RegistrySnapshot:
    """Immutable-in-spirit registry state at a specific epoch.

    Every mutation produces a new entry in `_entries`; the snapshot's
    epoch does not change (caller creates a new snapshot for new epochs).
    """

    def __init__(self, snapshot_epoch, universe=None):
        if not isinstance(snapshot_epoch, int) or isinstance(snapshot_epoch, bool):
            raise RegistryError("E-META-16a", "snapshot_epoch must be int")
        self.snapshot_epoch = snapshot_epoch
        self._universe = universe
        self._entries = {}
        self._compat = {}

    # ─── universe check ─────────────────────────────
    def _check_universe(self, namespace):
        if self._universe is None:
            return
        if namespace not in self._universe.registry_namespaces:
            raise RegistryError("E-META-19",
                f"namespace {namespace!r} not in Universe")

    # ─── entry registration ─────────────────────────
    def register(self, entry):
        if not isinstance(entry, Entry):
            raise RegistryError("E-META-16a",
                f"expected Entry, got {type(entry).__name__}")
        self._check_universe(entry.namespace)
        existing = self._entries.get(entry.id)
        if existing is not None:
            if existing.digest == entry.digest:
                return
            raise RegistryError("E-META-13",
                f"fork on id {entry.id!r}: "
                f"{existing.digest[:20]} != {entry.digest[:20]}")
        self._entries[entry.id] = entry

    def deprecate(self, id_str):
        e = self._require(id_str)
        if ("ACTIVE", "DEPRECATED") not in VALID_TRANSITIONS and e.status != "ACTIVE":
            raise RegistryError("E-META-16c",
                f"deprecate requires ACTIVE, got {e.status}")
        new = replace(e, status="DEPRECATED")
        self._entries[id_str] = new
        return new

    def revoke(self, id_str):
        e = self._require(id_str)
        if (e.status, "REVOKED") not in VALID_TRANSITIONS:
            raise RegistryError("E-META-16c",
                f"revoke from {e.status} not permitted")
        new = replace(e, status="REVOKED")
        self._entries[id_str] = new
        return new

    def lookup(self, id_str, now=None, require_status="ACTIVE"):
        e = self._entries.get(id_str)
        if e is None:
            return None
        if now is not None:
            if e.effective is not None and _cmp_time(e.effective, now) > 0:
                raise RegistryError("E-META-25",
                    f"entry {id_str!r} not yet effective")
            if e.expiry is not None and _cmp_time(e.expiry, now) <= 0:
                raise RegistryError("E-META-25",
                    f"entry {id_str!r} expired")
        if require_status is not None and e.status != require_status:
            return None
        return e

    def _require(self, id_str):
        e = self._entries.get(id_str)
        if e is None:
            raise RegistryError("E-META-25", f"unknown id {id_str!r}")
        return e

    # ─── compatibility ──────────────────────────────
    def declare_compat(self, rec):
        if not isinstance(rec, CompatibilityRecord):
            raise RegistryError("E-META-16a",
                f"expected CompatibilityRecord, got {type(rec).__name__}")
        key = (rec.from_id, rec.to_id)
        existing = self._compat.get(key)
        if existing is not None and existing.digest != rec.digest:
            raise RegistryError("E-META-13",
                f"compat fork on ({rec.from_id}, {rec.to_id})")
        self._compat[key] = rec

    def lookup_compat(self, from_id, to_id, scope=None, now=None):
        """Return relation string or None.

        No transitive inference (I17). No version-tuple inference.
        """
        rec = self._compat.get((from_id, to_id))
        if rec is None:
            return None
        if now is not None:
            if _cmp_time(rec.effective, now) > 0:
                raise RegistryError("E-META-26",
                    f"compat not yet effective for ({from_id}, {to_id})")
            if rec.expiry is not None and _cmp_time(rec.expiry, now) <= 0:
                raise RegistryError("E-META-26",
                    f"compat expired for ({from_id}, {to_id})")
        if scope is not None and len(rec.scope) > 0:
            for s in scope:
                if s not in rec.scope:
                    raise RegistryError("E-META-27",
                        f"scope {s!r} not in {rec.scope!r}")
        return rec.relation

    # ─── snapshot-level ─────────────────────────────
    def check_replay(self, known_epoch):
        if not isinstance(known_epoch, int) or isinstance(known_epoch, bool):
            raise RegistryError("E-META-16a", "known_epoch must be int")
        if known_epoch > self.snapshot_epoch:
            raise RegistryError("E-META-28",
                f"snapshot epoch {self.snapshot_epoch} < known {known_epoch}")

    def diff_fork(self, other):
        """Return list of ids whose digest differs between two snapshots."""
        if not isinstance(other, RegistrySnapshot):
            raise RegistryError("E-META-16a", "other must be RegistrySnapshot")
        conflicts = []
        for id_str, e1 in self._entries.items():
            e2 = other._entries.get(id_str)
            if e2 is not None and e2.digest != e1.digest:
                conflicts.append(id_str)
        return conflicts

    def ids(self):
        return sorted(self._entries.keys())

    def compat_keys(self):
        return sorted(self._compat.keys())


__all__ = [
    "RegistrySnapshot",
    "Entry",
    "CompatibilityRecord",
    "RegistryError",
    "parse_id",
]
