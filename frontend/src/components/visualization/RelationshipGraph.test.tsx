import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { RelationshipGraph } from './RelationshipGraph'
import type { GraphNode, GraphEdge } from './RelationshipGraph'

function makeNodes(): GraphNode[] {
  return [
    { id: 'evidence', label: 'Evidence', tone: 'unknown', count: null, x: 15, y: 25 },
    { id: 'decision', label: 'Decision', tone: 'unknown', count: null, x: 50, y: 50 },
    { id: 'outcome', label: 'Outcome', tone: 'unknown', count: null, x: 85, y: 75 },
  ]
}

function makeEdges(): GraphEdge[] {
  return [
    { from: 'evidence', to: 'decision', tone: 'unknown' },
    { from: 'decision', to: 'outcome', tone: 'unknown' },
  ]
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('RelationshipGraph', () => {
  it('renders an empty placeholder when nodes=[]', () => {
    renderWithThemeOnly(<RelationshipGraph nodes={[]} edges={[]} />)
    expect(screen.getByTestId('eg-relgraph-empty')).toBeTruthy()
    expect(screen.queryByTestId('eg-relgraph')).toBeNull()
  })

  it('empty placeholder shows the translated message', () => {
    renderWithThemeOnly(<RelationshipGraph nodes={[]} edges={[]} />)
    expect(screen.getByText(/No relationships to display/i)).toBeTruthy()
  })

  it('renders an SVG with role=img and an aria-label', () => {
    renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    const svg = screen.getByRole('img')
    expect(svg).toBeTruthy()
    expect(svg.getAttribute('aria-label')).toBe('Relationship graph')
  })

  it('accepts a custom aria-label', () => {
    renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} ariaLabel="Custom" />,
    )
    expect(screen.getByRole('img').getAttribute('aria-label')).toBe('Custom')
  })

  it('renders one <g> per node', () => {
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    expect(container.querySelectorAll('.eg-relgraph__node')).toHaveLength(3)
  })

  it('renders one <line> per edge', () => {
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    expect(container.querySelectorAll('.eg-relgraph__edge')).toHaveLength(2)
  })

  it('renders node labels', () => {
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    const texts = Array.from(container.querySelectorAll('.eg-relgraph__node-label'))
    expect(texts.map((t) => t.textContent)).toEqual(['Evidence', 'Decision', 'Outcome'])
  })

  it('renders — for null node counts', () => {
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    const counts = Array.from(container.querySelectorAll('.eg-relgraph__node-count'))
    expect(counts.every((c) => c.textContent === '—')).toBe(true)
  })

  it('renders numeric node counts when provided', () => {
    const nodes: GraphNode[] = [
      { id: 'a', label: 'A', tone: 'trust', count: 42, x: 50, y: 50 },
    ]
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={nodes} edges={[]} />,
    )
    const count = container.querySelector('.eg-relgraph__node-count')
    expect(count?.textContent).toBe('42')
  })

  it('sets data-tone on each node', () => {
    const nodes: GraphNode[] = [
      { id: 'a', label: 'A', tone: 'trust', x: 20, y: 20 },
      { id: 'b', label: 'B', tone: 'critical', x: 80, y: 80 },
    ]
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={nodes} edges={[]} />,
    )
    expect(container.querySelector('[data-tone="trust"]')).not.toBeNull()
    expect(container.querySelector('[data-tone="critical"]')).not.toBeNull()
  })

  it('sets data-from and data-to on each edge', () => {
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    const edge = container.querySelector('[data-from="evidence"][data-to="decision"]')
    expect(edge).not.toBeNull()
  })

  it('skips edges that reference unknown node ids', () => {
    const edges: GraphEdge[] = [
      { from: 'evidence', to: 'ghost', tone: 'unknown' },
    ]
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={edges} />,
    )
    expect(container.querySelectorAll('.eg-relgraph__edge')).toHaveLength(0)
  })

  it('shows node and edge counts', () => {
    renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    expect(screen.getByText('Nodes')).toBeTruthy()
    expect(screen.getByText('Connections')).toBeTruthy()
  })

  it('respects a custom aspect ratio', () => {
    const { container } = renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} aspect="4 / 3" />,
    )
    const root = container.querySelector('.eg-relgraph') as HTMLElement | null
    expect(root?.style.aspectRatio).toBe('4 / 3')
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<RelationshipGraph nodes={[]} edges={[]} />)
    expect(screen.getByText(/لا توجد علاقات للعرض/)).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without error', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(
      <RelationshipGraph nodes={makeNodes()} edges={makeEdges()} />,
    )
    expect(screen.getByRole('img')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })
})
