import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { DecisionChain } from '../../components/security'
import type { ChainStageKey, ChainStage } from '../../components/security'
import { EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn } from '../../components/data-display'
import { StatusBadge, TechnicalIdentifier } from '../../components/security'
import type { StatusKey } from '../../components/security'
import { RelationshipGraph } from '../../components/visualization'
import type { GraphNode, GraphEdge } from '../../components/visualization'

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

/**
 * Positions for the 8-stage ADIE pipeline rendered as a graph.
 * Three tiers stacked vertically:
 *   y=20  Observed   — Evidence, State, Prediction
 *   y=50  Decided    — Policy, Decision, Authority
 *   y=80  Executed   — Manifest, Outcome
 */
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
 * DecisionsPage — UI-01.E.3 (+ I.1).
 *
 * Shows the full ADIE pipeline in two complementary views:
 *   1. DecisionChain — linear, tier-based (Observed / Decided / Executed)
 *   2. RelationshipGraph — spatial, node/edge-based
 *
 * Both views render placeholder data (all nodes unknown, no counts).
 * No fake hashes. No fake decisions. No fake authority.
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
