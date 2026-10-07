# ADIE vΩ — Defects Log

**Purpose:** Record every defect discovered by a test suite.
**Rule (from this commit onward):** Every defect found by a test MUST be
logged here with root cause and fix. No silent corrections.

**Format:**DEFECT-NNN
date:
commit_found:
commit_fixed:
suite:
test_id:
test_name:
category: code | test | spec
root_cause:
fix:
lesson:
text


---

## DEFECT-001 — M19 was a duplicate of M06

date: 2026-10-06
commit_found: 99c8376
commit_fixed: a453556
suite: tests/vomega/meta/run_all.py
test_id: M19
test_name: Version Alias Collision
category: test
root_cause: Test registered the same rewrite rule with the same digest
twice. Registry.register_rewrite is idempotent for identical
digests by design, so no E-META-14 was raised. The test failed
to differentiate itself from M06 (Rewrite Rule Shadowing).
fix: Rewrote M19 to test three no-aliasing properties:
(a) distinct version strings stored as distinct entries,
(b) lookup does NOT cross-alias,
(c) same string + different digest → E-META-14.
lesson: A test that passes the same code path as another test does not
extend coverage. Each M-vector must exercise a distinct failure
mode. Review test intent, not test name.
text


---

## DEFECT-002 — A25: EQ did not enforce type check

date: 2026-10-06
commit_found: 5589bb2
commit_fixed: d39fb02
suite: tests/vomega/acl/run_all.py
test_id: A25
test_name: EQ int/str → E200_TYPE_MISMATCH
category: code
root_cause: In protocol/acl/eval.py, the EQ/NEQ branch returned
PASS/FAIL before the type-check block ran. Consequently
EQ(INT(5), STR("x")) returned FAIL instead of raising
E200_TYPE_MISMATCH, violating ACL-0.1 §2.2 (fail-closed on
type mismatch).
fix: Moved type check to the top of the EQ/NEQ/LT/... branch.
LT/LTE/GT/GTE additionally reject Bool and non-(int,str).
lesson: "Fail-closed" only holds if the check runs before any return.
Every comparison branch must validate types before producing
a result. Order of checks is a security property.
text


---

## Metrics

| Metric | Value |
|---|---|
| Total defects | 2 |
| Category: test | 1 |
| Category: code | 1 |
| Category: spec | 0 |
| Total tests at first defect | 40 |
| Total tests at second defect | 40 (ACL) |
| Total tests now | 143 |

---

**End of DEFECTS-LOG**

---


---

**End of DEFECTS-LOG**

---

## DEFECT-003 — Block B test 4 over-specified code

date: 2026-10-06
commit_found: <TBD>
commit_fixed: <TBD>
suite: Block B exploratory test
test_id: manual-4
test_name: authoring tampered → E-META-20
category: test
root_cause: ClaimRoot covers the `authoring` field (13 named fields). Tampering with authoring.canonical_ast_digest changes ClaimRoot, so DCP 2.0 pipeline raises E_CLAIM_ROOT_MISMATCH before the pilot-level authoring check runs. My expectation of E-META-20 was too specific.
fix: Accept either E_CLAIM_ROOT_MISMATCH or E-META-20 as valid rejection in the pilot conformance vectors. Document the ordering guarantee: DCP 2.0 claim_root runs before authoring-level checks.
lesson: Defense-in-depth means a single field tampering may be caught at multiple layers. Test expectations should be written against the failure SET, not a single code, unless the ordering is normative.

---

## DEFECT-004 — JS verify.mjs: ClaimRoot field mismatch + message format

date: 2026-10-06
commit_found: 5fe41ab
commit_fixed: <TBD>
suite: Block C differential
category: code
root_cause: (1) JS FIELD_ORDER had 13 fields; Python uses 14 (adds "proof-set" as always-ABSENT). 13+3 padding != 14+2 padding; Merkle roots diverged. (2) Error messages did not mirror Python str(VerifyError)="code: msg"[:120] format. (3) BindingError requires two-stage slicing [code: msg][:80] -> [code: sliced][:120].
fix: (1) FIELD_NAMES_13 + FIELD_ORDER_14; computeClaimRoot iterates all 14. (2) dcpMsg/bindingMsg helpers replicate Python slicing. (3) Rewrote verify.mjs.
lesson: Cross-language canonical byte-equality requires matching every detail: field order, padding strategy, error message format, and slicing semantics. "Byte-identical" is not just JSON.

---

## Schema addition (effective from DEFECT-006)

Future defect entries MUST include three additional fields:

```
language_pair:       py/js | py/rust | py/ts | single
failure_mode:        structural | message | crypto | timing | semantic
invariant_at_risk:   I13 | I14 | ... | I34 | none
```

Rationale: the pilot layer exposed that cross-language byte-equality failures split into three distinct classes (structural, message, crypto). Tracking them explicitly prevents future regression.

---

## DEFECT-006 — Rust verifier binding error codes use hyphens

date: 2026-10-06
commit_found: f8fb6e5
commit_fixed: <TBD>
suite: tests/vomega/rust/run_all.py
test_id: P06
test_name: wrong audience
test_phase: RUST-VERIFY
category: code
language_pair: py/rust
failure_mode: message
invariant_at_risk: I13 (cross-impl determinism)
root_cause: verifier.rs used E-BINDING-AUDIENCE-MISMATCH (hyphens) while Python verify_cli.py uses E_BINDING_AUDIENCE_MISMATCH (underscores). Cross-language byte-equality broke on error-code format, not on decision logic.
fix: Replaced all E-BINDING-* strings with E_BINDING_* in verifier.rs to match Python verify_pipeline.py and verify_cli.py.
lesson: The new DEFECT schema (language_pair/failure_mode/invariant_at_risk) was justified by this defect. Byte-equality is fragile at every layer including error identifiers. A single hyphen vs underscore = a real divergence. Tests caught it; the previous commit message did NOT (claimed 435/435 when actual was 434/435).

---

## DEFECT-007 — Premature GAP-5 commitment based on partial information

date: 2026-10-06
commit_found: 56717dc
commit_fixed: <TBD>
suite: n/a (process)
test_id: n/a
test_phase: Phase 2 setup
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34 (identifier immutability), I13 (determinism of records)
root_cause: After the first cargo fetch failed (Cargo 1.75 + edition2024), GAP-5 was committed as a permanent deferral without first attempting the alternative (rustup official). The second attempt succeeded immediately, invalidating the committed text.
fix: GAP-5 replaced by GAP-5-CORRECTED. DEFECT-007 logged. The lesson is that "attempt failed" does not equal "attempt impossible" — record the failed attempt as a note, not a permanent gap, until the alternative path is also tried.
lesson: In protocol documentation, "deferred" is a claim about the future. It requires exhausting known paths first. Partial-information commitments pollute the spec and require a correction cycle. Rule going forward: any GAP-N entry must include a "paths attempted" list.

---

## DEFECT-008 — Repeated GAP-N before exhausting paths

date: 2026-10-06
commit_found: 56f9bf7 (unpushed)
commit_fixed: <TBD>
suite: n/a (process)
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34
root_cause: Same as DEFECT-007, second occurrence. GAP-6 was written assuming nvm was the only path, while NodeSource was simultaneously attempted and succeeded.
fix: GAP-6-RETRACTED. DEFECT-008 logged.
lesson: This is a pattern, not an isolated incident. Going forward, GAP-N entries require a MANDATORY pre-condition: the author must run a "paths-tried" checklist and include raw evidence (commands + exit codes) for EVERY path before committing a "deferred" claim. A GAP-N without such evidence is treated as incomplete.

---

## DEFECT-009 — Placeholder contamination in spec §12.3

date: 2026-10-06
commit_found: <uncommitted>
commit_fixed: <TBD>
suite: n/a (documentation)
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34 (identifier immutability)
root_cause: A Python script was provided to update spec/HYBRID-CRYPTO-0.1.md with three hash values. The script included literal placeholders (INTEGRITY, SHA_MLDSA, SHA_PKG) with instructions to substitute them before running. The instruction was not followed, so the placeholders were written to the spec verbatim, making it look complete when it was not.
fix: Replaced placeholders by reading values directly from the filesystem inside the script. No manual substitution required.
lesson: Templates with placeholders are a failure mode. Any script that writes to a normative document MUST resolve all values programmatically. Manual substitution is not permitted for spec files. This is a stricter rule than DEFECT-007 and DEFECT-008 — the defect class is different (placeholders shipped, not partial-information commits).

---

## DEFECT-010 — pqcrypto cannot participate in deterministic ML-DSA testing

