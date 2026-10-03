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
import { Timeline } from '../../components/visualization'
import type { TimelineEvent } from '../../components/visualization'

interface AuditRow {
  id: string
  occurredAt: string
  actor: string
  action: string
  target: string
  authority: string
  state: StatusKey
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

const FILTER_KEYS = ['actor', 'action', 'authority', 'window'] as const

/**
 * AuditPage — UI-01.G.10 (+ I.2).
 *
 * The immutable audit trail. Two complementary views:
 *   1. Timeline — a visual event stream (chronological)
 *   2. Table — the tabular audit log (sortable, filterable)
 *
 * Both views are currently empty by design.
 * The UI never writes to the audit trail.
 */
export function AuditPage(): ReactElement {
  const { t } = useTranslation('audit')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const events: AuditRow[] = []

  const timelineEvents: TimelineEvent[] = []

  const columns: EnterpriseColumn<AuditRow>[] = [
    {
      key: 'id',
      header: t('trail.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    {
      key: 'occurredAt',
      header: t('trail.occurredAt'),
      render: (r) => <span className="eg-mono">{r.occurredAt}</span>,
    },
    { key: 'actor', header: t('trail.actor') },
    { key: 'action', header: t('trail.action') },
    {
      key: 'target',
      header: t('trail.target'),
      render: (r) => <span className="eg-mono">{r.target}</span>,
    },
    {
      key: 'authority',
      header: t('trail.authority'),
      render: (r) => <span className="eg-mono">{r.authority}</span>,
    },
    {
      key: 'state',
      header: t('trail.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
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

      <section className="eg-audit__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.events')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.actors')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.authorities')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.lastEvent')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-audit__filters" aria-label={t('filters.label')}>
        <div className="eg-audit__filters-header">
          <span className="eg-audit__filters-title">{t('filters.label')}</span>
          <span className="eg-audit__filters-note">{t('filters.unavailable')}</span>
        </div>
        <ul className="eg-audit__filters-list" role="list">
          {FILTER_KEYS.map((key) => (
            <li key={key} className="eg-audit__filter-item">
              <span className="eg-audit__filter-label">{t(`filters.${key}`)}</span>
              <span className="eg-audit__filter-value">—</span>
            </li>
          ))}
        </ul>
        <div className="eg-audit__filters-actions">
          <button
            type="button"
            className="eg-audit__filter-btn"
            disabled
            data-testid="eg-audit-apply"
          >
            {t('filters.apply')}
          </button>
          <button
            type="button"
            className="eg-audit__filter-btn eg-audit__filter-btn--ghost"
            disabled
            data-testid="eg-audit-clear"
          >
            {t('filters.clear')}
          </button>
        </div>
      </section>

      <section className="eg-audit__timeline">
        <Timeline events={timelineEvents} />
      </section>

      <section className="eg-audit__reference">
        <div className="eg-audit__reference-header">{t('reference.caption')}</div>
        <p className="eg-audit__reference-note">{t('reference.note')}</p>
      </section>

      <section className="eg-audit__trail">
        <EnterpriseTable<AuditRow>
          columns={columns}
          rows={events}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('trail.caption')}
          emptyMessage={t('trail.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
