import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

export type NavigationGroupKey =
  | 'command'
  | 'intelligence'
  | 'trust'
  | 'govern'
  | 'operate'
  | 'assurance'
  | 'administration'

export type NavigationItemKey =
  | 'overview'
  | 'securityOperations'
  | 'threatIntelligence'
  | 'decisionIntelligence'
  | 'evidence'
  | 'provenance'
  | 'sibbTrustCore'
  | 'policies'
  | 'governance'
  | 'approvals'
  | 'executionManifests'
  | 'systemHealth'
  | 'inspection'
  | 'maintenance'
  | 'analytics'
  | 'reports'
  | 'audit'
  | 'usersAccess'
  | 'configuration'

export interface NavigationItem {
  key: NavigationItemKey
  group: NavigationGroupKey
  /** Route path (placeholder during UI-01). */
  to: string
  /** Whether this item is currently active. */
  active?: boolean
}

export interface NavigationRailProps {
  expanded: boolean
  onToggleExpanded: () => void
  activePath?: string
  onNavigate?: (item: NavigationItem) => void
}

const GROUP_ORDER: NavigationGroupKey[] = [
  'command',
  'intelligence',
  'trust',
  'govern',
  'operate',
  'assurance',
  'administration',
]

const ITEMS: NavigationItem[] = [
  { key: 'overview', group: 'command', to: '/' },

  { key: 'securityOperations', group: 'intelligence', to: '/operations' },
  { key: 'threatIntelligence', group: 'intelligence', to: '/intelligence' },
  { key: 'decisionIntelligence', group: 'intelligence', to: '/decisions' },

  { key: 'evidence', group: 'trust', to: '/evidence' },
  { key: 'provenance', group: 'trust', to: '/provenance' },
  { key: 'sibbTrustCore', group: 'trust', to: '/sibb' },

  { key: 'policies', group: 'govern', to: '/policies' },
  { key: 'governance', group: 'govern', to: '/governance' },
  { key: 'approvals', group: 'govern', to: '/approvals' },
  { key: 'executionManifests', group: 'govern', to: '/manifests' },

  { key: 'systemHealth', group: 'operate', to: '/health' },
  { key: 'inspection', group: 'operate', to: '/inspection' },
  { key: 'maintenance', group: 'operate', to: '/maintenance' },

  { key: 'analytics', group: 'assurance', to: '/analytics' },
  { key: 'reports', group: 'assurance', to: '/reports' },
  { key: 'audit', group: 'assurance', to: '/audit' },

  { key: 'usersAccess', group: 'administration', to: '/access' },
  { key: 'configuration', group: 'administration', to: '/settings' },
]

export function NavigationRail({
  expanded,
  onToggleExpanded,
  activePath = '/',
  onNavigate,
}: NavigationRailProps): ReactElement {
  const { t } = useTranslation('navigation')

  const handleItemClick = (item: NavigationItem): void => {
    onNavigate?.(item)
  }

  return (
    <nav
      className={`eg-nav ${expanded ? 'eg-nav--expanded' : 'eg-nav--collapsed'}`}
      aria-label={t('actions.toggleRail')}
      data-expanded={expanded}
    >
      <div className="eg-nav__items">
        {GROUP_ORDER.map((group) => {
          const groupItems = ITEMS.filter((it) => it.group === group)
          if (groupItems.length === 0) return null

          return (
            <div key={group} className="eg-nav__group">
              {expanded && (
                <div className="eg-nav__group-label">{t(`groups.${group}`)}</div>
              )}
              <ul className="eg-nav__list" role="list">
                {groupItems.map((item) => {
                  const isActive = item.to === activePath
                  const label = t(`items.${item.key}`)
                  return (
                    <li key={item.key} className="eg-nav__list-item">
                      <button
                        type="button"
                        className={`eg-nav__item ${isActive ? 'eg-nav__item--active' : ''}`}
                        aria-current={isActive ? 'page' : undefined}
                        aria-label={label}
                        title={!expanded ? label : undefined}
                        onClick={() => handleItemClick(item)}
                      >
                        <span className="eg-nav__item-marker" aria-hidden="true" />
                        <span className="eg-nav__item-label">{label}</span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>
          )
        })}
      </div>

      <div className="eg-nav__footer">
        <button
          type="button"
          className="eg-nav__toggle"
          onClick={onToggleExpanded}
          aria-expanded={expanded}
          aria-label={expanded ? t('actions.collapse') : t('actions.expand')}
          title={expanded ? t('actions.collapse') : t('actions.expand')}
        >
          <span aria-hidden="true">{expanded ? '«' : '»'}</span>
        </button>
      </div>
    </nav>
  )
}
