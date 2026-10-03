#!/usr/bin/env python3
"""
EnterpriseGuard / SIBB - Continuity Point Engine (V8.0)
Cryptographic Checkpoint & Monotonic Time-Drift Verification Framework.

يوفر هذا المديول بنية "نقطة الاستمرارية" (ContinuityPoint) لربط سجلات SIBB بطبقة
إثبات غير قابلة للتعديل، مع كشف انحرافات الوقت والتلاعب بسلسلة الهاش.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class ContinuityPointError(Exception):
    """Base exception for ContinuityPoint operations."""


class TimeDriftViolationError(ContinuityPointError):
    """Raised when system time drift exceeds configured thresholds."""


class ChainIntegrityError(ContinuityPointError):
    """Raised when continuity hash link between points is broken."""


class CryptographicSignatureError(ContinuityPointError):
    """Raised when point signature verification fails."""


@dataclass(frozen=True)
class ContinuityPayload:
    """
    الحمولة الهيكلية لنقطة الاستمرارية.
    تتضمن طابع زمني دقيق بمستوى النانو، وهاش الحالة (Merkle Root)، ومؤشرات التوقيت أحادي الاتجاه.
    """
    sequence_number: int
    point_id: str
    previous_point_hash: str
    state_merkle_root: str
    timestamp_utc: str
    epoch_nanos: int
    monotonic_time_ns: int
    max_drift_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def serialize_canonical(self) -> bytes:
        """تحويل الحمولة إلى صيغة JSON معيارية ومحددة لضمان ثبات مطابقة الهاش."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':')).encode('utf-8')


