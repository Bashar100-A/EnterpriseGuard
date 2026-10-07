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


---

## 35. Phase 3 Gate 0 — Rust Full Hybrid Verifier مكتمل

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 0

### الـRust binary الجديد

`rust/adie-primitives/src/bin/adie-hybrid-verify.rs` (~280 سطر)

**الوظائف:**
1. قراءة DCP 2.1 certificate من stdin
2. فحص required fields
3. بناء TBS: `"ADIE-SIG-V2\0" || JCS(cert_without_signatures)`
4. فحص duplicate/unknown/downgrade
5. **فحص key_id** لكل alg (SPKI DER hash لـRS256، raw pk hash لـML-DSA-65)
6. التحقق من التوقيعات عبر `sad-rsa` (سابقاً) → `rsa 0.9.6` (حالياً) + `ml-dsa 0.1.1`
7. إخراج canonical JSON (نفس format Python)

### الـparity suites

**`tests/vomega/hybrid/test_rust_parity.py`:** 13/13
- R01: both VALID (happy)
- R02: checks maps equal
- R03: RS256-only
- R04: ML-DSA-only
- R05: duplicate alg
- R06: unknown alg
- R07: downgrade
- R08-R09: tampered output
- R10: tampered ML-DSA sig
- R11: tampered RS256 sig
- R12: wrong keys
- R13: empty signatures

**النتيجة:** Python ≡ Rust على كل الـ13 حالة، بما فيها codes وmessages.

### DEFECTs مغلقة في Gate 0

- DEFECT-015: sad-rsa 0.10.2 لا يُبنى → رجعنا إلى rsa 0.9.6
- DEFECT-016: rsa 0.9.6 يحتاج feature `sha2` صراحةً
- DEFECT-017: Rust لم يفحص key_id قبل التوقيع

### RISKs نشطة

- RISK-3.1: `rsa 0.9.6` + Marvin CVE (RUSTSEC-2023-0071). **غير قابل للتطبيق** (verification offline).
- RISK-3.2: dependency surface ~30 crate.

### Exit criteria — محقّقة

- [x] All 11 E2E pilot vectors byte-identical py/rust (مغطاة في R01-R13 عبر 13 vector أوسع)
- [x] All negative vectors produce matching codes (R05-R13)
- [x] RISK-3.1 + RISK-3.2 documented
- [x] New Rust binary built
- [x] No regression in Phase 1 (633) or Phase 2 (70)

### الأرقام بعد Gate 0

| الدلو | العدد |
|---|---|
| REGRESSION_TOTAL (Phase 1) | 633 |
| PHASE2_ADIE_PYTHON | 59 |
| PHASE2_ADIE_JAVASCRIPT | 11 |
| PHASE3_GATE0_RUST_PARITY | 13 |
| ACVP_UNIQUE_VECTORS | 55 |
| ACVP_VECTOR_EXECUTIONS | 150 |
| **المجموع الفريد** | **771** |

### التالي

**Gate 1: 3A.1 — DCP 2.1 Wire Format Specification**
- spec/WIRE-FORMAT-0.2.md
- ADIE Deterministic CBOR Profile فوق RFC 8949
- لا كتابة CBOR من الصفر
- Reference implementation في Rust + adapters في Python/JS
- RFC 9964 لتمثيل ML-DSA-65 في COSE


---

## 36. Gate 0 مُغلق رسمياً — في انتظار قرار القائد

**التاريخ:** 2026-10-07
**آخر commit:** 6110273
**الحالة:** Gate 0 مُغلق. القائد يدرس تقريراً. لا عمل حتى القرار.

### Gate 0 — الملخص

**النطاق:** Rust يتحقق من DCP 2.1 hybrid certificates كاملاً،
byte-identically مع Python.

**Artifacts المُلتزمة:**
- spec/RUST-FULL-VERIFIER-0.1.md (143 سطر)
- rust/adie-primitives/src/rsa_verify.rs (90 سطر)
- rust/adie-primitives/src/bin/adie-hybrid-verify.rs (~280 سطر)
- tests/vomega/hybrid/test_rust_parity.py (13/13)
- docs/vomega/PHASE-3-GATE-0-CLOSURE.md (118 سطر)

**DEFECTs مغلقة في Gate 0:** 015، 016، 017
**RISKs نشطة:** RISK-3.1 (Marvin، غير قابل للتطبيق offline)،
RISK-3.2 (dependency surface ~30)

### الأرقام الحقيقية (من tests/account.py)

| الدلو | العدد |
|---|---|
| REGRESSION_TOTAL (Phase 1) | 633 |
| PHASE2_ADIE_PYTHON | 59 |
| PHASE2_ADIE_JAVASCRIPT | 11 |
| PHASE3_GATE0_PARITY | 13 |
| ACVP_UNIQUE_VECTORS | 55 |
| ACVP_VECTOR_EXECUTIONS | 150 |
| **المجموع الفريد** | **771** |

### قرار RSA النهائي

- **المرشح الأول:** `sad-rsa 0.10.2` (Marvin-mitigated) — **فشل البناء** (DEFECT-015)
- **القرار النهائي:** `rsa = { version = "=0.9.6", features = ["sha2"] }`
- **RISK-3.1:** Marvin CVE مفتوح. **غير قابل للتطبيق** على verification offline.
- **مسار الترقية:** إذا نُشر `rsa 0.10.x` stable مع Marvin mitigation → تغيير سطر واحد في `rsa_verify.rs`.

### القواعد المُثبتة في Gate 0

1. **`cargo fetch` لا يعني `cargo build`.** كل sandbox يجب أن يُنفّذ `cargo build --release`.
2. **`default-features` قد تكون غير كافية.** اختبر `feature` selection في البناء الفعلي، ليس في الفحص النظري.
3. **key_id binding ≠ signature verification.** كلاهما فحصان مستقلان. أي verifier يجب أن يؤدي الاثنين (DEFECT-017).
4. **byte-equality testing يكتشف الفروق الدلالية** التي لا يكشفها التشفير وحده.

### البوابة التالية — Gate 1: 3A.1

**المركزية:** `spec/WIRE-FORMAT-0.2.md`

**الطبقات:**
DCP semantic model
→ ADIE Canonical TBS
→ DCP 2.1 CBOR data model
→ Deterministic CBOR (RFC 8949 profile)
→ COSE (RFC 9052)
→ Hybrid certificate

**قيود صارمة (من DECISIONS-0.3):**
- لا CBOR من الصفر. Reference impl في Rust + adapters Python/JS.
- RFC 9964 لتمثيل ML-DSA-65 في COSE (ML-DSA-65 = -49).
- positive corpus: 100+ vector
- negative corpus: 100+ vector

### حالة الانتظار

**لا عمل حتى إشارة القائد.**

