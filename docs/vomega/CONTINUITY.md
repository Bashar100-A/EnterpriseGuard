# ADIE — نقطة استمرارية vΩ

**التاريخ:** 2026-10-06
**الفرع النشط:** `vOmega`
**آخر commit:** `1aea20f` (Phase 1)
**المُجمَّد:** `master`, `gh-pages`, tag `v1.0-poc`

---

## 1. حالة المستودع الفعلية

### الفروع

| الفرع | الدور | الحالة |
|---|---|---|
| `master` | POC v1.0 المجمَّد | untracked: `outreach/email-regulator.md`, `outreach/linkedin-message-big4.md` |
| `gh-pages` | GitHub Pages (verify.html) | HTTP 200 |
| `vOmega` | فرع التطوير النشط | Phase 1 مكتمل |

### ملفات POC المُجمَّدة (موجودة فعلاً)

```
verify.html                       ✅
tests/adversarial/run_all.py       ✅ (51/51 ناجح)
PUBLIC_KEY_FINGERPRINT.txt         ✅
keys/adie-v1/                      ✅
THREAT_MODEL.md                    ✅
README.md                          ✅
docs/ADIE-v1.1.md                  ✅
docs/ADIE-v1.1-ar.md               ✅
samples/                           ✅
```

### ملفات كان يُفترض وجودها ولم تُنشأ

```
adie-cli-v2.py                     ❌ غير موجود
spec/ACL-0.1.md                    ❌ غير موجود
acl/python/eval.py                 ❌ غير موجود
acl/js/eval.mjs                    ❌ غير موجود
spec/CLAIM-SEMANTICS-v3.md         ❌ غير موجود
docs/ADIE-MASTER-PLAN.md           ❌ غير موجود
```

**السبب:** أوامر `cat > ... << 'EOF'` في الجلسات السابقة إما فشلت أو لم تُشغَّل فعلاً. **لا نعيد بناءها الآن** — Phase 1 تجاوزها بـ`protocol/core/`.

---

## 2. Phase 1 — ما بُني فعلاً

### البنية

```
protocol/
├── __init__.py                     (مفقود — يجب إنشاؤه)
└── core/
    ├── __init__.py                 (مفقود — يجب إنشاؤه)
    ├── domain_hash.py              ✅ H_A + FIELD_REGISTRY + STATUS_*
    ├── jcs.py                      ✅ strict_load + canonical_bytes
    ├── claim_root.py               ✅ compute_claim_root + 14-leaf Merkle
    ├── binding.py                  ✅ verify_binding + request_hash
    └── verify_pipeline.py          ✅ issue_dcp20 + verify_dcp20
tests/vomega/
└── run_all.py                      ✅ 12/12 attack vectors
```

**ملاحظة:** ملفات `__init__.py` غير موجودة، لكن الكود يعمل لـPython 3 implicit namespace packages. يجب إضافتها قبل أي packaging.

### المعايير المُثبَّتة

- **H_A(t,x)** = SHA256(`"ADIE/vOmega/2/"` || u16(|t|) || t || x)
- **14 domain tags** ثابتة في `FIELD_REGISTRY`
- **3 status codes**: `0x00 ABSENT` / `0x01 PRESENT` / `0x02 NULL`
- **Merkle** بـpadding إلى next-power-of-2 (لا "duplicate-last-leaf")
- **JCS** يرفض: duplicates, floats, NaN/Inf, int > 2^53, non-NFC strings, control chars
- **Binding** بأرقام purpose مُسجَّلة (7 = DEPLOYMENT_AUTHORIZATION)

### نتائج الاختبار

```
tests/vomega/run_all.py:       12/12 PASS
tests/adversarial/run_all.py:  51/51 PASS
git diff master..vOmega -- <frozen>: فارغ
```

### الـ12 attack vector المُغطَّاة

| ID | Attack | الحالة |
|---|---|---|
| 001 | Policy version substitution | ✅ E_CLAIM_ROOT_MISMATCH |
| 002 | Trust anchor circularity | ✅ E_SIGNATURE |
| 003 | Audience confusion | ✅ E_BINDING_AUDIENCE_MISMATCH |
| 004 | Extension injection | ✅ E_CLAIM_ROOT_MISMATCH |
| 005 | Number representation | ✅ E_CLAIM_ROOT_MISMATCH |
| 006 | Duplicate JSON member | ✅ E_CANONICAL |
| 007 | Unicode confusable | ✅ E_BINDING_AUDIENCE_MISMATCH |
| 008 | Algorithm downgrade | ✅ E_SIGNATURE |
| 009 | Model artifact swap | ✅ E_CLAIM_ROOT_MISMATCH |
| 010 | Training lineage swap | ✅ E_CLAIM_ROOT_MISMATCH |
| 011 | WASM binary replacement | ⏳ stub (Phase 2) |
| 012 | Split-view log | ⏳ stub (Phase 5) |

---

## 3. الالتزامات المعمارية المُعتمَدة

**من vΩ blueprint (33 invariant):**

