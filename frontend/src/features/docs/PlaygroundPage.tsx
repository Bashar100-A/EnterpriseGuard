import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'

import {
  StatusBadge,
  SeverityBadge,
  VerificationBadge,
  EnvironmentBadge,
  StateIndicator,
  EvidenceIndicator,
  TechnicalIdentifier,
} from '../../components/security'
import type {
  StatusKey,
  SeverityLevel,
  VerificationState,
  EnvironmentKey,
  SemanticTone,
} from '../../components/security'

import {
  MetricCard,
  EnterpriseTable,
  ChartFrame,
} from '../../components/data-display'
import type { EnterpriseColumn } from '../../components/data-display'

import { DataState } from '../../components/states'

import type { Evidence } from '../../services/contracts'
import { evidenceListFixture, isFixture } from '../../services/designFixtures'

const STATUS_SAMPLES: readonly StatusKey[] = [
  'pending',
  'proposed',
  'information',
  'unknown',
]

const SEVERITY_SAMPLES: readonly SeverityLevel[] = [
  'info',
  'low',
  'medium',
  'high',
  'critical',
]

const VERIFICATION_SAMPLES: readonly VerificationState[] = [
  'verified',
  'unverified',
  'invalid',
  'unknown',
  'notAvailable',
]

const ENVIRONMENT_SAMPLES: readonly EnvironmentKey[] = [
  'production',
  'staging',
  'development',
  'test',
  'unknown',
]

const TONE_SAMPLES: readonly SemanticTone[] = [
  'trust',
  'info',
  'warning',
  'critical',
  'unknown',
]

const evidenceColumns: EnterpriseColumn<Evidence>[] = [
  { key: 'id', header: 'ID' },
  { key: 'source', header: 'Source' },
  {
    key: 'verification',
    header: 'Verification',
    render: (e) => <VerificationBadge state={e.verification} />,
  },
  { key: 'summary', header: 'Summary' },
]

/**
 * PlaygroundPage — design-only preview of UI primitives.
 *
 * Semantic constraints (ADIE + DEVELOPMENT.md):
 *   - This page is a design reference. It NEVER mocks live data for pages.
 *   - Metric cards are shown in the honest "not connected" state.
 *   - The one fixture used (evidenceListFixture) is marked with
 *     `__egFixture`; the marker is asserted at module load.
 *   - No fetch, no adapters, no query client.
 */
