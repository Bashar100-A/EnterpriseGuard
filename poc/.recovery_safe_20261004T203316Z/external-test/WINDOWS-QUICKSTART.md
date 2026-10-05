# Windows Quickstart (v3)

Environment: Windows 11 + Python 3.12
Shell: PowerShell (recommended) or CMD

## Step 0 — Verify file integrity

    Get-Content SHA256SUMS | ForEach-Object {
      $parts = $_ -split '\s+', 2
      if ($parts.Count -lt 2) { return }
      $expected = $parts[0]
      $file = $parts[1].TrimStart('*')
      $actual = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
      if ($actual -eq $expected) { Write-Host "OK:      $file" }
      else { Write-Host "MISMATCH: $file" -ForegroundColor Red }
    }

Expected: all lines print "OK:".

## Step 1 — Install dependencies

    python -m pip install --user cryptography jcs
    python -c "import cryptography, jcs; print('deps OK')"

## Step 2 — Test A (valid)

    python verify.py certificate-001.json public-key-001.pem
    # Expected: VALID

## Step 3 — Test B (wrong key)

    python verify.py certificate-001.json wrong-key.pem
    # Expected: INVALID: E001_SIGNATURE_INVALID

## Step 4 — Test C (suite)

    python test_pstep02.py
    # Expected: Results: 10/10 passed

## Step 5 — Test D (second cert, optional)

    python verify.py certificate-002.json public-key-001.pem
    # Expected: VALID

## Step 6 — Report

Reply with:
- Step 0 result (all OK / which files mismatch)
- Test A output
- Test B output
- Test C result
- Test D output (if run)
- python --version

If any test fails, paste the exact error.

## CMD alternatives

Hash check:

    certutil -hashfile verify.py SHA256
    certutil -hashfile certificate-001.json SHA256
    certutil -hashfile certificate-002.json SHA256

Steps 1-5 identical.
