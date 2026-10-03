/**
 * Minimal ambient declaration for jest-axe.
 *
 * jest-axe ships without bundled types and we prefer not to depend on
 * `@types/jest-axe` for a project of this size. The declaration below is
 * exactly what we use: `axe(element, options) → { violations: [...] }`.
 *
 * If jest-axe's runtime surface changes, this file MUST be updated.
 */

declare module 'jest-axe' {
  export interface AxeNode {
    target: string | string[]
    html: string
    failureSummary?: string
  }

  export interface AxeViolation {
    id: string
    impact: string | null
    description: string
    help: string
    helpUrl: string
    tags: string[]
    nodes: AxeNode[]
  }

  export interface AxeResults {
    violations: AxeViolation[]
    passes: unknown[]
    incomplete: unknown[]
    inapplicable: unknown[]
  }

  export interface AxeOptions {
    rules?: Record<string, { enabled: boolean }>
  }

  export function axe(
    element: Element | string,
    options?: AxeOptions,
  ): Promise<AxeResults>
}