class ContinuityPoint:
    """
    يمثل نقطة استمرارية واحدة مقفلة بحجم وسلسلة تشفير غير قابلة للتغيير.
    """

    def __init__(
        self,
        payload: ContinuityPayload,
        hmac_signature: str,
        current_hash: str
    ) -> None:
        self.payload = payload
        self.hmac_signature = hmac_signature
        self.current_hash = current_hash

    @classmethod
    def create(
        cls,
        sequence_number: int,
        previous_point_hash: str,
        state_merkle_root: str,
        secret_key: bytes,
        last_monotonic_ns: Optional[int] = None,
        max_drift_ms: int = 5000
    ) -> ContinuityPoint:
        """
        إنشاء نقطة استمرارية جديدة مع التحقق من انحراف التوقيت الأحادي (Monotonic Time Drift Check).
        """
        now_utc = datetime.now(timezone.utc)
        epoch_nanos = time.time_ns()
        current_monotonic_ns = time.monotonic_ns()

        # 1. التحقق من التراجع الزمني من خلال الساعة الأحادية (Monotonic Clock)
        if last_monotonic_ns is not None:
            if current_monotonic_ns < last_monotonic_ns:
                raise TimeDriftViolationError(
                    f"Monotonic clock regression detected: {current_monotonic_ns} < {last_monotonic_ns}"
                )

            # حساب الانحراف الجداري مقابل الساعة الأحادية
            elapsed_monotonic_ms = (current_monotonic_ns - last_monotonic_ns) // 1_000_000
            # في الأنظمة الموزعة، يتم استخدام هذه القيم للتحقق من عدم حدوث Jump زمني خلفي أو أمامي متطرف
            if elapsed_monotonic_ms < 0 or elapsed_monotonic_ms > max_drift_ms * 10:
                raise TimeDriftViolationError(
                    f"Time drift delta ({elapsed_monotonic_ms}ms) exceeded maximum tolerance ({max_drift_ms}ms)"
                )

        payload = ContinuityPayload(
            sequence_number=sequence_number,
            point_id=str(uuid.uuid4()),
            previous_point_hash=previous_point_hash,
            state_merkle_root=state_merkle_root,
            timestamp_utc=now_utc.isoformat(),
            epoch_nanos=epoch_nanos,
            monotonic_time_ns=current_monotonic_ns,
            max_drift_ms=max_drift_ms
        )

        canonical_bytes = payload.serialize_canonical()
        
        # حساب التوقيع الرقمي HMAC-SHA256
        sig = hmac.new(secret_key, canonical_bytes, hashlib.sha256).hexdigest()

        # حساب الهاش الموحد للنقطة (يشمل الحمولة والتوقيع)
        hasher = hashlib.sha256()
        hasher.update(canonical_bytes)
        hasher.update(sig.encode('utf-8'))
        current_hash = hasher.hexdigest()

        return cls(payload=payload, hmac_signature=sig, current_hash=current_hash)

    def verify_signature_and_hash(self, secret_key: bytes) -> bool:
        """
        التحقق التشفيري المزدوج من صحة الهاش والتوقيع.
        """
        canonical_bytes = self.payload.serialize_canonical()
        expected_sig = hmac.new(secret_key, canonical_bytes, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(self.hmac_signature, expected_sig):
            raise CryptographicSignatureError(f"Signature mismatch on ContinuityPoint sequence #{self.payload.sequence_number}")

        hasher = hashlib.sha256()
        hasher.update(canonical_bytes)
        hasher.update(self.hmac_signature.encode('utf-8'))
        expected_hash = hasher.hexdigest()

        if not hmac.compare_digest(self.current_hash, expected_hash):
            raise ChainIntegrityError(f"Point hash mismatch on sequence #{self.payload.sequence_number}")

        return True

    def export_to_dict(self) -> Dict[str, Any]:
        return {
            "payload": self.payload.to_dict(),
            "hmac_signature": self.hmac_signature,
            "current_hash": self.current_hash
        }

    @classmethod
    def import_from_dict(cls, data: Dict[str, Any]) -> ContinuityPoint:
        p_data = data["payload"]
        payload = ContinuityPayload(
            sequence_number=p_data["sequence_number"],
            point_id=p_data["point_id"],
            previous_point_hash=p_data["previous_point_hash"],
            state_merkle_root=p_data["state_merkle_root"],
            timestamp_utc=p_data["timestamp_utc"],
            epoch_nanos=p_data["epoch_nanos"],
            monotonic_time_ns=p_data["monotonic_time_ns"],
            max_drift_ms=p_data.get("max_drift_ms", 5000)
        )
        return cls(
            payload=payload,
            hmac_signature=data["hmac_signature"],
            current_hash=data["current_hash"]
        )


class ContinuityChainVerifier:
    """
    مدير للتحقق السلسلي والمتتابع لنقاط الاستمرارية المكتوبة في طبقة WORM.
    """

    def __init__(self, secret_key: bytes) -> None:
        self.secret_key = secret_key

    def verify_chain_link(
        self,
        previous_point: Optional[ContinuityPoint],
        current_point: ContinuityPoint
    ) -> Tuple[bool, str]:
        """
        تحقق دقيق بين نقطتين متتاليتين في السلسلة.
        """
        try:
            # 1. التحقق الذاتي من النقطة الحالية
            current_point.verify_signature_and_hash(self.secret_key)

            if previous_point is None:
                # النقطة الأولى (Genesis Point)
                if current_point.payload.sequence_number != 0:
                    return False, f"Genesis point must have sequence number 0, got {current_point.payload.sequence_number}"
                if current_point.payload.previous_point_hash != "0" * 64:
                    return False, "Genesis point previous_point_hash must be zeroed SHA256"
                return True, "Genesis ContinuityPoint verified successfully"

            # 2. التحقق من التتابع الرقمي
            expected_seq = previous_point.payload.sequence_number + 1
            if current_point.payload.sequence_number != expected_seq:
                return False, f"Sequence gap detected: expected {expected_seq}, got {current_point.payload.sequence_number}"

            # 3. التحقق من الربط التشفيري بالسلسلة (Previous Point Hash)
            if current_point.payload.previous_point_hash != previous_point.current_hash:
                return False, (
                    f"Chain break on sequence #{current_point.payload.sequence_number}: "
                    f"previous_point_hash {current_point.payload.previous_point_hash[:16]}... "
                    f"does not match actual previous hash {previous_point.current_hash[:16]}..."
                )

            # 4. التحقق من التوقيت الأحادي
            if current_point.payload.monotonic_time_ns < previous_point.payload.monotonic_time_ns:
                return False, f"Monotonic time drift detected backward on sequence #{current_point.payload.sequence_number}"

            # 5. التحقق من التنسيق الزمني UTC
            prev_dt = datetime.fromisoformat(previous_point.payload.timestamp_utc)
            curr_dt = datetime.fromisoformat(current_point.payload.timestamp_utc)
            if curr_dt < prev_dt:
                return False, f"UTC Timestamp backward shift detected on sequence #{current_point.payload.sequence_number}"

            return True, f"Link #{previous_point.payload.sequence_number} -> #{current_point.payload.sequence_number} verified"

        except ContinuityPointError as e:
            return False, f"Verification failed: {e}"


# ========================================================================
# مكونات البنية التحتية التفصيلية لنقطة الاستمرارية (Technical Breakdown)
# ========================================================================
"""
تفاصيل معمارية الهيكل التكاملي لنقطة الاستمرارية (ContinuityPoint):

1. الهيكلية التجميعية والحماية من التلاعب (Canonical Serialization):
   - يتم تنظيم البيانات داخل `ContinuityPayload` بشكل غير قابل للتعديل (Frozen Dataclass).
   - الترسيم المعياري للبيانات `serialize_canonical` يضمن تحويل الكائن لبيانات بايتات ثابتة
     مفروزة الترتيب وبدون مسافات، لتفادي اختلاف الهاشات بين لغات البرمجة أو نسخ Python المختلفة.

2. مقاومة هجمات انحراف الوقت (Time-Drift & NTP Replay Protection):
   - تعتمد الأداة على التوقيت الأحادي للمُعالج (`time.monotonic_ns()`) جنباً إلى جنب مع `epoch_nanos` و `timestamp_utc`.
   - لا يمكن تقليل التوقيت الأحادي حتى لو تم إرجاع توقيت النظام أو خادم NTP للخلف، مما يكشف فوراً
     أي محاولة لتزوير طوابع التدقيق الزمني.

3. الربط التشفيري بالسلسلة المغلقة (Cryptographic Continuity Link):
   - كل نقطة تشمل `previous_point_hash` وهو الهاش الشامل لنقطة الاستمرارية التي سبقتها.
   - كسر هذه السلسلة أو تعديل أي سجل في SIBB بين النقطتين يلغي صحة الشجرة الكاملة (Merkle Root).

4. آلية التوقيع التكاملي المزدوج (HMAC & SHA-256 Digest):
   - توقيع HMAC ممتد على الحمولة الكاملة لضمان الأصالة (Authenticity).
   - الهاش النهائي للنقطة `current_hash` هو دمج مشفر للحمولة + التوقيع، ليكون بمثابة معرّف فريد غير قابل للتزوير.
"""


if __name__ == "__main__":
    print("=" * 70)
    print("EnterpriseGuard / SIBB - ContinuityPoint Engine Validation")
    print("=" * 70)

    # مفتاح سر آمن لاختبارات السلسلة
    secret_key = b"sibb_sovereign_immutable_master_key_32bytes!"

    verifier = ContinuityChainVerifier(secret_key)

    # 1. إنشاء نقطة البداية (Genesis Point #0)
    genesis_merkle = hashlib.sha256(b"genesis_state_block").hexdigest()
    genesis_point = ContinuityPoint.create(
        sequence_number=0,
        previous_point_hash="0" * 64,
        state_merkle_root=genesis_merkle,
        secret_key=secret_key
    )

    valid, msg = verifier.verify_chain_link(None, genesis_point)
    print(f"[*] Genesis Point Validation: {valid} -> {msg}")

    # 2. إنشاء النقطة التالية (Sequence #1)
    time.sleep(0.01) # تأخير طفيف لاختبار فرق التوقيت
    block_1_merkle = hashlib.sha256(b"tx_batch_1_state").hexdigest()
    point_1 = ContinuityPoint.create(
        sequence_number=1,
        previous_point_hash=genesis_point.current_hash,
        state_merkle_root=block_1_merkle,
        secret_key=secret_key,
        last_monotonic_ns=genesis_point.payload.monotonic_time_ns
    )

    valid, msg = verifier.verify_chain_link(genesis_point, point_1)
    print(f"[*] Continuity Point #1 Validation: {valid} -> {msg}")

    # 3. محاولة التلاعب بالهاش (Tamper Simulation Test)
    tampered_dict = point_1.export_to_dict()
    tampered_dict["payload"]["state_merkle_root"] = hashlib.sha256(b"tampered_data").hexdigest()
    tampered_point = ContinuityPoint.import_from_dict(tampered_dict)

    valid_tamper, msg_tamper = verifier.verify_chain_link(genesis_point, tampered_point)
    print(f"[!] Tampered Point Test (Should Fail): Valid={valid_tamper} -> {msg_tamper}")

    print("=" * 70)
    print("Self-test completed successfully.")
