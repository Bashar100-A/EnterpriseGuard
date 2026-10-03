import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { MetricCard, EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import {
  StatusBadge,
  TechnicalIdentifier,
} from '../../components/security'
import type { StatusKey } from '../../components/security'

interface ManifestRow {
  id: string
  intent: string
  state: StatusKey
  requestedBy: string
  requestedAt: string
}

interface ExecutionRow {
  manifestId: string
  outcome: string
  state: StatusKey
  executedAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * ManifestsPage — UI-01.G.5.
 *
 * Execution Manifests — the boundary between "decided" and "executed".
 *
 * A manifest is a PLAN. It is not an execution. This page shows:
 *   - Manifests: what was planned
 *   - Executions: what actually happened
 *
 * Keeping these two distinct is a core ADIE invariant:
 *   Decided ≠ Executed
 *
 * In UI-01 there is no backend, so both tables remain empty.
 */
export function ManifestsPage(): ReactElement {
  const { t } = useTranslation('manifests')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const manifests: ManifestRow[] = []
  const executions: ExecutionRow[] = []

  const manifestColumns: EnterpriseColumn<ManifestRow>[] = [
    {
      key: 'id',
      header: t('manifests.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'intent', header: t('manifests.intent') },
    {
      key: 'state',
      header: t('manifests.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    { key: 'requestedBy', header: t('manifests.requestedBy') },
    {
      key: 'requestedAt',
      header: t('manifests.requestedAt'),
      render: (r) => <span className="eg-mono">{r.requestedAt}</span>,
    },
  ]

  const executionColumns: EnterpriseColumn<ExecutionRow>[] = [
    {
      key: 'manifestId',
      header: t('executions.manifestId'),
      render: (r) => <TechnicalIdentifier value={r.manifestId} maxLength={14} />,
    },
    { key: 'outcome', header: t('executions.outcome') },
    {
      key: 'state',
      header: t('executions.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'executedAt',
      header: t('executions.executedAt'),
      render: (r) => <span className="eg-mono">{r.executedAt}</span>,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.govern') },
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

      <section className="eg-manifests__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.active')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.awaitingExecution')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.executed24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.failed24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-manifests__list">
        <EnterpriseTable<ManifestRow>
          columns={manifestColumns}
          rows={manifests}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('manifests.caption')}
          emptyMessage={t('manifests.empty')}
        />
      </section>

      <section className="eg-manifests__executions">
        <EnterpriseTable<ExecutionRow>
          columns={executionColumns}
          rows={executions}
          getRowKey={(r) => `${r.manifestId}-${r.executedAt}`}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('executions.caption')}
          emptyMessage={t('executions.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
