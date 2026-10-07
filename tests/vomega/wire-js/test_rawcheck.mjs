#!/usr/bin/env node
// ADIE wire rawcheck — JS conformance tests.

import { rawcheck, MAX_DEPTH } from '../../../js/wire/rawcheck.mjs';
import {
  Malformed, Trailing, Indefinite, Float as FloatErr, Tag as TagErr,
  NonCanonicalInt, InvalidUtf8,
} from '../../../js/wire/error.mjs';

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}

function h2b(hex) { return Buffer.from(hex, 'hex'); }

function expectOk(name, hex) {
  try { rawcheck(h2b(hex)); check(name, true); }
  catch (e) { check(name, false, `unexpected ${e.code || e.constructor.name}`); }
}

function expectRej(name, hex, errType) {
  try { rawcheck(h2b(hex)); check(name, false, `should have rejected as ${errType.name}`); }
  catch (e) {
    check(name, e instanceof errType,
          `expected ${errType.name}, got ${e.constructor.name} (${e.code || '?'})`);
  }
}

console.log('='.repeat(72));
console.log('ADIE wire rawcheck — JS conformance');
console.log('='.repeat(72));

// ─── Valid (canonical) ────────────────────────────────────────────
expectOk('V01 uint 0',                '00');
expectOk('V02 uint 1',                '01');
expectOk('V03 uint 23',               '17');
expectOk('V04 uint 24',               '1818');
expectOk('V05 uint 255',              '18ff');
expectOk('V06 uint 256',              '190100');
expectOk('V07 uint 65535',            '19ffff');
expectOk('V08 uint 65536',            '1a00010000');
expectOk('V09 uint u32::MAX',         '1affffffff');
expectOk('V10 uint u32::MAX+1',       '1b0000000100000000');
expectOk('V11 uint u64::MAX',         '1bffffffffffffffff');
expectOk('V12 negint -1',             '20');
expectOk('V13 negint -24',            '37');
expectOk('V14 negint -25',            '3818');
expectOk('V15 negint -256',           '38ff');
expectOk('V16 negint -257',           '390100');
expectOk('V17 bytes empty',           '40');
expectOk('V18 bytes 010203',          '43010203');
expectOk('V19 text empty',            '60');
expectOk('V20 text "hello"',          '6568656c6c6f');
expectOk('V21 array empty',           '80');
expectOk('V22 array [1,2,3]',         '83010203');
expectOk('V23 map empty',             'a0');
expectOk('V24 map {1:2}',             'a10102');
expectOk('V25 false (f4)',            'f4');
expectOk('V26 true (f5)',             'f5');
expectOk('V27 null (f6)',             'f6');
expectOk('V28 nested [1,[2,3]]',      '8201820203');

// ─── Reject: tags ────────────────────────────────────────────────
expectRej('R01 tag 1',                'c101', TagErr);
expectRej('R02 tag 0 + "2026-10-07"', 'c06a323032362d31302d3037', TagErr);
expectRej('R03 tag 9999',             'd9270f01', TagErr);

// ─── Reject: floats ──────────────────────────────────────────────
expectRej('R04 float16 1.0',          'f93c00', FloatErr);
expectRej('R05 float32 1.0',          'fa3f800000', FloatErr);
expectRej('R06 float64 1.0',          'fb3ff0000000000000', FloatErr);

// ─── Reject: indefinite ──────────────────────────────────────────
expectRej('R07 indefinite bytes',     '5f01ff', Indefinite);
expectRej('R08 indefinite text',      '7f0161ff', Indefinite);
expectRej('R09 indefinite array',     '9f01ff', Indefinite);
expectRej('R10 indefinite map',       'bf016178ff', Indefinite);

// ─── Reject: non-shortest int/length ─────────────────────────────
expectRej('R11 non-shortest uint 1 (ai24)',   '1801', NonCanonicalInt);
expectRej('R12 non-shortest uint 1 (ai25)',   '190001', NonCanonicalInt);
expectRej('R13 non-shortest uint 1 (ai26)',   '1a00000001', NonCanonicalInt);
expectRej('R14 non-shortest bytes len 0',     '5800', NonCanonicalInt);
expectRej('R15 non-shortest text len 0',      '7800', NonCanonicalInt);
expectRej('R16 non-shortest array len 0',     '9800', NonCanonicalInt);
expectRej('R17 non-shortest map len 0',       'b800', NonCanonicalInt);
expectRej('R18 non-shortest negint -0 (ai24)','3800', NonCanonicalInt);

// ─── Reject: trailing ────────────────────────────────────────────
expectRej('R19 trailing 1 byte',      '0000', Trailing);
expectRej('R20 trailing 2 bytes',     '00a0ff', Trailing);

// ─── Reject: reserved additional-info ────────────────────────────
expectRej('R21 reserved ai28',        '1c', Malformed);
expectRej('R22 reserved ai29',        '1d', Malformed);
expectRej('R23 reserved ai30',        '1e', Malformed);

// ─── Reject: forbidden simples ───────────────────────────────────
expectRej('R24 undefined (0xf7)',     'f7', Malformed);
expectRej('R25 break alone (0xff)',   'ff', Malformed);

// ─── Reject: malformed / truncated ───────────────────────────────
expectRej('R26 truncated bytes',      '430102', Malformed);
expectRej('R27 truncated text',       '6261', Malformed);
expectRej('R28 truncated array',      '8201', Malformed);
expectRej('R29 invalid UTF-8',        '62fffe', InvalidUtf8);

// ─── Architectural: T32 invariant at wire level ──────────────────
// DEFECT-026 / T32:
//   CBOR uint 1        ("01")               → Number 1  → ACCEPTED
//   CBOR float64 1.0   ("fb3ff0000000000000")→ Number 1  → REJECTED
// The two are INDISTINGUISHABLE after cbor@9 decoding. Only rawcheck
// can preserve this distinction. Removing rawcheck would lose it.
{
  let okAcc = false;
  try { rawcheck(h2b('01')); okAcc = true; } catch (_) {}

  let rejF64 = false;
  try { rawcheck(h2b('fb3ff0000000000000')); } catch (e) {
    rejF64 = e instanceof FloatErr;
  }

  check(
    'A01 ARCH uint "01" accepted + float64 "fb3ff0000000000000" rejected (rawcheck authority)',
    okAcc && rejF64
  );
}

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));

process.exit(FAIL_N === 0 ? 0 : 1);
