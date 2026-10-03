import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from '../security/tone'

export interface RadarDimension {
  id: string
  /** Localized display label. */
  label: string
  /** Score 0..max. Use null when the value is unknown/unavailable. */
  score: number | null
  /** Semantic tone — drives the polygon color. Default: 'unknown'. */
  tone?: SemanticTone
}

export interface RadarDimensionsProps {
  dimensions: RadarDimension[]
  /** Max score on each axis. Default: 100. */
  max?: number
  /** Optional accessible name. Falls back to a translated default. */
  ariaLabel?: string
  /** SVG viewBox size. Default: 200. */
  size?: number
}

const TONE_COLOR: Record<SemanticTone, string> = {
  trust: 'var(--eg-trust-emerald)',
  info: 'var(--eg-signal-blue)',
  warning: 'var(--eg-warning-amber)',
  critical: 'var(--eg-critical-red)',
  unknown: 'var(--eg-unknown-gray)',
}

const RADIUS = 80
const LABEL_RADIUS = 95
const RING_COUNT = 4

/**
 * RadarDimensions — a polygon "spider" chart showing one score per axis.
 *
 * Design:
 *   - N axes evenly spaced around a circle (N = dimensions.length).
 *   - 4 concentric guide rings at 25%, 50%, 75%, 100% of max.
 *   - Each dimension's score is plotted at score/max along its axis.
 *   - The resulting polygon is filled with a semi-transparent color.
 *
 * When `dimensions` is empty, an empty state is rendered. When a
 * dimension's score is null, its axis is drawn but the vertex sits at
 * the center (0) — the axis remains visible so the "missing" state is
 * clear rather than hidden.
 */
export function RadarDimensions({
  dimensions,
  max = 100,
  ariaLabel,
  size = 200,
}: RadarDimensionsProps): ReactElement {
  const { t } = useTranslation('visualization')

  if (dimensions.length === 0) {
    return (
      <div
        className="eg-radar eg-radar--empty"
        data-testid="eg-radar-empty"
      >
        <p className="eg-radar__empty">{t('radar.empty')}</p>
      </div>
    )
  }

  const N = dimensions.length
  const center = size / 2
  const safeMax = max > 0 ? max : 1

  /** Angle for axis i (starting from top, going clockwise). */
  const angleFor = (i: number): number => (Math.PI * 2 * i) / N - Math.PI / 2

  /** Point at radius r on axis i. */
  const pointAt = (i: number, r: number): [number, number] => {
    const a = angleFor(i)
    return [center + r * Math.cos(a), center + r * Math.sin(a)]
  }

  // Polygon vertices from the scores.
  const vertices = dimensions.map((d, i) => {
    const score = d.score === null ? 0 : Math.max(0, Math.min(d.score, safeMax))
    const r = (score / safeMax) * RADIUS
    return pointAt(i, r)
  })

  const polygonPoints = vertices.map(([x, y]) => `${x},${y}`).join(' ')

  // Compute average of numeric scores only.
  const numericScores = dimensions
    .map((d) => d.score)
    .filter((s): s is number => s !== null)
  const avg =
    numericScores.length === 0
      ? null
      : Math.round(
          numericScores.reduce((a, b) => a + b, 0) / numericScores.length,
        )

  // Tone for the polygon: if all known dimensions are 'unknown', use unknown.
  // Otherwise take the most "worrying" tone among known dimensions.
  const order = ['critical', 'warning', 'info', 'trust'] as const
  const knownTones = dimensions
    .map((d) => d.tone ?? 'unknown')
    .filter((tone) => tone !== 'unknown')
  const polygonTone: SemanticTone =
    knownTones.length === 0
      ? 'unknown'
      : (order.find((t) => knownTones.includes(t)) ?? 'unknown')

  return (
    <section
      className="eg-radar"
      role="region"
      aria-label={ariaLabel ?? (t('radar.label') as string)}
      data-testid="eg-radar"
      data-dimensions={N}
    >
      <header className="eg-radar__header">
        <h3 className="eg-radar__title">{t('radar.label')}</h3>
        <div className="eg-radar__stats">
          <span className="eg-radar__stat">
            <span className="eg-radar__stat-label">{t('radar.dimensionCount')}</span>
            <span className="eg-radar__stat-value">{N}</span>
          </span>
          <span className="eg-radar__stat">
            <span className="eg-radar__stat-label">{t('radar.avgScore')}</span>
            <span className="eg-radar__stat-value">
              {avg === null ? '—' : String(avg)}
            </span>
          </span>
        </div>
      </header>

      <div className="eg-radar__svg-wrap">
        <svg
          className="eg-radar__svg"
          viewBox={`0 0 ${size} ${size}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={ariaLabel ?? (t('radar.label') as string)}
        >
          {/* Guide rings */}
          {Array.from({ length: RING_COUNT }).map((_, i) => {
            const r = (RADIUS / RING_COUNT) * (i + 1)
            const pts = Array.from({ length: N }).map((_, j) =>
              pointAt(j, r).join(','),
            )
            return (
              <polygon
                key={`ring-${i}`}
                className="eg-radar__ring"
                points={pts.join(' ')}
                fill="none"
                stroke="var(--eg-border-subtle)"
                strokeWidth="0.5"
              />
            )
          })}

          {/* Axes lines */}
          {dimensions.map((d, i) => {
            const [x, y] = pointAt(i, RADIUS)
            return (
              <line
                key={`axis-${d.id}`}
                className="eg-radar__axis"
                x1={center}
                y1={center}
                x2={x}
                y2={y}
                stroke="var(--eg-border-subtle)"
                strokeWidth="0.5"
              />
            )
          })}

          {/* Data polygon */}
          <polygon
            className="eg-radar__polygon"
            data-tone={polygonTone}
            points={polygonPoints}
            fill={TONE_COLOR[polygonTone]}
            fillOpacity={0.18}
            stroke={TONE_COLOR[polygonTone]}
            strokeWidth="1"
          />

          {/* Vertex dots + axis labels */}
          {dimensions.map((d, i) => {
            const [vx, vy] = vertices[i] ?? [center, center]
            const [lx, ly] = pointAt(i, LABEL_RADIUS)
            const tone = d.tone ?? 'unknown'
            const displayScore =
              d.score === null
                ? (t('radar.unavailable') as string)
                : `${d.score}/${safeMax}`
            return (
              <g key={`vx-${d.id}`} className="eg-radar__vertex-group">
                <circle
                  cx={vx}
                  cy={vy}
                  r={2.5}
                  fill={TONE_COLOR[tone]}
                  stroke="var(--eg-bg-surface-1)"
                  strokeWidth="0.8"
                />
                <text
                  className="eg-radar__label"
                  x={lx}
                  y={ly}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  data-testid={`eg-radar-label-${d.id}`}
                  aria-label={
                    t('radar.axisAriaLabel', {
                      label: d.label,
                      score: d.score === null ? '—' : d.score,
                      max: safeMax,
                    }) as string
                  }
                >
                  {d.label}
                </text>
                <text
                  className="eg-radar__score"
                  x={lx}
                  y={ly + 9}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  data-testid={`eg-radar-score-${d.id}`}
                >
                  {displayScore}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </section>
  )
}
