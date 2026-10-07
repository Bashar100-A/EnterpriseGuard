#!/usr/bin/env node
// WASM precision — u64/i64 boundary values, DEFECT-029-WASM proof.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const WASM = require('../../../js/wasm-pkg-node/adie_wasm.js');

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}

console.log('='.repeat(72));
console.log('WASM precision — u64/i64 boundary (DEFECT-029-WASM)');
console.log('='.repeat(72));

const U64 = [
  ['0',                  '00'],
  ['23',                 '17'],
  ['24',                 '1818'],
  ['255',                '18ff'],
  ['256',                '190100'],
  ['65535',              '19ffff'],
  ['65536',              '1a00010000'],
  ['4294967295',         '1affffffff'],               // u32::MAX
  ['4294967296',         '1b0000000100000000'],       // u32::MAX+1
  ['18446744073709551615','1bffffffffffffffff'],      // u64::MAX
];
const I64 = [
  ['-1',                  '20',                    true],
  ['-9223372036854775808','3b7fffffffffffffff',    true],   // i64::MIN
  ['9223372036854775807', '1b7fffffffffffffff',    false],  // i64::MAX
];

for (const [dec, hex] of U64) {
  const json = JSON.stringify({t:'uint', v: dec});
  const bytes = WASM.encode(json);
  const got = Buffer.from(bytes).toString('hex');
  check(`u64 ${dec} encode`, got === hex, `got=${got} want=${hex}`);
  const back = JSON.parse(WASM.decode(new Uint8Array(bytes)));
  check(`u64 ${dec} decode lossless`,
        back.t === 'uint' && typeof back.v === 'string' && back.v === dec,
        `got=${JSON.stringify(back)}`);
}
// i64 tests: DCP 2.1 CBOR wire does NOT preserve t:'int' vs t:'uint'
// for positive values. Both encode as major type 0 (unsigned). Decoder
// always returns t:'uint' for non-negative. This is correct semantic
// normalization, not information loss.
//
// Therefore the round-trip invariant is: the NUMERIC VALUE survives
// losslessly, and for negatives the t:'int' tag survives. For positive
// i64 values, the decoder returns t:'uint'.
for (const [dec, hex, isNeg] of I64) {
  const json = JSON.stringify({t:'int', v: dec});
  const bytes = WASM.encode(json);
  const got = Buffer.from(bytes).toString('hex');
  check(`i64 ${dec} encode`, got === hex, `got=${got} want=${hex}`);
  const back = JSON.parse(WASM.decode(new Uint8Array(bytes)));
  const expectTag = isNeg ? 'int' : 'uint';
  check(`i64 ${dec} decode lossless (tag=${expectTag})`,
        back.t === expectTag && typeof back.v === 'string' && back.v === dec,
        `got=${JSON.stringify(back)}`);
}
// Out-of-range must be rejected
try { WASM.encode(JSON.stringify({t:'uint', v:'18446744073709551616'}));
      check('uint u64::MAX+1 rejected', false, 'accepted'); }
catch (_) { check('uint u64::MAX+1 rejected', true); }
try { WASM.encode(JSON.stringify({t:'uint', v:'-1'}));
      check('uint -1 rejected', false, 'accepted'); }
catch (_) { check('uint -1 rejected', true); }
try { WASM.encode(JSON.stringify({t:'int', v:'-9223372036854775809'}));
      check('int i64::MIN-1 rejected', false, 'accepted'); }
catch (_) { check('int i64::MIN-1 rejected', true); }
// Map key u64::MAX via string
try {
  const bytes = WASM.encode(JSON.stringify({t:'map', v:[['18446744073709551615', {t:'null'}]]}));
  const hex = Buffer.from(bytes).toString('hex');
  check('map key u64::MAX encodes', hex === 'a11bfffffffffffffffff6', `got=${hex}`);
  const back = JSON.parse(WASM.decode(new Uint8Array(bytes)));
  check('map key u64::MAX lossless',
        back.t === 'map' && back.v[0][0] === '18446744073709551615',
        `got=${JSON.stringify(back)}`);
} catch (e) { check('map key u64::MAX', false, String(e)); }

console.log();
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
process.exit(FAIL_N === 0 ? 0 : 1);
