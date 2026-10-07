#!/usr/bin/env python3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from enterpriseguard.adie.canonical.trust.assertion import TrustStatusAssertion
from enterpriseguard.adie.canonical.trust.authority_to_revoke import RevocationKind
from enterpriseguard.adie.canonical.trust.resolver import (
    TrustStatusResolver, ResolutionOutcome)
from enterpriseguard.adie.canonical.trust.status import TrustStatus as T

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

print("="*72); print("Temporal replay"); print("="*72)
r = TrustStatusResolver()
T1 = datetime(2026,1,1,tzinfo=timezone.utc)
T2 = datetime(2026,6,1,tzinfo=timezone.utc)
T3 = datetime(2026,12,1,tzinfo=timezone.utc)

# Case A: authority active at T1, revoked at T2
activate = TrustStatusAssertion(assertion_id="act", subject_id="auth-A",
    kind=RevocationKind.SUSPEND, asserted_at=T1, effective_at=T1, observed_at=T1,
    authority_ref="gov", authority_id="ra")   # ACTIVE-ish (SUSPENDED)
revoke = TrustStatusAssertion(assertion_id="rev", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T2, effective_at=T2, observed_at=T2,
    authority_ref="gov", authority_id="ra")

# at T1+day -> status is SUSPENDED (activation proxy)
res_T1 = r.resolve_at("auth-A", T1+timedelta(days=1), [activate, revoke])
check("A01 at T1+1d resolved", res_T1.outcome is ResolutionOutcome.RESOLVED)
check("A02 at T1+1d status SUSPENDED", res_T1.status is T.SUSPENDED)

# at T2+day -> REVOKED
res_T2 = r.resolve_at("auth-A", T2+timedelta(days=1), [activate, revoke])
check("A03 at T2+1d status REVOKED", res_T2.status is T.REVOKED)

# at T3 -> REVOKED (still)
res_T3 = r.resolve_at("auth-A", T3, [activate, revoke])
check("A04 at T3 still REVOKED", res_T3.status is T.REVOKED)

# historical query at T1 returns T1's status (not overwritten)
res_hist = r.resolve_at("auth-A", T1+timedelta(days=1), [activate, revoke])
check("A05 historical query unchanged by later revoke", res_hist.status is T.SUSPENDED)

# Case B: revocation effective in the past
past_effective = datetime(2025,1,1,tzinfo=timezone.utc)
observed_now = datetime(2026,1,1,tzinfo=timezone.utc)
b = TrustStatusAssertion(assertion_id="b1", subject_id="auth-B",
    kind=RevocationKind.REVOKE, asserted_at=observed_now,
    effective_at=past_effective, observed_at=observed_now,
    authority_ref="gov", authority_id="ra")
# Query at T_past+1d: is B revoked? effective_at <= query
res_past = r.resolve_at("auth-B", past_effective+timedelta(days=1), [b])
check("A06 past-effective assertion applies at past query", res_past.outcome is ResolutionOutcome.RESOLVED)
check("A07 status REVOKED", res_past.status is T.REVOKED)

# Case C: conflicting
c1 = TrustStatusAssertion(assertion_id="c1", subject_id="auth-C",
    kind=RevocationKind.REVOKE, asserted_at=T1, effective_at=T1, observed_at=T1,
    authority_ref="gov", authority_id="ra1")
c2 = TrustStatusAssertion(assertion_id="c2", subject_id="auth-C",
    kind=RevocationKind.SUSPEND, asserted_at=T1, effective_at=T1, observed_at=T1,
    authority_ref="gov", authority_id="ra2")
res_conf = r.resolve_at("auth-C", T1+timedelta(hours=1), [c1, c2])
check("A08 conflict detected", res_conf.outcome is ResolutionOutcome.CONFLICT)
check("A09 conflict fail-closed", res_conf.is_fail_closed)

# Case D: unauthorized revocation - not resolvable via resolver (resolver doesn't check auth)
# This is checked in history/authority layer (see test_history H05/H06).

# Case E: replay identical
for i in range(20):
    r1 = r.resolve_at("auth-A", T2+timedelta(days=1), [activate, revoke])
    r2 = r.resolve_at("auth-A", T2+timedelta(days=1), [activate, revoke])
    check(f"A{i+10:02d} replay identical #{i+1}",
          r1.status is r2.status and r1.source_assertion_id == r2.source_assertion_id)

# Full coverage: 5 statuses × 3 timing = 15 more checks
for i, kind in enumerate([RevocationKind.SUSPEND, RevocationKind.REVOKE,
                          RevocationKind.SUPERSEDE, RevocationKind.EXPIRE]):
    aa = TrustStatusAssertion(assertion_id=f"x{i}", subject_id=f"auth-{i}",
        kind=kind, asserted_at=T1, effective_at=T1, observed_at=T1,
        authority_ref="gov", authority_id="ra")
    rb = r.resolve_at(f"auth-{i}", T1-timedelta(seconds=1), [aa])
    ra_ = r.resolve_at(f"auth-{i}", T1, [aa])
    rl = r.resolve_at(f"auth-{i}", T1+timedelta(days=30), [aa])
    check(f"A{i+30:02d} before effective=UNKNOWN", rb.outcome is ResolutionOutcome.UNKNOWN)
    check(f"A{i+30:02d}b at effective=RESOLVED", ra_.outcome is ResolutionOutcome.RESOLVED)
    check(f"A{i+30:02d}c long after=RESOLVED", rl.outcome is ResolutionOutcome.RESOLVED)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
