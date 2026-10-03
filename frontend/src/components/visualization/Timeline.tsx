import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from '../security/tone'

export interface TimelineEvent {
  id: string
  /** ISO 8601 timestamp, or null when unknown. */
  timestamp: string | null
  /** Primary event title. */
  title: ReactNode
  /** Optional secondary description. */
  description?: ReactNode
  /** Semantic tone — drives the node marker color. */
  tone: SemanticTone
  /** Optional extra content rendered below (e.g., an ID, a badge). */
  extra?: ReactNode
}

export interface TimelineProps {
  events: TimelineEvent[]
  /** Optional accessible name. Falls back to a translated default. */
  ariaLabel?: string
  /** Show the event count in the header. Default: true. */
  showCount?: boolean
}

/**
 * Format an ISO timestamp into a compact human string for display.
 *
 * Returns null when the input is null — the caller decides how to
 * render missing time. Formatting is delegated to `Intl.DateTimeFormat`
 * with the browser's locale; this is a display concern, not a data one.
 */
function formatTimestamp(iso: string | null): string | null {
  if (iso === null) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  const dt = new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
  return dt.format(d)
}

/**
 * Timeline — a vertical event stream.
 *
 * Renders a central spine with markers on the inline-start side.
 * RTL-aware: the spine is drawn using logical properties, so under
 * RTL it appears on the right side automatically.
 *
 * The component does NOT sort, filter, or paginate. Events are rendered
 * in the order given — the caller is responsible for ordering.
 *
 * When the event list is empty, an empty state is rendered instead.
 */
export function Timeline({
  events,
  ariaLabel,
  showCount = true,
}: TimelineProps): ReactElement {
  const { t } = useTranslation('visualization')

  if (events.length === 0) {
    return (
      <div className="eg-timeline eg-timeline--empty" data-testid="eg-timeline-empty">
        <p className="eg-timeline__empty">{t('timeline.empty')}</p>
      </div>
    )
  }

  return (
    <section
      className="eg-timeline"
      role="region"
      aria-label={ariaLabel ?? (t('timeline.label') as string)}
      data-testid="eg-timeline"
    >
      <header className="eg-timeline__header">
        <h3 className="eg-timeline__title">{t('timeline.label')}</h3>
        {showCount && (
          <span className="eg-timeline__count">
            {t('timeline.eventCount', { count: events.length })}
          </span>
        )}
      </header>

      <ol className="eg-timeline__list" role="list">
        {events.map((event) => {
          const formatted = formatTimestamp(event.timestamp)
          return (
            <li
              key={event.id}
              className="eg-timeline__event"
              data-tone={event.tone}
              data-testid={`eg-timeline-event-${event.id}`}
            >
              <span className="eg-timeline__marker" aria-hidden="true" />
              <div className="eg-timeline__body">
                <div className="eg-timeline__meta">
                  <time
                    className="eg-timeline__time eg-mono"
                    dateTime={event.timestamp ?? undefined}
                    data-unknown={formatted === null ? 'true' : undefined}
                  >
                    {formatted ?? (t('timeline.unknownTime') as string)}
                  </time>
                </div>
                <div className="eg-timeline__title-text">{event.title}</div>
                {event.description !== undefined && (
                  <div className="eg-timeline__description">{event.description}</div>
                )}
                {event.extra !== undefined && (
                  <div className="eg-timeline__extra">{event.extra}</div>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
