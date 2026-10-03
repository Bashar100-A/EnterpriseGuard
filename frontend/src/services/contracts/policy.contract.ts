/**
 * UI-01.J.2 — Authority layer (Policies).
 *
 * Semantic note (ADIE):
 *   Policies define authority. They do not themselves act.
 */

import type { IsoDateTime, Page, PageRequest, RequestMeta } from './types'

export type PolicyState = 'draft' | 'active' | 'retired' | 'unknown'

export interface PolicyVersion {
  id: string
  version: number
  state: PolicyState
  effectiveAt: IsoDateTime | null
  retiredAt: IsoDateTime | null
  notes: string | null
}

export interface Policy {
  id: string
  key: string
  title: string
  currentVersionId: string | null
  versions: PolicyVersion[]
}

export interface PolicyListRequest extends PageRequest {
  state: PolicyState | null
}

export interface PolicyListResponse extends RequestMeta {
  page: Page<Policy>
}

export interface PolicyDetailResponse extends RequestMeta {
  policy: Policy
}