```
I1   Integrity ≠ Truth
I2   Cryptographic validity ≠ Real-world truth
I3   DID ≠ Trust Anchor
I4   Transparency ≠ Root of Trust
I5   Proof ≠ Trust
I6   ADIE Protocol ≠ ADIE Vendor
I13  Meta-State transitions are deterministic
I14  No silent semantic upgrade
I15  No silent semantic downgrade
I16  Signature ≠ semantic validity
I17  Compatibility is explicit
I18  No implicit semantic dependencies
I19  Critical meta universe is finite and declared
I20  Authoring closure is complete
I21  ACL execution is pure
I22  Offline revocation uncertainty is observable
I23  Canonical identity ≠ complete semantic equivalence
I24  Historical claims are immutable
I25  Reappraisal creates new state, never mutation
I26  Algorithm migration does not resurrect broken signatures
I27  Unknown critical objects fail closed
I28  Browser WASM is not a root of trust
I29  ZK ≠ Truth
I30  FHE ≠ Side-channel immunity
I31  Recursive proof ≠ Reality Oracle
I32  History-independent verification ≠ universal O(1)
I33  Offline ≠ Timeless
```

**الالتزامات العشرة vΩ.3 (I13–I22):** سارية.

---

## 4. ترتيب التنفيذ المُعتمَد (32 خطوة)

```
0.  Freeze POC                     ✅ (tag v1.0-poc)
1.  DCP 2.0                        ✅
2.  ClaimRoot + Binding            ✅
3.  63-test baseline               ✅ (12 + 51)
4.  META contract                  ⏳ التالي
5.  ACL executable semantics       ⏳
6.  Authoring compiler             ⏳
7.  Registry + compatibility       ⏳
8.  Pilot claim                    ⏳
9.  Python verifier                ⏳
10. Rust independent verifier      ⏳
11. Differential tests             ⏳
12. Governance ceremony            ⏳
13. Hybrid RS256 + ML-DSA          ⏳
14. WASM adapter                   ⏳
15. Model/weight provenance        ⏳
16. ZK-0                           ⏳
17. Transparency                   ⏳
18. Recursive state                ⏳
19. Regional/global aggregation    ⏳
20. Enterprise SDK                 ⏳
21. Privacy-preserving metering    ⏳
22. Security review                ⏳
23. External pilot                 ⏳
24. Interoperability program       ⏳
25. Standardization                ⏳
```

**القاعدة الحاكمة:** لا خطوة تتجاوز سابقتها.

---

## 5. الخطوة التالية المحددة

**Phase 1.5 — META-CONTRACT-0.1**

الموقع المقترح: `docs/vomega/META-CONTRACT-0.1.md`

المحتوى المطلوب (12–15 صفحة):
- §1 State machine (F_M, events)
- §2 Meta Object schema
- §3 I13–I22 مفصَّلة
- §4 Attack matrix M01–M40
- §5 Implementation Independence criteria
- §6 Assurance Vector extension
- §7 TV triple provenance
- §8 Spec division
- §9 Execution order
- §10 MetaScore

**لا يُنفَّذ Phase 2 قبل أن يُجمَّد هذا العقد.**

---

## 6. قواعد صارمة

| ✅ افعل | ❌ لا تفعل |
|---|---|
| التزم على `vOmega` | لا تلمس `master` أو `gh-pages` |
| احتفظ بـPOC v1.0 كمرجع | لا تعدّل `verify.html` أو `tests/adversarial/run_all.py` |
| شغّل 51/51 + 12/12 قبل كل commit | لا تُعلن، لا ترسل، لا تنشر |
| سجّل كل قرار في `CONTINUITY.md` | لا تبدأ Phase 2 قبل META contract |
| استخدم `H_A` مع domain tag دائماً | لا تُعِد استخدام digest عبر domains |
| أضف `__init__.py` قبل أي packaging | لا تفترض وجود ملفات لم تُنشأ |

---

## 7. مقاييس مُعتمَدة (لا تُرفَع)

| البُعد | الدرجة الفعلية |
|---|---|
| Architectural Philosophy | 9.7 / 10 |
| Technical Specification | 7.3 / 10 |
| Execution Plan | 5.8 / 10 |
| Standardization Readiness | 4.8 / 10 |

**لا تُرفع الدرجات بسبب التصميم. تُرفع فقط عند اجتياز gates فعلية.**

---

## 8. روابط مهمة

| المورد | الرابط |
|---|---|
| المستودع | `https://github.com/Bashar100-A/EnterpriseGuard` |
| فرع vOmega | `https://github.com/Bashar100-A/EnterpriseGuard/tree/vOmega` |
| GitHub Pages | `https://bashar100-a.github.io/EnterpriseGuard/verify.html` |
| البريد | `adie-contact@proton.me` |

---

## 9. ما يجب فعله عند استئناف الجلسة

```bash
cd ~/Desktop/EnterpriseGuard
git branch --show-current          # vOmega
git log --oneline -3
python3 tests/vomega/run_all.py    # 12/12
python3 tests/adversarial/run_all.py # 51/51
cat docs/vomega/CONTINUITY.md
```

**ثم ابدأ من §5 (Phase 1.5 — META-CONTRACT-0.1).**

---

## 10. تحديث — Phase 1.5 مكتمل

