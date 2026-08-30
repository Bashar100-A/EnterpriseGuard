"""
EnterpriseGuard - Enterprise State Model
========================================

Adaptive Defense Intelligence Engine (ADIE)

Purpose
-------

Defines the canonical representation of the current enterprise
security state.

The State layer is the temporal foundation of ADIE.

Architecture
------------

    Signals / Intelligence
             |
             v
       EnterpriseState
             |
             +---------> Prediction
             |
             +---------> Policy
             |
             +---------> Checkpoint
             |
             +---------> Decision

Design principles
-----------------

This module is intentionally:

- framework independent
- deterministic
- serializable
- validation-oriented
- immutable-by-construction
- safe for downstream intelligence layers

This module MUST NOT:

- perform threat detection
- execute ML models
- make security decisions
- execute playbooks
- modify external systems
- access filesystem
- perform network operations
- import Streamlit
- import DashboardAPI
- depend on UI components

The State layer describes reality.

It does not decide what to do about that reality.


State model
-----------

EnterpriseState
    |
    +-- Identity
    |     +-- state_id
    |     +-- version
    |     +-- timestamp
    |
    +-- Security posture
    |     +-- risk_score
    |     +-- threat_level
    |     +-- posture
    |
    +-- Signals
    |     +-- active_signals
    |     +-- signal_count
    |
    +-- Operational context
    |     +-- active_assets
    |     +-- active_identities
    |     +-- active_sessions
    |
    +-- Provenance
          +-- source
          +-- correlation_id
          +-- metadata


Important distinction
---------------------

A State is not an alert.

A State is not a prediction.

A State is not a decision.

A State answers:

    "What do we currently know about the enterprise?"

Prediction will later answer:

    "What is likely to happen next?"

Policy will later answer:

    "What should be allowed or recommended?"

Decision will later answer:

    "What defensive decision should be produced?"

Version
-------

1.0.0
"""


from __future__ import annotations


# ============================================================================
# Standard library
# ============================================================================

from dataclasses import (
    dataclass,
    field,
    replace,
)
from datetime import (
    datetime,
    timezone,
)
from enum import Enum
from math import (
    isfinite,
)
from types import (
    MappingProxyType,
)
from typing import (
    Any,
    Mapping,
    Sequence,
)


# ============================================================================
# Constants
# ============================================================================

STATE_SCHEMA_VERSION = "1.0.0"

DEFAULT_STATE_SOURCE = "enterpriseguard"

MAX_SIGNAL_COUNT = 10_000

MAX_METADATA_ITEMS = 1_000


# ============================================================================
# Enumerations
# ============================================================================


class ThreatLevel(str, Enum):
    """
    Normalized enterprise threat level.

    The enum represents state classification only.

    It does not represent a response decision.
    """

    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityPosture(str, Enum):
    """
    Current normalized security posture.
    """

    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    GUARDED = "GUARDED"
    ELEVATED = "ELEVATED"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


