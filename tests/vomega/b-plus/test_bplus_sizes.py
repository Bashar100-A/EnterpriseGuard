#!/usr/bin/env python3
"""B+ wire size baseline (Phase I)."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BIN = ROOT / "rust/adie-primitives/target/release/adie-cbor-envelope"

corpus = json.loads((ROOT / "tests/vomega/b-plus/corpus.json").read_text())

def r_call(p):
    r = subprocess.run([str(BIN)], input=json.dumps(p), capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

print("=" * 72)
print("B+ wire size baseline")
print("=" * 72)
print()
print(f"{'ID':<6} {'JSON':>8} {'JCS-sum':>9} {'env':>8} {'delta':>8}")
print("-" * 45)

totals = {"json":0,"jcs":0,"env":0}
for v in corpus["positive"]:
    cert = v["certificate"]
    json_bytes = len(json.dumps(cert, sort_keys=True, separators=(",",":")).encode())
    jcs_sum = sum(len(bytes.fromhex(h)) for h in v["nested_jcs_hex"].values())
    r = r_call({"op":"build","certificate_json":json.dumps(cert)})
    env_bytes = len(bytes.fromhex(r["envelope_hex"]))
    totals["json"] += json_bytes
    totals["jcs"] += jcs_sum
    totals["env"] += env_bytes
    print(f"{v['id']:<6} {json_bytes:>8} {jcs_sum:>9} {env_bytes:>8} {env_bytes-json_bytes:>+8}")

n = len(corpus["positive"])
print("-" * 45)
print(f"{'avg':<6} {totals['json']//n:>8} {totals['jcs']//n:>9} {totals['env']//n:>8} {(totals['env']-totals['json'])//n:>+8}")
print()
print("Rough breakdown (P01):")
v = corpus["positive"][0]
cert = v["certificate"]
json_bytes = len(json.dumps(cert, sort_keys=True, separators=(",",":")).encode())
jcs_sum = sum(len(bytes.fromhex(h)) for h in v["nested_jcs_hex"].values())
sig_bytes_total = 0
import base64
for s in cert["signatures"]:
    sig_bytes_total += len(base64.b64decode(s["value"][7:]))
r = r_call({"op":"build","certificate_json":json.dumps(cert)})
env_bytes = len(bytes.fromhex(r["envelope_hex"]))
print(f"  full JSON cert:     {json_bytes:>6} bytes")
print(f"  sum of JCS fields:  {jcs_sum:>6} bytes")
print(f"  raw signature sum:  {sig_bytes_total:>6} bytes")
print(f"  B+ envelope:        {env_bytes:>6} bytes")
print(f"  overhead vs JSON:   {env_bytes-json_bytes:>+6} bytes")
print()
print("Note: signatures are the dominant cost (~3565 bytes raw).")
print("Envelope adds CBOR header overhead and carries raw signature bytes.")