**التاريخ:** 2026-10-06
**Commit:** `3c27aa8`
**الملف:** `docs/vomega/META-CONTRACT-0.1.md` (699 سطر)

**المُعتمَد:**
- 10 invariants I13–I22
- 40 attack vector M01–M40
- TV triple provenance (SPEC/FORMAL/ATTACK)
- K_ACL = consistency oracle (لا مصدر حقيقة)
- تقسيم spec: CORE / ACL / META / WIRE / PROOF / OPS
- ترتيب تنفيذ 25 خطوة

**الخطوة التالية:** Phase 1.6 — بناء meta-layer تنفيذي + اختبارات M01–M40.

**ملاحظة صدق:** META-CONTRACT لا يدّعي formal verification. يدّعي pinning + finiteness + determinism + honesty. هذا الادعاء الأقصى المسموح.

---

## 11. تحديث — Phase 1.6 مكتمل

**التاريخ:** 2026-10-06
**الملفات الجديدة:**
- `protocol/meta/core.py`
- `tests/vomega/meta/run_all.py`

**النتيجة:** 39/40 في الالتزام الأول `99c8376` (M19 كان معطوباً في الاختبار نفسه، ليس في الكود).
**تصحيح:** M19 أُعيد كتابته ليختبر منع الـaliasing الضمني (I14) — وليس تكرار M06. النتيجة بعد التصحيح: 40/40. **جميعها `real` — لا stubs.**

**التغطية الفعلية:**
- MetaObject + type registry (M07, M11, M21)
- Registry مع digest pinning (M01, M05, M06, M13, M19, M20, M26)
- StateMachine مع epoch/determinism/freeze (M08, M25, M28, M37, M39)
- Manifest مع threshold (M10)
- KeyState مع role+state (M14, M15)
- Compiler مع declared params + env isolation (M02, M03, M12, M16, M24, M30, M32, M36, M38)
- Universe contains_* (M17, M18, M31)
- Compatibility: no inference (M04, M23, M29, M35)
- Purity: check_purity with forbidden imports (M27, M33)
- Offline: verify_offline (M09, M22, M34, M40)

**Total tests: 51 (frozen) + 12 (vΩ Phase 1) + 40 (vΩ Phase 1.6) = 103**

---

## 12. Phase 1.7 مغلق (ACL-0.1)

- commit: d39fb02 (ACL) + 2a2a71a (DEFECTS-LOG)
- suites: 51/51 + 12/12 + 40/40 + 40/40 = 143/143
- spec/ACL-0.1.md (119 سطر)
- protocol/acl/{__init__,ast,eval,normalize}.py
- tests/vomega/acl/run_all.py (40 vector)
- عيبان مُصحَّحان: DEFECT-001 (M19), DEFECT-002 (A25)
- القاعدة الجديدة: كل عيب اختبار → DEFECTS-LOG.md
- التالي: Phase 1.8 Authoring Compiler

---

## 13. Phase 1.9 (spec) — REGISTRY-0.1

**commit:** 1d4f1dc
**suites:** 163/163 (51+12+40+40+20)

**المُثبَّت:**
- spec/REGISTRY-0.1.md (169 سطر)
- ERROR-REGISTRY-0.1: E-META-23..28

**الحالة:**
- registry.py غير مكتوب
- registry_run.py غير مكتوب
- ADIE-PHYSICAL-ANCHOR-0.1.md مؤجل حتى اكتمال التنفيذ

---

## 14. تصنيف وثيقة Physical Anchor

**المصدر:** وثيقة القائد — Ontological Anchoring & Layer-2
**التصنيف:** NON-NORMATIVE — North Star supplement
**القيد:** لا تلمس META-CONTRACT / ACL / AUTHORING / ERROR-REGISTRY

**القرارات المُعتمَدة من الوثيقة:**
- Layer-2 = Integrity/Attestation Overlay (لا blockchain)
- PUF = Physical Identity Evidence (لا "impossible to clone")
- VDF = Sequential Work Evidence (لا absolute time)
- TEE = Hardware Execution Evidence (لا trust root)
- Kalman = AnomalyScore (لا CryptographicTruth)
- hardware_identity.py الحالي = SoftwareFingerprint (لا PUF)
- SIBB = Continuity Substrate، ADIE = Semantic Integrity
- الترتيب: META -> ACL -> Authoring -> Adapter -> TDX -> Temporal -> PUF -> VDF -> GC/SMPC -> ZK -> FHE -> Recursive
- Ontological Anchoring = Binding + Evidence (لا metaphysics)

**الجملة المحورية:** No physical primitive creates truth.

**التثبيت الرسمي:** بعد 183/183 (Phase 1.9 مكتمل)

---

## 15. Phase 1.9 مغلق + Physical Anchor مُثبَّت (NON-NORMATIVE)

**commits:** 5fe41ab (registry) + f0f3bf0 (Physical Anchor)
**suites:** 183/183 (51+12+40+20+40+20)

**Phase 1.9 مُكتمل:**
- spec/REGISTRY-0.1.md (169 سطر)
- protocol/meta/registry.py (342 سطر)
- tests/vomega/meta/registry_run.py (20 vector)
- ERROR-REGISTRY: E-META-23..28

