import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { TrustChainVisual } from './TrustChainVisual'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('TrustChainVisual', () => {
  it('renders with role=img', () => {
    renderWithThemeOnly(<TrustChainVisual root={null} height={null} />)
    expect(screen.getByRole('img')).toBeTruthy()
  })

  it('state=unknown when root is null', () => {
    const { container } = renderWithThemeOnly(<TrustChainVisual root={null} height={null} />)
    expect(container.querySelector('[data-state="unknown"]')).not.toBeNull()
  })

  it('shows root unavailable message when root is null', () => {
    renderWithThemeOnly(<TrustChainVisual root={null} height={null} />)
    expect(screen.getByText(/Root not established/i)).toBeTruthy()
  })

  it('state=ready when root is provided', () => {
    const { container } = renderWithThemeOnly(
      <TrustChainVisual root="deadbeefcafebabe0123456789abcdef" height={42} />,
    )
    expect(container.querySelector('[data-state="ready"]')).not.toBeNull()
  })

  it('renders TechnicalIdentifier for a provided root', () => {
    const { container } = renderWithThemeOnly(
      <TrustChainVisual root="deadbeefcafebabe0123456789abcdef" height={42} />,
    )
    expect(container.querySelector('.eg-tech-id')).not.toBeNull()
  })

  it('renders the root caption', () => {
    renderWithThemeOnly(<TrustChainVisual root={null} height={null} />)
    expect(screen.getByText('root')).toBeTruthy()
  })

  it('compact mode renders fewer leaves', () => {
    const { container: full } = renderWithThemeOnly(
      <TrustChainVisual root={null} height={null} />,
    )
    const fullLeaves = full.querySelectorAll('.eg-trust-chain__leaf').length
    cleanup()
    const { container: compact } = renderWithThemeOnly(
      <TrustChainVisual root={null} height={null} compact />,
    )
    const compactLeaves = compact.querySelectorAll('.eg-trust-chain__leaf').length
    expect(compactLeaves).toBeLessThan(fullLeaves)
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<TrustChainVisual root={null} height={null} />)
    expect(screen.getByText(/لم يتم إنشاء الجذر/)).toBeTruthy()
    await changeLanguage('en')
  })
})
