import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { Drawer } from './Drawer'

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('Drawer', () => {
  it('renders nothing when open=false', () => {
    const { container } = renderWithThemeOnly(
      <Drawer open={false} onClose={() => {}} title="Details">
        <div>content</div>
      </Drawer>,
    )
    expect(container.querySelector('[data-testid="eg-drawer"]')).toBeNull()
  })

  it('renders a dialog with role=dialog and aria-modal=true', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="Evidence details">
        <div>content</div>
      </Drawer>,
    )
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeTruthy()
    expect(dialog.getAttribute('aria-modal')).toBe('true')
  })

  it('uses the title as aria-label when it is a string', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="Evidence details">
        <div>content</div>
      </Drawer>,
    )
    expect(screen.getByRole('dialog').getAttribute('aria-label')).toBe('Evidence details')
  })

  it('renders the title as an h2', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="Evidence details">
        <div>content</div>
      </Drawer>,
    )
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBe('Evidence details')
  })

  it('renders children inside the body', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x">
        <div>the-content</div>
      </Drawer>,
    )
    expect(screen.getByText('the-content')).toBeTruthy()
  })

  it('renders the footer when provided', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x" footer={<button type="button">Save</button>}>
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByRole('button', { name: 'Save' })).toBeTruthy()
  })

  it('does NOT render a footer when absent', () => {
    const { container } = renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x">
        <div>c</div>
      </Drawer>,
    )
    expect(container.querySelector('.eg-drawer__footer')).toBeNull()
  })

  it('side defaults to end', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x">
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByTestId('eg-drawer').getAttribute('data-side')).toBe('end')
  })

  it('side=start sets data-side=start', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x" side="start">
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByTestId('eg-drawer').getAttribute('data-side')).toBe('start')
  })

  it('size defaults to md', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x">
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByTestId('eg-drawer').getAttribute('data-size')).toBe('md')
  })

  it('size=lg sets data-size=lg', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x" size="lg">
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByTestId('eg-drawer').getAttribute('data-size')).toBe('lg')
  })

  it('Escape key calls onClose', () => {
    const onClose = vi.fn()
    renderWithThemeOnly(
      <Drawer open onClose={onClose} title="x">
        <div>c</div>
      </Drawer>,
    )
    fireEvent.keyDown(screen.getByTestId('eg-drawer'), { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('X button calls onClose', () => {
    const onClose = vi.fn()
    renderWithThemeOnly(
      <Drawer open onClose={onClose} title="x">
        <div>c</div>
      </Drawer>,
    )
    fireEvent.click(screen.getByTestId('eg-drawer-close'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('clicking the backdrop calls onClose', () => {
    const onClose = vi.fn()
    renderWithThemeOnly(
      <Drawer open onClose={onClose} title="x">
        <div>c</div>
      </Drawer>,
    )
    fireEvent.click(screen.getByTestId('eg-drawer-overlay'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('clicking inside the panel does NOT call onClose', () => {
    const onClose = vi.fn()
    renderWithThemeOnly(
      <Drawer open onClose={onClose} title="x">
        <div>inner</div>
      </Drawer>,
    )
    fireEvent.click(screen.getByText('inner'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('accepts an ariaLabel override', () => {
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="x" ariaLabel="Custom panel">
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByRole('dialog').getAttribute('aria-label')).toBe('Custom panel')
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title="عربي">
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByRole('dialog')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })

  it('renders in Arabic (default aria-label when title is not a string)', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(
      <Drawer open onClose={() => {}} title={<span>عربي</span>}>
        <div>c</div>
      </Drawer>,
    )
    expect(screen.getByRole('dialog').getAttribute('aria-label')).toBe('لوحة التفاصيل')
    await changeLanguage('en')
  })
})
