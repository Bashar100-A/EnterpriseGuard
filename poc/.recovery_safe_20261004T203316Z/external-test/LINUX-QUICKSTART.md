# Linux Quickstart (v3)

Environment: Any modern Linux (Ubuntu 22.04+, Debian 12+, Fedora 38+)
Shell: bash or zsh

## Step 0 — Verify file integrity

    sha256sum -c SHA256SUMS

Expected: every line ends with `: OK`.

## Step 1 — Install dependencies

Recommended (any Linux):

    python3 -m venv .venv
    source .venv/bin/activate
    pip install cryptography jcs

If pip refuses on Ubuntu 23.04+ / Debian 12+ with
"externally-managed-environment":

    pip install --user cryptography jcs

Verify:

    python3 -c "import cryptography, jcs; print('deps OK')"

Expected: deps OK

## Step 2 — Test A (valid)

    python3 verify.py certificate-001.json public-key-001.pem
    # Expected: VALID

## Step 3 — Test B (wrong key)

    python3 verify.py certificate-001.json wrong-key.pem
    # Expected: INVALID: E001_SIGNATURE_INVALID

## Step 4 — Test C (suite)

    python3 test_pstep02.py
    # Expected: Results: 10/10 passed

## Step 5 — Test D (second cert, optional)

    python3 verify.py certificate-002.json public-key-001.pem
    # Expected: VALID

## Step 6 — Report

Reply with:
- Step 0 result (all OK / which failed)
- Test A output
- Test B output
- Test C result
- Test D output (if run)
- python3 --version
- uname -a

If any test fails, paste the exact error.
