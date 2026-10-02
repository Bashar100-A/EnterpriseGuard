import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

export interface ContextStripProps {
  /** Real value from import.meta.env or 'Unknown'. */
  environment?: string
  /** Real region or '—' when unavailable. */
  region?: string
  /** Freshness descriptor. 'Unknown' when unverified. */
  dataFreshness?: string
  /** Last verification descriptor. 'Unknown' when unverified. */
  lastVerification?: string
}

interface CellProps {
  label: string
  value: string
  muted?: boolean
}

function Cell({ label, value, muted = false }: CellProps): ReactElement {
  return (
    <div className="eg-context__cell">
      <span className="eg-context__label">{label}</span>
      <span className={`eg-context__value ${muted ? 'eg-context__value--muted' : ''}`}>
        {value}
      </span>
    </div>
  )
}

/**
 * ContextStrip — horizontal context row above the workspace content.
 * Spec §18. Never invents values: defaults to 'Unknown' when unverified.
 */
export function ContextStrip({
  environment = 'Unknown',
  region = '—',
  dataFreshness = 'Unknown',
  lastVerification = 'Unknown',
}: ContextStripProps): ReactElement {
  const { t } = useTranslation('workspace')

  return (
    <div className="eg-context" role="group" aria-label="Context">
      <Cell label={t('context.environment')} value={environment} />
      <Cell label={t('context.region')} value={region} muted={region === '—'} />
      <Cell
        label={t('context.dataFreshness')}
        value={dataFreshness}
        muted={dataFreshness === 'Unknown'}
      />
      <Cell
        label={t('context.lastVerification')}
        value={lastVerification}
        muted={lastVerification === 'Unknown'}
      />
    </div>
  )
}
