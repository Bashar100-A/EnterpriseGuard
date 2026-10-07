#!/usr/bin/env python3
import sys, tempfile, os
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from enterpriseguard.adie.canonical.trust.assertion import TrustStatusAssertion
from enterpriseguard.adie.canonical.trust.authority_to_revoke import (
    RevocationAuthority, RevocationKind, RevocationNotPermittedError)
from enterpriseguard.adie.canonical.trust.history import (
    TrustStatusStore, TrustHistoryError)
from enterpriseguard.adie.canonical.trust.resolver import ResolutionOutcome
from enterpriseguard.adie.canonical.trust.status import TrustStatus as T

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

def expect(n, fn, exc=TrustHistoryError):
    try: fn(); check(n, False, "did not raise")
    except exc: check(n, True)
    except Exception as e: check(n, False, f"wrong {type(e).__name__}")

print("="*72); print("TrustStatusStore"); print("="*72)
now = datetime.now(timezone.utc)

def mk(aid, kind, when=None):
    w = when or now
    return TrustStatusAssertion(assertion_id=aid, subject_id="auth-A",
        kind=kind, asserted_at=w, effective_at=w, observed_at=w,
        authority_ref="gov", authority_id="ra")

ra = RevocationAuthority(
    revocation_authority_id="ra", revocation_authority_ref="gov",
    permitted_kinds=frozenset({RevocationKind.REVOKE, RevocationKind.SUSPEND}),
    revocable_subject_ids=frozenset({"auth-A"}),
    valid_from=now-timedelta(hours=1), valid_until=now+timedelta(hours=1))

# in-memory
st = TrustStatusStore()
st.append(mk("a1", RevocationKind.REVOKE))
check("H01 length 1", len(st.all_assertions()) == 1)
check("H02 subject filter", len(st.assertions_for("auth-A")) == 1)
check("H03 subject filter empty", len(st.assertions_for("auth-B")) == 0)

# duplicate id
expect("H04 duplicate assertion_id", lambda: st.append(mk("a1", RevocationKind.SUSPEND)))

# authority gated append
st2 = TrustStatusStore()
expect("H05 not permitted kind", lambda: st2.append(mk("b1", RevocationKind.EXPIRE), revocation_authority=ra), RevocationNotPermittedError)
expect("H06 not permitted subject",
       lambda: st2.append(TrustStatusAssertion(assertion_id="b2", subject_id="auth-X",
           kind=RevocationKind.REVOKE, asserted_at=now, effective_at=now,
           observed_at=now, authority_ref="gov", authority_id="ra"),
           revocation_authority=ra), RevocationNotPermittedError)

st2.append(mk("b3", RevocationKind.REVOKE), revocation_authority=ra)
check("H07 authorized append", len(st2.all_assertions()) == 1)

# resolve through store
r = st.resolve_current("auth-A")
check("H08 resolve via store", r.outcome is ResolutionOutcome.RESOLVED)
check("H09 status REVOKED", r.status is T.REVOKED)

# persistence
with tempfile.TemporaryDirectory() as td:
    p = Path(td)/"trust.jsonl"
    st_p = TrustStatusStore(log_path=p)
    st_p.append(mk("p1", RevocationKind.REVOKE))
    st_p.append(mk("p2", RevocationKind.SUSPEND, now+timedelta(hours=1)))
    check("H10 persisted file exists", p.exists())
    check("H11 file non-empty", p.stat().st_size > 0)
    # recovery
    st_r = TrustStatusStore(log_path=p)
    check("H12 recovered count", len(st_r.all_assertions()) == 2)
    # p1 effective at `now`; p2 effective at `now + 1h`.
    # resolve_current uses real now, so only p1 applies -> REVOKED.
    r2_at_now = st_r.resolve_current("auth-A")
    check("H13a recovered resolve at now == REVOKED (p2 not yet effective)",
          r2_at_now.status is T.REVOKED)
    # Query at now+2h -> both assertions apply, later wins -> SUSPENDED
    r2_later = st_r.resolve_at("auth-A", now + timedelta(hours=2))
    check("H13b recovered resolve at now+2h == SUSPENDED",
          r2_later.status is T.SUSPENDED)
    # integrity
    vi = st_r.verify_integrity()
    check("H14 integrity valid", vi["valid"] is True)
    check("H15 integrity checked 2", vi["assertions_checked"] == 2)

# tampered file detected
with tempfile.TemporaryDirectory() as td:
    p = Path(td)/"trust.jsonl"
    st_p = TrustStatusStore(log_path=p)
    st_p.append(mk("t1", RevocationKind.REVOKE))
    # tamper
    lines = p.read_text().splitlines()
    tampered = lines[0].replace('"revoked"','"active"')
    p.write_text(tampered + "\n")
    st_t = TrustStatusStore(log_path=p)
    vi = st_t.verify_integrity()
    check("H16 tampered detected", vi["valid"] is False)

# empty-store integrity
st_e = TrustStatusStore()
check("H17 empty integrity valid", st_e.verify_integrity()["valid"] is True)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
