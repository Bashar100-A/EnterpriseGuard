import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import enCommon from './locales/en/common.json'
import enNavigation from './locales/en/navigation.json'
import enStates from './locales/en/states.json'
import enErrors from './locales/en/errors.json'
import enAccessibility from './locales/en/accessibility.json'
import enTopbar from './locales/en/topbar.json'
import enWorkspace from './locales/en/workspace.json'
import enAssurance from './locales/en/assurance.json'
import enSecurity from './locales/en/security.json'
import enDataDisplay from './locales/en/dataDisplay.json'
import enCommand from './locales/en/command.json'
import enDangerous from './locales/en/dangerous.json'
import enEvidence from './locales/en/evidence.json'
import enOverview from './locales/en/overview.json'
import enDecisions from './locales/en/decisions.json'
import enGovernance from './locales/en/governance.json'
import enHealth from './locales/en/health.json'
import enSibb from './locales/en/sibb.json'
import enProvenance from './locales/en/provenance.json'
import enOperations from './locales/en/operations.json'
import enThreat from './locales/en/threat.json'
import enPolicies from './locales/en/policies.json'
import enApprovals from './locales/en/approvals.json'
import enManifests from './locales/en/manifests.json'
import enInspection from './locales/en/inspection.json'
import enMaintenance from './locales/en/maintenance.json'
import enAnalytics from './locales/en/analytics.json'
import enReports from './locales/en/reports.json'
import enAudit from './locales/en/audit.json'
import enAccess from './locales/en/access.json'
import enConfig from './locales/en/config.json'
import enShortcuts from './locales/en/shortcuts.json'
import enToast from './locales/en/toast.json'
import enDrawer from './locales/en/drawer.json'

import arCommon from './locales/ar/common.json'
import arNavigation from './locales/ar/navigation.json'
import arStates from './locales/ar/states.json'
import arErrors from './locales/ar/errors.json'
import arAccessibility from './locales/ar/accessibility.json'
import arTopbar from './locales/ar/topbar.json'
import arWorkspace from './locales/ar/workspace.json'
import arAssurance from './locales/ar/assurance.json'
import arSecurity from './locales/ar/security.json'
import arDataDisplay from './locales/ar/dataDisplay.json'
import arCommand from './locales/ar/command.json'
import arDangerous from './locales/ar/dangerous.json'
import arEvidence from './locales/ar/evidence.json'
import arOverview from './locales/ar/overview.json'
import arDecisions from './locales/ar/decisions.json'
import arGovernance from './locales/ar/governance.json'
import arHealth from './locales/ar/health.json'
import arSibb from './locales/ar/sibb.json'
import arProvenance from './locales/ar/provenance.json'
import arOperations from './locales/ar/operations.json'
import arThreat from './locales/ar/threat.json'
import arPolicies from './locales/ar/policies.json'
import arApprovals from './locales/ar/approvals.json'
import arManifests from './locales/ar/manifests.json'
import arInspection from './locales/ar/inspection.json'
import arMaintenance from './locales/ar/maintenance.json'
import arAnalytics from './locales/ar/analytics.json'
import arReports from './locales/ar/reports.json'
import arAudit from './locales/ar/audit.json'
import arAccess from './locales/ar/access.json'
import arConfig from './locales/ar/config.json'
import arShortcuts from './locales/ar/shortcuts.json'
import arToast from './locales/ar/toast.json'
import arDrawer from './locales/ar/drawer.json'

export const SUPPORTED_LANGUAGES = ['en', 'ar'] as const
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

export const DEFAULT_LANGUAGE: SupportedLanguage = 'en'
export const LANGUAGE_STORAGE_KEY = 'eg.language'

export const NAMESPACES = [
  'common',
  'navigation',
  'states',
  'errors',
  'accessibility',
  'topbar',
  'workspace',
  'assurance',
  'security',
  'dataDisplay',
  'command',
  'dangerous',
  'evidence',
  'overview',
  'decisions',
  'governance',
  'health',
  'sibb',
  'provenance',
  'operations',
  'threat',
  'policies',
  'approvals',
  'manifests',
  'inspection',
  'maintenance',
  'analytics',
  'reports',
  'audit',
  'access',
  'config',
  'shortcuts',
  'toast',
  'drawer',
] as const

function isSupported(value: string | null | undefined): value is SupportedLanguage {
  return value === 'en' || value === 'ar'
}

function detectInitialLanguage(): SupportedLanguage {
  if (typeof window === 'undefined') return DEFAULT_LANGUAGE
  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
  return isSupported(stored) ? stored : DEFAULT_LANGUAGE
}

const resources = {
  en: {
    common: enCommon,
    navigation: enNavigation,
    states: enStates,
    errors: enErrors,
    accessibility: enAccessibility,
    topbar: enTopbar,
    workspace: enWorkspace,
    assurance: enAssurance,
    security: enSecurity,
    dataDisplay: enDataDisplay,
    command: enCommand,
    dangerous: enDangerous,
    evidence: enEvidence,
    overview: enOverview,
    decisions: enDecisions,
    governance: enGovernance,
    health: enHealth,
    sibb: enSibb,
    provenance: enProvenance,
    operations: enOperations,
    threat: enThreat,
    policies: enPolicies,
    approvals: enApprovals,
    manifests: enManifests,
    inspection: enInspection,
    maintenance: enMaintenance,
    analytics: enAnalytics,
    reports: enReports,
    audit: enAudit,
    access: enAccess,
    config: enConfig,
    shortcuts: enShortcuts,
    toast: enToast,
    drawer: enDrawer,
  },
  ar: {
    common: arCommon,
    navigation: arNavigation,
    states: arStates,
    errors: arErrors,
    accessibility: arAccessibility,
    topbar: arTopbar,
    workspace: arWorkspace,
    assurance: arAssurance,
    security: arSecurity,
    dataDisplay: arDataDisplay,
    command: arCommand,
    dangerous: arDangerous,
    evidence: arEvidence,
    overview: arOverview,
    decisions: arDecisions,
    governance: arGovernance,
    health: arHealth,
    sibb: arSibb,
    provenance: arProvenance,
    operations: arOperations,
    threat: arThreat,
    policies: arPolicies,
    approvals: arApprovals,
    manifests: arManifests,
    inspection: arInspection,
    maintenance: arMaintenance,
    analytics: arAnalytics,
    reports: arReports,
    audit: arAudit,
    access: arAccess,
    config: arConfig,
    shortcuts: arShortcuts,
    toast: arToast,
    drawer: arDrawer,
  },
}

function applyDocumentDirection(lang: SupportedLanguage): void {
  if (typeof document === 'undefined') return
  document.documentElement.lang = lang
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
}

const initialLang = detectInitialLanguage()

void i18n.use(initReactI18next).init({
  resources,
  lng: initialLang,
  fallbackLng: DEFAULT_LANGUAGE,
  defaultNS: 'common',
  ns: [...NAMESPACES],
  interpolation: { escapeValue: false },
  returnNull: false,
})

applyDocumentDirection(initialLang)

export async function changeLanguage(lang: SupportedLanguage): Promise<void> {
  await i18n.changeLanguage(lang)
  applyDocumentDirection(lang)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, lang)
  }
}

export default i18n
