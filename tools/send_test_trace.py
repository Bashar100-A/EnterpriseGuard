import os
import sys
from pathlib import Path
from langfuse import Langfuse

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
os.environ['LANGFUSE_SECRET_KEY'] = env.get('LANGFUSE_SECRET_KEY', '')
os.environ['LANGFUSE_PUBLIC_KEY'] = env.get('LANGFUSE_PUBLIC_KEY', '')
os.environ['LANGFUSE_BASE_URL'] = env.get('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')

client = Langfuse()

# إنشاء ملاحظة (observation) جديدة — هذه تنشئ تتبعًا ضمنيًا
obs = client.start_observation(
    name="test-agent-action",
    input={"message": "استدعاء وكيل ذكي"},
    output={"result": "تم تنفيذ الأمر"},
    metadata={"agent_id": "agent-123"},
)

# إنهاء الملاحظة وإرسالها
obs.end()
client.flush()
print("تم إرسال الملاحظة بنجاح")
