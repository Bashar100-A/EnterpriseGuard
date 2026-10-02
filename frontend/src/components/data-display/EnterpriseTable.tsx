import type { ReactElement, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { StateIndicator } from '../security/StateIndicator'
import type { SemanticTone } from '../security/tone'
import type { DataStateValue } from '../states/DataState'

export type ColumnAlign = 'start' | 'center' | 'end'

export type SortDirection = 'asc' | 'desc'

export interface EnterpriseColumn<Row> {
  /** Stable unique key for the column. */
  key: string
  /** Localized header label. */
  header: string
  /** Cell renderer. Falls back to String(row[key]) if absent. */
  render?: ((row: Row) => ReactNode) | undefined
  /** Text alignment. Default: 'start'. */
  align?: ColumnAlign
  /** CSS width, e.g. '120px' or '20%'. */
  width?: string
  /** Mark column as sortable (visual only in UI-01). */
  sortable?: boolean
}

export interface EnterpriseTableProps<Row> {
  columns: EnterpriseColumn<Row>[]
  rows: Row[]
  /** Stable unique key per row. */
  getRowKey: (row: Row) => string
  /** Data state — drives what is rendered. Default: 'loaded'. */
  state?: DataStateValue
  /** Optional caption above the table. */
  caption?: string
  /** Column currently sorted (visual only). */
  sortedBy?: string | undefined
  /** Sort direction (visual only). */
  sortDirection?: SortDirection | undefined
  /** Called when a sortable header is clicked. Visual only. */
  onSort?: ((key: string) => void) | undefined
  /** Called when Retry is clicked in error state. */
  onRetry?: (() => void) | undefined
  /** Custom empty-state message. */
  emptyMessage?: string
  /** Label per row for accessibility. */
  rowAriaLabel?: (row: Row, index: number) => string
}

const TONE_BY_STATE: Record<DataStateValue, SemanticTone> = {
  loading: 'info',
  loaded: 'trust',
  empty: 'unknown',
  partial: 'warning',
  stale: 'warning',
  unknown: 'unknown',
  error: 'critical',
  unavailable: 'unknown',
  permissionDenied: 'unknown',
}

function alignClass(align: ColumnAlign | undefined): string {
  switch (align) {
    case 'center':
      return 'eg-table__cell--center'
    case 'end':
      return 'eg-table__cell--end'
    default:
      return 'eg-table__cell--start'
  }
}

function Placeholder({
  title,
  hint,
  tone,
  onRetry,
  retryLabel,
}: {
  title: string
  hint: string
  tone: SemanticTone
  onRetry?: (() => void) | undefined
  retryLabel: string
}): ReactElement {
  return (
    <div className="eg-table__placeholder" data-tone={tone} role="status">
      <div className="eg-table__placeholder-title">{title}</div>
      {hint !== '' && <div className="eg-table__placeholder-hint">{hint}</div>}
      {onRetry !== undefined && (
        <button type="button" className="eg-table__retry" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  )
}

/**
 * EnterpriseTable — table primitive with explicit states.
 *
 * Spec §37. Does NOT sort, filter, or paginate. Those will be added by
 * feature code in later phases; this primitive provides the container,
 * the state handling, and the accessibility contract.
 *
 * Rows render ONLY when state is 'loaded' or 'partial'.
 * No hidden behavior. No server-side fetch. No fake data.
 */
export function EnterpriseTable<Row>({
  columns,
  rows,
  getRowKey,
  state = 'loaded',
  caption,
  sortedBy,
  sortDirection,
  onSort,
  onRetry,
  emptyMessage,
  rowAriaLabel,
}: EnterpriseTableProps<Row>): ReactElement {
  const { t } = useTranslation('dataDisplay')
  const tone = TONE_BY_STATE[state]
  const showRows = (state === 'loaded' || state === 'partial') && rows.length > 0
  const showEmpty = state === 'empty' || (state === 'loaded' && rows.length === 0)
  const showPartialBanner = state === 'partial' && rows.length > 0

  const stateLabel = t(`table.state.${state}`, { defaultValue: state }) as string
  const retryLabel = t('table.retry') as string

  if (columns.length === 0) {
    return (
      <div className="eg-table" role="region" aria-label={caption ?? t('table.row')}>
        <Placeholder
          title={t('table.noColumns') as string}
          hint=""
          tone="warning"
          retryLabel={retryLabel}
        />
      </div>
    )
  }

  const placeholderTitle = showEmpty
    ? (emptyMessage ?? (t('table.empty') as string))
    : (t(`table.${state}`) as string)
  const placeholderHint = showEmpty
    ? (t('table.emptyHint') as string)
    : (t(`table.${state}Hint`, { defaultValue: '' }) as string)

  return (
    <div className="eg-table" role="region" aria-label={caption ?? t('table.row')}>
      {caption !== undefined && <div className="eg-table__caption">{caption}</div>}

      {showPartialBanner && (
        <div className="eg-table__banner" role="note">
          <span className="eg-table__banner-title">{t('table.partial')}</span>
          <span className="eg-table__banner-hint">{t('table.partialHint')}</span>
        </div>
      )}

      {showRows ? (
        <div className="eg-table__scroll">
          <table className="eg-table__table">
            <thead>
              <tr>
                {columns.map((col) => {
                  const isSorted = sortedBy === col.key
                  const ariaSort = isSorted
                    ? sortDirection === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : col.sortable
                      ? 'none'
                      : undefined
                  const title = isSorted
                    ? sortDirection === 'asc'
                      ? (t('table.sortedAsc') as string)
                      : (t('table.sortedDesc') as string)
                    : col.sortable
                      ? (t('table.sortAsc') as string)
                      : undefined

                  return (
                    <th
                      key={col.key}
                      scope="col"
                      className={`eg-table__cell ${alignClass(col.align)}`}
                      style={col.width !== undefined ? { width: col.width } : undefined}
                      aria-sort={ariaSort}
                      data-sortable={col.sortable === true ? 'true' : undefined}
                    >
                      {col.sortable === true && onSort !== undefined ? (
                        <button
                          type="button"
                          className="eg-table__sort"
                          onClick={() => onSort(col.key)}
                          title={title}
                        >
                          <span>{col.header}</span>
                          <span className="eg-table__sort-arrow" aria-hidden="true">
                            {isSorted ? (sortDirection === 'asc' ? '↑' : '↓') : '↕'}
                          </span>
                        </button>
                      ) : (
                        <span>{col.header}</span>
                      )}
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const key = getRowKey(row)
                const ariaLabel = rowAriaLabel?.(row, i)
                return (
                  <tr
                    key={key}
                    className="eg-table__row"
                    aria-label={ariaLabel}
                  >
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        className={`eg-table__cell ${alignClass(col.align)}`}
                      >
                        {col.render !== undefined
                          ? col.render(row)
                          : String((row as Record<string, unknown>)[col.key] ?? '')}
                      </td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <Placeholder
          title={placeholderTitle}
          hint={placeholderHint}
          tone={tone}
          onRetry={state === 'error' ? onRetry : undefined}
          retryLabel={retryLabel}
        />
      )}

      <footer className="eg-table__footer">
        <StateIndicator tone={tone} label={stateLabel} size="sm" />
        {showRows && (
          <span className="eg-table__count">
            {t('table.selected', { count: rows.length, defaultValue: `${rows.length}` })}
          </span>
        )}
      </footer>
    </div>
  )
}
