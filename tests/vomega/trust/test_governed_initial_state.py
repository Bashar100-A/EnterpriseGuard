#!/usr/bin/env python3
"""DEFECT-043: governed initial state tests (resolver level)."""
import sys, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from enterpriseguard.adie.canonical.trust.assertion import TrustStatusAssertion
from enterpriseguard.adie.canonical.trust.authority_to_revoke import RevocationKind
from enterpriseguard.adie.canonical.trust.resolver import (
    TrustStatusResolver, ResolutionOutcome, GOVERNED_INITIAL_STATE)
from enterpriseguard.adie.canonical.trust.status import TrustStatus as T
from enterpriseguard.adie.canonical.trust.history import TrustStatusStore

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

print("="*72); print("Governed initial state (DEFECT-043)"); print("="*72)
r = TrustStatusResolver()
T1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 6, 1, tzinfo=timezone.utc)

# ── 1. Known authority + empty history -> ACTIVE ──
res = r.resolve_at("auth-A", T1, [],
                   known_authority_ids=frozenset({"auth-A"}))
check("G01 known + empty -> RESOLVED", res.outcome is ResolutionOutcome.RESOLVED)
check("G02 status is ACTIVE", res.status is T.ACTIVE)
check("G03 reason is GOVERNED_INITIAL_STATE", res.reason == GOVERNED_INITIAL_STATE)
check("G04 source_assertion_id is None", res.source_assertion_id is None)
check("G05 not fail-closed", not res.is_fail_closed)

# ── 2. Unknown authority -> UNKNOWN fail-closed ──
res = r.resolve_at("auth-UNKNOWN", T1, [],
                   known_authority_ids=frozenset({"auth-A"}))
check("G06 unknown -> UNKNOWN", res.outcome is ResolutionOutcome.UNKNOWN)
check("G07 unknown fail_closed", res.is_fail_closed)
check("G08 unknown no status", res.status is None)

# ── 3. Malformed assertion input -> UNKNOWN fail-closed ──
bad = [{"kind": "not-an-assertion"}]  # type: ignore
res = r.resolve_at("auth-A", T1, bad,  # type: ignore
                   known_authority_ids=frozenset({"auth-A"}))
check("G09 malformed -> UNKNOWN", res.outcome is ResolutionOutcome.UNKNOWN)
check("G10 malformed fail_closed", res.is_fail_closed)
check("G11 malformed reason", res.reason == "malformed_assertion_input")

# ── 4. Conflicting history -> CONFLICT fail-closed ──
c1 = TrustStatusAssertion(assertion_id="c1", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T1, effective_at=T1, observed_at=T1,
    authority_ref="gov", authority_id="gov")
c2 = TrustStatusAssertion(assertion_id="c2", subject_id="auth-A",
    kind=RevocationKind.SUSPEND, asserted_at=T1, effective_at=T1, observed_at=T1,
    authority_ref="gov", authority_id="gov")
res = r.resolve_at("auth-A", T2, [c1, c2],
                   known_authority_ids=frozenset({"auth-A"}))
check("G12 conflict -> CONFLICT", res.outcome is ResolutionOutcome.CONFLICT)
check("G13 conflict fail_closed", res.is_fail_closed)

# ── 5. Known + future-effective assertion only -> initial ACTIVE at T_now ──
fut = TrustStatusAssertion(assertion_id="fut", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T2, effective_at=T2, observed_at=T2,
    authority_ref="gov", authority_id="gov")
res = r.resolve_at("auth-A", T1, [fut],
                   known_authority_ids=frozenset({"auth-A"}))
check("G14 future-effective-only -> ACTIVE at T1",
      res.outcome is ResolutionOutcome.RESOLVED and res.status is T.ACTIVE)

# ── 6. Known + past-effective assertion -> resolved (not initial) ──
past = TrustStatusAssertion(assertion_id="past", subject_id="auth-A",
    kind=RevocationKind.REVOKE, asserted_at=T1, effective_at=T1, observed_at=T1,
    authority_ref="gov", authority_id="gov")
res = r.resolve_at("auth-A", T2, [past],
                   known_authority_ids=frozenset({"auth-A"}))
check("G15 past-effective -> REVOKED", res.status is T.REVOKED)
check("G16 past-effective reason not initial", res.reason != GOVERNED_INITIAL_STATE)

# ── 7. Store: integrity failure -> UNKNOWN fail-closed ──
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "trust.jsonl"
    st = TrustStatusStore(log_path=p)
    st.append(TrustStatusAssertion(assertion_id="s1", subject_id="auth-A",
        kind=RevocationKind.REVOKE, asserted_at=T1, effective_at=T1, observed_at=T1,
        authority_ref="gov", authority_id="gov"))
    # Tamper file
    txt = p.read_text()
    tampered = txt.replace('"revoked"', '"active"')
    p.write_text(tampered)
    st2 = TrustStatusStore(log_path=p)
    res = st2.resolve_current("auth-A", known_authority_ids=frozenset({"auth-A"}))
    check("G17 tampered store -> UNKNOWN fail-closed",
          res.outcome is ResolutionOutcome.UNKNOWN and res.is_fail_closed)
    check("G18 reason mentions integrity",
          "integrity" in res.reason)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