**Physical Anchor:**
- docs/vomega/ADIE-PHYSICAL-ANCHOR-0.1.md (456 سطر، NON-NORMATIVE)
- docs/vomega/decisions/DECISIONS-0.2.md (173 سطر، Binding)
- الجملة المحورية: No physical primitive creates truth.
- hardware_identity.py = SoftwareFingerprint، وليس PUF
- TDX = first production path، PUF/VDF = later profiles

**الترتيب التالي:**
- Phase 1.10: Pilot End-to-End (Python verifier + JS verifier + differential)
- ثم Phase 2: Hybrid Crypto

---

## 16. Phase 1.10 مغلق + Phase 1 كامل

**commit:** add07c2
**suites:** 198/198 (51+12+40+20+40+20+15)

**Phase 1.10 مُكتمل:**
- protocol/pilot/issue_cli.py (122 سطر)
- protocol/pilot/verify_cli.py (158 سطر)
- protocol/pilot/verify.mjs (300 سطر)
- tests/vomega/pilot/run_all.py + 15 vector

**العيب المكتشف:** DEFECT-005 (JS E_SIGNATURE message format)

**Phase 1 كامل:**
- DCP 2.0 + ClaimRoot + Binding
- META-CONTRACT-0.1 + I34 + ERROR-REGISTRY-0.1
- REGISTRY-0.1 + REGISTRY impl + 20 vector
- ACL-0.1 + ast/eval/normalize + 40 vector
- AUTHORING-0.1 + Python/JS compiler + 20 vector
- PILOT + Python/JS verifiers + 15 vector
- 5 defects logged (DEFECTS-LOG.md)
- 2 decision records (DECISIONS-0.1/0.2)

**ما لم يُغطَّ (صريح):**
- ML-DSA-65 / SLH-DSA
- CBOR / COSE wire
- Rust independent verifier
- Fuzzing beyond hand-picked vectors
- TEE / Hardware Evidence
- ZK / FHE / IVC

**التالي:** قرار المرحلة (Phase 2 vs Phase 1.11)

---

## 17. Phase 1.11 (fuzzing) مكتمل جزئياً

**التاريخ:** 2026-10-06

**المُثبَّت (يُلتزم الآن):**
- spec/FUZZ-0.1.md (115 سطر)
- protocol/fuzz/generator.py (136 سطر)
- protocol/fuzz/acl_fuzz.py (38 سطر)
- protocol/fuzz/claimroot_fuzz.py (29 سطر)
- protocol/fuzz/authoring_fuzz.py (70 سطر)
- protocol/fuzz/runner.py (يدعم 3 suites)
- protocol/acl/acl.mjs (210 سطر)
- protocol/core/claim_root.mjs (84 سطر)

**النتائج (seed=42, budget=500):**
- acl: 500/500
- claimroot: 500/500
- authoring: 500/500

**ما لم يُنجَز بعد:**
- Rust verifier (third-language primitive agreement)

**القاعدة الجديدة:**
- كل fuzz vector يعمل بايت-ببايت بين Python و JS
- كل DEFECT جديد من هنا يتضمن: language_pair، failure_mode، invariant_at_risk

**التالي:** Rust H_A + JCS + ClaimRoot + ACL normalize.

---

## 18. Phase 1.11 مكتمل — Rust third-verifier

**التاريخ:** 2026-10-06

**Rust crate:** rust/adie-primitives/
- SHA-256 من الصفر (FIPS 180-4): 3/3
- H_A: 20/20 مقابل Python
- JCS (canonical JSON): من الصفر
- ClaimRoot: 200/200 fuzzed
- ACL eval+normalize: 200/200 fuzzed
- لا external crate عدا serde_json للتحليل

**Python↔JS (1500 حالة):**
- ACL fuzz: 500/500
- ClaimRoot fuzz: 500/500
- Authoring fuzz: 500/500

**المجموع الكلي للـdifferential:** 1920/1920

**Rust بنى بنجاح:**
- cargo 1.75.0 (من apt، لا rustup)
- 3 binaries: adie-h-a, adie-claimroot, adie-acl

**ما لم يُثبَت بعد:**
- Rust DCP 2.0 verify كامل
- Rust Authoring compiler
- Rust RSA signature verify
- 10k+ fuzz cases

**التالي:** القرار (Phase 1.12 vs Phase 2)

---

## 19. قرار المرحلة

**التاريخ:** 2026-10-06
**القرار:** Phase 1.12-lite

**السبب:**
- Phase 1.11 أثبت: H_A + JCS + ClaimRoot + ACL في 3 لغات
- لم يُثبت: أن Rust يستخدمها في DCP 2.0 كاملاً
- RSA verify في Rust = أسبوع أو crate خارجي = كسر المبدأ

**الحل:**
- Rust semantic verifier (كل شيء عدا التوقيع)
- التوقيع في Python/JS فقط
- الفجوة موثقة صراحة في spec/RUST-VERIFIER-0.1.md

**التكلفة:** ~250 سطر Rust، ساعتان
**المكسب:** إغلاق الفجوة الدلالية ثلاثية اللغة قبل ML-DSA

---

## 20. Phase 1.12-lite مكتمل — Rust semantic verifier

**التاريخ:** 2026-10-06

