# ADIE — Gate 2 Pre-Audit Blueprint

**Status:** Operational reference
**Purpose:** Pre-planned decision tree for analyzing the external
developer's report on the P-STEP-02 POC.
**Rule:** No interpretation after the fact. Every scenario has a
pre-committed meaning.

---

## §0 — Inputs We Expect

The developer will send a short message. We expect it to contain:

1. Result of Test A (VALID / not).
2. Result of Test B (INVALID: E001 / not).
3. Result of Test C (10/10 / not).
4. Time spent.
5. Any error messages.
6. One sentence about confusion.

We do NOT expect: opinions, recommendations, or third-party references.

---

## §1 — PASS Scenarios

### S1.1 — Clean PASS

**What we see:**
- Test A -> VALID
- Test B -> INVALID: E001_SIGNATURE_INVALID
- Test C -> 10/10 passed
- Time <= 10 minutes
- No confusion reported

**Meaning:** Gate 2 Technical Truth = PASS.

**Action:**
1. Record the developer's full message.
2. Move to Gate 3 (Commercial Pilot Draft).
3. Do NOT reinterpret as "success of the idea" — only of the POC.

### S1.2 — PASS with friction

**What we see:**
- 3/3 tests pass, BUT
- Time > 10 minutes, OR
- One step reported as confusing.

**Meaning:** Gate 2 Technical Truth = PARTIAL PASS.

**Action:**
1. Identify the specific step that caused friction.
2. If friction is documentation -> fix INSTRUCTIONS.md or README.md.
3. If friction is a missing dependency check -> add pre-flight to verify.py.
4. If friction is Python version related -> document supported range.
5. Re-run with the same developer (or a second one) after fix.
6. Do NOT proceed to Gate 3 until PARTIAL becomes clean.

### S1.3 — PASS with unusual environment note

**What we see:**
- 3/3 tests pass, BUT
- Developer mentions their OS/version differs from ours
  (e.g., Windows 11 + Python 3.12, macOS + Python 3.13, WSL).

**Meaning:** Gate 2 Technical Truth = PASS, with a portability note.

**Action:**
1. Confirm the OS/Python combination.
2. Add it to poc/README.md under "Tested Environments".
3. If the developer used pip install cryptography jcs successfully ->
   we know the deps are installable there.
4. If they had to manually install -> record for packaging concerns.

---

## §2 — PARTIAL Scenarios (1 or 2 tests fail)

### S2.1 — Test A fails: certificate reports INVALID

**Possible causes (ranked by likelihood):**

| # | Cause | Test |
|---|---|---|
| 1 | jcs version mismatch | python -c "import jcs; print(jcs.__file__)" |
| 2 | Python 3.13+ behavior change | python --version |
| 3 | Operating system line-ending (CRLF) | file certificate-001.json |
| 4 | Public key file modified in transfer | compare SHA-256 of public-key-001.pem |
| 5 | Developer modified the certificate | ask directly |

**Action:**
1. Ask the developer for:
   - python --version
   - pip show cryptography jcs
   - uname -a (or Windows equivalent)
   - SHA-256 of the four files they received
2. Compare with our versions.
3. Re-run locally with matching version, if possible.
4. If we can reproduce -> fix and re-issue.
5. If we cannot reproduce -> ask for verify.py stdout/stderr exactly.

**Do NOT:**
- Blame the developer.
- Assume POC is broken.
- Assume developer did something wrong.

### S2.2 — Test B fails: wrong key accepted

**This is the most serious scenario.**

**Meaning:** Signature verification has a bug.

**Action:**
1. Immediately halt Gate 2 (do not proceed to Gate 3).
2. Ask developer to share: verify.py line count, Python version,
   cryptography version.
3. Re-run locally:
   python3 verify.py certificate-001.json wrong-key.pem
   If our local gives INVALID but theirs gives VALID -> environment issue.
   If ours also gives VALID -> we have a real bug.
4. If real bug: open a CRITICAL record. Do not accept any Gate 2
   result until fixed.

### S2.3 — Test C fails (fewer than 10)

**Possible causes:**
- Environment-specific (Unicode handling in Windows console).
- jcs behavior differences.
- One specific TC case is environment-dependent.

**Action:**
1. Ask which TC numbers failed.
2. Re-run those specific cases locally.
3. If they fail locally too -> fix.
4. If they pass locally -> environment-specific. Document. Consider
   making that TC "environment-sensitive" and marking it clearly.

