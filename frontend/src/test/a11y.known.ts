/**
 * UI-01.L.1 — Known accessibility violations (allowlist).
 *
 * axe-core has been run against key pages and produced these findings.
 * They are recorded here so the CI fails only on NEW violations, and so
 * that each one is tracked and fixed deliberately in the follow-up step.
 *
 * ==================================================================
 *  TODO (L.1b) — resolve each of these in a dedicated script:
 * ==================================================================
 *
 *  OverviewPage
 *    - heading-order:    an <h3> inside ChartFrame is reached without a
 *                        preceding <h2> in the same section. Fix: either
 *                        promote the chart section header to <h2> or add
 *                        a heading-agnostic wrapper.
 *    - landmark-unique:  the chart region carries an aria-label that
 *                        collides with another landmark (the page
 *                        container). Fix: give it a unique aria-label
 *                        or downgrade to a plain <div>.
 *
 *  HealthPage
 *    - heading-order:    same root cause as OverviewPage.
 *    - landmark-unique:  same class as OverviewPage; needs a unique
 *                        label. Sample target is a chartframe element.
 *
 *  EvidencePage
 *    - landmark-unique:  .eg-evidence-page__metrics collides with
 *                        another region; likely two sections with the
 *                        same aria-label ("Metrics").
 * ==================================================================
 *
 * Removing an entry from this map is the definition of "fixed".
 * Adding an entry requires a comment justifying why it's acceptable.
 */

export const KNOWN_A11Y_VIOLATIONS: Readonly<
  Record<string, readonly string[]>
> = Object.freeze({
  OverviewPage: ['heading-order', 'landmark-unique'],
  HealthPage: ['heading-order', 'landmark-unique'],
  EvidencePage: ['landmark-unique'],
})
