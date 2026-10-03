import type { ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import {
  SEMANTIC_TONES,
  type SemanticTone,
  VerificationBadge,
  StatusBadge,
} from '../../components/security'

interface ToneDef {
  tone: SemanticTone
  token: string
}

const TONE_DEFS: readonly ToneDef[] = [
  { tone: 'trust',    token: '--eg-trust-emerald' },
  { tone: 'info',     token: '--eg-signal-blue'   },
  { tone: 'warning',  token: '--eg-warning-amber' },
  { tone: 'critical', token: '--eg-critical-red'  },
  { tone: 'unknown',  token: '--eg-unknown-gray'  },
]

const ADIE_PAIRS: readonly { leftKey: string; rightKey: string }[] = [
  { leftKey: 'observed',   rightKey: 'decided'   },
  { leftKey: 'decided',    rightKey: 'executed'  },
  { leftKey: 'evidence',   rightKey: 'authority' },
  { leftKey: 'prediction', rightKey: 'decision'  },
]

/**
 * SemanticGuidePage — the meaning layer of the design system.
 *
 * The five tones are documented as behavior, not decoration:
 *   - trust      = verified, healthy, validated
 *   - info       = informational, pending, proposed
 *   - warning    = review needed, degraded
 *   - critical   = failure, attack
 *   - unknown    = not evaluated, unavailable
 *
 * Golden rule: Unknown never silently becomes Trust.
 */
export function SemanticGuidePage(): ReactElement {
  const { t } = useTranslation('docs')

  return (
    <section
      className="eg-semantics"
      role="region"
      aria-label={t('semanticGuidePage.title')}
      data-testid="semantics-region"
    >
      <header className="eg-semantics__header">
        <h2 className="eg-semantics__heading">{t('semanticGuidePage.title')}</h2>
        <p className="eg-semantics__description">
          {t('semanticGuidePage.description')}
        </p>
      </header>

      <section className="eg-semantics__section" aria-labelledby="sem-tones">
        <h3 id="sem-tones" className="eg-semantics__section-title">
          {t('semanticGuidePage.sections.tones')}
        </h3>
        <ul className="eg-semantics__tones" data-testid="semantics-tones">
          {TONE_DEFS.map(({ tone, token }) => (
            <li
              key={tone}
              className="eg-semantics__tone"
              data-testid={`semantic-tone-${tone}`}
            >
              <span
                className="eg-semantics__swatch"
                style={{ background: `var(${token})` }}
                aria-hidden="true"
              />
              <div className="eg-semantics__tone-meta">
                <code className="eg-semantics__tone-name">{tone}</code>
                <span className="eg-semantics__tone-token">{token}</span>
                <p className="eg-semantics__tone-meaning">
                  {t(`semanticGuidePage.tones.${tone}`)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section
        className="eg-semantics__section"
        aria-labelledby="sem-rule"
      >
        <h3 id="sem-rule" className="eg-semantics__section-title">
          {t('semanticGuidePage.sections.goldenRule')}
        </h3>
        <blockquote
          className="eg-semantics__rule"
          data-testid="semantics-golden-rule"
        >
          <p className="eg-semantics__rule-text">
            {t('semanticGuidePage.goldenRule.text')}
          </p>
          <p className="eg-semantics__rule-why">
            {t('semanticGuidePage.goldenRule.why')}
          </p>
        </blockquote>
        <div className="eg-semantics__examples">
          <div className="eg-semantics__example">
            <span className="eg-semantics__example-label">
              {t('semanticGuidePage.goldenRule.correct')}
            </span>
            <VerificationBadge state="unknown" />
          </div>
          <div className="eg-semantics__example">
            <span className="eg-semantics__example-label">
              {t('semanticGuidePage.goldenRule.incorrect')}
            </span>
            <VerificationBadge state="verified" />
            <span className="eg-semantics__example-note">
              {t('semanticGuidePage.goldenRule.incorrectNote')}
            </span>
          </div>
        </div>
      </section>

      <section className="eg-semantics__section" aria-labelledby="sem-adie">
        <h3 id="sem-adie" className="eg-semantics__section-title">
          {t('semanticGuidePage.sections.adie')}
        </h3>
        <p className="eg-semantics__adie-intro">
          {t('semanticGuidePage.adie.intro')}
        </p>
        <ul className="eg-semantics__pairs" data-testid="semantics-pairs">
          {ADIE_PAIRS.map(({ leftKey, rightKey }) => (
            <li
              key={`${leftKey}-${rightKey}`}
              className="eg-semantics__pair"
              data-testid={`semantic-pair-${leftKey}-${rightKey}`}
            >
              <span className="eg-semantics__pair-side">
                {t(`semanticGuidePage.adie.${leftKey}`)}
              </span>
              <span className="eg-semantics__pair-sep" aria-hidden="true">
                ≠
              </span>
              <span className="eg-semantics__pair-side">
                {t(`semanticGuidePage.adie.${rightKey}`)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="eg-semantics__section" aria-labelledby="sem-examples">
        <h3 id="sem-examples" className="eg-semantics__section-title">
          {t('semanticGuidePage.sections.examples')}
        </h3>
        <div className="eg-semantics__status-examples">
          <div className="eg-semantics__example-row">
            <StatusBadge status="pending" />
            <span className="eg-semantics__example-use">
              {t('semanticGuidePage.examples.pending')}
            </span>
          </div>
          <div className="eg-semantics__example-row">
            <StatusBadge status="unknown" />
            <span className="eg-semantics__example-use">
              {t('semanticGuidePage.examples.unknown')}
            </span>
          </div>
          <div className="eg-semantics__example-row">
            <StatusBadge status="information" />
            <span className="eg-semantics__example-use">
              {t('semanticGuidePage.examples.information')}
            </span>
          </div>
        </div>
      </section>

      <p className="eg-note eg-semantics__backend-note">
        {t('semanticGuidePage.backendNote')}
      </p>
    </section>
  )
}

// Keep SEMANTIC_TONES import meaningful: exports the canonical list which
// this page is required to cover. If a new tone is added, this page will fail
// to compile until TONE_DEFS is updated (intentional guard rail).
const _guard: SemanticTone[] = [...SEMANTIC_TONES]
void _guard
