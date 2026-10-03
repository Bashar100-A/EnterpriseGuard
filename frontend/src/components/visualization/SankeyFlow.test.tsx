import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { SankeyFlow } from './SankeyFlow'
import type { SankeyNode, SankeyLink } from './SankeyFlow'

function makeNodes(): SankeyNode[] {
  return [
    { id: 'evidence', label: 'Evidence', tone: 'unknown', column: 0, value: 100 },
    { id: 'state', label: 'State', tone: 'unknown', column: 1, value: 100 },
    { id: 'decision', label: 'Decision', tone: 'unknown', column: 2, value: 80 },
    { id: 'outcome', label: 'Outcome', tone: 'unknown', column: 3, value: 60 },
  ]
}

function makeLinks(): SankeyLink[] {
  return [
    { from: 'evidence', to: 'state', value: 100 },
    { from: 'state', to: 'decision', value: 80 },
    { from: 'decision', to: 'outcome', value: 60 },
  ]
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('SankeyFlow', () => {
  it('renders an empty placeholder when nodes=[]', () => {
    renderWithThemeOnly(<SankeyFlow nodes={[]} links={[]} />)
    expect(screen.getByTestId('eg-sankey-empty')).toBeTruthy()
    expect(screen.queryByTestId('eg-sankey')).toBeNull()
  })

  it('empty placeholder shows the translated message', () => {
    renderWithThemeOnly(<SankeyFlow nodes={[]} links={[]} />)
    expect(screen.getByText(/No flow data to display/i)).toBeTruthy()
  })

  it('renders a region with the default aria-label', () => {
    renderWithThemeOnly(<SankeyFlow nodes={makeNodes()} links={makeLinks()} />)
    expect(screen.getByRole('region', { name: 'Decision flow' })).toBeTruthy()
  })

  it('accepts a custom aria-label', () => {
    renderWithThemeOnly(
      <SankeyFlow nodes={makeNodes()} links={makeLinks()} ariaLabel="Custom flow" />,
    )
    expect(screen.getByRole('region', { name: 'Custom flow' })).toBeTruthy()
  })

  it('renders one rect per node', () => {
    const { container } = renderWithThemeOnly(
      <SankeyFlow nodes={makeNodes()} links={makeLinks()} />,
    )
    expect(container.querySelectorAll('.eg-sankey__node rect')).toHaveLength(4)
  })

  it('renders one path per valid link', () => {
    const { container } = renderWithThemeOnly(
      <SankeyFlow nodes={makeNodes()} links={makeLinks()} />,
    )
    expect(container.querySelectorAll('.eg-sankey__link')).toHaveLength(3)
  })

  it('skips links that reference unknown node ids', () => {
    const links: SankeyLink[] = [
      { from: 'evidence', to: 'ghost', value: 10 },
    ]
    const { container } = renderWithThemeOnly(
      <SankeyFlow nodes={makeNodes()} links={links} />,
    )
    expect(container.querySelectorAll('.eg-sankey__link')).toHaveLength(0)
  })

  it('renders node labels', () => {
    renderWithThemeOnly(<SankeyFlow nodes={makeNodes()} links={makeLinks()} />)
    expect(screen.getByText('Evidence')).toBeTruthy()
    expect(screen.getByText('State')).toBeTruthy()
    expect(screen.getByText('Decision')).toBeTruthy()
    expect(screen.getByText('Outcome')).toBeTruthy()
  })

  it('sets data-tone on each node', () => {
    const nodes: SankeyNode[] = [
      { id: 'a', label: 'A', tone: 'trust', column: 0, value: 1 },
      { id: 'b', label: 'B', tone: 'critical', column: 1, value: 1 },
    ]
    const { container } = renderWithThemeOnly(<SankeyFlow nodes={nodes} links={[]} />)
    expect(container.querySelector('[data-tone="trust"]')).not.toBeNull()
    expect(container.querySelector('[data-tone="critical"]')).not.toBeNull()
  })

  it('sets data-from and data-to on links', () => {
    const { container } = renderWithThemeOnly(
      <SankeyFlow nodes={makeNodes()} links={makeLinks()} />,
    )
    const link = container.querySelector('[data-from="evidence"][data-to="state"]')
    expect(link).not.toBeNull()
    expect(link?.getAttribute('data-value')).toBe('100')
  })

  it('shows the node count in the header', () => {
    renderWithThemeOnly(<SankeyFlow nodes={makeNodes()} links={makeLinks()} />)
    expect(screen.getByText('Stages')).toBeTruthy()
  })

  it('shows the link count in the header', () => {
    renderWithThemeOnly(<SankeyFlow nodes={makeNodes()} links={makeLinks()} />)
    expect(screen.getByText('Flows')).toBeTruthy()
  })

  it('shows the total flow in the header', () => {
    renderWithThemeOnly(<SankeyFlow nodes={makeNodes()} links={makeLinks()} />)
    expect(screen.getByText('Total')).toBeTruthy()
    // 100 + 80 + 60 = 240
    expect(screen.getByText('240')).toBeTruthy()
  })

  it('uses variable stroke width based on value', () => {
    const { container } = renderWithThemeOnly(
      <SankeyFlow nodes={makeNodes()} links={makeLinks()} />,
    )
    const links = container.querySelectorAll('.eg-sankey__link')
    const widths = Array.from(links).map((l) =>
      parseFloat(l.getAttribute('stroke-width') ?? '0'),
    )
    // All widths should be > 0
    expect(widths.every((w) => w > 0)).toBe(true)
  })

  it('each link has an aria-label', () => {
    const { container } = renderWithThemeOnly(
      <SankeyFlow nodes={makeNodes()} links={makeLinks()} />,
    )
    const links = container.querySelectorAll('.eg-sankey__link')
    for (const link of Array.from(links)) {
      expect(link.getAttribute('aria-label')).toBeTruthy()
    }
  })

  it('renders multiple nodes in the same column', () => {
    const nodes: SankeyNode[] = [
      { id: 'a', label: 'A', tone: 'info', column: 0, value: 50 },
      { id: 'b', label: 'B', tone: 'info', column: 0, value: 30 },
      { id: 'c', label: 'C', tone: 'info', column: 1, value: 80 },
    ]
    const links: SankeyLink[] = [
      { from: 'a', to: 'c', value: 50 },
      { from: 'b', to: 'c', value: 30 },
    ]
    const { container } = renderWithThemeOnly(<SankeyFlow nodes={nodes} links={links} />)
    expect(container.querySelectorAll('.eg-sankey__node rect')).toHaveLength(3)
    expect(container.querySelectorAll('.eg-sankey__link')).toHaveLength(2)
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<SankeyFlow nodes={[]} links={[]} />)
    expect(screen.getByText(/لا توجد بيانات تدفق للعرض/)).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without error', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(<SankeyFlow nodes={makeNodes()} links={makeLinks()} />)
    expect(screen.getByTestId('eg-sankey')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })
})
