import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { MetricCard, EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import {
  TrustChainVisual,
  TechnicalIdentifier,
  StatusBadge,
  StateIndicator,
} from '../../components/security'
import type { StatusKey } from '../../components/security'

interface CheckpointRow {
  id: string
  height: number
  state: StatusKey
  createdAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * SibbPage — UI-01.F.1.
 *
 * The SIBB Trust Core page — the cryptographic foundation of ADIE.
 *
 * Layout:
 *   - MetricCards for chain height, baseline state, last checkpoint, signatures
 *   - TrustChainVisual: a cinematic Merkle visualization
 *   - Four integrity indicators: baseline, chain, signature, storage
 *   - Table of recent checkpoints
 *
 * In UI-01 there is no SIBB backend. Every state renders as Unknown and
 * every metric is —. Nothing is fabricated, not even a placeholder hash.
 */
export function SibbPage(): ReactElement {
  const { t } = useTranslation('sibb')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }

  const checkpoints: CheckpointRow[] = []

  const columns: EnterpriseColumn<CheckpointRow>[] = [
    {
      key: 'id',
      header: t('checkpoints.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    {
      key: 'height',
      header: t('checkpoints.height'),
      render: (r) => <span className="eg-mono">{r.height}</span>,
    },
    {
      key: 'state',
      header: t('checkpoints.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'createdAt',
      header: t('checkpoints.createdAt'),
      render: (r) => <span className="eg-mono">{r.createdAt}</span>,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.trust') },
    { label: t('title'), current: true },
  ]

  const integrityItems: Array<{ key: 'baseline' | 'chain' | 'signature' | 'storage' }> = [
    { key: 'baseline' },
    { key: 'chain' },
    { key: 'signature' },
    { key: 'storage' },
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

      <section className="eg-sibb__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.chainHeight')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.baselineState')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.lastCheckpoint')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.signedItems')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-sibb__visual" aria-label={t('merkle.title')}>
        <div className="eg-sibb__visual-header">
          <h2 className="eg-sibb__visual-title">{t('merkle.title')}</h2>
          <p className="eg-sibb__visual-subtitle">{t('merkle.subtitle')}</p>
        </div>
        <TrustChainVisual root={null} height={null} />
      </section>

      <section className="eg-sibb__integrity" aria-label={t('integrity.label')}>
        <div className="eg-sibb__integrity-header">{t('integrity.label')}</div>
        <ul className="eg-sibb__integrity-list" role="list">
          {integrityItems.map((it) => (
            <li key={it.key} className="eg-sibb__integrity-item">
              <span className="eg-sibb__integrity-name">
                {t(`integrity.${it.key}`)}
              </span>
              <StateIndicator
                tone="unknown"
                label={t('metrics.baselineState') === 'Baseline State' ? 'Unknown' : 'غير معروف'}
                size="sm"
              />
            </li>
          ))}
        </ul>
      </section>

      <section className="eg-sibb__checkpoints">
        <EnterpriseTable<CheckpointRow>
          columns={columns}
          rows={checkpoints}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('checkpoints.caption')}
          emptyMessage={t('checkpoints.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
