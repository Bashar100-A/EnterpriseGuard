import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { HealthPage } from './HealthPage'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('HealthPage', () => {
  it('renders the title as h1', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('System Health')
  })

  it('renders the description', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getAllByText(/Live operational state of services, resources/i).length).toBeGreaterThan(0)
  })

  it('renders four metric cards', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelectorAll('.eg-metric').length).toBe(4)
  })

  it('renders all metric labels', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getAllByText('Uptime').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Availability').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Latency P99').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Error Rate').length).toBeGreaterThan(0)
  })

  it('metric values are — (no fake telemetry)', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    const values = container.querySelectorAll('.eg-metric__value')
    expect(values.length).toBe(4)
    for (const v of Array.from(values)) {
      expect(v.textContent).toBe('—')
    }
  })

  it('renders the RadarDimensions', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getByTestId('eg-radar')).toBeTruthy()
  })

  it('radar contains 6 axes', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelectorAll('.eg-radar__axis')).toHaveLength(6)
  })

  it('radar contains 6 vertex dots', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelectorAll('.eg-radar__vertex-group circle')).toHaveLength(6)
  })

  it('radar shows 6 dimensions in the header', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    const value = container.querySelector('.eg-radar__stat-value')
    expect(value?.textContent).toBe('6')
  })

  it('radar polygon uses unknown tone (no data)', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelector('.eg-radar__polygon')?.getAttribute('data-tone')).toBe('unknown')
  })

  it('renders two chart frames', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelectorAll('.eg-chartframe').length).toBe(2)
  })

  it('chart frames show resource titles', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getAllByText('CPU Usage').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Memory Usage').length).toBeGreaterThan(0)
  })

  it('chart frames are empty (no fake resource charts)', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    const frames = container.querySelectorAll('.eg-chartframe')
    for (const f of Array.from(frames)) {
      expect(f.getAttribute('data-state')).toBe('empty')
    }
  })

  it('renders the services table', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelector('.eg-table')).not.toBeNull()
  })

  it('services table shows empty message', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getAllByText('No services registered in this scope').length).toBeGreaterThan(0)
  })

  it('services table has no fabricated rows', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelectorAll('.eg-table tbody tr')).toHaveLength(0)
  })

  it('breadcrumb includes Operate group', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getAllByText('Operate').length).toBeGreaterThan(0)
  })

  it('renders the assurance badge as Unknown', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(
      container.querySelector('.eg-workspace__assurance')?.getAttribute('data-state'),
    ).toBe('unknown')
  })

  it('renders the backend note', () => {
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getAllByText(/Backend integration comes in a later phase/i).length).toBeGreaterThan(0)
  })

  it('does NOT contain any TechnicalIdentifier (no fake IDs)', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelector('.eg-tech-id')).toBeNull()
  })

  it('does NOT contain any StatusBadge (no fake service states)', () => {
    const { container } = renderWithThemeOnly(<HealthPage />)
    expect(container.querySelector('.eg-badge--status')).toBeNull()
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<HealthPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('صحة النظام')
    await changeLanguage('en')
  })
})
