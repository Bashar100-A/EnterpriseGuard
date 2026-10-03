import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { CommandPalette } from './CommandPalette'
import type { Command } from './CommandPalette'

function makeCommands(): Command[] {
  return [
    {
      id: 'nav-evidence',
      label: 'Go to Evidence',
      group: 'navigate',
      keywords: ['/evidence', 'evidence', 'Verified and unverified items within the current scope'],
      onRun: () => {},
    },
    {
      id: 'nav-decisions',
      label: 'Go to Decision Intelligence',
      group: 'navigate',
      keywords: ['/decisions', 'decisions', 'The full chain from observation to execution'],
      onRun: () => {},
    },
    {
      id: 'nav-sibb',
      label: 'Go to SIBB Trust Core',
      group: 'navigate',
      keywords: ['/sibb', 'sibb', 'The integrity foundation — baseline, chain, signatures'],
      onRun: () => {},
    },
  ]
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('CommandPalette — fuzzy search', () => {
  it('matches a query with a typo (evidance → Evidence)', () => {
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={makeCommands()} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: 'evidance' } })
    expect(screen.getByText('Go to Evidence')).toBeTruthy()
  })

  it('matches a substring of a keyword (integrity → SIBB)', () => {
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={makeCommands()} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: 'integrity' } })
    expect(screen.getByText('Go to SIBB Trust Core')).toBeTruthy()
  })

  it('matches a content-level query (observation → Decisions)', () => {
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={makeCommands()} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: 'observation execution' } })
    expect(screen.getByText('Go to Decision Intelligence')).toBeTruthy()
  })

  it('matches on the route path (/sibb)', () => {
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={makeCommands()} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: '/sibb' } })
    expect(screen.getByText('Go to SIBB Trust Core')).toBeTruthy()
  })

  it('hides non-matching commands', () => {
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={makeCommands()} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: 'integrity' } })
    expect(screen.queryByText('Go to Evidence')).toBeNull()
  })

  it('returns all commands for empty query', () => {
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={makeCommands()} />,
    )
    expect(screen.getByText('Go to Evidence')).toBeTruthy()
    expect(screen.getByText('Go to Decision Intelligence')).toBeTruthy()
    expect(screen.getByText('Go to SIBB Trust Core')).toBeTruthy()
  })

  it('shows no-results for a truly non-matching query', () => {
    renderWithThemeOnly(
      <CommandPalette open onClose={() => {}} commands={makeCommands()} />,
    )
    const input = screen.getByPlaceholderText(/Type a command or search/i)
    fireEvent.change(input, { target: { value: 'zzqqxxww' } })
    expect(screen.getByText(/No commands match/i)).toBeTruthy()
  })
})
