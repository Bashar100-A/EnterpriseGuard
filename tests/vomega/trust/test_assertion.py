#!/usr/bin/env python3
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from enterpriseguard.adie.canonical.trust.assertion import (
    TrustStatusAssertion, TrustStatusAssertionValidationError)
from enterpriseguard.adie.canonical.trust.authority_to_revoke import RevocationKind
from enterpriseguard.adie.canonical.trust.status import TrustStatus

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

def expect(n, fn, exc):
    try: fn(); check(n, False, "did not raise")
    except exc: check(n, True)
    except Exception as e: check(n, False, f"wrong {type(e).__name__}")

print("="*72); print("TrustStatusAssertion"); print("="*72)
now = datetime.now(timezone.utc)

a = TrustStatusAssertion(
    assertion_id="as-1", subject_id="auth-A", kind=RevocationKind.REVOKE,
    asserted_at=now, effective_at=now, observed_at=now,
    authority_ref="authority:gov-1", authority_id="ra-1")

check("A01 constructed", a.assertion_id == "as-1")
check("A02 asserted_status REVOKED", a.asserted_status is TrustStatus.REVOKED)
check("A03 fingerprint prefix", a.fingerprint().startswith("sha256:"))
check("A04 fingerprint length 71", len(a.fingerprint()) == 71)
check("A05 fingerprint deterministic", a.fingerprint() == a.fingerprint())

# kind -> status mapping
for i, (k, s) in enumerate([
    (RevocationKind.SUSPEND, TrustStatus.SUSPENDED),
    (RevocationKind.REVOKE, TrustStatus.REVOKED),
    (RevocationKind.SUPERSEDE, TrustStatus.SUPERSEDED),
    (RevocationKind.EXPIRE, TrustStatus.EXPIRED)]):
    aa = TrustStatusAssertion(assertion_id=f"as-{i}", subject_id="s",
        kind=k, asserted_at=now, effective_at=now, observed_at=now,
        authority_ref="x", authority_id="y")
    check(f"A{i+6:02d} {k.value} -> {s.value}", aa.asserted_status is s)

# validation
base = dict(assertion_id="as", subject_id="s", kind=RevocationKind.REVOKE,
            asserted_at=now, effective_at=now, observed_at=now,
            authority_ref="x", authority_id="y")

for i, f in enumerate(["assertion_id","subject_id","authority_ref","authority_id"]):
    kw = dict(base); kw[f] = ""
    expect(f"A{i+10:02d} empty {f}", lambda k=kw: TrustStatusAssertion(**k), TrustStatusAssertionValidationError)

kw = dict(base); kw["kind"] = "revoke"
expect("A14 non-kind", lambda: TrustStatusAssertion(**kw), TrustStatusAssertionValidationError)

for i, f in enumerate(["asserted_at","effective_at","observed_at"]):
    kw = dict(base); kw[f] = datetime(2026,1,1)
    expect(f"A{i+15:02d} naive {f}", lambda k=kw: TrustStatusAssertion(**k), TrustStatusAssertionValidationError)

kw = dict(base); kw["reason"] = 123
expect("A18 non-str reason", lambda: TrustStatusAssertion(**kw), TrustStatusAssertionValidationError)

try:
    a.subject_id = "x"; check("A19 frozen", False)
except Exception: check("A19 frozen", True)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
