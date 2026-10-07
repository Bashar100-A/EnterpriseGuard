#!/usr/bin/env node
// ADIE wire public API — JS conformance tests (D.7).

import * as Adie from '../../../js/wire/index.mjs';

let PASS_N = 0, FAIL_N = 0;
function check(name, cond, detail = '') {
  if (cond) { PASS_N++; console.log(`[PASS] ${name}`); }
  else { FAIL_N++; console.log(`[FAIL] ${name}: ${detail}`); }
}
function hx(b) { return Buffer.from(b).toString('hex'); }

console.log('='.repeat(72));
console.log('ADIE wire public API — JS conformance');
console.log('='.repeat(72));

// Public function presence
check('I01 encode exported',   typeof Adie.encode === 'function');
check('I02 decode exported',   typeof Adie.decode === 'function');
check('I03 rawcheck exported', typeof Adie.rawcheck === 'function');
check('I04 profileValidate exported',
      typeof Adie.profileValidate === 'function');

// Value constructors
check('I05 uint exported',  typeof Adie.uint === 'function');
check('I06 int exported',   typeof Adie.int === 'function');
check('I07 bytes exported', typeof Adie.bytes === 'function');
check('I08 text exported',  typeof Adie.text === 'function');
check('I09 bool exported',  typeof Adie.bool === 'function');
check('I10 nul exported',   typeof Adie.nul === 'function');
check('I11 array exported', typeof Adie.array === 'function');
check('I12 map exported',   typeof Adie.map === 'function');

// Error classes
for (const name of [
  'CborError', 'Malformed', 'Trailing', 'Indefinite', 'Float', 'Tag',
  'DuplicateKey', 'NonCanonicalInt', 'NonCanonicalMap', 'InvalidUtf8',
  'TypeMismatch', 'MissingField', 'UnknownCritical', 'Version', 'Ambiguous',
]) {
  check(`I13.${name} exported`, typeof Adie[name] === 'function');
}

// End-to-end via public API
{
  const v = Adie.map([
    [1, Adie.array([Adie.uint(2), Adie.text('x')])],
    [256, Adie.nul()],
  ]);
  const bytes = Adie.encode(v);
  const back = Adie.decode(bytes);
  check('I14 e2e encode/decode via index',
        hx(Adie.encode(back)) === hx(bytes));
}

// Architectural test at API surface
check('I15 ARCH uint 01 accepted via index',
      (() => { try { Adie.decode(Buffer.from('01','hex')); return true; } catch { return false; } })());
check('I16 ARCH float64 rejected via index',
      (() => {
        try { Adie.decode(Buffer.from('fb3ff0000000000000','hex')); return false; }
        catch (e) { return e instanceof Adie.Float; }
      })());

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));
process.exit(FAIL_N === 0 ? 0 : 1);
