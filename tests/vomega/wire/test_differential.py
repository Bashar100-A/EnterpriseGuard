#!/usr/bin/env python3
"""ADIE differential tests: Python ↔ Rust (Phase 3, Gate 1, 3A.3).

Compares:
  - encode: same AdieValue -> same CBOR bytes
  - decode: same CBOR -> same AdieValue
  - negative: same invalid input -> same error code
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.wire import decode, encode
from protocol.wire.error import CborError
from protocol.wire.value import (
    AdieValue, Array, Bool, Bytes, Int, Map, Null, Text, UInt,
)

VECTORS = HERE / "differential_vectors.json"
RUST_BIN = ROOT / "rust" / "adie-primitives" / "target" / "release" / "adie-cbor"

PASS_N = FAIL_N = 0


def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"[PASS] {name}")
    else:
        FAIL_N += 1
        print(f"[FAIL] {name}: {detail}")


# ─── AdieValue ↔ JSON (matches Rust adie-cbor binary format) ───

def to_json(v: AdieValue):
    if isinstance(v, UInt):  return {"t": "uint",  "v": v.value}
    if isinstance(v, Int):   return {"t": "int",   "v": v.value}
    if isinstance(v, Bytes): return {"t": "bytes", "v": v.value.hex()}
    if isinstance(v, Text):  return {"t": "text",  "v": v.value}
    if isinstance(v, Bool):  return {"t": "bool",  "v": v.value}
    if isinstance(v, Null):  return {"t": "null"}
    if isinstance(v, Array):
        return {"t": "array", "v": [to_json(x) for x in v.value]}
    if isinstance(v, Map):
        return {"t": "map", "v": [[k, to_json(val)] for k, val in v.value]}
    raise ValueError(f"unknown AdieValue: {v!r}")


def from_json(o):
    t = o["t"]
    if t == "uint":  return UInt(o["v"])
    if t == "int":   return Int(o["v"])
    if t == "bytes": return Bytes(bytes.fromhex(o["v"]))
    if t == "text":  return Text(o["v"])
    if t == "bool":  return Bool(o["v"])
    if t == "null":  return Null()
    if t == "array": return Array(tuple(from_json(x) for x in o["v"]))
    if t == "map":
        return Map(tuple((k, from_json(val)) for k, val in o["v"]))
    raise ValueError(f"unknown type tag: {t}")


# ─── Rust invocation ───

def rust_call(payload):
    r = subprocess.run(
        [str(RUST_BIN)],
        input=json.dumps(payload),
        capture_output=True, text=True, timeout=20)
    try:
        out = json.loads(r.stdout.strip())
    except Exception:
        out = {"_raw": r.stdout[:200], "_err": r.stderr[:200]}
    return r.returncode, out


def py_encode(value_json):
    try:
        v = from_json(value_json)
        b = encode(v)
        return ("OK", b.hex())
    except CborError as e:
        return ("ERR", e.code)
    except Exception as e:
        return ("EXC", f"{type(e).__name__}: {e}")


def py_decode(cbor_hex):
    try:
        b = bytes.fromhex(cbor_hex)
        v = decode(b)
        return ("OK", to_json(v))
    except CborError as e:
        return ("ERR", e.code)
    except Exception as e:
        return ("EXC", f"{type(e).__name__}: {e}")


def rust_encode(value_json):
    rc, out = rust_call({"op": "encode", "value": value_json})
    if rc == 0 and "cbor_hex" in out:
        return ("OK", out["cbor_hex"])
    if "error" in out:
        return ("ERR", out["error"])
    return ("EXC", str(out)[:100])


def rust_decode(cbor_hex):
    rc, out = rust_call({"op": "decode", "cbor_hex": cbor_hex})
    if rc == 0 and "value" in out:
        return ("OK", out["value"])
    if "error" in out:
        return ("ERR", out["error"])
    return ("EXC", str(out)[:100])


# ─── Comparisons ───

def compare_encode(v):
    py = py_encode(v["value"])
    rs = rust_encode(v["value"])
    if py[0] != "OK":
        check(f"E {v['id']} py encode ok", False, f"py={py}")
        return
    if rs[0] != "OK":
        check(f"E {v['id']} rust encode ok", False, f"rs={rs}")
        return
    check(f"E {v['id']} positive parity",
          py[1] == rs[1],
          f"py={py[1][:40]} rs={rs[1][:40]}")


def compare_decode(v):
    py = py_decode(v["cbor_hex"])
    rs = rust_decode(v["cbor_hex"])
    check(f"D {v['id']} parity",
          py == rs,
          f"py={py} rs={rs}")


def compare_negative(v):
    py = py_decode(v["cbor_hex"])
    rs = rust_decode(v["cbor_hex"])
    check(f"N {v['id']} rejection parity",
          py == rs and py[0] == "ERR",
          f"py={py} rs={rs}")


def main():
    print("=" * 72)
    print("ADIE differential: Python ↔ Rust")
    print("=" * 72)
    data = json.loads(VECTORS.read_text())

    for v in data["encode_vectors"]:
        compare_encode(v)
    for v in data["decode_vectors"]:
        compare_decode(v)
    for v in data["negative_vectors"]:
        compare_negative(v)

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
