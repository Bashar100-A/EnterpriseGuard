/**
 * Semantic tone — the visual contract of every badge and indicator in ADIE.
 * Colors are never arbitrary; each tone carries a precise meaning.
 *
 *   trust    — Verified, Integrity Confirmed, Validated, Healthy
 *   info     — Information, Pending, Proposed, Neutral actions
 *   warning  — Review Required, Degraded, Attention, Stale, Policy Conflict
 *   critical — Confirmed Critical, Verification Failure, Boundary Violation
 *   unknown  — Unknown, Unavailable, No Evidence, Not Evaluated, Not Connected
 *
 * Rule: unknown NEVER maps to trust silently.
 */
export type SemanticTone = 'trust' | 'info' | 'warning' | 'critical' | 'unknown'

export const SEMANTIC_TONES: readonly SemanticTone[] = [
  'trust',
  'info',
  'warning',
  'critical',
  'unknown',
] as const
