import { useState, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import {
  MetricCard,
  EnterpriseTable,
} from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import {
  StatusBadge,
  TechnicalIdentifier,
} from '../../components/security'
import type { StatusKey } from '../../components/security'
import { DangerousActionDialog } from '../../components/dangerous'

interface PolicyRow {
  id: string
  name: string
  scope: string
  state: StatusKey
}

interface ApprovalRow {
  id: string
  request: string
  requester: string
  state: StatusKey
}

function resolveEnvironment(): string {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'Production'
  if (mode === 'development') return 'Development'
  if (mode === 'test') return 'Test'
  return 'Unknown'
}

/**
 * GovernancePage — UI-01.E.4.
 *
 * Shows policies and pending approvals, plus the authority boundary in
 * action through the "Propose Policy" flow (DangerousActionDialog).
 *
 * The page never fabricates authorization. The dialog is real:
 * acknowledging intent does NOT execute anything; it emits a signal to
 * a backend that does not exist yet.
 */
export function GovernancePage(): ReactElement {
  const { t } = useTranslation('governance')
  const { t: tW } = useTranslation('workspace')
  const { t: tN } = useTranslation('navigation')

  const [proposeOpen, setProposeOpen] = useState(false)

  const backendConnected = false
  const emptyValue: MetricValue = { value: null }

  const policies: PolicyRow[] = []
  const approvals: ApprovalRow[] = []

  const policyColumns: EnterpriseColumn<PolicyRow>[] = [
    {
      key: 'id',
      header: t('policies.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'name', header: t('policies.name') },
    { key: 'scope', header: t('policies.scope') },
    {
      key: 'state',
      header: t('policies.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
    },
  ]

  const approvalColumns: EnterpriseColumn<ApprovalRow>[] = [
    {
      key: 'id',
      header: t('approvals.id'),
      render: (r) => <TechnicalIdentifier value={r.id} maxLength={14} />,
    },
    { key: 'request', header: t('approvals.request') },
    { key: 'requester', header: t('approvals.requester') },
    {
      key: 'state',
      header: t('approvals.state'),
      render: (r) => <StatusBadge status={r.state} withDot />,
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
        actions={
          <button
            type="button"
            className="eg-governance__propose"
            onClick={() => setProposeOpen(true)}
            data-testid="eg-governance-propose"
          >
            + {t('propose.label')}
          </button>
        }
      />

      <section
        className="eg-governance__metrics"
        aria-label={t('metrics.label')}
      >
        <MetricCard
          label={t('metrics.activePolicies')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.pendingApprovals')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.approvedToday')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
        <MetricCard
          label={t('metrics.rejectedToday')}
          value={emptyValue}
          dataState={backendConnected ? 'live' : 'notConnected'}
        />
      </section>

      <section className="eg-governance__policies">
        <EnterpriseTable<PolicyRow>
          columns={policyColumns}
          rows={policies}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('policies.caption')}
          emptyMessage={t('policies.empty')}
        />
      </section>

      <section className="eg-governance__approvals">
        <EnterpriseTable<ApprovalRow>
          columns={approvalColumns}
          rows={approvals}
          getRowKey={(r) => r.id}
          state={backendConnected ? 'loaded' : 'empty'}
          caption={t('approvals.caption')}
          emptyMessage={t('approvals.empty')}
        />
      </section>

      <p className="eg-note">{t('backendNote')}</p>

      <DangerousActionDialog
        open={proposeOpen}
        onClose={() => setProposeOpen(false)}
        intent={t('propose.intent')}
        explanation={t('propose.explanation')}
        impacts={[t('propose.impact1'), t('propose.impact2'), t('propose.impact3')]}
        requiredAuthority={t('propose.authorityRequired')}
        backendAuthority={t('propose.backendAuthority')}
        severity="high"
        requireAcknowledgment
        onConfirm={() => {
          // In UI-01 this does nothing real. The backend would receive this
          // request in a later phase. We close the dialog to prevent any
          // illusion that an action was taken.
          setProposeOpen(false)
        }}
      />
    </>
  )
}
