# Browser Verification (no Python required)

For auditors who cannot or will not install Python.

## Requirements

- A modern browser (Chrome, Edge, Firefox; Safari with caveat below).
- The two files: `certificate-001.json` and `public-key-001.pem`.

## Steps

1. **Open** `visual-verifier-v2.html` by double-clicking it.

2. **Drag** `certificate-001.json` into the first box.

3. **Drag** `public-key-001.pem` into the second box.

4. **Click** "Verify Certificate".

5. **Read the result.**

## Expected Outputs

### With a valid certificate

    ✓ VALID

    Decision ID: dec-poc-001
    Issuer: adie-poc-001
    Content Hash: sha256:e751b663...
    Fingerprint: sha256:6337c84b...

    The certificate integrity is confirmed.
    This proves the artifact has not been altered.
    It does NOT prove the decision was correct.

### With a tampered certificate

    ✗ INVALID: E002_HASH_MISMATCH

### With the wrong public key

    ✗ INVALID: E001_SIGNATURE_INVALID

## What This Proves

- The certificate has not been altered since issuance.
- The signature was produced by the holder of the corresponding
  private key.
- The content hash matches the signed assertion.

## What This Does NOT Prove

- That the decision was correct.
- That the AI model was accurate.
- That the input data was true.
- Compliance with any regulation.

## Browser Compatibility

| Browser | `file://` | Notes |
|---|---|---|
| Chrome | ✅ Works | |
| Edge | ✅ Works | |
| Firefox | ✅ Works | May need `privacy.file_unique_origin=false` |
| Safari | ⚠️ Requires HTTPS or localhost | Use `python3 -m http.server 8080` |

## If Web Crypto is unavailable

The page will display a warning. Open via localhost:

    cd <folder with the two files>
    python3 -m http.server 8080

Then open: `http://localhost:8080/visual-verifier-v2.html`

## Zero-Network Guarantee

This page has no CDN dependency, no fonts, no analytics, no external
calls. Once loaded, it works entirely in the browser.

You can verify this by opening the browser's Network tab — you will
see no outbound requests.
