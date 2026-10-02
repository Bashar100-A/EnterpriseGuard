import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import {
  MetricCard,
  ChartFrame,
  EnterpriseTable,
} from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import { StatusBadge } from '../../components/security'
import type { StatusKey } from '../../components/security'

interface ServiceRow {
  name: string
  state: StatusKey
  region: string
  since: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * HealthPage — UI-01.E.5.
 *
 * Shows operational state of services and resources. Uses the full
 * primitive set: MetricCard, ChartFrame, EnterpriseTable, StatusBadge.
 *
 * In UI-01 there is no backend, so all metrics show '—' with
 * 'Not Connected', charts render empty, and the services table is empty.
 *
 * No fake CPU percentages. No fake latency numbers. No fake uptime.
 */
export function HealthPage(): ReactElement {
  const { t } = useTranslation('health')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }

  const services: ServiceRow[] = []

  const serviceColumns: EnterpriseColumn<ServiceRow>[] = [
    { key: 'name', header: t('services.name') },
    {
      key: 'state',
      header: t('services.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    { key: 'region', header: t('services.region') },
    {
      key: 'since',
      header: t('services.since'),
      render: (r) => <span className="eg-mono">{r.since}</span>,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.operate') },
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

      <section className="eg-health__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.uptime')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.availability')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.latencyP99')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.errorRate')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-health__charts" aria-label={t('resources.cpu')}>
        <ChartFrame
          title={t('resources.cpu')}
          subtitle={t('resources.cpuSub')}
          state="empty"
          height={220}
        />
        <ChartFrame
          title={t('resources.memory')}
          subtitle={t('resources.memorySub')}
          state="empty"
          height={220}
        />
      </section>

      <section className="eg-health__services">
        <EnterpriseTable<ServiceRow>
          columns={serviceColumns}
          rows={services}
          getRowKey={(r) => r.name}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('services.caption')}
          emptyMessage={t('services.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
