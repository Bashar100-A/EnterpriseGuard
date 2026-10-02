import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { EvidenceIndicator } from './EvidenceIndicator'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('EvidenceIndicator', () => {
  it('renders the label for verified state', () => {
    renderWithThemeOnly(<EvidenceIndicator state="verified" />)
    expect(screen.getByText(/Verified evidence/i)).toBeTruthy()
  })

  it('renders the label for notAvailable state', () => {
    renderWithThemeOnly(<EvidenceIndicator state="notAvailable" />)
    expect(screen.getByText(/No evidence/i)).toBeTruthy()
  })

  it('sets data-tone=trust for verified', () => {
    const { container } = renderWithThemeOnly(<EvidenceIndicator state="verified" />)
    expect(container.querySelector('[data-tone="trust"]')).not.toBeNull()
  })

  it('sets data-tone=critical for invalid', () => {
    const { container } = renderWithThemeOnly(<EvidenceIndicator state="invalid" />)
    expect(container.querySelector('[data-tone="critical"]')).not.toBeNull()
  })

  it('sets data-evidence for test targeting', () => {
    const { container } = renderWithThemeOnly(<EvidenceIndicator state="unknown" />)
    expect(container.querySelector('[data-evidence="unknown"]')).not.toBeNull()
  })

  it('renders a dot', () => {
    const { container } = renderWithThemeOnly(<EvidenceIndicator state="verified" />)
    expect(container.querySelector('.eg-evidence__dot')).not.toBeNull()
  })

  it('shows the count when provided', () => {
    renderWithThemeOnly(<EvidenceIndicator state="verified" count={17} />)
    expect(screen.getByText('17')).toBeTruthy()
  })

  it('does NOT show count when absent', () => {
    const { container } = renderWithThemeOnly(<EvidenceIndicator state="verified" />)
    expect(container.querySelector('.eg-evidence__count')).toBeNull()
  })

  it('compact mode hides label but shows dot and count', () => {
    const { container } = renderWithThemeOnly(
      <EvidenceIndicator state="verified" count={5} compact />,
    )
    expect(container.querySelector('.eg-evidence--compact')).not.toBeNull()
    expect(container.querySelector('.eg-evidence__label')).toBeNull()
    expect(container.querySelector('.eg-evidence__dot')).not.toBeNull()
    expect(screen.getByText('5')).toBeTruthy()
  })

  it('accepts custom label', () => {
    renderWithThemeOnly(<EvidenceIndicator state="verified" label="Owned" />)
    expect(screen.getByText('Owned')).toBeTruthy()
  })

  it('renders all five states without crashing', () => {
    const all = ['verified', 'unverified', 'invalid', 'unknown', 'notAvailable'] as const
    for (const s of all) {
      const { container } = renderWithThemeOnly(<EvidenceIndicator state={s} />)
      expect(container.querySelector(`[data-evidence="${s}"]`)).not.toBeNull()
      cleanup()
    }
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<EvidenceIndicator state="verified" />)
    expect(screen.getByText(/أدلة موثّقة/)).toBeTruthy()
    await changeLanguage('en')
  })
})
