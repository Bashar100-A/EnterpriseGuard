import type { CSSProperties, ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import { TOKEN_GROUPS, type TokenDef } from './tokens'

function previewStyle(token: TokenDef): CSSProperties {
  switch (token.kind) {
    case 'color':
      return { background: `var(${token.name})` }
    case 'spacing':
      return { width: `var(${token.name})` }
    case 'radius':
      return { borderRadius: `var(${token.name})` }
    case 'font-family':
      return { fontFamily: `var(${token.name})` }
    case 'font-size':
      return { fontSize: `var(${token.name})` }
    case 'line-height':
      return { lineHeight: `var(${token.name})` }
  }
}

function previewClass(kind: TokenDef['kind']): string {
  switch (kind) {
    case 'color':
      return 'eg-tokens__swatch'
    case 'spacing':
      return 'eg-tokens__bar'
    case 'radius':
      return 'eg-tokens__box'
    default:
      return 'eg-tokens__sample'
  }
}

function TokenChip({ token }: { token: TokenDef }): ReactElement {
  return (
    <div className="eg-tokens__chip" data-testid={`token-${token.name}`}>
      <span
        className={previewClass(token.kind)}
        style={previewStyle(token)}
        aria-hidden="true"
      />
      <div className="eg-tokens__meta">
        <code className="eg-tokens__name">{token.name}</code>
        <span className="eg-tokens__value">{token.value}</span>
      </div>
    </div>
  )
}

/**
 * TokenViewerPage — static reference of CSS custom properties.
 *
 * Notes (ADIE):
 *   - No computed style reads; token values are declared in tokens.ts.
 *   - Preview swatches use var(--eg-*) so they reflect the live theme.
 *   - Theme-dependent tokens are labeled explicitly.
 */
export function TokenViewerPage(): ReactElement {
  const { t } = useTranslation('docs')

  return (
    <section
      className="eg-tokens"
      role="region"
      aria-label={t('tokenViewerPage.title')}
      data-testid="tokens-region"
    >
      <header className="eg-tokens__header">
        <h2 className="eg-tokens__heading">{t('tokenViewerPage.title')}</h2>
        <p className="eg-tokens__description">
          {t('tokenViewerPage.description')}
        </p>
        <p className="eg-tokens__note">{t('tokenViewerPage.note')}</p>
      </header>

      {TOKEN_GROUPS.map((group) => (
        <section
          key={group.key}
          className="eg-tokens__group"
          aria-label={t(`tokenViewerPage.groups.${group.key}`)}
          data-testid={`tokens-group-${group.key}`}
        >
          <h3 className="eg-tokens__group-title">
            {t(`tokenViewerPage.groups.${group.key}`)}
          </h3>
          <div className="eg-tokens__grid">
            {group.tokens.map((token) => (
              <TokenChip key={token.name} token={token} />
            ))}
          </div>
        </section>
      ))}

      <p className="eg-note eg-tokens__backend-note">
        {t('tokenViewerPage.backendNote')}
      </p>
    </section>
  )
}