date: 2026-10-06
commit_found: <uncommitted>
commit_fixed: <TBD>
suite: n/a (API capability)
category: process
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (not a protocol violation; a testing-scope reduction)
root_cause: pqcrypto 1.0.0 (C wrapper over PQClean) exposes sign(sk, msg, context=None, hash_algorithm=None) and keygen() with no arguments. There is no way to inject a fixed ξ seed for FIPS 204 KeyGen_internal, nor to force deterministic signing. Cross-language byte-equality tests (spec HYBRID-CRYPTO-0.1 sec 10, sec 11) require both. Measured: sig_a != sig_b for two identical calls with the same sk and msg.
fix: Reclassified pqcrypto as VERIFY-ONLY for Phase 2. Python production sign path is dilithium-py 1.4.0 (deterministic=True, key_derive(seed)). Python verify path runs BOTH pqcrypto and dilithium-py, and requires agreement. This preserves the independent cross-check where it matters most (verification).
lesson: A "vetted library" claim must be qualified by its API capabilities, not just its cryptographic primitive. pqcrypto implements ML-DSA correctly for the sign/verify operations it exposes, but does not expose the FIPS 204 deterministic interfaces required for reproducible testing. This is not a cryptographic weakness; it is a testing and reproducibility constraint.

---

## DEFECT-011 — mldsa wrapper assumed ctx=b""

date: 2026-10-06
commit_found: 157fa3e
commit_fixed: <TBD>
suite: n/a (spec-vs-KAT scope)
category: code
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (discovered while preparing Block D.2 KAT)
root_cause: The ML-DSA wrapper (mldsa.rs) hard-coded SIGNING_CONTEXT = b"". This was correct for MLDSA-XLANG-001 (which used ctx=b"") but does not cover the ACVP KAT vectors, which carry variable-length context strings (e.g. 17 bytes, 20 bytes). The mismatch was discovered by inspecting the ACVP JSON structure before writing the KAT runner, not by a failing test.
fix: Extended mldsa.rs to expose sign_deterministic_ctx(seed, msg, ctx) and verify_with_ctx(pk, msg, ctx, sig). Legacy sign_deterministic(tbs) and verify() now delegate with ctx=b"". The CLI adie-mldsa accepts ctx_hex (optional, defaults to empty). MLDSA-XLANG-001 regression check passes with ctx=b"".
lesson: A wrapper that "works" for one test vector can still be incomplete for the general case. When preparing to add standard test vectors, read their structure first and confirm the wrapper covers every field. This is DEFECT-009 applied to code instead of docs: do not assume the first passing input defines the contract.

---

## DEFECT-012 — RustCrypto decode was stricter than FIPS 204.Verify semantics

date: 2026-10-06
commit_found: uncommitted (Block D.2b Rust run)
commit_fixed: <TBD>
suite: tests/vomega/mldsa/kat/run_rust.py
test_id: sigver tcId=32,38,41
test_phase: Phase 2 D.2b
category: code
language_pair: py/rust
failure_mode: structural
invariant_at_risk: none (API shape, not protocol)
root_cause: RustCrypto ml-dsa 0.1.1 Signature::decode returns Option::None for signatures whose hint field is out of range (per FIPS 204 sigDecode). The wrapper mapped this None to Err("signature decode failed"). ACVP expects such inputs to produce testPassed=false, not an error. Python dilithium-py returns False directly. Divergence: Err vs Ok(false).
fix: mldsa.rs verify_with_ctx maps decode failures to Ok(false), matching FIPS 204 ML-DSA.Verify which rejects invalid signatures. Wrong-length signature bytes also return Ok(false) now (they cannot be valid by construction).
lesson: "Signature decode" and "signature verification" are both rejections under FIPS 204; only the input format is what differs. Splitting them into Err vs Ok(false) in a wrapper breaks cross-language byte-equality on the decision (which ACVP tests). API ergonomics should follow the spec, not vice versa.

---

## GAP-8 — Rust ML-DSA sigGen not covered by ACVP KAT

date: 2026-10-06
paths tried:
  1. sign_deterministic(seed, msg, ctx) — requires Seed(32B)
  2. ACVP sigGen provides sk (4032B), not seed. Seed cannot be recovered
     from sk (it is derived from seed by an irreversible expansion).
  3. SigningKey::from_expanded(enc) — takes ExpandedSigningKeyBytes, but
     ACVP sk format is FIPS 204 sk encoding, not the RustCrypto
     internal expanded format.
  4. ml-dsa 0.1.1 does not expose a public API to construct SigningKey
     from raw FIPS 204 sk bytes without round-tripping through seed.
consequence:
  - Rust covers: keygen (25/25) + sigver (15/15).
  - Rust does not cover: sigGen (0/15).
  - Cross-language coverage for sigGen: Python (15/15) + JS (pending).
  - This is a wrapper-coverage limit, not a cryptographic gap: Rust
    verifies every ACVP sigVer vector correctly and its pk matches
    every ACVP keygen vector exactly.
resolution path (Phase 2.5):
  - Inspect RustCrypto for a hypothetical from_encoded API in later
    versions, OR
  - Build a thin adapter that reconstitutes the internal key from the
    standard sk format (if FIPS 204 defines such a path).
  - MLDSA-XLANG-001 already proves byte-equality of sigGen across the
    three languages for the seed-based path.
not retracted: RISK-2.1 (ml-dsa pre-1.0, unaudited).

---

## DEFECT-013 — spec claimed 13-byte domain tag; actual is 11 chars + NUL = 12 bytes

date: 2026-10-07
commit_found: f05af3d
commit_fixed: <TBD>
suite: n/a (spec text)
category: spec
language_pair: n/a
failure_mode: semantic
invariant_at_risk: none (implementation was always 12 bytes; only doc was wrong)
root_cause: spec/HYBRID-CRYPTO-0.1.md §5 wrote ""ADIE-SIG-V2\0" is an ASCII domain separation tag (13 bytes + NUL)". The string ""ADIE-SIG-V2"" has 11 characters (A D I E - S I G - V 2), not 13. With NUL, the tag is 12 bytes. Hex "41 44 49 45 2D 53 49 47 2D 56 32 00" (also listed in the same sentence) was always correct.
fix: spec corrected to "11 ASCII chars + NUL = 12 bytes". Code (protocol/hybrid/tbs.py) has always used 12 bytes with an explicit assertion.
lesson: Spec docs should not describe byte counts in prose next to hex literals. The hex is the source of truth; the prose is commentary and can drift. This is the second spec-vs-implementation mismatch (DEFECT-009 was placeholder text, this is character count). Both were caught before they affected real byte output.

---

## GAP-9 — ML-DSA-65 key_id uses raw pk bytes, not SPKI DER

date: 2026-10-07
paths tried:
  1. Spec §6 originally stated "SPKI DER with OID id-ml-dsa-65 (RFC 9964)".
  2. SPKI encoding requires SEQUENCE { SEQUENCE { OID id-ml-dsa-65, NULL }, BIT STRING pk }.
  3. Implementing this requires DER OID encoding, BIT STRING wrapping,
     and length prefix computation, all of which need independent testing.
  4. Cross-language byte-equality of SPKI-wrapped ML-DSA-65 pk has not
     been verified.
consequence:
  - ML-DSA-65 key_id = sha256(SHA-256(pk_raw)) where pk_raw is 1952 bytes.
  - RS256 key_id = sha256(SHA-256(SPKI_DER)).
  - The two key_id derivations use different encodings.
  - Fine for internal consistency but blocks cross-algorithm key_id comparison.
resolution path (Phase 2.5):
  - Add SPKI wrapper for ML-DSA-65 with OID DER (id-ml-dsa-65 from RFC 9964).
  - Cross-verify SPKI bytes across Python/JS/Rust.
  - Bump to key_id scheme v2 (not v1, to avoid identifier redefinition).
not retracted: RISK-2.1.


---

## DEFECT-014 — Test count conflation across phases

date: 2026-10-07
commit_found: 6f1152b
commit_fixed: <TBD>
suite: n/a (process)
test_id: n/a
test_phase: Phase 2 closure
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34 (identifier immutability — numbers are identifiers)
root_cause: Multiple numbers were claimed based on ad-hoc summation:
  (a) "648 Phase 1 regression" — actually 633. Off by 15.
  (b) "723/723 total" — sum of 648 + 75. Neither base number was correct.
  (c) "75 Phase 2" — actually 59 Python + 11 JS = 70, with 5 TBS-differential
      not being a standalone suite (they are inside test_tbs.py).
  The numbers were asserted in commit messages (fd5d98d, 6f1152b) and in
  PHASE-2-CLOSURE.md before being measured by a tool.
fix: Created tests/account.py as the sole authority for test counts. It
  runs every suite as a subprocess and reads the TOTAL line from stdout.
  Real numbers: 633 regression + 59 py + 11 js + 55 ACVP-unique = 758.
  PHASE-2-CLOSURE.md §12 and CONTINUITY §32 record the correction.
