/**
 * UI-01.L.1 — Shared accessibility test helper.
 *
 * Wraps axe-core (via jest-axe) with:
 *   - Color-contrast disabled (jsdom cannot evaluate it; checked in Phase N).
 *   - A JSON-friendly summary that we can log when a violation appears.
 */

import { axe } from 'jest-axe'
import type { AxeResults, AxeViolation } from 'jest-axe'

export type A11yRunResult = AxeResults

export interface A11yViolationSummary {
  id: string
  impact: string | null
  description: string
  help: string
  helpUrl: string
  nodes: number
  sampleTarget: string | null
}

export async function runA11y(container: HTMLElement): Promise<A11yRunResult> {
  return axe(container, {
    rules: {
      // jsdom has no layout engine, so computed color is unreliable here.
      // Contrast is covered in Phase N (Playwright + real browser).
      'color-contrast': { enabled: false },
    },
  })
}

function targetOf(v: AxeViolation): string | null {
  const node = v.nodes[0]
  if (!node || !node.target) return null
  return Array.isArray(node.target) ? node.target.join(' ') : String(node.target)
}

export function summarizeViolations(
  results: A11yRunResult,
): A11yViolationSummary[] {
  return results.violations.map((v) => ({
    id: v.id,
    impact: v.impact,
    description: v.description,
    help: v.help,
    helpUrl: v.helpUrl,
    nodes: v.nodes.length,
    sampleTarget: targetOf(v),
  }))
}

export function formatViolations(
  label: string,
  summaries: A11yViolationSummary[],
): string {
  const lines = [`${label}: ${summaries.length} violation(s)`]
  for (const s of summaries) {
    lines.push(`  - ${s.id} [${s.impact ?? 'n/a'}] ${s.nodes} node(s)`)
    lines.push(`      help:    ${s.help}`)
    lines.push(`      target:  ${s.sampleTarget ?? '(n/a)'}`)
    lines.push(`      more:    ${s.helpUrl}`)
  }
  return lines.join('\n')
}
