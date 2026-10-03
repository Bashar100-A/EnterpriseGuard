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

interface SettingRow {
  key: string
  value: string
  scope: string
  state: StatusKey
  updatedAt: string
}

interface FlagRow {
  id: string
  name: string
  state: StatusKey
  enabled: boolean
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

const GROUP_KEYS = ['general', 'security', 'integrations', 'performance', 'notifications'] as const

/**
 * ConfigPage — UI-01.G.12.
 *
 * System configuration and feature flags.
 *
 * The UI never writes configuration. All settings are sourced from
 * the backend config service. Feature flags, overrides, and settings
 * are read-only in the UI.
 */
export function ConfigPage(): ReactElement {
  const { t } = useTranslation('config')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const settings: SettingRow[] = []
  const flags: FlagRow[] = []

  const settingColumns: EnterpriseColumn<SettingRow>[] = [
    {
      key: 'key',
      header: t('settings.key'),
      render: (r) => <TechnicalIdentifier value={r.key} maxLength={20} />,
    },
    {
      key: 'value',
      header: t('settings.value'),
      render: (r) => <span className="eg-mono">{r.value}</span>,
    },
    { key: 'scope', header: t('settings.scope') },
    {
      key: 'state',
      header: t('settings.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'updatedAt',
      header: t('settings.updatedAt'),
      render: (r) => <span className="eg-mono">{r.updatedAt}</span>,
    },
  ]

  const flagColumns: EnterpriseColumn<FlagRow>[] = [
    {
      key: 'id',
      header: t('flags.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'name', header: t('flags.name') },
    {
      key: 'state',
      header: t('flags.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'enabled',
      header: t('flags.enabled'),
      render: (r) => <span className="eg-mono">{r.enabled ? 'true' : 'false'}</span>,
    },
  ]

  const breadcrumb = [
    { label: tW('breadcrumb.home') },
    { label: tN('groups.administration') },
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

      <section className="eg-config__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.settings')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.flags')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.overrides')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.lastChange')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-config__groups" aria-label={t('groups.label')}>
        <div className="eg-config__groups-header">{t('groups.label')}</div>
        <ul className="eg-config__groups-list" role="list">
          {GROUP_KEYS.map((key) => (
            <li key={key} className="eg-config__group-item">
              {t(`groups.${key}`)}
            </li>
          ))}
        </ul>
      </section>

      <section className="eg-config__settings">
        <EnterpriseTable<SettingRow>
          columns={settingColumns}
          rows={settings}
          getRowKey={(r) => r.key}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('settings.caption')}
          emptyMessage={t('settings.empty')}
        />
      </section>

      <section className="eg-config__flags">
        <EnterpriseTable<FlagRow>
          columns={flagColumns}
          rows={flags}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('flags.caption')}
          emptyMessage={t('flags.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
