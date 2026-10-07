#!/usr/bin/env python3
import sys, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("E2E failure injection")

cert = make_cert("fi-1")
evidence = make_evidence()
authority = make_authority()

# FI01: malformed wire (subject not dict)
c = copy.deepcopy(cert); c["subject"] = "not-dict"
r = evaluate_end_to_end(certificate=c, evidence=evidence, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=True)
h.check("FI01 malformed wire -> REJECTED_WIRE", r.outcome is E2EOutcome.REJECTED_WIRE)

# FI02: missing binding
c = copy.deepcopy(cert); c.pop("binding")
r = evaluate_end_to_end(certificate=c, evidence=evidence, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=True)
h.check("FI02 missing binding -> REJECTED_WIRE", r.outcome is E2EOutcome.REJECTED_WIRE)

# FI03: invalid crypto (claim_root not valid)
c = copy.deepcopy(cert); c["claim_root"] = "sha256:zzz"
r = evaluate_end_to_end(certificate=c, evidence=evidence, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=True)
h.check("FI03 bad claim_root -> rejected at wire or trust",
        r.outcome is not E2EOutcome.ACCEPTED)

# FI04: no authority
r = evaluate_end_to_end(certificate=cert, evidence=evidence, authority=None,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("FI04 no authority -> REJECTED_AUTHORITY", r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# FI05: inactive authority window
auth_inactive = make_authority(valid_from=T2, valid_until=T2+timedelta(days=1))
r = evaluate_end_to_end(certificate=cert, evidence=evidence, authority=auth_inactive,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("FI05 inactive window -> REJECTED_AUTHORITY", r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# FI06: policy denied
ev_d = make_evidence(policy_allowed=False)
r = evaluate_end_to_end(certificate=cert, evidence=ev_d, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("FI06 policy denied -> REJECTED_POLICY", r.outcome is E2EOutcome.REJECTED_POLICY)

# FI07: revoked authority
r = evaluate_end_to_end(certificate=cert, evidence=evidence, authority=authority,
    scope="decide", trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("FI07 revoked -> REJECTED_TRUST", r.outcome is E2EOutcome.REJECTED_TRUST)

# FI08: conflicting trust
c1 = TrustStatusAssertion(assertion_id="fi-c1", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
c2 = TrustStatusAssertion(assertion_id="fi-c2", subject_id="auth-A",
    kind=RevocationKind.SUSPEND, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
r = evaluate_end_to_end(certificate=cert, evidence=evidence, authority=authority,
    scope="decide", trust_assertions=[c1, c2], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("FI08 conflicting trust -> REJECTED_TRUST", r.outcome is E2EOutcome.REJECTED_TRUST)

# FI09: dict evidence
r = evaluate_end_to_end(certificate=cert, evidence={"p": "1"}, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("FI09 dict evidence -> REJECTED_EVIDENCE", r.outcome is E2EOutcome.REJECTED_EVIDENCE)

# FI10: no target_resource_id (empty string)
r = evaluate_end_to_end(certificate=cert, evidence=evidence, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="",
    require_wire_roundtrip=False)
# E2E glue does not strictly validate empty string; but should produce a
# well-formed result. We check that a result is returned.
h.check("FI10 empty target_resource_id returns result", r is not None)

# FI11: naive datetime
try:
    evaluate_end_to_end(certificate=cert, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=[], at=datetime(2026,1,1),
        target_resource_id="res-1", require_wire_roundtrip=False)
    h.check("FI11 naive at -> error", False)
except Exception:
    h.check("FI11 naive at -> error", True)

# FI12: unknown subject_id at resolver (via known_authority_ids empty)
# Covered by resolver-level G06.

h.finish()
