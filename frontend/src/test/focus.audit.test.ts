import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * UI-01.L.4 — Focus-visible coverage regression test.
 *
 * This test reads src/app/styles.css as plain text and asserts that each
 * critical interactive selector still has a :focus-visible rule. It is
 * intentionally a file-content test: jsdom does not evaluate CSS selectors
 * against live DOM, so a behavioral test would give false confidence.
 *
 * Adding a new interactive primitive?
 *   1. Ensure it carries a :focus-visible rule (or a compatible global one).
 *   2. Register its className below.
 */

const CSS_PATH = resolve(__dirname, '..', 'app', 'styles.css')
const CSS = readFileSync(CSS_PATH, 'utf-8')

/**
 * Critical interactive selectors that MUST have an explicit :focus-visible
 * rule. Kept in sync with the "Focus Policy" section in DEVELOPMENT.md.
 */
const REQUIRED_FOCUS_SELECTORS: readonly string[] = [
  // Shell / navigation
  'eg-nav__item',
  'eg-nav__toggle',
  'eg-topbar__icon-btn',
  'eg-topbar__lang-btn',
  'eg-topbar__search',
  // Boundary / state
  'eg-boundary__retry',
  'eg-datastate__action',
  // Data display
  'eg-tech-id__copy',
  'eg-chartframe__expand',
  'eg-chartframe__retry',
  'eg-table__sort',
  'eg-table__retry',
  // Command palette (Phase L.4)
  'eg-cmd__close',
  'eg-cmd__item',
  // Dangerous actions
  'eg-danger__close',
  'eg-danger__btn',
  // Domain-specific
  'eg-chain__stage-btn',
  'eg-governance__propose',
  'eg-inspection__run',
  // Dialog & shell chrome
  'eg-assurance__close',
  'eg-shortcuts__close',
  'eg-drawer__close',
  // Toast
  'eg-toast__action',
  'eg-toast__close',
  // Tree (Phase L.4)
  'eg-tree__toggle',
  'eg-tree__node',
  'eg-tree__row',
]

function escapeForRegex(s: string): string {
  return s.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')
}

function hasFocusVisibleRule(className: string): boolean {
  const escaped = escapeForRegex(className)
  // Match `.className:focus-visible` (regardless of surrounding selectors)
  return new RegExp(`\\.${escaped}:focus-visible`).test(CSS)
}

describe('focus.audit — :focus-visible coverage in styles.css', () => {
  for (const cls of REQUIRED_FOCUS_SELECTORS) {
    it(`.${cls} has a :focus-visible rule`, () => {
      expect(hasFocusVisibleRule(cls)).toBe(true)
    })
  }
})

describe('focus.audit — global fallback', () => {
  it('a global :focus-visible rule exists (not prefixed by a class)', () => {
    // Look for `:focus-visible {` not immediately preceded by a class name.
    // We detect it by checking for the pattern in a context where the
    // preceding character is a newline or whitespace.
    const globalRule = /(^|\n)\s*:focus-visible\s*\{/m
    expect(globalRule.test(CSS)).toBe(true)
  })

  it('the global rule uses the signal-blue token', () => {
    const m = CSS.match(/(^|\n)\s*:focus-visible\s*\{([^}]*)\}/m)
    expect(m).not.toBeNull()
    if (m) {
      expect(m[2]).toContain('var(--eg-signal-blue)')
    }
  })
})

describe('focus.audit — sanity', () => {
  it('the CSS file is non-trivial (> 1000 lines)', () => {
    const lines = CSS.split('\n').length
    expect(lines).toBeGreaterThan(1000)
  })

  it('there are at least 25 :focus-visible rules', () => {
    const matches = CSS.match(/:focus-visible/g)
    expect(matches).not.toBeNull()
    expect((matches ?? []).length).toBeGreaterThanOrEqual(25)
  })
})
