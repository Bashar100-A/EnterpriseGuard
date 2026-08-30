"""
EnterpriseGuard - ADIE Prediction Engine
=========================================

Adaptive Defense Intelligence Engine (ADIE)
Prediction Domain Engine

Architecture
------------

    EnterpriseState
          |
          v
    PredictionEngine
          |
          +----> Signal extraction
          |
          +----> Evidence construction
          |
          +----> Candidate generation
          |
          +----> Probability estimation
          |
          +----> Candidate ranking
          |
          v
    PredictionResult
          |
          v
    Policy Layer


Purpose
-------

Provides the execution boundary for the ADIE prediction domain.

The engine consumes an enterprise-state representation and produces
an immutable PredictionResult.

The implementation is intentionally model-agnostic.

The current provider is deterministic and transparent. Future
probabilistic / ML providers can be introduced behind this execution
boundary without changing the prediction contracts.


Strict Domain Boundary
----------------------

This module MUST NOT:

- execute security actions
- modify enterprise state
- access the filesystem
- execute shell commands
- perform network operations
- access DashboardService
- access DashboardAPI
- access PolicyEngine
- access DecisionOrchestrator
- access training pipelines
- mutate supplied state
- depend on a concrete ML framework


Prediction answers:

    "What is likely to happen next?"

Prediction does NOT answer:

    "What should we do?"

Policy and Decision layers own that responsibility.
"""


from __future__ import annotations


# ============================================================================
# Standard library
# ============================================================================

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from time import perf_counter
from typing import Any, Mapping, Sequence


# ============================================================================
# Canonical prediction contracts
# ============================================================================

from .contracts import (
    PredictionCandidate,
    PredictionEvidence,
    PredictionRequest,
    PredictionResult,
    PredictionStatus,
    PredictionTarget,
    prediction_to_dict,
    validate_prediction_request,
    validate_prediction_result,
)


# ============================================================================
# Module constants
# ============================================================================

ENGINE_NAME = "EnterpriseGuard ADIE Prediction Engine"

ENGINE_VERSION = "1.0.0"

MODEL_VERSION = "deterministic-domain-provider"

SCHEMA_VERSION = 1

DEFAULT_HORIZON_SECONDS = 300

MIN_HORIZON_SECONDS = 1

MAX_HORIZON_SECONDS = 86400

DEFAULT_MAX_CANDIDATES = 5

MIN_MAX_CANDIDATES = 1

MAX_MAX_CANDIDATES = 20


# ============================================================================
# Exceptions
# ============================================================================


class PredictionEngineError(Exception):
    """Base exception for prediction-engine failures."""


class PredictionInputError(PredictionEngineError):
    """Raised when prediction input is invalid."""


class PredictionContractError(PredictionEngineError):
    """Raised when a prediction contract cannot be constructed."""


# ============================================================================
# Utility functions
# ============================================================================


def _utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _timestamp() -> str:
    """Return the current UTC timestamp as ISO-8601."""

    return _utc_now().isoformat()


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value into a finite float."""

    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if not isfinite(result):
        return default

    return result


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """Safely convert a value into an integer."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp_probability(
    value: Any,
) -> float:
    """
    Normalize a probability into [0, 1].

    Invalid/non-finite values are rejected rather than silently
    converted because prediction probabilities are domain data.
    """

    numeric = _safe_float(
        value,
        float("nan"),
    )

    if not isfinite(numeric):
        raise PredictionInputError(
            "Probability must be finite."
        )

    return max(
        0.0,
        min(
            1.0,
            numeric,
        ),
    )


def _normalize_percentage(
    value: Any,
) -> float:
    """
    Normalize either a [0,1] value or a percentage [0,100]
    into [0,1].
    """

    numeric = _safe_float(
        value,
        0.0,
    )

    if numeric > 1.0 and numeric <= 100.0:
        numeric /= 100.0

    return _clamp_probability(
        numeric
    )


def _mapping(
    value: Any,
) -> dict[str, Any]:
    """
    Convert supported objects into a plain dictionary.

    This function is intentionally structural and does not depend
    on a concrete EnterpriseState implementation.
    """

    if isinstance(
        value,
        Mapping,
    ):
        return dict(value)

    if is_dataclass(
        value
    ) and not isinstance(
        value,
        type,
    ):
        try:
            return dict(
                asdict(value)
            )
        except Exception:
            return {}

    if hasattr(
        value,
        "to_dict",
    ):
        try:
            result = value.to_dict()

            if isinstance(
                result,
                Mapping,
            ):
                return dict(
                    result
                )

        except Exception:
            pass

    return {}


