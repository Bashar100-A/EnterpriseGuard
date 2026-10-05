#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "=== branch ==="
git branch --show-current

echo "=== last 3 commits ==="
git log --oneline -3

echo "=== frozen 51 suite ==="
python3 tests/adversarial/run_all.py 2>&1 | tail -3

echo "=== vOmega 12 suite ==="
python3 tests/vomega/run_all.py 2>&1 | tail -3

echo "=== frozen files untouched? ==="
if git diff --quiet master..vOmega -- verify.html tests/adversarial/run_all.py; then
  echo "OK: frozen files untouched"
else
  echo "WARN: frozen files modified"
  git diff --stat master..vOmega -- verify.html tests/adversarial/run_all.py
fi

echo "=== CONTINUITY.md present? ==="
[ -f docs/vomega/CONTINUITY.md ] && echo "OK" || echo "MISSING"
