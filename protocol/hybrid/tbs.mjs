/**
 * ADIE hybrid signing — TBS builder (JavaScript).
 * Must produce byte-identical output to protocol/hybrid/tbs.py.
 *
 * spec/HYBRID-CRYPTO-0.1.md §5:
 *     TBS = "ADIE-SIG-V2\0" || JCS(certificate_without_signatures)
 */
import { canonicalBytes } from '../core/claim_root.mjs';

// Exact 12-byte domain tag.
export const DOMAIN_TAG = new Uint8Array([
  0x41, 0x44, 0x49, 0x45, 0x2d, 0x53,
  0x49, 0x47, 0x2d, 0x56, 0x32, 0x00,
]);

if (DOMAIN_TAG.length !== 12) {
  throw new Error('domain tag must be 12 bytes');
}

/**
 * Build the ADIE v2 To-Be-Signed byte sequence.
 * @param {object} certWithoutSignatures - cert dict without signatures/signature field.
 * @returns {Buffer}
 */
export function buildTbs(certWithoutSignatures) {
  if (typeof certWithoutSignatures !== 'object'
      || certWithoutSignatures === null
      || Array.isArray(certWithoutSignatures)) {
    throw new TypeError('certificate must be a plain object');
  }
  if ('signatures' in certWithoutSignatures) {
    throw new Error("cert has 'signatures' field; remove it before calling buildTbs");
  }
  if ('signature' in certWithoutSignatures) {
    throw new Error("cert has 'signature' field; remove it before calling buildTbs");
  }
  const body = canonicalBytes(certWithoutSignatures);
  return Buffer.concat([Buffer.from(DOMAIN_TAG), body]);
}
