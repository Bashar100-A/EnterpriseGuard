import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { MetricCard, EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import {
  SeverityBadge,
  StatusBadge,
  TechnicalIdentifier,
} from '../../components/security'
import type { SeverityLevel, StatusKey } from '../../components/security'

interface QueueRow {
  id: string
  request: string
  requester: string
  severity: SeverityLevel
  state: StatusKey
  submittedAt: string
}

interface HistoryRow {
  id: string
  decision: string
  authority: string
  state: StatusKey
  decidedAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * ApprovalsPage — UI-01.G.4.
 *
 * Human-in-the-loop review. Two tables:
 *   - Pending queue: awaiting authority
 *   - History: recent decisions with authority reference
 *
 * The UI never approves. All decisions are made by the backend after
 * the required authority confirms.
 */
export function ApprovalsPage(): ReactElement {
  const { t } = useTranslation('approvals')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const queue: QueueRow[] = []
  const history: HistoryRow[] = []

  const queueColumns: EnterpriseColumn<QueueRow>[] = [
    {
      key: 'id',
      header: t('queue.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'request', header: t('queue.request') },
    { key: 'requester', header: t('queue.requester') },
    {
      key: 'severity',
      header: t('queue.severity'),
      render: (r) => <SeverityBadge severity={r.severity} />,
    },
    {
      key: 'state',
      header: t('queue.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'submittedAt',
      header: t('queue.submittedAt'),
      render: (r) => <span className="eg-mono">{r.submittedAt}</span>,
    },
  ]

  const historyColumns: EnterpriseColumn<HistoryRow>[] = [
    {
      key: 'id',
      header: t('history.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'decision', header: t('history.decision') },
    { key: 'authority', header: t('history.authority') },
    {
      key: 'state',
      header: t('history.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'decidedAt',
      header: t('history.decidedAt'),
      render: (r) => <span className="eg-mono">{r.decidedAt}</span>,
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

      <section className="eg-approvals__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.pending')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.awaitingAuthority')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.approved24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.rejected24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-approvals__queue">
        <EnterpriseTable<QueueRow>
          columns={queueColumns}
          rows={queue}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('queue.caption')}
          emptyMessage={t('queue.empty')}
        />
      </section>

      <section className="eg-approvals__history">
        <EnterpriseTable<HistoryRow>
          columns={historyColumns}
          rows={history}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('history.caption')}
          emptyMessage={t('history.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
