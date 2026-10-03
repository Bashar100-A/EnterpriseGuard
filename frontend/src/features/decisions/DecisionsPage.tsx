import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { DecisionChain } from '../../components/security'
import type { ChainStageKey, ChainStage } from '../../components/security'
import { EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn } from '../../components/data-display'
import { StatusBadge, TechnicalIdentifier } from '../../components/security'
import type { StatusKey } from '../../components/security'
import { RelationshipGraph, SankeyFlow } from '../../components/visualization'
import type {
  GraphNode,
  GraphEdge,
  SankeyNode,
  SankeyLink,
} from '../../components/visualization'

interface DecisionRow {
  id: string
  state: StatusKey
  authority: string
  createdAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

const GRAPH_NODES: GraphNode[] = [
  { id: 'evidence',   label: 'Evidence',   tone: 'unknown', count: null, x: 17, y: 20 },
  { id: 'state',      label: 'State',      tone: 'unknown', count: null, x: 50, y: 20 },
  { id: 'prediction', label: 'Prediction', tone: 'unknown', count: null, x: 83, y: 20 },

  { id: 'policy',     label: 'Policy',     tone: 'unknown', count: null, x: 17, y: 50 },
  { id: 'decision',   label: 'Decision',   tone: 'unknown', count: null, x: 50, y: 50 },
  { id: 'authority',  label: 'Authority',  tone: 'unknown', count: null, x: 83, y: 50 },

  { id: 'manifest',   label: 'Manifest',   tone: 'unknown', count: null, x: 33, y: 80 },
  { id: 'outcome',    label: 'Outcome',    tone: 'unknown', count: null, x: 67, y: 80 },
]

const GRAPH_EDGES: GraphEdge[] = [
  { from: 'evidence',   to: 'state' },
  { from: 'state',      to: 'prediction' },
  { from: 'prediction', to: 'policy' },
  { from: 'policy',     to: 'decision' },
  { from: 'decision',   to: 'authority' },
  { from: 'authority',  to: 'manifest' },
  { from: 'manifest',   to: 'outcome' },
]

/**
 * Sankey nodes for the ADIE pipeline.
 *
 * Layout: 5 columns representing the coarse pipeline:
 *   Evidence (col 0) → State (col 1) → Decision (col 2)
 *     → Authority (col 3) → Outcome (col 4)
 *
 * All node.values are 0 in UI-01 — the Sankey renderer handles the
 * degenerate case (equal heights) gracefully.
 */
const SANKEY_NODES: SankeyNode[] = [
  { id: 'evidence',  label: 'Evidence',  tone: 'unknown', column: 0, value: 0 },
  { id: 'state',     label: 'State',     tone: 'unknown', column: 1, value: 0 },
  { id: 'decision',  label: 'Decision',  tone: 'unknown', column: 2, value: 0 },
  { id: 'authority', label: 'Authority', tone: 'unknown', column: 3, value: 0 },
  { id: 'outcome',   label: 'Outcome',   tone: 'unknown', column: 4, value: 0 },
]

const SANKEY_LINKS: SankeyLink[] = [
  { from: 'evidence',  to: 'state' },
  { from: 'state',     to: 'decision' },
  { from: 'decision',  to: 'authority' },
  { from: 'authority', to: 'outcome' },
].map((l) => ({ ...l, value: 0 }))

/**
 * DecisionsPage — UI-01.E.3 (+ I.1 + I.4).
 *
 * Three complementary views of the ADIE decision pipeline:
 *   1. DecisionChain — linear, tier-based (Observed / Decided / Executed)
 *   2. RelationshipGraph — spatial, node/edge-based
 *   3. SankeyFlow — flow-based, volume between stages
 *
 * All three render placeholder data (all nodes unknown, no counts, no
 * values). The page never fabricates decisions, hashes, or authority.
 */
export function DecisionsPage(): ReactElement {
  const { t } = useTranslation('decisions')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const stages: Partial<Record<ChainStageKey, ChainStage>> = {
    evidence: { status: 'unknown', count: null },
    state: { status: 'unknown', count: null },
    prediction: { status: 'unknown', count: null },
    policy: { status: 'unknown', count: null },
    decision: { status: 'unknown', count: null },
    authority: { status: 'unknown', count: null },
    manifest: { status: 'unknown', count: null },
    outcome: { status: 'unknown', count: null },
  }

  const decisions: DecisionRow[] = []

  const columns: EnterpriseColumn<DecisionRow>[] = [
    {
      key: 'id',
      header: t('table.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={16} />,
    },
    {
      key: 'state',
      header: t('table.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    { key: 'authority', header: t('table.authority') },
    {
      key: 'createdAt',
      header: t('table.createdAt'),
      render: (r) => <span className="eg-mono">{r.createdAt}</span>,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.intelligence') },
    { label: t('title'), current: true },
  ]

  return (
    <>
      <WorkspaceHeader
        breadcrumb={breadcrumb}
        title={t('title')}
        description={t('description')}
        assuranceState="unknown"
        context={
          <ContextStrip
            environment={resolveEnvironment()}
            region="—"
            dataFreshness="Unknown"
            lastVerification="Unknown"
          />
        }
      />

      <section className="eg-decisions__chain" aria-label={t('chain.label')}>
        <DecisionChain stages={stages} />
      </section>

      <section className="eg-decisions__graph">
        <RelationshipGraph nodes={GRAPH_NODES} edges={GRAPH_EDGES} />
      </section>

      <section className="eg-decisions__sankey">
        <SankeyFlow nodes={SANKEY_NODES} links={SANKEY_LINKS} />
      </section>

      <section className="eg-decisions__table">
        <EnterpriseTable<DecisionRow>
          columns={columns}
          rows={decisions}
          getRowKey={(r) => r.id}
          state="empty"
          caption={t('table.caption')}
          emptyMessage={t('table.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
