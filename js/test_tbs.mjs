#!/usr/bin/env node
import { DOMAIN_TAG, buildTbs } from '../protocol/hybrid/tbs.mjs';

let P = 0, F = 0;
const check = (name, cond, detail = '') => {
  if (cond) { P++; console.log(`[PASS] ${name}`); }
  else { F++; console.log(`[FAIL] ${name}: ${detail}`); }
};

check('T01 domain tag = 12 bytes', DOMAIN_TAG.length === 12);
check('T02 domain tag exact',
  Buffer.from(DOMAIN_TAG).toString('hex') === '414449452d5349472d563200');

const tbs = buildTbs({ dcp_version: '2.1', claim_id: 'c1' });
const tagBuf = Buffer.from(DOMAIN_TAG);
check('T03 starts with tag', tbs.subarray(0, 12).equals(tagBuf));
check('T04 body is JCS',
  tbs.subarray(12).toString() === '{"claim_id":"c1","dcp_version":"2.1"}',
  `got ${tbs.subarray(12).toString()}`);

let threw = false;
try { buildTbs({ signatures: [] }); } catch (e) { threw = true; }
check('T05 reject signatures field', threw);

threw = false;
try { buildTbs({ signature: {} }); } catch (e) { threw = true; }
check('T06 reject signature field', threw);

check('T07 empty dict',
  buildTbs({}).toString() === Buffer.concat([tagBuf, Buffer.from('{}')]).toString());

check('T08 Unicode',
  buildTbs({ note: 'café' }).subarray(12).toString('utf-8') === '{"note":"café"}');

check('T09 nested sorted',
  buildTbs({ b: { y: 1, x: 2 }, a: 3 }).subarray(12).toString()
    === '{"a":3,"b":{"x":2,"y":1}}');

threw = false;
try { buildTbs([]); } catch (e) { threw = true; }
check('T10 reject non-dict', threw);

const c = { dcp_version: '2.1', claim_id: 'c1' };
check('T11 determinism', buildTbs(c).equals(buildTbs(c)));

console.log();
console.log(`TOTAL: ${P + F} | PASS: ${P} | FAIL: ${F}`);
process.exit(F === 0 ? 0 : 1);
