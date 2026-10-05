## ADIE Independent Verification Protocol (v3 Fortified)
This packet tests the portability of the ADIE standalone cryptographic verifier.
## Pre-flight Setup
Ensure you have the required micro-dependencies installed:
bash pip install cryptography jcs --break-system-packages 
(If on Windows or standard Unix environment, you can drop the --break-system-packages flag or run inside a clean venv)
## Step 0: Integrity Validation
Verify that the files were not mangled during network transmission or unzipping:

* Linux/macOS: sha256sum -c SHA256SUMS
* Windows (PowerShell): Get-FileHash certificate-001.json, verify.py | Format-List

## Test A: Valid Verification (Expects: VALID)
bash python3 verify.py certificate-001.json public-key-001.pem 
## Test B: Attack Countermeasure (Expects: INVALID: E001_...)
bash python3 verify.py certificate-001.json wrong-key.pem 
## Test C: Adversarial Stress Test (Expects: 10/10 passed)
bash python3 test_pstep02.py 
