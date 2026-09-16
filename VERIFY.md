# Verifying ADIE Reports

Anyone can independently verify an ADIE validation report in 3 steps.

## 1. Download the report and our public key
- adie_validation_report.json
- keys/adie_public.pem

## 2. Run the verifier

pip install cryptography
python3 verify_report.py adie_validation_report.json keys/adie_public.pem

## 3. Expected output

[OK] Report integrity CONFIRMED
[OK] Ed25519 signature VALID

If either check fails, do NOT trust the report.

## What gets verified

1. Report integrity - SHA-256 hash of the report body matches the claimed hash.
2. Signature - Ed25519 signature over the hash is valid against our public key.

## What this proves

- The report was produced by ADIE official validator (version pinned by hash).
- The report has not been modified after signing.
- The 148 tests passed at a specific Git commit, reproducible with --seed.

## Reproducing the test run

git checkout COMMIT_FROM_REPORT
python3 adie_validator.py --seed 42

You should get the exact same report hash.
