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

def mk(aid, sid, kind, when):
    return TrustStatusAssertion(assertion_id=aid, subject_id=sid,
        kind=kind, asserted_at=when, effective_at=when, observed_at=when,
        authority_ref="gov", authority_id="ra")

print("="*72); print("Resolver"); print("="*72)
r = TrustStatusResolver()
t0 = datetime(2026,1,1,tzinfo=timezone.utc)

# empty
res = r.resolve_current("auth-A", [])
check("Q01 empty -> UNKNOWN", res.outcome is ResolutionOutcome.UNKNOWN)
check("Q02 empty fail_closed", res.is_fail_closed)

# single assertion
a = mk("a1","auth-A",RevocationKind.REVOKE, t0)
res = r.resolve_at("auth-A", t0+timedelta(seconds=1), [a])
check("Q03 resolved", res.outcome is ResolutionOutcome.RESOLVED)
check("Q04 status REVOKED", res.status is T.REVOKED)
check("Q05 source_assertion_id", res.source_assertion_id == "a1")

# not yet effective at earlier time
res = r.resolve_at("auth-A", t0-timedelta(seconds=1), [a])
check("Q06 before-effective -> UNKNOWN", res.outcome is ResolutionOutcome.UNKNOWN)

# different subject
res = r.resolve_at("auth-B", t0+timedelta(seconds=1), [a])
check("Q07 different subject -> UNKNOWN", res.outcome is ResolutionOutcome.UNKNOWN)

# multiple sequential
a2 = mk("a2","auth-A",RevocationKind.SUSPEND, t0+timedelta(hours=1))
res = r.resolve_at("auth-A", t0+timedelta(hours=2), [a, a2])
check("Q08 later assertion wins", res.status is T.SUSPENDED)
res = r.resolve_at("auth-A", t0+timedelta(minutes=30), [a, a2])
check("Q09 earlier assertion at earlier time", res.status is T.REVOKED)

# conflict same (effective, observed)
c1 = mk("c1","auth-A",RevocationKind.REVOKE, t0)
c2 = mk("c2","auth-A",RevocationKind.SUSPEND, t0)
res = r.resolve_at("auth-A", t0+timedelta(seconds=1), [c1, c2])
check("Q10 conflict -> CONFLICT", res.outcome is ResolutionOutcome.CONFLICT)
check("Q11 conflict fail_closed", res.is_fail_closed)
check("Q12 conflict no status", res.status is None)

# same kind at same time is NOT a conflict
d1 = mk("d1","auth-A",RevocationKind.REVOKE, t0)
d2 = mk("d2","auth-A",RevocationKind.REVOKE, t0)
res = r.resolve_at("auth-A", t0+timedelta(seconds=1), [d1, d2])
check("Q13 same kind same time resolved", res.outcome is ResolutionOutcome.RESOLVED)

# resolve_current uses now
a_old = mk("e1","auth-A",RevocationKind.REVOKE, datetime(2020,1,1,tzinfo=timezone.utc))
res = r.resolve_current("auth-A", [a_old])
check("Q14 resolve_current resolves past assertion", res.outcome is ResolutionOutcome.RESOLVED)
check("Q15 status REVOKED", res.status is T.REVOKED)

# total: 5 kinds x 3 timing positions = 15 more checks
for i, kind in enumerate([RevocationKind.SUSPEND, RevocationKind.REVOKE,
                          RevocationKind.SUPERSEDE, RevocationKind.EXPIRE]):
    aa = mk(f"m{i}", "auth-X", kind, t0)
    res_before = r.resolve_at("auth-X", t0-timedelta(seconds=1), [aa])
    res_at = r.resolve_at("auth-X", t0, [aa])
    res_after = r.resolve_at("auth-X", t0+timedelta(seconds=1), [aa])
    check(f"Q{i+16:02d} {kind.value} before", res_before.outcome is ResolutionOutcome.UNKNOWN)
    check(f"Q{i+16:02d}b {kind.value} at", res_at.outcome is ResolutionOutcome.RESOLVED)
    check(f"Q{i+16:02d}c {kind.value} after", res_after.outcome is ResolutionOutcome.RESOLVED)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
