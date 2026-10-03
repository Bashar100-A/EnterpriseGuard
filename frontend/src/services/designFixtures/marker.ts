/**
 * UI-01.J.6 — Fixture marker.
 *
 * Fixtures are for the /docs playground ONLY. Production pages must NEVER
 * consume them. To make that provable, every fixture object carries a
 * non-enumerable `__egFixture` flag that survives `structuredClone` but
 * is invisible to `JSON.stringify`.
 *
 *   assertNotFixture(value)  // throws if a fixture leaks into production
 *   isFixture(value)         // boolean, for filtering in dev tools
 */

export const FIXTURE_MARKER = '__egFixture' as const

export function markFixture<T extends object>(obj: T): T {
  Object.defineProperty(obj, FIXTURE_MARKER, {
    value: true,
    enumerable: false,
    writable: false,
    configurable: false,
  })
  return obj
}

export function isFixture(value: unknown): boolean {
  if (typeof value !== 'object' || value === null) return false
  return (
    (value as Record<string, unknown>)[FIXTURE_MARKER] === true
  )
}

export class FixtureLeakError extends Error {
  readonly code = 'FIXTURE_LEAK'

  constructor(where: string) {
    super(`Fixture value leaked into production path: ${where}`)
    this.name = 'FixtureLeakError'
  }
}

export function assertNotFixture(value: unknown, where: string): void {
  if (isFixture(value)) {
    throw new FixtureLeakError(where)
  }
}
