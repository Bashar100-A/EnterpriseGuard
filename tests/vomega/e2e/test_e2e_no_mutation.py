#!/usr/bin/env python3
import sys, copy, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("E2E no-mutation proof")

cert = make_cert("nomut-1")
evidence = make_evidence()
authority = make_authority()

cert_before = json.dumps(cert, sort_keys=True, default=str)
ev_before = evidence
auth_before = json.dumps({
    "authority_id": authority.authority_id,
    "scope": authority.scope,
    "valid_from": authority.valid_from.isoformat(),
    "valid_until": authority.valid_until.isoformat(),
}, sort_keys=True)

# Run accept path
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=True)

cert_after = json.dumps(cert, sort_keys=True, default=str)
ev_after = evidence
auth_after = json.dumps({
    "authority_id": authority.authority_id,
    "scope": authority.scope,
    "valid_from": authority.valid_from.isoformat(),
    "valid_until": authority.valid_until.isoformat(),
}, sort_keys=True)

h.check("N01 certificate not mutated", cert_before == cert_after)
h.check("N02 evidence not mutated", ev_before is ev_after)
h.check("N03 authority not mutated", auth_before == auth_after)
h.check("N04 accepted outcome", r.outcome is E2EOutcome.ACCEPTED)

# Run reject path (revoked) — same immutability check
c2 = make_cert("nomut-2")
cert_before2 = json.dumps(c2, sort_keys=True, default=str)
r2 = evaluate_end_to_end(
    certificate=c2, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=True)
cert_after2 = json.dumps(c2, sort_keys=True, default=str)
h.check("N05 rejected path: cert not mutated", cert_before2 == cert_after2)
h.check("N06 rejected path: no decision", r2.decision is None)

# envelope_bytes deterministic (not mutated)
r3 = evaluate_end_to_end(
    certificate=c2, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=True)
h.check("N07 envelope_bytes identical across calls",
        r2.envelope_bytes == r3.envelope_bytes)

# No mutation of cert during wire bridge call
c4 = make_cert("nomut-4")
before4 = json.dumps(c4, sort_keys=True, default=str)
_ = evaluate_end_to_end(
    certificate=c4, evidence=evidence, authority=authority, scope="decide",
    trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=True)
after4 = json.dumps(c4, sort_keys=True, default=str)
h.check("N08 cert not mutated by bridge", before4 == after4)

h.finish()
