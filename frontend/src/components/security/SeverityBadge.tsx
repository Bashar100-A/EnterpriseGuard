import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from './tone'

export type SeverityLevel = 'info' | 'low' | 'medium' | 'high' | 'critical'

const TONE_BY_SEVERITY: Record<SeverityLevel, SemanticTone> = {
  info: 'info',
  low: 'info',
  medium: 'warning',
  high: 'warning',
  critical: 'critical',
}

export interface SeverityBadgeProps {
  severity: SeverityLevel
  label?: ReactNode
  title?: string
}

/**
 * SeverityBadge — expresses a graded severity (info → critical).
 * Distinct from StatusBadge: severity is ordered, status is categorical.
 */
export function SeverityBadge({
  severity,
  label,
  title,
}: SeverityBadgeProps): ReactElement {
  const { t } = useTranslation('security')
  const tone: SemanticTone = TONE_BY_SEVERITY[severity]
  const text = label ?? t(`severity.${severity}`)

  return (
    <span
      className="eg-badge eg-badge--severity"
      data-tone={tone}
      data-severity={severity}
      title={title}
    >
      <span className="eg-badge__label">{text}</span>
    </span>
  )
}

export function toneForSeverity(severity: SeverityLevel): SemanticTone {
  return TONE_BY_SEVERITY[severity]
}
