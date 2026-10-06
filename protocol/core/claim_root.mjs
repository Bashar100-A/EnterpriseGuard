/**
 * ADIE vΩ — JavaScript mirror of protocol/core/claim_root.py.
 * MUST produce byte-identical digest to Python on every input.
 */
import { createHash } from 'node:crypto';

const DOMAIN_PREFIX = Buffer.from('ADIE/vOmega/2/', 'utf-8');
function hA(t, x) {
  const tb = Buffer.from(t, 'utf-8');
  const lenBuf = Buffer.alloc(2);
  lenBuf.writeUInt16BE(tb.length, 0);
  return createHash('sha256')
    .update(DOMAIN_PREFIX).update(lenBuf).update(tb).update(x).digest();
}

function stableStringify(x) {
  if (x === null) return 'null';
  if (typeof x === 'boolean') return x ? 'true' : 'false';
  if (typeof x === 'number') {
    if (!Number.isFinite(x)) throw new Error('non-finite');
    return JSON.stringify(x);
  }
  if (typeof x === 'string') return JSON.stringify(x);
  if (Array.isArray(x)) return '[' + x.map(stableStringify).join(',') + ']';
  if (typeof x === 'object') {
    const keys = Object.keys(x).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + stableStringify(x[k])).join(',') + '}';
  }
  throw new Error('unexpected type');
}

function canonicalBytes(x) {
  return Buffer.from(stableStringify(x), 'utf-8');
}

const FIELD_NAMES_13 = [
  'issuer','subject','request','context','policy','model','data',
  'runtime','output','binding','temporal','evidence','authoring',
];
const FIELD_ORDER_14 = [...FIELD_NAMES_13, 'proof-set'];

const STATUS_ABSENT = 0x00, STATUS_PRESENT = 0x01, STATUS_NULL = 0x02;

function leaf(fid, status, canonical) {
  const idBuf = Buffer.alloc(2); idBuf.writeUInt16BE(fid, 0);
  const lenBuf = Buffer.alloc(4); lenBuf.writeUInt32BE(canonical.length, 0);
  const body = Buffer.concat([idBuf, Buffer.from([status]), lenBuf, canonical]);
  return hA('leaf', body);
}
function paddingLeaf() { return hA('padding', Buffer.alloc(0)); }
function parentNode(l, r) { return hA('node', Buffer.concat([l, r])); }

export function computeClaimRoot(fields) {
  const leaves = [];
  for (let i = 0; i < FIELD_ORDER_14.length; i++) {
    const name = FIELD_ORDER_14[i];
    const fid = i + 1;
    if (!(name in fields)) {
      leaves.push(leaf(fid, STATUS_ABSENT, Buffer.alloc(0)));
      continue;
    }
    const v = fields[name];
    if (v === null || v === undefined) {
      leaves.push(leaf(fid, STATUS_NULL, Buffer.alloc(0)));
      continue;
    }
    leaves.push(leaf(fid, STATUS_PRESENT, canonicalBytes(v)));
  }
  let n = 1; while (n < leaves.length) n *= 2;
  const pad = paddingLeaf();
  while (leaves.length < n) leaves.push(pad);
  let level = leaves;
  while (level.length > 1) {
    const nxt = [];
    for (let i = 0; i < level.length; i += 2)
      nxt.push(parentNode(level[i], level[i + 1]));
    level = nxt;
  }
  return level[0];
}

export function claimRootHex(fields) {
  return 'sha256:' + computeClaimRoot(fields).toString('hex');
}