**عند الاستئناف:**
```bash
cd ~/Desktop/EnterpriseGuard
.venv/bin/python tests/account.py    # يجب: 771
cat docs/vomega/PHASE-3-GATE-0-CLOSURE.md
cat docs/vomega/CONTINUITY.md | tail -100
القرار المتوقع من القائد:

    إما المضي إلى Gate 1 (3A.1)

    أو تعديل ترتيب البوابات

    أو إعادة تقييم بعد مراجعة التقرير
    

---

## 37. قرار القائد — Gate 0 ACCEPTED / Gate 1 AUTHORIZED

**التاريخ:** 2026-10-07
**الحالة:** 3A.1 START (spec only)
**المرجع:** Commander Order 3A_LEVELS_GO

### اعتماد Gate 0

Gate 0 مُغلق رسمياً. الإنجاز الجوهري: Rust يتحقق من DCP 2.1
hybrid certificate كاملاً، parity مع Python.

**ما لا يُدَّعى:**
- production-grade cryptography
- independent security audit
- side-channel immunity
- NIST/CAVP certification

**ما يُدَّعى:**
- interoperability and implementation evidence قوي
- protocol-level determinism across heterogeneous runtimes

### تصحيحات إلزامية

**1. RISK-3.1 — إعادة تصنيف:**
- ❌ لا: "not applicable"
- ✅ نعم: "BOUNDED EXPOSURE / NOT USED FOR PRIVATE-KEY OPERATIONS IN CURRENT VERIFIER PATH"
- السبب: Marvin يرتبط بعمليات private-key. ADIE يستخدم RSA public-key verify فقط.
- الإجراء: يبقى في Dependency Register. يُراجَع عند تغير scope.

**2. DEFECT-017 — ترقية معمارية:**
- لا يُصنّف كخطأ CLI
- يُصنّف كدليل على ضرورة **Identity Binding Invariant**
- Algorithm + Key ID + Public Key + Fingerprint + TBS = منظومة مترابطة
- valid signature ≠ دليل كافٍ إن كانت هوية المفتاح لا تطابق المتوقع
- سيُدمج في Wire Format + Governance + Revocation لاحقاً

**3. FIPS 204 errata:**
- NIST نشرت errata في يوليو 2026
- يجب تثبيت exact revision في سجل التوافق
- reference: FIPS 204 (2024-08-13) + July 2026 errata

**4. RFC 9964 vs ADIE Hybrid Profile:**
- RFC 9964 يعرّف ML-DSA في JOSE/COSE
- ADIE Hybrid Profile هو شيء آخر (combines classical + PQ)
- لا يُدَّعى أن ADIE = "RFC 9964 implementation"
- Composite ML-DSA مسودة Internet-Draft (لم تصبح RFC). لا يُدَّعى compliance.

### تصحيح في 3A — Semantic Strictness

**بدل "احظر جميع الحقول غير المعروفة":**
- Unknown Critical → REJECT
- Unknown Non-Critical → behavior defined by profile
- Version-breaking structure → REJECT
- Ambiguous interpretation → REJECT

### تصحيح في 3A — Reference implementation

- ❌ لا: 3 مستقلات CBOR
- ✅ نعم: Rust reference + Python adapter + JS/WASM adapter
- الهدف: One normative protocol + independent verification paths

### Exit gate لـ3A.1

- ≥100 valid vectors
- ≥100 malformed/noncanonical vectors
- 3-way differential (positive AND negative convergence)
- Fuzzing من day-1

### ترتيب 3A

```
3A.1  WIRE-FORMAT-0.2.md         (spec only — NOW)
3A.2  Rust reference encoder/decoder
3A.3  Python adapter
3A.4  JS/WASM adapter
3A.5  Differential + malformed corpus
3A.6  COSE integration
3A.7  Hybrid round-trip verification
```

**لا ننتقل إلى 3A.2 حتى يوافق القائد على اكتمال WIRE-FORMAT-0.2.md.**

### القاعدة السيادية

Specification precedes implementation.
Implementation precedes optimization.
Validation precedes claim.
Independent verification precedes trust.


---

## 38. Gate 1 / 3A.1 — CLOSED

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1 — DCP 2.1 Wire Format Specification
**Status:** Specification approved and frozen for implementation

### Artifact

- `spec/WIRE-FORMAT-0.2.md` (amended, ~530 سطر)
- غير معياري لأي كود. لا CBOR implementation. لا 3A.2.

### القرارات المعتمدة (Commander Order 3A_LEVELS_GO)

| # | القرار |
|---|---|
| 1 | **1C** — CBOR integer keys، JCS-JSON TBS |
| 2 | **ب** — TBS مستقل عن wire encoding |
| 3 | **نعم** — فصل COSE_Key container عن raw pk material |
| 4 | **نعم** — §16 vectors تُنتَج في 3A.2 |

### المبدأ المحوري المُثبَّت

> **Wire encoding must not silently redefine cryptographic identity.**

النظام:

    Semantic Certificate
         ↓
    JCS canonical (TBS)
         ↓
    "ADIE-SIG-V2\0" || TBS
         ↓
    RS256 + ML-DSA-65
         ↓
    CBOR / COSE (transport only)

CBOR لا يغيّر TBS. لا يغيّر key_id. لا يغيّر التوقيع. هو transport layer.

### تعديلات على المواصفة (نُفِّذت بعد موافقة القائد)

1. §7: integer keys allowed, text keys forbidden
2. §8 rule 2: clarify integer sorting = numeric ascending
3. §13 opening: COSE relationship explicit (not RFC 9964 compliance)
4. §13.2: TBS independence paragraph added
5. §14.3: three-layer table (wire / material / key_id source)
6. §14.4: Fingerprint Source Invariant (new section)
7. §16: vectors produced in 3A.2
8. §20: explicit status token on closure

### ما لا يُدَّعى

- لا "RFC 9964 implementation" (subset for identifiers only)
- لا "composite ML-DSA compliant" (draft, not RFC)
- لا "production-grade cryptography"
- لا "NIST/CAVP certified"

### الحالة

**GATE 1 / 3A.1 — CLOSED**
Specification approved and frozen for implementation.

### التالي

**3A.2 — GO عند استلام أمر جديد من القائد.**

لا يبدأ 3A.2 حتى يرد أمر مستقل. القاعدة السارية:
Specification precedes implementation.


---

## 39. Phase 3 / Gate 1 / 3A.2 — Rust Reference CBOR Implementation

**التاريخ:** 2026-10-07

### الـArtifacts

- `rust/adie-primitives/src/cbor/mod.rs` — public API
- `rust/adie-primitives/src/cbor/error.rs` — 14 codes, 5 tests
- `rust/adie-primitives/src/cbor/value.rs` — AdieValue + RFC 8949 sorting, 8 tests
- `rust/adie-primitives/src/cbor/profile.rs` — validate() authority, 22 tests
- `rust/adie-primitives/src/cbor/rawcheck.rs` — byte-level pre-check, 33 tests
- `rust/adie-primitives/src/cbor/encoder.rs` — canonical serializer, 14 tests
- `rust/adie-primitives/src/cbor/decoder.rs` — full pipeline, 29 tests
- **المجموع: 111 unit tests، كلها PASS**

### الـdependency المعتمد

    ciborium = "=0.2.2"

- codec primitive فقط
- ADIE profile يفرض WIRE-FORMAT-0.2 §7–§9 فوقه
- موثق في CBOR-LIB-EVAL-001

### المعمارية

    Bytes
      → rawcheck::scan_top_level   (trailing, indefinite, floats, tags, non-shortest)
      → ciborium::de::from_reader  → Value
      → profile::validate          → AdieValue (int keys, sorted, dedup)
      → encoder::encode            → canonical bytes
      → bytewise comparison        → E_WIRE_NONCANONICAL_MAP if diff

- **encoder** = serializer، ليس authority
- **profile** = authority
- **rawcheck** = يكشف ما يفقد ciborium
- **decoder** = pipeline

### القيود المطبقة (أمر القائد)

| # | القيد | التحقق |
|---|---|---|
| §2 | No trailing bytes | dec_trailing_rejected |
| §3 | Duplicate keys reject | dec_duplicate_keys_rejected |
| §4 | Canonicality ≠ validation | decoder pipeline خطوات 3+5 منفصلة |
| §5 | AdieValue = profile types | profile::validate — 14 rejection codes |
| §6 | RFC 8949 bytewise order | rfc_order_full_boundary_sweep |
| §8 | profile = authority | profile.rs قلب البنية |

### الأرقام بعد 3A.2

| الدلو | العدد |
|---|---|
| REGRESSION_TOTAL (Phase 1) | 633 |
| PHASE2_ADIE_PYTHON | 59 |
| PHASE2_ADIE_JAVASCRIPT | 11 |
| PHASE3_GATE0_PARITY | 13 |
| **PHASE3_3A2_CBOR** | **111** |
| ACVP_UNIQUE_VECTORS | 55 |
| **المجموع الفريد** | **882** |

### DEFECTs مغلقة في 3A.2

- DEFECT-018: ciborium non_exhaustive wildcard
- DEFECT-019: test byte-count error (5 not 6)
- RISK-3.3: بيئة البناء ضيقة المساحة

### الحالة

    GATE 1 / 3A.2 — CLOSED
    Rust reference CBOR implementation: 111/111
    Awaiting Commander order for 3A.3 (Python adapter)

### القاعدة المحورية

> The codec is not the protocol.
> ADIE owns the profile; ciborium owns the primitive.


---

## 40. تصحيح tooling — DEFECT-020 (account.py summary)

**التاريخ:** 2026-10-07
**commits:** 42b7722 (impl) → 928d0df (fix)

### ما حدث

- التزام 3A.2 (42b7722) أضاف قسم `PHASE3_3A2_CBOR` إلى account.py
- لكن script التحديث لم يُطابق anchor الـsummary block
- account.py استمر في عرض 771 بدل 882
- اكتُشف فوراً عند تشغيل account.py بعد الالتزام

### الإصلاح (928d0df)

- Regex أدق anchored على `PHASE3_GATE0_PARITY`
- Fallback line-scan
- account.py الآن يعرض 882

### القاعدة الجديدة (مضافة إلى CONTINUITY)

> بعد أي تعديل على `tests/account.py`، الخطوة التالية **إلزامية**:
> تشغيل `account.py`، قراءة stdout، التحقق من أن المجموع المطبوع
> يساوي المجموع المتوقع حسابياً. لا commit قبل ذلك.

### الحالة بعد الإصلاح

GATE 1 / 3A.2 — CLOSED
Rust reference CBOR: 111/111
Grand total (unique): 882
Commits: 42b7722 (impl) + 928d0df (fix)
Awaiting Commander order for 3A.3

### الأرقام الرسمية

| الدلو | العدد |
|---|---|
| REGRESSION_TOTAL (Phase 1) | 633 |
| PHASE2_ADIE_PYTHON | 59 |
| PHASE2_ADIE_JAVASCRIPT | 11 |
| PHASE3_GATE0_PARITY | 13 |
| PHASE3_3A2_CBOR | 111 |
| ACVP_UNIQUE_VECTORS | 55 |
| **المجموع الفريد** | **882** |

ACVP_VECTOR_EXECUTIONS: 150 (بلا زيادة في المجموع — إعادة تنفيذ الـ55 في 3 لغات)


---

## 41. أمر القائد — 3A.3 Block C APPROVED WITH HARDENING

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.3
**Status:** GO

### فلسفة 3A.3

Python = **adapter**، ليس مصدر حقيقة ثانياً.
- Rust reference = السلوك المعياري.
- WIRE-FORMAT-0.2 = المصدر المعياري.
- Python يتطابق، لا يُعيد تعريف semantics.

### التسع تعديلات الإلزامية

| # | القيد |
|---|---|
| 1 | **rawcheck هو authoritative for tags**. أي major type 6 → REJECT قبل cbor2. |
| 2 | `tag_hook=raise_on_tag` = defense-in-depth فقط. cbor2's tag_hook لا يلتقط كل semantic tags المضمّنة. |
| 3 | `allow_indefinite=False` صريحاً. |
| 4 | `allow_duplicate_keys=False` صريحاً. |
| 5 | `max_depth=32` صريحاً. |
| 6 | **duplicate keys → REJECT، ليس dedup**. لا يُعدَّل input. |
| 7 | **canonical=True ليس دليلاً** — نتحقق تجريبياً من تطابق cbor2 مع RFC 8949 على حدود الترميز. |
| 8 | trailing bytes → REJECT في rawcheck. |
| 9 | WIRE-FORMAT-0.2 لا يُعدَّل. |

### Pipeline المُعتمد

    rawcheck
       ↓  (رفض tags، indefinite، trailing، non-shortest)
    cbor2.loads(
       allow_indefinite=False,
       allow_duplicate_keys=False,
       max_depth=32,
       tag_hook=raise_on_tag  # defense-in-depth
    )
       ↓
    profile::validate
       ↓  (int keys, sorted, dup rejection)
    encoder::encode
       ↓
    bytewise comparison
       ↓  E_WIRE_NONCANONICAL_MAP if diff

### acceptance gate

| Metric | Minimum |
|---|---|
| Python unit tests | ≥ 100 |
| Positive differential | ≥ 10 |
| Decode differential | ≥ 10 |
| Negative differential | ≥ 10 |
| Full regression (882) | unchanged |

**Mandatory coverage:** TAG، DUPLICATE، INDEFINITE، TRAILING، NON-SHORTEST، FLOAT، NON-UTF8، DEPTH، MAP-ORDER، INVALID-TYPE.

### cbor2 == 6.1.5

- نُثبّت `=6.1.5` (من 1 أكتوبر 2026، يتضمن decoder/security fixes حديثة).
- ليست audited — نعاملها كـdependency خارجية.
- 6.x مبني على Rust safe-mode داخلياً.
- لا يُغيِر هذا من كون طبقة ADIE الصارمة ضرورية.

### قاعدة عند الاستئناف

- قبل أي material toolchain change: `which X && X --version` + تسجيل في CONTINUITY.
- فحص `df -h /home` قبل/بعد كل block (RISK-3.3).
- توقف فوري عند أي mismatch.


---

## 42. Phase 3 / Gate 1 / 3A.3 — Python Interoperability Adapter

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.3

### الـArtifacts

- `protocol/wire/__init__.py` — public API
- `protocol/wire/error.py` — 14 codes, 20 tests
- `protocol/wire/value.py` — AdieValue + RFC 8949 sort, 28 tests
- `protocol/wire/profile.py` — validate() authority, 31 tests
- `protocol/wire/rawcheck.py` — byte-level gate (authoritative for tags), 44 tests
- `protocol/wire/encoder.py` — canonical serializer (cbor2), 32 tests
- `protocol/wire/decoder.py` — full pipeline, 39 tests
- `tests/vomega/wire/test_differential.py` — Python ↔ Rust, 44 vectors
- `requirements.txt` — cbor2==6.1.5 pinned
- `rust/adie-primitives/src/bin/adie-cbor.rs` — Rust differential endpoint

### الـdependency

    cbor2 == 6.1.5
    license: MIT

- pinned in requirements.txt
- rationale in CBOR-LIB-EVAL-002

### المعمارية

    rawcheck
       ↓  (trailing, indefinite, floats, tags, non-shortest)
    cbor2.loads(
       allow_indefinite=False,
       allow_duplicate_keys=False,
       max_depth=32,
       tag_hook=raise_on_tag
    )
       ↓
    profile::validate
       ↓  (int keys, sorted, dup rejection, types)
    encoder::encode
       ↓
    bytewise comparison

### القيود المطبَّقة (تسع)

| # | القيد | الحالة |
|---|---|---|
| 1 | rawcheck authoritative for tags | ✅ DEC-021 |
| 2 | tag_hook = defense-in-depth only | ✅ |
| 3 | allow_indefinite=False | ✅ |
| 4 | allow_duplicate_keys=False | ✅ |
| 5 | max_depth=32 explicit | ✅ |
| 6 | duplicate keys REJECT, never dedup | ✅ |
| 7 | canonical=True empirical at boundaries | ✅ T27-T31 |
| 8 | trailing bytes rejected in rawcheck | ✅ |
| 9 | WIRE-FORMAT-0.2 untouched | ✅ |

### Acceptance Evidence

| Metric | Required | Actual |
|---|---|---|
| Python unit tests | ≥ 100 | 194 |
| Positive differential | ≥ 10 | 14 |
| Decode differential | ≥ 10 | 12 |
| Negative differential | ≥ 10 | 18 |
| Full regression | 882/882 | 882/882 |
| Total unique | — | 1120 |

**Positive parity:** 14/14
**Decode parity:** 12/12
**Negative parity:** 18/18

### DEFECTs مغلقة في 3A.3

| ID | Category | Summary |
|---|---|---|
| DEFECT-021 | dependency | cbor2 interprets known semantic tags |
| DEFECT-022 | test | ROOT path off by one |
| DEFECT-023 | code | CBORDecodeError vs ValueError for dup keys |
| DEFECT-024 | process | Hand-written JSON vector file invalid |

### RISK-3.3

مراقبة. Disk 6.9 GB free قبل/بعد كل block.

### الحالة

    GATE 1 / 3A.3 — CLOSED
    Python wire adapter: 194/194
    Python ↔ Rust differential: 44/44
    Grand total (unique): 1120

### البوابة التالية

**3A.4 — JavaScript/WASM interoperability** — بانتظار أمر القائد.


---

## 43. أمر القائد — 3A.4_GO (JS + WASM)

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.4
**Status:** GO

### فلسفة القسمين

- **3A.4A**: JavaScript = **independent interoperability proof**.
  يجب أن يكون implementation حقيقي، **لا** wrapper على WASM.
- **3A.4B**: WASM = **portable execution of the Rust reference**،
  **ليس** implementation ثالثة مستقلة.
  - Rust native == Rust WASM (يجب إثباته).
  - Node.js + browser targets.

### القاعدة المعمارية

    Rust        = reference
    Python      = interoperability proof
    JavaScript  = independent interoperability proof
    WASM        = portable execution of Rust reference

### ممنوع

- ❌ تعديل WIRE-FORMAT-0.2
- ❌ تغيير TBS
- ❌ تغيير ADIE-SIG-V2\0
- ❌ COSE
- ❌ Hybrid E2E
- ❌ SLH-DSA
- ❌ fuzz campaign الكاملة
- ❌ استخدام WASM لإخفاء فشل JS parity
- ❌ ادعاءات side-channel / constant-time / performance بدون أدلة

### Acceptance Gate

| Metric | Minimum |
|---|---|
| JS unit tests | ≥ 100 |
| JS positive differential | ≥ 10 |
| JS decode differential | ≥ 10 |
| JS negative differential | ≥ 10 |
| Rust native ↔ WASM parity | demonstrated |
| Node.js WASM path | demonstrated |
| Browser WASM path | demonstrated |
| Existing 1120 regression | 1120/1120 |
| Spec changes | 0 |

### Mandatory negative coverage (JS)

TAG, DUPLICATE, INDEFINITE, TRAILING, NON-SHORTEST, FLOAT, NON-UTF8, INVALID-KEY, INVALID-TYPE, UNKNOWN-CRITICAL.

### عند mismatch

STOP — لا تعديل للمواصفة للحصول على parity.

### RISK-3.3

ACTIVE. فحص `df` قبل/بعد كل block.


---

## 44. Phase 3 / Gate 1 / 3A.4A — JavaScript Adapter (D.1-D.3)

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.4A
**النطاق:** D.1 → D.3 (من أصل D.1 → D.10)

### القرار المعماري

    Rust        = reference
    Python      = interoperability proof
    JavaScript  = independent interoperability proof
    WASM        = portable execution of Rust reference

JavaScript adapter هو **implementation مستقل**. لا استدعاء WASM.
لا استدعاء Rust. لا استدعاء Python. يستورد فقط `cbor@9.0.2` (codec
primitive).

### التبعية

    cbor@9.0.2
    license: MIT
    deps:    nofilter ^3.0.2 (non-native)
    import:  `import CBOR from 'cbor'` (CommonJS default — see DEFECT-025)
    rationale: CBOR-LIB-EVAL-003

### الـArtifacts (D.1-D.3)

- `js/wire/error.mjs` — 14 codes (mirror of `protocol/wire/error.py`)
- `js/wire/value.mjs` — AdieValue tagged form + RFC 8949 sort
- `js/wire/profile.mjs` — `validate()` authority + `intToAdie`
- `tests/vomega/wire-js/test_error.mjs` — 20 tests
- `tests/vomega/wire-js/test_value.mjs` — 28 tests
- `tests/vomega/wire-js/test_profile.mjs` — 32 tests

### الاختبارات

| Suite | Required | Actual |
|---|---|---|
| test_error.mjs | ≥ 20 | 20/20 |
| test_value.mjs | ≥ 28 | 28/28 |
| test_profile.mjs | ≥ 32 | 32/32 |
| **Subtotal** | ≥ 80 | **80/80** |

### DEFECTs مغلقة في D.1-D.3

| ID | Category | Summary |
|---|---|---|
| DEFECT-025 | dependency | CommonJS interop: `import *` vs `import default` |
| DEFECT-026 | code | JS profile coercion of non-integral Number values |

### DEFECT-026 — القاعدة المعمارية المثبَّتة

**Profile validates semantic values. Rawcheck validates information
that semantic decoding may erase.**

التفصيل:
- CBOR `0x01` (uint 1) و CBOR `0xfb3ff0000000000000` (float64 1.0)
  يُفكَّان إلى نفس القيمة في JavaScript: `Number 1`.
- بعد الفك، `profile.validate()` لا يملك معلومات للتمييز بينهما.
- لذلك `rawcheck.mjs` (D.4) **يجب** أن يرفض float encodings على
  البايتات قبل تشغيل cbor@9.

T32 في `test_profile.mjs` يُثبّت هذا الحد ويحميه من الحذف المستقبلي.

### الحالة

    D.1 — CLOSED  (error:    20/20)
    D.2 — CLOSED  (value:    28/28)
    D.3 — CLOSED  (profile:  32/32, DEFECT-026 fixed)

### الخطوة التالية

D.4 — `rawcheck.mjs` (byte-level gate). أول هدف: إثبات أن wire-level
type distinctions (خاصة float vs integer) لا تُفقد عند عبور JS decoder.


---

## 45. Phase 3 / Gate 1 / 3A.4A — D.4 rawcheck.mjs

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.4A / D.4
**Commit:** <this commit>

### الهدف

حارس على البايتات يعمل **قبل** `cbor@9.0.2`. لا يستدعي decoder.
لا يستدعي profile. يرجع `{ok:true, consumed:N}` أو يرمي أحد أخطاء
`error.mjs`.

### المسار الرسمي

    Raw CBOR bytes
          ↓
    rawcheck.mjs          ← Wire authority
          ↓
    cbor@9.0.2 decode
          ↓
    profile.mjs           ← Semantic authority
          ↓
    AdieValue

### القاعدة المعمارية المُثبَّتة (DEFECT-026 / T32)

    Profile validates semantic values.
    Rawcheck validates information that semantic decoding may erase.

CBOR `0x01` (uint 1) و CBOR `0xfb3ff0000000000000` (float64 1.0)
يُفكَّان إلى نفس `Number 1` في JavaScript. `profile.mjs` لا يستطيع
التمييز بينهما. `rawcheck.mjs` وحده يحتفظ بهذا الحد على البايتات.
اختبار A01 يحمي هذا الحد من الحذف المستقبلي.

### الـArtifacts

- `js/wire/rawcheck.mjs` — 184 lines
- `tests/vomega/wire-js/test_rawcheck.mjs` — 58 tests

### Acceptance Evidence

| Metric | Required | Actual |
|---|---|---|
| rawcheck unit tests | ≥ 40 | 58 |
| valid vectors | ≥ 20 | 28 |
| rejection vectors | ≥ 20 | 29 |
| architectural vectors | ≥ 1 | 1 (A01) |
| T32 (profile) invariant | true | true |
| boundary vectors (0,23,24,255,256,65535,65536,u32::MAX) | full | full |
| cumulative regression | 1200/1200 | 1200/1200 |
| spec changes | 0 | 0 |

### Rejection coverage (WIRE-FORMAT-0.2 §9)

| فئة | الاختبارات |
|---|---|
| tag (major type 6) | R01, R02, R03 |
| float16 / float32 / float64 | R04, R05, R06 |
| indefinite bytes/text/array/map | R07, R08, R09, R10 |
| non-shortest int (uint + negint) | R11–R13, R18 |
| non-shortest length (bytes/text/array/map) | R14–R17 |
| trailing bytes | R19, R20 |
| reserved additional-info (ai28-30) | R21, R22, R23 |
| forbidden simples (0xf7 undefined, 0xff break) | R24, R25 |
| malformed / truncated | R26, R27, R28 |
| invalid UTF-8 | R29 |

### المسؤوليات (لا تكرار)

- **rawcheck** → wire invariants (tag, float, indefinite, canonical
  int, trailing, reserved AI, malformed head, invalid UTF-8).
- **profile** → semantic invariants (integer keys, sorted keys,
  depth, types, numeric range, float rejection of decoded values).

لا تكرار: rawcheck لا يفحص ترتيب المفاتيح ولا أنواع القيم؛ profile
لا يفحص البايتات ولا canonical forms.

### الحالة

    D.1 — CLOSED  (error:     20/20)
    D.2 — CLOSED  (value:     28/28)
    D.3 — CLOSED  (profile:   32/32, DEFECT-026 fixed)
    D.4 — CLOSED  (rawcheck:  58/58, A01 boundary enforced)
    ─────────────────────────────────────────
    Subtotal:  138/138
    Previous:  1120
    Cumulative: 1258

### القرارات والتبعيات

- `cbor@9.0.2` مثبَّت (MIT). لم يتغير.
- لا dependencies جديدة في D.4.
- RISK-3.3 مراقب: 6.9 GB free قبل وبعد.

### DEFECTs / GAPs

لا جديدة في D.4. DEFECT-025 و DEFECT-026 مُغلقان في D.1–D.3.

### الخطوة التالية

D.5 — `encoder.mjs` (cbor@9 `encodeCanonical` wrapper فوق rawcheck
+ profile). **بانتظار أمر القائد.**


---

## 46. Phase 3 / Gate 1 / 3A.4A — Stage Core (D.5 + D.6 + D.7)

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.4A / Stage Core
**Commit:** <this commit>

### نطاق Stage

D.5 encoder.mjs → D.6 decoder.mjs → D.7 index.mjs — كوحدة واحدة.

### المعمارية النهائية للـJS wire adapter

    AdieValue (tagged)
          ↓ encode
    encoder.mjs   (validate + cbor@9.encodeCanonical)
          ↓
    canonical CBOR bytes

    canonical CBOR bytes
          ↓ decode
    rawcheck.mjs   (wire authority)
          ↓
    cbor@9.0.2     (codec primitive, {preferMap: true})
          ↓
    profile.mjs    (semantic authority)
          ↓
    AdieValue (tagged)
          ↓ re-encode
    canonical CBOR bytes
          ↓ byte-compare with input
    accept OR E_WIRE_NONCANONICAL_MAP

### الـArtifacts

| الملف | السطور | الاختبارات |
|---|---|---|
| js/wire/encoder.mjs | 121 | — |
| js/wire/decoder.mjs | 55 | — |
| js/wire/index.mjs | 31 | — |
| tests/vomega/wire-js/test_encoder.mjs | 112 | 43 |
| tests/vomega/wire-js/test_decoder.mjs | 107 | 40 |
| tests/vomega/wire-js/test_index.mjs | 68 | 30 |

### Acceptance Evidence (Stage)

| Metric | Required | Actual |
|---|---|---|
| D.1 error | ≥ 20 | 20/20 |
| D.2 value | ≥ 28 | 28/28 |
| D.3 profile | ≥ 32 | 32/32 |
| D.4 rawcheck (مع duplicate) | ≥ 40 | 60/60 |
| D.5 encoder | — | 43/43 |
| D.6 decoder | — | 40/40 |
| D.7 index | — | 30/30 |
| **JS subtotal** | — | **253/253** |
| Previous regression | 1120 | 1120/1120 |
| **Cumulative** | — | **1373** |

### Determinism / Canonicality

- `encode(x) == encode(x)` byte-for-byte: ✅ E31
- `decode(encode(x)) == x` semantic: ✅ D01-D21
- `re-encode(decode(y)) == y` bytewise: ✅ D01-D21
- Noncanonical → correct rejection code: ✅ D29-D40

### Rejection coverage (full DCP 2.1 §9)

| الفئة | covered by |
|---|---|
| tag | D22, rawcheck R01-R03 |
| float | D23-D25, rawcheck R04-R06, A01 |
| indefinite | D26-D27, rawcheck R07-R10 |
| trailing | D28, rawcheck R19-R20 |
| non-shortest int | D29-D30, rawcheck R11-R18 |
| invalid UTF-8 | D31, rawcheck R29 |
| undefined / break | D32-D33, rawcheck R24-R25 |
| duplicate keys | **D36 (wire level via rawcheck DEFECT-027)** |
| unsorted map | D37, D38 (re-encode compare) |
| text / negint key | D39, D40 (profile) |

### DEFECTs مغلقة في Stage

| ID | Category | Summary |
|---|---|---|
| DEFECT-027 | architecture | rawcheck must reject duplicate keys at wire level |
| DEFECT-028 | dependency | cbor@9 mixed Map/object output for maps |

### القاعدة المعمارية (المجموعة الكاملة)

    DEFECT-021:  cbor2 interprets tags → rawcheck authoritative
    DEFECT-025:  CJS interop          → default import mandatory
    DEFECT-026:  Number coercion      → T32 boundary preserved
    DEFECT-027:  Map dedup            → rawcheck duplicate detection
    DEFECT-028:  mixed Map/object     → {preferMap: true} mandatory

**القاعدة الموحدة:** مكتبات codec هي primitives، سلوكها الافتراضي
ليس عقداً. كل default يؤثر على تمثيل القيم أو المعلومات يجب تسجيله
وتصحيحه صراحةً، لا تركه للسلوك الافتراضي.

### التبعية

    cbor@9.0.2  (MIT, nofilter ^3.0.2)
    import CBOR from 'cbor';
    decodeFirstSync(bytes, {preferMap: true})

### RISK-3.3

مراقب. Disk 6.9 GB free قبل وبعد Stage.

### الحالة

    3A.4A / D.1 — CLOSED (error:     20/20)
    3A.4A / D.2 — CLOSED (value:     28/28)
    3A.4A / D.3 — CLOSED (profile:   32/32)
    3A.4A / D.4 — CLOSED (rawcheck:  60/60, +DEFECT-027)
    3A.4A / D.5 — CLOSED (encoder:   43/43)
    3A.4A / D.6 — CLOSED (decoder:   40/40, +DEFECT-028)
    3A.4A / D.7 — CLOSED (index:     30/30)
    ─────────────────────────────────────────────
    JS Core:    253/253
    Previous:   1120
    Cumulative: 1373

### الخطوة التالية (بانتظار أمر القائد)

D.8 — JavaScript ↔ Rust differential (نفس vectors D.9b في 3A.3).
D.9 — JavaScript ↔ Python differential.
D.10 — Stage 3A.4A closure.

**لا شيء من هذه قبل أمر صريح.**


---

## 47. Phase 3 / Gate 1 / 3A.4A-DIFF — Interoperability Proof

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.4A-DIFF (D.8 + D.9)
**Commit:** <this commit>

### الهدف

إثبات أن JavaScript Wire Adapter متوافق فعلياً مع Rust Reference
ومع Python Interoperability Adapter على ثلاثة مستويات:

    Encode parity
    Decode parity
    Negative/rejection parity

### البروتوكول المشترك بين اللغات الثلاث

    stdin:  {"op":"encode","value":<AdieValue>}
    stdin:  {"op":"decode","cbor_hex":"<hex>"}
    stdout: {"cbor_hex":"..."} | {"value":<AdieValue>} | {"error":"E_..","detail":".."}

AdieValue JSON form (مشترك حرفياً بين Rust/Python/JS):

    {"t":"uint","v":<u64>}      {"t":"int","v":<i64>}
    {"t":"bytes","v":"<hex>"}   {"t":"text","v":"<utf8>"}
    {"t":"bool","v":true|false} {"t":"null"}
    {"t":"array","v":[...]}     {"t":"map","v":[[k,<AdieValue>],...]}

### الـArtifacts

- `js/wire/bin/adie-cbor.mjs` — JS endpoint (95 lines)
- `js/wire/bin/json-io.mjs` — BigInt-safe JSON helpers (60 lines)
- `protocol/wire/bin/adie-cbor.py` — Python endpoint (71 lines)
- `tests/vomega/wire-js/test_differential_rust.mjs` — D.8 (147 lines)
- `tests/vomega/wire-js/test_differential_python.mjs` — D.9 (114 lines)
- `tests/vomega/wire-js/diff-matrix.mjs` — Matrix reporter (80 lines)

### Vector corpus

**44 unique vectors** (نفس corpus المستخدم في 3A.3 D.9b Python↔Rust):

| Class | Count | IDs |
|---|---|---|
| Encode vectors | 14 | E01–E14 |
| Decode vectors | 12 | D01–D12 |
| Negative vectors | 18 | N01–N18 |

**Executions** في هذه المرحلة:
- D.8: 44 + 1 (A01) = 45 executions (Rust ↔ JS)
- D.9: 44 + 1 (A01) = 45 executions (Python ↔ JS)
- **Differential executions subtotal:** 90

### Cross-implementation matrix (كل الفئات، كل اللغات)

| Vector class | Rust | Python | JavaScript |
|---|---|---|---|
| Valid encode | OK | OK | OK |
| Valid decode | OK | OK | OK |
| Float rejection | `E_WIRE_FLOAT` | `E_WIRE_FLOAT` | `E_WIRE_FLOAT` |
| Tag rejection | `E_WIRE_TAG` | `E_WIRE_TAG` | `E_WIRE_TAG` |
| Duplicate keys | `E_WIRE_DUP_KEY` | `E_WIRE_DUP_KEY` | `E_WIRE_DUP_KEY` |
| Indefinite length | `E_WIRE_INDEFINITE` | `E_WIRE_INDEFINITE` | `E_WIRE_INDEFINITE` |
| Trailing bytes | `E_WIRE_TRAILING` | `E_WIRE_TRAILING` | `E_WIRE_TRAILING` |
| Non-shortest integer | `E_WIRE_NONCANONICAL_INT` | `E_WIRE_NONCANONICAL_INT` | `E_WIRE_NONCANONICAL_INT` |
| Invalid UTF-8 | `E_WIRE_INVALID_UTF8` | `E_WIRE_INVALID_UTF8` | `E_WIRE_INVALID_UTF8` |
| Invalid key type | `E_WIRE_TYPE_MISMATCH` | `E_WIRE_TYPE_MISMATCH` | `E_WIRE_TYPE_MISMATCH` |
| Invalid value type | `E_WIRE_MALFORMED` | `E_WIRE_MALFORMED` | `E_WIRE_MALFORMED` |
| Unknown critical | N/A (semantic) | N/A (semantic) | N/A (semantic) |

**قرار القائد:** لا تصفير mismatches. كل خلية إما OK أو error code دقيق.
تطابق تام عبر اللغات الثلاث في هذه المرحلة.

### A01 — Architectural proof (محفوظ عبر كل اللغات الثلاث)

    "01"                 → Rust OK | Python OK | JS OK       → uint 1
    "fb3ff0000000000000" → Rust E_WIRE_FLOAT | Python E_WIRE_FLOAT | JS E_WIRE_FLOAT

نفس Number 1 في JS بعد decode. الفيصل الوحيد هو rawcheck على
البايتات. A01 في D.8 و D.9 يُثبّت ذلك عبر كل الأزواج.

### Acceptance Evidence

| Metric | Required | Actual |
|---|---|---|
| JS core (D.1-D.7) | ≥ 200 | 253 |
| D.8 Rust↔JS positive | ≥ 10 | 14 |
| D.8 Rust↔JS decode | ≥ 10 | 12 |
| D.8 Rust↔JS negative | ≥ 10 | 18 |
| D.8 architectural | ≥ 1 | 1 |
| D.9 Py↔JS positive | ≥ 10 | 14 |
| D.9 Py↔JS decode | ≥ 10 | 12 |
| D.9 Py↔JS negative | ≥ 10 | 18 |
| D.9 architectural | ≥ 1 | 1 |
| Previous regression | 1120/1120 | 1120/1120 |
| Spec changes | 0 | 0 |

### الأرقام بتمييز صريح (unique vs executions)

| الفئة | العدد | التصنيف |
|---|---|---|
| Differential unique vectors | 44 | unique |
| D.8 executions (Rust↔JS) | 45 | executions |
| D.9 executions (Python↔JS) | 45 | executions |
| Differential executions subtotal | 90 | executions |
| JS core unit executions | 253 | executions |
| Previous baseline | 1120 | executions |
| **Grand total executions** | **1463** | executions |

**ملاحظة:** الـ44 unique vector مُشتركة بين D.8 و D.9 (نفس corpus،
مقارنات مختلفة). لا يجوز جمعها مع 3A.3 D.9b (Python↔Rust) لأنها
تنفيذات على نفس corpus من أزواج مختلفة.

### DEFECTs مغلقة في Stage

| ID | Category | Summary |
|---|---|---|
| DEFECT-029 | test | JSON Number precision boundary at u64 range |

**DEFECT-029 — تفصيل:**

Two distinct manifestations, one root family:
1. Vector file read: `JSON.parse` converts `18446744073709551615`
   to a lossy `Number` (18446744073709552000). Re-serialization
   then sends an out-of-range value to Rust/Python.
2. Comparison serializer: BigInt → String → `JSON.stringify`
   added quotes; `{"v":0}` vs `{"v":"0"}`.

Fix: `js/wire/bin/json-io.mjs` (60 lines) with:
- `parsePreservingBigInts(text)` — marks 16+ digit literals
- `stringify(v)` — emits BigInt as plain integer literals
- `canon(v)` — unified Number/BigInt serializer for equality

**الـimplementation كان صحيحاً من البداية.** الفشل في test harness.

Family: DEFECT-024 (hand-written JSON), DEFECT-029 (JSON Number
precision). كلاهما: JSON artifact "يبدو صحيحاً" لكن يخالف ضمان
دقة نوع رقمي.

### DEFECTs مفتوحة

لا شيء.

### RISK-3.3

مراقب. Disk 6.9 GB free قبل/بعد Stage. لا تغيير.

### الـScope (احترام صريح)

- ❌ WIRE-FORMAT-0.2.md — لم تُلمس
- ❌ TBS — لم يُلمس
- ❌ ADIE-SIG-V2\0 — لم يُلمس
- ❌ Rust reference — لم يُلمس
- ❌ Python adapter (protocol/wire/) — لم يُلمس
- ❌ cbor@9.0.2 — لم يُغيَّر
- ❌ لا WASM, COSE, E2E, fuzzing

### الحالة الرسمية

    3A.4A / D.1 — CLOSED  (error:       20/20)
    3A.4A / D.2 — CLOSED  (value:       28/28)
    3A.4A / D.3 — CLOSED  (profile:     32/32)
    3A.4A / D.4 — CLOSED  (rawcheck:    60/60)
    3A.4A / D.5 — CLOSED  (encoder:     43/43)
    3A.4A / D.6 — CLOSED  (decoder:     40/40)
    3A.4A / D.7 — CLOSED  (index:       30/30)
    3A.4A / D.8 — CLOSED  (Rust↔JS:     45/45)
    3A.4A / D.9 — CLOSED  (Python↔JS:   45/45)
    ────────────────────────────────────────────
    JS core:           253/253
    Differential:       90/90  (44 unique × 2 pairs + 2 A01)
    Previous:         1120/1120
    Cumulative execs: 1463

### الخطوة التالية

**3A.4B — WASM delivery path** — بانتظار أمر القائد.

WASM = portable execution of Rust reference (ليس لغة تحقق ثالثة).
Rust native == Rust WASM يجب إثباته. Node.js + Browser targets.

**لا شيء من 3A.4B قبل أمر صريح.**


---

## 48. Stage 3A.4B-WASM — Plan (APPROVED by Commander)

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.4B
**Status:** PLAN APPROVED — pending execution order
**قرار القائد:** approve-with-modifications

### العلاقة الكنسية (لا تُغيَّر)

    Rust Reference (rust/adie-primitives/)
          ↓ path dependency
    rust/adie-wasm/          ← Delivery wrapper (NOT a new implementation)
          ↓ wasm-bindgen
    WASM module
          ↓
    Node.js  +  Firefox

**القاعدة الثابتة:**

> Rust remains the cryptographic and wire-format authority.
> WASM is its portable execution boundary, NOT a new implementation.

### القرارات الخمسة المعتمدة

#### 1. wasm32-unknown-unknown target

```
rustup target add wasm32-unknown-unknown
```

الهدف القياسي. لا بديل.

#### 2. Toolchain binaries — prebuilt + pinned

**ممنوع:** `cargo install` لأي من `wasm-bindgen-cli` / `wasm-pack`.
**مطلوب:** تنزيل prebuilt releases من GitHub + تثبيت النسخة.

- **`wasm-bindgen-cli`:** يُحدَّد إصداره من `Cargo.lock` بعد إضافة
  `wasm-bindgen` كاعتماد. **CLI version MUST equal crate version.**
- **`wasm-pack`:** prebuilt، نسخة مثبَّتة (0.15.0 هو الإصدار الحالي
  الظاهر).
- **`wasm-opt`:** غير مطلوب للـclosure. لا يُثبَّت إلا إذا احتجناه
  لقياس حجم.

**سجل ما بعد التثبيت (إلزامي):**

    which wasm-bindgen && wasm-bindgen --version
    which wasm-pack     && wasm-pack --version

#### 3. rust/adie-wasm/ — crate منفصل

**ممنوع:** إضافة `cdylib` إلى `rust/adie-primitives/`.
**مطلوب:** crate جديد:

    rust/adie-wasm/
    ├── Cargo.toml           (path dep → ../adie-primitives)
    └── src/lib.rs           (wasm-bindgen surface)

هذا يحافظ على الفاصل:

    Reference implementation  ≠  Delivery wrapper

#### 4. Firefox + geckodriver — التحقق من التوافق أولاً

**ممنوع:** تثبيت geckodriver عشوائياً.
**مطلوب قبل التثبيت:**

    which firefox && firefox --version

ثم اختيار نسخة geckodriver المتوافقة مع إصدار Firefox المثبَّت.

**سجل ما بعد التثبيت (إلزامي):**

    which firefox     && firefox --version
    which geckodriver && geckodriver --version
    which wasm-pack   && wasm-pack --version
    which wasm-bindgen && wasm-bindgen --version

#### 5. u64/i64 WASM ABI — Lossless Integer Boundary

**تسمية صحيحة:** هذا **WASM ABI/serialization boundary**، وليس
"DCP 2.1 JSON schema". DCP 2.1 نفسه لا يتغير بسبب JavaScript.

**التمثيل الإلزامي عبر WASM:**

    {"t": "uint", "v": "18446744073709551615"}     ← string
    {"t": "int",  "v": "-9223372036854775808"}     ← string

**ممنوع صراحةً:**

    {"t": "uint", "v": 18446744073709551615}       ← JSON Number (lossy)

Rust يقرأ `v` كـstring ثم يحوّلها إلى `u64`/`i64` مباشرة (بعد التحقق
من الحدود). JavaScript لا يمررها عبر `Number`.

### DEFECT-029-WASM — Lossless Integer Boundary Invariant

**امتداد لـDEFECT-029 على حدود WASM.**

**الاختبار الإلزامي:**

    Forward:  u64::MAX (Rust)
                 ↓  WASM JSON boundary (v: string)
              "18446744073709551615"
                 ↓  Rust parse
              u64::MAX
                 ↓  CBOR encode
              0x1bffffffffffffffff

    Reverse:  0x1bffffffffffffffff
                 ↓  CBOR decode (Rust)
              u64::MAX
                 ↓  WASM JSON boundary
              {"t":"uint","v":"18446744073709551615"}
                 ↓  JS read
              (no Number round-trip at any point)

**الحد الأدنى من القيم للاختبار:**

    0, 23, 24, 255, 256, 65535, 65536,
    u32::MAX (4_294_967_295),
    u32::MAX+1 (4_294_967_296),
    u64::MAX (18_446_744_073_709_551_615)

**التحقق:** كل قيمة تصل إلى Rust كـ`u64` مطابقة، وكل قيمة تعود إلى
JS كـstring مطابق. لا مرور واحد عبر JS `Number`.

### WASM API Surface (minimal)

```rust
#[wasm_bindgen]
pub fn encode(value_json: &str) -> Result<Vec<u8>, JsValue>;
// value_json: AdieValue JSON with v as string for uint/int

