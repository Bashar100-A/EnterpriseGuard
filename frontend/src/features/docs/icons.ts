/**
 * UI-01.K.4 — Icon adoption registry.
 *
 * The ADIE UI is deliberately icon-light at this stage: navigation is text,
 * state is expressed via semantic dots (StateIndicator), and no Lucide icon
 * is currently imported anywhere in src/.
 *
 * This file is the SINGLE place to register an icon when it is adopted:
 *   1. Import the component from 'lucide-react' in the consuming module.
 *   2. Add a record here describing its name, purpose, and where it appears.
 *   3. The IconCatalogPage will pick it up automatically.
 *
 * Rules (ADIE):
 *   - No speculation: an icon is 'adopted' only after real usage exists.
 *   - 'candidate' entries are non-authoritative and must be labeled as such.
 *   - This file has zero imports (data only), like tokens.ts.
 */

export type IconStatus = 'adopted' | 'candidate'

export interface IconAdoption {
  /** Lucide component name (e.g., 'ShieldCheck'). */
  name: string
  /** i18n key under iconCatalogPage.purpose.* explaining why it exists. */
  purposeKey: string
  /** Where the icon appears (informational, free text). */
  where: string
  status: IconStatus
}

/**
 * Icons actually imported and rendered in the app.
 * MUST stay empty until an icon is used in a real page.
 */
export const ADOPTED_ICONS: readonly IconAdoption[] = []

/**
 * Icons under consideration but not yet used. Never rendered as live usage.
 */
export const CANDIDATE_ICONS: readonly IconAdoption[] = []

export const TOTAL_ADOPTED = ADOPTED_ICONS.length
export const TOTAL_CANDIDATES = CANDIDATE_ICONS.length
