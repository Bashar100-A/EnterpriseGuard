import { describe, it, expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import type { ReactElement } from 'react'

import { renderWithProviders } from './renderWithProviders'
import { runA11y, summarizeViolations, formatViolations } from './a11y'
import { KNOWN_A11Y_VIOLATIONS } from './a11y.known'

import {
  DocsPage,
  PlaygroundPage,
  TokenViewerPage,
  IconCatalogPage,
  SemanticGuidePage,
} from '../features/docs'
import { OverviewPage } from '../features/overview'
import { EvidencePage } from '../features/evidence'
import { HealthPage } from '../features/health'
import { ConfigPage } from '../features/config'

afterEach(() => {
  cleanup()
})

interface AuditCase {
  name: keyof typeof KNOWN_A11Y_VIOLATIONS | string
  element: ReactElement
}

/**
 * Audit surface for L.1. Covers docs, overview, evidence, health, config.
 * Additional pages are added as we progress; the allowlist (a11y.known.ts)
 * tracks findings that are pending a dedicated fix.
 */
const CASES: AuditCase[] = [
  { name: 'DocsPage',          element: <DocsPage /> },
  { name: 'PlaygroundPage',    element: <PlaygroundPage /> },
  { name: 'TokenViewerPage',   element: <TokenViewerPage /> },
  { name: 'IconCatalogPage',   element: <IconCatalogPage /> },
  { name: 'SemanticGuidePage', element: <SemanticGuidePage /> },
  { name: 'OverviewPage',      element: <OverviewPage /> },
  { name: 'EvidencePage',      element: <EvidencePage /> },
  { name: 'HealthPage',        element: <HealthPage /> },
  { name: 'ConfigPage',        element: <ConfigPage /> },
]

describe('a11y audit — axe-core (WCAG 2.2 AA subset)', () => {
  for (const { name, element } of CASES) {
    it(`${name} has no unexpected axe violations`, async () => {
      const { container } = renderWithProviders(element)
      const results = await runA11y(container)
      const summaries = summarizeViolations(results)

      const allowed = new Set(KNOWN_A11Y_VIOLATIONS[name] ?? [])
      const known = summaries.filter((s) => allowed.has(s.id))
      const unexpected = summaries.filter((s) => !allowed.has(s.id))

      // Always log what we saw — even "known" ones — so the report shows
      // the exact state of a11y on each page for this commit.
      if (summaries.length > 0) {
        // eslint-disable-next-line no-console
        console.info(
          '\n' +
            `[a11y] ${name}: ${summaries.length} total ` +
            `(${known.length} known, ${unexpected.length} unexpected)`,
        )
        if (known.length > 0) {
          // eslint-disable-next-line no-console
          console.info(formatViolations(`${name} (known)`, known))
        }
        if (unexpected.length > 0) {
          // eslint-disable-next-line no-console
          console.error(formatViolations(`${name} (UNEXPECTED)`, unexpected))
        }
      }

      expect(unexpected).toEqual([])
    })
  }
})
