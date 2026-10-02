import { type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { MetricCard, EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import {
  EvidenceIndicator,
  TechnicalIdentifier,
} from '../../components/security'
import type { VerificationState } from '../../components/security'

interface EvidenceRow {
  id: string
  source: string
  verifiedAt: string
  state: VerificationState
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * EvidencePage — UI-01.E.2.
 *
 * Displays evidence items within the current scope with full provenance.
 *
 * In UI-01 there is no backend yet, so the page renders only the honest
 * empty state. No rows are fabricated. When the backend arrives, this same
 * page will display real data — no component changes required.
 *
 * Uses:
 *   - WorkspaceHeader + ContextStrip (structure)
 *   - MetricCard (summary counts — showing Not Connected for now)
 *   - EnterpriseTable (item list)
 *   - EvidenceIndicator (per-row verification)
 *   - TechnicalIdentifier (evidence IDs — mono, LTR-safe, copyable)
 */
export function EvidencePage(): ReactElement {
  const { t } = useTranslation('evidence')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  // No backend in UI-01. Empty by design.
  const rows: EvidenceRow[] = []
  const backendConnected = false

  const columns: EnterpriseColumn<EvidenceRow>[] = [
    {
      key: 'id',
      header: t('table.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={16} />,
    },
    {
      key: 'source',
      header: t('table.source'),
      render: (r) => r.source,
    },
    {
      key: 'verifiedAt',
      header: t('table.verifiedAt'),
      render: (r) => <span className="eg-mono">{r.verifiedAt}</span>,
    },
    {
      key: 'verification',
      header: t('table.verification'),
      render: (r) => <EvidenceIndicator state={r.state} />,
    },
  ]

  const emptyValue: MetricValue = { value: null }
  const totalValue: MetricValue = backendConnected ? { value: rows.length } : emptyValue
  const verifiedValue: MetricValue = backendConnected
    ? { value: rows.filter((r) => r.state === 'verified').length }
    : emptyValue
  const unknownValue: MetricValue = backendConnected
    ? { value: rows.filter((r) => r.state === 'unknown').length }
    : emptyValue
  const invalidValue: MetricValue = backendConnected
    ? { value: rows.filter((r) => r.state === 'invalid').length }
    : emptyValue

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

      <section
        className="eg-evidence-page__metrics"
        aria-label={t('table.caption')}
      >
        <MetricCard
          label={t('metrics.total')}
          value={totalValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.verified')}
          value={verifiedValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.unknown')}
          value={unknownValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.invalid')}
          value={invalidValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-evidence-page__table">
        <EnterpriseTable<EvidenceRow>
          columns={columns}
          rows={rows}
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
