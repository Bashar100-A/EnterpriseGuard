import { describe, it, expect, afterEach, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useKeyboardShortcuts } from './useKeyboardShortcuts'

afterEach(() => {
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

/**
 * Dispatch a keydown event.
 *
 * If `target` is provided, the event originates from that element
 * (bubbles to window, so the hook's window-level listener catches it).
 * Otherwise the event originates from window directly.
 */
function pressKey(init: KeyboardEventInit, target: EventTarget = window): void {
  const e = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init })
  target.dispatchEvent(e)
}

describe('useKeyboardShortcuts', () => {
  it('fires a bare-key shortcut when not in an input', () => {
    const handler = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: '?',
          description: 'x',
          group: 'g',
          match: (e) => e.key === '?',
          handler,
        },
      ]),
    )
    pressKey({ key: '?' })
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('does NOT fire a bare-key shortcut when focus is in an <input>', () => {
    const handler = vi.fn()
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()

    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: '?',
          description: 'x',
          group: 'g',
          match: (e) => e.key === '?',
          handler,
        },
      ]),
    )
    pressKey({ key: '?' }, input)
    expect(handler).not.toHaveBeenCalled()
  })

  it('does NOT fire a bare-key shortcut when focus is in a <textarea>', () => {
    const handler = vi.fn()
    const ta = document.createElement('textarea')
    document.body.appendChild(ta)
    ta.focus()

    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: '?',
          description: 'x',
          group: 'g',
          match: (e) => e.key === '?',
          handler,
        },
      ]),
    )
    pressKey({ key: '?' }, ta)
    expect(handler).not.toHaveBeenCalled()
  })

  it('does NOT fire a bare-key shortcut when focus is in a <select>', () => {
    const handler = vi.fn()
    const sel = document.createElement('select')
    document.body.appendChild(sel)
    sel.focus()

    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: 'a',
          description: 'x',
          group: 'g',
          match: (e) => e.key === 'a',
          handler,
        },
      ]),
    )
    pressKey({ key: 'a' }, sel)
    expect(handler).not.toHaveBeenCalled()
  })

  it('fires a modifier shortcut even inside an input', () => {
    const handler = vi.fn()
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()

    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: 'Ctrl+B',
          description: 'x',
          group: 'g',
          match: (e) => (e.ctrlKey || e.metaKey) && e.key === 'b',
          handler,
        },
      ]),
    )
    pressKey({ key: 'b', ctrlKey: true }, input)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('fires a Ctrl shortcut even inside a textarea', () => {
    const handler = vi.fn()
    const ta = document.createElement('textarea')
    document.body.appendChild(ta)
    ta.focus()

    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: 'Ctrl+J',
          description: 'x',
          group: 'g',
          match: (e) => (e.ctrlKey || e.metaKey) && e.key === 'j',
          handler,
        },
      ]),
    )
    pressKey({ key: 'j', ctrlKey: true }, ta)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('ignores key repeats', () => {
    const handler = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: 'a',
          description: 'x',
          group: 'g',
          match: (e) => e.key === 'a',
          handler,
        },
      ]),
    )
    pressKey({ key: 'a', repeat: true })
    expect(handler).not.toHaveBeenCalled()
  })

  it('only fires the first matching shortcut', () => {
    const h1 = vi.fn()
    const h2 = vi.fn()
    renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'a',
          keys: '?',
          description: 'a',
          group: 'g',
          match: (e) => e.key === '?',
          handler: h1,
        },
        {
          id: 'b',
          keys: '?',
          description: 'b',
          group: 'g',
          match: (e) => e.key === '?',
          handler: h2,
        },
      ]),
    )
    pressKey({ key: '?' })
    expect(h1).toHaveBeenCalledTimes(1)
    expect(h2).not.toHaveBeenCalled()
  })

  it('removes the listener on unmount', () => {
    const handler = vi.fn()
    const { unmount } = renderHook(() =>
      useKeyboardShortcuts([
        {
          id: 'x',
          keys: 'z',
          description: 'x',
          group: 'g',
          match: (e) => e.key === 'z',
          handler,
        },
      ]),
    )
    unmount()
    pressKey({ key: 'z' })
    expect(handler).not.toHaveBeenCalled()
  })
})
