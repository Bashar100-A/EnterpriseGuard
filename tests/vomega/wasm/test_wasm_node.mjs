#!/usr/bin/env node
// WASM Node.js differential — 44 vectors vs native Rust reference.
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { parsePreservingBigInts, stringify } from '../../../js/wire/bin/json-io.mjs';

const require = createRequire(import.meta.url);
const WASM = require('../../../js/wasm-pkg-node/adie_wasm.js');

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT      = resolve(__dirname, '../../..');
const RUST_BIN  = resolve(ROOT, 'rust/adie-primitives/target/release/adie-cbor');
const VECTORS   = resolve(ROOT, 'tests/vomega/wire/differential_vectors.json');

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}

function rustCall(p) {
  const r = spawnSync(RUST_BIN, [], { input: stringify(p), encoding:'utf8', timeout:20000 });
  try { return JSON.parse(r.stdout.trim()); } catch { return { error: '_PARSE' }; }
}
function wasmEncodeHex(valueJson) {
  try {
    const bytes = WASM.encode(JSON.stringify(toWasmAbi(valueJson)));
    return { cbor_hex: Buffer.from(bytes).toString('hex') };
  } catch (e) { return { error: String(e) }; }
}
function wasmDecodeValue(cborHex) {
  try {
    const s = WASM.decode(new Uint8Array(Buffer.from(cborHex, 'hex')));
    return { value: JSON.parse(s) };
  } catch (e) { return { error: String(e) }; }
}

// Convert AdieValue → WASM ABI (v as string for uint/int, keys as string)
function toWasmAbi(v) {
  if (v.t === 'uint' || v.t === 'int') return { t: v.t, v: String(v.v) };
  if (v.t === 'array') return { t: 'array', v: v.v.map(toWasmAbi) };
  if (v.t === 'map')   return { t: 'map', v: v.v.map(([k, val]) => [String(k), toWasmAbi(val)]) };
  return v;
}
// Canonicalize AdieValue JSON for comparison: Number v -> String v
function canon(v) {
  if (v === null) return null;
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v;
  if (typeof v === 'string') return v;
  if (Array.isArray(v)) return v.map(canon);
  if (v && typeof v === 'object') {
    // Map keys: Rust native returns numbers, WASM ABI returns strings.
    // Normalize both to strings (u64 boundary invariant).
    if (v.t === 'map' && Array.isArray(v.v)) {
      return {
        t: 'map',
        v: v.v.map(([k, val]) => [String(k), canon(val)]),
      };
    }
    const o = {};
    for (const k of Object.keys(v).sort()) {
      let val = v[k];
      // Numeric v: normalize to string (u64 boundary invariant).
      if ((v.t === 'uint' || v.t === 'int') && k === 'v' && typeof val === 'number') {
        val = String(val);
      }
      o[k] = canon(val);
    }
    return o;
  }
  return v;
}
function canonJson(x) { return JSON.stringify(canon(x)); }

console.log('='.repeat(72));
console.log('WASM Node.js differential vs native Rust (3A.4B)');
console.log('='.repeat(72));

const vectors = parsePreservingBigInts(readFileSync(VECTORS, 'utf8'));

// Encode parity
for (const v of vectors.encode_vectors) {
  const rs = rustCall({ op:'encode', value: v.value });
  const ws = wasmEncodeHex(v.value);
  if (rs.error || ws.error) { check(`E ${v.id}`, false, `rs=${rs.error} ws=${ws.error}`); continue; }
  check(`E ${v.id} WASM≡Rust`, rs.cbor_hex === ws.cbor_hex,
        `rust=${rs.cbor_hex?.slice(0,40)} wasm=${ws.cbor_hex?.slice(0,40)}`);
}
// Decode parity
for (const v of vectors.decode_vectors) {
  const rs = rustCall({ op:'decode', cbor_hex: v.cbor_hex });
  const ws = wasmDecodeValue(v.cbor_hex);
  if (rs.error || ws.error) { check(`D ${v.id}`, false, `rs=${rs.error} ws=${ws.error}`); continue; }
  check(`D ${v.id} WASM≡Rust`, canonJson(rs.value) === canonJson(ws.value),
        `rust=${canonJson(rs.value)?.slice(0,60)} wasm=${canonJson(ws.value)?.slice(0,60)}`);
}
// Negative parity
for (const v of vectors.negative_vectors) {
  const rs = rustCall({ op:'decode', cbor_hex: v.cbor_hex });
  const ws = wasmDecodeValue(v.cbor_hex);
  if (!rs.error || !ws.error) { check(`N ${v.id}`, false, `rs=${rs.error} ws=${ws.error}`); continue; }
  check(`N ${v.id} reject parity`, rs.error === ws.error, `rs=${rs.error} ws=${ws.error}`);
}
// A01 architectural
{
  const ok01 = wasmDecodeValue('01');
  const rejF = wasmDecodeValue('fb3ff0000000000000');
  check('A01 ARCH uint "01" accept + float64 reject',
        !ok01.error && rejF.error === 'E_WIRE_FLOAT');
}

console.log();
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
process.exit(FAIL_N === 0 ? 0 : 1);
