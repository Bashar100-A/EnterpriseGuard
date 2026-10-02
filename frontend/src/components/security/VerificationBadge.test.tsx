import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { VerificationBadge } from './VerificationBadge'
import { toneForVerification } from './tone'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('VerificationBadge', () => {
  it('renders the translated label for verified', () => {
    renderWithThemeOnly(<VerificationBadge state="verified" />)
    expect(screen.getByText('Verified')).toBeTruthy()
  })

  it('renders the translated label for unverified', () => {
    renderWithThemeOnly(<VerificationBadge state="unverified" />)
    expect(screen.getByText('Unverified')).toBeTruthy()
  })

  it('renders the translated label for invalid', () => {
    renderWithThemeOnly(<VerificationBadge state="invalid" />)
    expect(screen.getByText('Invalid')).toBeTruthy()
  })

  it('maps verified to tone=trust', () => {
    expect(toneForVerification('verified')).toBe('trust')
  })

  it('maps unverified to tone=warning', () => {
    expect(toneForVerification('unverified')).toBe('warning')
  })

  it('maps invalid to tone=critical', () => {
    expect(toneForVerification('invalid')).toBe('critical')
  })

  it('maps unknown and notAvailable to tone=unknown', () => {
    expect(toneForVerification('unknown')).toBe('unknown')
    expect(toneForVerification('notAvailable')).toBe('unknown')
  })

  it('sets data-verification for test targeting', () => {
    const { container } = renderWithThemeOnly(<VerificationBadge state="verified" />)
    expect(container.querySelector('[data-verification="verified"]')).not.toBeNull()
  })

  it('accepts a custom label override', () => {
    renderWithThemeOnly(<VerificationBadge state="unknown" label="Pending review" />)
    expect(screen.getByText('Pending review')).toBeTruthy()
  })

  it('renders all five states without crashing', () => {
    const all = ['verified', 'unverified', 'invalid', 'unknown', 'notAvailable'] as const
    for (const s of all) {
      const { container } = renderWithThemeOnly(<VerificationBadge state={s} />)
      expect(container.querySelector(`[data-verification="${s}"]`)).not.toBeNull()
      cleanup()
    }
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<VerificationBadge state="verified" />)
    expect(screen.getByText('موثّق')).toBeTruthy()
    await changeLanguage('en')
  })
})