# ============================================================================
# Utility functions
# ============================================================================


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC timestamp.
    """

    return datetime.now(timezone.utc)


def normalize_timestamp(
    value: datetime,
) -> datetime:
    """
    Normalize a datetime to timezone-aware UTC.

    Naive timestamps are rejected because temporal state is a
    foundational ADIE concept and silently assuming a timezone
    would make state comparisons unreliable.
    """

    if not isinstance(value, datetime):
        raise TypeError(
            "timestamp must be a datetime"
        )

    if value.tzinfo is None:
        raise ValueError(
            "timestamp must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def normalize_score(
    value: float,
) -> float:
    """
    Validate and normalize a risk score.

    Risk scores are represented on a normalized 0.0 .. 1.0 scale.
    """

    try:
        score = float(value)

    except (TypeError, ValueError) as exc:
        raise TypeError(
            "risk_score must be numeric"
        ) from exc

    if not isfinite(score):
        raise ValueError(
            "risk_score must be finite"
        )

    if not 0.0 <= score <= 1.0:
        raise ValueError(
            "risk_score must be between 0.0 and 1.0"
        )

    return score


def normalize_non_negative_int(
    value: int,
    *,
    field_name: str,
) -> int:
    """
    Validate a non-negative integer.
    """

    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    try:
        number = int(value)

    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"{field_name} must be an integer"
        ) from exc

    if number < 0:
        raise ValueError(
            f"{field_name} must not be negative"
        )

    return number


def normalize_string(
    value: str,
    *,
    field_name: str,
    allow_empty: bool = False,
) -> str:
    """
    Normalize a required string field.
    """

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    result = value.strip()

    if not allow_empty and not result:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    return result


def freeze_mapping(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """
    Create a shallow immutable mapping.

    Nested values are intentionally preserved as supplied. State metadata
    should therefore contain serialization-friendly primitive values.
    """

    if not isinstance(value, Mapping):
        raise TypeError(
            "metadata must be a mapping"
        )

    if len(value) > MAX_METADATA_ITEMS:
        raise ValueError(
            "metadata contains too many items"
        )

    normalized: dict[str, Any] = {}

    for key, item in value.items():

        if not isinstance(key, str):
            raise TypeError(
                "metadata keys must be strings"
            )

        normalized[key] = item

    return MappingProxyType(
        normalized
    )


def normalize_signals(
    signals: Sequence[str],
) -> tuple[str, ...]:
    """
    Normalize active security signals.

    Signals are represented as unique, ordered strings.
    """

    if isinstance(
        signals,
        (str, bytes),
    ):
        raise TypeError(
            "active_signals must be a sequence of strings"
        )

    try:
        values = list(signals)

    except TypeError as exc:
        raise TypeError(
            "active_signals must be iterable"
        ) from exc

    if len(values) > MAX_SIGNAL_COUNT:
        raise ValueError(
            "active_signals contains too many items"
        )

    result: list[str] = []
    seen: set[str] = set()

    for signal in values:

        normalized = normalize_string(
            signal,
            field_name="signal",
        )

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(normalized)

    return tuple(result)


def generate_state_id(
    timestamp: datetime,
    version: int,
) -> str:
    """
    Generate a deterministic human-readable state identifier.

    The identifier is intentionally local to the state object and does
    not require UUID generation or external state.
    """

    normalized_timestamp = normalize_timestamp(
        timestamp
    )

    compact_timestamp = (
        normalized_timestamp
        .strftime("%Y%m%dT%H%M%S%fZ")
    )

    return (
        f"state-{compact_timestamp}-v{version}"
    )


def derive_threat_level(
    risk_score: float,
) -> ThreatLevel:
    """
    Derive a normalized threat level from a normalized risk score.

    This is state classification, not a response policy.

    Mapping
    -------

    0.00 - 0.19 -> LOW
    0.20 - 0.49 -> MEDIUM
    0.50 - 0.79 -> HIGH
    0.80 - 1.00 -> CRITICAL
    """

    score = normalize_score(
        risk_score
    )

    if score < 0.20:
        return ThreatLevel.LOW

    if score < 0.50:
        return ThreatLevel.MEDIUM

    if score < 0.80:
        return ThreatLevel.HIGH

    return ThreatLevel.CRITICAL


def derive_security_posture(
    risk_score: float,
    *,
    signal_count: int,
) -> SecurityPosture:
    """
    Derive a normalized security posture.

    This classification intentionally considers both risk and
    active signal volume.

    It does not determine a defensive action.
    """

    score = normalize_score(
        risk_score
    )

    count = normalize_non_negative_int(
        signal_count,
        field_name="signal_count",
    )

    if score >= 0.80:
        return SecurityPosture.CRITICAL

    if score >= 0.50:
        return SecurityPosture.DEGRADED

    if score >= 0.20:
        return SecurityPosture.ELEVATED

    if count > 0:
        return SecurityPosture.GUARDED

    return SecurityPosture.HEALTHY


# ============================================================================
# Enterprise State
# ============================================================================


@dataclass(frozen=True, slots=True)
class EnterpriseState:
    """
    Canonical immutable representation of enterprise security state.

    The object represents a snapshot at a specific point in time.

    Downstream ADIE components should consume this object instead of
    passing loosely structured dictionaries between intelligence layers.
    """

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------

    state_id: str

    timestamp: datetime

    version: int = 1

    schema_version: str = STATE_SCHEMA_VERSION

    # ------------------------------------------------------------------------
    # Security posture
    # ------------------------------------------------------------------------

    risk_score: float = 0.0

    threat_level: ThreatLevel = ThreatLevel.UNKNOWN

    posture: SecurityPosture = SecurityPosture.UNKNOWN

    # ------------------------------------------------------------------------
    # Security signals
    # ------------------------------------------------------------------------

    active_signals: tuple[str, ...] = field(
        default_factory=tuple
    )

    # ------------------------------------------------------------------------
    # Operational context
    # ------------------------------------------------------------------------

    active_assets: int = 0

    active_identities: int = 0

    active_sessions: int = 0

    # ------------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------------

    source: str = DEFAULT_STATE_SOURCE

    correlation_id: str | None = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # ------------------------------------------------------------------------
    # Initialization validation
    # ------------------------------------------------------------------------

    def __post_init__(self) -> None:
        """
        Validate and normalize state invariants.
        """

        normalized_state_id = normalize_string(
            self.state_id,
            field_name="state_id",
        )

        normalized_timestamp = normalize_timestamp(
            self.timestamp
        )

        normalized_version = normalize_non_negative_int(
            self.version,
            field_name="version",
        )

        if not normalized_state_id:
            raise ValueError(
                "state_id must not be empty"
            )

        if normalized_version < 1:
            raise ValueError(
                "version must be >= 1"
            )

        if self.schema_version != STATE_SCHEMA_VERSION:
            raise ValueError(
                (
                    "unsupported schema_version: "
                    f"{self.schema_version}"
                )
            )

        normalized_score = normalize_score(
            self.risk_score
        )

        if not isinstance(
            self.threat_level,
            ThreatLevel,
        ):
            try:
                normalized_threat_level = (
                    ThreatLevel(
                        self.threat_level
                    )
                )

            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "invalid threat_level"
                ) from exc

        else:
            normalized_threat_level = (
                self.threat_level
            )

        if not isinstance(
            self.posture,
            SecurityPosture,
        ):
            try:
                normalized_posture = (
                    SecurityPosture(
                        self.posture
                    )
                )

            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "invalid posture"
                ) from exc

        else:
            normalized_posture = self.posture

        normalized_signals = normalize_signals(
            self.active_signals
        )

        normalized_assets = normalize_non_negative_int(
            self.active_assets,
            field_name="active_assets",
        )

        normalized_identities = normalize_non_negative_int(
            self.active_identities,
            field_name="active_identities",
        )

        normalized_sessions = normalize_non_negative_int(
            self.active_sessions,
            field_name="active_sessions",
        )

        normalized_source = normalize_string(
            self.source,
            field_name="source",
        )

        normalized_correlation_id = (
            None
        )

        if self.correlation_id is not None:
            normalized_correlation_id = (
                normalize_string(
                    self.correlation_id,
                    field_name="correlation_id",
                )
            )

        normalized_metadata = freeze_mapping(
            self.metadata
        )

        object.__setattr__(
            self,
            "state_id",
            normalized_state_id,
        )

        object.__setattr__(
            self,
            "timestamp",
            normalized_timestamp,
        )

        object.__setattr__(
            self,
            "version",
            normalized_version,
        )

        object.__setattr__(
            self,
            "risk_score",
            normalized_score,
        )

        object.__setattr__(
            self,
            "threat_level",
            normalized_threat_level,
        )

        object.__setattr__(
            self,
            "posture",
            normalized_posture,
        )

        object.__setattr__(
            self,
            "active_signals",
            normalized_signals,
        )

        object.__setattr__(
            self,
            "active_assets",
            normalized_assets,
        )

        object.__setattr__(
            self,
            "active_identities",
            normalized_identities,
        )

        object.__setattr__(
            self,
            "active_sessions",
            normalized_sessions,
        )

        object.__setattr__(
            self,
            "source",
            normalized_source,
        )

        object.__setattr__(
            self,
            "correlation_id",
            normalized_correlation_id,
        )

        object.__setattr__(
            self,
            "metadata",
            normalized_metadata,
        )

    # ------------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        risk_score: float = 0.0,
        active_signals: Sequence[str] = (),
        active_assets: int = 0,
        active_identities: int = 0,
        active_sessions: int = 0,
        source: str = DEFAULT_STATE_SOURCE,
        correlation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        timestamp: datetime | None = None,
        version: int = 1,
    ) -> EnterpriseState:
        """
        Create a validated enterprise state.

        Threat level and posture are derived from the supplied state
        characteristics unless explicitly reconstructed from serialized
        state.
        """

        resolved_timestamp = (
            utc_now()
            if timestamp is None
            else normalize_timestamp(
                timestamp
            )
        )

        normalized_score = normalize_score(
            risk_score
        )

        normalized_signals = normalize_signals(
            active_signals
        )

        normalized_threat_level = (
            derive_threat_level(
                normalized_score
            )
        )

        normalized_posture = (
            derive_security_posture(
                normalized_score,
                signal_count=len(
                    normalized_signals
                ),
            )
        )

        state_id = generate_state_id(
            resolved_timestamp,
            version,
        )

        return cls(
            state_id=state_id,
            timestamp=resolved_timestamp,
            version=version,
            schema_version=STATE_SCHEMA_VERSION,
            risk_score=normalized_score,
            threat_level=normalized_threat_level,
            posture=normalized_posture,
            active_signals=normalized_signals,
            active_assets=active_assets,
            active_identities=active_identities,
            active_sessions=active_sessions,
            source=source,
            correlation_id=correlation_id,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    # ------------------------------------------------------------------------
    # Evolution
    # ------------------------------------------------------------------------

    def evolve(
        self,
        *,
        risk_score: float | None = None,
        active_signals: Sequence[str] | None = None,
        active_assets: int | None = None,
        active_identities: int | None = None,
        active_sessions: int | None = None,
        source: str | None = None,
        correlation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> EnterpriseState:
        """
        Produce a new state derived from the current state.

        The original state remains unchanged.

        Version is incremented automatically.

        This is the primary mechanism for temporal state evolution.
        """

        next_timestamp = (
            utc_now()
            if timestamp is None
            else normalize_timestamp(
                timestamp
            )
        )

        next_risk_score = (
            self.risk_score
            if risk_score is None
            else normalize_score(
                risk_score
            )
        )

        next_signals = (
            self.active_signals
            if active_signals is None
            else normalize_signals(
                active_signals
            )
        )

        next_assets = (
            self.active_assets
            if active_assets is None
            else active_assets
        )

        next_identities = (
            self.active_identities
            if active_identities is None
            else active_identities
        )

        next_sessions = (
            self.active_sessions
            if active_sessions is None
            else active_sessions
        )

        next_source = (
            self.source
            if source is None
            else source
        )

        next_correlation_id = (
            self.correlation_id
            if correlation_id is None
            else correlation_id
        )

        next_metadata = (
            dict(self.metadata)
            if metadata is None
            else dict(metadata)
        )

        next_threat_level = (
            derive_threat_level(
                next_risk_score
            )
        )

        next_posture = (
            derive_security_posture(
                next_risk_score,
                signal_count=len(
                    next_signals
                ),
            )
        )

        return EnterpriseState(
            state_id=generate_state_id(
                next_timestamp,
                self.version + 1,
            ),
            timestamp=next_timestamp,
            version=self.version + 1,
            schema_version=STATE_SCHEMA_VERSION,
            risk_score=next_risk_score,
            threat_level=next_threat_level,
            posture=next_posture,
            active_signals=next_signals,
            active_assets=next_assets,
            active_identities=next_identities,
            active_sessions=next_sessions,
            source=next_source,
            correlation_id=next_correlation_id,
            metadata=next_metadata,
        )

    # ------------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the state into a JSON-friendly dictionary.

        This method does not write to disk.
        """

        return {
            "state_id": self.state_id,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "schema_version": self.schema_version,
            "risk_score": self.risk_score,
            "threat_level": self.threat_level.value,
            "posture": self.posture.value,
            "active_signals": list(
                self.active_signals
            ),
            "active_assets": self.active_assets,
            "active_identities": self.active_identities,
            "active_sessions": self.active_sessions,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "metadata": dict(
                self.metadata
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> EnterpriseState:
        """
        Reconstruct a validated EnterpriseState from serialized data.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "state data must be a mapping"
            )

        required_fields = (
            "state_id",
            "timestamp",
            "version",
            "schema_version",
            "risk_score",
            "threat_level",
            "posture",
            "active_signals",
            "active_assets",
            "active_identities",
            "active_sessions",
            "source",
            "correlation_id",
            "metadata",
        )

        missing = [
            field_name
            for field_name in required_fields
            if field_name not in data
        ]

        if missing:
            raise ValueError(
                "missing state fields: "
                + ", ".join(missing)
            )

        timestamp_value = data[
            "timestamp"
        ]

        if not isinstance(
            timestamp_value,
            datetime,
        ):

            if not isinstance(
                timestamp_value,
                str,
            ):
                raise TypeError(
                    "serialized timestamp must be a string"
                )

            try:
                timestamp_value = (
                    datetime.fromisoformat(
                        timestamp_value
                    )
                )

            except ValueError as exc:
                raise ValueError(
                    "invalid serialized timestamp"
                ) from exc

        return cls(
            state_id=str(
                data["state_id"]
            ),
            timestamp=timestamp_value,
            version=data["version"],
            schema_version=str(
                data["schema_version"]
            ),
            risk_score=data["risk_score"],
            threat_level=ThreatLevel(
                data["threat_level"]
            ),
            posture=SecurityPosture(
                data["posture"]
            ),
            active_signals=data[
                "active_signals"
            ],
            active_assets=data[
                "active_assets"
            ],
            active_identities=data[
                "active_identities"
            ],
            active_sessions=data[
                "active_sessions"
            ],
            source=data[
                "source"
            ],
            correlation_id=data[
                "correlation_id"
            ],
            metadata=data[
                "metadata"
            ],
        )

    # ------------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------------

    def changed_from(
        self,
        previous: EnterpriseState,
    ) -> dict[str, tuple[Any, Any]]:
        """
        Describe fields that changed from a previous state.

        Returns:

            {
                "risk_score": (old, new),
                ...
            }

        This is useful for future temporal reasoning and checkpoint
        comparison.
        """

        if not isinstance(
            previous,
            EnterpriseState,
        ):
            raise TypeError(
                "previous must be an EnterpriseState"
            )

        current = self.to_dict()
        earlier = previous.to_dict()

        changes: dict[
            str,
            tuple[Any, Any],
        ] = {}

        for key in current:

            if key in {
                "state_id",
                "timestamp",
                "version",
            }:
                continue

            if current[key] != earlier[key]:
                changes[key] = (
                    earlier[key],
                    current[key],
                )

        return changes

    # ------------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------------

    @property
    def signal_count(self) -> int:
        """
        Number of unique active security signals.
        """

        return len(
            self.active_signals
        )

    @property
    def is_elevated(self) -> bool:
        """
        Whether the current state is above normal posture.
        """

        return self.posture in {
            SecurityPosture.ELEVATED,
            SecurityPosture.DEGRADED,
            SecurityPosture.CRITICAL,
        }

    @property
    def is_critical(self) -> bool:
        """
        Whether the state is classified as critical.
        """

        return (
            self.threat_level
            == ThreatLevel.CRITICAL
        )

    def summary(self) -> dict[str, Any]:
        """
        Return a compact state summary.

        This method is intentionally read-only.
        """

        return {
            "state_id": self.state_id,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "risk_score": self.risk_score,
            "threat_level": self.threat_level.value,
            "posture": self.posture.value,
            "signal_count": self.signal_count,
            "active_assets": self.active_assets,
            "active_identities": self.active_identities,
            "active_sessions": self.active_sessions,
            "source": self.source,
        }


# ============================================================================
# State validation helpers
# ============================================================================


def validate_state(
    state: EnterpriseState,
) -> bool:
    """
    Validate an EnterpriseState instance.

    Returns True when valid.

    Since EnterpriseState validates itself during construction,
    this helper primarily provides a stable validation boundary for
    downstream components.
    """

    if not isinstance(
        state,
        EnterpriseState,
    ):
        raise TypeError(
            "state must be an EnterpriseState"
        )

    # Reconstructing through the public serialization contract provides
    # an additional integrity check.
    EnterpriseState.from_dict(
        state.to_dict()
    )

    return True


def create_initial_state(
    *,
    source: str = DEFAULT_STATE_SOURCE,
    metadata: Mapping[str, Any] | None = None,
) -> EnterpriseState:
    """
    Create a clean initial enterprise state.

    This represents an operational baseline rather than a security
    decision.
    """

    return EnterpriseState.create(
        risk_score=0.0,
        active_signals=(),
        active_assets=0,
        active_identities=0,
        active_sessions=0,
        source=source,
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
    )


# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Run deterministic isolated tests for the State layer.

    No:

    - network
    - filesystem
    - ML model
    - detector
    - dashboard
    - external service

    is used.
    """

    # ------------------------------------------------------------------------
    # Test 1: initial state
    # ------------------------------------------------------------------------

    initial = create_initial_state()

    assert isinstance(
        initial,
        EnterpriseState,
    )

    assert (
        initial.version
        == 1
    )

    assert (
        initial.schema_version
        == STATE_SCHEMA_VERSION
    )

    assert (
        initial.risk_score
        == 0.0
    )

    assert (
        initial.threat_level
        == ThreatLevel.LOW
    )

    assert (
        initial.posture
        == SecurityPosture.HEALTHY
    )

    assert (
        initial.signal_count
        == 0
    )

    # ------------------------------------------------------------------------
    # Test 2: signal normalization
    # ------------------------------------------------------------------------

    state_with_signals = (
        EnterpriseState.create(
            risk_score=0.35,
            active_signals=(
                "impossible_travel",
                "suspicious_login",
                "impossible_travel",
            ),
            active_assets=10,
            active_identities=25,
            active_sessions=40,
        )
    )

    assert (
        state_with_signals.signal_count
        == 2
    )

    assert (
        state_with_signals.active_signals
        == (
            "impossible_travel",
            "suspicious_login",
        )
    )

    assert (
        state_with_signals.threat_level
        == ThreatLevel.MEDIUM
    )

    assert (
        state_with_signals.posture
        == SecurityPosture.ELEVATED
    )

    # ------------------------------------------------------------------------
    # Test 3: high-risk state
    # ------------------------------------------------------------------------

    high_risk = (
        EnterpriseState.create(
            risk_score=0.85,
            active_signals=(
                "credential_abuse",
            ),
        )
    )

    assert (
        high_risk.threat_level
        == ThreatLevel.CRITICAL
    )

    assert (
        high_risk.posture
        == SecurityPosture.CRITICAL
    )

    assert high_risk.is_elevated

    assert high_risk.is_critical

    # ------------------------------------------------------------------------
    # Test 4: evolution
    # ------------------------------------------------------------------------

    evolved = initial.evolve(
        risk_score=0.65,
        active_signals=(
            "anomalous_authentication",
        ),
        active_assets=15,
        active_identities=30,
        active_sessions=55,
    )

    assert (
        evolved.version
        == initial.version + 1
    )

    assert (
        evolved.risk_score
        == 0.65
    )

    assert (
        evolved.threat_level
        == ThreatLevel.HIGH
    )

    assert (
        evolved.posture
        == SecurityPosture.DEGRADED
    )

    assert (
        initial.risk_score
        == 0.0
    )

    assert (
        initial.signal_count
        == 0
    )

    # ------------------------------------------------------------------------
    # Test 5: immutability
    # ------------------------------------------------------------------------

    try:
        evolved.risk_score = 0.2
        raise AssertionError(
            "EnterpriseState must be immutable"
        )

    except AttributeError:
        pass

    # ------------------------------------------------------------------------
    # Test 6: serialization
    # ------------------------------------------------------------------------

    serialized = evolved.to_dict()

    assert isinstance(
        serialized,
        dict,
    )

    assert (
        serialized["version"]
        == evolved.version
    )

    assert (
        serialized["threat_level"]
        == "HIGH"
    )

    restored = (
        EnterpriseState.from_dict(
            serialized
        )
    )

    assert (
        restored
        == evolved
    )

    # ------------------------------------------------------------------------
    # Test 7: validation boundary
    # ------------------------------------------------------------------------

    assert validate_state(
        restored
    ) is True

    # ------------------------------------------------------------------------
    # Test 8: state comparison
    # ------------------------------------------------------------------------

    changes = evolved.changed_from(
        initial
    )

    assert (
        "risk_score"
        in changes
    )

    assert (
        changes["risk_score"]
        == (
            0.0,
            0.65,
        )
    )

    assert (
        "active_signals"
        in changes
    )

    # ------------------------------------------------------------------------
    # Test 9: metadata
    # ------------------------------------------------------------------------

    metadata_state = (
        EnterpriseState.create(
            metadata={
                "environment": "test",
                "collector": "self-test",
            }
        )
    )

    assert (
        metadata_state.metadata[
            "environment"
        ]
        == "test"
    )

    assert isinstance(
        metadata_state.metadata,
        Mapping,
    )

    # ------------------------------------------------------------------------
    # Test 10: invalid risk score
    # ------------------------------------------------------------------------

    try:
        EnterpriseState.create(
            risk_score=1.5
        )

        raise AssertionError(
            "Invalid risk score was accepted"
        )

    except ValueError:
        pass

    # ------------------------------------------------------------------------
    # Test 11: invalid timestamp
    # ------------------------------------------------------------------------

    try:
        EnterpriseState(
            state_id="invalid",
            timestamp=datetime.now(),
        )

        raise AssertionError(
            "Naive timestamp was accepted"
        )

    except ValueError:
        pass

    # ------------------------------------------------------------------------
    # Test 12: invalid signal type
    # ------------------------------------------------------------------------

    try:
        EnterpriseState.create(
            active_signals="not-a-sequence"
        )

        raise AssertionError(
            "String signal collection was accepted"
        )

    except TypeError:
        pass

    # ------------------------------------------------------------------------
    # Test 13: deterministic score boundaries
    # ------------------------------------------------------------------------

    assert (
        derive_threat_level(0.00)
        == ThreatLevel.LOW
    )

    assert (
        derive_threat_level(0.19)
        == ThreatLevel.LOW
    )

    assert (
        derive_threat_level(0.20)
        == ThreatLevel.MEDIUM
    )

    assert (
        derive_threat_level(0.50)
        == ThreatLevel.HIGH
    )

    assert (
        derive_threat_level(0.80)
        == ThreatLevel.CRITICAL
    )

    # ------------------------------------------------------------------------
    # Test 14: summary contract
    # ------------------------------------------------------------------------

    summary = evolved.summary()

    assert isinstance(
        summary,
        dict,
    )

    for key in (
        "state_id",
        "timestamp",
        "version",
        "risk_score",
        "threat_level",
        "posture",
        "signal_count",
    ):
        assert key in summary

    # ------------------------------------------------------------------------
    # Test 15: no external dependencies
    # ------------------------------------------------------------------------

    # The state layer must remain a pure domain model.
    # Import-level architectural dependencies are intentionally absent.

    return True


# ============================================================================
# Module execution
# ============================================================================


if __name__ == "__main__":

    print("=" * 70)

    print(
        "EnterpriseGuard - ADIE State Layer Self-Test"
    )

    print("=" * 70)

    try:

        self_test()

        print(
            "[PASS] EnterpriseState model"
        )

        print(
            "[PASS] State validation"
        )

        print(
            "[PASS] Risk classification"
        )

        print(
            "[PASS] Security posture"
        )

        print(
            "[PASS] Temporal state evolution"
        )

        print(
            "[PASS] State immutability"
        )

        print(
            "[PASS] Serialization contract"
        )

        print(
            "[PASS] State comparison"
        )

        print(
            "[PASS] Input validation"
        )

        print(
            "[PASS] Domain-layer isolation"
        )

        print("=" * 70)

        print(
            "SELF-TEST PASSED"
        )

        print("=" * 70)

    except AssertionError as exc:

        print(
            "[FAIL] Assertion error:"
        )

        print(
            exc
        )

        raise SystemExit(1)

    except Exception as exc:

        print(
            "[FAIL] Unexpected error:"
        )

        print(
            exc
        )

        raise SystemExit(1)