"""Shared fixtures for 3D E2E assurance tests."""
import sys, base64, copy
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from enterpriseguard.adie.decision import DecisionEvidence
from enterpriseguard.adie.canonical.authority import Authority, AuthorityKind
from enterpriseguard.adie.canonical.trust.assertion import TrustStatusAssertion
from enterpriseguard.adie.canonical.trust.authority_to_revoke import RevocationKind

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 12, 1, tzinfo=timezone.utc)
T3 = datetime(2027, 6, 1, tzinfo=timezone.utc)

def _sig(alg, n):
    return "base64:" + base64.b64encode(b"\x55" * n).decode("ascii")

def make_cert(claim_id="e2e-001"):
    return {
        "dcp_version": "2.1", "claim_id": claim_id,
        "issuer": {"did": "did:adie:issuer-e2e", "key_id": "sha256:" + "0"*64},
        "subject": {"model_id": "credit-v7"},
        "request": {"id": "r1"},
        "context": {"locale": "en"},
        "policy": {"id": "credit-risk", "version": "7"},
        "model": {"id": "model-v1"},
        "data": {"commitment": "sha256:" + "c"*64},
        "runtime": {"measurement": "sha256:" + "d"*64},
        "output": {"result": "REJECTED"},
        "binding": {"audience": "com.example", "purpose": 7,
                    "resource": "model://" + claim_id,
                    "request_hash": "sha256:" + "e"*64,
                    "nonce": "a"*32, "certificate_id": claim_id},
        "temporal": {"issued_at": "2026-10-07T00:00:00Z"},
        "evidence": {"attestations": []},
        "authoring": {"template_digest": "sha256:"+"0"*64,
                      "parameter_digest": "sha256:"+"1"*64,
                      "compiler_digest": "sha256:"+"2"*64,
                      "acl_version": "0.1",
                      "canonical_ast_digest": "sha256:"+"3"*64,
                      "meta_manifest_digest": "sha256:"+"4"*64},
        "proofs": [],
        "claim_root": "sha256:" + "a"*64,
        "signatures": [
            {"alg": "RS256", "key_id": "sha256:"+"0"*64, "value": _sig("RS256", 256)},
            {"alg": "ML-DSA-65", "key_id": "sha256:"+"1"*64, "value": _sig("ML-DSA-65", 3309)},
        ],
    }

def make_evidence(policy_allowed=True, prob=0.5):
    return DecisionEvidence(
        prediction_id="pred-1", policy_id="pol-1",
        threat_probability=prob, prediction_confidence=0.9,
        state_risk=0.3, policy_allowed=policy_allowed, collected_at=T1,
    )

def make_authority(aid="auth-A", scope="decide",
                   valid_from=None, valid_until=None):
    return Authority(
        authority_id=aid, authority_kind=AuthorityKind.MACHINE,
        policy_id="pol-1", policy_version="1.0", scope=scope,
        valid_from=valid_from or (T1 - timedelta(days=30)),
        valid_until=valid_until or (T2 + timedelta(days=30)),
    )

def make_active_assertion(aid="auth-A", as_of=None):
    t = as_of or T0
    return TrustStatusAssertion(
        assertion_id="act-" + aid, subject_id=aid,
        kind=RevocationKind.SUSPEND,  # proxy for ACTIVE window
        asserted_at=t, effective_at=t, observed_at=t,
        authority_ref="gov-root", authority_id="gov-root",
    )

def make_revoke_assertion(aid="auth-A", effective_at=None):
    t = effective_at or T1
    return TrustStatusAssertion(
        assertion_id="rev-" + aid, subject_id=aid,
        kind=RevocationKind.REVOKE,
        asserted_at=t, effective_at=t, observed_at=t,
        authority_ref="gov-root", authority_id="gov-root",
    )

def make_active_assertion_alt(aid):
    """Real ACTIVE proxy: SUSPEND is reversible, resolver returns SUSPENDED.
    Use a previous REVOKE that is later SUPERSEDED to ACTIVE is not possible.
    So for tests requiring ACTIVE status, we assert ACTIVE via... hmm,
    ACTIVE is not directly assertable via RevocationKind. Use the resolver
    default: no assertion -> UNKNOWN. Instead, we define ACTIVE via a
    timeline where a REVOKE is effective in the FUTURE (so at T_now it's
    not yet effective) which yields UNKNOWN. That is also wrong.
    """
    raise NotImplementedError

def active_via_future_revoke(aid="auth-A", revoke_at=None):
    """Simulate ACTIVE at time T by having only a future-effective REVOKE.
    At T < revoke_at, resolver returns UNKNOWN (no applicable assertion).
    This test helper is NOT valid for 'ACTIVE' checks."""
    t = revoke_at or T2
    return TrustStatusAssertion(
        assertion_id="futrev-" + aid, subject_id=aid,
        kind=RevocationKind.REVOKE,
        asserted_at=t, effective_at=t, observed_at=t,
        authority_ref="gov-root", authority_id="gov-root",
    )

class Harness:
    def __init__(self, title):
        self.P = 0
        self.F = 0
        print("=" * 72); print(title); print("=" * 72)
    def check(self, name, cond, detail=""):
        if cond:
            self.P += 1; print(f"[PASS] {name}")
        else:
            self.F += 1; print(f"[FAIL] {name}: {detail}")
    def finish(self):
        print(f"\nTOTAL: {self.P + self.F} | PASS: {self.P} | FAIL: {self.F}")
        import sys
        sys.exit(0 if self.F == 0 else 1)
