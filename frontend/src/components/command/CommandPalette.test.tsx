import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent, waitFor } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { CommandPalette } from './CommandPalette'
import type { Command } from './CommandPalette'

interface CommandCalls {
  a: number
  b: number
  c: number
  d: number
}

function makeCommands(): { commands: Command[]; calls: CommandCalls } {
  const calls: CommandCalls = { a: 0, b: 0, c: 0, d: 0 }
  const commands: Command[] = [
    { id: 'a', label: 'Alpha', group: 'navigate', onRun: () => { calls.a += 1 } },
    { id: 'b', label: 'Beta', group: 'navigate', onRun: () => { calls.b += 1 } },
    { id: 'c', label: 'Gamma', group: 'system', onRun: () => { calls.c += 1 } },
    { id: 'd', label: 'Delta', group: 'system', disabled: true, onRun: () => { calls.d += 1 } },
  ]
  return { commands, calls }
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('CommandPalette', () => {
  it('renders nothing when open=false', () => {
    const { commands } = makeCommands()
    const { container } = renderWithThemeOnly(
      <CommandPalette open={false} onClose={() => {}} commands={commands} />,
    )
    expect(container.querySelector('.eg-cmd')).toBeNull()
  })

  it('renders the dialog when open=true', () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    expect(screen.getByRole('dialog')).toBeTruthy()
  })

  it('has aria-modal=true', () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    expect(screen.getByRole('dialog').getAttribute('aria-modal')).toBe('true')
  })

  it('renders all command labels', () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    expect(screen.getByText('Alpha')).toBeTruthy()
    expect(screen.getByText('Beta')).toBeTruthy()
    expect(screen.getByText('Gamma')).toBeTruthy()
    expect(screen.getByText('Delta')).toBeTruthy()
  })

  it('renders group headers', () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    expect(screen.getAllByText('Navigate').length).toBeGreaterThan(0)
    expect(screen.getAllByText('System').length).toBeGreaterThan(0)
  })

  it('has a search input with placeholder', () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    expect(input).toBeTruthy()
  })

  it('filters commands by query', () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: 'alp' } })
    expect(screen.getByText('Alpha')).toBeTruthy()
    expect(screen.queryByText('Beta')).toBeNull()
    expect(screen.queryByText('Gamma')).toBeNull()
  })

  it('shows no-results message when nothing matches', () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: 'zzzzz' } })
    expect(screen.getByText(/No commands match your search/i)).toBeTruthy()
  })

  it('clicking a command runs it and calls onClose', () => {
    const { commands, calls } = makeCommands()
    const onClose = vi.fn()
    renderWithThemeOnly(
      <CommandPalette open onClose={onClose} commands={commands} />,
    )
    fireEvent.click(screen.getByText('Beta'))
    expect(calls.b).toBe(1)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does NOT run a disabled command on click', () => {
    const { commands, calls } = makeCommands()
    const onClose = vi.fn()
    renderWithThemeOnly(
      <CommandPalette open onClose={onClose} commands={commands} />,
    )
    fireEvent.click(screen.getByText('Delta'))
    expect(calls.d).toBe(0)
    expect(onClose).not.toHaveBeenCalled()
  })

  it('pressing Escape calls onClose', () => {
    const { commands } = makeCommands()
    const onClose = vi.fn()
    renderWithThemeOnly(
      <CommandPalette open onClose={onClose} commands={commands} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.keyDown(input, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('pressing Enter runs the first (active) command', () => {
    const { commands, calls } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(calls.a).toBe(1)
  })

  it('ArrowDown moves the active index', () => {
    const { commands, calls } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.keyDown(input, { key: 'ArrowDown' })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(calls.b).toBe(1)
  })

  it('ArrowUp wraps to the last enabled command', () => {
    const { commands, calls } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    // From index 0, ArrowUp should wrap to last ENABLED (index 2, since 3 is disabled)
    fireEvent.keyDown(input, { key: 'ArrowUp' })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(calls.c).toBe(1)
  })

  it('clicking the backdrop calls onClose', () => {
    const { commands } = makeCommands()
    const onClose = vi.fn()
    const { container } = renderWithThemeOnly(
      <CommandPalette open onClose={onClose} commands={commands} />,
    )
    const overlay = container.querySelector('.eg-cmd-overlay') as HTMLElement | null
    expect(overlay).not.toBeNull()
    fireEvent.click(overlay as HTMLElement)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('clicking inside the dialog does not close', () => {
    const { commands } = makeCommands()
    const onClose = vi.fn()
    renderWithThemeOnly(
      <CommandPalette open onClose={onClose} commands={commands} />,
    )
    fireEvent.click(screen.getByRole('dialog'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('clicking the X button calls onClose', () => {
    const { commands } = makeCommands()
    const onClose = vi.fn()
    renderWithThemeOnly(
      <CommandPalette open onClose={onClose} commands={commands} />,
    )
    fireEvent.click(screen.getByRole('button', { name: /Close/i }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('autofocuses the input', async () => {
    const { commands } = makeCommands()
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type a command or search/i)
      expect(document.activeElement).toBe(input)
    })
  })

  it('renders in Arabic', async () => {
    const { commands } = makeCommands()
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={commands} />,
    )
    expect(screen.getByPlaceholderText(/اكتب أمرًا/)).toBeTruthy()
    await changeLanguage('en')
  })
})
