import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { DecisionChain } from '../../components/security'
import type { ChainStageKey, ChainStage } from '../../components/security'
import { EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn } from '../../components/data-display'
import { StatusBadge, TechnicalIdentifier } from '../../components/security'
import type { StatusKey } from '../../components/security'

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
 * DecisionsPage — UI-01.E.3.
 *
 * The full ADIE pipeline visualized end-to-end:
 *   Evidence → State → Prediction → Policy → Decision → Authority → Manifest → Outcome
 *
 * In UI-01 there is no backend, so all stages are unknown with null counts.
 * The chain is rendered completely — proving that the STRUCTURE works — but
 * no stage is filled with fabricated data.
 *
 * When the backend arrives, this page becomes the live audit surface for
 * every decision ever made.
 */
export function DecisionsPage(): ReactElement {
  const { t } = useTranslation('decisions')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  // No backend in UI-01. All stages default to unknown.
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
