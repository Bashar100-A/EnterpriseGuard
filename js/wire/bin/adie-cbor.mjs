#!/usr/bin/env node
// js/wire/bin/adie-cbor.mjs — JS endpoint for Rust/Python differentials.
//
// Protocol (identical to rust/adie-primitives/src/bin/adie-cbor.rs and
// protocol/wire/bin/adie-cbor.py):
//   stdin:  {"op":"encode","value":<AdieValue>}
//   stdin:  {"op":"decode","cbor_hex":"<hex>"}
//   stdout: {"cbor_hex":"..."} | {"value":<AdieValue>} | {"error":"E_..","detail":".."}
//
// AdieValue JSON form matches js/wire/value.mjs tagged objects exactly.

import { readFileSync } from 'node:fs';
import * as A from '../index.mjs';

// ─── lossless JSON parse for u64 values > 2^53 ────────────────────
// JSON.parse converts 18446744073709551615 to a lossy Number. We
// pre-quote integer literals with 16+ digits, then revive as BigInt.
function parsePreservingBigInts(text) {
  const marked = text.replace(
    /([\[,:]\s*)(-?\d{16,})(?=\s*[,\]}])/g,
    '$1"__BIGINT__$2"'
  );
  return revive(JSON.parse(marked));
}

function revive(x) {
  if (typeof x === 'string' && x.startsWith('__BIGINT__')) {
    return BigInt(x.slice(10));
  }
  if (Array.isArray(x)) return x.map(revive);
  if (x && typeof x === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(x)) out[k] = revive(v);
    return out;
  }
  return x;
}

// ─── lossless JSON serialize for BigInt in AdieValue ──────────────
function stringify(v) {
  if (v === null) return 'null';
  if (typeof v === 'boolean') return JSON.stringify(v);
  if (typeof v === 'number')  return String(v);
  if (typeof v === 'bigint')  return String(v);
  if (typeof v === 'string')  return JSON.stringify(v);
  if (Array.isArray(v))       return '[' + v.map(stringify).join(',') + ']';
  if (typeof v === 'object') {
    const parts = [];
    for (const [k, val] of Object.entries(v)) {
      parts.push(JSON.stringify(k) + ':' + stringify(val));
    }
    return '{' + parts.join(',') + '}';
  }
  return 'null';
}

// ─── main ────────────────────────────────────────────────────────
let raw;
try {
  raw = readFileSync(0, 'utf8');
} catch (e) {
  process.stdout.write('{"error":"E_IO","detail":"' + e.message + '"}\n');
  process.exit(1);
}

let req;
try {
  req = parsePreservingBigInts(raw);
} catch (e) {
  process.stdout.write('{"error":"E_JSON","detail":"' + e.message + '"}\n');
  process.exit(1);
}

function emit(obj) {
  process.stdout.write(stringify(obj) + '\n');
}

if (req.op === 'encode') {
  try {
    const bytes = A.encode(req.value);
    emit({ cbor_hex: Buffer.from(bytes).toString('hex') });
  } catch (e) {
    emit({ error: e.code || 'E_UNKNOWN', detail: String(e) });
  }
} else if (req.op === 'decode') {
  try {
    const v = A.decode(Buffer.from(req.cbor_hex, 'hex'));
    emit({ value: v });
  } catch (e) {
    emit({ error: e.code || 'E_UNKNOWN', detail: String(e) });
  }
} else {
  emit({ error: 'E_OP', detail: 'unknown op' });
  process.exit(1);
}
