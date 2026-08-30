"""
ADIE - State Foundation
=======================

Immutable, auditable representation of the current enterprise state.

Architectural role
------------------
ADIE State is the descriptive foundation of the ADIE Control Plane.

It represents observable reality at a specific point in time.

State does NOT:
- execute security actions
- make response decisions
- perform remediation
- perform rollback
- train models
- mutate external systems

Those responsibilities belong to higher ADIE layers.

Design goals
------------
- Strong immutability
- Explicit state identity
- Monotonic revision support
- Schema versioning
- UTC timestamps
- Structured system/security/model state
- Provenance tracking
- Safe serialization
- Deterministic validation
- Future compatibility with checkpoints/history/rewind
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional
from uuid import UUID, uuid4


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ADIE_STATE_SCHEMA_VERSION = "1.0"

VALID_STATUSES = frozenset(
    {
        "unknown",
        "healthy",
        "degraded",
        "at_risk",
        "critical",
    }
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ADIEStateError(ValueError):
    """Base exception for invalid ADIE state data."""


class ADIEStateValidationError(ADIEStateError):
    """Raised when ADIE state validation fails."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _normalize_timestamp(value: datetime) -> datetime:
    """
    Validate and normalize a timestamp.

    Naive timestamps are rejected deliberately because ADIE state
    must have an unambiguous temporal meaning.
    """
    if not isinstance(value, datetime):
        raise ADIEStateValidationError(
            "timestamp must be a datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise ADIEStateValidationError(
            "timestamp must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _validate_probability(
    value: float,
    field_name: str,
) -> float:
    """Validate a normalized value in the inclusive range [0.0, 1.0]."""
    if isinstance(value, bool):
        raise ADIEStateValidationError(
            f"{field_name} must be numeric, not boolean."
        )

    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ADIEStateValidationError(
            f"{field_name} must be numeric."
        ) from exc

    if not 0.0 <= normalized <= 1.0:
        raise ADIEStateValidationError(
            f"{field_name} must be between 0.0 and 1.0."
        )

    return normalized


