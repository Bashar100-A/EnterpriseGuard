/**
 * Semantic tone — the visual contract of every badge and indicator in ADIE.
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

// ============================================================
// Status ↔ Tone mapping (canonical)
// ============================================================

export type StatusKey =
  | 'verified'
  | 'validated'
  | 'healthy'
  | 'pending'
  | 'proposed'
  | 'information'
  | 'reviewRequired'
  | 'degraded'
  | 'stale'
  | 'policyConflict'
  | 'critical'
  | 'verificationFailed'
  | 'boundaryViolation'
  | 'error'
  | 'unknown'
  | 'unavailable'
  | 'notEvaluated'
  | 'notConnected'

export const TONE_BY_STATUS: Record<StatusKey, SemanticTone> = {
  verified: 'trust',
  validated: 'trust',
  healthy: 'trust',

  pending: 'info',
  proposed: 'info',
  information: 'info',

  reviewRequired: 'warning',
  degraded: 'warning',
  stale: 'warning',
  policyConflict: 'warning',

  critical: 'critical',
  verificationFailed: 'critical',
  boundaryViolation: 'critical',
  error: 'critical',

  unknown: 'unknown',
  unavailable: 'unknown',
  notEvaluated: 'unknown',
  notConnected: 'unknown',
}

export function toneForStatus(status: StatusKey): SemanticTone {
  return TONE_BY_STATUS[status]
}

// ============================================================
// Severity ↔ Tone mapping
// ============================================================

export type SeverityLevel = 'info' | 'low' | 'medium' | 'high' | 'critical'

export const TONE_BY_SEVERITY: Record<SeverityLevel, SemanticTone> = {
  info: 'info',
  low: 'info',
  medium: 'warning',
  high: 'warning',
  critical: 'critical',
}

export function toneForSeverity(severity: SeverityLevel): SemanticTone {
  return TONE_BY_SEVERITY[severity]
}

// ============================================================
// Verification ↔ Tone mapping
// ============================================================

export type VerificationState = 'verified' | 'unverified' | 'invalid' | 'unknown' | 'notAvailable'

export const TONE_BY_VERIFICATION: Record<VerificationState, SemanticTone> = {
  verified: 'trust',
  unverified: 'warning',
  invalid: 'critical',
  unknown: 'unknown',
  notAvailable: 'unknown',
}

export function toneForVerification(state: VerificationState): SemanticTone {
  return TONE_BY_VERIFICATION[state]
}

// ============================================================
// Environment classification (not a tone — a data attribute)
// ============================================================

export type EnvironmentKey = 'production' | 'staging' | 'development' | 'test' | 'unknown'

export const ENVIRONMENT_KEYS: readonly EnvironmentKey[] = [
  'production',
  'staging',
  'development',
  'test',
  'unknown',
] as const

export function isEnvironmentKey(value: unknown): value is EnvironmentKey {
  return (
    value === 'production' ||
    value === 'staging' ||
    value === 'development' ||
    value === 'test' ||
    value === 'unknown'
  )
}
