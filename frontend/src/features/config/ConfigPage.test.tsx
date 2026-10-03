import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { ConfigPage } from './ConfigPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('ConfigPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Configuration')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByText(/System settings, feature flags/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels (using getAllByText for safety)', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getAllByText('Settings').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Feature Flags').length).toBeGreaterThan(0)
    expect(screen.getByText('Overrides')).toBeTruthy()
    expect(screen.getByText('Last Change')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders five config group chips', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    expect(container.querySelectorAll('.eg-config__group-item').length).toBe(5)
  })

  it('renders all group labels', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByText('General')).toBeTruthy()
    expect(screen.getByText('Security')).toBeTruthy()
    expect(screen.getByText('Integrations')).toBeTruthy()
    expect(screen.getByText('Performance')).toBeTruthy()
    expect(screen.getByText('Notifications')).toBeTruthy()
  })

  it('renders two EnterpriseTables (settings + flags)', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    expect(container.querySelectorAll('.eg-table').length).toBe(2)
  })

  it('settings table shows empty message', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByText('No settings configured in this scope')).toBeTruthy()
  })

  it('flags table shows empty message', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByText('No feature flags in this scope')).toBeTruthy()
  })

  it('tables have no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Administration group', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getAllByText('Administration').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByText(/UI never writes configuration/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake states)', () => {
    const { container } = renderWithThemeOnly(<ConfigPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<ConfigPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('الإعدادات')
    await changeLanguage('en')
  })
})
