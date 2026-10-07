// js/wire/bin/json-io.mjs — BigInt-safe JSON helpers for differentials.
//
// JSON spec cannot represent u64 range as Number. These helpers:
//   - parsePreservingBigInts: mark 16+ digit literals before JSON.parse
//   - stringify:             emit BigInt as plain integer literals
//   - canon:                 unified Number/BigInt for equality comparison

export function parsePreservingBigInts(text) {
  const marked = text.replace(
    /([\[,:]\s*)(-?\d{16,})(?=\s*[,\]}])/g,
    '$1"__BIGINT__$2"'
  );
  return revive(JSON.parse(marked));
}

function revive(x) {
  if (typeof x === 'string' && x.startsWith('__BIGINT__')) {
    return BigInt(x.slice(10));
  }
  if (Array.isArray(x)) return x.map(revive);
  if (x && typeof x === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(x)) out[k] = revive(v);
    return out;
  }
  return x;
}

export function stringify(v) {
  if (v === null) return 'null';
  if (typeof v === 'boolean') return JSON.stringify(v);
  if (typeof v === 'number')  return String(v);
  if (typeof v === 'bigint')  return String(v);
  if (typeof v === 'string')  return JSON.stringify(v);
  if (Array.isArray(v))       return '[' + v.map(stringify).join(',') + ']';
  if (typeof v === 'object') {
    const parts = [];
    for (const [k, val] of Object.entries(v)) {
      parts.push(JSON.stringify(k) + ':' + stringify(val));
    }
    return '{' + parts.join(',') + '}';
  }
  return 'null';
}

// canon: unified serializer for equality. Numbers and BigInts both
// become plain integer literals so 0 and 0n produce identical text.
export function canon(v) {
  if (v === null) return 'null';
  if (typeof v === 'boolean') return String(v);
  if (typeof v === 'number')  return Number.isInteger(v) ? String(v) : JSON.stringify(v);
  if (typeof v === 'bigint')  return v.toString();
  if (typeof v === 'string')  return JSON.stringify(v);
  if (Array.isArray(v))       return '[' + v.map(canon).join(',') + ']';
  if (typeof v === 'object') {
    const keys = Object.keys(v).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}';
  }
  return 'null';
}