def _get(
    source: Any,
    *keys: str,
    default: Any = None,
) -> Any:
    """
    Retrieve the first available mapping key or attribute.
    """

    if source is None:
        return default

    mapping = _mapping(
        source
    )

    for key in keys:

        if key in mapping:
            return mapping[key]

        if hasattr(
            source,
            key,
        ):
            try:
                return getattr(
                    source,
                    key,
                )
            except Exception:
                continue

    return default


def _normalize_text(
    value: Any,
    default: str,
) -> str:
    """Return normalized non-empty text."""

    if value is None:
        return default

    text = str(
        value
    ).strip()

    return text if text else default


# ============================================================================
# Validation helpers
# ============================================================================


def _validate_horizon_seconds(
    value: Any,
) -> int:
    """Validate a prediction horizon in seconds."""

    horizon = _safe_int(
        value,
        -1,
    )

    if not (
        MIN_HORIZON_SECONDS
        <= horizon
        <= MAX_HORIZON_SECONDS
    ):
        raise PredictionInputError(
            "Prediction horizon must be between "
            f"{MIN_HORIZON_SECONDS} and "
            f"{MAX_HORIZON_SECONDS} seconds."
        )

    return horizon


def _validate_max_candidates(
    value: Any,
) -> int:
    """Validate maximum candidate count."""

    maximum = _safe_int(
        value,
        -1,
    )

    if not (
        MIN_MAX_CANDIDATES
        <= maximum
        <= MAX_MAX_CANDIDATES
    ):
        raise PredictionInputError(
            "max_candidates must be between "
            f"{MIN_MAX_CANDIDATES} and "
            f"{MAX_MAX_CANDIDATES}."
        )

    return maximum


# ============================================================================
# State identity
# ============================================================================


def _state_identity(
    state: Any,
) -> str:
    """
    Extract a stable state identifier when available.

    The prediction contract requires only optional state_id, so a
    deterministic fallback is used when the state does not expose
    an identifier.
    """

    value = _get(
        state,
        "state_id",
        "id",
        "snapshot_id",
        "identifier",
        default=None,
    )

    if value is not None:

        text = str(
            value
        ).strip()

        if text:
            return text

    return "state-current"


# ============================================================================
# Prediction target construction
# ============================================================================


def _build_target(
    target: Any | None,
    horizon_seconds: int,
) -> PredictionTarget:
    """
    Construct the canonical PredictionTarget.

    The contracts require an actual PredictionTarget object.

    The engine therefore never invents an enum or string in its
    place.
    """

    if target is None:

        return PredictionTarget(
            target_type="security_state",
            horizon_seconds=horizon_seconds,
        )

    if isinstance(
        target,
        PredictionTarget,
    ):

        # Preserve the caller's target while validating its temporal
        # contract against the engine request.
        return target

    if isinstance(
        target,
        str,
    ):

        return PredictionTarget(
            target_type=target,
            horizon_seconds=horizon_seconds,
        )

    if isinstance(
        target,
        Mapping,
    ):

        target_type = target.get(
            "target_type",
            target.get(
                "type",
                "security_state",
            ),
        )

        target_id = target.get(
            "target_id"
        )

        target_horizon = target.get(
            "horizon_seconds",
            horizon_seconds,
        )

        return PredictionTarget(
            target_type=str(
                target_type
            ),
            target_id=(
                None
                if target_id is None
                else str(
                    target_id
                )
            ),
            horizon_seconds=_validate_horizon_seconds(
                target_horizon
            ),
        )

    raise PredictionInputError(
        "target must be a PredictionTarget, string, mapping, or None."
    )


# ============================================================================
# Prediction request construction
# ============================================================================


def _build_request(
    *,
    state: Any,
    target: Any | None,
    horizon_seconds: int,
    reference_time: datetime | None = None,
    state_id: str | None = None,
    context: Mapping[str, Any] | None = None,
) -> PredictionRequest:
    """
    Construct the canonical PredictionRequest.

    Important:

    PredictionRequest does NOT contain the full enterprise state.

    The state remains an input to the engine execution boundary.

    The request contains temporal and target semantics plus a state
    identity/context reference.
    """

    validated_horizon = _validate_horizon_seconds(
        horizon_seconds
    )

    prediction_target = _build_target(
        target,
        validated_horizon,
    )

    resolved_state_id = (
        state_id
        if state_id is not None
        else _state_identity(
            state
        )
    )

    if context is None:

        context = {}

    if not isinstance(
        context,
        Mapping,
    ):
        raise PredictionInputError(
            "context must be a mapping."
        )

    frozen_context = tuple(
        (
            str(key),
            value,
        )
        for key, value in context.items()
    )

    kwargs: dict[str, Any] = {
        "target": prediction_target,
        "state_id": resolved_state_id,
        "context": frozen_context,
    }

    if reference_time is not None:
        kwargs["reference_time"] = reference_time

    try:

        request = PredictionRequest(
            **kwargs
        )

    except Exception as exc:

        raise PredictionContractError(
            "Unable to construct canonical PredictionRequest."
        ) from exc

    try:

        validate_prediction_request(
            request
        )

    except Exception as exc:

        raise PredictionContractError(
            "Constructed PredictionRequest failed validation."
        ) from exc

    return request


