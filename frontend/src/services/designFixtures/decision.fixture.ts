import type {
  DecisionDetailResponse,
  DecisionListResponse,
  IsoDateTime,
} from '../contracts'
import { markFixture } from './marker'

const t = (s: string): IsoDateTime => s as IsoDateTime

export const decisionListFixture: DecisionListResponse = markFixture({
  requestId: 'fx-dcl-1',
  page: {
    items: [
      {
        id: 'fx-dc-001',
        state: 'approved',
        impact: 'high',
        title: 'Isolate endpoint EDR-114 for containment',
        rationale: 'Confirmed lateral movement attempt observed.',
        decidedAt: t('2026-01-14T09:45:00Z'),
        requestedBy: 'fx-user-analyst-1',
        chain: {
          id: 'fx-chain-001',
          nodes: [
            {
              id: 'fx-node-1',
              label: 'Initial report',
              state: 'approved',
              decidedAt: t('2026-01-14T09:40:00Z'),
            },
            {
              id: 'fx-node-2',
              label: 'Containment approval',
              state: 'approved',
              decidedAt: t('2026-01-14T09:45:00Z'),
            },
          ],
          evidenceIds: ['fx-ev-001', 'fx-ev-002'],
        },
      },
      {
        id: 'fx-dc-002',
        state: 'under_review',
        impact: 'medium',
        title: 'Tighten MFA policy for admin role',
        rationale: null,
        decidedAt: null,
        requestedBy: null,
        chain: null,
      },
    ],
    nextCursor: null,
    total: 2,
  },
})

export const decisionDetailFixture: DecisionDetailResponse = markFixture({
  requestId: 'fx-dcd-1',
  decision: decisionListFixture.page.items[0]!,
})
