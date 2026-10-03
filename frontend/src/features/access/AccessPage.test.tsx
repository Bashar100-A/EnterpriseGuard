import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { AccessPage } from './AccessPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('AccessPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Users & Access')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByText(/Accounts, roles, and the permissions matrix/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<AccessPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByText('Active Users')).toBeTruthy()
    expect(screen.getAllByText('Roles').length).toBeGreaterThan(0)
    expect(screen.getByText('Active Sessions')).toBeTruthy()
    expect(screen.getByText('Pending Invites')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<AccessPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders the permissions matrix note', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByText('Permissions Matrix')).toBeTruthy()
    expect(screen.getByText(/The UI does not grant permissions/i)).toBeTruthy()
  })

  it('renders two EnterpriseTables (users + roles)', () => {
    const { container } = renderWithThemeOnly(<AccessPage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('users table shows empty message', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByText('No users in this scope')).toBeTruthy()
  })

  it('roles table shows empty message', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByText('No roles in this scope')).toBeTruthy()
  })

  it('tables have no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<AccessPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Administration group', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getAllByText('Administration').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<AccessPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByText(/No users are fabricated/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<AccessPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<AccessPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<AccessPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('المستخدمون والصلاحيات')
    await changeLanguage('en')
  })
})
