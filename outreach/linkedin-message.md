# LinkedIn message — to Internal Audit Lead, EU bank

Subject (if email): Decision integrity for AI — a working POC, not a pitch

---

Hi [Name],

You don't know me. I'll keep this short.

You probably have AI systems making credit decisions today, and an audit trail that's Excel files, screenshots, and trust.

Six months from now, when a regulator asks "prove decision 4291 wasn't altered," what will you show them?

I built a working answer. It's not a slide deck.

**60-second test, no signup:**

1. Open the repo: https://github.com/Bashar100-A/EnterpriseGuard
2. Download `verify.html` and `samples/`
3. Open `verify.html`, drag in `certificate-001.json` + `public.pem` → **VALID**
4. Drag in `certificate-001-TAMPERED.json` + same key → **INVALID: E002_HASH_MISMATCH**

That's it. Offline. No server. No vendor. 51 adversarial tests, all passing.

**What it proves:** the certificate was issued by the expected key, and no field was altered after issuance.
**What it does not prove:** that the decision was correct. Integrity ≠ Truth. The boundary is deliberate.

I'm not selling. I'm looking for 10 auditors to tell me honestly whether this artifact would be useful in their workflow — or whether it's solving the wrong problem.

If you have 10 minutes, try the demo and reply with one sentence: useful, or not useful, and why.

If not, no reply is fine. Thank you for reading.

— Bashar
adie-contact@proton.me
github.com/Bashar100-A/EnterpriseGuard

---

## Notes for you (not part of the message)

- Personalize `[Name]` for each recipient.
- If they're on LinkedIn, put the demo link in the message body.
- If by email, use the subject line above.
- Log every send in `outreach/sent.md`.
- Do NOT chase. One message, one reply window of 7 days.
