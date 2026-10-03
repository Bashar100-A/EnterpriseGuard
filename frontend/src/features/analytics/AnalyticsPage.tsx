import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import {
  MetricCard,
  ChartFrame,
  EnterpriseTable,
} from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import { TechnicalIdentifier } from '../../components/security'
import { Heatmap } from '../../components/visualization'
import type { HeatmapCell } from '../../components/visualization'

interface SnapshotRow {
  id: string
  window: string
  dataPoints: number
  createdAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

const DIMENSION_KEYS = ['time', 'source', 'severity', 'scope', 'authority'] as const

/**
 * AnalyticsPage — UI-01.G.8 (+ I.3).
 *
 * Metric grid + time series + heatmap + dimensions + snapshot table.
 *
 * The heatmap renders the full 7×24 grid structure but every cell is in
 * the 'none' intensity state — no activity data has arrived yet.
 */
export function AnalyticsPage(): ReactElement {
  const { t } = useTranslation('analytics')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const snapshots: SnapshotRow[] = []
  const heatmapCells: HeatmapCell[] = []

  const columns: EnterpriseColumn<SnapshotRow>[] = [
    {
      key: 'id',
      header: t('table.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'window', header: t('table.window') },
    {
      key: 'dataPoints',
      header: t('table.dataPoints'),
      render: (r) => <span className="eg-mono">{r.dataPoints}</span>,
    },
    {
      key: 'createdAt',
      header: t('table.createdAt'),
      render: (r) => <span className="eg-mono">{r.createdAt}</span>,
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

      <section className="eg-analytics__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.dataPoints')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.dimensions')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.windows')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.refreshRate')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-analytics__charts">
        <ChartFrame
          title={t('charts.volume')}
          subtitle={t('charts.volumeSub')}
          state="empty"
          height={220}
        />
        <ChartFrame
          title={t('charts.latency')}
          subtitle={t('charts.latencySub')}
          state="empty"
          height={220}
        />
        <ChartFrame
          title={t('charts.coverage')}
          subtitle={t('charts.coverageSub')}
          state="empty"
          height={220}
        />
      </section>

      <section className="eg-analytics__heatmap">
        <Heatmap cells={heatmapCells} />
      </section>

      <section className="eg-analytics__dimensions" aria-label={t('dimensions.label')}>
        <div className="eg-analytics__dimensions-header">
          {t('dimensions.label')}
        </div>
        <ul className="eg-analytics__dimensions-list" role="list">
          {DIMENSION_KEYS.map((key) => (
            <li key={key} className="eg-analytics__dimension-item">
              {t(`dimensions.${key}`)}
            </li>
          ))}
        </ul>
      </section>

      <section className="eg-analytics__snapshots">
        <EnterpriseTable<SnapshotRow>
          columns={columns}
          rows={snapshots}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('table.caption')}
          emptyMessage={t('table.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
