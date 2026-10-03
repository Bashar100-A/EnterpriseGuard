import type {
  PolicyDetailResponse,
  PolicyListResponse,
  IsoDateTime,
} from '../contracts'
import { markFixture } from './marker'

const t = (s: string): IsoDateTime => s as IsoDateTime

export const policyListFixture: PolicyListResponse = markFixture({
  requestId: 'fx-pll-1',
  page: {
    items: [
      {
        id: 'fx-pl-001',
        key: 'auth.mfa.admin',
        title: 'MFA required for administrator role',
        currentVersionId: 'fx-pv-001b',
        versions: [
          {
            id: 'fx-pv-001a',
            version: 1,
            state: 'retired',
            effectiveAt: t('2025-11-01T00:00:00Z'),
            retiredAt: t('2026-01-10T00:00:00Z'),
            notes: null,
          },
          {
            id: 'fx-pv-001b',
            version: 2,
            state: 'active',
            effectiveAt: t('2026-01-10T00:00:00Z'),
            retiredAt: null,
            notes: 'Extends MFA coverage to break-glass accounts.',
          },
        ],
      },
      {
        id: 'fx-pl-002',
        key: 'data.retention.default',
        title: 'Default data retention window',
        currentVersionId: null,
        versions: [],
      },
    ],
    nextCursor: null,
    total: 2,
  },
})

export const policyDetailFixture: PolicyDetailResponse = markFixture({
  requestId: 'fx-pld-1',
  policy: policyListFixture.page.items[0]!,
})
