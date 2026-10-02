import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { toneForSeverity, type SeverityLevel } from './tone'

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
  const tone = toneForSeverity(severity)
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
