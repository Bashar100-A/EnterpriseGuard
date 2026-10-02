import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { MetricCard, EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import {
  EvidenceIndicator,
  TechnicalIdentifier,
} from '../../components/security'
import type { VerificationState } from '../../components/security'

interface ProvenanceRow {
  id: string
  item: string
  source: string
  chain: string
  verified: VerificationState
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

const LEGEND_STATES: VerificationState[] = ['verified', 'unverified', 'unknown']

/**
 * ProvenancePage — UI-01.F.2.
 *
 * Shows how each item is traced back to its origin. A record is only
 * marked 'verified' when both its source AND its chain are confirmed
 * by SIBB. Otherwise the record remains unverified or unknown.
 *
 * In UI-01 there is no backend. The page renders the structure + the
 * legend, but the table stays empty.
 */
export function ProvenancePage(): ReactElement {
  const { t } = useTranslation('provenance')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }

  const records: ProvenanceRow[] = []

  const columns: EnterpriseColumn<ProvenanceRow>[] = [
    {
      key: 'id',
      header: t('table.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'item', header: t('table.item') },
    { key: 'source', header: t('table.source') },
    {
      key: 'chain',
      header: t('table.chain'),
      render: (r) => <span className="eg-mono">{r.chain}</span>,
    },
    {
      key: 'verified',
      header: t('table.verified'),
      render: (r) => <EvidenceIndicator state={r.verified} />,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.trust') },
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

      <section className="eg-prov__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.sources')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.chains')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.verifiedLinks')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.unresolvedLinks')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-prov__legend" aria-label={t('legend.label')}>
        <div className="eg-prov__legend-header">{t('legend.label')}</div>
        <ul className="eg-prov__legend-list" role="list">
          {LEGEND_STATES.map((state) => (
            <li key={state} className="eg-prov__legend-item">
              <EvidenceIndicator state={state} />
              <span className="eg-prov__legend-caption">
                {t(`legend.${state}`)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="eg-prov__table">
        <EnterpriseTable<ProvenanceRow>
          columns={columns}
          rows={records}
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
