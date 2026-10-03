import { useCallback, useMemo, useState, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import type { SemanticTone } from '../security/tone'

export interface TreeNode {
  id: string
  /** Parent node id, or null for a root. */
  parentId: string | null
  /** Localized display label. */
  label: string
  /** Semantic tone — drives the node bullet color. Default: 'unknown'. */
  tone?: SemanticTone
  /** Optional count badge. */
  count?: number | null
  /** Initial expanded state. Default: true. */
  defaultExpanded?: boolean
}

export interface HierarchyTreeProps {
  nodes: TreeNode[]
  /** Optional accessible name. Falls back to a translated default. */
  ariaLabel?: string
  /** Show the node/root counts in the header. Default: true. */
  showCounts?: boolean
}

interface NodeWithChildren extends TreeNode {
  children: NodeWithChildren[]
  depth: number
}

/**
 * Build a nested tree from a flat list of nodes with parentId pointers.
 * Nodes whose parentId points to a missing node are treated as roots —
 * this makes the tree tolerant of partial data without silently dropping
 * nodes.
 */
function buildTree(flat: TreeNode[]): NodeWithChildren[] {
  const map = new Map<string, NodeWithChildren>()
  for (const n of flat) {
    map.set(n.id, { ...n, children: [], depth: 0 })
  }
  const roots: NodeWithChildren[] = []
  for (const n of flat) {
    const node = map.get(n.id)
    if (node === undefined) continue
    const parent = n.parentId === null ? undefined : map.get(n.parentId)
    if (parent === undefined) {
      roots.push(node)
    } else {
      parent.children.push(node)
    }
  }
  // Assign depth
  const assignDepth = (list: NodeWithChildren[], d: number): void => {
    for (const n of list) {
      n.depth = d
      assignDepth(n.children, d + 1)
    }
  }
  assignDepth(roots, 0)
  return roots
}

const TONE_CLASS: Record<SemanticTone, string> = {
  trust: 'trust',
  info: 'info',
  warning: 'warning',
  critical: 'critical',
  unknown: 'unknown',
}

interface NodeRowProps {
  node: NodeWithChildren
  expandedSet: Set<string>
  onToggle: (id: string) => void
}

function NodeRow({ node, expandedSet, onToggle }: NodeRowProps): ReactElement {
  const { t } = useTranslation('visualization')
  const hasChildren = node.children.length > 0
  const isExpanded = expandedSet.has(node.id)
  const tone = node.tone ?? 'unknown'

  const ariaExpand = isExpanded
    ? (t('tree.collapse', { label: node.label }) as string)
    : (t('tree.expand', { label: node.label }) as string)

  return (
    <li
      className="eg-tree__node"
      role="treeitem"
      aria-expanded={hasChildren ? isExpanded : undefined}
      data-node-id={node.id}
      data-tone={tone}
      data-depth={node.depth}
      data-has-children={hasChildren ? 'true' : 'false'}
    >
      <div className="eg-tree__row" style={{ paddingInlineStart: `${node.depth * 16}px` }}>
        {hasChildren ? (
          <button
            type="button"
            className="eg-tree__toggle"
            onClick={() => onToggle(node.id)}
            aria-label={ariaExpand}
            aria-expanded={isExpanded}
            data-testid={`eg-tree-toggle-${node.id}`}
          >
            <span aria-hidden="true">{isExpanded ? '▾' : '▸'}</span>
          </button>
        ) : (
          <span className="eg-tree__toggle eg-tree__toggle--leaf" aria-hidden="true" />
        )}
        <span className="eg-tree__bullet" data-tone={tone} aria-hidden="true" />
        <span className="eg-tree__label">{node.label}</span>
        {node.count !== null && node.count !== undefined && (
          <span className="eg-tree__count">{node.count}</span>
        )}
      </div>

      {hasChildren && isExpanded && (
        <ul className="eg-tree__children" role="group">
          {node.children.map((child) => (
            <NodeRow
              key={child.id}
              node={child}
              expandedSet={expandedSet}
              onToggle={onToggle}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

/**
 * HierarchyTree — a collapsible tree view.
 *
 * Design:
 *   - Nodes have parent/child relationships via `parentId`.
 *   - Each node can be expanded or collapsed.
 *   - Nodes with children render a chevron button; leaf nodes render a
 *     small spacer to keep labels aligned.
 *   - Uses `role="tree"` / `role="treeitem"` for accessibility.
 *   - Indentation is logical (padding-inline-start), so RTL works.
 *
 * The component does NOT sort. Children appear in the order they were
 * supplied. Roots appear in the order they were supplied.
 *
 * If the flat list is empty, an empty state is rendered.
 */
export function HierarchyTree({
  nodes,
  ariaLabel,
  showCounts = true,
}: HierarchyTreeProps): ReactElement {
  const { t } = useTranslation('visualization')

  const roots = useMemo(() => buildTree(nodes), [nodes])

  // Initial expanded set: derived once from defaultExpanded (defaults to true).
  const initialExpanded = useMemo(() => {
    const s = new Set<string>()
    for (const n of nodes) {
      if (n.defaultExpanded !== false) s.add(n.id)
    }
    return s
  }, [nodes])

  const [expandedSet, setExpandedSet] = useState<Set<string>>(initialExpanded)
  // If the nodes prop changes identity, reset expanded state.
  // Using a small trick: track a "version" via JSON of ids.
  const idsKey = useMemo(() => nodes.map((n) => n.id).join('|'), [nodes])
  const lastKeyRef = useMemo(() => ({ current: idsKey }), [])
  if (lastKeyRef.current !== idsKey) {
    lastKeyRef.current = idsKey
    // Synchronous state correction; safe because we're inside render and
    // the value is derived from props.
    setExpandedSet(initialExpanded)
  }

  const handleToggle = useCallback((id: string) => {
    setExpandedSet((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  if (nodes.length === 0) {
    return (
      <div
        className="eg-tree eg-tree--empty"
        data-testid="eg-tree-empty"
      >
        <p className="eg-tree__empty">{t('tree.empty')}</p>
      </div>
    )
  }

  return (
    <section
      className="eg-tree"
      role="region"
      aria-label={ariaLabel ?? (t('tree.label') as string)}
      data-testid="eg-tree"
    >
      <header className="eg-tree__header">
        <h3 className="eg-tree__title">{t('tree.label')}</h3>
        {showCounts && (
          <div className="eg-tree__stats">
            <span className="eg-tree__stat">
              <span className="eg-tree__stat-label">{t('tree.nodeCount')}</span>
              <span className="eg-tree__stat-value">{nodes.length}</span>
            </span>
            <span className="eg-tree__stat">
              <span className="eg-tree__stat-label">{t('tree.rootCount')}</span>
              <span className="eg-tree__stat-value">{roots.length}</span>
            </span>
          </div>
        )}
      </header>

      <ul className="eg-tree__root" role="tree" aria-label={t('tree.label') as string}>
        {roots.map((root) => (
          <NodeRow
            key={root.id}
            node={root}
            expandedSet={expandedSet}
            onToggle={handleToggle}
          />
        ))}
      </ul>
    </section>
  )
}

// Silence the eslint rule that complained earlier about fast-refresh when
// a file exports both a component and helpers. This file exports only the
// component + types, but the internal helpers are still detected by ESLint
// in some configurations.
export const __TREE_TONE_CLASS = TONE_CLASS
