import type {
  ManifestDetailResponse,
  ManifestListResponse,
  IsoDateTime,
} from '../contracts'
import { markFixture } from './marker'

const t = (s: string): IsoDateTime => s as IsoDateTime

export const manifestListFixture: ManifestListResponse = markFixture({
  requestId: 'fx-mfl-1',
  page: {
    items: [
      {
        id: 'fx-mf-001',
        decisionId: 'fx-dc-001',
        state: 'executed',
        summary: 'EDR-114 network isolation',
        target: 'endpoint:EDR-114',
        createdAt: t('2026-01-14T09:46:00Z'),
        executions: [
          {
            id: 'fx-ex-001',
            startedAt: t('2026-01-14T09:46:10Z'),
            finishedAt: t('2026-01-14T09:46:32Z'),
            outcome: 'success',
            log: null,
          },
        ],
      },
      {
        id: 'fx-mf-002',
        decisionId: 'fx-dc-002',
        state: 'pending_authorization',
        summary: 'MFA policy tightening (awaiting authorization)',
        target: 'policy:auth.mfa',
        createdAt: t('2026-01-14T10:00:00Z'),
        executions: [],
      },
    ],
    nextCursor: null,
    total: 2,
  },
})

export const manifestDetailFixture: ManifestDetailResponse = markFixture({
  requestId: 'fx-mfd-1',
  manifest: manifestListFixture.page.items[0]!,
})
