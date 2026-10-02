import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { OperationsPage } from './OperationsPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('OperationsPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Security Operations')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getByText(/Active incident queue, response actions/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getByText('Active Incidents')).toBeTruthy()
    expect(screen.getByText('Critical')).toBeTruthy()
    expect(screen.getByText('Resolved (24h)')).toBeTruthy()
    expect(screen.getByText('MTTR')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('shows Not Connected on all metrics', () => {
    renderWithThemeOnly(<OperationsPage />)
    const nc = screen.getAllByText('Not Connected')
    expect(nc.length).toBeGreaterThanOrEqual(4)
  })

  it('renders the incidents table', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('incidents table shows empty message', () => {
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getByText('No active incidents in this scope')).toBeTruthy()
  })

  it('incidents table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Intelligence group', () => {
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getAllByText('Intelligence').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any SeverityBadge (no fake incidents)', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    expect(container.querySelector('.eg-badge--severity')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<OperationsPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<OperationsPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('العمليات الأمنية')
    await changeLanguage('en')
  })
})
