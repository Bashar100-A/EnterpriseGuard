import type {
  AuditListResponse,
  IsoDateTime,
} from '../contracts'
import { markFixture } from './marker'

const t = (s: string): IsoDateTime => s as IsoDateTime

export const auditListFixture: AuditListResponse = markFixture({
  requestId: 'fx-aul-1',
  page: {
    items: [
      {
        id: 'fx-au-001',
        occurredAt: t('2026-01-14T09:45:01Z'),
        actor: { kind: 'human', id: 'fx-user-analyst-1', displayName: 'Analyst' },
        action: 'decision.approve',
        targetKind: 'decision',
        targetId: 'fx-dc-001',
        outcome: 'success',
        details: null,
      },
      {
        id: 'fx-au-002',
        occurredAt: t('2026-01-14T09:46:32Z'),
        actor: { kind: 'system', id: null, displayName: 'executor' },
        action: 'manifest.execute',
        targetKind: 'manifest',
        targetId: 'fx-mf-001',
        outcome: 'success',
        details: null,
      },
      {
        id: 'fx-au-003',
        occurredAt: t('2026-01-14T10:00:00Z'),
        actor: { kind: 'human', id: 'fx-user-analyst-2', displayName: 'Analyst' },
        action: 'manifest.request_authorization',
        targetKind: 'manifest',
        targetId: 'fx-mf-002',
        outcome: 'denied',
        details: null,
      },
    ],
    nextCursor: null,
    total: 3,
  },
})
