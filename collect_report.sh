#!/bin/bash
# سكربت جمع تقرير شامل عن المشروع
OUT=~/Desktop/full_project_report.txt

# دالة مساعدة لطباعة عنوان قسم
section() {
  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo "▶ $1"
  echo "════════════════════════════════════════════════════════════"
  echo ""
}

# دالة لتنفيذ أمر وطباعته مع فاصل
run() {
  echo "───── \$ $* ─────"
  eval "$@" 2>&1
  echo ""
}

# دالة لعرض محتوى ملف بأمان
show_file() {
  local f="$1"
  echo "───── \$ cat $f ─────"
  if [ -f "$f" ]; then
    cat "$f"
  else
    echo "⚠️  الملف غير موجود: $f"
  fi
  echo ""
}

# بدء التقرير
{
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║  تقرير المشروع الكامل                                       ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo "التاريخ: $(date)"
  echo "المجلد: $(pwd)"
  echo "المستخدم: $(whoami)"
  echo ""

  # ═══ 1. الملفات الجذرية ═══
  section "1. الملفات الجذرية (pyproject, pytest, version...)"
  show_file pyproject.toml
  show_file pytest.ini
  show_file VERSION
  show_file requirements.txt
  show_file requirements.lock.txt

  # ═══ 2. اختبارات tests/ ═══
  section "2. بنية tests/"
  run "find tests -type f -name '*.py' | sort"

  show_file tests/test_sdk_signing.py
  show_file tests/test_sdk_client.py
  show_file tests/test_api_server.py
  show_file tests/test_decision_contract.py
  show_file tests/test_response_contract.py
  show_file tests/test_integrity_monitor.py
  show_file tests/test_prompt_security.py

  # ═══ 3. Git history ═══
  section "3. Git — آخر 40 commit"
  run "git log --oneline -40"

  section "4. Git — commits المعالم"
  run "git show --stat 8ee5e24"
  run "git show --stat 07583b4"
  run "git show --stat 949ec12"
  run "git show --stat ec7203a"
  run "git show --stat 3f38b49"
  run "git show --stat b94c6c1"

  section "5. Git — الفروقات في آخر أسبوع"
  run "git log --since='2026-09-12' --oneline --stat"

  # ═══ 6. tools/ ═══
  section "6. بنية tools/"
  run "find tools -maxdepth 1 -type f -name '*.py' | sort"

  show_file tools/innocence_chain.py
  show_file tools/signing_backend.py
  show_file tools/sibb_storage.py
  show_file tools/sibb_innocence_integration.py
  show_file tools/open_verifier.py
  show_file tools/sovereign_http_server.py
  show_file tools/paths_config.py

  # ═══ 7. continuity/ ═══
  section "7. continuity/"
  show_file continuity/COMPONENTS.md
  show_file continuity/GLOSSARY.md
  show_file continuity/RULES.md
  show_file continuity/DECISIONS_INDEX.md
  show_file continuity/CURRENT_STATE.md

  # ═══ 8. docs/ ═══
  section "8. docs/"
  show_file docs/PLAN_CHANGELOG.md
  show_file docs/ADIE_MASTER_PLAN.md
  show_file docs/PRODUCT_HYPOTHESIS.md
  show_file docs/ROADMAP.md

  # ═══ 9. Git status ═══
  section "9. Git status & branches"
  run "git status --short"
  run "git branch -a"
  run "git log --oneline -5"
  run "git stash list"

  # ═══ 10. Python environment ═══
  section "10. بيئة Python"
  run "pip show enterpriseguard"
  run "python3 -c 'import enterpriseguard; print(enterpriseguard.__file__)'"
  run "python3 -c 'from enterpriseguard.signing import sign_bytes; print(\"signing OK\")'"
  run "python3 -c 'from enterpriseguard.sdk import Client; print(\"sdk OK\")'"
  run "python3 -c 'from enterpriseguard.decision.contracts import ADIEDecision; print(\"decision OK\")'"

  # ═══ 11. الاختبارات ═══
  section "11. تشغيل pytest (بدون UI)"
  run "python3 -m pytest tests/ --ignore=tests/test_ui.py -v --tb=short 2>&1 | tail -50"

  section "12. اختبار SDK signing"
  run "python3 -m pytest tests/test_sdk_signing.py -v"

  section "13. اختبار API"
  run "python3 -m pytest tests/test_api_server.py -v"

  # ═══ 14. grep checks ═══
  section "14. grep — المتغيرات الحساسة"
  run "grep -rn 'EXECUTES_SECURITY_ACTIONS' src/enterpriseguard/ --include='*.py'"
  run "grep -rn 'DESTRUCTIVE_ACTIONS_ALLOWED' src/enterpriseguard/ --include='*.py'"

  # ═══ 15. existence checks ═══
  section "15. وجود مجلدات adie/intelligence"
  run "ls -d adie/ intelligence/ src/enterpriseguard/adie/ src/enterpriseguard/intelligence/ 2>/dev/null"

  section "16. وجود مجلدات docs/"
  run "ls -la docs/COMPONENTS/ 2>/dev/null"
  run "ls -la docs/RECIPES/ 2>/dev/null"

  # ═══ 17. docs إضافية ═══
  section "17. docs إضافية"
  show_file docs/QUICKSTART.md
  show_file docs/FAQ.md
  show_file docs/COMPONENTS/README.md
  show_file docs/ARCHITECTURAL_VISION.md
  show_file docs/WHITEPAPER.md
  show_file docs/DC-038_COMPLIANCE_MATRIX.md

  # ═══ 18. merge.py ═══
  section "18. merge.py"
  show_file merge.py
  run "find . -name 'merge*.py' -not -path './.git/*'"

  # نهاية
  echo ""
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║  ✅ انتهى التقرير                                           ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo "عدد الأسطر: $(wc -l < "$OUT" 2>/dev/null)"
} > "$OUT" 2>&1

echo "✅ تم حفظ التقرير في: $OUT"
echo "📄 عدد الأسطر: $(wc -l < "$OUT")"