**Rust binaries:**
- adie-h-a: H_A
- adie-claimroot: ClaimRoot
- adie-acl: ACL eval + normalize
- adie-verify: DCP 2.0 semantic verifier

**الـconformance الكامل:**
- RUST-HA: 20/20
- RUST-CR: 200/200
- RUST-ACL: 200/200
- RUST-VERIFY: 15/15 (14 مطابقة + 1 متوقع P13)
- TOTAL: 435/435

**الفجوات الموثقة (spec/RUST-VERIFIER-0.1.md §2):**
- GAP-1: RSA signature verify غير منفذ (SKIPPED)
- GAP-2: strict_load I-JSON غير منفذ
- GAP-3: ACL validate() غير منفذ في Rust verifier
- GAP-4: 200 حالة fuzz بدلاً من 10k

**الرصيد الكلي عبر اللغات الثلاث:**
- Python/JS ACL: 500/500
- Python/JS ClaimRoot: 500/500
- Python/JS Authoring: 500/500
- Python/Rust H_A: 20/20
- Python/Rust ClaimRoot: 200/200
- Python/Rust ACL: 200/200
- Python/Rust DCP verify: 15/15

**التراكمي:** 1935 حالة، كلها مطابقة

---

## 20-correction. تصحيح §20

**التصحيح:**
- الالتزام f8fb6e5 ادّعى 435/435 بينما الفعلي كان 434/435
- DEFECT-006: Rust استخدم أحرف `-` في E-BINDING-* بدل `_`
- الإصلاح: verifier.rs يستخدم E_BINDING_AUDIENCE_MISMATCH الآن
- النتيجة الفعلية بعد الإصلاح: 435/435

**الدرس:** كل رقم في CONTINUITY يجب أن يُنسخ من مخرجات فعلية. الادعاء قبل التحقق يُلوّث الذاكرة.

---

## 21. Phase 2 Block A — HYBRID-CRYPTO-0.1 spec

**التاريخ:** 2026-10-06
**الحالة:** spec-only، لا كود

**الملف:** spec/HYBRID-CRYPTO-0.1.md

**القرارات المُعتمَدة:**
- Option C: primitive from vetted library, protocol owned by ADIE
- TCB صريح: المكتبة جزء من TCB، مُثبَّتة الإصدار، قابلة للاستبدال، موثقة الحالة
- DCP 2.1: signatures (array) بدل signature (singular)
- TBS = "ADIE-SIG-V2\0" || JCS(cert_without_signatures)
- key_id = sha256:hex(SHA-256(SPKI-DER(pubkey)))
- Hybrid default = AND، OR للمهاجرة فقط بقرار manifest صريح
- Downgrade = E_SIGNATURE_DOWNGRADE
- 7 أكواد فشل جديدة (E_SIGNATURE_*)
- 100 متجه اختبار Phase 2 كحد أدنى
- 435/435 يبقى أخضر

**قيود:**
- لا SLH-DSA، لا ML-KEM، لا aggregation، لا ZK للـsignatures
- لا ادعاءات side-channel immunity
- لا ادعاءات library صحيحة بلا تدقيق مستقل

**التالي:** Block B — اختيار المكتبات + pinned versions

---

## 22. Phase 2 Block B — مكتبات مختارة

**التاريخ:** 2026-10-06

**القرار:**
- Rust: ml-dsa 0.1.1 (RustCrypto)
- Python A: pqcrypto 1.0.0 (production)
- Python B: dilithium-py 1.4.0 (cross-check مستقل)
- JavaScript: @noble/post-quantum 0.7.1
- RS256: pycryptodome 3.24.0 (موجود مسبقاً)

**مبدأ مزدوج Python:**
- مكتبتان مستقلتان = KAT agreement بدون ثقة أعمى

**مخاطر مسجلة (RISK-2.1..2.4):**
- ml-dsa pre-1.0، غير مدقق
- pqcrypto wrapper غير مدقق
- @noble pre-1.0، تدقيق غير معلن
- توفر wheel Python 3.12 غير مؤكد

**لا تثبيت حتى §12.1 مُلتزم.**
**التالي:** Block C — تثبيت + KAT اختبار

---

## 23. Phase 2 — بيئة Rust مُثبَّتة

**التاريخ:** 2026-10-06

**الأداة:**
- rustup (official) — من `sh.rustup.rs`
- rustc 1.99.0 (b940084d7 2026-09-28)
- cargo 1.99.0 (5f94df478 2026-08-27)
- default toolchain: stable-x86_64-unknown-linux-gnu
- المسار: /home/biss/.cargo/bin/{cargo,rustc}

**apt Rust (1.75.0) لا يزال موجوداً** في /usr/bin — لم نحذفه (أمان: لو rustup انهار، يبقى احتياطي قديم).

**الـPATH دائم:**
- أُضيف `. "$HOME/.cargo/env"` إلى ~/.bashrc
- التحقق: `bash -c "source ~/.bashrc; cargo --version"` = 1.99.0

**قاعدة جديدة نافذة:**
> كل أمر cargo/rustc في هذه الجلسة يُفترض أن يكون 1.99.0. إذا ظهر 1.75.0، فهذا يعني shell غير مبدوء من .bashrc → صحّح قبل المتابعة.

