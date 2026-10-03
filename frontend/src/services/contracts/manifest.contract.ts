/**
 * UI-01.J.2 — Execution layer (Manifests).
 *
 * Semantic note (ADIE):
 *   Manifests describe WHAT WILL BE / WAS executed.
 *   They are downstream of a Decision; they are not decisions.
 */

import type { IsoDateTime, Page, PageRequest, RequestMeta } from './types'

export type ManifestState =
  | 'draft'
  | 'pending_authorization'
  | 'authorized'
  | 'executing'
  | 'executed'
  | 'failed'
  | 'cancelled'
  | 'unknown'

export interface ManifestExecution {
  id: string
  startedAt: IsoDateTime | null
  finishedAt: IsoDateTime | null
  outcome: 'success' | 'failure' | 'partial' | 'unknown'
  log: string | null
}

export interface Manifest {
  id: string
  decisionId: string
  state: ManifestState
  summary: string
  target: string | null
  createdAt: IsoDateTime
  executions: ManifestExecution[]
}

export interface ManifestListRequest extends PageRequest {
  state: ManifestState | null
  decisionId: string | null
}

export interface ManifestListResponse extends RequestMeta {
  page: Page<Manifest>
}

export interface ManifestDetailResponse extends RequestMeta {
  manifest: Manifest
}
