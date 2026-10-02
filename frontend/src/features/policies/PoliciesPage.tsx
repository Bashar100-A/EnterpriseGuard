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

interface PolicyRow {
  id: string
  name: string
  scope: string
  state: StatusKey
  effectiveAt: string
}

interface VersionRow {
  policyId: string
  version: string
  author: string
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
 * PoliciesPage — UI-01.G.3.
 *
 * The policy catalog plus recent version activity. Policies define what
 * is permitted; versions define how those rules evolved.
 */
export function PoliciesPage(): ReactElement {
  const { t } = useTranslation('policies')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const policies: PolicyRow[] = []
  const versions: VersionRow[] = []

  const policyColumns: EnterpriseColumn<PolicyRow>[] = [
    {
      key: 'id',
      header: t('table.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'name', header: t('table.name') },
    { key: 'scope', header: t('table.scope') },
    {
      key: 'state',
      header: t('table.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'effectiveAt',
      header: t('table.effectiveAt'),
      render: (r) => <span className="eg-mono">{r.effectiveAt}</span>,
    },
  ]

  const versionColumns: EnterpriseColumn<VersionRow>[] = [
    {
      key: 'policyId',
      header: t('versions.policyId'),
      render: (r) => <TechnicalIdentifier value={r.policyId} maxLength={14} />,
    },
    {
      key: 'version',
      header: t('versions.version'),
      render: (r) => <span className="eg-mono">{r.version}</span>,
    },
    { key: 'author', header: t('versions.author') },
    {
      key: 'state',
      header: t('versions.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'createdAt',
      header: t('versions.createdAt'),
      render: (r) => <span className="eg-mono">{r.createdAt}</span>,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.govern') },
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

      <section className="eg-policies__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.active')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.draft')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.expiring')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.conflicts')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-policies__catalog">
        <EnterpriseTable<PolicyRow>
          columns={policyColumns}
          rows={policies}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('table.caption')}
          emptyMessage={t('table.empty')}
        />
      </section>

      <section className="eg-policies__versions">
        <EnterpriseTable<VersionRow>
          columns={versionColumns}
          rows={versions}
          getRowKey={(r) => `${r.policyId}-${r.version}`}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('versions.caption')}
          emptyMessage={t('versions.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
