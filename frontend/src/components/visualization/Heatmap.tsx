import { useMemo, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

export type HeatmapIntensity = 'none' | 'low' | 'medium' | 'high'

export interface HeatmapCell {
  /** Day index: 0 = Sunday, 6 = Saturday. */
  day: number
  /** Hour of day: 0-23. */
  hour: number
  /** Raw event count, or null when unknown. */
  count: number | null
}

export interface HeatmapProps {
  cells: HeatmapCell[]
  /** Optional accessible name. Falls back to a translated default. */
  ariaLabel?: string
  /** Show the intensity legend below the grid. Default: true. */
  showLegend?: boolean
}

const DAY_KEYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'] as const

/**
 * Classify a count into one of four intensity tiers.
 *
 * Thresholds are fixed (not calculated from the data) so that the same
 * count always yields the same color — a critical requirement for a
 * dashboard where color must be stable across renders and pages.
 */
function intensityFor(count: number | null): HeatmapIntensity {
  if (count === null) return 'none'
  if (count <= 0) return 'none'
  if (count < 5) return 'low'
  if (count < 20) return 'medium'
  return 'high'
}

/**
 * Heatmap — a 7×24 activity density grid.
 *
 * Design:
 *   - Rows are days (Sun → Sat), columns are hours (00 → 23).
 *   - Each cell is colored by intensity class (none/low/medium/high),
 *     never by an interpolated gradient. This makes the visual stable
 *     and testable.
 *   - Missing cells default to intensity=none; the component does not
 *     compute or invent data.
 *   - The grid is a semantic table: `<table>` with proper `<th scope>`
 *     headers, so screen readers can navigate it.
 *
 * In UI-01 the caller supplies an empty cell list; the component renders
 * the structure with all cells in the 'none' state. When the backend
 * arrives, only the `cells` prop changes.
 */
export function Heatmap({
  cells,
  ariaLabel,
  showLegend = true,
}: HeatmapProps): ReactElement {
  const { t } = useTranslation('visualization')

  const cellMap = useMemo(() => {
    const m = new Map<string, number | null>()
    for (const c of cells) {
      m.set(`${c.day}:${c.hour}`, c.count)
    }
    return m
  }, [cells])

  const hasAnyData = useMemo(
    () => cells.some((c) => c.count !== null && c.count > 0),
    [cells],
  )

  if (cells.length === 0 || !hasAnyData) {
    // Still render the grid structure — but every cell is 'none'.
    // This preserves the layout so the user sees the shape of the data
    // even when nothing has arrived yet.
  }

  return (
    <section
      className="eg-heatmap"
      role="region"
      aria-label={ariaLabel ?? (t('heatmap.label') as string)}
      data-testid="eg-heatmap"
    >
      <header className="eg-heatmap__header">
        <h3 className="eg-heatmap__title">{t('heatmap.label')}</h3>
        {!hasAnyData && (
          <span className="eg-heatmap__empty-hint" data-testid="eg-heatmap-empty-hint">
            {t('heatmap.empty')}
          </span>
        )}
      </header>

      <div className="eg-heatmap__scroll">
        <table className="eg-heatmap__grid">
          <caption className="eg-heatmap__caption">{t('heatmap.label')}</caption>
          <thead>
            <tr>
              <th scope="col" className="eg-heatmap__corner" aria-label={t('heatmap.day') as string} />
              {Array.from({ length: 24 }).map((_, h) => (
                <th
                  key={h}
                  scope="col"
                  className="eg-heatmap__hour"
                  aria-label={`${t('heatmap.hour')} ${h}`}
                >
                  {h.toString().padStart(2, '0')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 7 }).map((_, d) => {
              const dayKey = DAY_KEYS[d] ?? 'sun'
              const dayLabel = t(`heatmap.days.${dayKey}`) as string
              return (
                <tr key={d}>
                  <th scope="row" className="eg-heatmap__day">
                    {dayLabel}
                  </th>
                  {Array.from({ length: 24 }).map((_, h) => {
                    const count = cellMap.get(`${d}:${h}`) ?? null
                    const intensity = intensityFor(count)
                    const aria = count === null
                      ? (t('heatmap.cellAriaEmpty', { day: dayLabel, hour: h }) as string)
                      : (t('heatmap.cellAriaLabel', {
                          day: dayLabel,
                          hour: h,
                          count,
                        }) as string)
                    return (
                      <td
                        key={h}
                        className="eg-heatmap__cell"
                        data-intensity={intensity}
                        data-day={d}
                        data-hour={h}
                        data-count={count === null ? undefined : String(count)}
                        aria-label={aria}
                        title={aria}
                      />
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {showLegend && (
        <div className="eg-heatmap__legend" aria-hidden="true">
          <span className="eg-heatmap__legend-label">{t('legend.label')}</span>
          <span className="eg-heatmap__legend-item" data-intensity="none">
            {t('legend.intensity.none')}
          </span>
          <span className="eg-heatmap__legend-item" data-intensity="low">
            {t('legend.intensity.low')}
          </span>
          <span className="eg-heatmap__legend-item" data-intensity="medium">
            {t('legend.intensity.medium')}
          </span>
          <span className="eg-heatmap__legend-item" data-intensity="high">
            {t('legend.intensity.high')}
          </span>
        </div>
      )}
    </section>
  )
}
