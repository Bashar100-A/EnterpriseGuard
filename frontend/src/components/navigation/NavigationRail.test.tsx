import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import '../../i18n'
import { NavigationRail } from './NavigationRail'
import type { NavigationItem } from './NavigationRail'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
  window.localStorage.clear()
})

describe('NavigationRail', () => {
  it('renders a <nav> landmark', () => {
    const { container } = render(
      <NavigationRail expanded={false} onToggleExpanded={() => {}} />,
    )
    expect(container.querySelector('nav.eg-nav')).not.toBeNull()
  })

  it('renders in collapsed mode by default (class + data attr)', () => {
    const { container } = render(
      <NavigationRail expanded={false} onToggleExpanded={() => {}} />,
    )
    const nav = container.querySelector('nav.eg-nav')
    expect(nav?.classList.contains('eg-nav--collapsed')).toBe(true)
    expect(nav?.getAttribute('data-expanded')).toBe('false')
  })

  it('renders in expanded mode when expanded=true', () => {
    const { container } = render(
      <NavigationRail expanded onToggleExpanded={() => {}} />,
    )
    const nav = container.querySelector('nav.eg-nav')
    expect(nav?.classList.contains('eg-nav--expanded')).toBe(true)
    expect(nav?.getAttribute('data-expanded')).toBe('true')
  })

  it('renders all 20 navigation items', () => {
    render(<NavigationRail expanded onToggleExpanded={() => {}} />)
    const buttons = screen.getAllByRole('button').filter((b) =>
      b.classList.contains('eg-nav__item'),
    )
    expect(buttons).toHaveLength(20)
  })

  it('renders all 7 group labels in expanded mode', () => {
    render(<NavigationRail expanded onToggleExpanded={() => {}} />)
    expect(screen.getByText('Command')).toBeTruthy()
    expect(screen.getByText('Intelligence')).toBeTruthy()
    expect(screen.getByText('Trust')).toBeTruthy()
    expect(screen.getByText('Govern')).toBeTruthy()
    expect(screen.getByText('Operate')).toBeTruthy()
    expect(screen.getByText('Assurance')).toBeTruthy()
    expect(screen.getByText('Administration')).toBeTruthy()
  })

  it('does NOT render group labels in collapsed mode', () => {
    render(<NavigationRail expanded={false} onToggleExpanded={() => {}} />)
    expect(screen.queryByText('Command')).toBeNull()
    expect(screen.queryByText('Intelligence')).toBeNull()
  })

  it('marks the active item with aria-current=page', () => {
    render(
      <NavigationRail expanded onToggleExpanded={() => {}} activePath="/evidence" />,
    )
    const active = screen.getByRole('button', { name: /Evidence/i })
    expect(active.getAttribute('aria-current')).toBe('page')
  })

  it('does not mark non-active items', () => {
    render(
      <NavigationRail expanded onToggleExpanded={() => {}} activePath="/evidence" />,
    )
    const inactive = screen.getByRole('button', { name: /Overview/i })
    expect(inactive.getAttribute('aria-current')).toBeNull()
  })

  it('calls onNavigate with the item when clicked', () => {
    const handler = vi.fn<(item: NavigationItem) => void>()
    render(
      <NavigationRail expanded onToggleExpanded={() => {}} onNavigate={handler} />,
    )
    fireEvent.click(screen.getByRole('button', { name: /Overview/i }))
    expect(handler).toHaveBeenCalledTimes(1)
    const firstCall = handler.mock.calls[0]
    expect(firstCall).toBeDefined()
    const firstArg = firstCall?.[0]
    expect(firstArg).toMatchObject({ key: 'overview', to: '/' })
  })

  it('calls onToggleExpanded when the toggle button is clicked', () => {
    const toggle = vi.fn()
    render(<NavigationRail expanded={false} onToggleExpanded={toggle} />)
    fireEvent.click(screen.getByRole('button', { name: /Expand navigation|توسيع/i }))
    expect(toggle).toHaveBeenCalledTimes(1)
  })

  it('toggle button has aria-expanded reflecting state', () => {
    const { rerender } = render(
      <NavigationRail expanded={false} onToggleExpanded={() => {}} />,
    )
    expect(
      screen.getByRole('button', { name: /Expand navigation|توسيع/i }).getAttribute('aria-expanded'),
    ).toBe('false')
    rerender(<NavigationRail expanded onToggleExpanded={() => {}} />)
    expect(
      screen.getByRole('button', { name: /Collapse navigation|طي/i }).getAttribute('aria-expanded'),
    ).toBe('true')
  })

  it('renders Arabic labels when language is ar', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    render(<NavigationRail expanded onToggleExpanded={() => {}} />)
    expect(screen.getByText('نظرة عامة')).toBeTruthy()
    expect(screen.getByText('الثقة')).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without throwing', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    render(<NavigationRail expanded onToggleExpanded={() => {}} />)
    expect(screen.getByText('Overview')).toBeTruthy()
  })

  it('each item button has an aria-label', () => {
    render(<NavigationRail expanded onToggleExpanded={() => {}} />)
    const buttons = screen.getAllByRole('button').filter((b) =>
      b.classList.contains('eg-nav__item'),
    )
    for (const b of buttons) {
      expect(b.getAttribute('aria-label')).toBeTruthy()
    }
  })
})
