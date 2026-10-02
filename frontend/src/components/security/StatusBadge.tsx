import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { toneForStatus, type StatusKey } from './tone'

export interface StatusBadgeProps {
  status: StatusKey
  label?: ReactNode
  withDot?: boolean
  title?: string
}

/**
 * StatusBadge — the canonical way to show a categorical semantic state.
 * Colors are driven by data-tone; the mapping is defined in tone.ts.
 */
export function StatusBadge({
  status,
  label,
  withDot = false,
  title,
}: StatusBadgeProps): ReactElement {
  const { t } = useTranslation('security')
  const tone = toneForStatus(status)
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