lesson: A number in a document is an identifier (I34). It must be produced
  by a deterministic tool, not by memory. The pattern is identical to
  DEFECT-007, DEFECT-008, DEFECT-009: a claim was committed before being
  measured. The difference here is that the claim was numeric and would
  have propagated into external communication. The consequence of leaving
  it uncorrected: an investor or auditor could have found the discrepancy
  and lost confidence in all other numbers. Now the source of every number
  is a script that any third party can run.


---

## RISK-3.1 — sad-rsa fork tracks unstable rsa 0.10.x API line

date: 2026-10-07
phase: Phase 3, Gate 0
crate: sad-rsa 0.10.2
checksum: 195609fa42645e9a027b45bc953163057a7c6d468d98088d4a3551b2b1d02d0f
reason:
  - mainline `rsa 0.9.6` has RUSTSEC-2023-0071 (Marvin attack) unpatched.
  - mainline `rsa 0.10.x` is still in release-candidate (0.10.0-rc.19).
  - `sad-rsa 0.10.2` is a security-focused fork that applies Marvin
    mitigation, complete RFC 8017 length validation, and enhanced
    zeroization. It tracks the 0.10.x API line.
mitigation:
  - Isolated behind rust/adie-primitives/src/rsa_verify.rs (single module).
  - No direct call from verifier.rs or any other module.
  - Swap to mainline rsa is a one-line change if upstream stabilizes.
  - Vendor mirror + checksum pinned in Cargo.lock.
consequence: if maintainer disappears, we fall back to rsa 0.9.6 +
  documented Marvin CVE, or to mainline 0.10.x once stable.
not hidden: this is a documented trade-off, not a silent choice.

---

## RISK-3.2 — sad-rsa dependency surface (~46 crates)

date: 2026-10-07
phase: Phase 3, Gate 0
count: ~46 crates in the dependency tree
reason:
  - crypto-bigint 0.7 (modern, well-audited) replaces the older
    num-bigint-dig used by rsa 0.9.6.
  - SHA-2, PEM/SPKI, and rand are standard RustCrypto crates, also
    used by ml-dsa (Phase 2).
mitigation:
  - No exotic deps: all are RustCrypto or well-known (serde, zerocopy).
  - Cargo.lock pins exact versions.
  - Vendoring possible (cargo vendor) for reproducibility.
justification: RFC 8017 length validation in sad-rsa is complete,
  whereas upstream rsa 0.9.6 has partial validation. For a hybrid
  certificate verifier under regulatory audit, this is worth
  the extra dependency surface.

---

## Archival note — why not rsa 0.9.6

date: 2026-10-07
decision: rejected for Gate 0
reason:
  - RUSTSEC-2023-0071 open, no patch on mainline.
  - RFC 8017 length validation partial.
  - MSRV 1.65 is fine, but the crate is on a maintenance branch
    pending the 0.10 rewrite.
note: `rsa 0.9.6` remains a valid fallback if sad-rsa becomes
  unavailable. Its API shape is documented above (sections 5-7 of
  the Gate 0 investigation). Migration cost is contained because
  the invocation is isolated in one module.


---

## DEFECT-015 — sad-rsa 0.10.2 fails to build; rsa 0.9.6 selected as fallback

date: 2026-10-07
commit_found: a7082fa
commit_fixed: <this commit>
suite: rust/adie-primitives build
test_id: n/a
test_phase: Phase 3, Gate 0
category: dependency
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (build-time only)
root_cause: `sad-rsa 0.10.2` declares `pkcs1 = "0.8"` allowing RCs.
  Cargo resolved to `pkcs1 0.8.0-rc.5`, which changed `RsaPublicKey`
  to require a generic parameter `U`. sad-rsa's code was written
  against an earlier pkcs1 0.8 API and does not compile against
  rc.5. This is a pinned-RC issue, not a feature-selection issue —
  it fails with default features too.
resolution_attempted:
  1. `sad-rsa = { version = "=0.10.2", default-features = false, features = ["std","encoding","sha2"] }`
     -> 8 errors
  2. `sad-rsa = "=0.10.2"` (default features)
     -> same 8 errors
  3. Decision: fall back to `rsa 0.9.6` (mainline RustCrypto),
     which builds cleanly in `/tmp/adie-rsa-test/`.
consequence:
  - RISK-3.1 updated: mainline `rsa 0.9.6` has RUSTSEC-2023-0071
    (Marvin) open on PKCS#1 v1.5 DECRYPTION. ADIE does VERIFICATION
    only, offline. Marvin requires a decryption oracle and targets
    the private key. Not applicable.
  - RISK-3.2 updated: dependency surface ~30 crates (vs ~46 for sad-rsa).
  - Migration to sad-rsa remains possible once pkcs1 0.8.0 stable
    ships and sad-rsa updates. Single-module change.
lesson: A library that resolves in cargo fetch does not prove it
  compiles. The `/tmp/adie-sad-rsa-test/` sandbox fetched but was
  never built. Sandbox verification MUST include `cargo build`,
  not only `cargo fetch`. This is the same class as DEFECT-007/008
  (partial-information commitment), applied to build verification.


---

## DEFECT-016 — rsa 0.9.6 requires explicit sha2 feature

date: 2026-10-07
commit_found: ac1b2c4
commit_fixed: <this commit>
suite: rust/adie-primitives build
test_id: n/a
test_phase: Phase 3, Gate 0
category: dependency
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (build-time only)
root_cause: `rsa 0.9.6` default features are `[std, pem, u64_digit]`.
  The `sha2` feature is optional and gates both `rsa::sha2` and
  `RsaPublicKey::from_public_key_pem` for SHA-256 uses. Our initial
  Cargo.toml line was `rsa = "=0.9.6"` without the feature, causing
  `use rsa::sha2::Sha256` to fail with E0432.
fix: Changed to `rsa = { version = "=0.9.6", features = ["sha2"] }`.
  Rebuilt successfully.
lesson: `cargo fetch` succeeding does not prove `cargo build` will.
  Feature gating is invisible to fetch. Every sandbox verification
  MUST end with `cargo build --release`. This is the second build-time
  defect in the same layer (DEFECT-015, DEFECT-016) — the pattern is
  consistent: verify by building, not by inspecting.


---

## DEFECT-017 — Rust adie-hybrid-verify did not check key_id before signature

date: 2026-10-07
commit_found: 723e0ce
commit_fixed: <this commit>
suite: tests/vomega/hybrid/test_rust_parity.py
test_id: R12
test_phase: Phase 3, Gate 0
category: code
language_pair: py/rust
failure_mode: semantic
invariant_at_risk: none (protocol-visible behavior mismatch)
root_cause: The Rust binary computed signatures but never checked
  signature.key_id against the fingerprint of the provided public
  key. On a wrong-key scenario, Rust fell through to signature
  verification (which failed) and emitted E_SIGNATURE_HYBRID_INVALID.
  Python explicitly checks key_id first and emits E_SIGNATURE_KEY_MISMATCH.
  Both refuse the certificate, but with different error codes —
  breaking byte-equality on the decision.
fix: Added `rs256_key_id_from_pem` (SPKI DER hashed with SHA-256) and
  `mldsa65_key_id_from_raw` (raw pk hashed with SHA-256) helpers, and
  inserted a key_id comparison inside the per-alg verification loop,
  before invoking the primitive. On mismatch, emit E_SIGNATURE_KEY_MISMATCH
  with the same message format as Python.
lesson: key_id binding and signature verification are two independent
  security checks. A verifier must perform both. Byte-equality testing
  across languages is the mechanism that catches such omissions; without
  R12, this would have gone unnoticed until an auditor noted inconsistent
  error codes for the same rejection.


---

## RISK-3.1 RECLASSIFICATION (Commander order, 2026-10-07)

**Previous status:** "not applicable" (rejected as too absolute).

**New status:** BOUNDED EXPOSURE / NOT USED FOR PRIVATE-KEY
OPERATIONS IN CURRENT VERIFIER PATH.

**Technical basis:** RUSTSEC-2023-0071 (Marvin attack) targets
timing side channels in RSA PKCS#1 v1.5 *decryption* oracles,
where the attack extracts information about the private key from
distinguishable error responses. ADIE's current usage of `rsa`
is exclusively:

- RsaPublicKey::from_public_key_pem (public-key parsing)
- VerifyingKey::<Sha256>::verify (public-key verification)

No RSA private-key signing, no RSA decryption, no online oracle.

**Residual risk:** if ADIE ever moves to online private-key
operations (Phase 4+), this reclassification must be revisited.

**Register:** RISK-3.1 remains in the active risk register. It is
not converted to "resolved" or "accepted". It is bounded by usage
scope and by offline verification semantics.

