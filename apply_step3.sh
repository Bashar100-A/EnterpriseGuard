#!/usr/bin/env bash

TARGET_FILE="src/enterpriseguard/intelligence/prediction/contracts.py"
OUTPUT_FILE="step3_report.txt"

echo "==========================================" > "$OUTPUT_FILE"
echo " EnterpriseGuard - Step 3 Implementation Report" >> "$OUTPUT_FILE"
echo " Date: $(date -u)" >> "$OUTPUT_FILE"
echo "==========================================" >> "$OUTPUT_FILE"

# Execute python cleanly with stdout/stderr redirection
python3 - >> "$OUTPUT_FILE" 2>&1 << 'PYTHON_SCRIPT'
import sys

file_path = "src/enterpriseguard/intelligence/prediction/contracts.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "TypedFeatureSnapshot" in content:
    print("TypedFeatureSnapshot is already present in contracts.py")
    sys.exit(0)

# 1. Add required imports
imports_to_add = """
import hashlib
import math
import jcs
from pydantic import BaseModel, ConfigDict, Field, field_validator
"""

content = content.replace("import dataclasses", "import dataclasses" + imports_to_add)

# 2. Update __all__
all_replacement = """__all__ = [
    "TypedFeatureSnapshot",
    "PredictionContract",
"""
content = content.replace('__all__ = [\n', all_replacement)

# 3. Add classes definition right before PredictionStatus
classes_code = """

# ============================================================================
# Pydantic Immutable Domain Contracts (Phase 2 - JCS Deterministic)
# ============================================================================


class TypedFeatureSnapshot(BaseModel):
    \"\"\"
    Immutable snapshot of feature inputs for prediction.
    Strictly rejects NaN, Inf, or undefined float values to ensure deterministic hashing.
    \"\"\"
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    features: dict[str, Any]

    @field_validator("features")
    @classmethod
    def _validate_features(cls, v: dict[str, Any]) -> dict[str, Any]:
        for k, val in v.items():
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                raise ValueError(f"Feature '{k}' contains non-serializable float value (NaN/Inf)")
        return v


class PredictionContract(BaseModel):
    \"\"\"
    Immutable domain contract representing a cryptographically verifiable prediction evidence.
    \"\"\"
    model_config = ConfigDict(frozen=True)

    contract_id: str
    model_name: str
    model_version: str
    feature_snapshot: TypedFeatureSnapshot
    prediction_value: Any
    confidence: dict[str, Any]
    created_at: str

    def canonical_bytes(self) -> bytes:
        \"\"\"
        Returns deterministic RFC 8785 (JCS) JSON bytes representation.
        \"\"\"
        payload = self.model_dump(mode="json")
        return jcs.canonicalize(payload)

    def canonical_hash(self) -> str:
        \"\"\"
        Computes SHA-256 hash over canonical JCS bytes.
        \"\"\"
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

"""

content = content.replace("class PredictionStatus(str, Enum):", classes_code + "class PredictionStatus(str, Enum):")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully patched contracts.py with TypedFeatureSnapshot and PredictionContract")
PYTHON_SCRIPT

echo -e "\n--- [1] Checking syntax via python -m py_compile ---" >> "$OUTPUT_FILE"
python3 -m py_compile "$TARGET_FILE" >> "$OUTPUT_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "Syntax Check: PASSED" >> "$OUTPUT_FILE"
else
    echo "Syntax Check: FAILED" >> "$OUTPUT_FILE"
fi

echo -e "\n--- [2] Running pytest on contracts module ---" >> "$OUTPUT_FILE"
pytest tests/ -k "prediction or contracts" --maxfail=1 >> "$OUTPUT_FILE" 2>&1

echo -e "\n--- [3] Git Diff Summary ---" >> "$OUTPUT_FILE"
git diff "$TARGET_FILE" | head -n 40 >> "$OUTPUT_FILE" 2>&1

echo "Done. Report generated in $OUTPUT_FILE"
