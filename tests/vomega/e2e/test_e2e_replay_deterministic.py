#!/usr/bin/env python3
import sys, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("E2E deterministic replay")

cert = make_cert("rep-1")
evidence = make_evidence()
authority = make_authority()

# 20x replay: same inputs -> same result (ACCEPTED path)
for i in range(20):
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority, scope="decide",
        trust_assertions=[], at=T1, target_resource_id="res-1",
        require_wire_roundtrip=False)
    d = r.to_dict()
    h.check(f"R{i+1:02d} accepted", r.outcome is E2EOutcome.ACCEPTED)
    h.check(f"R{i+1:02d}b provenance stable",
            d["provenance"].get("trust_status_at_authorization") == "active")
    if i > 0:
        h.check(f"R{i+1:02d}c decision_id stable",
                d["decision"]["decision_id"] == prev_id)
    prev_id = d["decision"]["decision_id"]

# 10x replay: rejection path (revoked)
for i in range(10):
    r = evaluate_end_to_end(
        certificate=cert, evidence=evidence, authority=authority, scope="decide",
        trust_assertions=[make_revoke_assertion(effective_at=T0)],
        at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
    h.check(f"R{i+21:02d} rejected", r.outcome is E2EOutcome.REJECTED_TRUST)

# Divergence: alter ONE input -> different outcome
r_ok = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
r_rev = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("R31 single-input change -> divergence",
        r_ok.outcome is E2EOutcome.ACCEPTED and r_rev.outcome is E2EOutcome.REJECTED_TRUST)

# Divergence: alter evidence policy_allowed
ev_denied = make_evidence(policy_allowed=False)
r_den = evaluate_end_to_end(
    certificate=cert, evidence=ev_denied, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("R32 evidence policy-denied -> divergence",
        r_den.outcome is E2EOutcome.REJECTED_POLICY)

# Divergence: alter authority scope
auth_bad = make_authority(scope="execute")
r_scope = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=auth_bad, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("R33 authority scope -> divergence",
        r_scope.outcome is E2EOutcome.REJECTED_AUTHORITY)

h.finish()