---

## DEFECT-017 — ARCHITECTURAL CLASSIFICATION (Commander order, 2026-10-07)

**Previous classification:** code defect (CLI-level).

**New classification:** evidence for an **Identity Binding Invariant**.

**Invariant definition:**

    Algorithm
      + Key ID
      + Public Key
      + Fingerprint
      + TBS

must be treated as one interconnected system. A valid signature is
not sufficient evidence if the identity of the key used does not
match the expected identity for the protocol.

**Integration requirement:** this invariant must be implemented in
Wire Format (Gate 1), Governance (Gate 3), and Revocation (Gate 4),
not only in the verifier.

**Tracking:** new entry on the Phase 3 architecture requirements list.


---

## CBOR-LIB-EVAL-001 — ciborium 0.2.2 selected for 3A.2

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.2
category: dependency-selection

### Candidates surveyed

| crate | v | license | MSRV | Value type | status |
|---|---|---|---|---|---|
| ciborium | 0.2.2 | Apache-2.0 | 1.58 | Yes | selected |
| minicbor | 2.3.0 | BlueOak-1.0.0 | unknown | No (needs impl) | rejected |
| cbor4ii | 1.2.3 | MIT | unknown | types module only | rejected |
| serde_cbor | 0.11.2 | MIT/Apache | unknown | Yes | unmaintained since 2020 |
| cbor | 0.4.2 | — | — | — | deprecated (crates.io warning) |

### Rationale for ciborium

- Available on rustc 1.99 (MSRV 1.58).
- Provides a Value type (`ciborium::value::Value`) usable without
  serde derives.
- Apache-2.0 license, mainstream ecosystem.
- Actively maintained by Enarx project.

### What ciborium does NOT enforce (probe results)

Direct probe of the sandbox (`/tmp/adie-ciborium-test`), same input
encoded twice and same malformed inputs decoded:

| # | Behavior | Result |
|---|---|---|
| T1 | Deterministic map ordering | NO — insertion order preserved |
| T2 | Overlong integer | ACCEPTED |
| T3 | Indefinite-length map | ACCEPTED |
| T4 | Duplicate map keys | ACCEPTED (Vec of pairs) |
| T5 | Float | ACCEPTED |
| T6 | Tag | ACCEPTED |
| T7 | Trailing bytes | ACCEPTED |
| T8 | Round-trip stability | YES (for well-formed input) |

### Consequence

ciborium is the *codec primitive*. It does not implement the ADIE
Deterministic CBOR Profile (WIRE-FORMAT-0.2 §7–§9). ADIE code MUST
enforce the profile on top:

- Encode side: sort map keys numerically before writing.
- Decode side: after reading Value, walk it and reject:
  - noncanonical integers (must be shortest-form)
  - indefinite-length items
  - floats
  - tags
  - duplicate keys
  - trailing bytes after top-level Value
  - text keys / byte keys / compound keys (only integer keys allowed)
  - required fields with wrong type
  - unknown critical fields

This validation layer is ADIE-owned (`rust/adie-primitives/src/cbor/`).
ciborium is isolated to a single module; replacement (e.g., future
minicbor adoption) requires touching only that module.

### Not claimed

- ciborium does not provide ADIE profile enforcement.
- ciborium does not provide canonical encoding.
- Selection of ciborium does not imply it satisfies WIRE-FORMAT-0.2.
  The spec and the profile layer do.


---

## DEFECT-018 — ciborium::Value is #[non_exhaustive]

date: 2026-10-07
commit_found: <uncommitted, during 3A.2 D.3>
commit_fixed: <this commit>
suite: rust/adie-primitives build
test_id: n/a
test_phase: Phase 3, Gate 1, 3A.2
category: code
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (compile-time only)
root_cause: ciborium::value::Value is marked #[non_exhaustive].
The exhaustively-written match in profile::validate_depth failed to
compile with E0004 (non-exhaustive patterns: `&_` not covered).
fix: Added a wildcard `_ =>` arm returning CborError::Malformed.
An unrecognised variant must be rejected, not silently accepted.
lesson: non_exhaustive enums from external crates require explicit
wildcard handling. Under a rejection policy, the wildcard itself
must reject.

---

## DEFECT-019 — Test byte count error in rawcheck::valid_nested

date: 2026-10-07
commit_found: <uncommitted, during 3A.2 D.4>
commit_fixed: <this commit>
suite: cargo test --release --lib cbor::rawcheck
test_id: cbor::rawcheck::tests::valid_nested
test_phase: Phase 3, Gate 1, 3A.2
category: test
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (test bug, not code bug)
root_cause: The test asserted 6 bytes for {1:[true,null]}. Correct
count is 5: a1 + 01 + 82 + f5 + f6. Hand counting was wrong; the
rawcheck scanner was correct.
fix: Assertion updated to 5 with the byte-by-byte count written
literally into the test as a comment.
lesson: byte-count assertions must include the byte-by-byte derivation
in the test body. Hand-counting without a written trace is a recurring
source of noise.

---

## RISK-3.3 — Build environment is space-constrained

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.2
observation: Development disk is 38 GB with 36 GB used at peak,
leaving ~450 MB free. One `cargo build --release` required ~240 MB.
When the disk filled, the build failed with OS error 28
(No space left on device).
mitigation:
  - Removed ~6.7 GB of cache: ~/.cache/trunk (4.5 GB),
    ~/.npm/_cacache (1.2 GB), ~/.cache/pip (642 MB),
    mozilla cache (301 MB), node-gyp (56 MB), stale /tmp.
  - Rule: after each `cargo build --release`, check `df -h /home`.
    If free space < 1 GB, run `cargo clean` before continuing.
consequence: Development is functional but constrained.
not hidden: recorded as an active operational constraint.

---


---

## DEFECT-020 — account.py summary anchor mismatch

date: 2026-10-07
commit_found: 42b7722
commit_fixed: 928d0df
suite: n/a (tooling)
category: process
language_pair: n/a
failure_mode: structural
invariant_at_risk: I34 (identifier immutability — numbers)
root_cause: A Python updater script assumed the summary block in
tests/account.py had a fixed string form. The actual form differed
(pytest-style indentation, extra spaces). The script's anchor regex
did not match, so the PHASE3_3A2_CBOR line was not added and the
Grand total formula was not updated. account.py therefore continued
to display 771 instead of 882 in its final output.
fix: Rewrote the updater using a narrower regex anchored on
'PHASE3_GATE0_PARITY' with a fallback line-scan loop. Ran the
verifier; account.py now emits 882 correctly. Committed as 928d0df.
lesson: Numeric aggregation code is as sensitive as cryptographic
code. Strings that matter (formulas, summaries) must be updated by
parsing rather than string replacement, or must be regenerated from
a single source. This is the same class as DEFECT-014 (numbers
conflated) applied to the tooling layer: a fix that "looks done"
can still ship an incorrect number.
follow-up rule: after any change to tests/account.py, the immediate
next step is to run it and read its stdout. No commit until the
displayed total matches the expected sum.


---

## DEFECT-021 — cbor2 silently interprets known semantic tags

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.3
commit_found: probe during Block B
commit_fixed: <this commit>
suite: /tmp/adie-cbor2-test/probe.py
test_id: T6
category: dependency
language_pair: py/py-reference (asymmetry vs Rust reference)
failure_mode: semantic
invariant_at_risk: I19 (finite universe), I34 (identifier immutability)

root_cause:
  cbor2 6.1.5 does not reject CBOR tags by default. Tag 1
  (`0xc1 0x01` = epoch timestamp) is decoded to
  datetime.datetime(1970,1,1,0,0,1,tzinfo=UTC). The ADIE profile
  (WIRE-FORMAT-0.2 §7) forbids major type 6 entirely. A naive
  decoder using cbor2.loads() would silently accept a forbidden
  type and reinterpret it as a Python object.
  cbor2's tag_hook parameter is documented to apply only to
  semantic tags not covered by a built-in decoder; built-in
  tags such as 0, 1, 2, 3 (date, timestamp, bignum) bypass the
  hook. tag_hook alone is therefore NOT sufficient.

fix_plan (to be implemented in 3A.3):
  1. rawcheck.py runs BEFORE cbor2.loads(). It rejects any byte
     whose major type is 6 (0xC0..0xDF) before cbor2 sees it.
  2. cbor2.loads() is called with explicit hardened parameters:
       allow_indefinite=False,
       allow_duplicate_keys=False,
       max_depth=32,
       tag_hook=raise_on_tag  (defense-in-depth)
  3. The hardened parameters are mandatory and documented in the
     decoder. They are not optional.

