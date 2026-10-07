#!/usr/bin/env node
// ADIE differential: JavaScript ↔ Python (Stage 3A.4A-DIFF / D.9).
// Fixed per DEFECT-029.

import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import * as JS from '../../../js/wire/index.mjs';
import { parsePreservingBigInts, stringify, canon } from '../../../js/wire/bin/json-io.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT      = resolve(__dirname, '../../..');
const PY_BIN    = resolve(ROOT, '.venv/bin/python');
const PY_SCRIPT = resolve(ROOT, 'protocol/wire/bin/adie-cbor.py');
const VECTORS   = resolve(__dirname, '../wire/differential_vectors.json');

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}

function pyCall(payload) {
  const r = spawnSync(PY_BIN, [PY_SCRIPT], {
    input: stringify(payload),
    encoding: 'utf8',
    timeout: 20000,
    cwd: ROOT,
  });
  if (r.error) return { _err: String(r.error) };
  try { return JSON.parse(r.stdout.trim()); }
  catch { return { _raw: r.stdout.slice(0, 200), _err: r.stderr.slice(0, 200) }; }
}

function jsEncodeHex(valueJson) {
  try {
    const b = JS.encode(valueJson);
    return { cbor_hex: Buffer.from(b).toString('hex') };
  } catch (e) { return { error: e.code || 'E_UNKNOWN', detail: String(e) }; }
}
function jsDecodeValue(cborHex) {
  try {
    const v = JS.decode(Buffer.from(cborHex, 'hex'));
    return { value: v };
  } catch (e) { return { error: e.code || 'E_UNKNOWN', detail: String(e) }; }
}
function bothOk(r) { return r && !r.error && r._raw === undefined; }

console.log('='.repeat(72));
console.log('ADIE differential: JavaScript ↔ Python');
console.log('='.repeat(72));

const vectors = parsePreservingBigInts(readFileSync(VECTORS, 'utf8'));

for (const vec of vectors.encode_vectors) {
  const id = vec.id;
  const py = pyCall({ op: 'encode', value: vec.value });
  const js = jsEncodeHex(vec.value);
  if (!bothOk(py)) { check(`E ${id} py encode ok`, false, `py=${canon(py).slice(0,80)}`); continue; }
  if (!bothOk(js)) { check(`E ${id} js encode ok`, false, `js=${canon(js).slice(0,80)}`); continue; }
  check(`E ${id} positive parity`, py.cbor_hex === js.cbor_hex,
        `py=${py.cbor_hex?.slice(0,40)} js=${js.cbor_hex?.slice(0,40)}`);
}

for (const vec of vectors.decode_vectors) {
  const id = vec.id;
  const py = pyCall({ op: 'decode', cbor_hex: vec.cbor_hex });
  const js = jsDecodeValue(vec.cbor_hex);
  if (!bothOk(py)) { check(`D ${id} py decode ok`, false, `py=${canon(py).slice(0,80)}`); continue; }
  if (!bothOk(js)) { check(`D ${id} js decode ok`, false, `js=${canon(js).slice(0,80)}`); continue; }
  const pyC = canon(py.value), jsC = canon(js.value);
  check(`D ${id} decode parity`, pyC === jsC,
        `py=${pyC.slice(0,80)} js=${jsC.slice(0,80)}`);
}

for (const vec of vectors.negative_vectors) {
  const id = vec.id;
  const py = pyCall({ op: 'decode', cbor_hex: vec.cbor_hex });
  const js = jsDecodeValue(vec.cbor_hex);
  if (!py.error) { check(`N ${id} py rejects`, false, `accepted`); continue; }
  if (!js.error) { check(`N ${id} js rejects`, false, `accepted`); continue; }
  check(`N ${id} rejection parity`, py.error === js.error,
        `py=${py.error} js=${js.error}`);
}

{
  const ok01 = pyCall({ op: 'decode', cbor_hex: '01' });
  const rejF = pyCall({ op: 'decode', cbor_hex: 'fb3ff0000000000000' });
  const jsOk01 = jsDecodeValue('01');
  const jsRejF = jsDecodeValue('fb3ff0000000000000');
  const matched = !ok01.error && !jsOk01.error
    && rejF.error === 'E_WIRE_FLOAT' && jsRejF.error === 'E_WIRE_FLOAT';
  check('A01 ARCH uint "01" accepted + float64 rejected (py ≡ js)', matched);
}

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));
process.exit(FAIL_N === 0 ? 0 : 1);
