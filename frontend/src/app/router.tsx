import { createBrowserRouter, createMemoryRouter, type RouteObject } from 'react-router-dom'
import { RootLayout } from './RootLayout'
import { ErrorBoundary } from './ErrorBoundary'
import { PageShell } from './PageShell'
import { NotFound } from './NotFound'
import { EvidencePage } from '../features/evidence'
import { OverviewPage } from '../features/overview'
import { DecisionsPage } from '../features/decisions'
import { GovernancePage } from '../features/governance'
import { HealthPage } from '../features/health'
import { SibbPage } from '../features/sibb'
import { ProvenancePage } from '../features/provenance'
import { OperationsPage } from '../features/operations'
import { ThreatPage } from '../features/threat'
import { PoliciesPage } from '../features/policies'
import { ApprovalsPage } from '../features/approvals'

export interface RouteSpec {
  path: string
  titleKey: string
  groupKey: string
}

// 17 routes per spec section 50.
export const ROUTE_SPECS: RouteSpec[] = [
  { path: '/',                    titleKey: 'overview',             groupKey: 'command' },
  { path: '/operations',          titleKey: 'securityOperations',   groupKey: 'intelligence' },
  { path: '/intelligence',        titleKey: 'threatIntelligence',   groupKey: 'intelligence' },
  { path: '/decisions',           titleKey: 'decisionIntelligence', groupKey: 'intelligence' },
  { path: '/evidence',            titleKey: 'evidence',             groupKey: 'trust' },
  { path: '/provenance',          titleKey: 'provenance',           groupKey: 'trust' },
  { path: '/sibb',                titleKey: 'sibbTrustCore',        groupKey: 'trust' },
  { path: '/policies',            titleKey: 'policies',             groupKey: 'govern' },
  { path: '/governance',          titleKey: 'governance',           groupKey: 'govern' },
  { path: '/approvals',           titleKey: 'approvals',            groupKey: 'govern' },
  { path: '/manifests',           titleKey: 'executionManifests',   groupKey: 'govern' },
  { path: '/health',              titleKey: 'systemHealth',         groupKey: 'operate' },
  { path: '/inspection',          titleKey: 'inspection',           groupKey: 'operate' },
  { path: '/maintenance',         titleKey: 'maintenance',          groupKey: 'operate' },
  { path: '/analytics',           titleKey: 'analytics',            groupKey: 'assurance' },
  { path: '/reports',             titleKey: 'reports',              groupKey: 'assurance' },
  { path: '/audit',               titleKey: 'audit',                groupKey: 'assurance' },
  { path: '/access',              titleKey: 'usersAccess',          groupKey: 'administration' },
  { path: '/settings',            titleKey: 'configuration',        groupKey: 'administration' },
]

function buildChildRoutes(): RouteObject[] {
  const children: RouteObject[] = []

  ROUTE_SPECS.forEach((spec, i) => {
    const element =
      spec.path === '/' ? <OverviewPage />
      : spec.path === '/operations' ? <OperationsPage />
      : spec.path === '/intelligence' ? <ThreatPage />
      : spec.path === '/evidence' ? <EvidencePage />
      : spec.path === '/decisions' ? <DecisionsPage />
      : spec.path === '/governance' ? <GovernancePage />
      : spec.path === '/policies' ? <PoliciesPage />
      : spec.path === '/approvals' ? <ApprovalsPage />
      : spec.path === '/health' ? <HealthPage />
      : spec.path === '/sibb' ? <SibbPage />
      : spec.path === '/provenance' ? <ProvenancePage />
      : <PageShell titleKey={spec.titleKey} groupKey={spec.groupKey} />
    if (i === 0) {
      children.push({ index: true, element })
    } else {
      children.push({ path: spec.path.slice(1), element })
    }
  })

  children.push({ path: '*', element: <NotFound /> })
  return children
}

const routes: RouteObject[] = [
  {
    path: '/',
    element: <ErrorBoundary><RootLayout /></ErrorBoundary>,
    children: buildChildRoutes(),
  },
]

export const router = createBrowserRouter(routes)

/**
 * Memory router factory for tests. Uses the same routes as production.
 */
export function createTestRouter(initialEntries: string[] = ['/']): ReturnType<typeof createMemoryRouter> {
  return createMemoryRouter(routes, { initialEntries })
}
