/**
 * UI-01.J.2 — Observation layer (Evidence).
 *
 * Semantic note (ADIE):
 *   Evidence is what was OBSERVED. It never implies authority or decision.
 */

import type { IsoDateTime, Page, PageRequest, RequestMeta } from './types'

export type EvidenceSource =
  | 'sibb'
  | 'external'
  | 'internal'
  | 'manual'
  | 'unknown'

export type EvidenceVerification =
  | 'verified'
  | 'unverified'
  | 'invalid'
  | 'unknown'

export interface Evidence {
  id: string
  source: EvidenceSource
  verification: EvidenceVerification
  observedAt: IsoDateTime
  collectedAt: IsoDateTime
  summary: string
  payload: Record<string, unknown> | null
  provenanceId: string | null
  tags: string[]
}

export interface EvidenceListRequest extends PageRequest {
  verification: EvidenceVerification | null
  source: EvidenceSource | null
}

export interface EvidenceListResponse extends RequestMeta {
  page: Page<Evidence>
}

export interface EvidenceDetailResponse extends RequestMeta {
  evidence: Evidence
}
