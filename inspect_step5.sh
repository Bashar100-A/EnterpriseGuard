#!/usr/bin/env bash

OUTPUT_FILE="inspection_step5.txt"

echo "==========================================" > "$OUTPUT_FILE"
echo " EnterpriseGuard - Ring Storage Inspection" >> "$OUTPUT_FILE"
echo " Date: $(date -u)" >> "$OUTPUT_FILE"
echo "==========================================" >> "$OUTPUT_FILE"

echo -e "\n--- [1] Searching for ring_storage references ---" >> "$OUTPUT_FILE"
grep -rnE "ring_storage|\.jsonl" . --exclude-dir={.git,__pycache__,.pytest_cache} >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [2] Checking tools directory contents ---" >> "$OUTPUT_FILE"
ls -la tools/ >> "$OUTPUT_FILE" 2>&1

echo "Done. Results written to $OUTPUT_FILE"