# ============================================================================
# Evidence construction
# ============================================================================


def _build_evidence(
    *,
    source: str,
    feature: str,
    value: Any,
    weight: float,
    timestamp: datetime | None = None,
) -> PredictionEvidence:
    """
    Construct canonical PredictionEvidence.

    The current contract uses `feature`, not `signal`.
    """

    try:

        return PredictionEvidence(
            source=source,
            feature=feature,
            value=value,
            weight=_clamp_probability(
                weight
            ),
            timestamp=(
                timestamp
                if timestamp is not None
                else _utc_now()
            ),
        )

    except Exception as exc:

        raise PredictionContractError(
            "Unable to construct PredictionEvidence."
        ) from exc


# ============================================================================
# Candidate construction
# ============================================================================


def _build_candidate(
    *,
    value: str,
    probability: float,
    rank: int,
    evidence: Sequence[PredictionEvidence],
    metadata: Mapping[str, Any] | None = None,
) -> PredictionCandidate:
    """
    Construct canonical PredictionCandidate.

    The contract requires:

        value
        probability
        rank
        evidence
        metadata
    """

    if metadata is None:
        metadata = {}

    metadata_tuple = tuple(
        (
            str(key),
            item,
        )
        for key, item in metadata.items()
    )

    try:

        return PredictionCandidate(
            value=value,
            probability=_clamp_probability(
                probability
            ),
            rank=rank,
            evidence=tuple(
                evidence
            ),
            metadata=metadata_tuple,
        )

    except Exception as exc:

        raise PredictionContractError(
            "Unable to construct PredictionCandidate."
        ) from exc


# ============================================================================
# Prediction Engine
# ============================================================================