**GAP-5:** صُحِّح. ml-dsa 0.1.1 يُبنى على rustc 1.99 في 45 ثانية.

**DEFECT-007:** مُسجَّل (التزام قبل استنفاد البدائل).

**الـ435/435 خضراء** تحت rustc 1.99.

**التالي:** C.2.b — إضافة ml-dsa إلى adie-primitives.

---

## 24. Phase 2 C.2.b — ml-dsa مُدمَج في adie-primitives

**التاريخ:** 2026-10-06

**التغيير:**
- rust/adie-primitives/Cargo.toml: + ml-dsa = "=0.1.1"
- Cargo.lock يُثبّت checksum: add6b9d9...4a6f3d

**البناء:**
- rustc 1.99.0 / cargo 1.99.0
- 8 dependencies جديدة
- 1m 18s build time
- 435/435 اختبار لا يزال أخضر

**لم يُبنَ بعد:**
- منطق sign/verify ML-DSA في Rust
- هذا في C.2.c

**تمييز صريح:**
- ml-dsa الآن **مُدمَج** (dependency)
- ml-dsa **ليس مُستخدَماً** بعد (لا sign/verify)

**التالي:** C.3 — JavaScript @noble/post-quantum.

---

## 25. Phase 2 C.3 — JavaScript ML-DSA مُثبَّت

**التاريخ:** 2026-10-06

**التغييرات:**
- js/ directory أنشئت
- js/package.json (type=module, name=adie-js, version=0.1.0)
- @noble/post-quantum 0.7.1 مثبت
- 4 packages: post-quantum + curves + hashes + ciphers (كلها 2.4.0)
- Node 20.20.2 (NodeSource)

**API surface:**
- ml_dsa65: keygen, sign, verify, getPublicKey, prehash, info, lengths, securityLevel

**Import path:**
- `@noble/post-quantum/ml-dsa.js` (لاحقة .js إلزامية بسبب exports map)

**لم يُبنَ بعد:**
- كود ADIE يستخدم المكتبة
- يبدأ في Block D (KAT vectors)

**الجداول الآن:**
- Python: pqcrypto 1.0.0 + dilithium-py 1.4.0 ✅
- Rust: ml-dsa 0.1.1 (dependency فقط، لا استخدام) ⏳
- JS: @noble/post-quantum 0.7.1 ✅ (dependency فقط، لا استخدام)

**التالي:** C.2.c — كتابة Rust sign/verify، ثم Block D.


---

## 26. Phase 2 D.0 — أول تطابق ML-DSA bytes عبر اللغات

**التاريخ:** 2026-10-06

**الاكتشاف:**
- dilithium-py 1.4.0 (Python) + @noble/post-quantum 0.7.1 (JS)
- نفس ξ=0x42*32 → pk/sk/sig بايت-ببايت متطابقة
- pk: 1952 bytes, sk: 4032 bytes, sig: 3309 bytes

**الـtest vector مُثبَّت:**
- spec/test-vectors/MLDSA-XLANG-001.json

**DEFECT-010:**
- pqcrypto لا يستطيع المشاركة (لا seed injection، لا deterministic sign)
- أُعيد تصنيفه: verify-only
- Python sign path = dilithium-py فقط
- Python verify path = pqcrypto + dilithium-py (يجب أن يتفقا)

**لم يُختبر بعد:**
- ml-dsa 0.1.1 (RustCrypto) مقابل هذا الـvector
- verify parity عبر اللغات الثلاث

**التالي:** Block D.1 — Rust mldsa wrapper + cross-check.

---

## 27. Phase 2 D.1 — ML-DSA-65 مُثبَّت ثلاثياً

**التاريخ:** 2026-10-06
**commit:** القادم

**النتيجة:**
- Python (dilithium-py 1.4.0): byte-identical ✅
- JavaScript (@noble/post-quantum 0.7.1): byte-identical ✅
- Rust (RustCrypto ml-dsa 0.1.1): byte-identical ✅

**test vector:** spec/test-vectors/MLDSA-XLANG-001.json

**inputs:**
- seed = 0x42 * 32
- TBS  = "ADIE-SIG-V2\\0" || '{"test":"vector"}'
- ctx  = b""

**outputs:**
- pk  = 1952 bytes, first32 = ecfb1116...ea54
- sig = 3309 bytes, first32 = f02d487b...4a75, last32 = ff0c3b5e...2b33

**Rust binary:** rust/adie-primitives/src/bin/adie-mldsa.rs
**Rust wrapper:** rust/adie-primitives/src/mldsa.rs

**ما لم يُثبَت بعد:**
- NIST ACVP KAT vectors (Block D.2)
- DCP 2.1 integration (Block D.3)
- Hybrid RS256 + ML-DSA (Block D.4)

**RISK-2.1 يبقى نشطاً:** ml-dsa 0.1.1 غير مُدقَّق (self-declared). Cargo wrapper معزول، قابل للاستبدال.

**التالي:** Block D.2 — NIST ACVP KAT vectors.

---

## 28. Phase 2 D.2b — KAT: Python 55/55 + Rust 40/40

**التاريخ:** 2026-10-06

