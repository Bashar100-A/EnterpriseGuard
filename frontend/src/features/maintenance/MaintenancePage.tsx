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

interface ScheduleRow {
  id: string
  title: string
  state: StatusKey
  scheduledFor: string
  window: string
}

interface HistoryRow {
  id: string
  change: string
  state: StatusKey
  completedAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

const CAPABILITY_KEYS = ['planned', 'verification', 'rollback', 'history'] as const

/**
 * MaintenancePage — UI-01.G.7.
 *
 * Shows planned maintenance windows, their state, and history.
 *
 * The UI does NOT perform maintenance. Repair, rollback, restart,
 * delete, and migrate all require backend authority. This page shows
 * the interface that future maintenance operations will use.
 */
export function MaintenancePage(): ReactElement {
  const { t } = useTranslation('maintenance')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const schedule: ScheduleRow[] = []
  const history: HistoryRow[] = []

  const scheduleColumns: EnterpriseColumn<ScheduleRow>[] = [
    {
      key: 'id',
      header: t('schedule.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'title', header: t('schedule.title') },
    {
      key: 'state',
      header: t('schedule.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'scheduledFor',
      header: t('schedule.scheduledFor'),
      render: (r) => <span className="eg-mono">{r.scheduledFor}</span>,
    },
    {
      key: 'window',
      header: t('schedule.window'),
      render: (r) => <span className="eg-mono">{r.window}</span>,
    },
  ]

  const historyColumns: EnterpriseColumn<HistoryRow>[] = [
    {
      key: 'id',
      header: t('history.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'change', header: t('history.change') },
    {
      key: 'state',
      header: t('history.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'completedAt',
      header: t('history.completedAt'),
      render: (r) => <span className="eg-mono">{r.completedAt}</span>,
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

      <section className="eg-maintenance__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.scheduled')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.inProgress')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.completed24h')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.rollbackReady')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-maintenance__capabilities" aria-label={t('windows.label')}>
        <div className="eg-maintenance__capabilities-header">
          {t('windows.label')}
        </div>
        <ul className="eg-maintenance__capabilities-list" role="list">
          {CAPABILITY_KEYS.map((key) => (
            <li key={key} className="eg-maintenance__capability-item">
              {t(`windows.${key}`)}
            </li>
          ))}
        </ul>
      </section>

      <section className="eg-maintenance__schedule">
        <EnterpriseTable<ScheduleRow>
          columns={scheduleColumns}
          rows={schedule}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('schedule.caption')}
          emptyMessage={t('schedule.empty')}
        />
      </section>

      <section className="eg-maintenance__history">
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
