/**
 * UI-01.J.5 — Unified error shape.
 *
 * Semantic rules (ADIE):
 *   - The classifier NEVER fabricates a cause. If we don't know, it's 'unknown'.
 *   - 'not-connected' is distinct from 'network' (different user action).
 *   - Messages come from i18n keys; no English strings are stored here.
 */

export type ErrorKind =
  | 'network'
  | 'timeout'
  | 'auth'
  | 'validation'
  | 'not-found'
  | 'server'
  | 'not-connected'
  | 'unknown'

export type SuggestedAction =
  | 'retry'
  | 'reauthenticate'
  | 'fix-input'
  | 'navigate-back'
  | 'wait-and-retry'
  | 'connect-backend'
  | 'contact-admin'
  | 'none'

export interface ClassifiedError {
  kind: ErrorKind
  key: string         // i18n key under 'errors' namespace, e.g. 'api.network'
  action: SuggestedAction
  status: number | null
  requestId: string | null
  raw: unknown
}
