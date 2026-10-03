import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { MaintenancePage } from './MaintenancePage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('MaintenancePage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Maintenance')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByText(/Planned changes, verification, rollback/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByText('Scheduled')).toBeTruthy()
    expect(screen.getByText('In Progress')).toBeTruthy()
    expect(screen.getByText('Completed (24h)')).toBeTruthy()
    expect(screen.getByText('Rollback Ready')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders four capability items', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    expect(container.querySelectorAll('.eg-maintenance__capability-item').length).toBe(4)
  })

  it('renders capability labels', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByText('Planned Changes')).toBeTruthy()
    expect(screen.getByText('Verification')).toBeTruthy()
    expect(screen.getByText('Rollback')).toBeTruthy()
    expect(screen.getByText('History')).toBeTruthy()
  })

  it('renders two EnterpriseTables (schedule + history)', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('schedule table shows empty message', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByText('No maintenance scheduled in this scope')).toBeTruthy()
  })

  it('history table shows empty message', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByText('No maintenance history in this scope')).toBeTruthy()
  })

  it('tables have no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Operate group', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getAllByText('Operate').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByText(/Rollback and repair require backend authority/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<MaintenancePage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<MaintenancePage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('الصيانة')
    await changeLanguage('en')
  })
})
