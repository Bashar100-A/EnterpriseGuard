import time
from typing import Dict, Any, List

class ComplianceEngine:
    def __init__(self, policy: Dict[str, Any] = None):
        # السياسات الافتراضية المتوافقة مع EU AI Act (Article 12: Traceability & Article 14: Human Oversight)
        self.policy = policy or {
            "require_traceability_id": True,
            "require_human_oversight": True,
            "max_risk_score": 0.85,
            "allowed_roles": ["admin", "auditor", "system"]
        }

    def evaluate_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تقييم حدث الذكاء الاصطناعي مقابل سياسات الامتثال وتحديد حالة الالتزام
        """
        violations: List[str] = []
        
        # 1. التحقق من التتبع والشفافية (Article 12 - Traceability)
        if self.policy.get("require_traceability_id"):
            if not event_data.get("trace_id") or not event_data.get("model_version"):
                violations.append("انتهاك المادة 12 (EU AI Act): غياب معرف التتبع (trace_id) أو إصدار النموذج (model_version).")

        # 2. التحقق من الرقابة البشرية (Article 14 - Human Oversight)
        if self.policy.get("require_human_oversight"):
            risk_score = event_data.get("risk_score", 0.0)
            if risk_score > self.policy.get("max_risk_score", 0.85):
                if not event_data.get("human_approved", False):
                    violations.append(f"انتهاك المادة 14 (EU AI Act): درجة المخاطرة ({risk_score}) تتجاوز الحد المسموح به دون موافقة بشرية.")

        # 3. التحقق من صلاحيات الدور (Role Enforcement)
        user_role = event_data.get("user_role", "unknown")
        if user_role not in self.policy.get("allowed_roles", []):
            violations.append(f"تحذير أمني: الدور المستند '{user_role}' غير مدرج في قائمة الأدوار المعتمدة.")

        # تحديد الحالة النهائية
        status = "COMPLIANT" if len(violations) == 0 else "NON_COMPLIANT"

        return {
            "event_id": event_data.get("event_id"),
            "status": status,
            "violations": violations,
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "policy_version": "EU_AI_ACT_V1.0"
        }
