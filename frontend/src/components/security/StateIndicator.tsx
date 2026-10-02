import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from './tone'

export interface StateIndicatorProps {
  tone: SemanticTone
  /** Text label rendered next to the dot. */
  label: ReactNode
  /** Size of the dot: 'sm' (6px) | 'md' (8px) | 'lg' (10px). */
  size?: 'sm' | 'md' | 'lg'
  /** Optional title for tooltips. */
  title?: string
}

/**
 * StateIndicator — a colored dot + label, for compact contexts
 * (tables, lists, dense headers) where a full StatusBadge is too heavy.
 *
 * Distinct from StatusBadge: no border, no pill — just dot + text.
 */
export function StateIndicator({
  tone,
  label,
  size = 'md',
  title,
}: StateIndicatorProps): ReactElement {
  const { t } = useTranslation('security')
  return (
    <span
      className="eg-indicator"
      data-tone={tone}
      data-size={size}
      title={title ?? t('indicator.label')}
    >
      <span className="eg-indicator__dot" aria-hidden="true" />
      <span className="eg-indicator__label">{label}</span>
    </span>
  )
}
