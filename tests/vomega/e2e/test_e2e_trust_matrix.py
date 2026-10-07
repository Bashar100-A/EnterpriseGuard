#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)
from enterpriseguard.adie.canonical.trust.assertion import TrustStatusAssertion
from enterpriseguard.adie.canonical.trust.authority_to_revoke import RevocationKind

h = Harness("E2E trust status matrix (all 4 kinds x 3 timings)")

cert = make_cert("tm-1")
evidence = make_evidence()
authority = make_authority()

# RevocationKind -> expected TrustStatus at T > effective
KIND_TO_STATUS = {
    RevocationKind.SUSPEND: "suspended",
    RevocationKind.REVOKE: "revoked",
    RevocationKind.SUPERSEDE: "superseded",
    RevocationKind.EXPIRE: "expired",
}

for i, (kind, expected_status) in enumerate(KIND_TO_STATUS.items()):
    a = TrustStatusAssertion(
        assertion_id=f"k{i}", subject_id="auth-A", kind=kind,
        asserted_at=T0, effective_at=T0, observed_at=T0,
        authority_ref="gov", authority_id="gov")
    # Not ACTIVE -> rejected
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority, scope="decide",
        trust_assertions=[a], at=T1, target_resource_id="res-1",
        require_wire_roundtrip=False)
    h.check(f"T{i+1:02d} {expected_status} -> REJECTED_TRUST",
            r.outcome is E2EOutcome.REJECTED_TRUST)
    h.check(f"T{i+1:02d}b provenance has trust_status",
            r.provenance.get("trust_status") == expected_status)

# Before effective_at -> governed initial state (ACTIVE) -> ACCEPTED
# (DEFECT-043: future-effective assertions do not apply retroactively)
for i, kind in enumerate(KIND_TO_STATUS.keys()):
    a = TrustStatusAssertion(
        assertion_id=f"pre-{i}", subject_id="auth-A", kind=kind,
        asserted_at=T2, effective_at=T2, observed_at=T2,
        authority_ref="gov", authority_id="gov")
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority, scope="decide",
        trust_assertions=[a], at=T1, target_resource_id="res-1",
        require_wire_roundtrip=False)
    h.check(f"T{i+5:02d} {kind.value} before-effective -> ACCEPTED",
            r.outcome is E2EOutcome.ACCEPTED, r.rejection_reason)

# After effective_at -> rejected for each kind (matrix verification)
for i, (kind, expected) in enumerate(KIND_TO_STATUS.items()):
    a = TrustStatusAssertion(
        assertion_id=f"post-{i}", subject_id="auth-A", kind=kind,
        asserted_at=T0, effective_at=T0, observed_at=T0,
        authority_ref="gov", authority_id="gov")
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority, scope="decide",
        trust_assertions=[a], at=T1, target_resource_id="res-1",
        require_wire_roundtrip=False)
    h.check(f"T{i+9:02d} {kind.value} after-effective -> REJECTED_TRUST",
            r.outcome is E2EOutcome.REJECTED_TRUST)

# Conflicting assertions -> CONFLICT -> fail closed
c1 = TrustStatusAssertion(assertion_id="c1", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
c2 = TrustStatusAssertion(assertion_id="c2", subject_id="auth-A",
    kind=RevocationKind.SUSPEND, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[c1, c2], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("T09 conflict -> REJECTED_TRUST", r.outcome is E2EOutcome.REJECTED_TRUST)
h.check("T09b conflict reason mentions conflict",
        "conflict" in r.rejection_reason.lower())

h.finish()
