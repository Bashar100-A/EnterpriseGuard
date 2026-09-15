import re
import sys
import shutil
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True

# ==== المسار إلى الملف الأصلي ====
CHAIN_FILE = Path('tools/innocence_chain.py')

def backup_file(path: Path):
    """إنشاء نسخة احتياطية مؤرخة"""
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, backup)
    return backup

def modify_file():
    if not CHAIN_FILE.exists():
        print("الملف غير موجود!")
        return

    # قراءة المحتوى الحالي
    text = CHAIN_FILE.read_text(encoding='utf-8')

    # ===== 1. إضافة دالة get_last_agent_events_hash بعد get_last_realtime_event_hash =====
    # نبحث عن نهاية دالة get_last_realtime_event_hash (نفترض أنها تنتهي بعلامة return ثم سطر فارغ)
    # سنستخدم نمطًا: إدراج الدالة الجديدة بعد أول ظهور لتعريف get_last_realtime_event_hash وسطرها الأخير
    # لكن الأسهل: نبحث عن السطر الذي يبدأ بـ "def get_last_realtime_event_hash" ونتأكد من وجوده، ثم نضيف الدالة بعد نهاية هذه الدالة
    # سنستخدم طريقة: إدراج الدالة الجديدة مباشرة بعد السطر الذي يحتوي على "def get_last_realtime_event_hash():"
    # لكن يجب أن تكون بعد جسم الدالة بالكامل. لذا سنبحث عن أول سطر فارغ بعد هذا التعريف.
    # لتبسيط: سنستخدم تعبيرًا منتظمًا يجد نهاية الدالة (آخر return ثم سطر فارغ)
    pattern = r'(def get_last_realtime_event_hash\(\) -> str:.*?\n\n)'
    insertion = (
        "def get_last_agent_events_hash() -> str:\n"
        "    \"\"\"Compute SHA-256 of the last line in ring_storage.jsonl, or 'none' if missing/empty.\"\"\"\n"
        "    try:\n"
        "        agent_events_path = ROOT / \"tools\" / \"ring_storage.jsonl\"\n"
        "        if not agent_events_path.exists():\n"
        "            return \"none\"\n"
        "        last_line = None\n"
        "        with open(agent_events_path, 'r', encoding='utf-8') as f:\n"
        "            for line in f:\n"
        "                line = line.strip()\n"
        "                if line:\n"
        "                    last_line = line\n"
        "        if not last_line:\n"
        "            return \"none\"\n"
        "        return hashlib.sha256(last_line.encode('utf-8')).hexdigest()\n"
        "    except Exception:\n"
        "        return \"none\"\n"
        "\n"
        "\n"
    )
    # التأكد من وجود الدالة الأصلية
    if 'def get_last_realtime_event_hash' not in text:
        print("لم يتم العثور على get_last_realtime_event_hash")
        return
    # إدراج الدالة الجديدة بعد الدالة الأصلية مباشرة (نفترض أن الدالة الأصلية تنتهي بسطر فارغ)
    text = re.sub(pattern, lambda m: m.group(1) + insertion, text, count=1)

    # ===== 2. تعديل compute_ring_hash =====
    old_comp = '''def compute_ring_hash(prev_hash: str, identity_key: str,
                      integrity_status: str, snapshot: str,
                      realtime_events_hash: str = "none",
                      chain_id: str = "") -> str:
    """Compute ring hash with optional chain_id binding."""
    if not prev_hash:
        raise ValueError("prev_ring_hash cannot be empty")
    if not identity_key:
        raise ValueError("identity_key cannot be empty")
    if integrity_status not in {"PASS", "FAIL"}:
        raise ValueError("integrity_status must be PASS or FAIL")
    if not snapshot:
        raise ValueError("relational_memory_snapshot cannot be empty")
    if not realtime_events_hash:
        raise ValueError("realtime_events_hash cannot be empty")
    if chain_id is None:
        chain_id = ""

    combined = f"{prev_hash}{identity_key}{integrity_status}{snapshot}{realtime_events_hash}{chain_id}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()'''

    new_comp = '''def compute_ring_hash(prev_hash: str, identity_key: str,
                      integrity_status: str, snapshot: str,
                      realtime_events_hash: str = "none",
                      chain_id: str = "",
                      agent_events_hash: str = "none") -> str:
    """Compute ring hash with optional chain_id and agent events hash."""
    if not prev_hash:
        raise ValueError("prev_ring_hash cannot be empty")
    if not identity_key:
        raise ValueError("identity_key cannot be empty")
    if integrity_status not in {"PASS", "FAIL"}:
        raise ValueError("integrity_status must be PASS or FAIL")
    if not snapshot:
        raise ValueError("relational_memory_snapshot cannot be empty")
    if not realtime_events_hash:
        raise ValueError("realtime_events_hash cannot be empty")
    if chain_id is None:
        chain_id = ""
    if not agent_events_hash:
        raise ValueError("agent_events_hash cannot be empty")

    combined = f"{prev_hash}{identity_key}{integrity_status}{snapshot}{realtime_events_hash}{chain_id}{agent_events_hash}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()'''

    if old_comp not in text:
        print("لم يتم العثور على نص compute_ring_hash المطابق")
        return
    text = text.replace(old_comp, new_comp)

    # ===== 3. تعديل _verify_rings =====
    # إضافة قراءة agent_events_hash بعد realtime_events_hash
    old_verify_block = '''        ring_prev = ring.get("prev_ring_hash")
        ring_status = ring.get("integrity_status")
        ring_snapshot = ring.get("relational_memory_snapshot")
        ring_realtime_hash = ring.get("realtime_events_hash", "none")
        ring_signature = ring.get("signature")'''
    new_verify_block = '''        ring_prev = ring.get("prev_ring_hash")
        ring_status = ring.get("integrity_status")
        ring_snapshot = ring.get("relational_memory_snapshot")
        ring_realtime_hash = ring.get("realtime_events_hash", "none")
        ring_agent_events_hash = ring.get("agent_events_hash", "none")
        ring_signature = ring.get("signature")'''
    if old_verify_block not in text:
        print("لم يتم العثور على كتلة متغيرات التحقق")
        return
    text = text.replace(old_verify_block, new_verify_block, 1)

    # إضافة فحص نوع agent_events_hash بعد فحص realtime_events_hash
    old_check = '''        if not isinstance(ring_realtime_hash, str) or not ring_realtime_hash:
            return False'''
    new_check = '''        if not isinstance(ring_realtime_hash, str) or not ring_realtime_hash:
            return False
        if not isinstance(ring_agent_events_hash, str) or not ring_agent_events_hash:
            return False'''
    if old_check not in text:
        print("لم يتم العثور على فحص realtime_events_hash")
        return
    text = text.replace(old_check, new_check, 1)

    # تعديل استدعاء compute_ring_hash داخل _verify_rings
    old_call = '''            expected_hash = compute_ring_hash(
                ring_prev,
                identity_key,
                ring_status,
                ring_snapshot,
                ring_realtime_hash,
                chain_id,
            )'''
    new_call = '''            expected_hash = compute_ring_hash(
                ring_prev,
                identity_key,
                ring_status,
                ring_snapshot,
                ring_realtime_hash,
                chain_id,
                ring_agent_events_hash,
            )'''
    if old_call not in text:
        print("لم يتم العثور على استدعاء compute_ring_hash في _verify_rings")
        return
    text = text.replace(old_call, new_call, 1)

    # ===== 4. تعديل generate_ring =====
    # إضافة حساب agent_events_hash بعد realtime_events_hash
    old_gen = '''    realtime_events_hash = get_last_realtime_event_hash()
'''
    new_gen = '''    realtime_events_hash = get_last_realtime_event_hash()
    agent_events_hash = get_last_agent_events_hash()
'''
    if old_gen not in text:
        print("لم يتم العثور على سطر realtime_events_hash في generate_ring")
        return
    text = text.replace(old_gen, new_gen, 1)

    # تعديل استدعاء compute_ring_hash في generate_ring
    old_call2 = '''    ring_hash = compute_ring_hash(
        prev_hash, identity_key, integrity_status, snapshot,
        realtime_events_hash, chain_id
    )'''
    new_call2 = '''    ring_hash = compute_ring_hash(
        prev_hash, identity_key, integrity_status, snapshot,
        realtime_events_hash, chain_id, agent_events_hash
    )'''
    if old_call2 not in text:
        print("لم يتم العثور على استدعاء compute_ring_hash في generate_ring")
        return
    text = text.replace(old_call2, new_call2, 1)

    # تعديل بناء حلقة ring لإضافة agent_events_hash
    old_ring = '''    ring = {
        "ring_hash": ring_hash,
        "prev_ring_hash": prev_hash,
        "integrity_status": integrity_status,
        "relational_memory_snapshot": snapshot,
        "realtime_events_hash": realtime_events_hash,
        "signature": signature,
        "chain_id": chain_id,
        "created_at": utc_now_iso(),
    }'''
    new_ring = '''    ring = {
        "ring_hash": ring_hash,
        "prev_ring_hash": prev_hash,
        "integrity_status": integrity_status,
        "relational_memory_snapshot": snapshot,
        "realtime_events_hash": realtime_events_hash,
        "agent_events_hash": agent_events_hash,
        "signature": signature,
        "chain_id": chain_id,
        "created_at": utc_now_iso(),
    }'''
    if old_ring not in text:
        print("لم يتم العثور على بناء حلقة ring في generate_ring")
        return
    text = text.replace(old_ring, new_ring, 1)

    # ===== 5. حفظ الملف بعد التعديلات =====
    # إنشاء نسخة احتياطية
    backup = backup_file(CHAIN_FILE)
    print(f"تم إنشاء نسخة احتياطية: {backup}")

    # كتابة الملف المعدل
    with open(CHAIN_FILE, 'w', encoding='utf-8') as f:
        f.write(text)
    print("تم تعديل الملف بنجاح.")

if __name__ == "__main__":
    modify_file()
