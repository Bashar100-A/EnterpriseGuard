import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { ThreatPage } from './ThreatPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('ThreatPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Threat Intelligence')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByText(/Threat feeds, indicators of compromise/i)).toBeTruthy()
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByText('Active Threats')).toBeTruthy()
    expect(screen.getByText('Indicators (IOCs)')).toBeTruthy()
    expect(screen.getByText('Feeds Active')).toBeTruthy()
    expect(screen.getByText('Last Update')).toBeTruthy()
  })

  it('metric values are — (no fake numbers)', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders one chart frame (threat volume)', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    expect(container.querySelectorAll('.eg-chartframe').length).toBe(1)
  })

  it('chart frame shows its title', () => {
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByText('Threat Volume')).toBeTruthy()
  })

  it('chart frame is in empty state (no fake chart)', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    const frame = container.querySelector('.eg-chartframe')
    expect(frame?.getAttribute('data-state')).toBe('empty')
  })

  it('renders the IOC table', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('IOC table shows empty message', () => {
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByText('No indicators in this scope')).toBeTruthy()
  })

  it('IOC table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Intelligence group', () => {
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getAllByText('Intelligence').length).toBeGreaterThan(0)
  })

  it('assurance badge is Unknown', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByText(/Backend integration comes in a later phase/i)).toBeTruthy()
  })

  it('does NOT contain any TechnicalIdentifier (no fake IOCs)', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any SeverityBadge (no fake threats)', () => {
    const { container } = renderWithThemeOnly(<ThreatPage />)
    expect(container.querySelector('.eg-badge--severity')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<ThreatPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('استخبارات التهديدات')
    await changeLanguage('en')
  })
})