---

## §3 — FAIL Scenarios (3 fail or environment error)

### S3.1 — Setup fails (pip install fails)

**Possible causes:**
- No internet, no pip.
- Corporate proxy.
- Python not installed at all.

**Meaning:** Not a POC failure. A setup failure.

**Action:**
1. Ask which step failed exactly.
2. Provide a fallback: vendored wheels, or a Docker image.
3. Record the fallback as a future packaging requirement.
4. Re-run with a different developer on a standard environment.

### S3.2 — Python version incompatible

**What we see:**
- Developer reports SyntaxError, ImportError, or TypeError.

**Action:**
1. Determine the version.
2. If < 3.10 -> document as unsupported; ask developer to upgrade.
3. If 3.11 - 3.13 -> investigate; likely fixable.
4. If >= 3.14 -> document as untested.

### S3.3 — Certificate file "looks different" after transfer

**Possible cause:** Line-ending conversion (CRLF vs LF), encoding, or
byte re-encoding.

**Diagnostic:**
1. Ask developer: sha256sum certificate-001.json (or Windows equivalent).
2. Compare with the original hash we computed locally.
3. If different -> transfer issue.
4. Fix: ship the certificate with explicit \n line endings, or transfer
   as .tar.gz and extract.

---

## §4 — OS-Specific Diagnostics

### Windows-specific risks

| Risk | Symptom | Mitigation |
|---|---|---|
| CRLF conversion on copy | Hash mismatch | Verify .tar.gz extraction preserves bytes |
| Console encoding (cp1252) | UnicodeError on output | Use python3 -X utf8 or set PYTHONUTF8=1 |
| pip not on PATH | pip not found | Use python -m pip |
| Python from Microsoft Store | Different path behavior | Document python3 vs python |

### macOS-specific risks

| Risk | Symptom | Mitigation |
|---|---|---|
| Python from Homebrew vs System | Version confusion | Document which python3 |
| ARM64 (cryptography binaries) | Install issues | Use latest cryptography |
| pip install --user conflicts | Permission error | Use venv |

### Linux-specific risks

| Risk | Symptom | Mitigation |
|---|---|---|
| Multiple Pythons | Wrong version used | Document python3 --version |
| System pip blocked (PEP 668) | error: externally-managed-environment | Use venv |

**Universal fix:** Always recommend a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate     # or .venv\Scripts\activate on Windows
    pip install cryptography jcs

Add this to INSTRUCTIONS.md preemptively for the next round.

---

## §5 — Decision Matrix

| Scenario | Gate 2 Result | Next Step |
|---|---|---|
| 3/3 PASS, <= 10 min, no friction | PASS | Move to Gate 3 |
| 3/3 PASS, > 10 min, or friction | PARTIAL PASS | Fix, re-test |
| 1-2 fail, environment-specific | PARTIAL FAIL | Document env, re-test |
| 1-2 fail, locally reproducible | FAIL (bug) | Fix before re-test |
| 3 fail or setup failure | INCOMPLETE | Address, re-run |
| Test B accepts wrong key | CRITICAL | Halt, fix, re-test |

---

## §6 — What Each Outcome Means (Strategic)

**PASS:**
- An independent developer, on their machine, in a standard environment,
  verified the certificate.
- This is the first external evidence that the POC is portable.
- It does not mean the idea is right, the market exists, or the
  product is sellable.

**PARTIAL PASS:**
- The technical core works, but packaging / documentation needs work.
- This is normal. Almost every POC goes through this.
- It does not mean the architecture is wrong.

**FAIL (bug):**
- We have a real defect. This is valuable — better found now than at a
  customer site.
- Record as an explicit defect. Do not hide.

**INCOMPLETE:**
- No signal. Try another developer.
- Do not interpret as failure.

---

## §7 — What We Do NOT Do After the Response

- We do not celebrate a PASS as if the idea is validated.
- We do not treat a FAIL as a reason to abandon.
- We do not "clarify" the developer's report with interpretation.
- We do not send a second copy with modified files without a new hash.

---

## §8 — Logging

Every response — PASS, FAIL, or INCOMPLETE — is logged verbatim in
poc/gate2/<timestamp>-response.txt, along with:

- OS, Python version, cryptography, jcs versions.
- Time to complete.
- Any file hashes the developer reported.

This log becomes part of Gate 2 evidence.

**End of Pre-Audit Blueprint.**
