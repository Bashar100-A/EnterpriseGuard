import { describe, it, expect, afterEach } from 'vitest'
import { render, cleanup, fireEvent, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { useFocusTrap, getFocusableElements } from './useFocusTrap'

afterEach(() => {
  cleanup()
})

function Trap(): ReactElement {
  const { handleTabKey } = useFocusTrap({ active: true })
  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="dialog"
      onKeyDown={handleTabKey}
    >
      <button data-testid="first">A</button>
      <button data-testid="middle">B</button>
      <button data-testid="last">C</button>
    </div>
  )
}

function makeOutsideButton(): HTMLButtonElement {
  const btn = document.createElement('button')
  btn.type = 'button'
  btn.textContent = 'outside'
  btn.setAttribute('data-testid', 'outside')
  document.body.appendChild(btn)
  return btn
}

describe('useFocusTrap — getFocusableElements', () => {
  it('returns empty array for container with no focusables', () => {
    const div = document.createElement('div')
    div.innerHTML = '<span>text</span>'
    document.body.appendChild(div)
    expect(getFocusableElements(div)).toEqual([])
  })

  it('returns buttons in DOM order', () => {
    const div = document.createElement('div')
    div.innerHTML = '<button>1</button><a href="#">2</a><button>3</button>'
    document.body.appendChild(div)
    const els = getFocusableElements(div)
    expect(els.length).toBe(3)
    expect(els[0]!.textContent).toBe('1')
    expect(els[2]!.textContent).toBe('3')
  })

  it('skips disabled buttons', () => {
    const div = document.createElement('div')
    div.innerHTML = '<button>1</button><button disabled>2</button><button>3</button>'
    document.body.appendChild(div)
    expect(getFocusableElements(div).length).toBe(2)
  })

  it('skips tabindex=-1 elements', () => {
    const div = document.createElement('div')
    div.innerHTML = '<button>1</button><div tabindex="-1">x</div><button>3</button>'
    document.body.appendChild(div)
    expect(getFocusableElements(div).length).toBe(2)
  })

  it('skips hidden elements', () => {
    const div = document.createElement('div')
    div.innerHTML = '<button>1</button><button hidden>2</button><button>3</button>'
    document.body.appendChild(div)
    expect(getFocusableElements(div).length).toBe(2)
  })

  it('skips aria-hidden=true elements', () => {
    const div = document.createElement('div')
    div.innerHTML = '<button>1</button><button aria-hidden="true">2</button><button>3</button>'
    document.body.appendChild(div)
    expect(getFocusableElements(div).length).toBe(2)
  })
})

describe('useFocusTrap — focus restoration', () => {
  it('restores focus to the trigger on unmount', () => {
    const trigger = makeOutsideButton()
    trigger.focus()
    expect(document.activeElement).toBe(trigger)

    const { unmount } = render(<Trap />)
    unmount()
    expect(document.activeElement).toBe(trigger)

    trigger.remove()
  })
})

describe('useFocusTrap — Tab trapping', () => {
  it('Tab from last wraps to first', () => {
    render(<Trap />)
    const last = screen.getByTestId('last')
    last.focus()
    fireEvent.keyDown(screen.getByTestId('dialog'), { key: 'Tab' })
    expect(document.activeElement).toBe(screen.getByTestId('first'))
  })

  it('Shift+Tab from first wraps to last', () => {
    render(<Trap />)
    const first = screen.getByTestId('first')
    first.focus()
    fireEvent.keyDown(screen.getByTestId('dialog'), {
      key: 'Tab',
      shiftKey: true,
    })
    expect(document.activeElement).toBe(screen.getByTestId('last'))
  })

  it('Tab from middle does not wrap (browser handles native movement)', () => {
    render(<Trap />)
    const middle = screen.getByTestId('middle')
    middle.focus()
    fireEvent.keyDown(screen.getByTestId('dialog'), { key: 'Tab' })
    // Handler does not preventDefault when focus is in the middle.
    // jsdom does not move focus natively, so activeElement stays.
    expect(document.activeElement).toBe(middle)
  })

  it('Tab from outside wraps to first', () => {
    render(<Trap />)
    const outside = makeOutsideButton()
    outside.focus()
    expect(document.activeElement).toBe(outside)
    fireEvent.keyDown(screen.getByTestId('dialog'), { key: 'Tab' })
    expect(document.activeElement).toBe(screen.getByTestId('first'))
    outside.remove()
  })

  it('Shift+Tab from outside wraps to last', () => {
    render(<Trap />)
    const outside = makeOutsideButton()
    outside.focus()
    fireEvent.keyDown(screen.getByTestId('dialog'), {
      key: 'Tab',
      shiftKey: true,
    })
    expect(document.activeElement).toBe(screen.getByTestId('last'))
    outside.remove()
  })

  it('non-Tab key does nothing', () => {
    render(<Trap />)
    const first = screen.getByTestId('first')
    first.focus()
    fireEvent.keyDown(screen.getByTestId('dialog'), { key: 'a' })
    expect(document.activeElement).toBe(first)
  })
})
