#!/usr/bin/env bash

OUTPUT_FILE="inspection_step2.txt"

echo "==========================================" > "$OUTPUT_FILE"
echo " EnterpriseGuard - Contracts Structure Inspection" >> "$OUTPUT_FILE"
echo "==========================================" >> "$OUTPUT_FILE"

echo -e "\n--- [1] Detailed Imports (Lines 90-130) ---" >> "$OUTPUT_FILE"
sed -n '90,130p' src/enterpriseguard/intelligence/prediction/contracts.py >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [2] Lines surrounding first class (Lines 300-330) ---" >> "$OUTPUT_FILE"
sed -n '300,330p' src/enterpriseguard/intelligence/prediction/contracts.py >> "$OUTPUT_FILE" 2>&1

echo "Done. Results written to $OUTPUT_FILE"
