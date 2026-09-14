# Blockers

## BLOCKER-001: compliance_policy.json permissions
**Date:** 2026-09-10  
**File:** tools/compliance_policy.json  
**Issue:** Permissions were 0777 (world-writable).  
**Expected:** 0600  
**Action:** Fixed by `chmod 600` + commit `42f9bda`.  
**Status:** ✅ CLOSED

---

## BLOCKER-002: Git repository is severely incomplete
**Date:** 2026-09-10  
**Severity:** CRITICAL

**Issue:**  
A fresh `git clone` of the repository is missing most of the
project. Specifically:

- `tests/` — missing entirely
- `continuity/` — missing entirely
- `docs/` — only 6 files present
- `tools/` — missing many tools like `sibb_cli.py`,
  `hardware_identity.py`, `genesis_seed.py`, `innocence_chain.py`,
  `signing_backend.py`, `paths_config.py`, and others

**Impact:**  
Phase A gate ("any new person can run the product from zero in
<10 minutes") cannot be verified because the clone is not runnable.

**Root Cause:**  
Most project files have been `Untracked` in git since the project
began. They were never committed.

**Fix Plan:**  
1. Update `.gitignore` to protect sensitive and runtime files
2. Explicitly add source directories to git:
   `tools/`, `tests/`, `continuity/`, `docs/`, `deploy/`, `src/`
   (excluding forbidden subdirectories)
3. Ensure forbidden paths are NOT added:
   `src/enterpriseguard/adie/`, `src/enterpriseguard/intelligence/`
4. Ensure per-machine runtime state is NOT added:
   `tools/hardware_identity.json`, `tools/genesis_baseline.json`,
   `.env*`, `.venv/`, `backups/`
5. Commit and retry clean clone test

---

## BLOCKER-003: Quick Start bugs discovered by end-to-end test
**Date:** 2026-09-10  
**Severity:** HIGH (blocks Phase A gate)

**Bugs found during fresh-clone Quick Start test:**

1. `docs/QUICKSTART.md` used `genesis_seed.py --generate` which doesn't exist.
2. `docs/QUICKSTART.md` used `python` which may not be on PATH.
3. `tools/sibb_cli.py` did not add project root to `sys.path`.
4. `tools/sibb_cli.py` called `append_activity` with wrong signature.
5. `tools/sibb_cli.py` called `storage.verify()` instead of `verify_integrity()`.

**Status:** ✅ CLOSED — all 5 fixed and re-tested in fresh clone.

---

## BLOCKER-004: GPG Signing Key Lost

**Date:** 2026-09-12
**Severity:** HIGH
**Category:** Release integrity / Governance

**Issue:**
The GPG signing key created in DC-041 for release file signatures was lost. The keyring at `/home/bashar/.gnupg/` was destroyed when the original OS installation was reformatted to a new user profile (`/home/biss/`).

**Affected files (now archived):**
- `VERSION.asc`
- `CHANGELOG.md.asc`
- `TRUSTED_BASELINE_SENTINEL.json.asc`
- `integrity_baseline_sentinel.json.asc`
- `tools/TRUSTED_BASELINE.json.asc`
- `tools/integrity_baseline.json.asc`

**Key identity:**
- UID: `EnterpriseGuard ADIE <adie@enterpriseguard.local>`
- Long Key ID: `9188569AD7F609C869730CFB20AB83C64E6B50CB`
- Full fingerprint: never recorded (systematic failure)

**Root cause:**
1. Full fingerprint was not recorded at creation time.
2. No backup of the private key was taken.
3. The public key was never exported to a persistent location.

**Immediate action taken:**
- Files moved to `archive/signatures-2026-09-01-lost-key/`
- Retrospective documented as new DC entry

**Resolution plan:**
1. Modify `tools/sign_release.py` to pin a `GPG_KEY_ID`.
2. Generate new Ed25519 key with a strong passphrase.
3. Export public key to `deploy/keys/release_key_public.asc`.
4. Export encrypted private key to two external backup media.
5. Create `docs/RELEASE_KEY.md` with full fingerprint.
6. Re-sign the six critical files.

**Status:** 🔄 IN PROGRESS — key generation pending

## Behavioral Deviations Note — Phase C (Commit 7e0e12c)

- **Deviation 1 (Command Modification):**
  - **Observed:** Executed `git commit -F ...` omitting `--no-gpg-sign`.
  - **Impact:** None (repo `commit.gpgsign` was false), but represents unauthorized command modification.
  - **Mitigation:** Strict enforcement of verbatim command execution rule.

- **Deviation 2 (Fabricated Artifact URL):**
  - **Observed:** Generated fake GitHub organization URL for local-only commit `7e0e12c`.
  - **Impact:** High risk of false assumption regarding remote push status.
  - **Mitigation:** Strict rule prohibiting generation of unverified external URLs.
