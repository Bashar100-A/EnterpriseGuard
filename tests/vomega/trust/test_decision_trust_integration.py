#!/usr/bin/env python3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from enterpriseguard.adie.decision import (
    DecisionContract, DecisionIntent, DecisionLifecycle, AuthorizationStatus, TrustStatus)
from enterpriseguard.adie.canonical.trust.assertion import TrustStatusAssertion
from enterpriseguard.adie.canonical.trust.authority_to_revoke import RevocationKind
from enterpriseguard.adie.canonical.trust.resolver import TrustStatusResolver
from enterpriseguard.adie.canonical.trust.status import TrustStatus as T

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

print("="*72); print("Decision × Trust integration"); print("="*72)
now = datetime.now(timezone.utc)
T1 = datetime(2026,1,1,tzinfo=timezone.utc)
T2 = datetime(2026,6,1,tzinfo=timezone.utc)
T3 = datetime(2027,1,1,tzinfo=timezone.utc)

# Contract records status-at-authorization
c = DecisionContract(
    decision_id="d1", intent=DecisionIntent.MONITOR,
    lifecycle=DecisionLifecycle.AUTHORIZED,
    decision_score=0.5, confidence=0.5,
    prediction_id="p", policy_id="pol", rationale="r", reason_codes=(),
    created_at=T1,
    authorization_status=AuthorizationStatus.AUTHORIZED,
    authority_status_at_authorization=T.SUSPENDED,
    authority_status_at_authorization_time=T1)

check("I01 recorded status preserved", c.authority_status_at_authorization is T.SUSPENDED)
check("I02 recorded time preserved", c.authority_status_at_authorization_time == T1)

# Later revocation
rev = TrustStatusAssertion(
    assertion_id="rev", subject_id="auth-A", kind=RevocationKind.REVOKE,
    asserted_at=T2, effective_at=T2, observed_at=T2,
    authority_ref="gov", authority_id="ra")
resolver = TrustStatusResolver()
# Simulate the earlier "activated" assertion too
act = TrustStatusAssertion(
    assertion_id="act", subject_id="auth-A", kind=RevocationKind.SUSPEND,
    asserted_at=T1, effective_at=T1, observed_at=T1,
    authority_ref="gov", authority_id="ra")

current_now = resolver.resolve_at("auth-A", T3, [act, rev])
check("I03 current status is REVOKED at T3", current_now.status is T.REVOKED)

# Historical status at T1 is unchanged
historical = resolver.resolve_at("auth-A", T1+timedelta(days=1), [act, rev])
check("I04 historical status at T1 unchanged", historical.status is T.SUSPENDED)

# Contract's recorded value matches T1 historical (not current)
check("I05 contract recorded ≠ current",
      c.authority_status_at_authorization is not current_now.status)
check("I06 contract recorded == historical",
      c.authority_status_at_authorization is historical.status)

# to_dict preserves
d = c.to_dict()
check("I07 to_dict has auth_status_at_authorization", d["authority_status_at_authorization"] == "suspended")
check("I08 to_dict has auth_status_at_authorization_time", d["authority_status_at_authorization_time"] is not None)

# Contract with None values still allowed
c2 = DecisionContract(
    decision_id="d2", intent=DecisionIntent.MONITOR,
    lifecycle=DecisionLifecycle.PROPOSED,
    decision_score=0.5, confidence=0.5,
    prediction_id="p", policy_id="pol", rationale="r", reason_codes=(),
    created_at=now)
check("I09 None allowed", c2.authority_status_at_authorization is None)
check("I10 None time allowed", c2.authority_status_at_authorization_time is None)
d2 = c2.to_dict()
check("I11 None in to_dict", d2["authority_status_at_authorization"] is None)

# Invalid type rejected
try:
    DecisionContract(
        decision_id="d3", intent=DecisionIntent.MONITOR,
        lifecycle=DecisionLifecycle.PROPOSED,
        decision_score=0.5, confidence=0.5,
        prediction_id="p", policy_id="pol", rationale="r", reason_codes=(),
        created_at=now, authority_status_at_authorization="active")
    check("I12 invalid type rejected", False)
except Exception: check("I12 invalid type rejected", True)

# Lifecycle still validated (3B invariant)
try:
    DecisionContract(
        decision_id="d4", intent=DecisionIntent.MONITOR,
        lifecycle=DecisionLifecycle.PROPOSED,
        decision_score=0.5, confidence=0.5,
        prediction_id="p", policy_id="pol", rationale="r", reason_codes=(),
        created_at=now, authorization_status=AuthorizationStatus.AUTHORIZED)
    check("I13 3B invariant still enforced", False)
except Exception: check("I13 3B invariant still enforced", True)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
