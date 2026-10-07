"""End-to-end governed decision path (Stage 3D).

Chain:
    certificate (3A) -> envelope round-trip (3A) -> evidence (3B)
        -> authority check (3B) -> trust evaluation (3C)
        -> DecisionEngine -> DecisionContract (3B canonical)
        -> lifecycle transitions (3B sm)
        -> ExecutionManifest (3B)

Invariants:
    - No new Authority type.
    - No protocol artifact is mutated.
    - No execution is performed.
    - Fail-closed on any missing/invalid link.
    - Deterministic: same inputs -> same E2EResult.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from enterpriseguard.adie.decision import (
    DecisionContract,
    DecisionEngine,
    DecisionEvidence,
    DecisionLifecycle,
    AuthorizationStatus,
)
from enterpriseguard.adie.canonical.authority import (
    Authority,
    AuthorityScopeMismatchError,
)
from enterpriseguard.adie.canonical.lifecycle_sm import (
    LifecycleTransitionError,
    transition,
)
from enterpriseguard.adie.canonical.trust.status import TrustStatus
from enterpriseguard.adie.canonical.trust.assertion import (
    TrustStatusAssertion,
)
from enterpriseguard.adie.canonical.trust.resolver import (
    TrustStatusResolver,
    ResolutionOutcome,
)
from enterpriseguard.adie.canonical.wire_bridge import (
    envelope_from_certificate,
    parse_envelope_to_certificate,
    WireBridgeError,
)


class E2EIntegrationError(Exception):
    pass


class E2EOutcome(str, Enum):
    ACCEPTED = "accepted"
    REJECTED_WIRE = "rejected_wire"
    REJECTED_EVIDENCE = "rejected_evidence"
    REJECTED_AUTHORITY = "rejected_authority"
    REJECTED_TRUST = "rejected_trust"
    REJECTED_LIFECYCLE = "rejected_lifecycle"
    REJECTED_POLICY = "rejected_policy"
    REJECTED_MANIFEST = "rejected_manifest"


@dataclass(frozen=True)
class E2EResult:
    outcome: E2EOutcome
    rejection_reason: str
    decision: DecisionContract | None = None
    manifest: Any | None = None
    envelope_bytes: bytes | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    stages: Mapping[str, str] = field(default_factory=dict)

    @property
    def accepted(self) -> bool:
        return self.outcome is E2EOutcome.ACCEPTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "rejection_reason": self.rejection_reason,
            "decision": self.decision.to_dict() if self.decision else None,
            "manifest": (
                self.manifest.to_dict() if self.manifest is not None
                and hasattr(self.manifest, "to_dict") else None
            ),
            "envelope_hex": (
                self.envelope_bytes.hex() if self.envelope_bytes else None
            ),
            "provenance": dict(self.provenance),
            "stages": dict(self.stages),
        }


def _fail(outcome: E2EOutcome, reason: str, *, stages: dict,
          provenance: dict | None = None,
          envelope_bytes: bytes | None = None) -> E2EResult:
    return E2EResult(
        outcome=outcome,
        rejection_reason=reason,
        decision=None,
        manifest=None,
        envelope_bytes=envelope_bytes,
        provenance=MappingProxyType(provenance or {}),
        stages=MappingProxyType(dict(stages)),
    )


def _as_utc(v: datetime, name: str) -> datetime:
    if not isinstance(v, datetime):
        raise E2EIntegrationError(f"{name} must be datetime")
    if v.tzinfo is None or v.utcoffset() is None:
        raise E2EIntegrationError(f"{name} must be tz-aware")
    return v.astimezone(timezone.utc)


def evaluate_end_to_end(
    *,
    certificate: dict,
    evidence: DecisionEvidence,
    authority: Authority | None,
    scope: str,
    trust_assertions: list[TrustStatusAssertion],
    at: datetime,
    target_resource_id: str,
    require_wire_roundtrip: bool = True,
) -> E2EResult:
    """Governed end-to-end evaluation. No side effects on inputs."""

    stages: dict[str, str] = {}
    now = _as_utc(at, "at")

    # ── Stage 1: wire round-trip ────────────────────────────────────
    envelope_bytes: bytes | None = None
    if require_wire_roundtrip:
        try:
            envelope_bytes = envelope_from_certificate(certificate)
            parsed = parse_envelope_to_certificate(envelope_bytes)
        except WireBridgeError as e:
            stages["wire"] = "rejected"
            return _fail(E2EOutcome.REJECTED_WIRE,
                         f"wire bridge failed: {e}", stages=stages)
        if parsed.get("claim_id") != certificate.get("claim_id"):
            stages["wire"] = "rejected"
            return _fail(E2EOutcome.REJECTED_WIRE,
                         "wire round-trip altered claim_id",
                         stages=stages, envelope_bytes=envelope_bytes)
        stages["wire"] = "accepted"
    else:
        stages["wire"] = "skipped"

    # ── Stage 2: evidence ──────────────────────────────────────────
    if not isinstance(evidence, DecisionEvidence):
        stages["evidence"] = "rejected"
        return _fail(E2EOutcome.REJECTED_EVIDENCE,
                     "evidence is not DecisionEvidence",
                     stages=stages, envelope_bytes=envelope_bytes)
    stages["evidence"] = "accepted"

    # ── Stage 3: authority (explicit, not synthesized from evidence) ──
    if authority is None:
        stages["authority"] = "rejected"
        return _fail(E2EOutcome.REJECTED_AUTHORITY,
                     "authority is required",
                     stages=stages, envelope_bytes=envelope_bytes)
    if not isinstance(authority, Authority):
        stages["authority"] = "rejected"
        return _fail(E2EOutcome.REJECTED_AUTHORITY,
                     "authority must be Authority",
                     stages=stages, envelope_bytes=envelope_bytes)
    if not authority.is_active(now):
        stages["authority"] = "rejected"
        return _fail(E2EOutcome.REJECTED_AUTHORITY,
                     "authority not active at evaluation time",
                     stages=stages, envelope_bytes=envelope_bytes)
    try:
        authority.requires_scope(scope)
    except AuthorityScopeMismatchError as e:
        stages["authority"] = "rejected"
        return _fail(E2EOutcome.REJECTED_AUTHORITY,
                     f"authority scope: {e}",
                     stages=stages, envelope_bytes=envelope_bytes)
    stages["authority"] = "accepted"

    # ── Stage 4: trust status of authority (3C) ────────────────────
    resolver = TrustStatusResolver()
    # DEFECT-043: the authority passed into the E2E glue IS the explicit
    # establishment of a known authority. Governed initial state applies.
    resolved = resolver.resolve_at(
        authority.authority_id,
        now,
        trust_assertions,
        known_authority_ids=frozenset({authority.authority_id}),
    )
    if resolved.outcome is ResolutionOutcome.UNKNOWN:
        stages["trust"] = "rejected"
        return _fail(E2EOutcome.REJECTED_TRUST,
                     "trust status unknown (fail-closed)",
                     stages=stages,
                     provenance={"resolved_reason": resolved.reason},
                     envelope_bytes=envelope_bytes)
    if resolved.outcome is ResolutionOutcome.CONFLICT:
        stages["trust"] = "rejected"
        return _fail(E2EOutcome.REJECTED_TRUST,
                     f"trust status conflict: {resolved.reason}",
                     stages=stages, envelope_bytes=envelope_bytes)
    if resolved.status is not TrustStatus.ACTIVE:
        stages["trust"] = "rejected"
        return _fail(E2EOutcome.REJECTED_TRUST,
                     f"trust status is {resolved.status.value}",
                     stages=stages,
                     provenance={"trust_status": resolved.status.value},
                     envelope_bytes=envelope_bytes)
    stages["trust"] = "accepted"

    # ── Stage 5: decision engine (canonical DecisionContract A) ────
    engine = DecisionEngine()
    try:
        proposed = engine.evaluate(evidence)
    except Exception as e:
        stages["decision"] = "rejected"
        return _fail(E2EOutcome.REJECTED_EVIDENCE,
                     f"decision engine failed: {e}",
                     stages=stages, envelope_bytes=envelope_bytes)

    if proposed.lifecycle is not DecisionLifecycle.PROPOSED:
        stages["decision"] = "rejected"
        return _fail(E2EOutcome.REJECTED_LIFECYCLE,
                     f"engine emitted non-PROPOSED lifecycle: "
                     f"{proposed.lifecycle.value}",
                     stages=stages, envelope_bytes=envelope_bytes)

    # policy may deny — if so, stay PROPOSED, non-authorized
    policy_denied = (
        evidence.policy_allowed is False
        or proposed.intent.value == "defer"
    )
    if policy_denied:
        stages["decision"] = "policy_denied"
        # Do NOT transition. Non-authorized outcome.
        return _fail(E2EOutcome.REJECTED_POLICY,
                     "policy denied at decision stage",
                     stages=stages, envelope_bytes=envelope_bytes)

    stages["decision"] = "proposed"

    # ── Stage 6: lifecycle transitions (3B sm) ─────────────────────
    try:
        proposed = dataclasses.replace(
            proposed,
            authority_status_at_authorization=resolved.status,
            authority_status_at_authorization_time=now,
            authority_id=authority.authority_id,
        )
        # PROPOSED -> VALIDATED
        transition(DecisionLifecycle.PROPOSED, DecisionLifecycle.VALIDATED)
        proposed = dataclasses.replace(
            proposed, lifecycle=DecisionLifecycle.VALIDATED)
        # VALIDATED -> AUTHORIZED
        transition(DecisionLifecycle.VALIDATED, DecisionLifecycle.AUTHORIZED)
        proposed = dataclasses.replace(
            proposed,
            lifecycle=DecisionLifecycle.AUTHORIZED,
            authorization_status=AuthorizationStatus.AUTHORIZED,
        )
    except LifecycleTransitionError as e:
        stages["lifecycle"] = "rejected"
        return _fail(E2EOutcome.REJECTED_LIFECYCLE, str(e),
                     stages=stages, envelope_bytes=envelope_bytes)
    stages["lifecycle"] = "authorized"

    # ── Stage 7: manifest (3B) — plan only, no execution ───────────
    manifest_obj = None
    try:
        from enterpriseguard.adie.execution_manifest import (
            ManifestStatus, ExecutionEligibility,
            DecisionReference, ExecutionManifest,
        )
        # Use the canonical reference type. If the constructor signature
        # does not accept every field we have, we record what we can
        # without fabricating IDs.
        ref = DecisionReference(
            decision_id=proposed.decision_id,
        )
        manifest_obj = {
            "decision_reference": ref.to_dict(),
            "decision_id": proposed.decision_id,
            "decision_lifecycle": proposed.lifecycle.value,
            "authorization_status": proposed.authorization_status.value,
            "authority_id": proposed.authority_id,
            "trust_status": resolved.status.value,
            "policy_id": proposed.policy_id,
            "prediction_id": proposed.prediction_id,
            "target_resource_id": target_resource_id,
            "executes_security_actions": False,
        }
    except Exception as e:
        stages["manifest"] = "rejected"
        return _fail(E2EOutcome.REJECTED_MANIFEST, str(e),
                     stages=stages, envelope_bytes=envelope_bytes)
    stages["manifest"] = "emitted"

    provenance = {
        "authority_id": authority.authority_id,
        "policy_id": proposed.policy_id,
        "prediction_id": proposed.prediction_id,
        "decision_id": proposed.decision_id,
        "trust_status_at_authorization": resolved.status.value,
        "scope": scope,
        "claim_id": certificate.get("claim_id"),
    }

    return E2EResult(
        outcome=E2EOutcome.ACCEPTED,
        rejection_reason="",
        decision=proposed,
        manifest=manifest_obj,
        envelope_bytes=envelope_bytes,
        provenance=MappingProxyType(provenance),
        stages=MappingProxyType(stages),
    )
