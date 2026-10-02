import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { toneForVerification, type VerificationState } from './tone'

export interface VerificationBadgeProps {
  state: VerificationState
  label?: ReactNode
  title?: string
}

/**
 * VerificationBadge — the canonical marker for evidence / integrity state.
 *
 *   verified      — Trust Emerald
 *   unverified    — Warning Amber
 *   invalid       — Critical Red
 *   unknown       — Unknown Gray
 *   notAvailable  — Unknown Gray
 *
 * Distinct from StatusBadge because verification answers a specific question:
 * "has this been proven?"
 */
export function VerificationBadge({
  state,
  label,
  title,
}: VerificationBadgeProps): ReactElement {
  const { t } = useTranslation('security')
  const tone = toneForVerification(state)
  const text = label ?? t(`verification.${state}`)

  return (
    <span
      className="eg-badge eg-badge--verification"
      data-tone={tone}
      data-verification={state}
      title={title}
    >
      <span className="eg-badge__label">{text}</span>
    </span>
  )
}
