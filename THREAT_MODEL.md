# ADIE Threat Model

**Version:** 1.0 | **Published:** 2026-10-05

## What ADIE proves
- Certificate issued by holder of private key matching `issuer_fingerprint`.
- No field altered after issuance (RFC 8785 canonical + RSA signature).
- Certificate not expired.
- Fingerprint in cert matches fingerprint of verification key.

## What ADIE does NOT prove
- Decision was correct.
- AI model was accurate.
- Input data was truthful.
- Policy was appropriate.
- Decision even occurred.

This is **Integrity ≠ Truth**.

## Threat model — POC v1.0

| # | Threat | Mitigation | Residual | Planned |
|---|---|---|---|---|
| T01 | Content altered | RFC 8785 + signature (B01–B07) | None | — |
| T02 | Signature tampered | base64 + RSA verify (E01–E04) | None | — |
| T03 | Key substitution | `issuer_fingerprint` in cert (C01–C04) | Verifier must get correct key | X.509 v1.1 |
| T04 | Expired cert used | `expires_at` checked (D01–D02) | None | — |
| T05 | Bad timestamp order | `issued_at <= expires_at` (D03) | None | — |
| T06 | Missing field | 10 required fields (F01–F05) | None | — |
| T07 | Malformed JSON | Schema check (F06–F09) | None | — |
| T08 | Invalid UTF-8 | Decode check (J01) | None | — |
| T09 | Version downgrade | `version == 1.0` (B08) | None | — |
| T10 | Replay old cert | `nonce` + `expires_at` | No server registry | v1.1 |
| T11 | Key compromise | None | High | v1.1 revocation |
| T12 | GitHub compromise | Multiple fingerprint channels | Single point | v1.1 X.509+CT |
| T13 | Issuer repudiation | Signature non-repudiable | Key custody | v1.1 HSM |
| T14 | Verifier tampered | 196 LOC, open source | Browser trust | v1.1 checksum |

## Trust anchor — how you know the key is right

**Procedure:**
1. Compute fingerprint of received key: `openssl pkey -pubin -in public.pem -outform DER | openssl dgst -sha256 -hex`
2. Compare to published: `5df07c90c4b346277e585d2a8b20283864dfb74b526c23cda6c993fc37b942a4`
3. If match → authentic. If not → stop.

Published in: `PUBLIC_KEY_FINGERPRINT.txt`, verifier UI, every certificate.

## Known limitations of POC v1.0
- No key revocation, rotation, HSM, X.509 chain, CT log, server-side nonce.
- Trust anchor relies on GitHub.

## Adversarial coverage
`tests/adversarial/run_all.py` — **51 tests, 100% pass.**
