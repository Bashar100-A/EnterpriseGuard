import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import {
  ADOPTED_ICONS,
  CANDIDATE_ICONS,
  TOTAL_ADOPTED,
  TOTAL_CANDIDATES,
} from './icons'

function EmptyNote({
  testId,
  titleKey,
  bodyKey,
}: {
  testId: string
  titleKey: string
  bodyKey: string
}): ReactElement {
  const { t } = useTranslation('docs')
  return (
    <div className="eg-icons__empty" data-testid={testId}>
      <p className="eg-icons__empty-title">{t(titleKey)}</p>
      <p className="eg-icons__empty-body">{t(bodyKey)}</p>
    </div>
  )
}

/**
 * IconCatalogPage — reference for adopted Lucide icons.
 *
 * At present no icon is imported anywhere in src/. This page documents that
 * reality instead of rendering a fabricated catalog.
 */
export function IconCatalogPage(): ReactElement {
  const { t } = useTranslation('docs')

  return (
    <section
      className="eg-icons"
      role="region"
      aria-label={t('iconCatalogPage.title')}
      data-testid="icons-region"
    >
      <header className="eg-icons__header">
        <h2 className="eg-icons__heading">{t('iconCatalogPage.title')}</h2>
        <p className="eg-icons__description">
          {t('iconCatalogPage.description')}
        </p>
      </header>

      <section className="eg-icons__section" aria-labelledby="icons-adopted">
        <h3 id="icons-adopted" className="eg-icons__section-title">
          {t('iconCatalogPage.sections.adopted')}
          <span className="eg-icons__count"> ({TOTAL_ADOPTED})</span>
        </h3>
        {TOTAL_ADOPTED === 0 ? (
          <EmptyNote
            testId="icons-empty-adopted"
            titleKey="iconCatalogPage.emptyAdoptedTitle"
            bodyKey="iconCatalogPage.emptyAdoptedBody"
          />
        ) : (
          <ul className="eg-icons__grid" data-testid="icons-adopted-grid">
            {ADOPTED_ICONS.map((icon) => (
              <li key={icon.name} className="eg-icons__card">
                <code className="eg-icons__name">{icon.name}</code>
                <span className="eg-icons__purpose">
                  {t(icon.purposeKey)}
                </span>
                <span className="eg-icons__where">{icon.where}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="eg-icons__section" aria-labelledby="icons-candidates">
        <h3 id="icons-candidates" className="eg-icons__section-title">
          {t('iconCatalogPage.sections.candidates')}
          <span className="eg-icons__count"> ({TOTAL_CANDIDATES})</span>
        </h3>
        {TOTAL_CANDIDATES === 0 ? (
          <EmptyNote
            testId="icons-empty-candidates"
            titleKey="iconCatalogPage.emptyCandidatesTitle"
            bodyKey="iconCatalogPage.emptyCandidatesBody"
          />
        ) : (
          <ul className="eg-icons__grid" data-testid="icons-candidates-grid">
            {CANDIDATE_ICONS.map((icon) => (
              <li key={icon.name} className="eg-icons__card">
                <code className="eg-icons__name">{icon.name}</code>
                <span className="eg-icons__purpose">
                  {t(icon.purposeKey)}
                </span>
                <span className="eg-icons__where">{icon.where}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="eg-icons__philosophy">
        {t('iconCatalogPage.philosophy')}
      </p>
      <p className="eg-note eg-icons__backend-note">
        {t('iconCatalogPage.backendNote')}
      </p>
    </section>
  )
}
