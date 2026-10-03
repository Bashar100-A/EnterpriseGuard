import { useMemo, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from '../security/tone'

export interface SankeyNode {
  id: string
  /** Localized display label. */
  label: string
  /** Semantic tone — drives the node bar color. */
  tone: SemanticTone
  /** Column index (0-based). Nodes in the same column stack vertically. */
  column: number
  /** Explicit node height contribution (e.g., total flow). Optional. */
  value?: number
}

export interface SankeyLink {
  from: string
  to: string
  /** Link magnitude. Drives thickness. */
  value: number
  /** Semantic tone — defaults to 'unknown'. */
  tone?: SemanticTone
}

export interface SankeyFlowProps {
  nodes: SankeyNode[]
  links: SankeyLink[]
  /** Optional accessible name. Falls back to a translated default. */
  ariaLabel?: string
  /** Vertical padding between nodes in the same column. Default: 4. */
  nodePadding?: number
  /** Max node height in viewBox units. Default: 80. */
  maxNodeHeight?: number
}

const TONE_COLOR: Record<SemanticTone, string> = {
  trust: 'var(--eg-trust-emerald)',
  info: 'var(--eg-signal-blue)',
  warning: 'var(--eg-warning-amber)',
  critical: 'var(--eg-critical-red)',
  unknown: 'var(--eg-unknown-gray)',
}

const VIEWBOX_W = 100
const VIEWBOX_H = 100
const NODE_BAR_W = 4

/**
 * Compute node positions and heights.
 *
 * Layout algorithm (deterministic, no physics):
 *   1. Group nodes by column.
 *   2. Each column occupies an evenly spaced x position.
 *   3. Within a column, distribute heights proportionally to node.value
 *      (or equally if value is undefined).
 *   4. Stack them vertically with nodePadding between.
 */
interface PositionedNode extends SankeyNode {
  x: number
  y: number
  h: number
  totalValue: number
}

function layout(nodes: SankeyNode[], padding: number, maxH: number): {
  positioned: Map<string, PositionedNode>
  columns: number
} {
  const byColumn = new Map<number, SankeyNode[]>()
  let maxColumn = 0
  for (const n of nodes) {
    const arr = byColumn.get(n.column) ?? []
    arr.push(n)
    byColumn.set(n.column, arr)
    if (n.column > maxColumn) maxColumn = n.column
  }

  const columns = maxColumn + 1
  const positioned = new Map<string, PositionedNode>()

  for (const [col, list] of byColumn.entries()) {
    const x = columns === 1
      ? VIEWBOX_W / 2
      : (col / (columns - 1)) * (VIEWBOX_W - NODE_BAR_W) + NODE_BAR_W / 2

    const values = list.map((n) => n.value ?? 0)
    const sum = values.reduce((a, b) => a + b, 0)
    const totalHeight = VIEWBOX_H - padding * (list.length - 1)

    let y = 0
    for (let i = 0; i < list.length; i++) {
      const node = list[i]
      if (node === undefined) continue
      const v = node.value ?? 0
      let h: number
      if (sum > 0) {
        h = (v / sum) * totalHeight
      } else {
        h = totalHeight / list.length
      }
      if (h > maxH) h = maxH
      positioned.set(node.id, {
        ...node,
        x,
        y: y + h / 2,
        h,
        totalValue: v,
      })
      y += h + padding
    }
  }

  return { positioned, columns }
}

/**
 * Build an SVG path for a link between two positioned nodes.
 * Uses cubic bezier for smooth flow.
 */
function linkPath(from: PositionedNode, to: PositionedNode): string {
  const x1 = from.x + NODE_BAR_W / 2
  const y1 = from.y
  const x2 = to.x - NODE_BAR_W / 2
  const y2 = to.y
  const cx = (x1 + x2) / 2
  return `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`
}

/**
 * SankeyFlow — a flow diagram showing volume between stages.
 *
 * Design:
 *   - Nodes are vertical bars at column positions.
 *   - Links are bezier curves with thickness proportional to value.
 *   - No physics, no animation that pretends progress.
 *   - The component does NOT compute layout beyond a fixed column-based
 *     algorithm. Positions are deterministic and reproducible.
 *
 * The component renders an empty state when there are no nodes.
 */
export function SankeyFlow({
  nodes,
  links,
  ariaLabel,
  nodePadding = 4,
  maxNodeHeight = 80,
}: SankeyFlowProps): ReactElement {
  const { t } = useTranslation('visualization')

  const { positioned, columns } = useMemo(
    () => layout(nodes, nodePadding, maxNodeHeight),
    [nodes, nodePadding, maxNodeHeight],
  )

  const validLinks = useMemo(
    () =>
      links.filter((l) => positioned.has(l.from) && positioned.has(l.to)),
    [links, positioned],
  )

  const maxLinkValue = useMemo(
    () => validLinks.reduce((m, l) => Math.max(m, l.value), 0),
    [validLinks],
  )

  const totalFlow = useMemo(
    () => validLinks.reduce((s, l) => s + l.value, 0),
    [validLinks],
  )

  if (nodes.length === 0) {
    return (
      <div
        className="eg-sankey eg-sankey--empty"
        data-testid="eg-sankey-empty"
      >
        <p className="eg-sankey__empty">{t('sankey.empty')}</p>
      </div>
    )
  }

  return (
    <section
      className="eg-sankey"
      role="region"
      aria-label={ariaLabel ?? (t('sankey.label') as string)}
      data-testid="eg-sankey"
      data-columns={columns}
    >
      <header className="eg-sankey__header">
        <h3 className="eg-sankey__title">{t('sankey.label')}</h3>
        <div className="eg-sankey__stats">
          <span className="eg-sankey__stat">
            <span className="eg-sankey__stat-label">{t('sankey.nodeCount')}</span>
            <span className="eg-sankey__stat-value">{nodes.length}</span>
          </span>
          <span className="eg-sankey__stat">
            <span className="eg-sankey__stat-label">{t('sankey.linkCount')}</span>
            <span className="eg-sankey__stat-value">{validLinks.length}</span>
          </span>
          <span className="eg-sankey__stat">
            <span className="eg-sankey__stat-label">{t('sankey.totalFlow')}</span>
            <span className="eg-sankey__stat-value">{totalFlow}</span>
          </span>
        </div>
      </header>

      <div className="eg-sankey__svg-wrap">
        <svg
          className="eg-sankey__svg"
          viewBox={`0 0 ${VIEWBOX_W} ${VIEWBOX_H}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={ariaLabel ?? (t('sankey.label') as string)}
        >
          {/* Links first so nodes render on top */}
          {validLinks.map((link, i) => {
            const from = positioned.get(link.from)
            const to = positioned.get(link.to)
            if (from === undefined || to === undefined) return null
            const tone = link.tone ?? 'unknown'
            const strokeW = maxLinkValue > 0
              ? Math.max(0.4, (link.value / maxLinkValue) * 3)
              : 0.6
            const fromLabel = from.label
            const toLabel = to.label
            return (
              <path
                key={`l-${i}`}
                className="eg-sankey__link"
                d={linkPath(from, to)}
                stroke={TONE_COLOR[tone]}
                strokeOpacity={tone === 'unknown' ? 0.35 : 0.55}
                strokeWidth={strokeW}
                fill="none"
                data-from={link.from}
                data-to={link.to}
                data-tone={tone}
                data-value={link.value}
                aria-label={
                  t('sankey.linkAriaLabel', {
                    from: fromLabel,
                    to: toLabel,
                    value: link.value,
                  }) as string
                }
              />
            )
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = positioned.get(node.id)
            if (pos === undefined) return null
            return (
              <g
                key={node.id}
                className="eg-sankey__node"
                data-node-id={node.id}
                data-tone={node.tone}
              >
                <rect
                  x={pos.x - NODE_BAR_W / 2}
                  y={pos.y - pos.h / 2}
                  width={NODE_BAR_W}
                  height={pos.h}
                  rx={0.5}
                  fill={TONE_COLOR[node.tone]}
                  stroke={TONE_COLOR[node.tone]}
                  strokeWidth="0.3"
                />
                <text
                  className="eg-sankey__node-label"
                  x={pos.x}
                  y={pos.y + pos.h / 2 + 3}
                  textAnchor="middle"
                  dominantBaseline="hanging"
                >
                  {node.label}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </section>
  )
}
