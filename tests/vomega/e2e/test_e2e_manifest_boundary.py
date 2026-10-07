#!/usr/bin/env python3
"""E2E manifest boundary — 3D-R1 uses real ExecutionManifest."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)
from enterpriseguard.adie.execution_manifest import (
    ExecutionManifest, ManifestStatus, ExecutionEligibility)

h = Harness("E2E manifest boundary (real ExecutionManifest)")

cert = make_cert("mb-1")
evidence = make_evidence()
authority = make_authority()
ctx = make_manifest_context("mb-1")

# Accept + real manifest
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False, manifest_context=ctx)

h.check("M01 accepted", r.outcome is E2EOutcome.ACCEPTED, r.rejection_reason)
h.check("M02 manifest is ExecutionManifest instance",
        isinstance(r.manifest, ExecutionManifest),
        type(r.manifest).__name__ if r.manifest is not None else "None")

if r.manifest is not None:
    m = r.manifest
    h.check("M03 decision_id matches", m.decision_id == r.decision.decision_id)
    h.check("M04 decision_lifecycle=AUTHORIZED", m.decision_lifecycle == "authorized")
    h.check("M05 decision_reference points at canonical",
            m.decision_reference.contract_type == "adie.decision.DecisionContract")
    h.check("M06 decision_reference.version 3.0.1",
            m.decision_reference.contract_version == "3.0.1")
    h.check("M07 policy_id present", m.policy_id == "pol-1")
    h.check("M08 prediction_id present", m.prediction_id == "pred-1")
    h.check("M09 authority_id in governance_metadata",
            m.governance_metadata.get("authority_id") == authority.authority_id)
    h.check("M10 trust_status in governance_metadata",
            m.governance_metadata.get("trust_status") == "active")
    h.check("M11 status is DRAFT",
            m.status is ManifestStatus.DRAFT)
    h.check("M12 eligibility NOT_ELIGIBLE",
            m.eligibility is ExecutionEligibility.NOT_ELIGIBLE)
    d = m.to_dict()
    h.check("M13 to_dict returns dict", isinstance(d, dict))
    h.check("M14 no execution field true",
            d.get("capability") != "EXECUTE" and "executes_security_actions" not in d)
else:
    for i in range(3, 15):
        h.check(f"M{i:02d} skipped (no manifest)", False)

# No context -> no manifest
r2 = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("M15 no context -> manifest None (no parallel dict)",
        r2.manifest is None)
h.check("M15b acceptance still valid", r2.outcome is E2EOutcome.ACCEPTED)

# Reject -> no manifest (even with context)
r3 = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False,
    manifest_context=ctx)
h.check("M16 rejected has no manifest", r3.manifest is None)
h.check("M17 rejected has no decision", r3.decision is None)

# Policy deny -> no manifest
r4 = evaluate_end_to_end(
    certificate=cert, evidence=make_evidence(policy_allowed=False),
    authority=authority, scope="decide", trust_assertions=[],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False,
    manifest_context=ctx)
h.check("M18 policy-denied has no manifest", r4.manifest is None)

h.finish()
