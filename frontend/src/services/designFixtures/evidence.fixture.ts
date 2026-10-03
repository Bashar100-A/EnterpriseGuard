import type {
  EvidenceDetailResponse,
  EvidenceListResponse,
  IsoDateTime,
} from '../contracts'
import { markFixture } from './marker'

const t = (s: string): IsoDateTime => s as IsoDateTime

export const evidenceListFixture: EvidenceListResponse = markFixture({
  requestId: 'fx-evl-1',
  page: {
    items: [
      {
        id: 'fx-ev-001',
        source: 'sibb',
        verification: 'verified',
        observedAt: t('2026-01-14T09:12:00Z'),
        collectedAt: t('2026-01-14T09:12:05Z'),
        summary: 'Signed integrity check passed for control C-17',
        payload: null,
        provenanceId: 'fx-prov-001',
        tags: ['integrity', 'sibb'],
      },
      {
        id: 'fx-ev-002',
        source: 'external',
        verification: 'unverified',
        observedAt: t('2026-01-14T09:30:00Z'),
        collectedAt: t('2026-01-14T09:31:12Z'),
        summary: 'Threat feed returned a new IOC batch',
        payload: null,
        provenanceId: null,
        tags: ['threat', 'ioc'],
      },
      {
        id: 'fx-ev-003',
        source: 'manual',
        verification: 'unknown',
        observedAt: t('2026-01-14T10:05:00Z'),
        collectedAt: t('2026-01-14T10:05:00Z'),
        summary: 'Analyst note attached to incident INC-2041',
        payload: null,
        provenanceId: null,
        tags: ['note'],
      },
    ],
    nextCursor: null,
    total: 3,
  },
})

export const evidenceDetailFixture: EvidenceDetailResponse = markFixture({
  requestId: 'fx-evd-1',
  evidence: evidenceListFixture.page.items[0]!,
})
