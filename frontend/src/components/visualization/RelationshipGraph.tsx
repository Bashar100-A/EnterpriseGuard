import { useId, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from '../security/tone'

export interface GraphNode {
  id: string
  /** Localized display label. */
  label: string
  /** Semantic tone — drives the node color. */
  tone: SemanticTone
  /** Optional count badge. null / undefined when unavailable. */
  count?: number | null
  /** X position as percent (0-100). */
  x: number
  /** Y position as percent (0-100). */
  y: number
}

export interface GraphEdge {
  from: string
  to: string
  /** Optional tone for the edge — defaults to 'unknown'. */
  tone?: SemanticTone
}

export interface RelationshipGraphProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  /** Aspect ratio of the SVG viewBox. Default: '16 / 9'. */
  aspect?: string
  /** Accessible name. Falls back to a translated default. */
  ariaLabel?: string
}

const TONE_COLOR: Record<SemanticTone, string> = {
  trust: 'var(--eg-trust-emerald)',
  info: 'var(--eg-signal-blue)',
  warning: 'var(--eg-warning-amber)',
  critical: 'var(--eg-critical-red)',
  unknown: 'var(--eg-unknown-gray)',
}

const NODE_RADIUS = 24

/**
 * RelationshipGraph — renders an arbitrary node/edge graph as SVG.
 *
 * Design principles:
 *   - The caller provides positions (x/y in percent). The component does
 *     not compute a layout. This keeps it pure and testable.
 *   - Nodes are circles with a semantic tone (same 5 tones used
 *     everywhere else in the app).
 *   - Edges are straight lines with an arrow marker.
 *   - No client-side physics, no animation that pretends progress.
 *
 * In UI-01 the caller supplies placeholder positions. When the backend
 * arrives and real relationship data is available, only the props change
 * — never the component.
 */
export function RelationshipGraph({
  nodes,
  edges,
  aspect = '16 / 9',
  ariaLabel,
}: RelationshipGraphProps): ReactElement {
  const { t } = useTranslation('visualization')
  const markerId = useId()

  if (nodes.length === 0) {
    return (
      <div
        className="eg-relgraph eg-relgraph--empty"
        data-testid="eg-relgraph-empty"
      >
        <p className="eg-relgraph__empty">{t('graph.empty')}</p>
      </div>
    )
  }

  const nodeMap = new Map(nodes.map((n) => [n.id, n]))

  return (
    <div
      className="eg-relgraph"
      style={{ aspectRatio: aspect }}
      data-testid="eg-relgraph"
    >
      <svg
        className="eg-relgraph__svg"
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={ariaLabel ?? (t('graph.label') as string)}
      >
        <defs>
          <marker
            id={`arrow-${markerId}`}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="4"
            markerHeight="4"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--eg-text-muted)" />
          </marker>
        </defs>

        {edges.map((edge, i) => {
          const from = nodeMap.get(edge.from)
          const to = nodeMap.get(edge.to)
          if (from === undefined || to === undefined) return null
          const tone = edge.tone ?? 'unknown'
          return (
            <line
              key={`e-${i}`}
              className="eg-relgraph__edge"
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={TONE_COLOR[tone]}
              strokeOpacity={tone === 'unknown' ? 0.3 : 0.55}
              strokeWidth="0.35"
              strokeDasharray={tone === 'unknown' ? '1.2 0.8' : undefined}
              markerEnd={`url(#arrow-${markerId})`}
              data-tone={tone}
              data-from={edge.from}
              data-to={edge.to}
            />
          )
        })}

        {nodes.map((node) => (
          <g
            key={node.id}
            className="eg-relgraph__node"
            transform={`translate(${node.x}, ${node.y})`}
            data-node-id={node.id}
            data-tone={node.tone}
          >
            <circle
              r={NODE_RADIUS}
              fill="var(--eg-bg-surface-2)"
              stroke={TONE_COLOR[node.tone]}
              strokeWidth="0.6"
            />
            <text
              className="eg-relgraph__node-label"
              textAnchor="middle"
              dominantBaseline="middle"
              y="-1"
            >
              {node.label.length > 10 ? node.label.slice(0, 9) + '…' : node.label}
            </text>
            <text
              className="eg-relgraph__node-count"
              textAnchor="middle"
              dominantBaseline="middle"
              y="5"
            >
              {node.count === null || node.count === undefined ? '—' : String(node.count)}
            </text>
          </g>
        ))}
      </svg>

      <div className="eg-relgraph__stats" aria-hidden="true">
        <span className="eg-relgraph__stat">
          <span className="eg-relgraph__stat-label">{t('graph.nodeCount')}</span>
          <span className="eg-relgraph__stat-value">{nodes.length}</span>
        </span>
        <span className="eg-relgraph__stat">
          <span className="eg-relgraph__stat-label">{t('graph.edgeCount')}</span>
          <span className="eg-relgraph__stat-value">{edges.length}</span>
        </span>
      </div>
    </div>
  )
}
