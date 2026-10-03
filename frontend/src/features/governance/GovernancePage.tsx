import { useState, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import { WorkspaceHeader, ContextStrip } from '../../components/workspace'
import { MetricCard, EnterpriseTable } from '../../components/data-display'
import type { EnterpriseColumn, MetricValue } from '../../components/data-display'
import { StatusBadge, TechnicalIdentifier } from '../../components/security'
import type { StatusKey } from '../../components/security'
import { DangerousActionDialog } from '../../components/dangerous'
import { HierarchyTree } from '../../components/visualization'
import type { TreeNode } from '../../components/visualization'

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
 * Policy tree structure — placeholder.
 *
 * Renders the shape of the ADIE policy hierarchy (a single root with
 * three scopes and three example policies). All nodes are unknown tone,
 * no counts. When the backend arrives, real policy data replaces this
 * constant — no component changes needed.
 */
const POLICY_TREE: TreeNode[] = [
  { id: 'root',   label: 'Policies',     parentId: null },
  { id: 'gov',    label: 'Governance',   parentId: 'root' },
  { id: 'sec',    label: 'Security',     parentId: 'root' },
  { id: 'ops',    label: 'Operations',   parentId: 'root' },
  { id: 'gov-1',  label: 'POL-GOV-001',  parentId: 'gov' },
  { id: 'gov-2',  label: 'POL-GOV-002',  parentId: 'gov' },
  { id: 'sec-1',  label: 'POL-SEC-001',  parentId: 'sec' },
  { id: 'ops-1',  label: 'POL-OPS-001',  parentId: 'ops' },
]

/**
 * GovernancePage — UI-01.E.4 (+ I.5).
 *
 * Shows policies and approvals, plus the policy hierarchy as an
 * expandable tree.
 *
 * The page never fabricates authorization. The dangerous-action dialog
 * is real: acknowledging intent does NOT execute anything; it emits a
 * signal to a backend that does not exist yet.
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

      <section className="eg-governance__tree">
        <HierarchyTree nodes={POLICY_TREE} ariaLabel={t('policies.caption')} />
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
          setProposeOpen(false)
        }}
      />
    </>
  )
}
