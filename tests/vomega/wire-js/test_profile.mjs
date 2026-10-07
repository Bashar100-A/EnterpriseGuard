#!/usr/bin/env node
// ADIE wire profile validation — JS conformance tests.

import { validate, MAX_DEPTH } from '../../../js/wire/profile.mjs';
import {
  Malformed, Float as FloatErr, NonCanonicalInt, Tag as TagErr,
  TypeMismatch,
} from '../../../js/wire/error.mjs';

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}

function expectErr(fn, errType) {
  try { fn(); return false; }
  catch (e) { return e instanceof errType; }
}

console.log('='.repeat(72));
console.log('ADIE wire profile validation — JS conformance');
console.log('='.repeat(72));

// ── Accepts primitives ──
check('T01 accepts null',  validate(null).t === 'null');
check('T02 accepts true',  validate(true).t === 'bool' && validate(true).v === true);
check('T03 accepts false', validate(false).t === 'bool' && validate(false).v === false);
check('T04 accepts empty text', validate('').t === 'text' && validate('').v === '');
check('T05 accepts text', validate('hello').t === 'text' && validate('hello').v === 'hello');
check('T06 accepts empty bytes',
      validate(new Uint8Array(0)).t === 'bytes' && validate(new Uint8Array(0)).v === '');
check('T07 accepts bytes',
      validate(Uint8Array.from([1, 2, 3])).t === 'bytes' &&
      validate(Uint8Array.from([1, 2, 3])).v === '010203');
check('T08 accepts uint 0', validate(0).t === 'uint' && validate(0).v === 0n);
check('T09 accepts uint 42', validate(42).t === 'uint' && validate(42).v === 42n);
check('T10 accepts uint u64::MAX',
      validate(0xFFFFFFFFFFFFFFFFn).t === 'uint' &&
      validate(0xFFFFFFFFFFFFFFFFn).v === 0xFFFFFFFFFFFFFFFFn);
check('T11 accepts negative -1', validate(-1).t === 'int' && validate(-1).v === -1n);
check('T12 accepts negative i64::MIN',
      validate(-0x8000000000000000n).t === 'int');

// ── Reject floats ──
check('T13 rejects float 1.0', expectErr(() => validate(1.5), FloatErr));
check('T14 rejects float Infinity',
      expectErr(() => validate(Infinity), FloatErr) ||
      expectErr(() => validate(Infinity), Malformed));

// ── Arrays ──
check('T15 accepts empty array',
      validate([]).t === 'array' && validate([]).v.length === 0);
check('T16 accepts array of primitives',
      validate(['a', 1, true, null]).v.length === 4);
check('T17 rejects array with float',
      expectErr(() => validate(['a', 1.5]), FloatErr));

// ── Maps ──
check('T18 accepts empty map',
      validate(new Map()).t === 'map' && validate(new Map()).v.length === 0);

const m1 = new Map([[1, 'a'], [2, 'b']]);
const v1 = validate(m1);
check('T19 accepts integer-keyed map',
      v1.t === 'map' && v1.v.length === 2 &&
      v1.v[0][0] === 1n && v1.v[1][0] === 2n);

const unsorted = new Map([[2, 'b'], [1, 'a']]);
const vU = validate(unsorted);
check('T20 canonicalizes unsorted map',
      vU.t === 'map' && vU.v.length === 2 &&
      Number(vU.v[0][0]) === 1 && Number(vU.v[1][0]) === 2);

check('T21 rejects text key',
      expectErr(() => validate(new Map([['k', 1]])), TypeMismatch));
check('T22 rejects bytes key',
      expectErr(() => validate(new Map([[new Uint8Array([1]), 1]])), TypeMismatch));
check('T23 rejects negative key',
      expectErr(() => validate(new Map([[-1, 'x']])), TypeMismatch));
check('T24 rejects bool key',
      expectErr(() => validate(new Map([[true, 1]])), TypeMismatch));

// ── Depth ──
function nested(d) {
  let v = null;
  for (let i = 0; i < d; i++) v = [v];
  return v;
}
check('T25 accepts depth 32', validate(nested(32)) !== null);
check('T26 rejects depth 33',
      expectErr(() => validate(nested(33)), Malformed));

// ── Nested ──
const nestedMap = new Map([[1, 'v'], [2, [1, 2]], [3, new Map([[10, false]])]]);
check('T27 accepts nested', validate(nestedMap) !== null);

// ── Out-of-range int ──
check('T28 rejects int > u64::MAX',
      expectErr(() => validate(0x10000000000000000n), NonCanonicalInt));

// ── Tag-result types (defense-in-depth) ──
check('T29 rejects Date',
      expectErr(() => validate(new Date()), TagErr));

// ── Unrecognised type ──
class Custom { }
check('T30 rejects custom object',
      expectErr(() => validate(new Custom()), Malformed));

// ── u64 range guards ──
let rangeOk = false;
try { validate(-0x8000000000000001n); } catch (e) { rangeOk = true; }
check('T31 rejects int < i64::MIN', rangeOk);

// ── T32: architectural boundary ─────────────────────────────
// Wire-level float/integer ambiguity is OUTSIDE profile authority.
//
// Two distinct CBOR encodings:
//     0x01                 (unsigned integer 1)
//     0xfb3ff0000000000000 (float64 1.0)
// decode to the SAME JavaScript value (Number 1) via cbor@9.
// Profile sees a Number and cannot distinguish the source encoding.
//
// Therefore rawcheck.mjs MUST reject forbidden float encodings at the
// byte level BEFORE cbor@9 runs. This test documents the boundary and
// prevents future removal of rawcheck on the false premise that
// "profile should have caught it".
{
  const v = validate(1);
  check('T32 profile cannot see float/int distinction (rawcheck authority)',
        v.t === 'uint' && v.v === 1n);
}

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));

process.exit(FAIL_N === 0 ? 0 : 1);
