import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { EnvironmentBadge } from './EnvironmentBadge'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('EnvironmentBadge', () => {
  it('renders the translated label for production', () => {
    renderWithThemeOnly(<EnvironmentBadge environment="production" />)
    expect(screen.getByText('Production')).toBeTruthy()
  })

  it('renders the translated label for staging', () => {
    renderWithThemeOnly(<EnvironmentBadge environment="staging" />)
    expect(screen.getByText('Staging')).toBeTruthy()
  })

  it('renders the translated label for development', () => {
    renderWithThemeOnly(<EnvironmentBadge environment="development" />)
    expect(screen.getByText('Development')).toBeTruthy()
  })

  it('renders the translated label for test', () => {
    renderWithThemeOnly(<EnvironmentBadge environment="test" />)
    expect(screen.getByText('Test')).toBeTruthy()
  })

  it('renders the translated label for unknown', () => {
    renderWithThemeOnly(<EnvironmentBadge environment="unknown" />)
    expect(screen.getByText('Unknown')).toBeTruthy()
  })

  it('sets data-environment for CSS and test targeting', () => {
    const { container } = renderWithThemeOnly(<EnvironmentBadge environment="production" />)
    expect(container.querySelector('[data-environment="production"]')).not.toBeNull()
  })

  it('does NOT set a data-tone (environment is not a tone)', () => {
    const { container } = renderWithThemeOnly(<EnvironmentBadge environment="production" />)
    expect(container.querySelector('[data-tone]')).toBeNull()
  })

  it('accepts a custom label override', () => {
    renderWithThemeOnly(<EnvironmentBadge environment="production" label="PROD" />)
    expect(screen.getByText('PROD')).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<EnvironmentBadge environment="production" />)
    expect(screen.getByText('الإنتاج')).toBeTruthy()
    await changeLanguage('en')
  })
})
