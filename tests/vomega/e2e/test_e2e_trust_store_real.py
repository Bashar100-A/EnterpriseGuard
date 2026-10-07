#!/usr/bin/env python3
"""3D-R1 FINDING-3D-03: real TrustStatusStore in E2E path.

The E2E acceptance path must exercise the production TrustStatusStore,
not an in-memory assertion list.
"""
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)
from enterpriseguard.adie.canonical.trust.history import TrustStatusStore
from enterpriseguard.adie.canonical.trust.authority_to_revoke import (
    RevocationAuthority, RevocationKind)

h = Harness("3D-R1 F-03: real TrustStatusStore in E2E")

cert = make_cert("ts-1")
evidence = make_evidence()
authority = make_authority()
ctx = make_manifest_context("ts-1")

with tempfile.TemporaryDirectory() as td:
    logp = Path(td) / "trust.jsonl"
    store = TrustStatusStore(log_path=logp)

    ra = RevocationAuthority(
        revocation_authority_id="ra-1",
        revocation_authority_ref="gov-root",
        permitted_kinds=frozenset({RevocationKind.REVOKE, RevocationKind.SUSPEND}),
        revocable_subject_ids=frozenset({"auth-A"}),
        valid_from=T1 - timedelta(days=30),
        valid_until=T1 + timedelta(days=30),
    )

    # TS01: store empty -> governed initial ACTIVE via store path -> ACCEPTED
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=store)
    h.check("TS01 empty store -> ACCEPTED (initial state)",
            r.outcome is E2EOutcome.ACCEPTED, r.rejection_reason)
    h.check("TS01b stages trust_source=store",
            r.stages.get("trust_source") == "store")
    h.check("TS01c manifest is real ExecutionManifest",
            r.manifest is not None and r.manifest.__class__.__name__ == "ExecutionManifest")

    # TS02: append revoke -> E2E path sees it via store -> REJECTED_TRUST
    rev = make_revoke_assertion("auth-A", effective_at=T1 - timedelta(hours=1))
    store.append(rev, revocation_authority=ra, authorization_time=T1)
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=store)
    h.check("TS02 store sees revoke -> REJECTED_TRUST",
            r.outcome is E2EOutcome.REJECTED_TRUST, r.rejection_reason)

    # TS03: historical query via store, before effective_at -> ACCEPTED
    early = T1 - timedelta(days=15)
    # Add an "activation" via SUSPEND to make history nontrivial? No — we
    # instead demonstrate: at T_before_revoke, no applicable assertion,
    # known -> governed initial ACTIVE -> ACCEPTED.
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=early,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=store)
    h.check("TS03 historical query before revoke -> ACCEPTED",
            r.outcome is E2EOutcome.ACCEPTED, r.rejection_reason)

    # TS04: append suspend effective at T1+h -> still REVOKED at T1 (revoke wins by timestamp)
    sus = TrustStatusAssertion(
        assertion_id="sus-1", subject_id="auth-A",
        kind=RevocationKind.SUSPEND,
        asserted_at=T1, effective_at=T1 + timedelta(hours=2),
        observed_at=T1,
        authority_ref="gov-root", authority_id="ra-1")
    store.append(sus, revocation_authority=ra, authorization_time=T1)

    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=store)
    h.check("TS04 still REVOKED at T1 (suspend effective later)",
            r.outcome is E2EOutcome.REJECTED_TRUST, r.rejection_reason)

    # TS05: integrity valid
    vi = store.verify_integrity()
    h.check("TS05 integrity valid", vi["valid"] is True)
    h.check("TS05b checked 2 assertions", vi["assertions_checked"] == 2)

    # TS06: tamper store -> E2E path sees integrity failure -> UNKNOWN -> REJECTED_TRUST
    txt = logp.read_text()
    tampered = txt.replace('"revoke"', '"expire"')
    logp.write_text(tampered)
    store_reopened = TrustStatusStore(log_path=logp)
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=store_reopened)
    h.check("TS06 tampered store -> REJECTED_TRUST (integrity fail-closed)",
            r.outcome is E2EOutcome.REJECTED_TRUST, r.rejection_reason)
    h.check("TS06b reason mentions integrity",
            "integrity" in r.rejection_reason)

    # TS07: TrustStatusStore without log_path (in-memory) still participates
    mem_store = TrustStatusStore()
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=mem_store)
    h.check("TS07 in-memory store: empty -> ACCEPTED",
            r.outcome is E2EOutcome.ACCEPTED)

    # TS08: two E2E runs against same store are deterministic
    r_a = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=mem_store)
    r_b = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=None, at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        manifest_context=ctx, trust_store=mem_store)
    h.check("TS08 store-based E2E deterministic",
            r_a.outcome == r_b.outcome and r_a.decision.decision_id == r_b.decision.decision_id)

h.finish()
