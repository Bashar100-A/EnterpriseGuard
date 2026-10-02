import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import enCommon from './locales/en/common.json'
import enNavigation from './locales/en/navigation.json'
import enStates from './locales/en/states.json'
import enErrors from './locales/en/errors.json'
import enAccessibility from './locales/en/accessibility.json'

import arCommon from './locales/ar/common.json'
import arNavigation from './locales/ar/navigation.json'
import arStates from './locales/ar/states.json'
import arErrors from './locales/ar/errors.json'
import arAccessibility from './locales/ar/accessibility.json'

export const SUPPORTED_LANGUAGES = ['en', 'ar'] as const
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

export const DEFAULT_LANGUAGE: SupportedLanguage = 'en'
export const LANGUAGE_STORAGE_KEY = 'eg.language'

export const NAMESPACES = ['common', 'navigation', 'states', 'errors', 'accessibility'] as const

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
  },
  ar: {
    common: arCommon,
    navigation: arNavigation,
    states: arStates,
    errors: arErrors,
    accessibility: arAccessibility,
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
