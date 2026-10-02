import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { EnvironmentKey } from './tone'

export interface EnvironmentBadgeProps {
  environment: EnvironmentKey
  label?: ReactNode
  title?: string
}

/**
 * EnvironmentBadge — identifies the deployment environment.
 *
 * Not a semantic tone: environment is a fact, not a judgment.
 * Production is styled with a subtle accent to signal caution,
 * but it is NOT rendered as tone=warning (that would dilute the
 * meaning of warning for actual problems).
 */
export function EnvironmentBadge({
  environment,
  label,
  title,
}: EnvironmentBadgeProps): ReactElement {
  const { t } = useTranslation('security')
  const text = label ?? t(`environment.${environment}`)
  return (
    <span
      className="eg-badge eg-badge--environment"
      data-environment={environment}
      title={title ?? t('environment.label')}
    >
      <span className="eg-badge__label">{text}</span>
    </span>
  )
}
