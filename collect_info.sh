#!/usr/bin/env bash

OUTPUT_FILE="inspection_report.txt"

echo "==========================================" > "$OUTPUT_FILE"
echo " EnterpriseGuard - Inspection Report" >> "$OUTPUT_FILE"
echo " Date: $(date -u)" >> "$OUTPUT_FILE"
echo "==========================================" >> "$OUTPUT_FILE"

echo -e "\n--- [1] Environment & Dependencies Check ---" >> "$OUTPUT_FILE"
python3 -c "import pydantic; print('Pydantic version:', pydantic.__version__)" >> "$OUTPUT_FILE" 2>&1
python3 -c "import jcs; print('JCS status: Installed')" >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [2] Git Working Tree Status ---" >> "$OUTPUT_FILE"
git status --short >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [3] Imports in prediction/contracts.py ---" >> "$OUTPUT_FILE"
head -n 25 src/enterpriseguard/intelligence/prediction/contracts.py >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [4] Defined Classes in prediction/contracts.py ---" >> "$OUTPUT_FILE"
grep -n "class " src/enterpriseguard/intelligence/prediction/contracts.py >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [5] Tail of prediction/contracts.py ---" >> "$OUTPUT_FILE"
tail -n 40 src/enterpriseguard/intelligence/prediction/contracts.py >> "$OUTPUT_FILE" 2>&1

echo "Done. Results written to $OUTPUT_FILE"
