/**
 * UI-01.J.2 — Audit trail.
 *
 * Semantic note (ADIE):
 *   Audit events are recorded facts. They never claim causality.
 */

import type { IsoDateTime, Page, PageRequest, RequestMeta } from './types'

export type AuditActorKind = 'human' | 'system' | 'external' | 'unknown'

export interface AuditActor {
  kind: AuditActorKind
  id: string | null
  displayName: string | null
}

export interface AuditEvent {
  id: string
  occurredAt: IsoDateTime
  actor: AuditActor
  action: string
  targetKind: string
  targetId: string | null
  outcome: 'success' | 'failure' | 'denied' | 'unknown'
  details: Record<string, unknown> | null
}

export interface AuditListRequest extends PageRequest {
  actorKind: AuditActorKind | null
  outcome: AuditEvent['outcome'] | null
}

export interface AuditListResponse extends RequestMeta {
  page: Page<AuditEvent>
}
