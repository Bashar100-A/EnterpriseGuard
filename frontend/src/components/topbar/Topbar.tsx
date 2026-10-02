import { useCallback, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import i18n, { changeLanguage, type SupportedLanguage } from '../../i18n'
import { useTheme, THEME_MODES, type ThemeMode } from '../../theme'

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
  currentPath?: string
  /** Whether the assurance rail is currently open. */
  assuranceOpen?: boolean
  /** Called when the user toggles the assurance panel. */
  onToggleAssurance?: () => void
}

export function Topbar({
  currentPath = '/',
  assuranceOpen = false,
  onToggleAssurance,
}: TopbarProps): ReactElement {
  const { t } = useTranslation('topbar')
  const { t: tA } = useTranslation('assurance')
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

  const pathSegment = currentPath === '/' ? 'overview' : currentPath.replace(/^\//, '')
  const breadcrumbLabel = t('breadcrumb.home')

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

        {onToggleAssurance !== undefined && (
          <button
            type="button"
            className="eg-topbar__icon-btn"
            onClick={onToggleAssurance}
            aria-label={assuranceOpen ? tA('toggle.close') : tA('toggle.open')}
            aria-pressed={assuranceOpen}
            title={assuranceOpen ? tA('toggle.close') : tA('toggle.open')}
            data-assurance-open={assuranceOpen}
          >
            <span aria-hidden="true">◇</span>
          </button>
        )}

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
