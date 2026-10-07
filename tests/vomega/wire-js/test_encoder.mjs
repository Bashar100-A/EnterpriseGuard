#!/usr/bin/env node
// ADIE wire encoder — JS conformance tests (D.5).

import { encode } from '../../../js/wire/encoder.mjs';
import {
  uint, int, bytes, text, bool, nul, array, map,
} from '../../../js/wire/value.mjs';
import {
  Malformed, DuplicateKey, NonCanonicalInt,
} from '../../../js/wire/error.mjs';

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}
function hx(b) { return Buffer.from(b).toString('hex'); }
function expectErr(fn, errType) {
  try { fn(); return false; } catch (e) { return e instanceof errType; }
}

console.log('='.repeat(72));
console.log('ADIE wire encoder — JS conformance');
console.log('='.repeat(72));

// ── Scalars ──
check('E01 null',   hx(encode(nul())) === 'f6');
check('E02 true',   hx(encode(bool(true))) === 'f5');
check('E03 false',  hx(encode(bool(false))) === 'f4');
check('E04 uint 0',  hx(encode(uint(0))) === '00');
check('E05 uint 1',  hx(encode(uint(1))) === '01');
check('E06 uint 23', hx(encode(uint(23))) === '17');
check('E07 uint 24', hx(encode(uint(24))) === '1818');
check('E08 uint 255', hx(encode(uint(255))) === '18ff');
check('E09 uint 256', hx(encode(uint(256))) === '190100');
check('E10 uint 65535', hx(encode(uint(65535))) === '19ffff');
check('E11 uint 65536', hx(encode(uint(65536))) === '1a00010000');
check('E12 uint u32::MAX', hx(encode(uint(0xFFFFFFFF))) === '1affffffff');
check('E13 uint u32::MAX+1', hx(encode(uint(0x100000000n))) === '1b0000000100000000');
check('E14 uint u64::MAX', hx(encode(uint(0xFFFFFFFFFFFFFFFFn))) === '1bffffffffffffffff');
check('E15 int -1',   hx(encode(int(-1))) === '20');
check('E16 int -24',  hx(encode(int(-24))) === '37');
check('E17 int -25',  hx(encode(int(-25))) === '3818');
check('E18 int -256', hx(encode(int(-256))) === '38ff');
check('E19 int -257', hx(encode(int(-257))) === '390100');
check('E20 text empty', hx(encode(text(''))) === '60');
check('E21 text "hello"', hx(encode(text('hello'))) === '6568656c6c6f');
check('E22 bytes empty', hx(encode(bytes(''))) === '40');
check('E23 bytes 010203', hx(encode(bytes('010203'))) === '43010203');

// ── Structures ──
check('E24 array empty', hx(encode(array([]))) === '80');
check('E25 array [1,2,3]',
      hx(encode(array([uint(1), uint(2), uint(3)]))) === '83010203');
check('E26 map empty', hx(encode(map([]))) === 'a0');
check('E27 map {1:"a"}',
      hx(encode(map([[1, text('a')]]))) === 'a1016161');
check('E28 map {1:"a",2:"b"}',
      hx(encode(map([[1, text('a')], [2, text('b')]]))) === 'a2016161026162');
check('E29 nested {1:[2,3]}',
      hx(encode(map([[1, array([uint(2), uint(3)])]]))) === 'a101820203');

// ── Determinism / sorting ──
const m1 = map([[1, text('a')], [2, text('b')]]);
const m2 = map([[2, text('b')], [1, text('a')]]);
check('E30 unsorted insertion normalized',
      hx(encode(m1)) === hx(encode(m2)) && hx(encode(m1)) === 'a2016161026162');

{
  const complex = map([
    [1, text('v')],
    [2, array([uint(1), nul()])],
    [3, map([[256, bool(true)]])],
  ]);
  let ok = true;
  for (let i = 0; i < 5; i++) {
    if (hx(encode(complex)) !== hx(encode(complex))) { ok = false; break; }
  }
  check('E31 deterministic repeated encoding', ok);
}

// ── Rejections ──
check('E32 reject unknown tag',
      expectErr(() => encode({t:'foo', v:1}), Malformed));
check('E33 reject uint -1',
      expectErr(() => encode({t:'uint', v:-1}), NonCanonicalInt));
check('E34 reject uint with string',
      expectErr(() => encode({t:'uint', v:'5'}), NonCanonicalInt));
check('E35 reject text with number',
      expectErr(() => encode({t:'text', v:5}), Malformed));
check('E36 reject array non-array',
      expectErr(() => encode({t:'array', v:'nope'}), Malformed));
check('E37 reject map duplicate keys',
      expectErr(() => encode(map([[1, text('a')], [1, text('b')]])), DuplicateKey));
check('E38 reject map string key',
      expectErr(() => encode({t:'map', v:[['k', {t:'null'}]]}), NonCanonicalInt));
check('E39 reject map negint key',
      expectErr(() => encode({t:'map', v:[[-1, {t:'null'}]]}), NonCanonicalInt));
check('E40 reject bytes odd hex',
      expectErr(() => encode({t:'bytes', v:'abc'}), Malformed));
check('E41 reject bytes non-hex',
      expectErr(() => encode({t:'bytes', v:'zz'}), Malformed));
check('E42 reject null with v',
      expectErr(() => encode({t:'null', v:1}), Malformed));
check('E43 reject bool with number',
      expectErr(() => encode({t:'bool', v:1}), Malformed));

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));
process.exit(FAIL_N === 0 ? 0 : 1);