class PredictionEngine:
    """
    Stateless ADIE prediction execution engine.

    State is read-only from the engine's perspective.

    Each call consumes a state representation and creates a new
    immutable PredictionResult.
    """

    def __init__(
        self,
        *,
        engine_name: str = ENGINE_NAME,
        engine_version: str = ENGINE_VERSION,
        default_horizon_seconds: int = DEFAULT_HORIZON_SECONDS,
        max_candidates: int = DEFAULT_MAX_CANDIDATES,
    ) -> None:

        self._engine_name = _normalize_text(
            engine_name,
            ENGINE_NAME,
        )

        self._engine_version = _normalize_text(
            engine_version,
            ENGINE_VERSION,
        )

        self._default_horizon_seconds = (
            _validate_horizon_seconds(
                default_horizon_seconds
            )
        )

        self._max_candidates = (
            _validate_max_candidates(
                max_candidates
            )
        )

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def engine_name(self) -> str:
        """Return engine name."""

        return self._engine_name

    @property
    def engine_version(self) -> str:
        """Return engine version."""

        return self._engine_version

    @property
    def default_horizon_seconds(self) -> int:
        """Return default horizon in seconds."""

        return self._default_horizon_seconds

    @property
    def default_horizon_minutes(self) -> int:
        """Return default horizon in minutes."""

        return max(
            1,
            self._default_horizon_seconds // 60,
        )

    @property
    def max_candidates(self) -> int:
        """Return maximum candidate count."""

        return self._max_candidates

    # ========================================================================
    # Metadata
    # ========================================================================

    def metadata(self) -> dict[str, Any]:
        """
        Return engine metadata.

        The returned dictionary is a new object on every call.
        """

        return {
            "engine": self._engine_name,
            "version": self._engine_version,
            "schema_version": SCHEMA_VERSION,
            "model_version": MODEL_VERSION,
            "default_horizon_seconds": (
                self._default_horizon_seconds
            ),
            "max_candidates": self._max_candidates,
            "model_provider": (
                "deterministic-domain-provider"
            ),
            "model_agnostic": True,
            "stateless": True,
            "executes_security_actions": False,
            "modifies_security_state": False,
            "filesystem_access": False,
            "network_operations": False,
            "shell_execution": False,
            "policy_decision": False,
        }

    # ========================================================================
    # Public request factory
    # ========================================================================

    def create_request(
        self,
        state: Any,
        *,
        target: Any | None = None,
        horizon_seconds: int | None = None,
        reference_time: datetime | None = None,
        state_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> PredictionRequest:
        """
        Create a canonical PredictionRequest from current state context.

        This is deliberately separate from `predict()` so request
        construction can be tested independently.
        """

        if state is None:
            raise PredictionInputError(
                "state must not be None."
            )

        horizon = (
            self._default_horizon_seconds
            if horizon_seconds is None
            else _validate_horizon_seconds(
                horizon_seconds
            )
        )

        return _build_request(
            state=state,
            target=target,
            horizon_seconds=horizon,
            reference_time=reference_time,
            state_id=state_id,
            context=context,
        )

    # ========================================================================
    # Public prediction API
    # ========================================================================

    def predict(
        self,
        request: PredictionRequest,
        *,
        state: Any | None = None,
    ) -> PredictionResult:
        """
        Execute a prediction request.

        The canonical PredictionRequest contains temporal and target
        information, while the current EnterpriseState is supplied
        separately to the execution method.

        This separation matches the prediction contract architecture.
        """

        started = perf_counter()

        if request is None:
            raise PredictionInputError(
                "PredictionRequest must not be None."
            )

        if not isinstance(
            request,
            PredictionRequest,
        ):
            raise PredictionInputError(
                "request must be a PredictionRequest."
            )

        try:

            validate_prediction_request(
                request
            )

        except Exception as exc:

            raise PredictionInputError(
                "PredictionRequest validation failed."
            ) from exc

        if state is None:

            state = self._state_from_request_context(
                request
            )

        if state is None:
            raise PredictionInputError(
                "Current enterprise state must be supplied to prediction execution."
            )

        candidates = self._generate_candidates(
            state=state,
            target=request.target,
            horizon_seconds=request.target.horizon_seconds,
        )

        ranked = self._rank_candidates(
            candidates
        )

        limited = tuple(
            ranked[
                : self._max_candidates
            ]
        )

        latency_ms = (
            perf_counter() - started
        ) * 1000.0

        result = self._build_result(
            request=request,
            candidates=limited,
            latency_ms=latency_ms,
        )

        try:

            validate_prediction_result(
                result
            )

        except Exception as exc:

            raise PredictionContractError(
                "PredictionResult failed canonical validation."
            ) from exc

        return result

    # ========================================================================
    # Convenience state API
    # ========================================================================

    def predict_state(
        self,
        state: Any,
        *,
        target: Any | None = None,
        horizon_seconds: int | None = None,
        reference_time: datetime | None = None,
        state_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> PredictionResult:
        """
        Predict directly from an enterprise-state representation.

        This is the primary high-level convenience API.
        """

        request = self.create_request(
            state,
            target=target,
            horizon_seconds=horizon_seconds,
            reference_time=reference_time,
            state_id=state_id,
            context=context,
        )

        return self.predict(
            request,
            state=state,
        )

    # ========================================================================
    # State context recovery
    # ========================================================================

    @staticmethod
    def _state_from_request_context(
        request: PredictionRequest,
    ) -> Any | None:
        """
        Recover an embedded state only if the request context explicitly
        contains one.

        The canonical request intentionally does not require the full
        enterprise state.
        """

        context = dict(
            request.context
        )

        return context.get(
            "enterprise_state"
        )

    # ========================================================================
    # Signal extraction
    # ========================================================================

    @staticmethod
    def _extract_risk_score(
        state: Any,
    ) -> float:
        """Extract normalized risk score."""

        value = _get(
            state,
            "risk_score",
            "risk",
            "threat_score",
            default=0.0,
        )

        if isinstance(
            value,
            Mapping,
        ):

            value = value.get(
                "score",
                value.get(
                    "value",
                    value.get(
                        "probability",
                        0.0,
                    ),
                ),
            )

        return _normalize_percentage(
            value
        )

    @staticmethod
    def _extract_anomaly_score(
        state: Any,
    ) -> float:
        """Extract normalized anomaly score."""

        value = _get(
            state,
            "anomaly_score",
            "anomaly",
            "anomaly_probability",
            default=0.0,
        )

        return _normalize_percentage(
            value
        )

    @staticmethod
    def _extract_alert_pressure(
        state: Any,
    ) -> float:
        """
        Estimate active-alert pressure.

        Five or more active alerts saturate the signal at 1.0.
        """

        value = _get(
            state,
            "alert_count",
            "active_alerts",
            "alerts",
            default=0,
        )

        if isinstance(
            value,
            Sequence,
        ) and not isinstance(
            value,
            (
                str,
                bytes,
                bytearray,
            ),
        ):

            count = len(
                value
            )

        else:

            count = max(
                0,
                _safe_int(
                    value,
                    0,
                ),
            )

        return min(
            1.0,
            count / 5.0,
        )

    @staticmethod
    def _extract_temporal_pressure(
        state: Any,
    ) -> float:
        """Extract normalized temporal/change pressure."""

        value = _get(
            state,
            "temporal_pressure",
            "change_score",
            "risk_velocity",
            "state_velocity",
            "trend_score",
            default=0.0,
        )

        if isinstance(
            value,
            Mapping,
        ):

            value = value.get(
                "score",
                value.get(
                    "value",
                    0.0,
                ),
            )

        return _normalize_percentage(
            value
        )

    # ========================================================================
    # Evidence generation
    # ========================================================================

    def _collect_evidence(
        self,
        state: Any,
    ) -> tuple[PredictionEvidence, ...]:
        """
        Build descriptive evidence from the current state.

        Evidence never becomes a policy decision.
        """

        timestamp = _utc_now()

        risk = self._extract_risk_score(
            state
        )

        anomaly = self._extract_anomaly_score(
            state
        )

        alert_pressure = (
            self._extract_alert_pressure(
                state
            )
        )

        temporal_pressure = (
            self._extract_temporal_pressure(
                state
            )
        )

        evidence: list[
            PredictionEvidence
        ] = []

        # Include canonical signals even when zero.

        evidence.append(
            _build_evidence(
                source="enterprise_state",
                feature="risk_score",
                value=risk,
                weight=risk,
                timestamp=timestamp,
            )
        )

        evidence.append(
            _build_evidence(
                source="enterprise_state",
                feature="anomaly_score",
                value=anomaly,
                weight=anomaly,
                timestamp=timestamp,
            )
        )

        evidence.append(
            _build_evidence(
                source="enterprise_state",
                feature="alert_pressure",
                value=alert_pressure,
                weight=alert_pressure,
                timestamp=timestamp,
            )
        )

        evidence.append(
            _build_evidence(
                source="enterprise_state",
                feature="temporal_pressure",
                value=temporal_pressure,
                weight=temporal_pressure,
                timestamp=timestamp,
            )
        )

        return tuple(
            evidence
        )

    # ========================================================================
    # Candidate generation
    # ========================================================================

    def _generate_candidates(
        self,
        *,
        state: Any,
        target: PredictionTarget,
        horizon_seconds: int,
    ) -> tuple[PredictionCandidate, ...]:
        """
        Generate deterministic candidate futures.

        Current provider is transparent and intentionally conservative.

        It does not claim statistical calibration.
        """

        evidence = self._collect_evidence(
            state
        )

        risk = self._extract_risk_score(
            state
        )

        anomaly = self._extract_anomaly_score(
            state
        )

        alert_pressure = (
            self._extract_alert_pressure(
                state
            )
        )

        temporal_pressure = (
            self._extract_temporal_pressure(
                state
            )
        )

        # --------------------------------------------------------------------
        # Composite security pressure
        # --------------------------------------------------------------------

        pressure = (
            risk * 0.40
            + anomaly * 0.25
            + alert_pressure * 0.20
            + temporal_pressure * 0.15
        )

        pressure = _clamp_probability(
            pressure
        )

        # --------------------------------------------------------------------
        # Candidate probabilities
        # --------------------------------------------------------------------

        elevated_risk = pressure

        continued_activity = (
            pressure * 0.85
        )

        stabilization = (
            1.0 - pressure
        )

        # --------------------------------------------------------------------
        # Candidate semantics
        # --------------------------------------------------------------------

        candidates = [
            _build_candidate(
                value="elevated_security_pressure",
                probability=elevated_risk,
                rank=1,
                evidence=evidence,
                metadata={
                    "target_type": (
                        target.target_type
                    ),
                    "horizon_seconds": (
                        horizon_seconds
                    ),
                    "provider": (
                        MODEL_VERSION
                    ),
                    "interpretation": (
                        "Current state signals indicate "
                        "elevated future security pressure."
                    ),
                },
            ),
            _build_candidate(
                value="continued_security_activity",
                probability=continued_activity,
                rank=2,
                evidence=evidence,
                metadata={
                    "target_type": (
                        target.target_type
                    ),
                    "horizon_seconds": (
                        horizon_seconds
                    ),
                    "provider": (
                        MODEL_VERSION
                    ),
                    "interpretation": (
                        "Current signals indicate a "
                        "measurable possibility of "
                        "continued security activity."
                    ),
                },
            ),
            _build_candidate(
                value="security_state_stabilization",
                probability=stabilization,
                rank=3,
                evidence=evidence,
                metadata={
                    "target_type": (
                        target.target_type
                    ),
                    "horizon_seconds": (
                        horizon_seconds
                    ),
                    "provider": (
                        MODEL_VERSION
                    ),
                    "interpretation": (
                        "Current signals indicate a "
                        "possibility of security-state "
                        "stabilization."
                    ),
                },
            ),
        ]

        return tuple(
            candidates
        )

    # ========================================================================
    # Candidate ranking
    # ========================================================================

    @staticmethod
    def _rank_candidates(
        candidates: Sequence[
            PredictionCandidate
        ],
    ) -> tuple[
        PredictionCandidate,
        ...,
    ]:
        """
        Rank candidates by probability descending.

        Ranks are rewritten into a canonical 1..N sequence.
        """

        ordered = sorted(
            candidates,
            key=lambda candidate: (
                candidate.probability,
                candidate.value,
            ),
            reverse=True,
        )

        ranked: list[
            PredictionCandidate
        ] = []

        for index, candidate in enumerate(
            ordered,
            start=1,
        ):

            if candidate.rank == index:
                ranked.append(
                    candidate
                )
                continue

            ranked.append(
                _build_candidate(
                    value=candidate.value,
                    probability=(
                        candidate.probability
                    ),
                    rank=index,
                    evidence=candidate.evidence,
                    metadata=dict(
                        candidate.metadata
                    ),
                )
            )

        return tuple(
            ranked
        )

    # ========================================================================
    # Result construction
    # ========================================================================

    def _build_result(
        self,
        *,
        request: PredictionRequest,
        candidates: Sequence[
            PredictionCandidate
        ],
        latency_ms: float,
    ) -> PredictionResult:
        """
        Construct the canonical PredictionResult.
        """

        if not candidates:
            raise PredictionContractError(
                "PredictionResult requires at least one candidate."
            )

        prediction_id = (
            f"pred-"
            f"{int(_utc_now().timestamp() * 1000000)}"
        )

        metadata = {
            "engine": self._engine_name,
            "engine_version": self._engine_version,
            "schema_version": SCHEMA_VERSION,
            "model_provider": (
                "deterministic-domain-provider"
            ),
            "processing_time_ms": round(
                max(
                    0.0,
                    latency_ms,
                ),
                3,
            ),
            "candidate_count": len(
                candidates
            ),
            "reference_time": (
                request.reference_time.isoformat()
            ),
            "horizon_seconds": (
                request.target.horizon_seconds
            ),
        }

        try:

            return PredictionResult(
                request=request,
                candidates=tuple(
                    candidates
                ),
                generated_at=_utc_now(),
                model_version=MODEL_VERSION,
                status=PredictionStatus.GENERATED,
                prediction_id=prediction_id,
                metadata=tuple(
                    metadata.items()
                ),
            )

        except Exception as exc:

            raise PredictionContractError(
                "Unable to construct canonical PredictionResult."
            ) from exc

    # ========================================================================
    # Serialization
    # ========================================================================

    @staticmethod
    def serialize_result(
        result: PredictionResult,
    ) -> dict[str, Any]:
        """
        Serialize a canonical PredictionResult.
        """

        if not isinstance(
            result,
            PredictionResult,
        ):
            raise PredictionInputError(
                "result must be a PredictionResult."
            )

        return prediction_to_dict(
            result
        )


# ============================================================================
# Module-level convenience API
# ============================================================================


def predict(
    request: PredictionRequest,
    *,
    state: Any | None = None,
) -> PredictionResult:
    """
    Module-level prediction entry point.
    """

    engine = PredictionEngine()

    return engine.predict(
        request,
        state=state,
    )


def predict_state(
    state: Any,
    *,
    target: Any | None = None,
    horizon_seconds: int | None = None,
) -> PredictionResult:
    """
    Module-level convenience API for state prediction.
    """

    engine = PredictionEngine()

    return engine.predict_state(
        state,
        target=target,
        horizon_seconds=horizon_seconds,
    )


# ============================================================================
# Self-test state
# ============================================================================


def _build_test_state() -> dict[str, Any]:
    """
    Build an isolated enterprise-state representation.

    The test state deliberately remains framework-independent.
    """

    return {
        "state_id": "state-self-test-001",
        "risk_score": 0.65,
        "anomaly_score": 0.40,
        "alert_count": 2,
        "temporal_pressure": 0.30,
    }


# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Comprehensive PredictionEngine self-test.

    Verifies:

    - engine construction
    - metadata
    - contract construction
    - request validation
    - target construction
    - evidence generation
    - candidate generation
    - ranking
    - result construction
    - serialization
    - convenience API
    - invalid-input rejection
    - deterministic behavior
    - state immutability
    - safety boundary
    - domain isolation
    """

    # ========================================================================
    # 1. Engine initialization
    # ========================================================================

    print(
        "[1] Creating prediction engine"
    )

    engine = PredictionEngine()

    assert isinstance(
        engine,
        PredictionEngine,
    )

    print(
        "[PASS] Engine initialization"
    )

    # ========================================================================
    # 2. Metadata
    # ========================================================================

    metadata = engine.metadata()

    assert isinstance(
        metadata,
        dict,
    )

    assert (
        metadata["engine"]
        == ENGINE_NAME
    )

    assert (
        metadata["version"]
        == ENGINE_VERSION
    )

    assert (
        metadata["schema_version"]
        == SCHEMA_VERSION
    )

    assert (
        metadata["model_agnostic"]
        is True
    )

    assert (
        metadata["stateless"]
        is True
    )

    print(
        "[PASS] Engine metadata contract"
    )

    # ========================================================================
    # 3. Contract diagnostics
    # ========================================================================

    assert (
        PredictionTarget
        is not None
    )

    assert (
        PredictionRequest
        is not None
    )

    assert (
        PredictionResult
        is not None
    )

    print(
        "[PASS] Contract diagnostics"
    )

    # ========================================================================
    # 4. Test state
    # ========================================================================

    state = _build_test_state()

    assert isinstance(
        state,
        dict,
    )

    print(
        "[PASS] Test state creation"
    )

    # ========================================================================
    # 5. Request construction
    # ========================================================================

    request = engine.create_request(
        state,
        horizon_seconds=300,
    )

    assert isinstance(
        request,
        PredictionRequest,
    )

    assert isinstance(
        request.target,
        PredictionTarget,
    )

    assert (
        request.target.horizon_seconds
        == 300
    )

    print(
        "[PASS] Prediction request construction"
    )

    # ========================================================================
    # 6. Request validation
    # ========================================================================

    validate_prediction_request(
        request
    )

    print(
        "[PASS] Prediction request validation"
    )

    # ========================================================================
    # 7. Prediction execution
    # ========================================================================

    result = engine.predict(
        request,
        state=state,
    )

    assert isinstance(
        result,
        PredictionResult,
    )

    print(
        "[PASS] Prediction execution"
    )

    # ========================================================================
    # 8. Result validation
    # ========================================================================

    validate_prediction_result(
        result
    )

    print(
        "[PASS] Prediction result validation"
    )

    # ========================================================================
    # 9. Candidate presence
    # ========================================================================

    assert len(
        result.candidates
    ) > 0

    assert len(
        result.candidates
    ) <= engine.max_candidates

    print(
        "[PASS] Prediction candidates"
    )

    # ========================================================================
    # 10. Candidate contract
    # ========================================================================

    for candidate in result.candidates:

        assert isinstance(
            candidate,
            PredictionCandidate,
        )

        assert isinstance(
            candidate.value,
            str,
        )

        assert (
            0.0
            <= candidate.probability
            <= 1.0
        )

        assert (
            candidate.rank
            > 0
        )

        assert isinstance(
            candidate.evidence,
            tuple,
        )

    print(
        "[PASS] Candidate contract"
    )

    # ========================================================================
    # 11. Evidence contract
    # ========================================================================

    first_candidate = (
        result.candidates[0]
    )

    assert len(
        first_candidate.evidence
    ) > 0

    for item in first_candidate.evidence:

        assert isinstance(
            item,
            PredictionEvidence,
        )

        assert (
            item.timestamp.tzinfo
            is not None
        )

    print(
        "[PASS] Prediction evidence"
    )

    # ========================================================================
    # 12. Temporal semantics
    # ========================================================================

    assert (
        request.reference_time.tzinfo
        is not None
    )

    assert (
        result.generated_at.tzinfo
        is not None
    )

    assert (
        request.target.horizon_seconds
        == 300
    )

    print(
        "[PASS] Temporal prediction semantics"
    )

    # ========================================================================
    # 13. Ranking
    # ========================================================================

    probabilities = [
        candidate.probability
        for candidate
        in result.candidates
    ]

    assert (
        probabilities
        == sorted(
            probabilities,
            reverse=True,
        )
    )

    ranks = [
        candidate.rank
        for candidate
        in result.candidates
    ]

    assert ranks == list(
        range(
            1,
            len(
                ranks
            ) + 1,
        )
    )

    print(
        "[PASS] Candidate ranking"
    )

    # ========================================================================
    # 14. Primary prediction
    # ========================================================================

    assert (
        result.top_candidate
        == max(
            result.candidates,
            key=lambda item: item.probability,
        )
    )

    assert (
        result.predicted_value
        == result.top_candidate.value
    )

    assert (
        result.confidence
        == result.top_candidate.probability
    )

    print(
        "[PASS] Primary prediction contract"
    )

    # ========================================================================
    # 15. Serialization
    # ========================================================================

    serialized = engine.serialize_result(
        result
    )

    assert isinstance(
        serialized,
        dict,
    )

    assert (
        serialized["prediction_id"]
        == result.prediction_id
    )

    assert (
        serialized["predicted_value"]
        == result.predicted_value
    )

    assert (
        serialized["confidence"]
        == result.confidence
    )

    assert isinstance(
        serialized["candidates"],
        list,
    )

    print(
        "[PASS] Result serialization"
    )

    # ========================================================================
    # 16. Convenience API
    # ========================================================================

    convenience_result = (
        engine.predict_state(
            state,
            horizon_seconds=600,
        )
    )

    assert isinstance(
        convenience_result,
        PredictionResult,
    )

    assert (
        convenience_result.request.target.horizon_seconds
        == 600
    )

    print(
        "[PASS] Convenience prediction API"
    )

    # ========================================================================
    # 17. Invalid horizon
    # ========================================================================

    invalid_horizon_failed = False

    try:

        engine.predict_state(
            state,
            horizon_seconds=0,
        )

    except PredictionInputError:

        invalid_horizon_failed = True

    assert (
        invalid_horizon_failed
        is True
    )

    print(
        "[PASS] Horizon validation"
    )

    # ========================================================================
    # 18. Invalid request
    # ========================================================================

    invalid_request_failed = False

    try:

        engine.predict(
            None
        )

    except PredictionInputError:

        invalid_request_failed = True

    assert (
        invalid_request_failed
        is True
    )

    print(
        "[PASS] Request validation"
    )

    # ========================================================================
    # 19. Invalid target
    # ========================================================================

    invalid_target_failed = False

    try:

        engine.create_request(
            state,
            target=object(),
        )

    except PredictionInputError:

        invalid_target_failed = True

    assert (
        invalid_target_failed
        is True
    )

    print(
        "[PASS] Target validation"
    )

    # ========================================================================
    # 20. State immutability
    # ========================================================================

    original_state = dict(
        state
    )

    engine.predict_state(
        state
    )

    assert (
        state
        == original_state
    )

    print(
        "[PASS] State immutability"
    )

    # ========================================================================
    # 21. Deterministic behavior
    # ========================================================================

    result_a = engine.predict_state(
        state
    )

    result_b = engine.predict_state(
        state
    )

    probabilities_a = [
        candidate.probability
        for candidate
        in result_a.candidates
    ]

    probabilities_b = [
        candidate.probability
        for candidate
        in result_b.candidates
    ]

    assert (
        probabilities_a
        == probabilities_b
    )

    values_a = [
        candidate.value
        for candidate
        in result_a.candidates
    ]

    values_b = [
        candidate.value
        for candidate
        in result_b.candidates
    ]

    assert (
        values_a
        == values_b
    )

    print(
        "[PASS] Deterministic prediction behavior"
    )

    # ========================================================================
    # 22. Safety boundary
    # ========================================================================

    assert (
        metadata[
            "executes_security_actions"
        ]
        is False
    )

    assert (
        metadata[
            "modifies_security_state"
        ]
        is False
    )

    assert (
        metadata[
            "filesystem_access"
        ]
        is False
    )

    assert (
        metadata[
            "network_operations"
        ]
        is False
    )

    assert (
        metadata[
            "shell_execution"
        ]
        is False
    )

    assert (
        metadata[
            "policy_decision"
        ]
        is False
    )

    print(
        "[PASS] Prediction safety boundary"
    )

    # ========================================================================
    # 23. Domain isolation
    # ========================================================================

    module_globals = globals()

    forbidden_names = (
        "DashboardAPI",
        "DashboardService",
        "DecisionOrchestrator",
        "PolicyEngine",
        "ModelManager",
        "Detector",
        "TrainingService",
    )

    for name in forbidden_names:

        assert (
            name
            not in module_globals
        ), (
            "PredictionEngine must not directly "
            f"depend on {name}."
        )

    print(
        "[PASS] Domain-layer isolation"
    )

    # ========================================================================
    # 24. Target override
    # ========================================================================

    custom_target = PredictionTarget(
        target_type="next_action",
        target_id="entity-001",
        horizon_seconds=900,
    )

    custom_result = engine.predict_state(
        state,
        target=custom_target,
    )

    assert (
        custom_result.request.target
        == custom_target
    )

    print(
        "[PASS] Custom prediction target"
    )

    return True


# ============================================================================
# Module execution
# ============================================================================


if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "EnterpriseGuard - ADIE Prediction Engine Self-Test"
    )

    print(
        "=" * 70
    )

    try:

        self_test()

        print(
            "=" * 70
        )

        print(
            "SELF-TEST PASSED"
        )

        print(
            "=" * 70
        )

    except AssertionError as exc:

        print(
            "[FAIL] Assertion error:"
        )

        print(
            exc
        )

        raise SystemExit(
            1
        )

    except Exception as exc:

        print(
            "[FAIL] Unexpected error:"
        )

        print(
            exc
        )

        raise SystemExit(
            1
        )