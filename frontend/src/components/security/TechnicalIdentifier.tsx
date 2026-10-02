import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from 'react'
import { useTranslation } from 'react-i18next'

export type TruncateMode = 'none' | 'start' | 'middle' | 'end'

export interface TechnicalIdentifierProps {
  /** The full identifier value. Always preserved in full. */
  value: string
  /** Optional prefix rendered outside the truncated value (e.g., "DEC-"). */
  prefix?: string
  /** Optional visible label above/beside the identifier. */
  label?: ReactNode
  /** Allow copying the full value to the clipboard. Default: true. */
  copyable?: boolean
  /** How to truncate the display. Default: 'middle'. */
  truncate?: TruncateMode
  /** Maximum visible characters (excluding prefix). Default: 16. */
  maxLength?: number
  /** Visual size. Default: 'md'. */
  size?: 'sm' | 'md'
  /** Custom tooltip. Defaults to the full value. */
  title?: string
}

/**
 * Truncate a string according to the given mode.
 * The original string is never modified; truncation is display-only.
 */
function truncate(value: string, mode: TruncateMode, max: number): string {
  if (mode === 'none' || value.length <= max) return value
  if (max <= 3) return '…'

  const head = Math.ceil((max - 1) / 2)
  const tail = max - 1 - head

  switch (mode) {
    case 'start':
      return '…' + value.slice(value.length - (max - 1))
    case 'end':
      return value.slice(0, max - 1) + '…'
    case 'middle':
      return value.slice(0, head) + '…' + value.slice(value.length - tail)
    default:
      return value
  }
}

async function writeToClipboard(text: string): Promise<boolean> {
  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
    return false
  } catch {
    return false
  }
}

/**
 * TechnicalIdentifier — displays a monospace, LTR-forced, selectable,
 * optionally copyable identifier (hashes, IDs, manifest keys).
 *
 * Spec §22. Always monospace. Direction is forced to LTR even under RTL.
 * The full value is preserved in the DOM and in the tooltip; only the
 * visual representation is truncated.
 */
export function TechnicalIdentifier({
  value,
  prefix,
  label,
  copyable = true,
  truncate: mode = 'middle',
  maxLength = 16,
  size = 'md',
  title,
}: TechnicalIdentifierProps): ReactElement {
  const { t } = useTranslation('security')
  const [copied, setCopied] = useState(false)
  const [failed, setFailed] = useState(false)
  const timerRef = useRef<number | undefined>(undefined)

  const handleCopy = useCallback(() => {
    void writeToClipboard(value).then((ok) => {
      if (ok) {
        setCopied(true)
        setFailed(false)
      } else {
        setFailed(true)
        setCopied(false)
      }
      if (timerRef.current !== undefined) {
        window.clearTimeout(timerRef.current)
      }
      timerRef.current = window.setTimeout(() => {
        setCopied(false)
        setFailed(false)
      }, 1500)
    })
  }, [value])

  useEffect(() => {
    return () => {
      if (timerRef.current !== undefined) {
        window.clearTimeout(timerRef.current)
      }
    }
  }, [])

  const display = truncate(value, mode, maxLength)
  const tooltip = title ?? value
  const copyLabel = copied
    ? t('identifier.copied')
    : failed
      ? t('identifier.copyFailed')
      : t('identifier.copy')

  return (
    <span
      className={`eg-tech-id eg-tech-id--${size}`}
      data-copied={copied ? 'true' : undefined}
      data-failed={failed ? 'true' : undefined}
    >
      {label !== undefined && <span className="eg-tech-id__label">{label}</span>}
      <span className="eg-tech-id__value eg-mono" title={tooltip} dir="ltr">
        {prefix !== undefined && <span className="eg-tech-id__prefix">{prefix}</span>}
        <span className="eg-tech-id__body">{display}</span>
      </span>
      {copyable && (
        <button
          type="button"
          className="eg-tech-id__copy"
          onClick={handleCopy}
          aria-label={copyLabel}
          title={copyLabel}
        >
          <span aria-hidden="true">{copied ? '✓' : failed ? '×' : '⧉'}</span>
        </button>
      )}
    </span>
  )
}
