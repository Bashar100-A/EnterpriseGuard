import uuid
import time
from typing import Dict, Any

class LLMConnector:
    """
    محول موحد لجلب وتحويل سجلات التتبع من منصات LangSmith و Langfuse
    إلى صيغة موحدة قابلة للمعالجة والتدقيق بواسطة EnterpriseGuard
    """
    def __init__(self, source_name: str = "LangSmith"):
        self.source_name = source_name

    def parse_langsmith_trace(self, raw_trace: Dict[str, Any]) -> Dict[str, Any]:
        """تحويل سجلات LangSmith إلى بنية بيانات موحدة"""
        return {
            "event_id": raw_trace.get("id", str(uuid.uuid4())),
            "trace_id": raw_trace.get("trace_id", str(uuid.uuid4())),
            "source": "LangSmith",
            "model_version": raw_trace.get("extra", {}).get("model_name", "gpt-4o"),
            "risk_score": raw_trace.get("metadata", {}).get("risk_score", 0.1),
            "human_approved": raw_trace.get("metadata", {}).get("human_approved", True),
            "user_role": raw_trace.get("metadata", {}).get("user_role", "admin"),
            "prompt": raw_trace.get("inputs", {}).get("input", ""),
            "response": raw_trace.get("outputs", {}).get("output", ""),
            "timestamp": raw_trace.get("end_time") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    def parse_langfuse_trace(self, raw_trace: Dict[str, Any]) -> Dict[str, Any]:
        """تحويل سجلات Langfuse إلى بنية بيانات موحدة"""
        return {
            "event_id": raw_trace.get("id", str(uuid.uuid4())),
            "trace_id": raw_trace.get("traceId", str(uuid.uuid4())),
            "source": "Langfuse",
            "model_version": raw_trace.get("model", "gpt-4o"),
            "risk_score": raw_trace.get("scores", {}).get("risk", 0.0),
            "human_approved": raw_trace.get("metadata", {}).get("human_approved", False),
            "user_role": raw_trace.get("userId", "system"),
            "prompt": str(raw_trace.get("input", "")),
            "response": str(raw_trace.get("output", "")),
            "timestamp": raw_trace.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