lesson:
  "Codec behavior ≠ protocol behavior." A general-purpose CBOR
  library, by design, accepts a wider input universe than any
  given protocol profile. When the profile is stricter (forbids
  tags, floats, indefinite lengths, duplicate keys), the protocol
  layer MUST enforce its own constraints on raw bytes and MUST
  configure the codec explicitly where the codec allows it.
  This is the same architectural pattern as DEFECT-012 (Rust
  decode semantics) and DEFECT-006 (Rust error code formatting):
  the external library is a primitive, not an authority.


---

## DEFECT-022 — Test harness ROOT path off by one

date: 2026-10-07
commit_found: <uncommitted, during 3A.3 D.1>
commit_fixed: <this commit>
suite: tests/vomega/wire/test_error.py
category: test
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (test infrastructure only)
root_cause: The test file lives at tests/vomega/wire/test_error.py.
Four path components from repo root. HERE.parents[2] is the repo
root (wire -> vomega -> tests -> ROOT); HERE.parents[3] is one level
above the repo. The test used parents[3], so `sys.path` pointed at
the wrong directory and `import protocol` failed.
fix: Changed to HERE.parents[2]. Also reordered mkdir before touch
in the test file creation script.
lesson: The N in HERE.parents[N] equals the number of directory
levels between the test file and the project root. Every new test
directory should include a comment with its depth derivation.

---

## DEFECT-023 — cbor2 raises CBORDecodeError for duplicate keys

date: 2026-10-07
commit_found: <uncommitted, during 3A.3 D.6>
commit_fixed: <this commit>
suite: tests/vomega/wire/test_decoder.py
test_id: T25
category: code
language_pair: py/py-library
failure_mode: structural
invariant_at_risk: none (mapping bug)
root_cause: The decoder's exception handler caught CBORDecodeError
before checking for "duplicate" in the message, converting it to
Malformed. cbor2 6.1.5 raises CBORDecodeError (not ValueError) for
allow_duplicate_keys violations, with message
"error decoding map: Duplicate map key: 1".
fix: Moved the "duplicate" / "indefinite" message inspection into
the CBORDecodeError handler. Both CBORDecodeError and ValueError
paths now check the message first.
lesson: Error class assumptions for external libraries must be
verified by probe, not by documentation memory. cbor2 uses
CBORDecodeError for both its optional strict-mode rejections.

---

## DEFECT-024 — Hand-written JSON vector file had invalid syntax

date: 2026-10-07
commit_found: <uncommitted, during 3A.3 D.9b>
commit_fixed: <this commit>
suite: tests/vomega/wire/differential_vectors.json
category: process
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (tooling)
root_cause: The vectors file was hand-written with placeholder
replacements like
    "cbor_hex": "a201616101616 2".replace(" ", "")
embedded directly in the JSON source. Python's json module rejects
this as invalid. The intent was to make long hex strings readable,
but the mechanism was a Python expression, not JSON syntax.
fix: Regenerated the file entirely from Python (json.dumps of a
Python dict). Long hex strings are now written as single literals.
Lesson: JSON files must be generated by a program. Hand-written
JSON with embedded "workarounds" is fragile and error-prone.
This is the third instance (DEFECT-009, DEFECT-014, DEFECT-020,
DEFECT-024) of the same pattern: a text artifact that "looks right"
but is not machine-valid.

---

## CBOR-LIB-EVAL-002 — cbor2 6.1.5 selected for Python adapter (3A.3)

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.3
category: dependency-selection
library: cbor2
version: 6.1.5
license: MIT
pypi: https://pypi.org/project/cbor2/6.1.5/

### Rationale

- Pinned exact version.
- Provides CBOR encoder and decoder primitives.
- Exposes explicit strict-mode flags:
    allow_indefinite=False
    allow_duplicate_keys=False
    max_depth=<n>
    tag_hook=<callable>
- canonical=True produces shortest-form, definite-length,
  sorted-map output. Verified empirically against RFC 8949
  integer-boundary vectors (test_encoder T27-T31).

### Probe findings (sandbox)

| # | Behavior | cbor2 6.1.5 |
|---|---|---|
| T1 | canonical map order | YES with canonical=True |
| T2 | overlong integer | ACCEPTED by default |
| T3 | indefinite map | ACCEPTED by default |
| T4 | duplicate keys | ACCEPTED by default (last wins) |
| T5 | float64 | ACCEPTED |
| T6 | tag 1 (epoch) | INTERPRETED as datetime |
| T7 | trailing bytes | ACCEPTED (ignored) |

### Required hardening (Commander order §3-§5)

- allow_indefinite=False (explicit)
- allow_duplicate_keys=False (explicit)
- max_depth=32 (explicit)
- tag_hook=raise_on_tag (defense-in-depth only)

rawcheck runs BEFORE cbor2 and is authoritative for tag rejection.

### What cbor2 is not

- cbor2 is not an authority for the ADIE profile.
- It is a codec primitive. The profile is enforced by
  protocol/wire/rawcheck.py, protocol/wire/profile.py, and the
  decoder's canonical re-encode comparison.

### Trust boundary

- cbor2 is a third-party dependency.
- Its behavior differences from the Rust reference (ciborium)
  are documented and compensated by the ADIE profile layer.
- It is not audited; treated as a primitive, not as an oracle.


---

## DEFECT-025 — CommonJS interop: named exports not visible in ESM

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4A
commit_found: probe during Block B
commit_fixed: <this 3A.4 commit>
suite: /tmp/adie-js-cbor-test/probe.mjs, probe_cbor.mjs
category: dependency
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (build-time integration)
root_cause: cbor@10.0.12 and cbor@9.0.2 are CommonJS modules. When
imported via `import * as CBOR from 'cbor'`, Node.js does not surface
the module's runtime properties (encode, encodeCanonical,
decodeFirstSync) as named exports. The full module object lives at
CBOR.default. Additionally, cbor@10.x rewrote its public API and no
longer ships the encode/decode/encodeCanonical helpers at all; only
low-level Encoder/Decoder classes remain.
fix: (1) Use `import CBOR from 'cbor'` (default import) to access the
CommonJS object. (2) Select cbor@9.0.2 (last major line with classic
helper API). (3) Document that callers MUST use the default-import
form.
lesson: ESM/CJS interop is not transparent. Every JS dependency's
import style must be verified at the probe stage, not at integration
time. This is a specific case of the general rule: "codec behavior
!= protocol behavior" (DEFECT-021), extended to "module shape !=
namespace shape".

---

## CBOR-LIB-EVAL-003 — cbor 9.0.2 selected for JavaScript adapter (3A.4A)

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4A
category: dependency-selection
library: cbor
version: 9.0.2
license: MIT
npm: https://www.npmjs.com/package/cbor

### Candidates surveyed

| library | version | license | deps | deterministic map sort | trailing reject | status |
|---|---|---|---|---|---|---|
| cbor-x | 1.6.6 | MIT | native (cbor-extract, node-gyp-build) | **NO** | YES | REJECTED |
| cbor | 10.0.12 | MIT | nofilter | API removed | n/a | REJECTED |
| cbor | 9.0.2 | MIT | nofilter | **YES** | **YES** | **SELECTED** |
| cbor2 | 2.4.0 | MIT | @cto.af/wtf8 | (not probed) | (not probed) | fallback |

### Rationale for cbor@9.0.2

- Exposes classic helper API: encode, encodeCanonical,
  decodeFirstSync, decodeAllSync.
- encodeCanonical produces byte-identical output to ciborium
  (Rust) and cbor2 (Python) on our probe cases, including map key
  sorting and integer boundaries.
- Rejects trailing bytes at decodeFirstSync.
- Round-trip stability confirmed empirically.
- Single non-native dependency (nofilter).

### Rejected candidates (evidence)

- **cbor-x 1.6.6:** canonical option does not sort map keys
  (`T1 canonical: false`); round-trip not byte-stable; interprets
  known tags as Date. Also pulls native bindings (cbor-extract,
  node-gyp-build), which would be a first for the project's
  pure-JS dependency tree.
- **cbor 10.0.12:** API rewrite. encode/decode/encodeCanonical are
  not exported; only low-level Encoder/Decoder classes with
  push/pull interfaces. Not a suitable codec primitive for a
  protocol that requires a single canonical function.

### cbor@9.0.2 behavior to be compensated by ADIE layer

Same pattern as DEFECT-021 (cbor2, Python):

| Case | cbor@9 | Compensated by |
|---|---|---|
| tag 0 (date string) | decoded to Date | rawcheck rejects major type 6 |
| tag 1 (epoch) | decoded to Date | rawcheck rejects major type 6 |
| unknown tag | decoded to Tagged | rawcheck rejects major type 6 |
| overlong int | accepted | rawcheck rejects non-shortest |
| indefinite | accepted | rawcheck rejects |
| duplicate keys | accepted | rawcheck + cbor preferredSerialization |

