#!/usr/bin/env python3
"""B+ envelope endpoint — Python adapter."""
import sys, json, base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from protocol.wire import encode, decode
from protocol.wire.error import CborError as WireCborError
from protocol.wire.value import Array, Bytes, Map, Text, UInt
from protocol.core.jcs import canonical_bytes

NESTED = [
    ("issuer", 3), ("subject", 4), ("request", 5), ("context", 6),
    ("policy", 7), ("model", 8), ("data", 9), ("runtime", 10),
    ("output", 11), ("binding", 12), ("temporal", 13),
    ("evidence", 14), ("authoring", 15),
]


def build_envelope(cert_json_str):
    cert = json.loads(cert_json_str)
    entries = [
        (1, Text(cert["dcp_version"])),
        (2, Text(cert["claim_id"])),
    ]
    for name, lbl in NESTED:
        if name not in cert or not isinstance(cert[name], dict):
            raise ValueError("envelope: {} must be object".format(name))
        jcs = canonical_bytes(cert[name])
        entries.append((lbl, Bytes(jcs)))
    proofs = cert.get("proofs", [])
    if proofs != []:
        raise ValueError("envelope: non-empty proofs reserved")
    entries.append((16, Array(())))
    cr = cert["claim_root"]
    if not cr.startswith("sha256:"):
        raise ValueError("envelope: claim_root must start sha256:")
    raw_cr = bytes.fromhex(cr[7:])
    if len(raw_cr) != 32:
        raise ValueError("envelope: claim_root must be 32 bytes")
    entries.append((17, Bytes(raw_cr)))
    sig_objs = []
    for s in cert["signatures"]:
        v = s["value"]
        if not v.startswith("base64:"):
            raise ValueError("envelope: sig.value must start base64:")
        raw_sig = base64.b64decode(v[7:])
        sig_objs.append(Map((
            (1, Text(s["alg"])),
            (2, Text(s["key_id"])),
            (3, Bytes(raw_sig)),
        )))
    entries.append((18, Array(tuple(sig_objs))))
    return encode(Map(tuple(entries)))


def parse_envelope(data):
    val = decode(data)
    if not isinstance(val, Map):
        raise ValueError("envelope: top-level must be map")
    cert = {}
    seen = set()
    sigs_out = None
    for k, v in val.value:
        if k in seen:
            raise ValueError("envelope: duplicate label {}".format(k))
        seen.add(k)
        if k == 1:
            if not isinstance(v, Text): raise ValueError("dcp_version must be text")
            cert["dcp_version"] = v.value
        elif k == 2:
            if not isinstance(v, Text): raise ValueError("claim_id must be text")
            cert["claim_id"] = v.value
        elif 3 <= k <= 15:
            name = next(n for n, l in NESTED if l == k)
            if not isinstance(v, Bytes): raise ValueError("{} must be bstr".format(name))
            raw = v.value
            raw.decode("utf-8")
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                raise ValueError("{} must be JSON object".format(name))
            re = canonical_bytes(obj)
            if re != raw:
                raise ValueError("{} JCS non-canonical".format(name))
            cert[name] = obj
        elif k == 16:
            if not isinstance(v, Array): raise ValueError("proofs must be array")
            if len(v.value) != 0: raise ValueError("non-empty proofs reserved")
            cert["proofs"] = []
        elif k == 17:
            if not isinstance(v, Bytes): raise ValueError("claim_root must be bstr")
            if len(v.value) != 32: raise ValueError("claim_root must be 32 bytes")
            cert["claim_root"] = "sha256:" + v.value.hex()
        elif k == 18:
            if not isinstance(v, Array): raise ValueError("signatures must be array")
            out = []
            for so in v.value:
                if not isinstance(so, Map): raise ValueError("sig must be map")
                alg = kid = raw_sig = None
                for sl, sv in so.value:
                    if sl == 1:
                        if not isinstance(sv, Text): raise ValueError("sig.alg must be text")
                        alg = sv.value
                    elif sl == 2:
                        if not isinstance(sv, Text): raise ValueError("sig.key_id must be text")
                        kid = sv.value
                    elif sl == 3:
                        if not isinstance(sv, Bytes): raise ValueError("sig.value must be bstr")
                        raw_sig = sv.value
                    else:
                        raise ValueError("sig: unknown label {}".format(sl))
                out.append({
                    "alg": alg, "key_id": kid,
                    "value": "base64:" + base64.b64encode(raw_sig).decode("ascii"),
                })
            sigs_out = out
        else:
            raise ValueError("envelope: unknown label {}".format(k))
    for req in ["dcp_version","claim_id","issuer","subject","request","context",
                "policy","model","data","runtime","output","binding",
                "temporal","evidence","authoring","proofs","claim_root"]:
        if req not in cert:
            raise ValueError("envelope: missing {}".format(req))
    if sigs_out is None:
        raise ValueError("envelope: missing signatures")
    cert["signatures"] = sigs_out
    return json.dumps(cert, sort_keys=True, separators=(",", ":"))


def main():
    try:
        req = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"error": "E-JSON", "detail": str(e)}))
        return
    op = req.get("op")
    if op == "build":
        try:
            env = build_envelope(req["certificate_json"])
            print(json.dumps({"envelope_hex": env.hex()}))
        except Exception as e:
            print(json.dumps({"error": "BUILD-FAIL", "detail": str(e)}))
    elif op == "parse":
        try:
            data = bytes.fromhex(req["envelope_hex"])
            print(json.dumps({"certificate_json": parse_envelope(data)}))
        except Exception as e:
            print(json.dumps({"error": "PARSE-FAIL", "detail": str(e)}))
    elif op == "parse_batch":
        arr = req.get("envelopes_hex", [])
        results = []
        for hx in arr:
            try:
                data = bytes.fromhex(hx)
                try:
                    results.append({"certificate_json": parse_envelope(data)})
                except WireCborError as e:
                    results.append({"error": e.code, "detail": str(e)})
                except Exception as e:
                    results.append({"error": "E_WIRE_MALFORMED", "detail": str(e)})
            except Exception as e:
                results.append({"error": "E_WIRE_MALFORMED", "detail": str(e)})
        print(json.dumps({"results": results}))
    else:
        print(json.dumps({"error": "E-OP"}))


if __name__ == "__main__":
    main()
