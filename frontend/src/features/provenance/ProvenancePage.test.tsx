import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { ProvenancePage } from './ProvenancePage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('ProvenancePage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Provenance')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByText(/Where each item came from/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByText('Sources')).toBeTruthy()
    expect(screen.getByText('Chains')).toBeTruthy()
    expect(screen.getByText('Verified Links')).toBeTruthy()
    expect(screen.getByText('Unresolved Links')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders the legend section', () => {
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByText('Legend')).toBeTruthy()
  })

  it('renders three legend items with EvidenceIndicator', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    expect(container.querySelectorAll('.eg-prov__legend-item').length).toBe(3)
  })

  it('legend covers verified, unverified, unknown', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    const states = container.querySelectorAll('[data-evidence]')
    expect(states.length).toBeGreaterThanOrEqual(3)
  })

  it('renders the provenance table', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('table shows empty message', () => {
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByText('No provenance records in this scope')).toBeTruthy()
  })

  it('table does NOT render fabricated rows', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Trust group', () => {
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getAllByText('Trust').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<ProvenancePage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<ProvenancePage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('المصدرية')
    await changeLanguage('en')
  })
})
