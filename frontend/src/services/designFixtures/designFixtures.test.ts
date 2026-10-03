import { describe, it, expect } from 'vitest'
import {
  FIXTURE_MARKER,
  FixtureLeakError,
  assertNotFixture,
  isFixture,
  markFixture,
} from './marker'
import {
  evidenceListFixture,
  evidenceDetailFixture,
  decisionListFixture,
  decisionDetailFixture,
  manifestListFixture,
  manifestDetailFixture,
  policyListFixture,
  policyDetailFixture,
  auditListFixture,
} from './index'

describe('marker — primitives', () => {
  it('FIXTURE_MARKER is a non-empty string', () => {
    expect(typeof FIXTURE_MARKER).toBe('string')
    expect(FIXTURE_MARKER.length).toBeGreaterThan(0)
  })

  it('markFixture sets the marker non-enumerably', () => {
    const o = markFixture({ a: 1 })
    expect(isFixture(o)).toBe(true)
    expect(Object.keys(o)).toEqual(['a'])
  })

  it('markFixture survives Object.keys filtering', () => {
    const o = markFixture({ a: 1, b: 2 })
    expect(Object.keys(o).sort()).toEqual(['a', 'b'])
  })

  it('markFixture survives JSON.stringify cleanly', () => {
    const o = markFixture({ a: 1 })
    expect(JSON.stringify(o)).toBe('{"a":1}')
  })

  it('isFixture returns false for plain objects', () => {
    expect(isFixture({ a: 1 })).toBe(false)
  })

  it('isFixture returns false for null', () => {
    expect(isFixture(null)).toBe(false)
  })

  it('isFixture returns false for primitives', () => {
    expect(isFixture(1)).toBe(false)
    expect(isFixture('x')).toBe(false)
    expect(isFixture(undefined)).toBe(false)
  })

  it('assertNotFixture throws FixtureLeakError', () => {
    const o = markFixture({ a: 1 })
    expect(() => assertNotFixture(o, 'prod-path')).toThrow(FixtureLeakError)
  })

  it('FixtureLeakError carries code + message', () => {
    const e = new FixtureLeakError('page.evidence')
    expect(e.code).toBe('FIXTURE_LEAK')
    expect(e.message).toContain('page.evidence')
    expect(e.name).toBe('FixtureLeakError')
  })

  it('assertNotFixture passes for plain values', () => {
    expect(() => assertNotFixture({ a: 1 }, 'x')).not.toThrow()
    expect(() => assertNotFixture(null, 'x')).not.toThrow()
    expect(() => assertNotFixture(42, 'x')).not.toThrow()
  })
})

describe('fixtures — evidence', () => {
  it('evidenceListFixture is marked', () => {
    expect(isFixture(evidenceListFixture)).toBe(true)
  })

  it('evidenceListFixture carries requestId', () => {
    expect(evidenceListFixture.requestId).toMatch(/^fx-/)
  })

  it('evidenceListFixture page.items is non-empty', () => {
    expect(evidenceListFixture.page.items.length).toBeGreaterThan(0)
  })

  it('every evidence has an id and verification', () => {
    for (const ev of evidenceListFixture.page.items) {
      expect(typeof ev.id).toBe('string')
      expect(['verified', 'unverified', 'invalid', 'unknown']).toContain(ev.verification)
    }
  })

  it('evidenceDetailFixture is marked', () => {
    expect(isFixture(evidenceDetailFixture)).toBe(true)
  })
})

describe('fixtures — decision / manifest / policy / audit', () => {
  it('decisionListFixture is marked and non-empty', () => {
    expect(isFixture(decisionListFixture)).toBe(true)
    expect(decisionListFixture.page.items.length).toBeGreaterThan(0)
  })

  it('decision chain nodes reference evidence ids', () => {
    const d = decisionListFixture.page.items[0]!
    expect(d.chain).not.toBeNull()
    expect(Array.isArray(d.chain!.evidenceIds)).toBe(true)
  })

  it('manifestListFixture is marked and carries a decisionId', () => {
    expect(isFixture(manifestListFixture)).toBe(true)
    for (const m of manifestListFixture.page.items) {
      expect(typeof m.decisionId).toBe('string')
    }
  })

  it('manifest executions are arrays', () => {
    for (const m of manifestListFixture.page.items) {
      expect(Array.isArray(m.executions)).toBe(true)
    }
  })

  it('policyListFixture is marked and carries versions array', () => {
    expect(isFixture(policyListFixture)).toBe(true)
    for (const p of policyListFixture.page.items) {
      expect(Array.isArray(p.versions)).toBe(true)
    }
  })

  it('auditListFixture is marked and outcomes are valid', () => {
    expect(isFixture(auditListFixture)).toBe(true)
    for (const a of auditListFixture.page.items) {
      expect(['success', 'failure', 'denied', 'unknown']).toContain(a.outcome)
    }
  })

  it('every fixture is JSON-serializable without the marker', () => {
    const samples = [
      evidenceListFixture,
      decisionListFixture,
      manifestListFixture,
      policyListFixture,
      auditListFixture,
    ]
    for (const s of samples) {
      const j = JSON.stringify(s)
      expect(j).not.toContain(FIXTURE_MARKER)
      const round = JSON.parse(j) as object
      expect(isFixture(round)).toBe(false)
    }
  })

  it('detail fixtures wrap the first list item (no drift)', () => {
    expect(evidenceDetailFixture.evidence).toBe(
      evidenceListFixture.page.items[0],
    )
    expect(decisionDetailFixture.decision).toBe(
      decisionListFixture.page.items[0],
    )
    expect(manifestDetailFixture.manifest).toBe(
      manifestListFixture.page.items[0],
    )
    expect(policyDetailFixture.policy).toBe(
      policyListFixture.page.items[0],
    )
  })
})
