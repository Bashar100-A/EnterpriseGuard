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

interface RunRow {
  id: string
  scope: string
  state: StatusKey
  duration: string
  completedAt: string
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

const SCOPE_KEYS = ['code', 'dependencies', 'configuration', 'tests', 'integrity', 'runtime'] as const

/**
 * InspectionPage — UI-01.G.6.
 *
 * On-demand inspection surface. Shows:
 *   - Six inspection scopes (Code, Dependencies, Config, Tests, Integrity, Runtime)
 *   - A disabled "Run Inspection" button until the backend is connected
 *   - History table of past runs (empty by design in UI-01)
 *
 * The Run button remains disabled — the UI never pretends to run
 * an inspection without a backend to authorize and execute it.
 */
export function InspectionPage(): ReactElement {
  const { t } = useTranslation('inspection')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const runs: RunRow[] = []

  const columns: EnterpriseColumn<RunRow>[] = [
    {
      key: 'id',
      header: t('history.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'scope', header: t('history.scope') },
    {
      key: 'state',
      header: t('history.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'duration',
      header: t('history.duration'),
      render: (r) => <span className="eg-mono">{r.duration}</span>,
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

      <section className="eg-inspection__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.scopeItems')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.lastRun')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.passed')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.failed')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-inspection__scope" aria-label={t('scopes.label')}>
        <div className="eg-inspection__scope-header">
          <span className="eg-inspection__scope-title">{t('scopes.label')}</span>
          <button
            type="button"
            className="eg-inspection__run"
            disabled
            title={t('run.unavailable')}
            data-testid="eg-inspection-run"
          >
            {t('run.label')}
          </button>
        </div>
        <ul className="eg-inspection__scope-list" role="list">
          {SCOPE_KEYS.map((key) => (
            <li key={key} className="eg-inspection__scope-item">
              {t(`scopes.${key}`)}
            </li>
          ))}
        </ul>
      </section>

      <section className="eg-inspection__history">
        <EnterpriseTable<RunRow>
          columns={columns}
          rows={runs}
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
