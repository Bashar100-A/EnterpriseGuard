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

interface UserRow {
  id: string
  name: string
  role: string
  state: StatusKey
  lastSeen: string
}

interface RoleRow {
  id: string
  name: string
  scope: string
  members: number
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * AccessPage — UI-01.G.11.
 *
 * Users, roles, and the permissions matrix.
 *
 * The UI never grants or revokes access. Every authorization check
 * is evaluated by the backend. The permissions matrix note makes
 * this boundary explicit.
 */
export function AccessPage(): ReactElement {
  const { t } = useTranslation('access')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }
  const users: UserRow[] = []
  const roles: RoleRow[] = []

  const userColumns: EnterpriseColumn<UserRow>[] = [
    {
      key: 'id',
      header: t('users.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'name', header: t('users.name') },
    { key: 'role', header: t('users.role') },
    {
      key: 'state',
      header: t('users.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
    {
      key: 'lastSeen',
      header: t('users.lastSeen'),
      render: (r) => <span className="eg-mono">{r.lastSeen}</span>,
    },
  ]

  const roleColumns: EnterpriseColumn<RoleRow>[] = [
    {
      key: 'id',
      header: t('roles.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'name', header: t('roles.name') },
    { key: 'scope', header: t('roles.scope') },
    {
      key: 'members',
      header: t('roles.members'),
      render: (r) => <span className="eg-mono">{r.members}</span>,
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

      <section className="eg-access__metrics" aria-label={t('metrics.label')}>
        <MetricCard
          label={t('metrics.users')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.roles')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.sessions')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.pendingInvites')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-access__matrix" aria-label={t('matrix.label')}>
        <div className="eg-access__matrix-header">{t('matrix.label')}</div>
        <p className="eg-access__matrix-note">{t('matrix.note')}</p>
      </section>

      <section className="eg-access__users">
        <EnterpriseTable<UserRow>
          columns={userColumns}
          rows={users}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('users.caption')}
          emptyMessage={t('users.empty')}
        />
      </section>

      <section className="eg-access__roles">
        <EnterpriseTable<RoleRow>
          columns={roleColumns}
          rows={roles}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('roles.caption')}
          emptyMessage={t('roles.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>
    </>
  )
}
