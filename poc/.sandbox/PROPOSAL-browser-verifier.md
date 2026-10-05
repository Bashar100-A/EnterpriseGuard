# Proposal — Browser-Based Visual Verifier

Status: Proposal only. Not to be executed.
Date: 2026-10-04
Source: External script (from another AI model).

## The Idea (Good)

A single HTML file that lets an auditor verify a decision certificate
entirely in the browser — no Python installation required.

## Why It's Valuable

- Gate 3 auditors won't install Python.
- Drag-and-drop is intuitive.
- Removes one barrier for real-world adoption.

## Why This Version Cannot Be Used

### 1. Violates PR-05 (Standalone Verifier)
- Loads Forge from https://cloudflare.com — an external CDN.
- Requires internet on first load.
- Creates external trust dependency.

### 2. CDN URL is Incorrect
- https://cloudflare.com is Cloudflare's main website.
- Correct URL: https://cdnjs.cloudflare.com/ajax/libs/forge/
- Result: Forge will not load; the verifier will crash.

### 3. JCS Implementation is Incorrect
function jcsCanonicalize(obj) {
    return JSON.stringify(obj, Object.keys(obj).sort());
}
- Sorts only top-level keys.
- Does not recurse into nested objects.
- Not RFC 8785 compliant.
- Will produce a false E002_HASH_MISMATCH on any nested structure.

### 4. Violates PR-04 (Frozen Phase P Scope)
- Adds a 5th file beyond the frozen 4.
- Scope change requires a formal DEC.

### 5. Violates PR-06 (No External Modification)
- External script, not reviewed before application.

## What a Correct Version Requires

1. Offline-first (vendor Forge, or use Web Crypto API).
2. Correct RFC 8785 JCS implementation.
3. Match Python byte-for-byte.
4. Tested against certificate-001 and certificate-002.
5. Reviewed before poc/ application (per PR-06).

## Decision

- Preserve as proposal.
- Do NOT execute.
- Revisit after Gate 3 (if auditors actually request browser tooling).
