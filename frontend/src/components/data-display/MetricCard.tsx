import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { StateIndicator } from '../security/StateIndicator'
import type { SemanticTone } from '../security/tone'

export type MetricDataState = 'live' | 'stale' | 'unknown' | 'unavailable' | 'notConnected'
export type TrendDirection = 'up' | 'down' | 'flat' | 'unknown'

const TONE_BY_DATA_STATE: Record<MetricDataState, SemanticTone> = {
  live: 'trust',
  stale: 'warning',
  unknown: 'unknown',
  unavailable: 'unknown',
  notConnected: 'unknown',
}

export interface MetricValue {
  /** Numeric value, or null when not available. */
  value: number | null
  /** Optional unit, e.g. "%", "ms", "req/s". */
  unit?: string | undefined
  /** Optional preformatted display string. Overrides numeric rendering. */
  formatted?: string | undefined
}

export interface MetricCardProps {
  label: string
  value: MetricValue
  /** Optional context line under the value. */
  context?: ReactNode
  /** Trend direction. Undefined when not evaluated. */
  trend?: TrendDirection | undefined
  /** Trend delta, e.g., "+3.2%". */
  trendValue?: string | undefined
  /** Timestamp string. Not formatted by this component. */
  timestamp?: string | undefined
  /** Data source state — drives tone and default indicator. */
  dataState?: MetricDataState
  /** Optional action slot (button, link). */
  action?: ReactNode
}

function formatMetricValue(v: MetricValue): string {
  if (v.formatted !== undefined) return v.formatted
  if (v.value === null) return '—'
  return String(v.value)
}

function TrendArrow({ direction }: { direction: TrendDirection }): ReactElement {
  const symbol =
    direction === 'up' ? '↑' :
    direction === 'down' ? '↓' :
    direction === 'flat' ? '→' : '·'
  return <span aria-hidden="true">{symbol}</span>
}

/**
 * MetricCard — displays a single metric with full provenance context.
 *
 * Spec §35. Never a bare "number + title":
 *   Label / Value / Unit / Context / Trend / Timestamp / Data State / Action
 *
 * When value.value === null or dataState !== 'live', the card makes the
 * uncertainty explicit. It never pretends a value is live if it isn't.
 */
export function MetricCard({
  label,
  value,
  context,
  trend,
  trendValue,
  timestamp,
  dataState = 'unknown',
  action,
}: MetricCardProps): ReactElement {
  const { t } = useTranslation('dataDisplay')
  const tone = TONE_BY_DATA_STATE[dataState]
  const displayValue = formatMetricValue(value)
  const isMissing = value.value === null && value.formatted === undefined

  let trendLabel = t('metric.trendUnknown')
  if (trend === 'up') trendLabel = t('metric.trendUp')
  else if (trend === 'down') trendLabel = t('metric.trendDown')
  else if (trend === 'flat') trendLabel = t('metric.trendFlat')

  return (
    <article className="eg-metric" data-state={dataState} aria-label={label}>
      <header className="eg-metric__header">
        <div className="eg-metric__label">{label}</div>
        {action !== undefined && <div className="eg-metric__action">{action}</div>}
      </header>

      <div className="eg-metric__value-row" data-tone={tone}>
        <span
          className={`eg-metric__value ${isMissing ? 'eg-metric__value--missing' : ''}`}
          title={isMissing ? t('metric.noData') : undefined}
        >
          {displayValue}
        </span>
        {value.unit !== undefined && !isMissing && (
          <span className="eg-metric__unit">{value.unit}</span>
        )}
        {trend !== undefined && trend !== 'unknown' && (
          <span className="eg-metric__trend" data-trend={trend} title={trendLabel}>
            <TrendArrow direction={trend} />
            {trendValue !== undefined && (
              <span className="eg-metric__trend-value">{trendValue}</span>
            )}
          </span>
        )}
      </div>

      {context !== undefined && (
        <div className="eg-metric__context">{context}</div>
      )}

      <footer className="eg-metric__footer">
        <StateIndicator tone={tone} label={t(`metric.${dataState}`)} size="sm" />
        {timestamp !== undefined && (
          <span className="eg-metric__timestamp">{timestamp}</span>
        )}
      </footer>
    </article>
  )
}
