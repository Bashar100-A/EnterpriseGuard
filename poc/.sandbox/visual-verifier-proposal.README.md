# Proposal — Browser-Based Visual Verifier

**Status:** Proposal only. Not to be executed.
**Date:** 2026-10-04
**Source:** External script (ChatGPT or other AI model)

## Idea

A single HTML file that lets an auditor verify a decision
certificate entirely in the browser, with no Python installation.

## Why It's Valuable

- Gate 3 auditors won't install Python.
- Drag-and-drop is intuitive.
- Browser-native verification removes one barrier.

## Why This Version Cannot Be Used

### 1. Violates PR-05 (Standalone Verifier)
- Loads Forge from `https://cloudflare.com` (external CDN).
- Requires internet on first load.
- Creates external trust dependency.

### 2. CDN URL is Incorrect
- `https://cloudflare.com` is Cloudflare's main website.
- Correct URL: `https://cdnjs.cloudflare.com/ajax/libs/forge/...`
- Result: Forge will not load; verifier will crash.

### 3. JCS Implementation is Incorrect
```js
function jcsCanonicalize(obj) {
    return JSON.stringify(obj, Object.keys(obj).sort());
}
    Sorts only top-level keys.

    Does not recurse into nested objects.

    Not RFC 8785 compliant.

    Will produce false E002_HASH_MISMATCH on any nested structure.

4. Violates PR-04 (Frozen Phase P Scope)

    Adds a 5th file beyond the frozen 4.

    Scope change requires formal DEC.

5. Violates PR-06 (No External Modification)

    External script, not reviewed before application.

What a Correct Version Requires

To be usable in future:

    Offline-first: vendor Forge into the HTML file, or write
    pure-JS crypto using Web Crypto API (SubtleCrypto).

    Correct JCS: use a real RFC 8785 implementation, or vendor
    canonicalize npm package's logic.

    Match Python byte-for-byte: same output for same input.

    Tested against: certificate-001, certificate-002.

    Reviewed before poc/ application: per PR-06.

Decision

    Save as proposal.

    Do NOT execute.

    Revisit after Gate 3 (if auditors actually want browser tooling).

