import { useTranslation } from 'react-i18next'

interface DocSection {
  key: 'playground' | 'tokens' | 'icons' | 'semantics'
}

const SECTIONS: DocSection[] = [
  { key: 'playground' },
  { key: 'tokens' },
  { key: 'icons' },
  { key: 'semantics' },
]

export function DocsPage() {
  const { t } = useTranslation('docs')

  return (
    
      <section
        className="eg-docs"
        role="region"
        aria-label={t('title')}
            data-testid="docs-region"
      >
        <header className="eg-docs__header">
          <h2 className="eg-docs__heading">{t('title')}</h2>
          <p className="eg-docs__description">{t('description')}</p>
        </header>

        <div className="eg-docs__grid">
          {SECTIONS.map((s) => (
            <article
              key={s.key}
              className="eg-docs__card"
              data-testid={`docs-card-${s.key}`}
            >
              <h3 className="eg-docs__card-title">
                {t(`sections.${s.key}.title`)}
              </h3>
              <p className="eg-docs__card-description">
                {t(`sections.${s.key}.description`)}
              </p>
              <p className="eg-docs__card-footnote">{t('comingSoon')}</p>
            </article>
          ))}
        </div>

        <p className="eg-note eg-docs__note">{t('backendNote')}</p>
      </section>
    
  )
}
