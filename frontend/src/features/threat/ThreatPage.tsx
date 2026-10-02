import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import {
  MetricCard,
  ChartFrame,
  EnterpriseTable,
} from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import {
  SeverityBadge,
  TechnicalIdentifier,
} from '../../components/security'
import type { SeverityLevel } from '../../components/security'

interface IocRow {
  id: string
  type: string
  severity: SeverityLevel
  source: string
  observedAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * ThreatPage — UI-01.G.2.
 *
 * Threat Intelligence — feeds, IOCs, adversary tracking.
 *
 * In UI-01 there is no backend, so the IOC table is empty by design.
 * The threat volume chart renders in the 'empty' state. No IOCs are
 * fabricated. Every metric renders as — with a Not Connected state.
 */
export function ThreatPage(): ReactElement {
  const { t } = useTranslation('threat')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const iocs: IocRow[] = []

  const columns: EnterpriseColumn<IocRow>[] = [
    {
      key: 'id',
      header: t('iocs.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={16} />,
    },
    { key: 'type', header: t('iocs.type') },
    {
      key: 'severity',
      header: t('iocs.severity'),
      render: (r) => <SeverityBadge severity={r.severity} />,
    },
    { key: 'source', header: t('iocs.source') },
    {
      key: 'observedAt',
      header: t('iocs.observedAt'),
      render: (r) => <span className="eg-mono">{r.observedAt}</span>,
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

      <section className="eg-threat__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.activeThreats')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.iocs')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.feedsActive')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.lastUpdate')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-threat__volume" aria-label={t('volume.title')}>
        <ChartFrame
          title={t('volume.title')}
          subtitle={t('volume.subtitle')}
          state="empty"
          height={260}
        />
      </section>

      <section className="eg-threat__iocs">
        <EnterpriseTable<IocRow>
          columns={columns}
          rows={iocs}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('iocs.caption')}
          emptyMessage={t('iocs.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