### Import form (mandatory)

    import CBOR from 'cbor';   // default import — NOT * as CBOR

See DEFECT-025.

### Trust boundary

- cbor@9.0.2 is a third-party CommonJS dependency.
- It is a codec primitive, not an authority for the ADIE profile.
- Its behavior differences from Rust/Python are documented and
  compensated by protocol/wire-js/rawcheck.js and profile.js.
- It is not audited; treated as a primitive.


---

## DEFECT-026 — JS profile coercion of non-integral Number values

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4A
commit_found: <uncommitted, during 3A.4A D.3>
commit_fixed: <this D.3 commit>
suite: tests/vomega/wire-js/test_profile.mjs
test_ids: T13, T14, T17 (all failed with 28/31)
category: code
language_pair: n/a
failure_mode: semantic-coercion
invariant_at_risk: A JavaScript Number that is not a mathematical
integer MUST NEVER be silently coerced into an integer ADIE value.

root_cause:
intToAdie() in js/wire/profile.mjs performed `BigInt(n)` on any
incoming `number` without first verifying integer-ness. JavaScript's
BigInt() constructor truncates fractional values
(BigInt(1.5) === 1n), and throws a native RangeError for
Infinity/NaN. The result was:
  - 1.5       → {t:'uint', v:1n}    (silent truncation, no error)
  - Infinity  → native RangeError   (not an ADIE typed rejection)
  - [1.5]     → same as above inside arrays
All three cases violated the profile contract: the validator is the
authority on semantic admissibility, and it must never normalize.

fix:
Insert explicit Number.isInteger() and Number.isSafeInteger() guards
inside intToAdie() BEFORE any BigInt() conversion. Non-integral
Numbers throw FloatErr. Unsafe integers throw NonCanonicalInt.
BigInt inputs bypass the guards and are range-checked directly
against U64_MAX / I64_MIN.

lesson:
BigInt() is not a validator; it is a coercion primitive. Any
language-level numeric conversion MUST be preceded by an explicit
type/integer check when the value may originate from an untrusted
decode path.

architectural_note:
Wire-level float/integer ambiguity is OUTSIDE profile authority once
decoding has erased the original CBOR major type. Two distinct CBOR
encodings —
    0x01                 (unsigned integer 1)
    0xfb3ff0000000000000 (float64 1.0)
— decode to the SAME JavaScript value (Number 1) via cbor@9. Once
that erasure has occurred, profile.validate() has no information to
distinguish them. Therefore rawcheck.mjs MUST reject forbidden float
encodings at the byte level BEFORE cbor@9 runs. This is the
architectural invariant that T32 documents.

invariant_statement:
Profile validates semantic values.
Rawcheck validates information that semantic decoding may erase.


---

## DEFECT-027 — rawcheck must reject duplicate keys at wire level

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4A / D.4-D.6
commit_found: <uncommitted, during 3A.4A stage>
commit_fixed: <this stage commit>
suite: js/wire/rawcheck.mjs
category: architecture
failure_mode: information-loss
invariant_at_risk: Wire-level duplicate keys MUST be rejected before
any semantic decoding step that could deduplicate them.

root_cause:
cbor@9.0.2 decodes CBOR maps into JavaScript Map objects. When two
entries share the same key, the JS Map silently overwrites the first
value with the second. This loses the wire-level fact that a
duplicate existed. Therefore rawcheck MUST detect and reject
duplicates at the byte level, BEFORE cbor@9 runs. D.4 rawcheck
initially left duplicate detection to profile.mjs; testing revealed
that this placed the check too late in the pipeline.

fix:
Extend walkMap() in rawcheck.mjs to record each key's byte range and
reject identical byte sequences with DuplicateKey. This is bytewise
identity, which is the correct DCP 2.1 rule (RFC 8949 §5.6).

architectural_note:
This is the same principle as DEFECT-026 (T32): the semantic layer
must not be trusted to detect information that the codec erases.
The rawcheck's responsibility list therefore grows by one wire-level
invariant, WITHOUT pulling semantic logic (integer-only keys, sorted
order, depth) into rawcheck. Those remain profile responsibilities.

invariant_statement:
Rawcheck's mandate covers every wire-level distinction that would
be lost by cbor@9's structural normalization. Duplicate keys are
one such distinction. Sorting order is another (compensated at the
re-encode step in decoder.mjs). Type-erasure is a third (DEFECT-026).

---

## DEFECT-028 — cbor@9 mixed Map/object output for maps

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4A / D.6
commit_found: <uncommitted, during D.6 test_decoder run>
commit_fixed: <this stage commit>
suite: tests/vomega/wire-js/test_decoder.mjs
test_ids: D17 (empty map), D39 (text-key map)
category: dependency
language_pair: n/a
failure_mode: structural
invariant_at_risk: profile.validate must receive a consistent
representation of CBOR maps, independent of the key types present.

root_cause:
cbor@9.0.2's default decode behavior (`preferMap: false`) returns:
  - integer-keyed maps -> JS Map
  - string-keyed maps  -> JS Object
  - empty maps         -> JS Object
This mixed representation caused:
  D17 (a0): profile.validate saw {} (plain Object) and threw
      Malformed instead of accepting an empty map.
  D39 (a1616b01 = {"k":1}): profile.validate saw {k:1} (plain
      Object) and threw Malformed instead of TypeMismatch on the
      non-integer key.

fix:
Pass `{ preferMap: true }` to CBOR.decodeFirstSync in decoder.mjs.
This forces ALL CBOR maps to be decoded as JavaScript Map objects,
giving profile.validate a single, consistent shape to inspect.
Semantic rejection of non-integer keys then happens naturally in
profile.mjs with the correct error code (TypeMismatch).

lesson:
Default codec options are not neutral. Every decoder setting that
affects JS value shape MUST be examined, documented, and either
accepted or overridden explicitly. This is the fourth DEFECT in
the family: DEFECT-021 (cbor2 tags), DEFECT-025 (CJS interop),
DEFECT-026 (Number coercion), DEFECT-028 (preferMap). All four are
"library defaults that do not match protocol authority defaults".

invariant_statement:
The semantic authority (profile.mjs) must receive CBOR maps in
exactly one JS representation. Cross-language parity requires it.
Rawcheck does not address this; it is a decoder-config concern.


---

## DEFECT-029 — JSON Number precision boundary at u64 range

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4A-DIFF
commit_found: <uncommitted, during stage 3A.4A-DIFF>
commit_fixed: <this stage commit>
suite: tests/vomega/wire-js/test_differential_{rust,python}.mjs
test_ids: D.8: E06, D03-D05, D10-D12 (7 fails)
          D.9: E06, D03-D05, D10-D12 (7 fails)
category: test
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (test harness only; implementations correct)

root_cause:
Two distinct failure modes with the same root family — JSON text
serialization of the u64 numeric range:

1. Vector file read: JSON.parse(vectors.json) parses the E06 vector's
   v=18446744073709551615 (u64::MAX) into a lossy JavaScript Number
   (18446744073709552000). Re-serialization by JSON.stringify sent a
   value > u64::MAX to Rust/Python, which correctly rejected it with
   a range error.

2. Comparison serializer: the previous canonical() converted BigInt
   values to Strings before JSON.stringify, causing JSON.stringify
   to add double quotes. Result:
       Rust/Py: {"t":"uint","v":0}    (Number 0)
       JS test: {"t":"uint","v":"0"}  (String "0")
   Textual mismatch — semantic identical.

fix:
- New helper js/wire/bin/json-io.mjs:
    parsePreservingBigInts(text) — marks 16+ digit literals before parse,
      revives them as BigInt
    stringify(v) — emits BigInt as plain integer literals
    canon(v) — unified serializer; Number and BigInt both become plain
      decimal literals, arrays and objects serialized deterministically
- Both differential tests import these helpers.
- Vector file read via parsePreservingBigInts.
- Rust/Python payload stringify via stringify.
- Comparison via canon on both sides.

lesson:
JSON is a text format with a Number type that cannot represent the
full u64 range. Whenever a protocol uses the u64 range (as ADIE's
DCP 2.1 profile does for map keys and integer values), every JSON
boundary in the toolchain MUST handle 16+ digit integers explicitly.
This is the same family as DEFECT-024 (hand-written JSON vector file):
the artifact "looks right" in text form but violates the format's
numeric precision guarantee.

architectural_note:
The endpoints themselves were correct throughout. Rust's adie-cbor
correctly rejected an out-of-range uint. The Python endpoint's UInt
correctly rejected an out-of-range value. The JS endpoint's own
BigInt handling was correct. Only the test harness's JSON pipeline
was lossy. The fix is confined to test infrastructure and a new
shared helper; no protocol, spec, or endpoint behavior changed.

