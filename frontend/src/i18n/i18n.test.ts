import { describe, it, expect, beforeEach } from 'vitest'
import i18n, { changeLanguage, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE } from './index'

// Unicode NFC normalization — safe for canonical-equivalent Arabic variants
// (e.g. precomposed hamza vs alef + combining hamza).
const norm = (s: string): string => s.normalize('NFC')

describe('i18n infrastructure', () => {
  beforeEach(async () => {
    await changeLanguage(DEFAULT_LANGUAGE)
  })

  it('declares en and ar as supported languages', () => {
    expect(SUPPORTED_LANGUAGES).toContain('en')
    expect(SUPPORTED_LANGUAGES).toContain('ar')
  })

  it('loads resource bundles for both languages', () => {
    expect(i18n.hasResourceBundle('en', 'common')).toBe(true)
    expect(i18n.hasResourceBundle('en', 'navigation')).toBe(true)
    expect(i18n.hasResourceBundle('en', 'states')).toBe(true)
    expect(i18n.hasResourceBundle('en', 'errors')).toBe(true)
    expect(i18n.hasResourceBundle('en', 'accessibility')).toBe(true)
    expect(i18n.hasResourceBundle('ar', 'common')).toBe(true)
    expect(i18n.hasResourceBundle('ar', 'navigation')).toBe(true)
    expect(i18n.hasResourceBundle('ar', 'states')).toBe(true)
    expect(i18n.hasResourceBundle('ar', 'errors')).toBe(true)
    expect(i18n.hasResourceBundle('ar', 'accessibility')).toBe(true)
  })

  it('translates known keys in English (common ns)', async () => {
    await changeLanguage('en')
    expect(i18n.t('app.vendor')).toBe('EnterpriseGuard')
    expect(i18n.t('app.product')).toBe('ADIE')
    expect(i18n.t('actions.retry')).toBe('Retry')
    expect(i18n.t('actions.confirm')).toBe('Confirm')
  })

  it('translates known keys in English (states ns)', async () => {
    await changeLanguage('en')
    expect(i18n.t('trust.verified', { ns: 'states' })).toBe('Verified')
    expect(i18n.t('trust.unknown', { ns: 'states' })).toBe('Unknown')
    expect(i18n.t('data.notConnected', { ns: 'states' })).toBe('Not Connected')
  })

  it('translates known keys in Arabic (common ns)', async () => {
    await changeLanguage('ar')
    expect(norm(i18n.t('actions.retry'))).toBe(norm('إعادة المحاولة'))
    expect(norm(i18n.t('actions.confirm'))).toBe(norm('تأكيد'))
    expect(norm(i18n.t('actions.close'))).toBe(norm('إغلاق'))
  })

  it('translates known keys in Arabic (states ns)', async () => {
    await changeLanguage('ar')
    expect(norm(i18n.t('trust.verified', { ns: 'states' }))).toBe(norm('موثّق'))
    expect(norm(i18n.t('trust.unknown', { ns: 'states' }))).toBe(norm('غير معروف'))
    expect(norm(i18n.t('data.notConnected', { ns: 'states' }))).toBe(norm('غير متصل'))
  })

  it('uses namespace overrides', () => {
    expect(i18n.t('items.overview', { ns: 'navigation', lng: 'en' })).toBe('Overview')
    expect(norm(i18n.t('items.overview', { ns: 'navigation', lng: 'ar' }))).toBe(norm('نظرة عامة'))
  })

  it('returns the key itself for missing translations (no silent fallback)', () => {
    const missing = i18n.t('__definitely.missing.key__', { lng: 'en' })
    expect(missing).toBe('__definitely.missing.key__')
  })

  it('sets document direction to rtl for Arabic', async () => {
    await changeLanguage('ar')
    expect(document.documentElement.dir).toBe('rtl')
    expect(document.documentElement.lang).toBe('ar')
  })

  it('sets document direction to ltr for English', async () => {
    await changeLanguage('en')
    expect(document.documentElement.dir).toBe('ltr')
    expect(document.documentElement.lang).toBe('en')
  })

  it('persists language choice in localStorage', async () => {
    await changeLanguage('ar')
    expect(window.localStorage.getItem('eg.language')).toBe('ar')
    await changeLanguage('en')
    expect(window.localStorage.getItem('eg.language')).toBe('en')
  })
})
