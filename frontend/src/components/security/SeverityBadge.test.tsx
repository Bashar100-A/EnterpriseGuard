import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { SeverityBadge } from './SeverityBadge'
import { toneForSeverity } from './tone'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('SeverityBadge', () => {
  it('renders the translated label for info', () => {
    renderWithThemeOnly(<SeverityBadge severity="info" />)
    expect(screen.getByText('Info')).toBeTruthy()
  })

  it('renders the translated label for critical', () => {
    renderWithThemeOnly(<SeverityBadge severity="critical" />)
    expect(screen.getByText('Critical')).toBeTruthy()
  })

  it('maps info to tone=info', () => {
    expect(toneForSeverity('info')).toBe('info')
  })

  it('maps medium and high to tone=warning', () => {
    expect(toneForSeverity('medium')).toBe('warning')
    expect(toneForSeverity('high')).toBe('warning')
  })

  it('maps critical to tone=critical', () => {
    expect(toneForSeverity('critical')).toBe('critical')
  })

  it('sets data-severity for test targeting', () => {
    const { container } = renderWithThemeOnly(<SeverityBadge severity="high" />)
    expect(container.querySelector('[data-severity="high"]')).not.toBeNull()
  })

  it('accepts custom label override', () => {
    renderWithThemeOnly(<SeverityBadge severity="low" label="Minor" />)
    expect(screen.getByText('Minor')).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<SeverityBadge severity="critical" />)
    expect(screen.getByText('حرج')).toBeTruthy()
    await changeLanguage('en')
  })
})
