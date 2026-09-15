import re
import sys
import shutil
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True
ROOT = Path('.')

def backup_file(path):
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    b = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, b)
    return b

def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise

file = ROOT / 'tools' / 'innocence_chain.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# ===== 1. استبدال دالة get_rfc3161_timestamp بنسخة تدعم failover =====
old_func_pattern = r'def get_rfc3161_timestamp\(data: str\) -> str:.*?(?=\n\ndef |\n\Z)'
new_func = '''def get_rfc3161_timestamp(data: str):
    """Request RFC3161 timestamp from a pool of TSA providers, returning (token, provider)."""
    import subprocess
    import requests
    import base64
    from urllib.parse import urlparse

    # قراءة قائمة المزودين من متغير البيئة (مفصولة بفواصل) أو استخدام الافتراضية
    providers_str = os.environ.get("AAAC_TSA_URLS", "http://time.certum.pl,https://freetsa.org/tsr,https://zeitstempel.dfn.de")
    providers = [p.strip() for p in providers_str.split(",") if p.strip()]

    # توليد استعلام RFC3161 مرة واحدة
    try:
        query = subprocess.run(
            ["openssl", "ts", "-query", "-data", "-", "-sha256"],
            input=data.encode("utf-8"),
            capture_output=True,
            timeout=10,
            check=True,
        ).stdout
    except Exception as e:
        print(f"Failed to create TSA query: {e}", file=sys.stderr)
        return "", ""

    last_error = None
    for tsa_url in providers:
        try:
            headers = {"Content-Type": "application/timestamp-query"}
            resp = requests.post(tsa_url, data=query, headers=headers, timeout=15)
            if resp.status_code == 200:
                token_b64 = base64.b64encode(resp.content).decode("ascii")
                return token_b64, tsa_url
            else:
                last_error = f"status {resp.status_code}"
        except Exception as e:
            last_error = str(e)
            continue

    print(f"All TSA providers failed. Last error: {last_error}", file=sys.stderr)
    return "", ""
'''

if re.search(old_func_pattern, text, flags=re.DOTALL):
    text = re.sub(old_func_pattern, new_func, text, count=1, flags=re.DOTALL)
    print("تم استبدال دالة get_rfc3161_timestamp")
else:
    print("لم يتم العثور على دالة get_rfc3161_timestamp")
    sys.exit(1)

# ===== 2. تعديل استدعاء الدالة في generate_ring =====
# البحث عن السطر الحالي الذي يخصص rfc3161_token و tsa_provider
old_call = 'rfc3161_token = get_rfc3161_timestamp(agent_events_hash)\n    tsa_provider = os.environ.get(\'AAAC_TSA_URL\', \'http://time.certum.pl\')'
new_call = 'rfc3161_token, tsa_provider = get_rfc3161_timestamp(agent_events_hash)'

if old_call in text:
    text = text.replace(old_call, new_call, 1)
    print("تم تعديل استدعاء get_rfc3161_timestamp في generate_ring")
else:
    # fallback: محاولة استبدال جزء أبسط
    # ربما كان السطر مختلفاً، نبحث عن النمط العام
    pattern_call = r'rfc3161_token = get_rfc3161_timestamp\(agent_events_hash\)\n\s*tsa_provider = os\.environ\.get\([^\n]+\)'
    if re.search(pattern_call, text):
        text = re.sub(pattern_call, 'rfc3161_token, tsa_provider = get_rfc3161_timestamp(agent_events_hash)', text, count=1)
        print("تم تعديل الاستدعاء (fallback)")
    else:
        print("تعذر العثور على استدعاء get_rfc3161_timestamp، يرجى الفحص اليدوي")
        sys.exit(1)

atomic_write(file, text)
print("تم تحديث innocence_chain.py بنجاح")
