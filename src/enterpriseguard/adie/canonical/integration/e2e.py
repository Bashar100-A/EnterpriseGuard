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
from protocol.hybrid.verify import verify_hybrid, HybridVerifyError


class E2EIntegrationError(Exception):
    pass


class E2EOutcome(str, Enum):
    ACCEPTED = "accepted"
    REJECTED_WIRE = "rejected_wire"
    REJECTED_CRYPTO = "rejected_crypto"
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
    trust_assertions: list[TrustStatusAssertion] | None = None,
    at: datetime,
    target_resource_id: str,
    require_wire_roundtrip: bool = True,
    # 3D-R1 (FINDING-3D-01): crypto verification
    require_crypto_verification: bool = False,
    rs256_pub_pem: bytes | None = None,
    mldsa65_pub_raw: bytes | None = None,
    # 3D-R1 (FINDING-3D-03): real trust store
    trust_store: Any | None = None,
    # 3D-R1 (FINDING-3D-02): real ExecutionManifest context
    manifest_context: Mapping[str, Any] | None = None,
) -> E2EResult:
    """Governed end-to-end evaluation. No side effects on inputs.

    Crypto verification (FINDING-3D-01):
        When require_crypto_verification=True, the certificate's RS256 +
        ML-DSA-65 signatures are verified via protocol.hybrid.verify_hybrid
        (the same 3A production verifier). Public keys are supplied by the
        caller (rs256_pub_pem, mldsa65_pub_raw).

    Trust store (FINDING-3D-03):
        When trust_store is supplied (a TrustStatusStore), it is used to
        resolve trust status instead of the in-memory trust_assertions list.
        The store's integrity gate participates in the resolution.

    Real manifest (FINDING-3D-02):
        When manifest_context is supplied, the acceptance path instantiates
        the production ExecutionManifest.from_intent(...). Otherwise no
        manifest is emitted (no parallel dict-shaped manifest).
    """

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

    # ── Stage 1.5: cryptographic verification (FINDING-3D-01) ───────
    if require_crypto_verification:
        if rs256_pub_pem is None or mldsa65_pub_raw is None:
            stages["crypto"] = "missing_keys"
            return _fail(
                E2EOutcome.REJECTED_CRYPTO,
                "crypto verification required but public keys not supplied",
                stages=stages, envelope_bytes=envelope_bytes)
        cert_wo_sigs = {k: v for k, v in certificate.items() if k != "signatures"}
        sigs = certificate.get("signatures") or []
        try:
            vr = verify_hybrid(
                cert_wo_sigs, sigs, ["RS256", "ML-DSA-65"],
                rs256_pub_pem=rs256_pub_pem,
                mldsa65_pub_raw=mldsa65_pub_raw,
            )
        except HybridVerifyError as e:
            stages["crypto"] = "rejected"
            return _fail(E2EOutcome.REJECTED_CRYPTO,
                         f"hybrid verify error: {e}",
                         stages=stages, envelope_bytes=envelope_bytes)
        except Exception as e:
            stages["crypto"] = "rejected"
            return _fail(E2EOutcome.REJECTED_CRYPTO,
                         f"crypto verify failed: {e}",
                         stages=stages, envelope_bytes=envelope_bytes)
        if vr.get("status") != "VALID":
            stages["crypto"] = "rejected"
            return _fail(E2EOutcome.REJECTED_CRYPTO,
                         f"hybrid verify not VALID: {vr}",
                         stages=stages, envelope_bytes=envelope_bytes)
        stages["crypto"] = "verified"
    else:
        stages["crypto"] = "skipped"

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
    # FINDING-3D-03: prefer the real TrustStatusStore when supplied.
    known_ids = frozenset({authority.authority_id})
    if trust_store is not None:
        try:
            resolved = trust_store.resolve_at(
                authority.authority_id,
                now,
                known_authority_ids=known_ids,
            )
        except TypeError:
            resolved = trust_store.resolve_at(authority.authority_id, now)
        stages["trust_source"] = "store"
    else:
        resolver = TrustStatusResolver()
        assertions_in = trust_assertions or []
        resolved = resolver.resolve_at(
            authority.authority_id, now, assertions_in,
            known_authority_ids=known_ids,
        )
        stages["trust_source"] = "in_memory"
    if resolved.outcome is ResolutionOutcome.UNKNOWN:
        stages["trust"] = "rejected"
        # Propagate the resolver's own reason so callers can see WHY
        # (e.g., integrity_check_failed).
        return _fail(E2EOutcome.REJECTED_TRUST,
                     f"trust status unknown (fail-closed): {resolved.reason}",
                     stages=stages,
                     provenance={"resolved_reason": resolved.reason},
                     envelope_bytes=envelope_bytes)
    if resolved.outcome is ResolutionOutcome.CONFLICT:
        stages["trust"] = "rejected"
        return _fail(E2EOutcome.REJECTED_TRUST,
                     f"trust status conflict: {resolved.reason}",
                     stages=stages,
                     provenance={"resolved_reason": resolved.reason},
                     envelope_bytes=envelope_bytes)
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
    # FINDING-3D-02: when manifest_context is supplied, instantiate the
    # real ExecutionManifest.from_intent(...). No parallel dict shape.
    manifest_obj = None
    if manifest_context is not None:
        try:
            from enterpriseguard.adie.execution_manifest import (
                ManifestStatus, ExecutionEligibility,
                DecisionReference, ExecutionManifest,
                MANIFEST_CONTRACT_VERSION,
            )
            from enterpriseguard.adie.execution_contract import (
                ExecutionIntent, ExecutionMode, ApprovalRequirement,
            )
            ctx = dict(manifest_context)
            ref = DecisionReference(decision_id=proposed.decision_id)
            intent = ExecutionIntent(
                execution_intent_id=ctx.get(
                    "execution_intent_id",
                    f"intent-{proposed.decision_id}"),
                decision_id=proposed.decision_id,
                playbook_id=ctx.get("playbook_id", "playbook-default"),
                mode=ctx.get("mode", ExecutionMode.DRY_RUN),
                approval_requirement=ctx.get(
                    "approval_requirement", ApprovalRequirement.NOT_REQUIRED),
                actions=tuple(),
            )
            manifest_obj = ExecutionManifest.from_intent(
                manifest_id=ctx.get("manifest_id",
                                    f"manifest-{proposed.decision_id}"),
                manifest_version=ctx.get(
                    "manifest_version", MANIFEST_CONTRACT_VERSION),
                intent=intent,
                event_id=ctx.get("event_id", "event-default"),
                policy_id=proposed.policy_id,
                policy_evaluation_id=ctx.get("policy_evaluation_id",
                                             f"peval-{proposed.decision_id}"),
                policy_version=ctx.get("policy_version", "1.0"),
                prediction_id=proposed.prediction_id,
                playbook_version=ctx.get("playbook_version", "1.0"),
                state_id=ctx.get("state_id", "state-default"),
                state_version=ctx.get("state_version", "1.0"),
                tenant_id=ctx.get("tenant_id", "tenant-default"),
                environment_id=ctx.get("environment_id", "env-default"),
                resource_scope=ctx.get("resource_scope",
                                       {"resource_id": target_resource_id}),
                decision_reference=ref,
                decision_lifecycle=proposed.lifecycle.value,
                decision_rationale=proposed.rationale,
                decision_reason_codes=tuple(proposed.reason_codes),
                capability=ctx.get("capability", "UNSPECIFIED"),
                adapter_reference=ctx.get("adapter_reference", "UNSPECIFIED"),
                governance_metadata={
                    "trust_status": resolved.status.value,
                    "authority_id": proposed.authority_id,
                },
            )
        except Exception as e:
            stages["manifest"] = "rejected"
            return _fail(E2EOutcome.REJECTED_MANIFEST, str(e),
                         stages=stages, envelope_bytes=envelope_bytes)
        stages["manifest"] = "emitted"
    else:
        stages["manifest"] = "not_emitted_no_context"

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
