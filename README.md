# ADIE — Autonomous Decision Governance Infrastructure

[![ADIE Validation](https://github.com/Bashar100-A/EnterpriseGuard/actions/workflows/adie-validate.yml/badge.svg)](https://github.com/Bashar100-A/EnterpriseGuard/actions/workflows/adie-validate.yml)
![Tests](https://img.shields.io/badge/tests-148%2F148-brightgreen)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Signed](https://img.shields.io/badge/reports-Ed25519%20signed-purple)

**Independent Control Plane for AI-Driven Enterprise Decisions.**

ADIE intercepts every AI-driven decision before execution, records it in a
hash-chained HMAC-signed ledger, and emits an Ed25519-signed proof - giving
auditors cryptographic evidence, not logs.

## Verify our latest report

Run: python3 verify_report.py adie_validation_report.json keys/adie_public.pem

Or open verify.html in any modern browser.

## Adversarial Validation Suite

148 real attack simulations across 6 MITRE ATT&CK-mapped vectors:
Crypto-Core, Time Spoofing, TOCTOU, Hard Fork, DoS Defense, Supply Chain.

## Reproducibility

Same seed produces same hash. Any third party can independently reproduce.

See VERIFY.md for details.

ADIE Public Key Fingerprint
============================
Algorithm: RSA-2048
Fingerprint (SHA-256 of DER):
99692745d8792e486dc0b002ccc2562f563b5c92a40499f57fa5a897e799fb08

Published: 2026-10-05
Verify with: openssl pkey -pubin -in public.pem -outform DER | openssl dgst -sha256 -hex
```

## Public Key Fingerprint

```
ADIE Public Key Fingerprint
============================
Algorithm: RSA-2048
Fingerprint (SHA-256 of DER):
5df07c90c4b346277e585d2a8b20283864dfb74b526c23cda6c993fc37b942a4

Public key: keys/adie-v1/public.pem
Self-signed cert: keys/adie-v1/selfsigned.pem
Published: 2026-10-05
Verify with: openssl pkey -pubin -in public.pem -outform DER | openssl dgst -sha256 -hex
```
