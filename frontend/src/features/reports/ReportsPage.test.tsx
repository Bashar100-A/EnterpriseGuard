import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { ReportsPage } from './ReportsPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('ReportsPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Reports')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByText(/Report catalog, scheduled deliveries/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<ReportsPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByText('Available Reports')).toBeTruthy()
    expect(screen.getByText('Scheduled')).toBeTruthy()
    expect(screen.getByText('Generated (24h)')).toBeTruthy()
    expect(screen.getByText('Failed (24h)')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<ReportsPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders two EnterpriseTables (catalog + deliveries)', () => {
    const { container } = renderWithThemeOnly(<ReportsPage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('catalog table shows empty message', () => {
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByText('No reports in this scope')).toBeTruthy()
  })

  it('deliveries table shows empty message', () => {
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByText('No scheduled deliveries in this scope')).toBeTruthy()
  })

  it('tables have no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<ReportsPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Assurance group', () => {
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getAllByText('Assurance').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<ReportsPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByText(/Export and delivery require the backend/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<ReportsPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<ReportsPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<ReportsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('التقارير')
    await changeLanguage('en')
  })
})