def _validate_non_negative_int(
    value: int,
    field_name: str,
) -> int:
    """Validate a non-negative integer."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ADIEStateValidationError(
            f"{field_name} must be an integer."
        )

    if value < 0:
        raise ADIEStateValidationError(
            f"{field_name} cannot be negative."
        )

    return value


def _validate_optional_string(
    value: Optional[str],
    field_name: str,
) -> Optional[str]:
    """Validate an optional non-empty string."""
    if value is None:
        return None

    if not isinstance(value, str):
        raise ADIEStateValidationError(
            f"{field_name} must be a string or None."
        )

    if not value.strip():
        raise ADIEStateValidationError(
            f"{field_name} cannot be empty."
        )

    return value.strip()


def _freeze_value(value: Any) -> Any:
    """
    Recursively convert common mutable containers into immutable forms.

    Mapping  -> MappingProxyType
    list     -> tuple
    tuple    -> tuple with recursively frozen values
    set      -> frozenset
    scalar   -> unchanged

    This prevents callers from mutating nested metadata after
    an ADIEState has been created.
    """
    if isinstance(value, Mapping):
        frozen = {
            str(key): _freeze_value(item)
            for key, item in value.items()
        }
        return MappingProxyType(frozen)

    if isinstance(value, list):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, tuple):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, set):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, frozenset):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    return value


def _thaw_value(value: Any) -> Any:
    """
    Convert immutable internal values into ordinary Python
    structures suitable for serialization.
    """
    if isinstance(value, Mapping):
        return {
            key: _thaw_value(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [
            _thaw_value(item)
            for item in value
        ]

    if isinstance(value, (set, frozenset)):
        return [
            _thaw_value(item)
            for item in value
        ]

    return value


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StateIdentity:
    """
    Stable identity information for an ADIE state snapshot.

    state_id:
        Globally unique identifier for this snapshot.

    revision:
        Monotonic logical revision supplied by the state producer.

    schema_version:
        Version of the serialized state contract.
    """

    state_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    revision: int = 0

    schema_version: str = ADIE_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        try:
            UUID(self.state_id)
        except (ValueError, AttributeError, TypeError) as exc:
            raise ADIEStateValidationError(
                "state_id must be a valid UUID string."
            ) from exc

        if isinstance(self.revision, bool) or not isinstance(
            self.revision,
            int,
        ):
            raise ADIEStateValidationError(
                "revision must be an integer."
            )

        if self.revision < 0:
            raise ADIEStateValidationError(
                "revision cannot be negative."
            )

        if not isinstance(self.schema_version, str):
            raise ADIEStateValidationError(
                "schema_version must be a string."
            )

        if not self.schema_version.strip():
            raise ADIEStateValidationError(
                "schema_version cannot be empty."
            )


# ---------------------------------------------------------------------------
# System State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SystemState:
    """Observable health and operational status of the enterprise."""

    status: str = "unknown"

    health: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.status, str):
            raise ADIEStateValidationError(
                "system status must be a string."
            )

        normalized_status = self.status.strip().lower()

        if normalized_status not in VALID_STATUSES:
            raise ADIEStateValidationError(
                "Invalid system status: "
                f"{self.status!r}. "
                f"Expected one of: {sorted(VALID_STATUSES)}."
            )

        object.__setattr__(
            self,
            "status",
            normalized_status,
        )

        object.__setattr__(
            self,
            "health",
            _validate_probability(
                self.health,
                "health",
            ),
        )


# ---------------------------------------------------------------------------
# Security State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SecurityState:
    """
    Observable security posture.

    Important:
        risk is a normalized risk score.
        It is NOT automatically equivalent to ML probability,
        threat probability, or model confidence.
    """

    risk: float = 0.0

    active_threats: int = 0

    alerts: int = 0

    escalations: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "risk",
            _validate_probability(
                self.risk,
                "risk",
            ),
        )

        object.__setattr__(
            self,
            "active_threats",
            _validate_non_negative_int(
                self.active_threats,
                "active_threats",
            ),
        )

        object.__setattr__(
            self,
            "alerts",
            _validate_non_negative_int(
                self.alerts,
                "alerts",
            ),
        )

        object.__setattr__(
            self,
            "escalations",
            _validate_non_negative_int(
                self.escalations,
                "escalations",
            ),
        )


# ---------------------------------------------------------------------------
# Model State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelState:
    """Observable state of the model currently associated with ADIE."""

    active_model: Optional[str] = None

    model_version: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "active_model",
            _validate_optional_string(
                self.active_model,
                "active_model",
            ),
        )

        object.__setattr__(
            self,
            "model_version",
            _validate_optional_string(
                self.model_version,
                "model_version",
            ),
        )


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StateProvenance:
    """
    Describes where the state came from.

    Provenance is descriptive only.
    It does not execute or authorize anything.
    """

    source: str = "adie"

    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.source, str):
            raise ADIEStateValidationError(
                "provenance source must be a string."
            )

        if not self.source.strip():
            raise ADIEStateValidationError(
                "provenance source cannot be empty."
            )

        object.__setattr__(
            self,
            "source",
            self.source.strip(),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_value(self.metadata),
        )


# ---------------------------------------------------------------------------
# ADIE State
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ADIEState:
    """
    Immutable snapshot of the observable enterprise state.

    Every instance represents a distinct state snapshot.

    A new state should be created from an existing state rather
    than mutating the existing object.
    """

    identity: StateIdentity = field(
        default_factory=StateIdentity
    )

    timestamp: datetime = field(
        default_factory=_utc_now
    )

    system: SystemState = field(
        default_factory=SystemState
    )

    security: SecurityState = field(
        default_factory=SecurityState
    )

    model: ModelState = field(
        default_factory=ModelState
    )

    provenance: StateProvenance = field(
        default_factory=StateProvenance
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.identity,
            StateIdentity,
        ):
            raise ADIEStateValidationError(
                "identity must be a StateIdentity."
            )

        object.__setattr__(
            self,
            "timestamp",
            _normalize_timestamp(self.timestamp),
        )

        if not isinstance(
            self.system,
            SystemState,
        ):
            raise ADIEStateValidationError(
                "system must be a SystemState."
            )

        if not isinstance(
            self.security,
            SecurityState,
        ):
            raise ADIEStateValidationError(
                "security must be a SecurityState."
            )

        if not isinstance(
            self.model,
            ModelState,
        ):
            raise ADIEStateValidationError(
                "model must be a ModelState."
            )

        if not isinstance(
            self.provenance,
            StateProvenance,
        ):
            raise ADIEStateValidationError(
                "provenance must be a StateProvenance."
            )

    # ------------------------------------------------------------------
    # Compatibility / convenience properties
    # ------------------------------------------------------------------

    @property
    def state_id(self) -> str:
        """Return the unique state identifier."""
        return self.identity.state_id

    @property
    def revision(self) -> int:
        """Return the logical state revision."""
        return self.identity.revision

    @property
    def schema_version(self) -> str:
        """Return the state schema version."""
        return self.identity.schema_version

    @property
    def status(self) -> str:
        """Return current system status."""
        return self.system.status

    @property
    def health(self) -> float:
        """Return normalized system health."""
        return self.system.health

    @property
    def risk(self) -> float:
        """Return normalized security risk."""
        return self.security.risk

    @property
    def active_threats(self) -> int:
        """Return the number of active threats."""
        return self.security.active_threats

    @property
    def alerts(self) -> int:
        """Return the number of active alerts."""
        return self.security.alerts

    @property
    def escalations(self) -> int:
        """Return the number of escalations."""
        return self.security.escalations

    @property
    def active_model(self) -> Optional[str]:
        """Return the active model identifier."""
        return self.model.active_model

    @property
    def model_version(self) -> Optional[str]:
        """Return the active model version."""
        return self.model.model_version

    @property
    def source(self) -> str:
        """Return the state provenance source."""
        return self.provenance.source

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Return a fully detached, serialization-friendly dictionary.

        The returned object can be mutated by the caller without
        affecting the ADIEState instance.
        """
        return {
            "identity": {
                "state_id": self.identity.state_id,
                "revision": self.identity.revision,
                "schema_version": self.identity.schema_version,
            },
            "timestamp": self.timestamp.isoformat(),
            "system": {
                "status": self.system.status,
                "health": self.system.health,
            },
            "security": {
                "risk": self.security.risk,
                "active_threats": self.security.active_threats,
                "alerts": self.security.alerts,
                "escalations": self.security.escalations,
            },
            "model": {
                "active_model": self.model.active_model,
                "model_version": self.model.model_version,
            },
            "provenance": {
                "source": self.provenance.source,
                "metadata": _thaw_value(
                    self.provenance.metadata
                ),
            },
        }

    def to_json_dict(self) -> dict[str, Any]:
        """Explicit serialization alias."""
        return self.to_dict()

    # ------------------------------------------------------------------
    # State evolution
    # ------------------------------------------------------------------

    def with_updates(
        self,
        *,
        revision: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        system: Optional[SystemState] = None,
        security: Optional[SecurityState] = None,
        model: Optional[ModelState] = None,
        provenance: Optional[StateProvenance] = None,
    ) -> "ADIEState":
        """
        Create a new state snapshot.

        The current state is NEVER mutated.

        By default:
        - a new UUID is generated
        - revision is incremented
        - timestamp is refreshed
        """
        next_revision = (
            self.revision + 1
            if revision is None
            else revision
        )

        if next_revision <= self.revision:
            raise ADIEStateValidationError(
                "New state revision must be greater than "
                "the current revision."
            )

        next_identity = StateIdentity(
            state_id=str(uuid4()),
            revision=next_revision,
            schema_version=self.schema_version,
        )

        return ADIEState(
            identity=next_identity,
            timestamp=(
                _utc_now()
                if timestamp is None
                else timestamp
            ),
            system=(
                self.system
                if system is None
                else system
            ),
            security=(
                self.security
                if security is None
                else security
            ),
            model=(
                self.model
                if model is None
                else model
            ),
            provenance=(
                self.provenance
                if provenance is None
                else provenance
            ),
        )

    # ------------------------------------------------------------------
    # Operational helpers
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        """
        Return whether the state currently represents
        a healthy low-risk posture.
        """
        return (
            self.system.health >= 0.70
            and self.security.risk < 0.30
            and self.system.status == "healthy"
        )

    def is_high_risk(self) -> bool:
        """Return whether the current normalized risk is high."""
        return self.security.risk >= 0.70

    def has_active_threats(self) -> bool:
        """Return whether active threats are currently observed."""
        return self.security.active_threats > 0

    def summary(self) -> dict[str, Any]:
        """Return a compact operational representation."""
        return {
            "state_id": self.state_id,
            "revision": self.revision,
            "schema_version": self.schema_version,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "status": self.status,
            "health": self.health,
            "risk": self.risk,
            "active_threats": self.active_threats,
            "alerts": self.alerts,
            "escalations": self.escalations,
            "active_model": self.active_model,
            "model_version": self.model_version,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_initial_state(
    *,
    source: str = "adie",
    status: str = "unknown",
    revision: int = 0,
) -> ADIEState:
    """
    Create the initial ADIE state.

    The initial state represents the point at which ADIE has
    established its first observable baseline.
    """
    return ADIEState(
        identity=StateIdentity(
            revision=revision,
        ),
        timestamp=_utc_now(),
        system=SystemState(
            status=status,
            health=1.0,
        ),
        security=SecurityState(
            risk=0.0,
            active_threats=0,
            alerts=0,
            escalations=0,
        ),
        model=ModelState(),
        provenance=StateProvenance(
            source=source,
        ),
    )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


def self_test() -> bool:
    """Run internal validation tests for the ADIE State Foundation."""

    # 1. Initial state
    state = create_initial_state(
        source="self_test",
        status="unknown",
    )

    assert state.state_id
    assert state.revision == 0
    assert state.schema_version == ADIE_STATE_SCHEMA_VERSION
    assert state.timestamp.tzinfo is not None
    assert state.timestamp.utcoffset() is not None

    assert state.source == "self_test"
    assert state.status == "unknown"
    assert state.health == 1.0
    assert state.risk == 0.0

    # 2. Nested state structure
    assert isinstance(
        state.system,
        SystemState,
    )

    assert isinstance(
        state.security,
        SecurityState,
    )

    assert isinstance(
        state.model,
        ModelState,
    )

    assert isinstance(
        state.provenance,
        StateProvenance,
    )

    # 3. Serialization
    serialized = state.to_dict()

    assert isinstance(serialized, dict)
    assert serialized["identity"]["state_id"] == state.state_id
    assert serialized["identity"]["revision"] == 0
    assert isinstance(
        serialized["timestamp"],
        str,
    )

    # 4. Immutable state evolution
    next_state = state.with_updates(
        system=SystemState(
            status="at_risk",
            health=0.60,
        ),
        security=SecurityState(
            risk=0.80,
            active_threats=2,
            alerts=1,
            escalations=0,
        ),
    )

    assert next_state.state_id != state.state_id
    assert next_state.revision == 1

    assert state.risk == 0.0
    assert state.active_threats == 0

    assert next_state.risk == 0.80
    assert next_state.active_threats == 2
    assert next_state.alerts == 1

    # 5. High-risk detection
    assert not state.is_high_risk()
    assert next_state.is_high_risk()
    assert next_state.has_active_threats()

    # 6. Deep immutability test
    metadata = {
        "environment": {
            "region": "test",
            "tags": ["a", "b"],
        }
    }

    metadata_state = ADIEState(
        provenance=StateProvenance(
            source="self_test",
            metadata=metadata,
        )
    )

    metadata["environment"]["tags"].append("MUTATION")

    stored_metadata = metadata_state.provenance.metadata

    assert (
        "MUTATION"
        not in stored_metadata["environment"]["tags"]
    )

    # 7. Serialization isolation
    exported = metadata_state.to_dict()

    exported["provenance"]["metadata"]["environment"][
        "tags"
    ].append("EXTERNAL_MUTATION")

    assert (
        "EXTERNAL_MUTATION"
        not in metadata_state.provenance.metadata[
            "environment"
        ]["tags"]
    )

    # 8. Validation checks
    try:
        SecurityState(risk=1.5)
        raise AssertionError(
            "Invalid risk should have been rejected."
        )
    except ADIEStateValidationError:
        pass

    try:
        SystemState(status="invalid_status")
        raise AssertionError(
            "Invalid status should have been rejected."
        )
    except ADIEStateValidationError:
        pass

    try:
        SecurityState(active_threats=-1)
        raise AssertionError(
            "Negative threat count should have been rejected."
        )
    except ADIEStateValidationError:
        pass

    try:
        StateIdentity(revision=-1)
        raise AssertionError(
            "Negative revision should have been rejected."
        )
    except ADIEStateValidationError:
        pass

    # 9. Revision monotonicity
    try:
        state.with_updates(revision=0)
        raise AssertionError(
            "Non-increasing revision should have been rejected."
        )
    except ADIEStateValidationError:
        pass

    print("ADIE State Foundation self-test: PASS")

    return True


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    self_test()