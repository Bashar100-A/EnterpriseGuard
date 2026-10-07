#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("E2E manifest boundary")

cert = make_cert("mb-1")
evidence = make_evidence()
authority = make_authority()

# Accept -> manifest emitted
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)

h.check("M01 accepted", r.outcome is E2EOutcome.ACCEPTED)
h.check("M02 manifest not None", r.manifest is not None)
m = r.manifest
h.check("M03 decision_lifecycle=AUTHORIZED",
        m.get("decision_lifecycle") == "authorized")
h.check("M04 authorization_status=AUTHORIZED",
        m.get("authorization_status") == "authorized")
h.check("M05 trust_status=active", m.get("trust_status") == "active")
h.check("M06 authority_id present", m.get("authority_id") == authority.authority_id)
h.check("M07 policy_id present", m.get("policy_id") is not None)
h.check("M08 prediction_id present", m.get("prediction_id") is not None)
h.check("M09 executes_security_actions=False",
        m.get("executes_security_actions") is False)
h.check("M10 decision_reference present", "decision_reference" in m)

# Reject -> no manifest
r2 = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("M11 rejected has no manifest", r2.manifest is None)
h.check("M12 rejected has no decision", r2.decision is None)

# Policy deny -> no manifest
r3 = evaluate_end_to_end(
    certificate=cert, evidence=make_evidence(policy_allowed=False),
    authority=authority, scope="decide", trust_assertions=[],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("M13 policy-denied has no manifest", r3.manifest is None)

# No manifest content ever sets executes_security_actions=True
for out in [r, r2, r3]:
    if out.manifest is not None:
        h.check("M14 manifest never executes",
                out.manifest.get("executes_security_actions") is False)

h.finish()
