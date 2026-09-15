import os
import sys
import json
import base64
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.dont_write_bytecode = True

def load_env(env_path=Path('.env')):
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env

env = load_env()
PUBLIC_KEY = env.get('LANGFUSE_PUBLIC_KEY')
SECRET_KEY = env.get('LANGFUSE_SECRET_KEY')
BASE_URL = env.get('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')

RING_STORAGE_PATH = Path('tools/ring_storage.jsonl')

def get_headers():
    auth = base64.b64encode(f"{PUBLIC_KEY}:{SECRET_KEY}".encode()).decode()
    return {"Authorization": f"Basic {auth}"}

def fetch_observations(limit=10):
    """جلب الملاحظات من Langfuse v2 API خلال آخر 24 ساعة"""
    headers = get_headers()
    to_time = datetime.now(timezone.utc)
    from_time = to_time - timedelta(hours=24)
    params = {
        "fromStartTime": from_time.isoformat(),
        "toStartTime": to_time.isoformat(),
        "limit": limit,
    }
    url = f"{BASE_URL}/api/public/v2/observations"
    resp = requests.get(url, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])

def fetch_trace(trace_id):
    """جلب تفاصيل التتبع من Langfuse v1 trace endpoint"""
    headers = get_headers()
    url = f"{BASE_URL}/api/public/traces/{trace_id}"
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code == 200:
        return resp.json()
    return {}

def sanitize(text):
    if not isinstance(text, str):
        return ""
    for key in ["api_key", "password", "secret", "token"]:
        text = text.replace(key, "***")
    return text[:200]

def normalize_observation(obs, trace_data=None):
    """تحويل observation إلى حدث موحد مع دمج بيانات التتبع"""
    if trace_data is None:
        trace_data = {}
    metadata = trace_data.get("metadata", {}) or {}
    return {
        "timestamp": obs.get("startTime", ""),
        "agent_id": metadata.get("agent_id", "unknown"),
        "trace_id": obs.get("traceId", ""),
        "run_id": obs.get("id", ""),
        "command": obs.get("name", ""),
        "actor_type": "agent",
        "input_summary": sanitize(str(trace_data.get("input", ""))),
        "output_summary": sanitize(str(trace_data.get("output", ""))),
        "latency_ms": obs.get("latency", 0),
    }



def load_existing_trace_ids():
    """Return set of trace_ids already stored in ring_storage.jsonl."""
    ids = set()
    if RING_STORAGE_PATH.exists():
        try:
            with open(RING_STORAGE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            tid = event.get('trace_id')
                            if tid:
                                ids.add(tid)
                        except json.JSONDecodeError:
                            continue
        except OSError:
            pass
    return ids

def save_event_to_ring_storage(event: dict):
    """إضافة حدث إلى ring_storage.jsonl بطريقة آمنة"""
    # تأكد من وجود المجلد
    RING_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # كتابة JSONL مع fsync
    with open(RING_STORAGE_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
        f.flush()
        os.fsync(f.fileno())

if __name__ == "__main__":
    print("جلب الملاحظات من Langfuse v2...")
    observations = fetch_observations(limit=10)
    print(f"تم جلب {len(observations)} ملاحظة")

    existing_ids = load_existing_trace_ids()
    normalized_events = []
    for obs in observations:
        trace_id = obs.get("traceId", "")
        if trace_id in existing_ids:
            print(f"Skipping duplicate trace_id: {trace_id}")
            continue
        trace_data = fetch_trace(trace_id) if trace_id else {}
        event = normalize_observation(obs, trace_data)
        normalized_events.append(event)

    if normalized_events:
        # حفظ الأحداث
        for event in normalized_events:
            save_event_to_ring_storage(event)
        print(f"تم حفظ {len(normalized_events)} حدث في {RING_STORAGE_PATH}")
        print("مثال على حدث موحد:")
        print(json.dumps(normalized_events[0], indent=2, ensure_ascii=False))
    else:
        print("لا توجد ملاحظات حديثة.")
