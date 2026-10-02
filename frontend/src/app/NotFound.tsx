import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

export function NotFound(): ReactElement {
  const { t } = useTranslation('errors')
  return (
    <div className="eg-notfound">
      <h2 className="eg-notfound__title">{t('notFound.title')}</h2>
      <p className="eg-notfound__message">{t('notFound.message')}</p>
    </div>
  )
}
