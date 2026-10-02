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

interface IncidentRow {
  id: string
  severity: SeverityLevel
  state: StatusKey
  source: string
  detectedAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * OperationsPage — UI-01.G.1.
 *
 * Security Operations — the incident queue.
 *
 * In UI-01 there is no backend, so the queue is empty by design.
 * Every metric renders as — with a Not Connected state. No incidents
 * are fabricated. When the backend arrives, this page becomes the
 * live operations console without code changes.
 */
export function OperationsPage(): ReactElement {
  const { t } = useTranslation('operations')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const incidents: IncidentRow[] = []

  const columns: EnterpriseColumn<IncidentRow>[] = [
    {
      key: 'id',
      header: t('incidents.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    {
      key: 'severity',
      header: t('incidents.severity'),
      render: (r) => <SeverityBadge severity={r.severity} />,
    },
    {
      key: 'state',
      header: t('incidents.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    { key: 'source', header: t('incidents.source') },
    {
      key: 'detectedAt',
      header: t('incidents.detectedAt'),
      render: (r) => <span className="eg-mono">{r.detectedAt}</span>,
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

      <section className="eg-ops__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.activeIncidents')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.critical')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.resolved24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.mttr')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-ops__incidents">
        <EnterpriseTable<IncidentRow>
          columns={columns}
          rows={incidents}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('incidents.caption')}
          emptyMessage={t('incidents.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
