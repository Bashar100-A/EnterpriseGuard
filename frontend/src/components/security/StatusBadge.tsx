import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from './tone'

/**
 * Canonical status keys. Each maps to a fixed semantic tone.
 * The mapping is a design contract, not a runtime calculation.
 */
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

const TONE_BY_STATUS: Record<StatusKey, SemanticTone> = {
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

export interface StatusBadgeProps {
  status: StatusKey
  /** Optional custom label override. If absent, uses security.status.<key>. */
  label?: ReactNode
  /** Show a leading dot indicator. */
  withDot?: boolean
  /** Optional title attribute for tooltips. */
  title?: string
}

/**
 * StatusBadge — the canonical way to show a semantic state.
 * Data attribute data-tone drives CSS; data-status allows test targeting.
 */
export function StatusBadge({
  status,
  label,
  withDot = false,
  title,
}: StatusBadgeProps): ReactElement {
  const { t } = useTranslation('security')
  const tone: SemanticTone = TONE_BY_STATUS[status]
  const text = label ?? t(`status.${status}`)

  return (
    <span
      className="eg-badge eg-badge--status"
      data-tone={tone}
      data-status={status}
      title={title}
    >
      {withDot && <span className="eg-badge__dot" aria-hidden="true" />}
      <span className="eg-badge__label">{text}</span>
    </span>
  )
}

export function toneForStatus(status: StatusKey): SemanticTone {
  return TONE_BY_STATUS[status]
}
