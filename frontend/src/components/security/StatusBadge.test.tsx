import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { StatusBadge, toneForStatus } from './StatusBadge'
import type { StatusKey } from './StatusBadge'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('StatusBadge', () => {
  it('renders the translated label for verified', () => {
    renderWithThemeOnly(<StatusBadge status="verified" />)
    expect(screen.getByText('Verified')).toBeTruthy()
  })

  it('renders the translated label for unknown', () => {
    renderWithThemeOnly(<StatusBadge status="unknown" />)
    expect(screen.getByText('Unknown')).toBeTruthy()
  })

  it('sets data-tone=trust for verified', () => {
    const { container } = renderWithThemeOnly(<StatusBadge status="verified" />)
    expect(container.querySelector('[data-tone="trust"]')).not.toBeNull()
  })

  it('sets data-tone=critical for critical', () => {
    const { container } = renderWithThemeOnly(<StatusBadge status="critical" />)
    expect(container.querySelector('[data-tone="critical"]')).not.toBeNull()
  })

  it('sets data-tone=unknown for unknown', () => {
    const { container } = renderWithThemeOnly(<StatusBadge status="unknown" />)
    expect(container.querySelector('[data-tone="unknown"]')).not.toBeNull()
  })

  it('never maps unknown to trust', () => {
    expect(toneForStatus('unknown')).toBe('unknown')
    expect(toneForStatus('notConnected')).toBe('unknown')
    expect(toneForStatus('unavailable')).toBe('unknown')
    expect(toneForStatus('notEvaluated')).toBe('unknown')
  })

  it('maps degraded and stale to warning', () => {
    expect(toneForStatus('degraded')).toBe('warning')
    expect(toneForStatus('stale')).toBe('warning')
  })

  it('maps verificationFailed to critical', () => {
    expect(toneForStatus('verificationFailed')).toBe('critical')
  })

  it('accepts a custom label override', () => {
    renderWithThemeOnly(<StatusBadge status="verified" label="Custom" />)
    expect(screen.getByText('Custom')).toBeTruthy()
  })

  it('renders a dot when withDot is true', () => {
    const { container } = renderWithThemeOnly(<StatusBadge status="verified" withDot />)
    expect(container.querySelector('.eg-badge__dot')).not.toBeNull()
  })

  it('does not render a dot by default', () => {
    const { container } = renderWithThemeOnly(<StatusBadge status="verified" />)
    expect(container.querySelector('.eg-badge__dot')).toBeNull()
  })

  it('exposes data-status for test targeting', () => {
    const { container } = renderWithThemeOnly(<StatusBadge status="pending" />)
    expect(container.querySelector('[data-status="pending"]')).not.toBeNull()
  })

  it('renders all 18 status keys without crashing', () => {
    const all: StatusKey[] = [
      'verified', 'validated', 'healthy',
      'pending', 'proposed', 'information',
      'reviewRequired', 'degraded', 'stale', 'policyConflict',
      'critical', 'verificationFailed', 'boundaryViolation', 'error',
      'unknown', 'unavailable', 'notEvaluated', 'notConnected',
    ]
    for (const status of all) {
      const { container } = renderWithThemeOnly(<StatusBadge status={status} />)
      expect(container.querySelector(`[data-status="${status}"]`)).not.toBeNull()
      cleanup()
    }
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<StatusBadge status="verified" />)
    expect(screen.getByText('موثّق')).toBeTruthy()
    await changeLanguage('en')
  })
})
