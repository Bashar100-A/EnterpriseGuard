#!/usr/bin/env node
// ADIE wire errors — JS conformance tests.

import {
  CborError,
  Malformed, Trailing, Indefinite, Float, Tag, DuplicateKey,
  NonCanonicalInt, NonCanonicalMap, InvalidUtf8,
  TypeMismatch, MissingField, UnknownCritical, Version, Ambiguous,
} from '../../../js/wire/error.mjs';

let PASS_N = 0, FAIL_N = 0;

function check(name, cond, detail = '') {
  if (cond) {
    PASS_N++;
    console.log(`[PASS] ${name}`);
  } else {
    FAIL_N++;
    console.log(`[FAIL] ${name}: ${detail}`);
  }
}

console.log('='.repeat(72));
console.log('ADIE wire errors — JS conformance');
console.log('='.repeat(72));

// T01-T14: stable codes
check('T01 Malformed.code',   new Malformed('x').code === 'E_WIRE_MALFORMED');
check('T02 Trailing.code',    new Trailing(1).code === 'E_WIRE_TRAILING');
check('T03 Indefinite.code',  new Indefinite().code === 'E_WIRE_INDEFINITE');
check('T04 Float.code',       new Float().code === 'E_WIRE_FLOAT');
check('T05 Tag.code',         new Tag(1).code === 'E_WIRE_TAG');
check('T06 DuplicateKey.code', new DuplicateKey().code === 'E_WIRE_DUP_KEY');
check('T07 NonCanonicalInt.code',
      new NonCanonicalInt().code === 'E_WIRE_NONCANONICAL_INT');
check('T08 NonCanonicalMap.code',
      new NonCanonicalMap().code === 'E_WIRE_NONCANONICAL_MAP');
check('T09 InvalidUtf8.code', new InvalidUtf8().code === 'E_WIRE_INVALID_UTF8');
check('T10 TypeMismatch.code',
      new TypeMismatch('x', 'y').code === 'E_WIRE_TYPE_MISMATCH');
check('T11 MissingField.code',
      new MissingField('x').code === 'E_WIRE_MISSING_FIELD');
check('T12 UnknownCritical.code',
      new UnknownCritical(99).code === 'E_WIRE_UNKNOWN_CRITICAL');
check('T13 Version.code',     new Version('2.0').code === 'E_WIRE_VERSION');
check('T14 Ambiguous.code',   new Ambiguous('x').code === 'E_WIRE_AMBIGUOUS');

// T15: display includes code
check('T15 Trailing str includes code',
      String(new Trailing(3)).startsWith('E_WIRE_TRAILING'));
check('T16 Trailing str includes count',
      String(new Trailing(3)).includes('3'));

// T17: MissingField str shows name
check('T17 MissingField str includes "binding"',
      String(new MissingField('binding')).includes('binding') &&
      String(new MissingField('binding')).includes('E_WIRE_MISSING_FIELD'));

// T18: Version str shows value
check('T18 Version str includes "9.9"',
      String(new Version('9.9')).includes('9.9') &&
      String(new Version('9.9')).includes('E_WIRE_VERSION'));

// T19: Tag str shows number
check('T19 Tag str includes 42',
      String(new Tag(42)).includes('42') &&
      String(new Tag(42)).includes('E_WIRE_TAG'));

// T20: all inherit CborError
const all = [
  new Malformed(''), new Trailing(0), new Indefinite(), new Float(),
  new Tag(0), new DuplicateKey(), new NonCanonicalInt(), new NonCanonicalMap(),
  new InvalidUtf8(), new TypeMismatch('', ''), new MissingField(''),
  new UnknownCritical(0), new Version(''), new Ambiguous(''),
];
check('T20 all inherit CborError', all.every(e => e instanceof CborError));

console.log();
console.log('='.repeat(72));
console.log(`TOTAL: ${PASS_N + FAIL_N} | PASS: ${PASS_N} | FAIL: ${FAIL_N}`);
console.log('='.repeat(72));

process.exit(FAIL_N === 0 ? 0 : 1);
