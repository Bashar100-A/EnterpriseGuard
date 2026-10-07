#!/usr/bin/env python3
"""B+ differential fuzzer (Stage 3A.6)."""
import json, subprocess, sys, time, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUST = ROOT / "rust/adie-primitives/target/release/adie-cbor-envelope"
PY_BIN = ROOT / ".venv/bin/python"
PY_S = ROOT / "protocol/wire/bin/adie-cbor-envelope.py"
JS_S = ROOT / "js/wire/bin/adie-cbor-envelope.mjs"

N_CASES = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
CHUNK = 500
SEED = 0xC0FFEE

corpus = json.loads((ROOT / "tests/vomega/b-plus/corpus_v2.json").read_text())
print("corpus_v2: %d vectors" % len(corpus["positive"]))

BASE = []
for v in corpus["positive"]:
    r = subprocess.run([str(RUST)],
                       input=json.dumps({"op":"build","certificate_json":json.dumps(v["certificate"])}),
                       capture_output=True, text=True, timeout=30)
    out = json.loads(r.stdout)
    if "envelope_hex" not in out:
        print("build failed: %s" % out); sys.exit(1)
    BASE.append(out["envelope_hex"])
print("built %d base envelopes" % len(BASE))

def m_delete(h, rng):
    b = bytearray.fromhex(h)
    if len(b) < 3: return h
    del b[rng.randrange(len(b))]; return b.hex()
def m_insert(h, rng):
    b = bytearray.fromhex(h)
    b.insert(rng.randrange(len(b)+1), rng.randrange(256)); return b.hex()
def m_flip(h, rng):
    b = bytearray.fromhex(h)
    b[rng.randrange(len(b))] ^= (1 << rng.randrange(8)); return b.hex()
def m_trailing(h, rng):
    return h + rng.choice([b"\x00", b"\xff", b"\xc1\x01",
                           b"\xfb\x3f\xf0\x00\x00\x00\x00\x00\x00",
                           b"\x00\x00\x00\x00"]).hex()
def m_truncate(h, rng):
    b = bytearray.fromhex(h); return bytes(b[:rng.randrange(1, len(b))]).hex()
def m_tag(h, rng):
    b = bytearray.fromhex(h); pos = rng.randrange(1, len(b))
    b[pos:pos] = b"\xc1"; return bytes(b).hex()
def m_float(h, rng):
    b = bytearray.fromhex(h); pos = rng.randrange(1, len(b))
    b[pos:pos] = b"\xfb\x3f\xf0\x00\x00\x00\x00\x00\x00"; return bytes(b).hex()
def m_indef(h, rng):
    b = bytearray.fromhex(h); pos = rng.randrange(1, len(b))
    b[pos:pos] = b"\x9f"; return bytes(b).hex()
def m_zero_run(h, rng):
    b = bytearray.fromhex(h)
    if len(b) < 20: return h
    pos = rng.randrange(len(b) - 16)
    b[pos:pos+16] = b"\x00" * 16; return bytes(b).hex()

MUTS = [("delete",m_delete),("insert",m_insert),("flip",m_flip),
        ("trailing",m_trailing),("truncate",m_truncate),("tag",m_tag),
        ("float",m_float),("indef",m_indef),("zero_run",m_zero_run)]

rng = random.Random(SEED)
print("generating %d cases..." % N_CASES)
t0 = time.time()
cases = []
for i in range(N_CASES):
    base = BASE[i % len(BASE)]
    name, fn = MUTS[i % len(MUTS)]
    try: mut = fn(base, rng)
    except Exception: mut = base
    cases.append((i, name, mut))
print("generated in %.1fs" % (time.time()-t0))

def call(cmd_args, hexes, timeout=180):
    try:
        r = subprocess.run(cmd_args,
            input=json.dumps({"op":"parse_batch","envelopes_hex":hexes}),
            capture_output=True, text=True, timeout=timeout,
            cwd=str(ROOT))
        return json.loads(r.stdout)["results"]
    except subprocess.TimeoutExpired:
        return [{"error":"TIMEOUT"}] * len(hexes)
    except Exception as e:
        return [{"error":"CHUNK-FAIL","detail":str(e)}] * len(hexes)

results = {"rust": [], "py": [], "js": []}
n_chunks = (len(cases) + CHUNK - 1) // CHUNK
print("running %d chunks of %d..." % (n_chunks, CHUNK))
t0 = time.time()
for ci in range(n_chunks):
    chunk = [c[2] for c in cases[ci*CHUNK:(ci+1)*CHUNK]]
    results["rust"].extend(call([str(RUST)], chunk))
    results["py"].extend(call([str(PY_BIN), str(PY_S)], chunk))
    results["js"].extend(call(["node", str(JS_S)], chunk))
    if (ci+1) % 5 == 0:
        print("  %d/%d chunks (%.1fs)" % (ci+1, n_chunks, time.time()-t0))

def acc(r): return "certificate_json" in r
acc_mismatch = 0
ar=ap=aj=0
for i in range(len(cases)):
    rr=results["rust"][i]; pr=results["py"][i]; jr=results["js"][i]
    if acc(rr): ar+=1
    if acc(pr): ap+=1
    if acc(jr): aj+=1
    if not (acc(rr)==acc(pr)==acc(jr)):
        acc_mismatch += 1
        if acc_mismatch <= 5:
            print("  ACC MISMATCH case=%d mut=%s R=%s P=%s J=%s" %
                  (i, cases[i][1], acc(rr), acc(pr), acc(jr)))

print()
print("total cases:         %d" % len(cases))
print("Rust accepted:       %d" % ar)
print("Python accepted:     %d" % ap)
print("JS accepted:         %d" % aj)
print("acceptance mismatch: %d" % acc_mismatch)

code_mismatch = 0
code_samples = []
for i in range(len(cases)):
    rr=results["rust"][i]; pr=results["py"][i]; jr=results["js"][i]
    if acc(rr) or acc(pr) or acc(jr): continue
    re=rr.get("error","?"); pe=pr.get("error","?"); je=jr.get("error","?")
    if re != pe or re != je:
        code_mismatch += 1
        if len(code_samples) < 5:
            code_samples.append((i, cases[i][1], re, pe, je))

print("rejection code mismatch: %d" % code_mismatch)
for i,mut,re,pe,je in code_samples:
    print("  case=%d mut=%s: Rust=%s Py=%s JS=%s" % (i,mut,re,pe,je))
print()
print("elapsed: %.1fs" % (time.time()-t0))
sys.exit(0 if acc_mismatch == 0 else 1)
