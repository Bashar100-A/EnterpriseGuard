#!/usr/bin/env python3
import sys, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("E2E crypto/gov mismatch — cases A-F")

cert = make_cert("cgm-1")
evidence = make_evidence()
authority = make_authority()

# Case A: crypto-valid artifact (well-formed), revoked authority
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("CG-A01 revoked authority rejects", r.outcome is E2EOutcome.REJECTED_TRUST)
h.check("CG-A02 rejection_reason not empty", len(r.rejection_reason) > 0)

# Case B: invalid wire (malformed cert), active authority window
bad_cert = copy.deepcopy(cert)
bad_cert["subject"] = ["not","an","object"]
r = evaluate_end_to_end(
    certificate=bad_cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=True)
h.check("CG-B01 malformed cert rejected at wire",
        r.outcome is E2EOutcome.REJECTED_WIRE)

# Case C: valid cert + future-effective revocation -> governs as ACTIVE at T1
cert_c = make_cert("cgm-C")
cert_c["claim_id"] = "cgm-C"
r = evaluate_end_to_end(
    certificate=cert_c, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T3)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=True)
# Valid wire + future revoke does not yet apply -> governed initial ACTIVE
h.check("CG-C01 valid wire + future revoke -> ACCEPTED",
        r.outcome is E2EOutcome.ACCEPTED, r.rejection_reason)

# Case D: valid artifact + active authority + no trust history
# -> governed initial state = ACTIVE -> ACCEPTED
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("CG-D01 no-trust-history -> ACCEPTED (governed initial state)",
        r.outcome is E2EOutcome.ACCEPTED, r.rejection_reason)

# Case E: conflicting policy/trust assertion
c1 = TrustStatusAssertion(assertion_id="e1", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
c2 = TrustStatusAssertion(assertion_id="e2", subject_id="auth-A",
    kind=RevocationKind.SUSPEND, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[c1, c2], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("CG-E01 conflicting trust -> REJECTED_TRUST",
        r.outcome is E2EOutcome.REJECTED_TRUST)
h.check("CG-E02 conflict detected in reason",
        "conflict" in r.rejection_reason.lower())

# Case F: historical valid authorization + later revocation
# We can't easily simulate "historical authorization" in one call.
# Instead: verify that a REVOKE with effective_at in the past correctly
# invalidates a current call, and a REVOKE effective in future does not.
past_revoke = make_revoke_assertion(effective_at=T0)
future_revoke = make_revoke_assertion(effective_at=T3)
r_past = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[past_revoke], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
r_future = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[future_revoke], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("CG-F01 past revoke rejects at T1",
        r_past.outcome is E2EOutcome.REJECTED_TRUST)
h.check("CG-F02 future revoke does not apply at T1 (ACCEPTED via initial state)",
        r_future.outcome is E2EOutcome.ACCEPTED, r_future.rejection_reason)

h.finish()
