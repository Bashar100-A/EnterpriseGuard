import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { Timeline } from './Timeline'
import type { TimelineEvent } from './Timeline'

function makeEvents(): TimelineEvent[] {
  return [
    {
      id: 'e1',
      timestamp: '2026-10-03T10:00:00Z',
      title: 'Policy created',
      description: 'POL-042 approved',
      tone: 'trust',
    },
    {
      id: 'e2',
      timestamp: '2026-10-03T10:05:00Z',
      title: 'Evidence linked',
      tone: 'info',
    },
    {
      id: 'e3',
      timestamp: null,
      title: 'Manual review required',
      tone: 'warning',
    },
  ]
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('Timeline', () => {
  it('renders an empty placeholder when events=[]', () => {
    renderWithThemeOnly(<Timeline events={[]} />)
    expect(screen.getByTestId('eg-timeline-empty')).toBeTruthy()
    expect(screen.queryByTestId('eg-timeline')).toBeNull()
  })

  it('empty placeholder shows the translated message', () => {
    renderWithThemeOnly(<Timeline events={[]} />)
    expect(screen.getByText(/No events to display/i)).toBeTruthy()
  })

  it('renders a region with an aria-label', () => {
    renderWithThemeOnly(<Timeline events={makeEvents()} />)
    const region = screen.getByRole('region', { name: 'Timeline' })
    expect(region).toBeTruthy()
  })

  it('accepts a custom aria-label', () => {
    renderWithThemeOnly(<Timeline events={makeEvents()} ariaLabel="Audit trail" />)
    expect(screen.getByRole('region', { name: 'Audit trail' })).toBeTruthy()
  })

  it('renders one <li> per event', () => {
    const { container } = renderWithThemeOnly(<Timeline events={makeEvents()} />)
    expect(container.querySelectorAll('.eg-timeline__event')).toHaveLength(3)
  })

  it('renders all event titles', () => {
    renderWithThemeOnly(<Timeline events={makeEvents()} />)
    expect(screen.getByText('Policy created')).toBeTruthy()
    expect(screen.getByText('Evidence linked')).toBeTruthy()
    expect(screen.getByText('Manual review required')).toBeTruthy()
  })

  it('renders description when provided', () => {
    renderWithThemeOnly(<Timeline events={makeEvents()} />)
    expect(screen.getByText('POL-042 approved')).toBeTruthy()
  })

  it('sets data-tone per event', () => {
    const { container } = renderWithThemeOnly(<Timeline events={makeEvents()} />)
    expect(container.querySelector('[data-tone="trust"]')).not.toBeNull()
    expect(container.querySelector('[data-tone="info"]')).not.toBeNull()
    expect(container.querySelector('[data-tone="warning"]')).not.toBeNull()
  })

  it('renders formatted time for known timestamps', () => {
    const { container } = renderWithThemeOnly(<Timeline events={makeEvents()} />)
    const times = container.querySelectorAll('.eg-timeline__time')
    expect(times.length).toBe(3)
    // First two have timestamps — no "unknown" marker
    expect(times[0]?.getAttribute('data-unknown')).toBeNull()
    expect(times[1]?.getAttribute('data-unknown')).toBeNull()
  })

  it('renders "Time unknown" for null timestamps', () => {
    renderWithThemeOnly(<Timeline events={makeEvents()} />)
    expect(screen.getByText('Time unknown')).toBeTruthy()
  })

  it('sets data-unknown=true on null timestamp', () => {
    const { container } = renderWithThemeOnly(<Timeline events={makeEvents()} />)
    const unknown = container.querySelector('.eg-timeline__time[data-unknown="true"]')
    expect(unknown).not.toBeNull()
  })

  it('renders a <time> element with dateTime attribute', () => {
    const { container } = renderWithThemeOnly(<Timeline events={makeEvents()} />)
    const time = container.querySelector('time[datetime]')
    expect(time?.getAttribute('datetime')).toBe('2026-10-03T10:00:00Z')
  })

  it('shows the event count in the header by default', () => {
    renderWithThemeOnly(<Timeline events={makeEvents()} />)
    expect(screen.getByText(/3 events/i)).toBeTruthy()
  })

  it('hides the count when showCount=false', () => {
    const { container } = renderWithThemeOnly(
      <Timeline events={makeEvents()} showCount={false} />,
    )
    expect(container.querySelector('.eg-timeline__count')).toBeNull()
  })

  it('renders extra content when provided', () => {
    const events: TimelineEvent[] = [
      {
        id: 'x',
        timestamp: '2026-10-03T10:00:00Z',
        title: 'Event',
        tone: 'info',
        extra: <span data-testid="my-extra">extra</span>,
      },
    ]
    renderWithThemeOnly(<Timeline events={events} />)
    expect(screen.getByTestId('my-extra')).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<Timeline events={[]} />)
    expect(screen.getByText(/لا توجد أحداث للعرض/)).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without error', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(<Timeline events={makeEvents()} />)
    expect(screen.getByRole('region', { name: /Timeline|الخط الزمني/ })).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })

  it('does NOT reorder the given events', () => {
    const { container } = renderWithThemeOnly(<Timeline events={makeEvents()} />)
    const titles = Array.from(container.querySelectorAll('.eg-timeline__title-text'))
    expect(titles.map((t) => t.textContent)).toEqual([
      'Policy created',
      'Evidence linked',
      'Manual review required',
    ])
  })
})
