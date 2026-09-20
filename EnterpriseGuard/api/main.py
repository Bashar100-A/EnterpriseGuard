import uuid
import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

# إضافة المجلد الرئيسي لمسار النظام لاستيراد الوحدات
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.crypto.ecdsa_manager import ECDSAManager
from core.storage.sibb_storage import SIBBStorage
from core.compliance.compliance_engine import ComplianceEngine
from core.blockchain.anchor_service import AnchorService
from connectors.native_connectors import LLMConnector

app = FastAPI(
    title="EnterpriseGuard AAAC Core Engine",
    version="1.0.0-Enterprise",
    description="Automated AI Governance, Compliance & Tamper-Proof Audit Vault"
)

# تهيئة الخدمات الموحدة
crypto_mgr = ECDSAManager()
sibb_vault = SIBBStorage()
compliance = ComplianceEngine()
blockchain = AnchorService()
connector = LLMConnector()

class IngestRequest(BaseModel):
    source: str = "LangSmith"  # LangSmith or Langfuse or Native
    raw_trace: Dict[str, Any]

@app.get("/")
def read_root():
    return {
        "system": "EnterpriseGuard AAAC Engine",
        "status": "OPERATIONAL",
        "version": "1.0.0-Enterprise Release",
        "modules": {
            "crypto": "ECDSA SECP256R1 Active",
            "storage": "SIBB WORM Vault Active",
            "compliance": "EU AI Act Engine Active",
            "blockchain": "Ethereum Sepolia Anchor Active"
        }
    }

@app.post("/api/v1/ingest")
def ingest_trace(payload: IngestRequest):
    try:
        # 1. تحويل سجلات التتبع من الموصلات
        if payload.source.lower() == "langsmith":
            parsed_event = connector.parse_langsmith_trace(payload.raw_trace)
        elif payload.source.lower() == "langfuse":
            parsed_event = connector.parse_langfuse_trace(payload.raw_trace)
        else:
            parsed_event = payload.raw_trace

        event_id = parsed_event.get("event_id", str(uuid.uuid4()))

        # 2. التقييم مقابل سياسات الامتثال (EU AI Act)
        compliance_result = compliance.evaluate_event(parsed_event)

        # 3. توقيع الحدث رقمياً عبر ECDSA
        event_bytes = str(parsed_event).encode('utf-8')
        signature = crypto_mgr.sign(event_bytes).hex()

        # 4. حفظ البيانات في صندوق SIBB المحصن (WORM)
        record_payload = {
            "event": parsed_event,
            "compliance": compliance_result,
            "signature": signature
        }
        sibb_file_path = sibb_vault.write_record(event_id, record_payload)

        # 5. التوثيق على شبكة البلوكشين والأختام الزمنية
        record_hash = sibb_vault.read_record(event_id).get("event", {}).get("event_id", event_id)
        anchor_proof = blockchain.create_anchor(record_hash)

        return {
            "status": "SUCCESS",
            "event_id": event_id,
            "compliance_status": compliance_result["status"],
            "signature": signature[:20] + "...",
            "storage_path": sibb_file_path,
            "blockchain_anchor": anchor_proof
        }

    except FileExistsError as fe:
        raise HTTPException(status_code=409, detail=str(fe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

@app.get("/api/v1/report/{event_id}")
def get_compliance_report(event_id: str):
    try:
        record = sibb_vault.read_record(event_id)
        return {
            "status": "VERIFIED",
            "record": record
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="السجل غير موجود أو تم حذف بياناته.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