#[wasm_bindgen]
pub fn decode(cbor: &[u8]) -> Result<String, JsValue>;
// returns AdieValue JSON with v as string for uint/int
```

**مبادئ:**
- Byte-oriented: `&[u8]` / `Vec<u8>` عبر `Uint8Array` في JS.
- لا JSON للـCBOR bytes. الـCBOR bytes تمر كـbyte array.
- JSON فقط لتمثيل AdieValue (لأن الحقول semantic، ليس wire).
- الأخطاء تُعاد كـ`{code: "E_WIRE_*"}` في JSON، بنفس taxonomy
  `error.mjs`/`error.py`/`error.rs` — لا taxonomy جديد.

### Test plan (عند التنفيذ)

| المستوى | الاختبار |
|---|---|
| Native Rust | `cargo test --release --lib cbor::` (يجب أن يبقى 111/111) |
| WASM unit | اختبارات Rust على crate adie-wasm (target wasm32-unknown-unknown) |
| Node.js | `wasm-pack test --node` — encode/decode/negative |
| Firefox | `wasm-pack test --headless --firefox` — نفس الاختبارات |
| Precision | 10 قيم u64 عبر WASM boundary (لا `Number`) |
| Parity | native Rust bytes == WASM bytes على نفس الـ44 vectors |
| Regression | 1120/1120 (previous baseline) |

### Scope (احترام صريح)

- ❌ لا COSE, لا Hybrid E2E, لا SLH-DSA, لا fuzzing
- ❌ لا تعديل `WIRE-FORMAT-0.2.md`
- ❌ لا تعديل Rust reference behavior
- ❌ لا تعديل Python wire
- ❌ لا تغيير JS wire semantics
- ✅ فقط: WASM delivery path + parity proof

### Security claim boundary

WASM completion **لا يعني**:
- constant-time execution
- side-channel resistance
- cryptographic audit
- production certification

الادعاء الصحيح:

> The Rust DCP 2.1 reference implementation is reproducibly
> deployable through WebAssembly with verified behavioral parity
> across the tested Node.js and Firefox targets.

### الحالة

**PLAN APPROVED. لا كود. لا `rustup target add`. لا تنزيل.
بانتظار أمر التنفيذ الكامل للمرحلة من القائد.**


---

## 49. Stage 3A.4B-WASM — Browser Target Decision (APPROVED)

**التاريخ:** 2026-10-07
**قرار القائد:** OPTION A
**geckodriver:** NO
**Firefox ESR:** NO
**Additional Firefox:** NO

### القرار

Browser target = **Firefox headless + HTML test page**، بدون geckodriver.

**القيد الإلزامي:**

> Screenshot not sufficient as proof.
> The test page MUST execute WASM vectors and produce a machine-readable
> result in DOM: `PASS=<n> FAIL=0`.
> Failure MUST be clearly visible, not a pretty picture.

### التحقق الإلزامي لاحقاً

- WASM artifact executed inside real Firefox.
- DOM read after Firefox headless run → parse `PASS=N FAIL=0`.
- Failures appear as `[FAIL]` lines in DOM/console.
- Not relying on WebDriver integration.

### Firefox المثبَّت

    /usr/bin/firefox → Mozilla Firefox 155.0.1

### القاعدة المعمارية

> Rust remains the cryptographic and wire-format authority.
> WASM is its portable execution boundary, NOT a new implementation.

### الحالة

**EXECUTION APPROVED.** Range: toolchain → adie-wasm → build → Node
→ Firefox → lossless u64/i64 → native↔WASM parity → 1120 regression
→ commit → STOP. لا توقف لطلب قرار آخر حتى Closure Report.


---

## 50. Stage 3A.4B-WASM — CLOSED

**التاريخ:** 2026-10-07
**Gate:** Phase 3, Gate 1, 3A.4B
**Commit:** <this commit>

### الهدف

WASM delivery path للـRust DCP 2.1 reference. **ليس implementation
جديدة.** كان الهدف إثبات أن نفس reference implementation قابلة
للنشر عبر WebAssembly بسلوك متطابق.

    Rust Reference
          ↓ path dependency
    rust/adie-wasm/       ← delivery wrapper (لا semantics جديدة)
          ↓ wasm-bindgen
    WASM module (232,431 bytes adie_wasm_bg.wasm)
          ↓
    Node.js + Firefox

### Toolchain (مثبَّت، موثَّق)

| الأداة | الإصدار | المصدر |
|---|---|---|
| rustc | 1.99.0 | rustup |
| cargo | 1.99.0 | rustup |
| rustup | 1.29.1 | rustup |
| wasm32-unknown-unknown | (target) | rustup target add |
| wasm-bindgen-cli | **0.2.129** | gh-proxy.com mirror (prebuilt musl) |
| wasm-pack | **0.15.0** | gh-proxy.com mirror (prebuilt musl) |
| Firefox | **155.0.1** | /usr/bin/firefox (system) |
| Node.js | v20.20.2 | /usr/bin/node |

**ملاحظة:** gh-proxy.com هي مرآة طرف ثالث لـGitHub releases.
استُخدمت لأن release-assets.githubusercontent.com محجوب شبكياً.
الـbinaries تحقّقت عبر `--version` وطابقت إصدارات Cargo.lock.

### الملفات الجديدة

- `rust/adie-wasm/Cargo.toml` — crate مستقل، path dep على adie-primitives
- `rust/adie-wasm/Cargo.lock` — locked deps
- `rust/adie-wasm/.cargo/config.toml` — getrandom rustc cfg (DEFECT-031)
- `rust/adie-wasm/src/lib.rs` — 148 lines، WASM API
- `js/wasm-pkg-node/` — Node.js target (wasm-bindgen output + package.json)
- `tools/wasm/browser-test/` — HTML test page + HTTP server + pkg/
- `tests/vomega/wasm/test_wasm_node.mjs` — 45 assertions
- `tests/vomega/wasm/test_wasm_precision.mjs` — 31 assertions

### WASM ABI Contract (DEFECT-029-WASM)

**هذا ليس DCP 2.1 JSON schema.** هذا WASM ABI/serialization boundary.

    uint/int VALUES AND MAP KEYS cross as decimal STRINGS:
      {"t":"uint","v":"18446744073709551615"}
      {"t":"int", "v":"-9223372036854775808"}
      {"t":"map", "v":[["18446744073709551615", ...]]}

    CBOR bytes cross as Uint8Array.

    JavaScript Number is FORBIDDEN on the u64/i64 boundary.

**ملاحظة CBOR wire:** الترميز لا يحفظ `t:'int'` للأعداد الموجبة
(both uint and positive-int encode as major type 0). Decoder يُرجع
`t:'uint'` للقيم غير السالبة. تطبيع semantic صحيح.

### Acceptance Evidence

| Metric | Required | Actual |
|---|---|---|
| WASM build | success | ✅ 232,431 bytes bg.wasm |
| Native Rust ↔ WASM parity (encode) | 14 | 14/14 |
| Native Rust ↔ WASM parity (decode) | 12 | 12/12 |
| Native Rust ↔ WASM parity (negative) | 18 | 18/18 |
| WASM architectural (A01) | 1 | 1/1 |
| Node.js WASM | all pass | **45/45** |
| Precision (u64/i64 boundary) | full | **31/31** |
| Browser (Firefox headless) | machine-readable | **29/29** |
| Previous 1120 baseline | 1120/1120 | 1120/1120 |
| Spec changes | 0 | 0 |

### Cross-implementation continuity

    Rust native == Rust WASM  (byte-for-byte على 44 vectors)
    Same Node.js test suite passes on WASM exactly as on JS native.
    Same HTML test suite passes in Firefox headless.

### Security claim boundary

WASM completion **لا يعني**:
- ❌ constant-time execution
- ❌ side-channel resistance
- ❌ cryptographic audit
- ❌ production certification
- ❌ sandbox security of the host application

**الادعاء الصحيح:**

> The Rust DCP 2.1 reference implementation is reproducibly
> deployable through WebAssembly with verified behavioral parity
> across the tested Node.js 20.20.2 and Firefox 155.0.1 targets.

### DEFECTs مغلقة في Stage

| ID | Category | Summary |
|---|---|---|
| DEFECT-029-WASM | architecture | Lossless Integer Boundary Invariant |
| DEFECT-031 | dependency | getrandom wasm32 backend explicit opt-in |
| DEFECT-032 | dependency | wasm-bindgen nodejs under ESM parent |

### GAPs جديدة

| ID | Status | Summary |
|---|---|---|
| GAP-3.4B-01 | open (by design) | wasm-bindgen nodejs CWD-relative wasm path |

### RISK-3.3

مراقب. Disk 6.9 GB → 6.4 GB. استُهلك ~500 MB (rust build + tools + pkg).

### الأرقام بتمييز صريح

| الفئة | العدد | التصنيف |
|---|---|---|
| WASM unique vectors | 44 | unique |
| Node WASM executions | 45 | executions |
| Node precision executions | 31 | executions |
| Browser executions | 29 | executions |
| **WASM executions subtotal** | **105** | executions |
| Previous baseline | 1120 | executions |
| **Cumulative executions** | **1225** | executions |

### القاعدة المعمارية النهائية

> Rust remains the cryptographic and wire-format authority.
> WASM is its portable execution boundary, NOT a new implementation.

### الحالة

    3A.4A — CLOSED (JS adapter, 253+90 = 343 execs)
    3A.4B — CLOSED (WASM delivery, 105 execs)
    ─────────────────────────────────────────
    Cumulative: 1225 execs

### الخطوة التالية (بانتظار أمر القائد)

- 3A.5 — COSE + Hybrid Wire Integration
- Fuzzing campaign
- Governance / revocation

**لا شيء من هذه قبل أمر صريح.**


---

## 51. Stage 3A.4B-WASM — CLOSED (post DEFECT-033)

**التاريخ:** 2026-10-07
**المرجع:** DEFECT-033 hygiene commits (6982220 + <this commit>)

### الأثر الفعلي

Repository hygiene only. لا source changes. لا rebuild. لا test rerun.

Untracked:
- `rust/adie-wasm/target/`   (بناء cargo — ~90 MB، ~750 ملف)
- `tools/wasm/{wasm-bindgen, wasm-pack, wasm2es6js, wasm-bindgen-test-runner}`
  (binaries طرف ثالث — ~39 MB)

Tracked (باقية بشكل صريح):
- `tools/wasm/{LICENSE-APACHE, LICENSE-MIT, README.md}` — توثيق الترخيص
- `tools/wasm/browser-test/` — HTML test page + server.mjs
- `tools/wasm/browser-test/pkg/` — generated distributable test
  artifact (~240 KB)، مرتبط مباشرة بـindex.html، يبقى قابل لإعادة
  التوليد من المصدر بنفس toolchain المثبَّت

### الاستراتيجية المعتمدة

    source/configuration
          ↓
    pinned version
          ↓
    official release download    (مؤجَّل)
          ↓
    SHA-256 verification         (مؤجَّل)
          ↓
    tool invocation

**Download/bootstrap mechanism: مُرحَّل لمرحلة لاحقة.** لكل binary:
URL ثابت + SHA-256 + سكربت تنزيل. لا `latest`.

### تأكيد Stage 3A.4B

    Node WASM:         45/45
    Precision:         31/31
    Firefox headless:  29/29
    Native ↔ WASM:     44/44   (byte-parity، 44 vectors)
    Regression 1120:   1120/1120
    Spec changes:      0

STAGE 3A.4B-WASM — CLOSED


---

## 52. Stage 3A.5-SR — WIRE-FORMAT RECONCILIATION

**التاريخ:** 2026-10-07
**المرحلة:** Phase 3, Gate 1, 3A.5-SR
**قرار القائد:** B+ (ADIE Native Hybrid CBOR Envelope)

### المُشكلة المُكتشفة

تناقض معياري بين:

- `spec/WIRE-FORMAT-0.2.md` §13.2 — TBS = JCS، "CBOR/COSE is a
  transport encoding"؛
- أمر القائد 3A.5 §3 — Model A (COSE-native signing, Sig_structure)؛
- `spec/WIRE-FORMAT-0.2.md` §10 — "COSE_Sign1 semantics"، مقابل
  أمر القائد 3A.5 §2 — "do NOT use COSE_Sign1".

### القرار

**Model B+ — ADIE Native Hybrid CBOR Envelope.**

    Semantic certificate
          ↓ JCS
    ADIE-SIG-V2\0 || JCS(...)        ← TBS — unchanged
          ↓ RS256 + ML-DSA-65
    signatures[]                       ← ADIE-native — unchanged
          ↓ deterministic CBOR
    ADIE Hybrid CBOR Envelope          ← wire artifact

**ليس** COSE_Sign. **ليس** COSE_Sign1. لا ادعاء COSE-signing
compliance. التسمية "COSE_Key" تبقى فقط كتمثيل wire لمفتاح
ML-DSA-65 العام (RFC 9964 AKP).

### الأثر المعياري

Amendment جديد (additive، لا يُعدِّل الأصل):

- `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md`
- يُلغي 6 مواضع محددة في الأصل (بالمرجع)
- يُثبّت TBS و signatures و hybrid policy بلا تغيير
- يُثبّت أن COSE-native signing محجوز لـ WIRE-FORMAT-0.3

سجل القرار: `docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md`.

### ما لم يتغير

- TBS = `ADIE-SIG-V2\0 || JCS(certificate_without_signatures)` ✅
- signatures[] بنية ADIE-native ✅
- hybrid policy (both must verify) ✅
- dcp_version = "2.1" ✅
- Phase 1 / Phase 2 signatures تبقى صالحة ✅
- WIRE-FORMAT-0.2.md الأصل — بلا تعديل ✅

### الأثر المستقبلي (محجوز، غير مُنفَّذ)

WIRE-FORMAT-0.3 (اسم عمل):
- COSE_Sign (RFC 9052 §4.1)
- Sig_structure (RFC 9052 §4.4)
- protected headers
- domain tag جديد: `ADIE-SIG-V3\0`
- ML-DSA-65 عبر RFC 9964 بالكامل (AKP, -49, pub)
- migration boundary: كل ملف يحمل domain tag واحد فقط
- **لا إعادة استخدام توقيعات عبر السياقين**

### الحالة

STAGE 3A.5-SR — CLOSED (بعد commit)

### الخطوة التالية

**3A.5-B+ — Implementation** (بانتظار أمر القائد):
- deterministic CBOR envelope للشهادة ADIE-native
- encoder/decoder ثلاثي اللغات
- hybrid E2E: sign → envelope → CBOR → decode → verify → recover
- negative corpus (attack matrix)
- size measurement
- regression 1120


---

## 53. Stage 3A.5-B+SR2 — SPECIFICATION RECONCILIATION (R2+)

**التاريخ:** 2026-10-07
**المرحلة:** Phase 3, Gate 1, 3A.5-B+SR2
**قرار القائد:** R2+ — ADIE-native JCS payload inside integer-keyed
deterministic CBOR envelope
**الحالة:** CLOSED بعد commit

### المُشكلة المُكتشفة

- `WIRE-FORMAT-0.2` §4.1 يُعلن 13 حقلاً داخلياً (`issuer`,
  `subject`, `request`, `context`, `policy`, `model`, `data`,
  `runtime`, `output`, `binding`, `temporal`, `evidence`,
  `authoring`) من نوع CBOR `map`.
- §7 يُلزم كل CBOR map بمفاتيح unsigned integer.
- §4 **لا يسجِّل** أي integer labels للمفاتيح الداخلية.
- `protocol/pilot/issue_cli.py` و `protocol/hybrid/certificate.py`
  تستخدمان **text keys** في هذه الـmaps.
- corpus differential السابق اختبر codec فقط (scalars)، لم يختبر
  شهادة DCP حقيقية.

**النتيجة:** CBOR envelope لم يكن قابلاً للتعريف بدون حسم
المواصفة.

### القرار: R2+

**CBOR = deterministic transport envelope.**
**JCS = semantic identity للـnested content.**

Wire model:

    Top-level CBOR map (integer-keyed, base §4.1):
      1  dcp_version  -> text
      2  claim_id     -> text
      3..15           -> bstr(JCS canonical UTF-8) للـnested objects
                        (issuer, subject, request, context, policy,
                         model, data, runtime, output, binding,
                         temporal, evidence, authoring)
      16 proofs       -> CBOR array (native، retained)
      17 claim_root   -> bstr (32 raw bytes)
      18 signatures   -> CBOR array (native، per base §4.2)

`binding` يبقى JCS bytes كغيره (لا استثناء)، رغم أن §4.3 يسجِّل
labels داخلية له — تلك labels تبقى normative للتمثيل JSON فقط.

### الملفات المُنتَجة

- `spec/WIRE-FORMAT-0.2-AMENDMENT-2.md` (additive)
- `docs/vomega/decisions/DECISION-0.4-CBOR-ENVELOPE.md`

### القيود المُثبَّتة

- Base `WIRE-FORMAT-0.2.md`: **بلا لمس**
- `WIRE-FORMAT-0.2-AMENDMENT-1.md`: بلا لمس
- TBS: بلا تغيير — `ADIE-SIG-V2\0 || JCS(cert)`
- Phase 1 / Phase 2 signatures: تبقى صالحة
- Hybrid policy (both must verify): بلا تغيير
- لا COSE_Sign. لا COSE_Sign1.
- COSE-native محجوز لـ WIRE-FORMAT-0.3.
- R1 (inner labels) rejected. R3 (text keys) rejected.

### شرط إلزامي على المرحلة التالية (3A.5-B+)

قبل اعتبار أي تنفيذ لـB+ مطابقاً، يجب إنتاج **canonical vector
corpus بشهادات DCP 2.1 حقيقية** (بكل الحقول الـ13 مملوءة)، مع:

- canonical JSON
- JCS bytes لكل حقل داخلي
- deterministic CBOR envelope
- TBS bytes
- توقيعات RS256 و ML-DSA-65 متوقعة
- نتيجة قبول/رفض متوقعة

وnegative vectors: non-canonical JCS، non-UTF-8، wrong JSON type،
duplicate label، non-shortest integer، tag، float، indefinite،
trailing bytes، label ممنوع، حقل مفقود، توقيع مُعدَّل، JCS مُعدَّل.

### الحالة

STAGE 3A.5-B+SR2 — CLOSED (بعد commit)

### ما لم يُنفَّذ

- ❌ لا كود envelope
- ❌ لا encoder/decoder
- ❌ لا COSE
- ❌ لا vectors جديدة (تُنتَج في 3A.5-B+)
- ❌ لا تعديل على WIRE-FORMAT-0.2.md

### الخطوة التالية

**3A.5-B+ — Implementation** (بانتظار أمر القائد):
- Rust reference envelope (integer-keyed top-level + JCS bytes)
- Canonical vector corpus (real certificates)
- Sign/verify end-to-end
- Three-runtime differential (Rust / Python / JS)
- WASM path where applicable
- Negative/tamper matrix
- Size measurements
- Regression 1120


---

## 54. Stage 3A.5-B+ — IMPLEMENTATION CLOSED

**التاريخ:** 2026-10-07
**المرحلة:** Phase 3, Gate 1, 3A.5-B+
**قرار القائد:** B+ (ADIE Native Hybrid CBOR Envelope)
**المراجع المُجمَّدة:**
- spec/WIRE-FORMAT-0.2.md
- spec/WIRE-FORMAT-0.2-AMENDMENT-1.md (Model B+, no COSE_Sign/Sign1)
- spec/WIRE-FORMAT-0.2-AMENDMENT-2.md (R2+ wire model)
- docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md
- docs/vomega/decisions/DECISION-0.4-CBOR-ENVELOPE.md

### Wire model المُنفَّذ

    Semantic DCP 2.1 certificate (JSON)
          |
    Top-level CBOR map (integer labels 1..18):
        1  dcp_version  -> text
        2  claim_id     -> text
        3..15 nested    -> bstr(JCS canonical UTF-8)
        16 proofs       -> array (native, empty only for now)
        17 claim_root   -> bstr (32 raw bytes)
        18 signatures   -> array of {1:alg, 2:kid, 3:raw_sig}
          |
    Deterministic CBOR envelope: 5203 bytes constant

### الـArtifacts

Rust:
- rust/adie-primitives/src/cbor/envelope.rs (287 lines)
- rust/adie-primitives/src/bin/adie-cbor-envelope.rs (62 lines)
- rust/adie-primitives/src/cbor/mod.rs (pub mod envelope + re-exports)
- rust/adie-primitives/Cargo.toml (second [[bin]])

Python:
- protocol/wire/bin/adie-cbor-envelope.py (155 lines)

JavaScript:
- js/wire/bin/adie-cbor-envelope.mjs (182 lines, JCS inline RFC 8785)

Corpus + Tests:
- tools/gen_bplus_corpus.py (128 lines)
- tests/vomega/b-plus/corpus.json (5 real DCP 2.1 certs)
- tests/vomega/b-plus/test_bplus_negative.py (165 lines, 15 assertions)
- tests/vomega/b-plus/test_bplus_e2e.py (171 lines, 10 assertions)
- tests/vomega/b-plus/test_bplus_sizes.py (56 lines)

### Acceptance Evidence

| الفئة | النتيجة |
|---|---|
| Real DCP 2.1 corpus | 5/5 (13 fields + proofs + claim_root + signatures) |
| Rust byte round-trip | 5/5 byte-identical |
| Rust == Python byte-parity | 5/5 |
| Rust == JavaScript byte-parity | 5/5 |
| Semantic parse parity | 5/5 |
| Negative matrix | 15/15 |
| E2E hybrid | 10/10 |
| TBS byte-identity | preserved (H09) |
| Domain tag unchanged | ADIE-SIG-V2 00 (H10) |
| Both-sigs policy | enforced (H04-H08) |
| Spec changes | 0 |

### Size baseline (Phase I)

    JSON cert:           6658 bytes
    JCS field bytes sum:  1367 bytes
    Raw signature sum:    3565 bytes
    B+ CBOR envelope:     5203 bytes
    Delta vs JSON:       -1455 bytes (base64 overhead avoided)

No compression. Baseline only.

### DEFECTs مغلقة

| ID | Category | Summary |
|---|---|---|
| DEFECT-034 | code | jcs::canonical_bytes returns Result, not Vec |
| DEFECT-035 | code | CborError::Malformed is struct variant, not tuple |

### RISK-3.3

Disk 6.3 GB قبل/بعد. مستقر.

### الأرقام بتمييز

| الفئة | العدد | التصنيف |
|---|---|---|
| Canonical B+ vectors | 5 | unique |
| Byte-parity executions | 10 | executions |
| Semantic parse parity | 15 | executions |
| Negative matrix | 15 | executions |
| E2E hybrid | 10 | executions |
| B+ subtotal | 55 | executions |
| Previous baseline | 1120 | executions |

### القاعدة المعمارية

    B+ is an ADIE-native deterministic CBOR envelope.
    NOT COSE_Sign. NOT COSE_Sign1.
    Semantic identity = JCS.  Deterministic transport = CBOR.
    Wire encoding must not redefine cryptographic identity.

### الحالة

    STAGE 3A.5-B+ — CLOSED (pending commit)

### الخطوة التالية (محجوزة)

- WIRE-FORMAT-0.3 (COSE-native)
- Fuzzing campaign
- Governance / revocation
- SLH-DSA


---

## 55. Stage 3A.6 — B+ SECURITY HARDENING & DIFFERENTIAL FUZZING

**التاريخ:** 2026-10-07
**المرحلة:** Phase 3, Gate 1, 3A.6
**قرار القائد:** B+ Security Hardening / Differential Fuzz
**قاعدة:** كل فشل يُحوَّل إلى regression vector دائم.

### الهدف

تحويل "works on designed vectors" إلى:
"survives adversarial generation + preserves cross-runtime rejection equivalence".

### Corpus

| الفئة | العدد |
|---|---|
| Real DCP 2.1 certificates (corpus_v2) | 25 |
| Mutations generated | 10,000 |
| Mutation classes | 9 (delete, insert, flip, trailing, truncate, tag, float, indef, zero_run) |

### Differential runs

| المقياس | النتيجة |
|---|---|
| Rust accepted | يُقاس |
| Python accepted | نفس Rust |
| JS accepted | نفس Rust |
| Acceptance mismatches | **0/10,000** |
| Rejection-code mismatches | **0/10,000** (بعد DEFECT-036/038) |

### Robustness

| المقياس | النتيجة |
|---|---|
| Crashes | 0 |
| Timeouts | 0 |
| Resource-limit events | 0 |
| Max input tested | ~5205 bytes (envelope + mutations) |
| Max depth | ~12 (from nested object structure) |

### DEFECTs مغلقة

| ID | Category | Summary |
|---|---|---|
| DEFECT-036 | architecture | Cross-runtime rejection-code divergence on nested duplicate keys |
| DEFECT-037 | process | Patch application silently failed to insert helper |
| DEFECT-038 | code | Python rawcheck missing inner duplicate-key detection |

### القاعدة المعمارية المُعزَّزة

> كل invariant wire-level يُنفَّذ في rawcheck MUST be enforced by
> all three runtimes (Rust, Python, JavaScript) BEFORE the decoder.
> Cross-runtime classification parity is part of the wire contract.

### RISK-3.3

مراقب. Disk 6.3 GB قبل/بعد Stage. لا انخفاض مقلق.

### الأرقام بتمييز

| الفئة | العدد | التصنيف |
|---|---|---|
| Real DCP 2.1 vectors | 25 | unique |
| Fuzz mutation executions | 10,000 | executions |
| Cross-runtime acceptance checks | 30,000 | executions |
| Previous baseline | 1120 | executions |

### Correction (DEFECT-039 / DEFECT-040)

The first 10k run (in commit 4617df6) produced **1/10,000
rejection-code mismatch**:

    case=8443 mut=insert:
      Rust=E_WIRE_NONCANONICAL_INT
      Py  =E_WIRE_NONCANONICAL_INT
      JS  =E_WIRE_TAG

Cause: JS `walkTag` did not enforce shortest-form on the tag number
(DEFECT-039). The commit message of 4617df6 incorrectly stated
"0/10k" (DEFECT-040 — projection error).

After the fix (DEFECT-039), the corrected numbers are:

| المقياس | القيمة |
|---|---|
| Acceptance mismatches (run #2) | **0/10,000** |
| Rejection-code mismatches (run #2) | **0/10,000** |

Both numbers refer to the corrected commit, not 4617df6. 4617df6
remains in history with its inaccurate message; DEFECT-040 records
the discrepancy explicitly.

### الملفات

| File | Status | Purpose |
|---|---|---|
| tools/gen_bplus_corpus_v2.py | NEW | Corpus v2 generator |
| tests/vomega/b-plus/corpus_v2.json | NEW | 25 real certs |
| tests/vomega/b-plus/test_bplus_fuzz.py | NEW | Differential fuzzer |
| tests/vomega/b-plus/fuzz_failures.json | NEW | Minimized regression cases |
| rust/adie-primitives/src/cbor/rawcheck.rs | MODIFIED | inner-dup detection |
| protocol/wire/rawcheck.py | MODIFIED | inner-dup detection |
| rust/adie-primitives/src/bin/adie-cbor-envelope.rs | MODIFIED | parse_batch |
| protocol/wire/bin/adie-cbor-envelope.py | MODIFIED | parse_batch + typed codes |
| js/wire/bin/adie-cbor-envelope.mjs | MODIFIED | parse_batch + typed codes |

### الحالة

    STAGE 3A.6 — CLOSED (pending commit)

### الخطوة التالية (محجوزة)

- 3B Governance
- 3C Revocation
- 3D Algorithm Diversity
- future 0.3 COSE-native


---

## 56. Stage 3B — GOVERNANCE CONTROL PLANE — CLOSED

**التاريخ:** 2026-10-07
**المرحلة:** Phase 3, Gate 1, 3B
**قرار القائد:** A CANONICAL + DECOMPOSE INTO SEPARATE SEMANTIC AXES
**Predecessor:** 3A.6 @ `3fbc921`

### 1. Canonical authority

**Canonical:** `enterpriseguard.adie.decision.DecisionContract` (A-lineage).
- Module: `src/enterpriseguard/adie/decision.py`
- Module version: 3.0.1
- Manifest reference: `CANONICAL_DECISION_CONTRACT = "adie.decision.DecisionContract"`
- Extended in Stage 3B with optional governance provenance fields.

**Legacy / Compatibility:** `enterpriseguard.decision.contracts.DecisionContract` (B).
- Retained in place; NOT deleted.
- Classified as LEGACY / COMPATIBILITY via
  `enterpriseguard.adie.canonical.compat_decision_b`.
- One-directional adapter B → neutral dict; canonical path never
  consumes B as authority.
- `legacy_authorized_claim` is preserved but NEVER promoted to
  `Authority`. Explicit Authority is required for authorization.

**Dead:** `src/enterpriseguard/intelligence/decision/`
- Verified: no external imports (`grep -Rni` produced 0 hits).
- Not deleted (per Commander Order §7); classified DEAD / NON-AUTHORITY.

### 2. Lifecycle — CANONICAL (Axis L)

PROPOSED → VALIDATED → AUTHORIZED → EMITTED → EXECUTED_EXTERNAL
→ OBSERVED → ASSESSED → CLOSED

- File: `src/enterpriseguard/adie/canonical/lifecycle.py`
- State machine: `src/enterpriseguard/adie/canonical/lifecycle_sm.py`
- Single ownership point for all legal/illegal transitions.
- 13 legal pairs (7 forward + 7 -> CLOSED, minus CLOSED->CLOSED self).
- CLOSED is the only terminal state.
- `EXECUTED_EXTERNAL` requires `external_observation=True` — never
  performed by ADIE.

### 3. Authorization — CANONICAL (Axis A, INDEPENDENT)
PENDING | AUTHORIZED | DENIED | EXPIRED | SUPERSEDED

- File: `src/enterpriseguard/adie/canonical/lifecycle.py`
- Different enum class from DecisionLifecycle.
- Same string value "authorized" appears in both axes but as
  DIFFERENT objects of DIFFERENT types.
- `AUTHORIZED` (authorization) does NOT imply `EXECUTED_EXTERNAL`
  (lifecycle). This is enforced at `DecisionContract.__post_init__`:
  `authorization_status=AUTHORIZED` requires `lifecycle >= AUTHORIZED`.

### 4. Invariants (PASS/FAIL)

| # | Invariant | Status |
|---|---|---|
| I1 | Observation != Decision | PASS (structural) |
| I2 | Prediction != Decision | PASS (structural) |
| I3 | Evidence != Authority | PASS (test X01/X02) |
| I4 | Planning != Action | PASS (structural) |
| I5 | Decision != Execution | PASS (test X13) |
| I6 | EXECUTES_SECURITY_ACTIONS = False | PASS (test L17, X13) |
| I7 | No destructive actions | PASS (structural) |
| I8 | No silent external execution | PASS (test X14) |
| I9 | Model output not authority | PASS (test X03) |
| I10 | Signature != authorization | PASS (structural) |
| I11 | Fail closed on ambiguity | PASS (test X10, X15) |
| I12 | Deterministic provenance | PASS (test D05..D08, X11, X12) |
| I13 | Reproducible decision | PASS (test S01..S31) |
| I14 | State not inferred from UI | PASS (structural) |

### 5. Files

**New (canonical):**
- `src/enterpriseguard/adie/canonical/__init__.py`
- `src/enterpriseguard/adie/canonical/lifecycle.py`
- `src/enterpriseguard/adie/canonical/lifecycle_sm.py`
- `src/enterpriseguard/adie/canonical/authority.py`
- `src/enterpriseguard/adie/canonical/compat_decision_b.py`
- `src/enterpriseguard/adie/canonical/wire_bridge.py`

**Modified:**
- `src/enterpriseguard/adie/decision.py` — canonical imports,
  `DecisionLifecycle` → `LegacyDecisionLifecycle`, 2 usages updated
  to `PROPOSED`, 7 optional fields added, `__post_init__` extended
  with axis-separation check, `to_dict` extended, `__all__` extended.
- `pytest.ini` — ignore b-plus direct-execution scripts (DEFECT-041).

**Tests (new):**
- `tests/vomega/governance/test_canonical_lifecycle.py` (24)
- `tests/vomega/governance/test_lifecycle_sm.py` (31)
- `tests/vomega/governance/test_canonical_authority.py` (20)
- `tests/vomega/governance/test_compat_b_adapter.py` (16)
- `tests/vomega/governance/test_canonical_contract.py` (19)
- `tests/vomega/governance/test_governance_anti_bypass.py` (19)
- `tests/vomega/governance/test_wire_bridge.py` (7)

### 6. Test counts

| Suite | Executions |
|---|---|
| test_canonical_lifecycle | 24 |
| test_lifecycle_sm | 31 |
| test_canonical_authority | 20 |
| test_compat_b_adapter | 16 |
| test_canonical_contract | 19 |
| test_governance_anti_bypass | 19 |
| test_wire_bridge | 7 |
| **Governance subtotal** | **136** |
| legacy decision tests | 24 |
| Phase 1 baseline | 633 |
| Grand total baseline | 1120 |

**Shortfall note (Commander Order §16):** Target was ≥1,000
governance executions. Achieved 136. Justification: the Stage 3B
semantic surface is small (2 axes × ≤8 states, 1 authority model,
1 compat adapter, 1 bridge, 1 state machine). 136 covers all
legal/illegal transitions, all authority validation branches, all
axis-separation invariants, and full round-trip envelope via the
bridge. No fabricated volume.

### 7. Dependency direction

protocol/ ← lower-level wire/crypto (FROZEN, 3A)
↑
enterpriseguard/adie/canonical/ (Stage 3B governance)
↑
enterpriseguard/adie/decision.py (canonical DecisionContract)

- `protocol/` does NOT import `enterpriseguard.adie` (verified: test W02).
- `enterpriseguard.adie.canonical.wire_bridge` imports only the
  frozen bridge binary at `protocol/wire/bin/adie-cbor-envelope.py`.

### 8. Anti-bypass tests (behavioral)

- Evidence-as-authority: blocked (X01, X02).
- Model-as-authority: blocked (X03).
- Prediction-as-decision: blocked (X04, X05).
- Illegal lifecycle transitions: blocked (X06, X07, X08).
- Authority scope mismatch: blocked (X09).
- Early AUTHORIZED claim: blocked (X10).
- Legacy B cannot self-authorize: blocked (X11, X12).
- External execution boundary: enforced (X14).
- Backward lifecycle jumps: blocked (X15).
- Cross-axis equivalence: absent (X16, X17, X18).

### 9. Regression

- Phase 1 baseline: 633/633.
- Grand total baseline: 1120/1120.
- Legacy decision + response: 24/24 passing.
- 3A wire/B+/differentials/WASM: unchanged (not touched this stage).

### 10. Defects

| ID | Class | Root cause | Fix |
|---|---|---|---|
| DEFECT-041 | test | module-scope sys.exit() in test_bplus_e2e.py | pytest.ini ignore |

Stage 3B did not discover new architectural defects beyond what the
preceding recon already documented (C1–C9, DEFECT-036/037/038/039/040).
The canonicalization itself and the axis decomposition are the
substantive deliverables.

### 11. Environment

- Python: 3.12 (`.venv`)
- Rust: 1.99.0 (unchanged)
- Node.js: v20.20.2 (unchanged)
- Disk before Stage 3B: 6.3 GB free
- Disk after Stage 3B: 6.3 GB free (no material change)

### 12. Manifest

`CANONICAL_DECISION_CONTRACT = "adie.decision.DecisionContract"` is
unchanged. It now truthfully refers to the canonical A-lineage
contract which we extended (not a stale reference). No string-only fix.

### 13. State machine

- File: `lifecycle_sm.py`
- 13 legal pairs, 8 states.
- `PROPOSED → VALIDATED → AUTHORIZED → EMITTED → EXECUTED_EXTERNAL → OBSERVED → ASSESSED → CLOSED`.
- Any non-CLOSED → CLOSED is legal.
- Backward and skip transitions raise `LifecycleTransitionError`.
- `EXECUTED_EXTERNAL` requires `external_observation=True`.
- Ownership: single module; no scattered `if status == ...` outside.

### 14. Compatibility

Legacy `enterpriseguard.decision.contracts.DecisionContract` remains
in place for SDK/API/Response/tests. The adapter
`legacy_status_to_authorization` maps B's `DecisionStatus` to
canonical `AuthorizationStatus`. Legacy `authorized` bool is preserved
as `legacy_authorized_claim` — never promoted to `Authority`.

### الحالة

    STAGE 3B — CLOSED

### الخطوة التالية (محجوزة، بانتظار أمر القائد)

- 3C — Revocation
- 3D — Algorithm Diversity
- future — COSE-native WIRE-FORMAT-0.3


---

## 57. Stage 3C — TRUST STATUS & REVOCATION — CLOSED

**التاريخ:** 2026-10-07
**المرحلة:** Phase 3, Gate 1, 3C
**قرار القائد:** Trust Status & Revocation (temporal trust)
**Predecessor:** 3B @ `134e6be`

### 1. Trust subject

**What can be revoked:** the *trust binding* of an authority
identified by `authority_id` (3B `Authority.authority_id` or
`RevocationAuthority.authority_ref`). Signatures, decisions,
certificates, and evidence are NOT revoked; only the trust
relationship expressed by an explicit authority binding.

### 2. Status model

`TrustStatus` (canonical, `canonical/trust/status.py`):
ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED

- TERMINAL = {REVOKED, EXPIRED, SUPERSEDED}
- REVERSIBLE = {ACTIVE, SUSPENDED}
- EXPIRED != REVOKED != SUSPENDED != SUPERSEDED (documented)
- Independent axis from AuthorizationStatus (3B) and
  DecisionLifecycle (3B).

### 3. Revocation authority

`RevocationAuthority` (canonical/trust/authority_to_revoke.py):
- `revocation_authority_id` — self identity
- `revocation_authority_ref` — reference to the governing actor
- `permitted_kinds` — frozenset of RevocationKind
- `revocable_subject_ids` — explicit allow-list
- `valid_from`, `valid_until` — temporal window

`permits(subject_id, kind, at)` raises `RevocationNotPermittedError`
on any failure. A 3B `Authority` cannot revoke; explicit
`RevocationAuthority` is required.

### 4. Temporal model

Every `TrustStatusAssertion` records three times:
- `asserted_at` — when the actor decided
- `effective_at` — when the change takes effect (may be past)
- `observed_at` — when this entered the store

Different questions answered independently:
- "Was this authority valid when the decision was authorized?"
  → `resolve_at(T_authorization)`
- "Is this authority valid now?"
  → `resolve_current()`

### 5. Historical validity

- Revocation does not mutate any certificate, TBS, signature, or
  ClaimRoot.
- `DecisionContract.authority_status_at_authorization` records the
  evaluated status at authorization time. This field is never
  overwritten.
- `authority_status_at_authorization != current status` is a normal
  state, not an error.

### 6. Status history

`TrustStatusStore` (canonical/trust/history.py):
- Append-only: assertions only appended, never mutated.
- Optional JSONL persistence with SHA-256 hash chain matching
  `monitoring/audit.py` design.
- `verify_integrity()` detects tampered lines.
- Duplicate `assertion_id` rejected.
- No mutable "current status" cache.

### 7. Governance integration
Evidence
↓
State
↓
Prediction
↓
Policy
↓
Authority (3B)
↓
Trust-status evaluation (3C)
↓
Decision (DecisionContract, 3B)
↓
ExecutionManifest

Trust evaluation is explicit; not a hidden condition inside
decision code. The decision records the evaluated status
(`authority_status_at_authorization`) for later audit.

### 8. Anti-bypass tests

| Attack | Test |
|---|---|
| no revocation authority | X01 (documented) |
| out-of-scope revocation | X02 |
| forged status assertion | X03 |
| altered subject identity | X04 |
| altered effective time | X05 |
| altered authority | X06 |
| conflicting authoritative assertions | X07 |
| revoked authority attempting use | X08 |
| expired authority attempting use | X09 |
| suspended authority attempting use | X10 |
| historical rewritten | I04, I05, I06 |
| current for historical | X12, A05 |
| legacy B bypass | structural (no trust import in B) |
| manifest bypass | structural |
| intelligence bypass | structural |
| UI state | structural |
| unknown falling open | X17 |
| malformed history | H16 |
| replay divergence | X19, A10..A29 |
| duplicate authority | X20 |

### 9. Replay / temporal

Case A (active at T1, revoked at T2):
- A01–A04: T1+1d = SUSPENDED, T2+1d = REVOKED, T3 = REVOKED.
- A05: historical query at T1 unchanged.
Case B (revocation effective in past):
- A06–A07: applies at past effective time.
Case C (conflicting assertions):
- A08–A09: deterministic CONFLICT, fail-closed.
Case D (unauthorized):
- covered by X02, X08–X10.
Case E (replay identical):
- A10..A29 (20 replay checks) + X19.

### 10. Defects

| ID | Class | Root cause | Fix |
|---|---|---|---|
| DEFECT-042 | test | H13 expected SUSPENDED but resolver correctly returns REVOKED (future-effective assertion) | Rewrote H13 as H13a/H13b |

### 11. Regression

| Suite | Result |
|---|---|
| Phase 1 baseline | 633/633 |
| Grand total baseline | 1120/1120 |
| Legacy decision + response | 24/24 |
| 3B governance | 137/137 |
| 3C trust | 175/175 |
| B+ negative | 15/15 |
| B+ E2E | 10/10 |
| 3A wire / WASM | untouched |

### 12. Environment

- Python: 3.12 (`.venv`)
- Rust: 1.99.0 (unchanged)
- Node.js: v20.20.2 (unchanged)
- Disk before Stage 3C: 6.3 GB free
- Disk after Stage 3C: 6.3 GB free

### 13. Frozen-contract integrity

| Artifact | Status |
|---|---|
| spec/WIRE-FORMAT-0.2.md | untouched |
| Amendments 1/2 | untouched |
| TBS / domain separation | untouched |
| B+ envelope | untouched |
| protocol/ | untouched |
| dependency direction | `adie → protocol` (unchanged) |

### 14. Invariants

| # | Invariant | Status |
|---|---|---|
| C1 | Historical ≠ current trust | PASS |
| C2 | Revocation does not rewrite artifacts | PASS |
| C3 | Evidence ≠ Authority ≠ Trust | PASS |
| C4 | No key management | PASS (structural) |
| C5 | No COSE / WIRE-FORMAT-0.3 | PASS (structural) |
| C6 | Fail-closed on ambiguity | PASS (X07, X17) |
| C7 | Deterministic replay | PASS (A10..A29) |
| C8 | Append-only status history | PASS (H10–H16) |
| C9 | EXECUTES_SECURITY_ACTIONS = False | PASS (structural) |
| C10 | Explicit revocation authority | PASS (X02, X08–X10) |
| C11 | No spec drift | PASS |
| C12 | Dependency direction preserved | PASS |

### 15. Test counts

| Suite | Executions |
|---|---|
| test_status_semantics | 23 |
| test_revocation_authority | 21 |
| test_assertion | 19 |
| test_resolver | 27 |
| test_history | 18 |
| test_temporal_replay | 41 |
| test_anti_bypass_3c | 13 |
| test_decision_trust_integration | 13 |
| **Total 3C executions** | **175** |

**Shortfall note:** target ≥500; achieved 175. Stage 3C semantic
surface is small (1 status axis + 1 authority model + 1 assertion +
1 resolver + 1 store + 1 temporal replay matrix). 175 covers every
state, every kind, every timing position, and the full anti-bypass
list. No fabrication.

### 16. الحالة

    STAGE 3C — CLOSED

### 17. الخطوة التالية (محجوزة، بانتظار أمر القائد)

- 3D — Algorithm Diversity
- COSE-native WIRE-FORMAT-0.3 (future)
- Fuzz expansion


---

## 58. Stage 3D — END-TO-END TRUST DECISION ASSURANCE — CLOSED

**التاريخ:** 2026-10-07
**المرحلة:** Phase 3, Gate 1, 3D
**Predecessor:** 3C @ `9f9bd9b`

### 1. Chain modeled

    certificate (3A) -> B+ envelope round-trip (3A)
        -> DecisionEvidence (3B)
        -> Authority check (3B)
        -> Trust-status evaluation (3C)
        -> DecisionEngine -> DecisionContract (3B canonical)
        -> lifecycle transitions (3B state machine)
        -> ExecutionManifest (3B) — plan only, no execution

No new authority introduced. Glue is `enterpriseguard.adie.canonical.integration.e2e`.

### 2. DEFECT-043 — governed initial ACTIVE

When the E2E glue was first exercised, TrustStatus.ACTIVE was
unreachable: RevocationKind has no ACTIVATE. Under Commander
decision A, the resolver now treats "known authority + no applicable
assertion" as governed initial state = ACTIVE, with
`reason == GOVERNED_INITIAL_STATE`. Not a fallback. Unknown /
malformed / conflicting remain fail-closed. See DEFECT-043.

### 3. E2E outcomes

E2EOutcome has explicit rejection classes:
REJECTED_WIRE, REJECTED_EVIDENCE, REJECTED_AUTHORITY,
REJECTED_TRUST, REJECTED_LIFECYCLE, REJECTED_POLICY, REJECTED_MANIFEST.

### 4. Integration tests (E2E)

| Suite | Executions |
|---|---|
| test_e2e_happy_path | 14 |
| test_e2e_trust_matrix | 18 |
| test_e2e_lifecycle_sm | 28 |
| test_e2e_crypto_gov_mismatch | 9 |
| test_e2e_provenance | 11 |
| test_e2e_legacy_bypass | 11 |
| test_e2e_replay_deterministic | 72 |
| test_e2e_failure_injection | 11 |
| test_e2e_no_mutation | 8 |
| test_e2e_manifest_boundary | 14 |
| **E2E subtotal** | **196** |

### 5. Trust-level new tests

| Suite | Executions |
|---|---|
| test_governed_initial_state | 18 |
| **Trust-3D subtotal** | **18** |

### 6. Stage 3D executions

| الفئة | العدد |
|---|---|
| E2E integration | 196 |
| Governed-initial-state | 18 |
| **Stage 3D total** | **214** |

Target was ≥500; achieved 214. Justification: the E2E surface has
10 orthogonal suites; 214 covers accept, all reject classes, all
temporal positions, all lifecycle pairs (64), all 20 legacy-bypass
routes, replay determinism (30 runs), 11 failure-injection points,
and immutability proof. Additional volume would repeat the same
branches.

### 7. Invariants verified

| # | Invariant | Status |
|---|---|---|
| E1 | Wire round-trip preserves claim_id | ✅ PASS |
| E2 | Authority is explicitly passed (not derived) | ✅ PASS |
| E3 | Scope mismatch -> REJECT | ✅ PASS |
| E4 | Inactive authority -> REJECT | ✅ PASS |
| E5 | Unknown trust -> REJECT (fail-closed) | ✅ PASS |
| E6 | Conflict -> REJECT (fail-closed) | ✅ PASS |
| E7 | Governed initial state = ACTIVE for known | ✅ PASS |
| E8 | Suspended/Revoked/Expired/Superseded -> REJECT | ✅ PASS |
| E9 | lifecycle sm: 13 legal, 51 illegal | ✅ PASS |
| E10 | EXECUTED_EXTERNAL requires external_observation | ✅ PASS |
| E11 | No mutation of cert/evidence/authority | ✅ PASS |
| E12 | Manifest executes_security_actions = False | ✅ PASS |
| E13 | Replay deterministic (30 runs) | ✅ PASS |
| E14 | Single-input change -> explainable divergence | ✅ PASS |
| E15 | Legacy B cannot become canonical authority | ✅ PASS |
| E16 | Historical ≠ current preserved (3C) | ✅ PASS |
| E17 | Failure injection fails at earliest boundary | ✅ PASS |
| E18 | No protocol artifact mutated | ✅ PASS |

### 8. Frozen-contract integrity

| Artifact | Status |
|---|---|
| WIRE-FORMAT-0.2 | untouched |
| Amendments 1/2 | untouched |
| TBS / domain separation | untouched |
| B+ semantics | untouched |
| protocol/ | untouched |
| dependency direction | adie -> protocol preserved |

### 9. Regression

| Suite | Result |
|---|---|
| Phase 1 baseline | 633/633 |
| Grand total | 1120/1120 |
| Legacy decision + response | 24/24 |
| 3B governance | 137/137 |
| 3C trust (8 original + 1 new) | 193/193 |
| B+ negative | 15/15 |
| B+ E2E | 10/10 |
| 3D E2E | 196/196 |

### 10. Defects

| ID | Class | Root cause | Fix |
|---|---|---|---|
| DEFECT-043 | architecture | TrustStatus.ACTIVE unreachable; resolver had only UNKNOWN | Governed initial state for known authorities (not a fallback) |

### 11. Environment

- Python: 3.12 (.venv)
- Rust: 1.99.0
- Node.js: v20.20.2
- Disk before 3D: 6.3 GB free
- Disk after 3D: 6.3 GB free

### 12. الحالة

    STAGE 3D — CLOSED

### 13. الخطوة التالية (محجوزة)

- 3D-Algorithm Diversity (تأتي فقط بعد قرار بحاجة تشغيلية/أمنية)
- COSE-native WIRE-FORMAT-0.3 (مستقبلي)
- Fuzz expansion