**ACVP vectors المُستخرجة:**
- keygen_65.json: 25 (كلها pure)
- siggen_65.json: 15 (deterministic + pure + ctx متنوع)
- sigver_65.json: 15 (pure + ctx متنوع)
- المُستبعَد: 90 siggen (HashML-DSA) + 15 siggen (randomized) + 45 sigver (HashML-DSA)

**Python (dilithium-py 1.4.0):**
- keygen: 25/25
- siggen: 15/15
- sigver: 15/15
- TOTAL: 55/55

**Rust (RustCrypto ml-dsa 0.1.1):**
- keygen: 25/25
- sigver: 15/15
- siggen: not covered (GAP-8، بسبب API seed-only)
- TOTAL: 40/40 (cross-python مطابق في كل ما غُطّي)

**DEFECT-012:** Rust decode كان يُرجع Err بدل Ok(false) لتوقيعات malformed. صُحِّح.

**GAP-8:** Rust لا يغطي sigGen بسبب API. موثق مع paths tried.

**التالي:** Block D.2c — JS KAT (sigGen + sigVer).

---

## 29. Phase 2 D.2c — JS KAT 55/55 (mldsa ثلاثي مُغطّى)

**التاريخ:** 2026-10-06

**JS (@noble/post-quantum 0.7.1):**
- keygen: 25/25
- siggen: 15/15
- sigver: 15/15
- TOTAL: 55/55

**الحصيلة الكلية على NIST ACVP ML-DSA-65 (pure):**
- Python (dilithium-py 1.4.0): 55/55
- JavaScript (@noble 0.7.1):    55/55
- Rust (RustCrypto 0.1.1):      40/40 (keygen+sigver؛ sigGen = GAP-8)
- **Total: 150/150**

**الـrunner:**
- js/run_acvp_kat.mjs (موضوع داخل js/ لـmodule resolution)
- tests/vomega/mldsa/kat/run_python.py
- tests/vomega/mldsa/kat/run_rust.py

**الـvectors:**
- tests/vomega/mldsa/kat/{keygen,siggen,sigver}_65.json
- مُستخرجة من NIST ACVP-Server عبر jsDelivr CDN

**GAP-8 بقي:** Rust sigGen غير مغطّى عبر API. القرار: مقبول، موثّق.

**التالي:** Block D.3 — hybrid combiner (RS256 + ML-DSA-65).

---

## 30. Phase 2 D.3c — Hybrid signer (Python) 16/16

**التاريخ:** 2026-10-07

**الـsigner:**
- protocol/hybrid/sign.py (93 سطر)
- tests/vomega/hybrid/test_sign.py (16 test، كلها pass)

**قاعدتان تشغيليتان نافذتان:**

1. كل runner Python يستخدم `.venv/bin/python`، ليس `python3` (Phase 2 deps فقط في .venv).
2. ML-DSA-65 signature يستهلك `sk` (4032B) الخام، ليس seed.

**GAP-9:** ML-DSA-65 key_id يستخدم raw pk bytes، وليس SPKI DER. موثق.

**الحالة:**
- TBS: py 12/12، js 11/11، diff 5/5
- Sign: py 16/16
- Verify: smoke test ✅ (5/5)

---

## 31. Phase 2 مُغلق رسمياً

**التاريخ:** 2026-10-07

**الحصيلة النهائية:**
- Phase 2 suites: 70/70 (59 Python + 11 JS) (TBS 12+11+5، Sign 16، Verify 20، E2E 11)
- NIST ACVP ML-DSA-65: 150/150 (Python 55، JS 55، Rust 40 مع GAP-8)
- MLDSA-XLANG-001: ثلاث لغات مطابقة بايت-ببايت
- Phase 1 regression: 648/648 لا يزال أخضر
- **المجموع: 758 حالة فريدة عبر 4 دلو (633+59+11+55)**

**DEFECTs مغلقة في Phase 2:** 010, 011, 012, 013
**GAPs مفتوحة:** 8 (Rust sigGen)، 9 (raw pk key_id)
**RISKs نشطة:** 2.1، 2.2، 2.3

**الوثائق:**
- PHASE-2-CLOSURE.md
- spec/HYBRID-CRYPTO-0.1.md
- spec/test-vectors/MLDSA-XLANG-001.json

**التالي:** قرار Phase 3 (3A-3E مرشحة، الأرجح 3A = CBOR/COSE).


---

## 32. تصحيح عدّ الاختبارات (DEFECT-014)

**التاريخ:** 2026-10-07

**الادعاء الخاطئ السابق:** 723/723 مجموع، 75 Phase-2.
**الحقيقة بعد إنشاء tests/account.py:**
- 633 regression (Phase 1)
- 59 Phase 2 Python
- 11 Phase 2 JS
- 55 ACVP unique (150 executions)
- **المجموع الفريد: 758**

**السبب الجذري:** الأرقام كانت تُحسب يدوياً/ذاكرياً. `648` كان خطأ جمع، `75` كان خلطاً بين Python و JS.

**الحل:**
- `tests/account.py` مصدر السلطة الوحيد للأرقام
- كل ادعاء خارجي ينسخ الأرقام من stdout الأداة
- لا رقم في commit message قبل رؤيته في المخرجات

