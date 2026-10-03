/**
 * UI-01.K.3 — Design token catalog.
 *
 * This is a static reference of the CSS custom properties defined in
 * src/app/styles.css. Values are declared explicitly because jsdom cannot
 * compute CSS var() at test time, and because we want the docs page to be
 * readable even before styles are applied.
 *
 * Rules (ADIE + DEVELOPMENT.md):
 *   - No fabrication. Tokens are copied verbatim from styles.css.
 *   - Theme-dependent tokens are labeled as such, not guessed.
 *   - This file has zero React imports (data only).
 */

export type TokenKind =
  | 'color'
  | 'spacing'
  | 'radius'
  | 'font-family'
  | 'font-size'
  | 'line-height'

export interface TokenDef {
  /** The CSS custom property name, including the --eg- prefix. */
  name: string
  /** The declared value. For theme-dependent tokens, 'theme-dependent'. */
  value: string
  /** Determines how the token is previewed. */
  kind: TokenKind
}

export interface TokenGroup {
  /** i18n key under tokenViewerPage.groups.* */
  key: string
  tokens: TokenDef[]
}

export const THEME_DEPENDENT = 'theme-dependent'

export const TOKEN_GROUPS: readonly TokenGroup[] = [
  {
    key: 'semanticColors',
    tokens: [
      { name: '--eg-trust-emerald', value: '#10b981', kind: 'color' },
      { name: '--eg-signal-blue', value: '#38bdf8', kind: 'color' },
      { name: '--eg-warning-amber', value: '#f59e0b', kind: 'color' },
      { name: '--eg-critical-red', value: '#ef4444', kind: 'color' },
      { name: '--eg-unknown-gray', value: '#6b7280', kind: 'color' },
    ],
  },
  {
    key: 'surfaces',
    tokens: [
      { name: '--eg-bg', value: THEME_DEPENDENT, kind: 'color' },
      { name: '--eg-bg-surface-1', value: THEME_DEPENDENT, kind: 'color' },
      { name: '--eg-bg-surface-2', value: THEME_DEPENDENT, kind: 'color' },
    ],
  },
  {
    key: 'borders',
    tokens: [
      { name: '--eg-border-subtle', value: THEME_DEPENDENT, kind: 'color' },
      { name: '--eg-border-strong', value: THEME_DEPENDENT, kind: 'color' },
    ],
  },
  {
    key: 'text',
    tokens: [
      { name: '--eg-text-primary', value: THEME_DEPENDENT, kind: 'color' },
      { name: '--eg-text-secondary', value: THEME_DEPENDENT, kind: 'color' },
      { name: '--eg-text-muted', value: THEME_DEPENDENT, kind: 'color' },
    ],
  },
  {
    key: 'spacing',
    tokens: [
      { name: '--eg-space-1', value: '4px', kind: 'spacing' },
      { name: '--eg-space-2', value: '8px', kind: 'spacing' },
      { name: '--eg-space-3', value: '16px', kind: 'spacing' },
      { name: '--eg-space-4', value: '24px', kind: 'spacing' },
    ],
  },
  {
    key: 'radius',
    tokens: [
      { name: '--eg-radius-sm', value: '4px', kind: 'radius' },
      { name: '--eg-radius-md', value: '6px', kind: 'radius' },
      { name: '--eg-radius-lg', value: '8px', kind: 'radius' },
      { name: '--eg-radius-xl', value: '12px', kind: 'radius' },
    ],
  },
  {
    key: 'typography',
    tokens: [
      { name: '--eg-font-sans', value: 'Inter', kind: 'font-family' },
      { name: '--eg-font-arabic', value: 'IBM Plex Sans Arabic', kind: 'font-family' },
      { name: '--eg-font-mono', value: 'JetBrains Mono', kind: 'font-family' },
      { name: '--eg-font-size-body', value: '14px', kind: 'font-size' },
      { name: '--eg-font-size-title', value: '20px', kind: 'font-size' },
      { name: '--eg-line-height-body', value: '1.5', kind: 'line-height' },
    ],
  },
] as const

export const TOTAL_TOKENS = TOKEN_GROUPS.reduce(
  (sum, g) => sum + g.tokens.length,
  0,
)
