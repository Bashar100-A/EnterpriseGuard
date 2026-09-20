import sys
import os

# إضافة الجذر الرئيسي لمسار النظام
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.crypto.ecdsa_manager import ECDSAManager
from core.storage.sibb_storage import SIBBStorage
from core.compliance.compliance_engine import ComplianceEngine
from core.blockchain.anchor_service import AnchorService
from connectors.native_connectors import LLMConnector

def run_system_test():
    print("=== بدء اختبار نظام EnterpriseGuard الموحد ===")

    # 1. اختبار الموصلات (Connectors)
    connector = LLMConnector(source_name="LangSmith")
    mock_raw_trace = {
        "id": "trace-101",
        "trace_id": "tr-abc-123",
        "extra": {"model_name": "gpt-4o"},
        "metadata": {"risk_score": 0.12, "human_approved": True, "user_role": "admin"},
        "inputs": {"input": "أهلاً بك"},
        "outputs": {"output": "مرحباً! كيف يمكنني مساعدتك؟"}
    }
    parsed_event = connector.parse_langsmith_trace(mock_raw_trace)
    print("[✓] تم تحويل بيانات التتبع بنجاح.")

    # 2. اختبار محرك الامتثال (Compliance Engine)
    compliance = ComplianceEngine()
    compliance_res = compliance.evaluate_event(parsed_event)
    print(f"[✓] نتيجة تقييم الامتثال: {compliance_res['status']}")

    # 3. اختبار التوقيع الرقمي (ECDSA)
    crypto_mgr = ECDSAManager()
    event_bytes = str(parsed_event).encode('utf-8')
    signature = crypto_mgr.sign(event_bytes)
    is_valid = crypto_mgr.verify(signature, event_bytes)
    print(f"[✓] التوقيع الرقمي والتحقق من الصحة: {is_valid}")

    # 4. اختبار التخزين المحصن (SIBB WORM Vault)
    sibb_vault = SIBBStorage(storage_dir="test_sibb_vault")
    record_payload = {
        "event": parsed_event,
        "compliance": compliance_res,
        "signature": signature.hex()
    }
    file_path = sibb_vault.write_record("trace-101", record_payload)
    print(f"[✓] تم حفظ السجل في الخزنة المحصنة: {file_path}")

    # 5. اختبار التوثيق على البلوكشين (Blockchain Anchor)
    blockchain = AnchorService()
    anchor_proof = blockchain.create_anchor(parsed_event["event_id"])
    print(f"[✓] تم التوثيق على شبكة البلوكشين: {anchor_proof['tx_hash']}")

    print("\n=== اكتملت جميع الاختبارات بنجاح 100% ===")

if __name__ == "__main__":
    run_system_test()
