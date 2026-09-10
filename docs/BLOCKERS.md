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