invariant_statement:
Every JSON boundary in the ADIE toolchain must preserve the full
u64 range as integers. Numbers of 16+ digits must be handled as
BigInt end-to-end, never routed through JavaScript's Number type.


---

## DEFECT-029-WASM — Lossless Integer Boundary Invariant (WASM ABI)

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4B
commit_found: <uncommitted, during 3A.4B>
commit_fixed: <this stage commit>
suite: rust/adie-wasm/src/lib.rs, tests/vomega/wasm/test_wasm_precision.mjs
category: architecture
failure_mode: potential-information-loss
invariant_at_risk: Wire-protocol u64/i64 values MUST NOT transit the
JavaScript Number type (IEEE-754) at any point in the WASM delivery
boundary.

root_cause:
DCP 2.1 wire format encodes uint (major type 0) and int (major type 1)
in the range [0, 2^64-1] and [-2^63, 2^63-1] respectively. JSON's
Number is IEEE-754 double-precision (safe integer range ±2^53-1).
Any JSON boundary that serializes u64/i64 as a bare Number is lossy.
This is the same class of hazard as DEFECT-029 (JSON Number precision
boundary), but on a different surface — the WASM ABI.

fix:
The WASM ABI contract (WASM ABI/serialization boundary, NOT DCP 2.1
JSON schema) is:

  uint/int VALUES AND MAP KEYS cross the boundary as decimal STRINGS:

    {"t":"uint","v":"18446744073709551615"}
    {"t":"int", "v":"-9223372036854775808"}
    {"t":"map", "v":[["18446744073709551615", ...]]}

The Rust side parses these with u64::from_str / i64::from_str and
range-checks immediately. The JavaScript side receives them as
strings from the WASM return value. No Number ever touches a wire
integer.

Proof artifacts:
  - rust/adie-wasm/src/lib.rs: read_u64/read_i64 prefer string form
  - test_wasm_precision.mjs: 10 u64 + 3 i64 boundaries, all lossless
  - test_wasm_node.mjs: 44-vector corpus, WASM ≡ native Rust
  - tools/wasm/browser-test/index.html: 29 assertions in Firefox headless

Note: CBOR wire does NOT preserve t:'int' vs t:'uint' for positive
values. Both encode as major type 0 (unsigned). The decoder returns
t:'uint' for non-negative, and t:'int' for negative. This is correct
semantic normalization, not information loss. Documented in the
precision test (i64::MAX → t:'uint' on decode).

invariant_statement:
The WASM ABI is a decimal-string boundary for u64/i64.
JavaScript Number is forbidden on that boundary.

---

## DEFECT-031 — getrandom wasm32 backend requires explicit opt-in

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4B
commit_found: <uncommitted, during 3A.4B build>
commit_fixed: <this stage commit>
suite: rust/adie-wasm/Cargo.toml, rust/adie-wasm/.cargo/config.toml
category: dependency
failure_mode: build-failure
invariant_at_risk: none (build-time only)

root_cause:
The transitive dependency graph of adie-primitives includes getrandom
in two major lines:
  - getrandom 0.2.x (pulled by some crypto dependency)
  - getrandom 0.4.x (pulled by a newer crypto dependency)

Neither backend is enabled by default on wasm32-unknown-unknown. Each
major line uses a DIFFERENT opt-in mechanism:
  - 0.2.x: crate feature "js"
  - 0.4.x: crate feature "wasm_js" AND rustc cfg
           --cfg getrandom_backend="wasm_js"

fix:
- rust/adie-wasm/Cargo.toml declares both under
  [target.'cfg(target_arch = "wasm32")'.dependencies]:
    getrandom_02 = { package = "getrandom", version = "0.2", features = ["js"] }
    getrandom_04 = { package = "getrandom", version = "0.4", features = ["wasm_js"] }
- rust/adie-wasm/.cargo/config.toml declares the rustc cfg:
    [target.wasm32-unknown-unknown]
    rustflags = ['--cfg', 'getrandom_backend="wasm_js"']

The reference crate rust/adie-primitives is UNCHANGED. The delivery
wrapper owns the target-specific adaptation.

lesson:
Cargo features are additive and graph-wide. A path-dependency crate
can activate features on shared transitive dependencies without
modifying the parent. This is the correct place for target-specific
adaptation: the delivery wrapper, not the reference.

---

## DEFECT-032 — wasm-bindgen nodejs output under ESM parent

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4B
commit_found: <uncommitted, during 3A.4B Node probe>
commit_fixed: <this stage commit>
suite: js/wasm-pkg-node/package.json
category: dependency
failure_mode: structural
invariant_at_risk: none (module loading only)

root_cause:
wasm-bindgen --target nodejs generates CommonJS output
(module.exports = ...). Node.js resolves module type from the
nearest package.json. js/package.json declares "type": "module",
which propagates to js/wasm-pkg-node/ (no local override). Node
therefore attempts to load adie_wasm.js as ESM, sees no export
statements in the CJS form, and returns an empty namespace object
(`exports: []`).

fix:
Added js/wasm-pkg-node/package.json with:
  { "type": "commonjs", "main": "adie_wasm.js" }

This is a loader hint. It does not modify the artifact. The
require('...') form works, exports become visible, and the same
binary is exercised end-to-end.

lesson:
When wasm-bindgen writes into a subtree under a "type":"module"
parent, the subtree MUST be pinned to CommonJS explicitly. This is
the fifth DEFECT in the family "library defaults that do not match
protocol/repo defaults" (DEFECT-021/025/026/028/032).

---

## GAP-3.4B-01 — wasm-bindgen nodejs CWD-relative wasm path

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4B
category: documentation
status: open (by design — known behavior)

description:
wasm-bindgen --target nodejs emits adie_wasm.js that loads the
companion wasm via a CWD-relative path ('./adie_wasm_bg.wasm').
Consumers must either run Node from within js/wasm-pkg-node/, or use
a path-resolving shim. This is a known limitation of the nodejs
target; not a defect in our wrapper. Documented here so future
integrators do not mistake the ENOENT for an ADIE failure.

impact: low. No protocol semantics affected. Delivery consumers
(applications) will typically use --target bundler or
--target web with a proper module resolution setup.


---

## DEFECT-033 — Build artifacts and toolchain binaries tracked

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.4B
commit_found: e710fa4
commit_fixed: 6982220 (partial: target/) + <this commit> (tools/wasm/ + docs)
category: process
failure_mode: repository-hygiene
invariant_at_risk: Build artifacts and third-party binaries MUST NOT
enter the permanent repository history.

root_cause:
The 3A.4B stage commit (e710fa4) used a single `git add rust/adie-wasm/`
glob. This tracked:
  - rust/adie-wasm/target/  (~750 files, ~90 MB of cargo output)
  - tools/wasm/wasm-bindgen, wasm-pack, wasm2es6js,
    wasm-bindgen-test-runner  (~39 MB of prebuilt binaries)

Neither path was in .gitignore. Git status inspection did not surface
the scale (~750 files).

fix (split across two commits):
  1. Commit 6982220:
       git rm -r --cached rust/adie-wasm/target
  2. This commit:
       git rm --cached tools/wasm/{wasm-bindgen, wasm-pack,
                                    wasm2es6js, wasm-bindgen-test-runner}
       Extend .gitignore with the paths above.
       Log DEFECT-033 and CONTINUITY §51.

Retained (tracked, intentional):
  - tools/wasm/LICENSE-APACHE, LICENSE-MIT, README.md
  - tools/wasm/browser-test/          (HTML test page + server.mjs)
  - tools/wasm/browser-test/pkg/      (generated distributable test
                                       artifact، ~240 KB، tied to
                                       index.html so the browser test
                                       runs on fresh clone without
                                       rebuild)

Future consumers obtain the binaries via a pinned-version download
script (tracked separately; not implemented in this commit).

lesson:
`git add <dir>/` is unsafe when a directory mixes source and build
output. Every directory with generated content MUST have an explicit
.gitignore entry BEFORE first add. The failure scales silently with
file count; pre-commit visual inspection is insufficient.

note:
Repository hygiene only. No protocol, code, test, or binary content
was altered. All Stage 3A.4B results remain valid:
Node 45/45, Precision 31/31, Browser 29/29, Native↔WASM 44/44,
regression 1120/1120.


---

## DEFECT-034 — jcs::canonical_bytes returns Result, not Vec

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.5-B+
commit_found: uncommitted, during 3A.5-B+ Phase B
commit_fixed: this stage commit
suite: rust/adie-primitives/src/cbor/envelope.rs
category: code
failure_mode: type-mismatch
invariant_at_risk: none (compilation only)

