# Verifiable Decision Certificates for Audit

**For:** Internal Audit Leads at EU banks
**Context:** DORA / AI Act
**Date:** 2026-10-04

## The Problem You Face Today

When an AI system makes a consequential decision (e.g., loan
rejection), and later audit or a regulator asks "what happened?", you
have to:

- Pull logs from multiple systems
- Reconcile timestamps manually
- Produce a PDF report
- Ask the regulator to trust your report

**None of these can be independently verified** by the regulator.
Everything depends on your institution's word.

## What We Provide

A **decision certificate** — a small file (JSON) that any third party
can verify **offline**, in **5 minutes**, without contacting you.

The certificate proves:
- A specific decision was issued by your system.
- It was issued under a declared policy and authority (as **signed
  assertions**).
- The certificate has not been altered since issuance.

**The verifier is 179 lines of Python.** Anyone can read it.

## What It Does NOT Prove

We are explicit:

- It does **not** prove the decision was correct.
- It does **not** prove the AI model was accurate.
- It does **not** prove the input data was true.
- It does **not** prove compliance with any regulation.

**We only prove integrity.** Interpretation is left to you and the
regulator.

## A Concrete Example

The certificate contains:
- Decision ID, timestamp, policy ID, authority ID
- A cryptographic hash of the decision contract
- A cryptographic fingerprint binding all evidence (via RFC 6962 Merkle
  tree)
- An RSA-2048 signature over the fingerprint

An auditor runs:

    python3 verify.py certificate.json public-key.pem

Output: `VALID` or `INVALID: <specific reason>`.

That's it.

## Why This Matters to You

- **Audit prep time**: You stop extracting logs; you receive a
  certificate.
- **Independent re-verification**: A regulator can verify 2 years later,
  without your help.
- **No blind trust**: The regulator does not have to trust your report.
- **Time-bounded**: Verification takes 5 minutes, not 5 days.

## What We Are Asking (Today)

Nothing yet. We want **20 minutes** of your time to:

1. Understand how you currently prepare AI decision evidence.
2. Show you the certificate and verifier.
3. Ask whether this would help.

If it's useful, we can discuss a **7-day pilot** later. No commitment
today.

## Contact

[Your name]
[Your email]
[Your LinkedIn]

**No sales. Only questions.**
