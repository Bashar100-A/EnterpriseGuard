import os
import json
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SIBBStorage:
    def __init__(self, storage_dir="sibb_vault", key=None):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        # توليد مفتاح AES-256 إذا لم يتم توفيره
        self.key = key or AESGCM.generate_key(bit_length=256)
        self.aesgcm = AESGCM(self.key)

    def write_record(self, record_id: str, data: dict) -> str:
        """كتابة سجّل جديد مع حظر إعادة الكتابة (مفهوم WORM)"""
        file_path = os.path.join(self.storage_dir, f"{record_id}.sibb")
        
        # حماية ضد التعديل أو التجاوز (WORM Enforcement)
        if os.path.exists(file_path):
            raise FileExistsError(f"انتهاك WORM: السجل {record_id} موجود مسبقاً ولا يمكن تعديله أو الكتابة فوقه.")

        raw_data = json.dumps(data, sort_keys=True).encode('utf-8')
        nonce = os.urandom(12)
        encrypted_data = self.aesgcm.encrypt(nonce, raw_data, None)
        record_hash = hashlib.sha256(raw_data).hexdigest()

        payload = {
            "record_id": record_id,
            "nonce": nonce.hex(),
            "data": encrypted_data.hex(),
            "hash": record_hash
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)

        return file_path

    def read_record(self, record_id: str) -> dict:
        """قراءة وفك تشفير السجل مع التحقق من السلامة"""
        file_path = os.path.join(self.storage_dir, f"{record_id}.sibb")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"السجل {record_id} غير موجود.")

        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        nonce = bytes.fromhex(payload["nonce"])
        encrypted_data = bytes.fromhex(payload["data"])
        
        decrypted_bytes = self.aesgcm.decrypt(nonce, encrypted_data, None)
        computed_hash = hashlib.sha256(decrypted_bytes).hexdigest()

        # التحقق من سلامة البيانات ضد التلاعب
        if computed_hash != payload["hash"]:
            raise ValueError("خطأ أمني: الهاش غير متطابق! هناك احتمال للتلاعب بالبيانات.")

        return json.loads(decrypted_bytes.decode('utf-8'))
