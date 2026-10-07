#!/usr/bin/env node
// B+ envelope endpoint — JavaScript adapter.
import { readFileSync } from 'node:fs';
import * as W from '../index.mjs';

const NESTED = [
  ['issuer', 3], ['subject', 4], ['request', 5], ['context', 6],
  ['policy', 7], ['model', 8], ['data', 9], ['runtime', 10],
  ['output', 11], ['binding', 12], ['temporal', 13],
  ['evidence', 14], ['authoring', 15],
];

// RFC 8785 JCS — serialize object with sorted keys, no whitespace.
function jcs(obj) {
  if (obj === null) return 'null';
  if (typeof obj === 'boolean') return obj ? 'true' : 'false';
  if (typeof obj === 'number') {
    if (!Number.isFinite(obj)) throw new Error('JCS: non-finite number');
    if (!Number.isInteger(obj)) {
      // JCS: use shortest roundtrip representation (ECMAScript Number.toString)
      return JSON.stringify(obj);
    }
    return String(obj);
  }
  if (typeof obj === 'string') return JSON.stringify(obj);
  if (Array.isArray(obj)) {
    return '[' + obj.map(jcs).join(',') + ']';
  }
  if (typeof obj === 'object') {
    const keys = Object.keys(obj).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + jcs(obj[k])).join(',') + '}';
  }
  throw new Error('JCS: unsupported type ' + typeof obj);
}

function buildEnvelope(certJsonStr) {
  const cert = JSON.parse(certJsonStr);
  const entries = [];
  entries.push([1, W.text(cert.dcp_version)]);
  entries.push([2, W.text(cert.claim_id)]);
  for (const [name, lbl] of NESTED) {
    const field = cert[name];
    if (!field || typeof field !== 'object' || Array.isArray(field)) {
      throw new Error(`envelope: ${name} must be object`);
    }
    const jcsStr = jcs(field);
    const jcsBytes = Buffer.from(jcsStr, 'utf8');
    entries.push([lbl, W.bytes(jcsBytes)]);
  }
  const proofs = cert.proofs || [];
  if (!Array.isArray(proofs) || proofs.length !== 0) {
    throw new Error('envelope: non-empty proofs reserved');
  }
  entries.push([16, W.array([])]);
  const cr = cert.claim_root;
  if (!cr.startsWith('sha256:')) throw new Error('envelope: claim_root must start sha256:');
  const rawCr = Buffer.from(cr.slice(7), 'hex');
  if (rawCr.length !== 32) throw new Error('envelope: claim_root must be 32 bytes');
  entries.push([17, W.bytes(rawCr)]);
  const sigObjs = [];
  for (const s of cert.signatures) {
    const v = s.value;
    if (!v.startsWith('base64:')) throw new Error('envelope: sig.value must start base64:');
    const rawSig = Buffer.from(v.slice(7), 'base64');
    sigObjs.push(W.map([
      [1, W.text(s.alg)],
      [2, W.text(s.key_id)],
      [3, W.bytes(rawSig)],
    ]));
  }
  entries.push([18, W.array(sigObjs)]);
  return Buffer.from(W.encode(W.map(entries)));
}

