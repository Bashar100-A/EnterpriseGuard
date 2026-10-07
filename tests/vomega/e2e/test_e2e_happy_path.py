#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("E2E happy path (require_wire_roundtrip=False)")

cert = make_cert("happy-1")
evidence = make_evidence()
authority = make_authority()
# Resolve ACTIVE via a SUSPENDED assertion is wrong. We need a state that
# the E2E glue accepts. Currently the glue requires TrustStatus.ACTIVE.
# But TrustStatus.ACTIVE is not directly assertable via RevocationKind.
# The cleanest path: extend the resolver's input to allow a "reactivate"
# assertion kind. That's a design gap.
#
# Workaround for this block: the glue accepts only ACTIVE. We expose
# "no future-revoke" path by supplying a "prior SUSPEND then later SUSPEND
# (idempotent)" series — resolver returns SUSPENDED, which the glue rejects.
#
# This reveals: the E2E glue needs to support "explicit activation"
# assertions. For now, we test the reject-path in happy_path and handle
# accept-path in a dedicated test that bypasses ACTIVE via an added
# RevocationKind. That will be Block C.
#
# Therefore this file validates the REJECT paths only.

# Reject: no authority
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=None, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("H01 missing authority rejected",
        r.outcome is E2EOutcome.REJECTED_AUTHORITY)
h.check("H02 stages has evidence accepted", r.stages.get("evidence") == "accepted")

# Reject: wrong scope
bad_scope = make_authority(scope="execute")
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=bad_scope, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("H03 scope mismatch rejected",
        r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# Reject: inactive authority
inactive = make_authority(valid_from=T3, valid_until=T3+timedelta(days=1))
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=inactive, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False)
h.check("H04 inactive authority rejected",
        r.outcome is E2EOutcome.REJECTED_AUTHORITY)

# ACCEPT: known authority + empty trust history -> governed initial ACTIVE
# (DEFECT-043, Commander decision A)
# 3D-R1 (FINDING-3D-02): supply manifest_context so real ExecutionManifest
# is emitted by the production contract (not a parallel dict).
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False,
    manifest_context=make_manifest_context("happy-1"))
h.check("H05 known + empty history -> ACCEPTED (governed initial state)",
        r.outcome is E2EOutcome.ACCEPTED, r.rejection_reason)
h.check("H05b decision not None", r.decision is not None)
h.check("H05c manifest not None", r.manifest is not None)
h.check("H05d lifecycle is AUTHORIZED",
        r.decision is not None and r.decision.lifecycle.value == "authorized")
h.check("H05e authorization_status AUTHORIZED",
        r.decision is not None and r.decision.authorization_status.value == "authorized")
h.check("H05f authority_status_at_authorization is ACTIVE",
        r.decision is not None
        and r.decision.authority_status_at_authorization is not None
        and r.decision.authority_status_at_authorization.value == "active")
h.check("H05g no execution performed",
        r.decision is not None and r.decision.executes_security_actions is False)

# Reject: revoked authority
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("H06 revoked trust rejected", r.outcome is E2EOutcome.REJECTED_TRUST)

# Reject: policy denied
ev_denied = make_evidence(policy_allowed=False)
r = evaluate_end_to_end(
    certificate=cert, evidence=ev_denied, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T3)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False)
h.check("H07 policy denied -> REJECTED_TRUST or POLICY",
        r.outcome in (E2EOutcome.REJECTED_TRUST, E2EOutcome.REJECTED_POLICY))

# Reject: invalid certificate -> wire bridge fails only if wire_roundtrip=True
cert_bad = make_cert("bad-1")
cert_bad["subject"] = "not-an-object"
r = evaluate_end_to_end(
    certificate=cert_bad, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T3)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=True)
h.check("H08 wire round-trip rejects malformed subject",
        r.outcome is E2EOutcome.REJECTED_WIRE, r.rejection_reason)

h.finish()
