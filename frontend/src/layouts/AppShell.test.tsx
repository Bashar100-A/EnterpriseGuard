import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import '../i18n'
import { AppShell } from './AppShell'

afterEach(() => {
  cleanup()
  document.documentElement.dir = 'ltr'
  document.documentElement.lang = 'en'
})

describe('AppShell', () => {
  it('renders children inside the main workspace', () => {
    render(
      <AppShell>
        <div>hello-workspace</div>
      </AppShell>,
    )
    expect(screen.getByText('hello-workspace')).toBeTruthy()
  })

  it('has a semantic <main id="eg-main">', () => {
    const { container } = render(
      <AppShell>
        <div />
      </AppShell>,
    )
    const main = container.querySelector('main#eg-main')
    expect(main).not.toBeNull()
    expect(main?.getAttribute('tabindex')).toBe('-1')
  })

  it('renders a skip link pointing at #eg-main', () => {
    render(
      <AppShell>
        <div />
      </AppShell>,
    )
    const link = screen.getByRole('link')
    expect(link.getAttribute('href')).toBe('#eg-main')
  })

  it('does NOT render topbar when prop is absent', () => {
    const { container } = render(
      <AppShell>
        <div />
      </AppShell>,
    )
    expect(container.querySelector('header[role="banner"]')).toBeNull()
  })

  it('renders topbar slot when provided', () => {
    render(
      <AppShell topbar={<div>my-topbar</div>}>
        <div />
      </AppShell>,
    )
    expect(screen.getByText('my-topbar')).toBeTruthy()
  })

  it('does NOT render navigation rail when prop is absent', () => {
    const { container } = render(
      <AppShell>
        <div />
      </AppShell>,
    )
    expect(container.querySelector('aside.eg-shell__nav')).toBeNull()
  })

  it('renders navigation rail slot when provided', () => {
    render(
      <AppShell navigationRail={<div>my-nav</div>}>
        <div />
      </AppShell>,
    )
    expect(screen.getByText('my-nav')).toBeTruthy()
  })

  it('does NOT render assurance rail by default (assuranceOpen=false)', () => {
    render(
      <AppShell assuranceRail={<div>my-assurance</div>}>
        <div />
      </AppShell>,
    )
    expect(screen.queryByText('my-assurance')).toBeNull()
  })

  it('renders assurance rail when assuranceOpen is true', () => {
    render(
      <AppShell assuranceRail={<div>my-assurance</div>} assuranceOpen>
        <div />
      </AppShell>,
    )
    expect(screen.getByText('my-assurance')).toBeTruthy()
  })

  it('does not render assurance rail when open=true but rail prop is absent', () => {
    const { container } = render(
      <AppShell assuranceOpen>
        <div />
      </AppShell>,
    )
    expect(container.querySelector('aside.eg-shell__assurance')).toBeNull()
  })

  it('renders in RTL without throwing', () => {
    document.documentElement.dir = 'rtl'
    document.documentElement.lang = 'ar'
    render(
      <AppShell navigationRail={<div>nav</div>}>
        <div>content</div>
      </AppShell>,
    )
    expect(screen.getByText('content')).toBeTruthy()
  })

  it('applies eg-shell root class', () => {
    const { container } = render(
      <AppShell>
        <div />
      </AppShell>,
    )
    expect(container.querySelector('.eg-shell')).not.toBeNull()
  })
})