root_cause:
crate::jcs::canonical_bytes in the Rust crate returns
Result<Vec<u8>, String>, unlike the Python helper of the same name
which returns bytes directly. The initial envelope implementation
used it as if it returned Vec<u8>, producing two compile errors at
lines 235 and 249.

fix:
Add .map_err(...) at both call sites to translate the error into
CborError::Malformed with context.

lesson:
Cross-language symmetry of helper names does not imply symmetry of
error handling. Every call site must be checked against the actual
signature.


---

## DEFECT-035 — CborError::Malformed is a struct variant, not tuple

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.5-B+
commit_found: uncommitted, during 3A.5-B+ Phase B fix of DEFECT-034
commit_fixed: this stage commit
suite: rust/adie-primitives/src/cbor/envelope.rs
category: code
failure_mode: type-mismatch
invariant_at_risk: none (compilation only)

root_cause:
CborError::Malformed in the existing error module is declared as a
struct variant: Malformed { detail: String }. The envelope helper
malformed(msg: impl Into<String>) constructed it as a tuple variant
CborError::Malformed(msg.into()), which is not valid for a struct
variant.

fix:
Change the helper construction to
CborError::Malformed { detail: msg.into() }.

lesson:
Rust enum variants differ in shape (unit, tuple, struct). Every
construction must match the declared shape. The defect is
compile-time only; no runtime behavior was affected.


---

## DEFECT-036 — Cross-runtime rejection-code divergence on nested duplicate keys

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.6
commit_found: uncommitted, during 3A.6 fuzz pilot
commit_fixed: this stage commit
suite: tests/vomega/b-plus/test_bplus_fuzz.py
category: architecture
failure_mode: classification-divergence
invariant_at_risk: When multiple wire-level violations are present in
one input, all three runtimes MUST report the same ADIE error code,
or the protocol MUST declare which check has priority.

symptom (pilot 100):
  case=26 mut=zero_run: Rust=E_WIRE_TRAILING Py=E_WIRE_TRAILING JS=E_WIRE_DUP_KEY
  case=53 mut=zero_run: Rust=E_WIRE_MALFORMED Py=E_WIRE_MALFORMED JS=E_WIRE_DUP_KEY
  case=98 mut=zero_run: Rust=E_WIRE_MALFORMED Py=E_WIRE_MALFORMED JS=E_WIRE_DUP_KEY

root_cause:
JS rawcheck.mjs detected inner duplicate keys (per DEFECT-027).
Rust rawcheck.rs and Python rawcheck.py did NOT: they only detected
top-level duplicates (via the re-encode comparison in the decoder).
When the input contained both an inner duplicate key AND trailing
bytes, JS aborted at the duplicate (inside the map) while Rust/Py
walked to the end and aborted at trailing.

fix:
Extend both Rust scan_item (major=5 branch) and Python _scan_item
(major=5 branch) to detect byte-identical inner keys before walking
the value. This aligns them with JS rawcheck.

lesson:
An architectural decision (DEFECT-027: rawcheck owns duplicate-key
detection) must be enforced in every implementation, not just the
one that discovered it. Drift between runtimes is only visible under
adversarial inputs that combine multiple violations.

invariant_statement:
Rawcheck enforces duplicate-key rejection at wire level in every
runtime before the decoder runs. Classification priority is therefore
identical across Rust, Python, and JavaScript.


---

## DEFECT-037 — Patch application silently failed to insert helper

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.6
commit_found: uncommitted, during 3A.6 fix of DEFECT-036
commit_fixed: this stage commit
suite: rust/adie-primitives/src/cbor/rawcheck.rs
category: process
failure_mode: verification-gap
invariant_at_risk: none (process only)

root_cause:
The first attempt to insert `scan_map_body` into Rust rawcheck used
a string-replace that printed "OK helper inserted" but did not
actually write the helper. The subsequent build failed with E0425
(scan_map_body not found). A safer approach was then used: explicit
grep verification after the write, followed by build check.

fix:
Second insertion attempt used `raise SystemExit(0)` on already-present
check, `grep -n` verification, and post-build verification. The
helper was confirmed present before build.

lesson:
Every patch script that reports success MUST be followed by a
verification step (grep, file size, or build) before declaring the
patch effective. Silent no-op is worse than an explicit failure.


---

## DEFECT-038 — Python rawcheck missing inner duplicate-key detection

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.6
commit_found: uncommitted, during 3A.6 fix of DEFECT-036
commit_fixed: this stage commit
suite: protocol/wire/rawcheck.py
category: code
failure_mode: missing-check
invariant_at_risk: Wire-level inner duplicate keys MUST be rejected
at rawcheck in all runtimes.

root_cause:
protocol/wire/rawcheck.py `_scan_item` major==5 branch walked keys
and values without recording key byte ranges. Inner duplicates were
left to the decoder (cbor2 + re-encode comparison). When trailing
bytes were also present, rawcheck aborted at trailing before the
decoder could detect the duplicate, producing E_WIRE_TRAILING instead
of E_WIRE_DUP_KEY.

fix:
Extend the major==5 branch to record each key's byte range and
reject byte-identical duplicates with DuplicateKey, matching the
Rust and JS rawcheck behavior.

lesson:
This is the same class as DEFECT-036. Any invariant enforced by one
runtime's rawcheck MUST be enforced by all, otherwise cross-runtime
classification parity is silently broken.


---

## DEFECT-039 — JS walkTag skipped shortest-form check on tag number

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.6
commit_found: 4617df6 (during 3A.6 fuzz campaign, case 8443)
commit_fixed: <this commit>
suite: js/wire/rawcheck.mjs
category: code
failure_mode: missing-check
invariant_at_risk: The ADIE rejection priority for a tag with a
non-shortest argument MUST be E_WIRE_NONCANONICAL_INT (shortest-form
rule) before E_WIRE_TAG, matching Rust and Python.

symptom:
  case=8443 mut=insert: R=E_WIRE_NONCANONICAL_INT P=E_WIRE_NONCANONICAL_INT J=E_WIRE_TAG

minimal reproducer:
  envelope_hex = "d801"
  Rust / Python: E_WIRE_NONCANONICAL_INT
  JavaScript:    E_WIRE_TAG        (before fix)

root_cause:
js/wire/rawcheck.mjs `walkTag` read the tag number via `readAdditional`
and immediately threw `TagErr`. `readAdditional` does NOT enforce
shortest form (unlike Rust's read_length and Python's _read_length,
both of which check `b < 24` / `n < 256` / etc. before returning).
So the tag arm skipped the shortest-form rule that all other arms
enforce via `checkShortest`.

fix:
Insert `checkShortest(tag, ai)` inside `walkTag` before throwing
`TagErr`. This restores priority: non-shortest → NonCanonicalInt,
otherwise → Tag.

lesson:
Every CBOR arm that reads a length via `readAdditional` MUST either
call `checkShortest` explicitly or use a helper that does. The
tag arm was the only one without it. This kind of omission is only
visible when a fuzzer generates a byte sequence whose class depends
on which check runs first. Hand-authored vectors had tag and
non-shortest cases separately; the combined case was not covered.

regression vector:
tests/vomega/b-plus/fuzz_case_8443.json (saved). The minimal
reproducer `d801` should also be retained as a regression case in
the rawcheck tests.

invariant_statement:
Classification priority is part of the wire contract. If two
violations are present, all runtimes MUST pick the same one, in
the same order defined by WIRE-FORMAT-0.2 §9.

---

## DEFECT-040 — Commit message claimed 0/10k mismatch while 1/10k existed

date: 2026-10-07
phase: Phase 3, Gate 1, 3A.6
commit_found: 4617df6
commit_fixed: <this commit>
category: process
failure_mode: inaccurate-reporting
invariant_at_risk: The commit record is part of the audit trail.
It MUST reflect the exact measured result, not the intended result.

description:
Commit 4617df6 has the message:
  "... 0/10k rejection-code mismatches across Rust/Python/JS ..."
The measured result of that commit's fuzz run was:
  rejection code mismatch: 1
  case=8443 mut=insert: R=E_WIRE_NONCANONICAL_INT P=E_WIRE_NONCANONICAL_INT J=E_WIRE_TAG

The "0/10k" text was a projection from the 100-case pilot, written
before the 10k run completed. The actual result of the 10k run was
captured in the same shell output but not reflected back into the
commit message before the commit was pushed.

fix:
No code change. This defect is logged to make the record honest.
The correction is the current commit, whose message describes the
actual progression:
  10k run #1 (4617df6): 1 mismatch → fixed in this commit.
  10k run #2 (this commit): 0 mismatch (expected).

lesson:
A commit message is a claim. It must be derived from the exact
terminal output of the command that produced the result, not from
a prior intermediate run. The rule established in DEFECT-037
(verify after patch) extends to commit messages: verify the number
you are about to write into the permanent record.
