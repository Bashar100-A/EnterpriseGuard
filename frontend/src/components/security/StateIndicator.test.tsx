import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { StateIndicator } from './StateIndicator'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('StateIndicator', () => {
  it('renders the label', () => {
    renderWithThemeOnly(<StateIndicator tone="trust" label="Healthy" />)
    expect(screen.getByText('Healthy')).toBeTruthy()
  })

  it('renders a dot', () => {
    const { container } = renderWithThemeOnly(<StateIndicator tone="trust" label="x" />)
    expect(container.querySelector('.eg-indicator__dot')).not.toBeNull()
  })

  it('sets data-tone', () => {
    const { container } = renderWithThemeOnly(<StateIndicator tone="critical" label="x" />)
    expect(container.querySelector('[data-tone="critical"]')).not.toBeNull()
  })

  it('defaults to size=md', () => {
    const { container } = renderWithThemeOnly(<StateIndicator tone="trust" label="x" />)
    expect(container.querySelector('[data-size="md"]')).not.toBeNull()
  })

  it('accepts size=sm', () => {
    const { container } = renderWithThemeOnly(<StateIndicator tone="trust" label="x" size="sm" />)
    expect(container.querySelector('[data-size="sm"]')).not.toBeNull()
  })

  it('accepts size=lg', () => {
    const { container } = renderWithThemeOnly(<StateIndicator tone="trust" label="x" size="lg" />)
    expect(container.querySelector('[data-size="lg"]')).not.toBeNull()
  })

  it('uses title from prop when provided', () => {
    const { container } = renderWithThemeOnly(
      <StateIndicator tone="unknown" label="x" title="No data" />,
    )
    expect(container.querySelector('[title="No data"]')).not.toBeNull()
  })

  it('falls back to translated title when absent', () => {
    const { container } = renderWithThemeOnly(<StateIndicator tone="unknown" label="x" />)
    expect(container.querySelector('[title="State indicator"]')).not.toBeNull()
  })
})