function parseEnvelope(data) {
  const val = W.decode(Buffer.from(data));
  if (val.t !== 'map') throw new Error('envelope: top-level must be map');
  const cert = {};
  const seen = new Set();
  let sigsOut = null;
  for (const [k, v] of val.v) {
    const kn = Number(k);
    if (seen.has(kn)) throw new Error(`envelope: duplicate label ${kn}`);
    seen.add(kn);
    if (kn === 1) {
      if (v.t !== 'text') throw new Error('dcp_version must be text');
      cert.dcp_version = v.v;
    } else if (kn === 2) {
      if (v.t !== 'text') throw new Error('claim_id must be text');
      cert.claim_id = v.v;
    } else if (kn >= 3 && kn <= 15) {
      const name = NESTED.find(([_, l]) => l === kn)[0];
      if (v.t !== 'bytes') throw new Error(`${name} must be bstr`);
      const raw = Buffer.from(v.v, 'hex');
      const str = raw.toString('utf8');
      if (Buffer.from(str, 'utf8').compare(raw) !== 0) {
        throw new Error(`${name} not UTF-8`);
      }
      let obj;
      try { obj = JSON.parse(str); } catch (e) { throw new Error(`${name} not JSON`); }
      if (!obj || typeof obj !== 'object' || Array.isArray(obj)) {
        throw new Error(`${name} must be JSON object`);
      }
      const re = Buffer.from(jcs(obj), 'utf8');
      if (re.compare(raw) !== 0) throw new Error(`${name} JCS non-canonical`);
      cert[name] = obj;
    } else if (kn === 16) {
      if (v.t !== 'array') throw new Error('proofs must be array');
      if (v.v.length !== 0) throw new Error('non-empty proofs reserved');
      cert.proofs = [];
    } else if (kn === 17) {
      if (v.t !== 'bytes') throw new Error('claim_root must be bstr');
      const raw = Buffer.from(v.v, 'hex');
      if (raw.length !== 32) throw new Error('claim_root must be 32 bytes');
      cert.claim_root = 'sha256:' + raw.toString('hex');
    } else if (kn === 18) {
      if (v.t !== 'array') throw new Error('signatures must be array');
      const out = [];
      for (const so of v.v) {
        if (so.t !== 'map') throw new Error('sig must be map');
        let alg = null, kid = null, rawSig = null;
        for (const [sl, sv] of so.v) {
          const sln = Number(sl);
          if (sln === 1) {
            if (sv.t !== 'text') throw new Error('sig.alg must be text');
            alg = sv.v;
          } else if (sln === 2) {
            if (sv.t !== 'text') throw new Error('sig.key_id must be text');
            kid = sv.v;
          } else if (sln === 3) {
            if (sv.t !== 'bytes') throw new Error('sig.value must be bstr');
            rawSig = Buffer.from(sv.v, 'hex');
          } else {
            throw new Error(`sig: unknown label ${sln}`);
          }
        }
        out.push({
          alg, key_id: kid,
          value: 'base64:' + rawSig.toString('base64'),
        });
      }
      sigsOut = out;
    } else {
      throw new Error(`envelope: unknown label ${kn}`);
    }
  }
  const required = ['dcp_version','claim_id','issuer','subject','request','context',
                    'policy','model','data','runtime','output','binding',
                    'temporal','evidence','authoring','proofs','claim_root'];
  for (const req of required) {
    if (!(req in cert)) throw new Error(`envelope: missing ${req}`);
  }
  if (!sigsOut) throw new Error('envelope: missing signatures');
  cert.signatures = sigsOut;
  const keys = Object.keys(cert).sort();
  const sorted = {};
  for (const k of keys) sorted[k] = cert[k];
  return JSON.stringify(sorted);
}

// ─── main ───
let raw;
try { raw = readFileSync(0, 'utf8'); } catch (e) {
  process.stdout.write(JSON.stringify({error:'E-IO'}) + '\n'); process.exit(1);
}
let req;
try { req = JSON.parse(raw); } catch (e) {
  process.stdout.write(JSON.stringify({error:'E-JSON', detail: String(e)}) + '\n'); process.exit(1);
}
const emit = (o) => process.stdout.write(JSON.stringify(o) + '\n');

if (req.op === 'build') {
  try { emit({envelope_hex: buildEnvelope(req.certificate_json).toString('hex')}); }
  catch (e) { emit({error: 'BUILD-FAIL', detail: String(e)}); }
} else if (req.op === 'parse') {
  try {
    const data = Buffer.from(req.envelope_hex, 'hex');
    emit({certificate_json: parseEnvelope(data)});
  } catch (e) { emit({error: 'PARSE-FAIL', detail: String(e)}); }
} else if (req.op === 'parse_batch') {
  const arr = req.envelopes_hex || [];
  const results = [];
  for (const hx of arr) {
    try {
      const data = Buffer.from(hx, 'hex');
      try {
        results.push({certificate_json: parseEnvelope(data)});
      } catch (e) {
        // DEFECT-036: preserve typed code when available (from wire layer).
        const code = (e && typeof e.code === 'string' && e.code.startsWith('E_WIRE_'))
                     ? e.code : 'E_WIRE_MALFORMED';
        results.push({error: code, detail: String(e)});
      }
    } catch (e) {
      results.push({error: 'E_WIRE_MALFORMED', detail: String(e)});
    }
  }
  emit({results});
} else {
  emit({error: 'E-OP'});
}
