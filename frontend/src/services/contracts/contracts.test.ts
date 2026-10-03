import { describe, it, expect, expectTypeOf } from 'vitest'
import {
  DEFAULT_PAGE_LIMIT,
  MAX_PAGE_LIMIT,
} from './types'
import type {
  AuditEvent,
  AuditListResponse,
  Decision,
  DecisionListResponse,
  Evidence,
  EvidenceListResponse,
  IsoDateTime,
  Manifest,
  ManifestListResponse,
  Page,
  Policy,
  PolicyListResponse,
} from './index'

describe('contracts — shared primitives', () => {
  it('DEFAULT_PAGE_LIMIT is 50', () => {
    expect(DEFAULT_PAGE_LIMIT).toBe(50)
  })

  it('MAX_PAGE_LIMIT is 200', () => {
    expect(MAX_PAGE_LIMIT).toBe(200)
  })

  it('MAX_PAGE_LIMIT > DEFAULT_PAGE_LIMIT', () => {
    expect(MAX_PAGE_LIMIT).toBeGreaterThan(DEFAULT_PAGE_LIMIT)
  })
})

describe('contracts — type-level invariants', () => {
  it('Page<T> exposes items/nextCursor/total', () => {
    type P = Page<{ id: string }>
    expectTypeOf<P['items']>().toEqualTypeOf<{ id: string }[]>()
    expectTypeOf<P['nextCursor']>().toEqualTypeOf<string | null>()
    expectTypeOf<P['total']>().toEqualTypeOf<number>()
  })

  it('EvidenceListResponse carries requestId + page', () => {
    const r: EvidenceListResponse = {
      requestId: 'r-1',
      page: { items: [], nextCursor: null, total: 0 },
    }
    expect(r.requestId).toBe('r-1')
    expect(r.page.items).toEqual([])
  })

  it('DecisionListResponse carries requestId + page', () => {
    const r: DecisionListResponse = {
      requestId: 'r-2',
      page: { items: [], nextCursor: null, total: 0 },
    }
    expect(r.requestId).toBe('r-2')
  })

  it('ManifestListResponse carries requestId + page', () => {
    const r: ManifestListResponse = {
      requestId: 'r-3',
      page: { items: [], nextCursor: null, total: 0 },
    }
    expect(r.requestId).toBe('r-3')
  })

  it('PolicyListResponse carries requestId + page', () => {
    const r: PolicyListResponse = {
      requestId: 'r-4',
      page: { items: [], nextCursor: null, total: 0 },
    }
    expect(r.requestId).toBe('r-4')
  })

  it('AuditListResponse carries requestId + page', () => {
    const r: AuditListResponse = {
      requestId: 'r-5',
      page: { items: [], nextCursor: null, total: 0 },
    }
    expect(r.requestId).toBe('r-5')
  })
})

describe('contracts — semantic separation (ADIE)', () => {
  it('Evidence has source + verification + observedAt; no decision fields', () => {
    const e: Evidence = {
      id: 'ev-1',
      source: 'sibb',
      verification: 'verified',
      observedAt: '2026-01-01T00:00:00Z' as IsoDateTime,
      collectedAt: '2026-01-01T00:00:00Z' as IsoDateTime,
      summary: 'x',
      payload: null,
      provenanceId: null,
      tags: [],
    }
    expect(e.source).toBe('sibb')
    // @ts-expect-error Evidence must not carry a `decision` field
    void e.decision
  })

  it('Decision has state + impact; no execution field', () => {
    const d: Decision = {
      id: 'd-1',
      state: 'proposed',
      impact: 'low',
      title: 'x',
      rationale: null,
      decidedAt: null,
      requestedBy: null,
      chain: null,
    }
    expect(d.state).toBe('proposed')
    // @ts-expect-error Decision must not carry an `execution` field
    void d.execution
  })

  it('Manifest has decisionId + executions; not a decision', () => {
    const m: Manifest = {
      id: 'm-1',
      decisionId: 'd-1',
      state: 'draft',
      summary: 'x',
      target: null,
      createdAt: '2026-01-01T00:00:00Z' as IsoDateTime,
      executions: [],
    }
    expect(m.decisionId).toBe('d-1')
    // @ts-expect-error Manifest must not carry a `rationale` field
    void m.rationale
  })

  it('Policy has versions; not an execution', () => {
    const p: Policy = {
      id: 'p-1',
      key: 'auth.mfa',
      title: 'MFA',
      currentVersionId: null,
      versions: [],
    }
    expect(p.key).toBe('auth.mfa')
    // @ts-expect-error Policy must not carry an `executions` field
    void p.executions
  })

  it('AuditEvent has actor + outcome; not a policy', () => {
    const a: AuditEvent = {
      id: 'a-1',
      occurredAt: '2026-01-01T00:00:00Z' as IsoDateTime,
      actor: { kind: 'system', id: null, displayName: null },
      action: 'read',
      targetKind: 'evidence',
      targetId: null,
      outcome: 'success',
      details: null,
    }
    expect(a.actor.kind).toBe('system')
    // @ts-expect-error AuditEvent must not carry a `versions` field
    void a.versions
  })

  it('null is used for missing optional fields (not undefined)', () => {
    const e: Evidence = {
      id: 'ev-2',
      source: 'unknown',
      verification: 'unknown',
      observedAt: '2026-01-01T00:00:00Z' as IsoDateTime,
      collectedAt: '2026-01-01T00:00:00Z' as IsoDateTime,
      summary: 'x',
      payload: null,
      provenanceId: null,
      tags: [],
    }
    expect(e.payload).toBeNull()
    expect(e.provenanceId).toBeNull()
  })
})