**القاعدة (نافذة):** لا أرقام مُتذكَّرة. لا أرقام مُجمَّعة. لا أرقام مُقدَّرة.
فقط أرقام من أداة آلية.


---

## 33. تصحيح العدّ + DEFECT-014 + DECISIONS-0.3 + Gate 0 spec

**التاريخ:** 2026-10-07
**آخر commit:** cf1f017

### الأرقام الحقيقية (من tests/account.py)

| الدلو | العدد |
|---|---|
| REGRESSION_TOTAL (Phase 1) | 633 |
| PHASE2_ADIE_PYTHON | 59 |
| PHASE2_ADIE_JAVASCRIPT | 11 |
| ACVP_UNIQUE_VECTORS | 55 |
| ACVP_VECTOR_EXECUTIONS | 150 |
| **المجموع الفريد** | **758** |

**الادعاءات المصححة:**
- "648 Phase 1" → الفعلي 633
- "723/723 total" → غير صحيح
- "75 Phase 2" → الفعلي 70 (59 Python + 11 JS)

### DEFECT-014

**الفئة:** process
**السبب:** الأرقام كانت تُحسب ذاكرياً أو يدوياً قبل إنشاء الأداة.
**الأثر:** ادعاءات في commit messages (fd5d98d, 6f1152b) وPHASE-2-CLOSURE.md.
**الحل:** tests/account.py مصدر السلطة الوحيد.

### DECISIONS-0.3 (8 قرارات)

1. **Three-bucket accounting** — لا جمع أرقام من دلاء متقاطعة
2. **Forbidden phrases** — "NIST Certified", "Zero errors", "Production-grade PQC" ممنوعة
3. **Approved claim forms** — صيغ محددة لكل نوع ادعاء
4. **DEFECT/GAP discipline** — حقول إلزامية
5. **RFC 9964 adoption** — ML-DSA في COSE = IANA identifiers، لا اختراع
6. **CBOR philosophy** — لا CBOR من الصفر، ADIE Deterministic CBOR Profile فوق RFC 8949
7. **Phase 3 gate order** — 3E → 3A → 3B → 3C → 3D
8. **Commit message numbers** — لا رقم قبل نسخه من stdout لأداة

### RUST-FULL-VERIFIER-0.1 (Gate 0 spec)

- 143 سطر، معياري
- Rust يتحقق من DCP 2.1 كاملاً (كان GAP-6 في Phase 1)
- RISK-3.1: rsa crate MSRV/audit
- RISK-3.2: RSA padding strictness
- GAP-8 يبقى مفتوحاً (Rust sigGen)
- Exit: 11 E2E vectors + 20 negative vectors byte-identical Python≡Rust

### قواعد تشغيلية جديدة نافذة

**1. لا heredoc مع triple backticks في markdown.**
السبب: bash يفشل صامتاً. الحل: Python `Path().write_text()`.
يُسجَّل هذا كامتداد لـDEFECT-009.

**2. لا رقم في commit message قبل نسخه من stdout.**
السبب: DEFECT-014.
الحل: `tests/account.py` هو المصدر.

**3. كل runner Python يستخدم `.venv/bin/python`.**
السبب: Phase 2 deps فقط في .venv (PEP 668).

### الحالة الحالية

- branch: vOmega
- last commit: cf1f017
- suites: 633 + 59 + 11 + 55 = 758 (كلها خضراء)
- DEFECTs: 14 (كلها مُغلقة/موثقة)
- GAPs: 8، 9 (مفتوحة، موثقة)
- RISKs: 2.1، 2.2، 2.3 (نشطة)
- Phase 3: Gate 0 جاهز للبدء

### التالي

**3E Block 1:** فحص `rsa` crate API (نفس منهج `ml-dsa` في Phase 2):
- cargo search rsa
- cargo tree rsa --depth 1
- MSRV من Cargo.toml
- Audit status من README

**لا كود قبل الفحص.**


---

## 34. قاعدة الفحص الإجرائية (Gate 0)

**التاريخ:** 2026-10-07

**القاعدة النافذة:**
> أي sandbox لفحص مكتبة خارجية **يجب** أن يُنفّذ `cargo build --release`
> قبل أن يُعلن أن المكتبة "قابلة للاستخدام". `cargo fetch` أو `cargo tree`
> أو `cargo info` **لا تكفي**.

**الأسباب المُثبتة:**
- DEFECT-015: `sad-rsa 0.10.2` نجح في `cargo fetch`، فشل في `cargo build`.
- DEFECT-016: `rsa 0.9.6` نجح مع default features في `/tmp/`, لكنه احتاج
  feature `sha2` صراحةً في `adie-primitives`.

**ما يجري في كل sandbox مستقبلي:**
1. `cargo add` أو كتابة Cargo.toml
2. `cargo fetch` — تحميل
3. **`cargo build --release`** — إثبات البناء
4. `cargo tree --depth 1` — شجرة التبعيات
5. تسجيل checksums
6. **فقط بعد 1-5:** القرار

**هذا امتداد لـDEFECT-007/008/009/014:** كل ادعاء يجب أن يُختبر، لا يُفترض.
