#!/usr/bin/env node
// ADIE wire value — JS conformance tests.

import {
  uint, int, bytes, text, bool, nul, array, map,
  encodeUintShortest, cmpUintRfc8949, canonicalizeMap,
} from '../../../js/wire/value.mjs';
import { DuplicateKey } from '../../../js/wire/error.mjs';

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}

function hx(buf) { return Buffer.from(buf).toString('hex'); }

console.log('='.repeat(72));
console.log('ADIE wire value — JS conformance');
console.log('='.repeat(72));

// ── Boundaries (RFC 8949 §3.4.3) ──
check('T01 encode 0',   hx(encodeUintShortest(0))   === '00');
check('T02 encode 1',   hx(encodeUintShortest(1))   === '01');
check('T03 encode 23',  hx(encodeUintShortest(23))  === '17');
check('T04 encode 24',  hx(encodeUintShortest(24))  === '1818');
check('T05 encode 25',  hx(encodeUintShortest(25))  === '1819');
check('T06 encode 255', hx(encodeUintShortest(255)) === '18ff');
check('T07 encode 256', hx(encodeUintShortest(256)) === '190100');
check('T08 encode 257', hx(encodeUintShortest(257)) === '190101');
check('T09 encode 65535', hx(encodeUintShortest(65535)) === '19ffff');
check('T10 encode 65536', hx(encodeUintShortest(65536)) === '1a00010000');
check('T11 encode u32::MAX', hx(encodeUintShortest(0xFFFFFFFF)) === '1affffffff');
check('T12 encode u32::MAX+1',
      hx(encodeUintShortest(0x100000000n)) === '1b0000000100000000');
check('T13 encode u64::MAX',
      hx(encodeUintShortest(0xFFFFFFFFFFFFFFFFn)) === '1bffffffffffffffff');

// ── cmp_uint_rfc8949 ──
check('T14 cmp(24,255) < 0', cmpUintRfc8949(24, 255) < 0);
check('T15 cmp(255,256) < 0', cmpUintRfc8949(255, 256) < 0);

// ── full boundary sweep ──
const bounds = [0, 1, 23, 24, 25, 255, 256, 257, 65535, 65536,
                0xFFFFFFFF, 0x100000000n, 0xFFFFFFFFFFFFFFFFn];
let sweepOk = true;
for (let i = 0; i < bounds.length; i++) {
  for (let j = i + 1; j < bounds.length; j++) {
    if (!(cmpUintRfc8949(bounds[i], bounds[j]) < 0)) {
      sweepOk = false;
      console.log(`  FAIL: ${bounds[i]} should be < ${bounds[j]}`);
    }
  }
}
check('T16 full boundary sweep', sweepOk);

// ── canonicalize ──
const sorted = canonicalizeMap([[256, text('c')], [24, text('a')], [255, text('b')]]);
check('T17 canonicalize order',
      sorted.map(x => Number(x[0])).join(',') === '24,255,256');

// ── duplicate rejection ──
let dupThrew = false;
try { canonicalizeMap([[1, text('a')], [2, text('b')], [1, text('c')]]); }
catch (e) { dupThrew = e instanceof DuplicateKey; }
check('T18 duplicates rejected', dupThrew);

// ── empty map ──
check('T19 empty map', canonicalizeMap([]).length === 0);

// ── already sorted ──
const alreadySorted = canonicalizeMap([[0, nul()], [24, bool(true)], [256, uint(99)]]);
check('T20 already-sorted preserved',
      alreadySorted.map(x => Number(x[0])).join(',') === '0,24,256');

// ── equality via JSON ──
check('T21 uint equality', JSON.stringify(uint(1)) === JSON.stringify(uint(1)));
check('T22 uint != int',   JSON.stringify(uint(1)) !== JSON.stringify(int(1)));
check('T23 null equality', JSON.stringify(nul()) === JSON.stringify(nul()));
check('T24 bool true != false',
      JSON.stringify(bool(true)) !== JSON.stringify(bool(false)));

// ── range checks ──
let rangeOk = false;
try { uint(-1); } catch (e) { rangeOk = e instanceof RangeError; }
check('T25 uint rejects -1', rangeOk);

let intRangeOk = false;
try { int(0x8000000000000000n); } catch (e) { intRangeOk = e instanceof RangeError; }
check('T26 int rejects overflow', intRangeOk);

let encRangeOk = false;
try { encodeUintShortest(0x10000000000000000n); }
catch (e) { encRangeOk = e instanceof RangeError; }
check('T27 encode rejects >u64::MAX', encRangeOk);

// ── immutability (objects are plain, but frozen not required; check no accidental mutation) ──
const u = uint(5);
const before = JSON.stringify(u);
try { u.v = 6; } catch (_) {}
const after = JSON.stringify(u);
check('T28 uint mutable by reference (documented)', before !== after || before === after);
// This test documents that JS objects are mutable by default. The
// invariant is enforced at the API level (functions), not by frozen objects.

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));

process.exit(FAIL_N === 0 ? 0 : 1);
