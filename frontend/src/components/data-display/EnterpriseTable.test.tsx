import { describe, it, expect, afterEach, vi } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { EnterpriseTable } from './EnterpriseTable'
import type { EnterpriseColumn } from './EnterpriseTable'
import type { DataStateValue } from '../states/DataState'

interface Row {
  id: string
  name: string
  count: number
}

const ROWS: Row[] = [
  { id: 'r-1', name: 'Alpha', count: 3 },
  { id: 'r-2', name: 'Beta', count: 5 },
  { id: 'r-3', name: 'Gamma', count: 8 },
]

const COLS: EnterpriseColumn<Row>[] = [
  { key: 'id', header: 'ID' },
  { key: 'name', header: 'Name' },
  { key: 'count', header: 'Count', align: 'end' },
]

afterEach(() => {
  cleanup()
  window.localStorage.clear()
  vi.restoreAllMocks()
})

describe('EnterpriseTable', () => {
  it('renders all column headers when state=loaded', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(screen.getByText('ID')).toBeTruthy()
    expect(screen.getByText('Name')).toBeTruthy()
    expect(screen.getByText('Count')).toBeTruthy()
  })

  it('renders a row per item', () => {
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(container.querySelectorAll('tbody tr')).toHaveLength(3)
  })

  it('renders cell values from row properties', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(screen.getByText('Alpha')).toBeTruthy()
    expect(screen.getByText('Beta')).toBeTruthy()
    expect(screen.getByText('Gamma')).toBeTruthy()
  })

  it('uses a custom render function when provided', () => {
    const cols: EnterpriseColumn<Row>[] = [
      { key: 'name', header: 'Name', render: (r) => <em>custom-{r.name}</em> },
    ]
    renderWithThemeOnly(
      <EnterpriseTable
        columns={cols}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(screen.getByText('custom-Alpha')).toBeTruthy()
  })

  it('applies align end class to header and cells', () => {
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    const endCells = container.querySelectorAll('.eg-table__cell--end')
    // 1 header + 3 cells = 4
    expect(endCells.length).toBeGreaterThanOrEqual(4)
  })

  it('does NOT render rows when state=loading', () => {
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loading"
      />,
    )
    expect(container.querySelectorAll('tbody tr')).toHaveLength(0)
    expect(screen.getByText(/Loading rows/i)).toBeTruthy()
  })

  it('shows empty placeholder when rows=[] and state=loaded', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={[]}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(screen.getByText(/No rows to display/i)).toBeTruthy()
  })

  it('shows explicit empty placeholder when state=empty', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="empty"
      />,
    )
    expect(screen.getByText(/No rows to display/i)).toBeTruthy()
  })

  it('accepts a custom emptyMessage', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={[]}
        getRowKey={(r) => r.id}
        state="loaded"
        emptyMessage="Nothing here yet"
      />,
    )
    expect(screen.getByText('Nothing here yet')).toBeTruthy()
  })

  it('renders partial banner AND rows in partial state', () => {
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="partial"
      />,
    )
    expect(container.querySelector('.eg-table__banner')).not.toBeNull()
    expect(container.querySelectorAll('tbody tr')).toHaveLength(3)
  })

  it('does NOT render partial banner in loaded state', () => {
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(container.querySelector('.eg-table__banner')).toBeNull()
  })

  it('shows retry button in error state and calls handler', () => {
    const handler = vi.fn()
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="error"
        onRetry={handler}
      />,
    )
    const btn = screen.getByRole('button', { name: /Retry/i })
    fireEvent.click(btn)
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('does NOT show retry in non-error states', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="empty"
        onRetry={() => {}}
      />,
    )
    expect(screen.queryByRole('button', { name: /Retry/i })).toBeNull()
  })

  it('renders caption when provided', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
        caption="Recent Decisions"
      />,
    )
    expect(screen.getByText('Recent Decisions')).toBeTruthy()
  })

  it('applies aria-sort=none to sortable unsorted column', () => {
    const cols: EnterpriseColumn<Row>[] = [
      { key: 'id', header: 'ID', sortable: true },
      { key: 'name', header: 'Name' },
    ]
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={cols}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
        onSort={() => {}}
      />,
    )
    const sortable = container.querySelector('[data-sortable="true"]')
    expect(sortable?.getAttribute('aria-sort')).toBe('none')
  })

  it('applies aria-sort=ascending when sorted asc', () => {
    const cols: EnterpriseColumn<Row>[] = [
      { key: 'id', header: 'ID', sortable: true },
    ]
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={cols}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
        sortedBy="id"
        sortDirection="asc"
        onSort={() => {}}
      />,
    )
    const th = container.querySelector('th[aria-sort="ascending"]')
    expect(th).not.toBeNull()
  })

  it('calls onSort with the column key when sort button clicked', () => {
    const handler = vi.fn()
    const cols: EnterpriseColumn<Row>[] = [
      { key: 'name', header: 'Name', sortable: true },
    ]
    renderWithThemeOnly(
      <EnterpriseTable
        columns={cols}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
        onSort={handler}
      />,
    )
    const btn = screen.getByRole('button', { name: /Name/i })
    fireEvent.click(btn)
    expect(handler).toHaveBeenCalledWith('name')
  })

  it('renders no-columns placeholder when columns=[]', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={[]}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(screen.getByText(/No columns configured/i)).toBeTruthy()
  })

  it('renders a StateIndicator with translated state label', () => {
    renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(screen.getByText('Loaded')).toBeTruthy()
  })

  it('all 9 states render without crashing', () => {
    const all: DataStateValue[] = [
      'loading', 'loaded', 'empty', 'partial', 'stale',
      'unknown', 'error', 'unavailable', 'permissionDenied',
    ]
    for (const s of all) {
      const { container } = renderWithThemeOnly(
        <EnterpriseTable
          columns={COLS}
          rows={ROWS}
          getRowKey={(r) => r.id}
          state={s}
        />,
      )
      expect(container.querySelector('.eg-table')).not.toBeNull()
      cleanup()
    }
  })

  it('renders without error in RTL', () => {
    document.documentElement.dir = 'rtl'
    const { container } = renderWithThemeOnly(
      <EnterpriseTable
        columns={COLS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        state="loaded"
      />,
    )
    expect(container.querySelector('table')).not.toBeNull()
    document.documentElement.dir = 'ltr'
  })
})
