import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { EvidencePage } from './EvidencePage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('EvidencePage', () => {
  it('renders the page title as h1', () => {
    renderWithThemeOnly(<EvidencePage />)
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1.textContent).toBe('Evidence')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<EvidencePage />)
    expect(
      screen.getByText('Verified and unverified items within the current scope'),
    ).toBeTruthy()
  })

  it('renders the workspace breadcrumb with Trust group', () => {
    renderWithThemeOnly(<EvidencePage />)
    expect(screen.getByText('Home')).toBeTruthy()
    expect(screen.getAllByText('Trust').length).toBeGreaterThan(0)
  })

  it('renders the context strip', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    expect(container.querySelector('.eg-context')).not.toBeNull()
    expect(screen.getByText('Environment')).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    const metrics = container.querySelectorAll('.eg-metric')
    expect(metrics.length).toBe(4)
  })

  it('metric cards show metric labels', () => {
    renderWithThemeOnly(<EvidencePage />)
    expect(screen.getByText('Total Items')).toBeTruthy()
    expect(screen.getAllByText('Verified').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Unknown').length).toBeGreaterThan(0)
    expect(screen.getByText('Invalid')).toBeTruthy()
  })

  it('metric cards show — when no data (no fake values)', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('metric cards show Not Connected state indicator', () => {
    renderWithThemeOnly(<EvidencePage />)
    const notConnected = screen.getAllByText('Not Connected')
    // One per metric card
    expect(notConnected.length).toBeGreaterThanOrEqual(4)
  })

  it('renders the assurance badge as Unknown', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    const badge = container.querySelector('.eg-workspace__assurance')
    expect(badge?.getAttribute('data-state')).toBe('unknown')
  })

  it('renders the enterprise table', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('table shows empty message', () => {
    renderWithThemeOnly(<EvidencePage />)
    expect(screen.getByText('No evidence available in this scope')).toBeTruthy()
  })

  it('table does NOT render fabricated rows', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<EvidencePage />)
    expect(
      screen.getByText(/Backend integration comes in a later phase/i),
    ).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any EvidenceIndicator (no fake rows)', () => {
    const { container } = renderWithThemeOnly(<EvidencePage />)
    expect(container.querySelector('.eg-evidence')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<EvidencePage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<EvidencePage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('الأدلة')
    await changeLanguage('en')
  })
})
