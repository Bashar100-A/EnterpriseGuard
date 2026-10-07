#!/usr/bin/env python3
"""protocol/wire/bin/adie-cbor.py — Python endpoint for differentials.

Protocol identical to rust/adie-primitives/src/bin/adie-cbor.rs.
"""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from protocol.wire import encode, decode
from protocol.wire.error import CborError
from protocol.wire.value import (
    AdieValue, Array, Bool, Bytes, Int, Map, Null, Text, UInt,
)

def to_json(v):
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

def emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")

def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw)
    except Exception as e:
        emit({"error": "E_JSON", "detail": str(e)}); return

    op = req.get("op")
    if op == "encode":
        try:
            v = from_json(req["value"])
            emit({"cbor_hex": encode(v).hex()})
        except CborError as e:
            emit({"error": e.code, "detail": str(e)})
    elif op == "decode":
        try:
            v = decode(bytes.fromhex(req["cbor_hex"]))
            emit({"value": to_json(v)})
        except CborError as e:
            emit({"error": e.code, "detail": str(e)})
    else:
        emit({"error": "E_OP", "detail": "unknown op"})

if __name__ == "__main__":
    main()
