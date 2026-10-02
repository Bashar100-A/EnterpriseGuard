import { useCallback, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import i18n, { changeLanguage, type SupportedLanguage } from '../../i18n'
import { useTheme, THEME_MODES, type ThemeMode } from '../../theme'

/**
 * Environment label derived from Vite's build mode. This is a real value,
 * not fake telemetry: Vite sets MODE to 'development' for `vite dev` and
 * 'production' for `vite build`.
 */
function resolveEnvironmentKey(): 'production' | 'development' | 'test' | 'unknown' {
  const mode = import.meta.env.MODE
  if (mode === 'production') return 'production'
  if (mode === 'development') return 'development'
  if (mode === 'test') return 'test'
  return 'unknown'
}

interface LanguageSwitcherProps {
  current: SupportedLanguage
  onChange: (lang: SupportedLanguage) => void
  label: string
}

function LanguageSwitcher({ current, onChange, label }: LanguageSwitcherProps): ReactElement {
  const { t } = useTranslation('topbar')
  return (
    <div className="eg-topbar__lang" role="group" aria-label={label}>
      <button
        type="button"
        className={`eg-topbar__lang-btn ${current === 'en' ? 'eg-topbar__lang-btn--active' : ''}`}
        aria-pressed={current === 'en'}
        onClick={() => onChange('en')}
      >
        {t('language.en')}
      </button>
      <button
        type="button"
        className={`eg-topbar__lang-btn ${current === 'ar' ? 'eg-topbar__lang-btn--active' : ''}`}
        aria-pressed={current === 'ar'}
        onClick={() => onChange('ar')}
      >
        {t('language.ar')}
      </button>
    </div>
  )
}

interface ThemeSwitcherProps {
  mode: ThemeMode
  onCycle: () => void
  label: string
}

function ThemeSwitcher({ mode, onCycle, label }: ThemeSwitcherProps): ReactElement {
  const { t } = useTranslation('topbar')
  const icon = mode === 'dark' ? '◐' : mode === 'light' ? '◑' : '◓'
  return (
    <button
      type="button"
      className="eg-topbar__icon-btn"
      onClick={onCycle}
      aria-label={t('theme.cycle')}
      title={`${label}: ${t(`theme.${mode}`)}`}
      data-theme-mode={mode}
    >
      <span aria-hidden="true">{icon}</span>
    </button>
  )
}

export interface TopbarProps {
  /** Current workspace breadcrumb (route path). Defaults to '/'. */
  currentPath?: string
}

/**
 * Topbar — global command bar (spec §15).
 * Left: workspace breadcrumb. Center: search trigger (visual, no behavior).
 * Right: environment badge, language switcher, theme switcher, user slot.
 *
 * No business logic. No operational data. No fake telemetry.
 * All state is either real (Vite mode, i18n, theme) or explicitly 'Unknown'.
 */
export function Topbar({ currentPath = '/' }: TopbarProps): ReactElement {
  const { t } = useTranslation('topbar')
  const { mode, setMode } = useTheme()

  const currentLang: SupportedLanguage = i18n.language === 'ar' ? 'ar' : 'en'
  const envKey = resolveEnvironmentKey()

  const handleLanguageChange = useCallback((lang: SupportedLanguage) => {
    void changeLanguage(lang)
  }, [])

  const handleCycleTheme = useCallback(() => {
    const idx = THEME_MODES.indexOf(mode)
    const next = THEME_MODES[(idx + 1) % THEME_MODES.length] ?? 'dark'
    setMode(next)
  }, [mode, setMode])

  // Very small breadcrumb derivation — no routing yet.
  const pathSegment = currentPath === '/' ? 'overview' : currentPath.replace(/^\//, '')
  const breadcrumbLabel = t(`breadcrumb.home`)

  return (
    <div className="eg-topbar">
      <div className="eg-topbar__start">
        <span className="eg-topbar__vendor">EnterpriseGuard</span>
        <span className="eg-topbar__sep" aria-hidden="true">/</span>
        <span className="eg-topbar__workspace" aria-current="page">
          {breadcrumbLabel}
          {pathSegment !== 'overview' && (
            <>
              <span className="eg-topbar__sep" aria-hidden="true">/</span>
              <span className="eg-topbar__crumb-tail">{pathSegment}</span>
            </>
          )}
        </span>
      </div>

      <div className="eg-topbar__center">
        <button
          type="button"
          className="eg-topbar__search"
          aria-label={t('search.label')}
          title={t('search.hint')}
          disabled
        >
          <span className="eg-topbar__search-icon" aria-hidden="true">⌕</span>
          <span className="eg-topbar__search-label">{t('search.label')}</span>
          <span className="eg-topbar__search-shortcut" aria-hidden="true">{t('search.shortcut')}</span>
        </button>
      </div>

      <div className="eg-topbar__end">
        <span
          className="eg-topbar__badge eg-topbar__badge--env"
          title={t('environment.label')}
        >
          {t(`environment.${envKey}`)}
        </span>

        <span
          className="eg-topbar__badge eg-topbar__badge--state"
          title={t('systemState.label')}
          data-state="unknown"
        >
          {t('systemState.unknown')}
        </span>

        <LanguageSwitcher
          current={currentLang}
          onChange={handleLanguageChange}
          label={t('language.label')}
        />

        <ThemeSwitcher mode={mode} onCycle={handleCycleTheme} label={t('theme.label')} />

        <button
          type="button"
          className="eg-topbar__icon-btn eg-topbar__user"
          aria-label={t('user.label')}
          title={t('user.notConnected')}
          disabled
        >
          <span aria-hidden="true">◯</span>
        </button>
      </div>
    </div>
  )
}
