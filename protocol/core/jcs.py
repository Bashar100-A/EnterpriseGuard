"""ADIE vΩ — strict JCS + I-JSON subset (Phase 1)."""
import json
import math
import unicodedata


class CanonicalError(Exception):
    pass


def strict_load(text: str):
    """Parse JSON, rejecting duplicate keys and non-I-JSON values."""
    dup = {"found": False}

    def hook(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                dup["found"] = True
                raise CanonicalError(f"duplicate key: {k!r}")
            seen.add(k)
        return dict(pairs)

    try:
        obj = json.loads(text, object_pairs_hook=hook,
                         parse_constant=lambda x: (_ for _ in ()).throw(
                             CanonicalError(f"non-I-JSON constant: {x}")))
    except CanonicalError:
        raise
    except json.JSONDecodeError as e:
        raise CanonicalError(f"malformed JSON: {e}")
    _validate_ijson(obj)
    return obj


def _validate_ijson(obj, path="root"):
    if obj is None or isinstance(obj, (bool, str)):
        if isinstance(obj, str):
            # NFC check
            if unicodedata.normalize("NFC", obj) != obj:
                raise CanonicalError(f"non-NFC string at {path}")
            for ch in obj:
                if ord(ch) < 0x20:
                    raise CanonicalError(f"control char at {path}")
        return
    if isinstance(obj, int) and not isinstance(obj, bool):
        if obj.bit_length() > 63:
            raise CanonicalError(f"int > 2^53 at {path}")
        return
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise CanonicalError(f"non-finite number at {path}")
        raise CanonicalError(f"float forbidden in I-JSON subset at {path}")
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            _validate_ijson(v, f"{path}[{i}]")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonicalError(f"non-string key at {path}")
            _validate_ijson(v, f"{path}.{k}")
        return
    raise CanonicalError(f"unexpected type {type(obj).__name__} at {path}")


def canonical_bytes(obj) -> bytes:
    """JCS subset: sort keys, no whitespace, UTF-8, no BOM."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def strict_canonicalize(text: str) -> bytes:
    obj = strict_load(text)
    return canonical_bytes(obj)
