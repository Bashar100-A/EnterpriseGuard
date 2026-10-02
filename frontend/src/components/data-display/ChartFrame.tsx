import { useState, type ReactElement, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { StateIndicator } from '../security/StateIndicator'
import type { SemanticTone } from '../security/tone'

export type ChartState =
  | 'loading'
  | 'ready'
  | 'empty'
  | 'partial'
  | 'stale'
  | 'error'
  | 'unavailable'
  | 'permissionDenied'

const TONE_BY_STATE: Record<ChartState, SemanticTone> = {
  loading: 'info',
  ready: 'trust',
  empty: 'unknown',
  partial: 'warning',
  stale: 'warning',
  error: 'critical',
  unavailable: 'unknown',
  permissionDenied: 'unknown',
}

export interface ChartFrameProps {
  title: string
  state: ChartState
  children?: ReactNode
  subtitle?: ReactNode
  actions?: ReactNode
  onRetry?: (() => void) | undefined
  timestamp?: string | undefined
  height?: number
}

function Placeholder({
  title,
  hint,
  tone,
  onRetry,
  retryLabel,
}: {
  title: string
  hint: string
  tone: SemanticTone
  onRetry?: (() => void) | undefined
  retryLabel: string
}): ReactElement {
  return (
    <div className="eg-chartframe__placeholder" data-tone={tone} role="status">
      <div className="eg-chartframe__placeholder-title">{title}</div>
      {hint !== '' && (
        <div className="eg-chartframe__placeholder-hint">{hint}</div>
      )}
      {onRetry !== undefined && (
        <button type="button" className="eg-chartframe__retry" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  )
}

/**
 * ChartFrame — a wrapper for any chart renderer.
 *
 * Spec §36. Ensures consistent chart states across the app.
 *
 * children are rendered ONLY when state is 'ready' or 'partial'.
 * The footer StateIndicator uses short labels (chart.state.*) to avoid
 * duplicating the full placeholder message in the DOM.
 */
export function ChartFrame({
  title,
  state,
  children,
  subtitle,
  actions,
  onRetry,
  timestamp,
  height = 280,
}: ChartFrameProps): ReactElement {
  const { t } = useTranslation('dataDisplay')
  const [expanded, setExpanded] = useState(false)
  const tone = TONE_BY_STATE[state]
  const showChart = state === 'ready' || state === 'partial'
  const showPartialBanner = state === 'partial' && showChart

  // Short state label for the indicator (distinct from placeholder text).
  const stateLabel = t(`chart.state.${state}`) as string

  // Long descriptive message for the placeholder.
  const placeholderTitle = t(`chart.frame.${state}`) as string
  const placeholderHint = t(`chart.frame.${state}Hint`, { defaultValue: '' }) as string
  const retryLabel = t('chart.actions.retry') as string

  return (
    <section
      className={`eg-chartframe ${expanded ? 'eg-chartframe--expanded' : ''}`}
      data-state={state}
      aria-label={title}
    >
      <header className="eg-chartframe__header">
        <div className="eg-chartframe__titles">
          <h3 className="eg-chartframe__title">{title}</h3>
          {subtitle !== undefined && (
            <div className="eg-chartframe__subtitle">{subtitle}</div>
          )}
        </div>
        <div className="eg-chartframe__header-side">
          {actions !== undefined && (
            <div className="eg-chartframe__actions">{actions}</div>
          )}
          <button
            type="button"
            className="eg-chartframe__expand"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            aria-label={
              expanded
                ? (t('chart.actions.collapse') as string)
                : (t('chart.actions.expand') as string)
            }
            title={
              expanded
                ? (t('chart.actions.collapse') as string)
                : (t('chart.actions.expand') as string)
            }
          >
            <span aria-hidden="true">{expanded ? '⤡' : '⤢'}</span>
          </button>
        </div>
      </header>

      {showPartialBanner && (
        <div className="eg-chartframe__banner" role="note">
          <span className="eg-chartframe__banner-title">
            {t('chart.frame.partial')}
          </span>
          <span className="eg-chartframe__banner-hint">
            {t('chart.frame.partialHint')}
          </span>
        </div>
      )}

      <div
        className="eg-chartframe__body"
        style={{ minHeight: `${height}px` }}
      >
        {showChart ? (
          children
        ) : (
          <Placeholder
            title={placeholderTitle}
            hint={placeholderHint}
            tone={tone}
            onRetry={state === 'error' ? onRetry : undefined}
            retryLabel={retryLabel}
          />
        )}
      </div>

      <footer className="eg-chartframe__footer">
        <StateIndicator tone={tone} label={stateLabel} size="sm" />
        {timestamp !== undefined && (
          <span className="eg-chartframe__timestamp">{timestamp}</span>
        )}
      </footer>
    </section>
  )
}
