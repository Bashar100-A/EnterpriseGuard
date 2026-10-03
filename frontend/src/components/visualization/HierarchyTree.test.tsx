import { describe, it, expect, afterEach } from 'vitest'
import { screen, cleanup, fireEvent } from '@testing-library/react'
import { renderWithThemeOnly } from '../../test/renderWithProviders'
import { HierarchyTree } from './HierarchyTree'
import type { TreeNode } from './HierarchyTree'

function makeNodes(): TreeNode[] {
  return [
    { id: 'root', label: 'Policies', parentId: null },
    { id: 'gov', label: 'Governance', parentId: 'root' },
    { id: 'sec', label: 'Security', parentId: 'root' },
    { id: 'g1', label: 'POL-GOV-001', parentId: 'gov' },
    { id: 'g2', label: 'POL-GOV-002', parentId: 'gov' },
    { id: 's1', label: 'POL-SEC-001', parentId: 'sec' },
  ]
}

afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

describe('HierarchyTree', () => {
  it('renders an empty placeholder when nodes=[]', () => {
    renderWithThemeOnly(<HierarchyTree nodes={[]} />)
    expect(screen.getByTestId('eg-tree-empty')).toBeTruthy()
    expect(screen.queryByTestId('eg-tree')).toBeNull()
  })

  it('empty placeholder shows the translated message', () => {
    renderWithThemeOnly(<HierarchyTree nodes={[]} />)
    expect(screen.getByText(/No hierarchy to display/i)).toBeTruthy()
  })

  it('renders a region with the default aria-label', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    expect(screen.getByRole('region', { name: 'Hierarchy' })).toBeTruthy()
  })

  it('accepts a custom aria-label', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} ariaLabel="Policy tree" />)
    expect(screen.getByRole('region', { name: 'Policy tree' })).toBeTruthy()
  })

  it('renders one treeitem per visible node', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    const items = screen.getAllByRole('treeitem')
    expect(items).toHaveLength(6)
  })

  it('renders all labels when fully expanded (default)', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    expect(screen.getByText('Policies')).toBeTruthy()
    expect(screen.getByText('Governance')).toBeTruthy()
    expect(screen.getByText('Security')).toBeTruthy()
    expect(screen.getByText('POL-GOV-001')).toBeTruthy()
    expect(screen.getByText('POL-GOV-002')).toBeTruthy()
    expect(screen.getByText('POL-SEC-001')).toBeTruthy()
  })

  it('respects defaultExpanded=false (collapses on mount)', () => {
    const nodes: TreeNode[] = [
      { id: 'root', label: 'Root', parentId: null, defaultExpanded: false },
      { id: 'child', label: 'Child', parentId: 'root' },
    ]
    renderWithThemeOnly(<HierarchyTree nodes={nodes} />)
    expect(screen.getByText('Root')).toBeTruthy()
    expect(screen.queryByText('Child')).toBeNull()
  })

  it('clicking the toggle collapses children', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    expect(screen.getByText('Governance')).toBeTruthy()
    fireEvent.click(screen.getByTestId('eg-tree-toggle-root'))
    expect(screen.queryByText('Governance')).toBeNull()
    expect(screen.queryByText('POL-GOV-001')).toBeNull()
  })

  it('clicking the toggle again re-expands', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    fireEvent.click(screen.getByTestId('eg-tree-toggle-root'))
    expect(screen.queryByText('Governance')).toBeNull()
    fireEvent.click(screen.getByTestId('eg-tree-toggle-root'))
    expect(screen.getByText('Governance')).toBeTruthy()
  })

  it('sets aria-expanded=true on expanded nodes with children', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    const rootItem = screen.getByTestId('eg-tree-toggle-root').closest('li')
    expect(rootItem?.getAttribute('aria-expanded')).toBe('true')
  })

  it('sets aria-expanded=false after collapsing', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    fireEvent.click(screen.getByTestId('eg-tree-toggle-root'))
    const rootItem = screen.getByTestId('eg-tree-toggle-root').closest('li')
    expect(rootItem?.getAttribute('aria-expanded')).toBe('false')
  })

  it('does NOT render a toggle button for leaf nodes', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    // POL-GOV-001 is a leaf; its toggle should be a spacer, not a button
    expect(screen.queryByTestId('eg-tree-toggle-g1')).toBeNull()
  })

  it('leaf nodes have data-has-children=false', () => {
    const { container } = renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    const leaf = container.querySelector('[data-node-id="g1"]')
    expect(leaf?.getAttribute('data-has-children')).toBe('false')
  })

  it('renders node counts when provided', () => {
    const nodes: TreeNode[] = [
      { id: 'a', label: 'A', parentId: null, count: 42 },
    ]
    renderWithThemeOnly(<HierarchyTree nodes={nodes} />)
    expect(screen.getByText('42')).toBeTruthy()
  })

  it('sets data-depth per node', () => {
    const { container } = renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    expect(container.querySelector('[data-node-id="root"]')?.getAttribute('data-depth')).toBe('0')
    expect(container.querySelector('[data-node-id="gov"]')?.getAttribute('data-depth')).toBe('1')
    expect(container.querySelector('[data-node-id="g1"]')?.getAttribute('data-depth')).toBe('2')
  })

  it('sets data-tone per node', () => {
    const nodes: TreeNode[] = [
      { id: 'a', label: 'A', parentId: null, tone: 'trust' },
      { id: 'b', label: 'B', parentId: 'a', tone: 'critical' },
    ]
    const { container } = renderWithThemeOnly(<HierarchyTree nodes={nodes} />)
    expect(container.querySelector('[data-node-id="a"]')?.getAttribute('data-tone')).toBe('trust')
    expect(container.querySelector('[data-node-id="b"]')?.getAttribute('data-tone')).toBe('critical')
  })

  it('treats nodes with missing parents as roots', () => {
    const nodes: TreeNode[] = [
      { id: 'orphan', label: 'Orphan', parentId: 'ghost' },
    ]
    const { container } = renderWithThemeOnly(<HierarchyTree nodes={nodes} />)
    expect(container.querySelector('[data-node-id="orphan"]')).not.toBeNull()
  })

  it('shows node count in the header', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    expect(screen.getByText('Nodes')).toBeTruthy()
  })

  it('shows root count in the header', () => {
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    expect(screen.getByText('Roots')).toBeTruthy()
  })

  it('renders in Arabic', async () => {
    const { changeLanguage } = await import('../../i18n')
    await changeLanguage('ar')
    renderWithThemeOnly(<HierarchyTree nodes={[]} />)
    expect(screen.getByText(/لا يوجد تسلسل للعرض/)).toBeTruthy()
    await changeLanguage('en')
  })

  it('renders in RTL without error', () => {
    document.documentElement.dir = 'rtl'
    renderWithThemeOnly(<HierarchyTree nodes={makeNodes()} />)
    expect(screen.getByTestId('eg-tree')).toBeTruthy()
    document.documentElement.dir = 'ltr'
  })
})
