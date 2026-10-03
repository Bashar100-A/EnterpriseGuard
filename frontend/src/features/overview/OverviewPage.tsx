import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import {
  MetricCard,
  ChartFrame,
  EnterpriseTable,
} from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'

interface ActivityRow {
  id: string
  time: string
  actor: string
  action: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * OverviewPage — UI-01.E.1.
 *
 * The Situation Room. A professional operations view that shows:
 *   - Core operational metrics (all Not Connected in UI-01)
 *   - Two trend charts (empty by design)
 *   - Recent activity table (empty by design)
 *
 * The doctrine strip at the top is a page-local reminder of ADIE's core
 * invariant: Observed ≠ Decided ≠ Executed. It is design, not data.
 *
 * No fabricated numbers. No fake telemetry. Every value that isn't
 * available renders as — with a Not Connected indicator.
 */
export function OverviewPage(): ReactElement {
  const { t } = useTranslation('overview')
  const { t: tW } = useTranslation('workspace')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }

  const activityColumns: EnterpriseColumn<ActivityRow>[] = [
    { key: 'time', header: t('activity.time') },
    { key: 'actor', header: t('activity.actor') },
    { key: 'action', header: t('activity.action') },
  ]

  const breadcrumb = [{ label: tW('breadcrumb.home'), current: true }]

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

      {/* Doctrine strip — ADIE's core invariant, made visible. */}
      <section
        className="eg-overview__doctrine"
        aria-label="ADIE doctrine"
      >
        <span className="eg-overview__doctrine-term">
          {t('doctrine.observed')}
        </span>
        <span className="eg-overview__doctrine-sep" aria-hidden="true">
          ≠
        </span>
        <span className="eg-overview__doctrine-term">
          {t('doctrine.decided')}
        </span>
        <span className="eg-overview__doctrine-sep" aria-hidden="true">
          ≠
        </span>
        <span className="eg-overview__doctrine-term">
          {t('doctrine.executed')}
        </span>
      </section>

      {/* Key operational indicators */}
      <section
        className="eg-overview__metrics"
        aria-label={t('metrics.label')}
      >
        <MetricCard
          label={t('metrics.systemHealth')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.activeEvidence')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.pendingApprovals')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.lastDecision')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      {/* Trends */}
      <section className="eg-overview__charts">
        <h2 className="eg-visually-hidden">{t('charts.sectionLabel')}</h2>
        <ChartFrame
          title={t('charts.decisionVolume')}
          subtitle={t('charts.decisionVolumeSub')}
          state="empty"
          height={240}
        />
        <ChartFrame
          title={t('charts.evidenceFreshness')}
          subtitle={t('charts.evidenceFreshnessSub')}
          state="empty"
          height={240}
        />
      </section>

      {/* Recent activity */}
      <section className="eg-overview__activity">
        <EnterpriseTable<ActivityRow>
          columns={activityColumns}
          rows={[]}
          getRowKey={(r) => r.id}
          state="empty"
          caption={t('activity.caption')}
          emptyMessage={t('activity.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
