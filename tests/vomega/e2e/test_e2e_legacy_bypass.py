#!/usr/bin/env python3
import sys, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)
from enterpriseguard.adie.canonical.compat_decision_b import (
    legacy_contract_to_neutral, LegacyAdapterError)

h = Harness("E2E legacy bypass attempts")

cert = make_cert("leg-1")
evidence = make_evidence()
authority = make_authority()

# 1. Legacy B adapter does not grant canonical authority
class FakeStatus:
    def __init__(self, v): self.value = v
class FakeLegacy:
    def __init__(self):
        self.decision_id="b"; self.evaluation_id="e"; self.policy_id="p"
        self.status=FakeStatus("authorized"); self.authorized=True
        self.target_resource_id="r"; self.expires_at=None

neutral = legacy_contract_to_neutral(FakeLegacy())
h.check("LBY01 legacy emits no authority_id", "authority_id" not in neutral)
h.check("LBY02 legacy claim preserved as legacy_authorized_claim",
        neutral["legacy_authorized_claim"] is True)

# 2. Legacy neutral dict cannot be fed to e2e as authority
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=neutral, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("LBY03 neutral dict rejected as authority",
        r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# 3. String authority rejected
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority="authority-A", scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("LBY04 string authority rejected",
        r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# 4. Dict authority rejected
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence,
    authority={"authority_id": "x", "scope": "decide"}, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("LBY05 dict authority rejected",
        r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# 5. None authority
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=None, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("LBY06 None authority rejected",
        r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# 6. Evidence-like dict is not DecisionEvidence
r = evaluate_end_to_end(
    certificate=cert, evidence={"prediction_id": "x"}, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("LBY07 dict evidence rejected",
        r.outcome is E2EOutcome.REJECTED_EVIDENCE)

# 7-10. Certificate structure variations
for i, mutation in enumerate(["claim_id", "dcp_version", "binding", "claim_root"]):
    c = copy.deepcopy(cert)
    if mutation == "binding":
        c.pop("binding", None)  # wire requires binding
    elif mutation == "claim_root":
        c["claim_root"] = "not-hex"
    else:
        c.pop(mutation, None)
    r = evaluate_end_to_end(
        certificate=c, evidence=evidence, authority=authority, scope="decide",
        trust_assertions=[make_revoke_assertion(effective_at=T3)],
        at=T1, target_resource_id="res-1", require_wire_roundtrip=True)
    # All should fail somewhere (wire or trust UNKNOWN)
    h.check(f"LBY{i+8:02d} mutated {mutation} rejected",
            r.outcome is not E2EOutcome.ACCEPTED)

h.finish()
