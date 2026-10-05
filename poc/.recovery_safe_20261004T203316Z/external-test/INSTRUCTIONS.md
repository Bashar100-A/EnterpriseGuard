# ADIE External Test — Instructions

You are being asked to test a **cryptographic verifier** for a system
called ADIE. You do not need to know anything about ADIE to complete
this test.

## What you are testing

A small Python script that checks whether a "decision certificate" has
been tampered with. The script is offline, needs no network, and has
no dependency on the ADIE project itself.

## Time required

Approximately **5–10 minutes**.

## Step 0 — Verify file integrity (Windows-safe)

Before running anything, verify the files were not corrupted during
transfer. Line-ending conversion (LF <-> CRLF) by some Windows
extraction tools can modify file bytes.

**On Linux / macOS:**

    sha256sum -c SHA256SUMS

**On Windows (PowerShell):**

    Get-Content SHA256SUMS | ForEach-Object {
      $parts = $_ -split '\s+', 2
      $expected = $parts[0]
      $file = $parts[1].TrimStart('*')
      $actual = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
      if ($actual -eq $expected) { Write-Host "OK: $file" }
      else { Write-Host "MISMATCH: $file" -ForegroundColor Red }
    }

**On any OS (Python):**

    python3 -c "
    import hashlib, pathlib
    for line in open('SHA256SUMS'):
        parts = line.split()
        if len(parts) < 2: continue
        expected, name = parts[0], parts[1].lstrip('*')
        actual = hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()
        print(f'{name}: ' + ('OK' if actual == expected else 'MISMATCH'))
    "

**If any file reports MISMATCH:** re-extract from the original
.tar.gz. Do not proceed.

## Step 1 — Install dependencies

**Recommended (any OS):** use a virtual environment.

    python3 -m venv .venv
    source .venv/bin/activate     # Linux/macOS
    # .venv\Scripts\activate      # Windows

    pip install cryptography jcs

**If you prefer not to use a venv on Ubuntu 23.04+ / Debian 12+:**
pip may refuse with `error: externally-managed-environment`. In that
case, use:

    pip install --user cryptography jcs

Or, as a last resort:

    pip install --break-system-packages cryptography jcs

**If you prefer not to use a venv on macOS with Homebrew Python:**

    pip install --user cryptography jcs

**Verify installation:**

    python3 -c "import cryptography, jcs; print('deps OK')"
    # Expected: deps OK

## Step 2 — Run three tests

### Test A — Valid certificate

    python3 verify.py certificate-001.json public-key-001.pem

Expected output: `VALID`

### Test B — Wrong public key

    python3 verify.py certificate-001.json wrong-key.pem

Expected output: `INVALID: E001_SIGNATURE_INVALID`

### Test C — Full suite (10 cases)

    python3 test_pstep02.py

Expected output ends with: `Results: 10/10 passed`

### Test D (optional, 30 seconds) — Second independent certificate

    python3 verify.py certificate-002.json public-key-001.pem

Expected output: `VALID`

This is a **different** certificate (different decision, different
inputs), verified with the same public key. If it also reports
`VALID`, the verifier is not overfit to a single example.

## Step 3 — Report back

Please report, in a single message:

1. Did Test A produce `VALID`? (yes / no)
2. Did Test B produce `INVALID: E001_...`? (yes / no)
3. Did Test C produce `10/10 passed`? (yes / no)
4. If you ran Test D: did it produce `VALID`? (yes / no / skipped)
4. Time you spent (in minutes).
5. Any error messages you saw.
6. One sentence: was anything confusing?

## What we do NOT ask

- We do not ask for your opinion on the idea.
- We do not ask you to trust us.
- We do not ask you to read the ADIE project files.
- We do not ask you for a recommendation.

We only want to know: **does it work in 10 minutes, on your machine,
without any help from us?**

## Files in this package

| File | Purpose |
|---|---|
| `verify.py` | The verifier (179 lines, no ADIE import) |
| `certificate-001.json` | A signed certificate (test fixture) |
| `public-key-001.pem` | The correct public key |
| `wrong-key.pem` | An incorrect key (for Test B) |
| `test_pstep02.py` | Automated suite (10 cases) |
| `README.md` | Full documentation |

## If something fails

Please copy the exact error message and paste it into your report.
**A failure is a useful result.** We would rather know now.

— End of instructions.
