import sys, shutil, tempfile, os
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
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

file = ROOT / 'tools' / 'sovereign_http_server.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# إضافة دالة compliance_report داخل الفئة بعد serve_dashboard
marker = '    def log_message(self, format: str, *args: object) -> None:\n        return\n'
report_func = '''

    def serve_compliance_report(self):
        """Return a JSON compliance report based on current chain."""
        chain_data = load_json(INNOCENCE_CHAIN_PATH, None)
        if not isinstance(chain_data, dict):
            self._send_json(200, {"error": "chain unavailable"})
            return

        rings = chain_data.get("rings", [])
        if not isinstance(rings, list) or not rings:
            self._send_json(200, {"error": "no rings"})
            return

        last_ring = rings[-1]
        report = {
            "generated_at": utc_now_iso(),
            "chain_id": chain_data.get("chain_id") or last_ring.get("chain_id", "unknown"),
            "number_of_rings": len(rings),
            "last_ring_hash": last_ring.get("ring_hash", ""),
            "last_ring_created_at": last_ring.get("created_at", ""),
            "integrity_status": last_ring.get("integrity_status", "UNKNOWN"),
            "agent_events_hash": last_ring.get("agent_events_hash", ""),
            "realtime_events_hash": last_ring.get("realtime_events_hash", ""),
            "relational_memory_snapshot": last_ring.get("relational_memory_snapshot", ""),
            "tsa_provider": last_ring.get("tsa_provider", ""),
            "tsa_verified": last_ring.get("tsa_verified", False),
            "genesis_signature": last_ring.get("genesis_signature", "") if rings and "genesis_signature" in rings[0] else "",
            "verification_result": verify_chain()[0],
        }
        self._send_json(200, report)
'''
text = text.replace(marker, marker + '\n' + report_func, 1)

# إضافة المسار في do_GET بعد /verify-chain
old_block = '''        elif self.path == "/verify-chain":
            valid, reason = verify_chain()
            self._send_json(200, {"valid": valid, "reason": reason})'''
new_block = '''        elif self.path == "/verify-chain":
            valid, reason = verify_chain()
            self._send_json(200, {"valid": valid, "reason": reason})
        elif self.path == "/compliance-report":
            self.serve_compliance_report()'''
if old_block not in text:
    print("Old verify-chain block not found")
    sys.exit(1)
text = text.replace(old_block, new_block, 1)

atomic_write(file, text)
print("Successfully added /compliance-report endpoint")