export function PlaygroundPage(): ReactElement {
  const { t } = useTranslation('docs')

  // Fail-closed: if the fixture ever loses its marker, refuse to render.
  if (!isFixture(evidenceListFixture)) {
    throw new Error('PlaygroundPage: expected a marked fixture')
  }

  return (
    <section
      className="eg-playground"
      role="region"
      aria-label={t('playgroundPage.title')}
      data-testid="playground-region"
    >
      <header className="eg-playground__header">
        <h2 className="eg-playground__heading">{t('playgroundPage.title')}</h2>
        <p className="eg-playground__description">
          {t('playgroundPage.description')}
        </p>
        <p className="eg-playground__fixture-note">
          {t('playgroundPage.fixtureNote')}
        </p>
      </header>

      <section className="eg-playground__section" aria-labelledby="pg-badges">
        <h3 id="pg-badges" className="eg-playground__section-title">
          {t('playgroundPage.sections.badges')}
        </h3>
        <div className="eg-playground__grid">
          <div className="eg-playground__cell">
            <div className="eg-playground__cell-label">StatusBadge</div>
            <div className="eg-playground__cell-body">
              {STATUS_SAMPLES.map((s) => (
                <StatusBadge key={s} status={s} />
              ))}
            </div>
          </div>
          <div className="eg-playground__cell">
            <div className="eg-playground__cell-label">SeverityBadge</div>
            <div className="eg-playground__cell-body">
              {SEVERITY_SAMPLES.map((s) => (
                <SeverityBadge key={s} severity={s} />
              ))}
            </div>
          </div>
          <div className="eg-playground__cell">
            <div className="eg-playground__cell-label">VerificationBadge</div>
            <div className="eg-playground__cell-body">
              {VERIFICATION_SAMPLES.map((s) => (
                <VerificationBadge key={s} state={s} />
              ))}
            </div>
          </div>
          <div className="eg-playground__cell">
            <div className="eg-playground__cell-label">EnvironmentBadge</div>
            <div className="eg-playground__cell-body">
              {ENVIRONMENT_SAMPLES.map((s) => (
                <EnvironmentBadge key={s} environment={s} />
              ))}
            </div>
          </div>
        </div>
      </section>

      <section
        className="eg-playground__section"
        aria-labelledby="pg-indicators"
      >
        <h3 id="pg-indicators" className="eg-playground__section-title">
          {t('playgroundPage.sections.indicators')}
        </h3>
        <div className="eg-playground__grid">
          <div className="eg-playground__cell">
            <div className="eg-playground__cell-label">StateIndicator</div>
            <div className="eg-playground__cell-body eg-playground__cell-body--column">
              {TONE_SAMPLES.map((tone) => (
                <StateIndicator key={tone} tone={tone} label={tone} />
              ))}
            </div>
          </div>
          <div className="eg-playground__cell">
            <div className="eg-playground__cell-label">EvidenceIndicator</div>
            <div className="eg-playground__cell-body eg-playground__cell-body--column">
              {VERIFICATION_SAMPLES.map((s) => (
                <EvidenceIndicator key={s} state={s} count={3} />
              ))}
            </div>
          </div>
        </div>
      </section>

      <section
        className="eg-playground__section"
        aria-labelledby="pg-identifiers"
      >
        <h3 id="pg-identifiers" className="eg-playground__section-title">
          {t('playgroundPage.sections.identifiers')}
        </h3>
        <div className="eg-playground__grid">
          <div className="eg-playground__cell">
            <div className="eg-playground__cell-label">
              TechnicalIdentifier
            </div>
            <div className="eg-playground__cell-body eg-playground__cell-body--column">
              <TechnicalIdentifier
                value="dec_01H2XW9K7F3GQ7P1Z8M4T6R2V5"
                prefix="DEC-"
              />
              <TechnicalIdentifier
                value="manifest-2026-01-14-avery-long-identifier-value-here"
                prefix="MF-"
                size="sm"
              />
              <TechnicalIdentifier value="ev-001" />
            </div>
          </div>
        </div>
      </section>

      <section
        className="eg-playground__section"
        aria-labelledby="pg-data-display"
      >
        <h3 id="pg-data-display" className="eg-playground__section-title">
          {t('playgroundPage.sections.dataDisplay')}
        </h3>
        <div className="eg-playground__metrics">
          <MetricCard
            label={t('playgroundPage.metrics.uptime')}
            value={{ value: null }}
            dataState="notConnected"
          />
          <MetricCard
            label={t('playgroundPage.metrics.requests')}
            value={{ value: null }}
            dataState="notConnected"
          />
          <MetricCard
            label={t('playgroundPage.metrics.errors')}
            value={{ value: null }}
            dataState="notConnected"
          />
          <MetricCard
            label={t('playgroundPage.metrics.latency')}
            value={{ value: null }}
            dataState="notConnected"
          />
        </div>
        <div className="eg-playground__table">
          <EnterpriseTable<Evidence>
            columns={evidenceColumns}
            rows={evidenceListFixture.page.items}
            getRowKey={(e) => e.id}
            state="loaded"
            caption={t('playgroundPage.table.fixtureCaption')}
          />
        </div>
      </section>

      <section className="eg-playground__section" aria-labelledby="pg-states">
        <h3 id="pg-states" className="eg-playground__section-title">
          {t('playgroundPage.sections.states')}
        </h3>
        <div className="eg-playground__states">
          <DataState state="empty" />
          <DataState state="loading" />
          <DataState
            state="error"
            onRetry={() => {
              /* visual only */
            }}
          />
          <DataState state="loaded">
            <div className="eg-playground__loaded-sample">Content</div>
          </DataState>
        </div>
      </section>

      <section className="eg-playground__section" aria-labelledby="pg-chart">
        <h3 id="pg-chart" className="eg-playground__section-title">
          {t('playgroundPage.sections.chart')}
        </h3>
        <div className="eg-playground__chart">
          <ChartFrame
            title={t('playgroundPage.chart.title')}
            state="empty"
            height={160}
          />
        </div>
      </section>

      <p className="eg-note eg-playground__note">
        {t('playgroundPage.backendNote')}
      </p>
    </section>
  )
}
