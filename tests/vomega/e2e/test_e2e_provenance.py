#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("E2E provenance")

cert = make_cert("prov-1")
evidence = make_evidence()
authority = make_authority()

# Rejected paths: no provenance
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=None, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("P01 missing authority -> no decision",
        r.decision is None and r.manifest is None)

# Rejected: trust conflict -> has provenance with reason
c1 = TrustStatusAssertion(assertion_id="p1", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
c2 = TrustStatusAssertion(assertion_id="p2", subject_id="auth-A",
    kind=RevocationKind.SUSPEND, asserted_at=T0, effective_at=T0, observed_at=T0,
    authority_ref="gov", authority_id="gov")
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[c1, c2], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("P02 conflict -> no decision", r.decision is None)

# Rejected trust: reason mentions status
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("P03 rejected trust has provenance trust_status",
        r.provenance.get("trust_status") == "revoked")
h.check("P04 rejected trust has no manifest", r.manifest is None)
h.check("P05 rejected trust has no decision", r.decision is None)

# Rejected authority: stages recorded
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=None, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("P06 stages includes evidence accepted",
        r.stages.get("evidence") == "accepted")
h.check("P07 stages includes authority rejected",
        r.stages.get("authority") == "rejected")
h.check("P08 stages has no trust", "trust" not in r.stages)

# to_dict on rejected: no fabricated IDs
d = r.to_dict()
h.check("P09 to_dict decision is None", d["decision"] is None)
h.check("P10 to_dict manifest is None", d["manifest"] is None)
h.check("P11 to_dict provenance is dict", isinstance(d["provenance"], dict))

h.finish()
