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

interface CatalogRow {
  id: string
  title: string
  state: StatusKey
  format: string
  updatedAt: string
}

interface DeliveryRow {
  id: string
  report: string
  schedule: string
  state: StatusKey
  nextRun: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * ReportsPage — UI-01.G.9.
 *
 * Report catalog plus scheduled deliveries.
 *
 * The UI does not generate reports. Export and delivery require the
 * backend report service. Until then, both tables remain empty.
 */
export function ReportsPage(): ReactElement {
  const { t } = useTranslation('reports')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const catalog: CatalogRow[] = []
  const deliveries: DeliveryRow[] = []

  const catalogColumns: EnterpriseColumn<CatalogRow>[] = [
    {
      key: 'id',
      header: t('catalog.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'title', header: t('catalog.title') },
    {
      key: 'state',
      header: t('catalog.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'format',
      header: t('catalog.format'),
      render: (r) => <span className="eg-mono">{r.format}</span>,
    },
    {
      key: 'updatedAt',
      header: t('catalog.updatedAt'),
      render: (r) => <span className="eg-mono">{r.updatedAt}</span>,
    },
  ]

  const deliveryColumns: EnterpriseColumn<DeliveryRow>[] = [
    {
      key: 'id',
      header: t('deliveries.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'report', header: t('deliveries.report') },
    {
      key: 'schedule',
      header: t('deliveries.schedule'),
      render: (r) => <span className="eg-mono">{r.schedule}</span>,
    },
    {
      key: 'state',
      header: t('deliveries.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'nextRun',
      header: t('deliveries.nextRun'),
      render: (r) => <span className="eg-mono">{r.nextRun}</span>,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.assurance') },
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

      <section className="eg-reports__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.available')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.scheduled')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.generated24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.failed24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-reports__catalog">
        <EnterpriseTable<CatalogRow>
          columns={catalogColumns}
          rows={catalog}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('catalog.caption')}
          emptyMessage={t('catalog.empty')}
        />
      </section>

      <section className="eg-reports__deliveries">
        <EnterpriseTable<DeliveryRow>
          columns={deliveryColumns}
          rows={deliveries}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('deliveries.caption')}
          emptyMessage={t('deliveries.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
