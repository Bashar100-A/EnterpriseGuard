import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

export type AssuranceValueState =
  | 'unknown'
  | 'unavailable'
  | 'notConnected'
  | 'notEvaluated'
  | 'notAuthorized'
  | 'verified'
  | 'unverified'
  | 'stale'
  | 'fresh'

interface SectionProps {
  title: string
  children: ReactNode
}

function Section({ title, children }: SectionProps): ReactElement {
  return (
    <section className="eg-assurance__section">
      <h2 className="eg-assurance__section-title">{title}</h2>
      <div className="eg-assurance__section-body">{children}</div>
    </section>
  )
}

interface ValueProps {
  state: AssuranceValueState
}

/**
 * Value badge — renders a translated state label with a data-state attribute
 * so CSS can color it semantically. No calculation, no inference.
 */
function ValueBadge({ state }: ValueProps): ReactElement {
  const { t } = useTranslation('assurance')
  return (
    <span
      className={`eg-assurance__value eg-assurance__value--${state}`}
      data-state={state}
    >
      {t(`values.${state}`)}
    </span>
  )
}

export interface AssuranceRailProps {
  /** Optional close handler — when provided, a close button is rendered. */
  onClose?: () => void

  /* Values — all default to 'unknown' / 'notConnected' / 'unavailable'.
     These are NOT calculated. They are supplied by whoever wires the rail
     to real backend data in a future phase. */

  systemState?: AssuranceValueState
  dataFreshness?: AssuranceValueState
  evidenceState?: AssuranceValueState
  verification?: AssuranceValueState
  permissions?: AssuranceValueState
  auditReference?: string
}

/**
 * AssuranceRail — contextual, collapsible right-side panel.
 * Spec §44. Pure presentation. All values default to honest 'Unknown'.
 */
export function AssuranceRail({
  onClose,
  systemState = 'unknown',
  dataFreshness = 'unknown',
  evidenceState = 'unknown',
  verification = 'unknown',
  permissions = 'notConnected',
  auditReference,
}: AssuranceRailProps): ReactElement {
  const { t } = useTranslation('assurance')

  return (
    <div className="eg-assurance" role="complementary" aria-label={t('title')}>
      <div className="eg-assurance__header">
        <h2 className="eg-assurance__title">{t('title')}</h2>
        {onClose !== undefined && (
          <button
            type="button"
            className="eg-assurance__close"
            onClick={onClose}
            aria-label={t('toggle.close')}
            title={t('toggle.close')}
          >
            <span aria-hidden="true">×</span>
          </button>
        )}
      </div>

      <div className="eg-assurance__body">
        <Section title={t('sections.systemState')}>
          <ValueBadge state={systemState} />
        </Section>

        <Section title={t('sections.dataFreshness')}>
          <ValueBadge state={dataFreshness} />
        </Section>

        <Section title={t('sections.evidenceState')}>
          <ValueBadge state={evidenceState} />
        </Section>

        <Section title={t('sections.verification')}>
          <ValueBadge state={verification} />
        </Section>

        <Section title={t('sections.permissions')}>
          <ValueBadge state={permissions} />
        </Section>

        <Section title={t('sections.auditReference')}>
          <span
            className={`eg-assurance__value eg-assurance__value--${auditReference === undefined ? 'unavailable' : 'unknown'}`}
            data-state={auditReference === undefined ? 'unavailable' : 'unknown'}
          >
            {auditReference ?? t('values.unavailable')}
          </span>
        </Section>
      </div>

      <div className="eg-assurance__hint">{t('hint.noBackend')}</div>
    </div>
  )
}
