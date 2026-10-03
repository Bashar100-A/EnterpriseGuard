/**
 * UI-01.J.2 — Decision layer.
 *
 * Semantic note (ADIE):
 *   A Decision is never equal to its Execution, nor to its Evidence.
 */

import type { IsoDateTime, Page, PageRequest, RequestMeta } from './types'

export type DecisionState =
  | 'proposed'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'unknown'

export type DecisionImpact = 'low' | 'medium' | 'high' | 'critical' | 'unknown'

export interface DecisionNode {
  id: string
  label: string
  state: DecisionState
  decidedAt: IsoDateTime | null
}

export interface DecisionChain {
  id: string
  nodes: DecisionNode[]
  evidenceIds: string[]
}

export interface Decision {
  id: string
  state: DecisionState
  impact: DecisionImpact
  title: string
  rationale: string | null
  decidedAt: IsoDateTime | null
  requestedBy: string | null
  chain: DecisionChain | null
}

export interface DecisionListRequest extends PageRequest {
  state: DecisionState | null
  impact: DecisionImpact | null
}

export interface DecisionListResponse extends RequestMeta {
  page: Page<Decision>
}

export interface DecisionDetailResponse extends RequestMeta {
  decision: Decision
}
