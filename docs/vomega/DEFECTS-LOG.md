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
