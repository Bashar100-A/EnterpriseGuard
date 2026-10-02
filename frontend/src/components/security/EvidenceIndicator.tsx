import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { toneForVerification, type VerificationState } from './tone'

export interface EvidenceIndicatorProps {
  state: VerificationState
  /** Optional count of linked evidence items. */
  count?: number
  /** Optional custom label override. */
  label?: ReactNode
  /** Compact form: dot + count only (no label text). */
  compact?: boolean
  /** Optional title. */
  title?: string
}

/**
 * EvidenceIndicator — states the current status of evidence for a scope.
 *
 * Distinct from VerificationBadge: this component carries evidence-specific
 * context (linked item count) and is the canonical marker used in
 * Evidence, Provenance, and Decision Intelligence workspaces.
 */
export function EvidenceIndicator({
  state,
  count,
  label,
  compact = false,
  title,
}: EvidenceIndicatorProps): ReactElement {
  const { t } = useTranslation('security')
  const tone = toneForVerification(state)
  const text = label ?? t(`evidence.${state}`)
  const showCount = typeof count === 'number' && count >= 0
  const countText = showCount
    ? t('evidence.count', { count, defaultValue: `${count} items` })
    : undefined

  return (
    <span
      className={`eg-evidence ${compact ? 'eg-evidence--compact' : ''}`}
      data-tone={tone}
      data-evidence={state}
      title={title ?? t('evidence.label')}
    >
      <span className="eg-evidence__dot" aria-hidden="true" />
      {!compact && <span className="eg-evidence__label">{text}</span>}
      {showCount && (
        <span className="eg-evidence__count" aria-label={countText}>
          {count}
        </span>
      )}
    </span>
  )
}
