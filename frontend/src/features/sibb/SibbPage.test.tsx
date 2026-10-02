import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { SibbPage } from './SibbPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('SibbPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('SIBB Trust Core')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByText(/The integrity foundation/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByText('Chain Height')).toBeTruthy()
    expect(screen.getByText('Baseline State')).toBeTruthy()
    expect(screen.getByText('Last Checkpoint')).toBeTruthy()
    expect(screen.getByText('Signed Items')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders the TrustChainVisual', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(container.querySelector('[data-testid="eg-trust-chain"]')).not.toBeNull()
  })

  it('TrustChainVisual shows "Root not established" (no fake hash)', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByText(/Root not established/i)).toBeTruthy()
  })

  it('does NOT render any TechnicalIdentifier (no fake root hash)', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('renders the Merkle section header', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByText('Merkle Chain')).toBeTruthy()
  })

  it('renders four integrity indicators', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(container.querySelectorAll('.eg-sibb__integrity-item').length).toBe(4)
  })

  it('integrity items show the four labels', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByText('Baseline')).toBeTruthy()
    expect(screen.getByText('Chain')).toBeTruthy()
    expect(screen.getByText('Signature')).toBeTruthy()
    expect(screen.getByText('Storage')).toBeTruthy()
  })

  it('renders the checkpoints table', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('checkpoints table shows empty message', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByText('No checkpoints recorded in this scope')).toBeTruthy()
  })

  it('checkpoints table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Trust group', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getAllByText('Trust').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('does NOT render any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<SibbPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<SibbPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('نواة الثقة SIBB')
    await changeLanguage('en')
  })
})
