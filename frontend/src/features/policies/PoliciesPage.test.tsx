import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { PoliciesPage } from './PoliciesPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('PoliciesPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Policies')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByText(/The rules that govern decisions/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<PoliciesPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByText('Active Policies')).toBeTruthy()
    expect(screen.getByText('Drafts')).toBeTruthy()
    expect(screen.getByText('Expiring Soon')).toBeTruthy()
    expect(screen.getByText('Conflicts')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<PoliciesPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders two EnterpriseTables (catalog + versions)', () => {
    const { container } = renderWithThemeOnly(<PoliciesPage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('catalog table shows empty message', () => {
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByText('No policies configured in this scope')).toBeTruthy()
  })

  it('versions table shows empty message', () => {
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByText('No version activity in this scope')).toBeTruthy()
  })

  it('tables have no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<PoliciesPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Govern group', () => {
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getAllByText('Govern').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<PoliciesPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<PoliciesPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<PoliciesPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<PoliciesPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('السياسات')
    await changeLanguage('en')
  })
})
