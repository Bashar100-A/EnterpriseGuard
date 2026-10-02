/* eslint-disable react-refresh/only-export-components */
import type { ReactElement, ReactNode } from 'react'
import { render, type RenderResult } from '@testing-library/react'
import { ThemeProvider } from '../theme'
import '../i18n'

interface ProvidersProps {
  children: ReactNode
}

function AllProviders({ children }: ProvidersProps): ReactElement {
  return <ThemeProvider>{children}</ThemeProvider>
}

/**
 * Render a component wrapped in the same providers used by main.tsx.
 *
 * Use this in tests that mount components relying on useTheme(),
 * useTranslation(), or useDirection(). Calling plain `render()` will
 * throw if the component tree reaches a provider-dependent hook.
 */
export function renderWithProviders(ui: ReactElement): RenderResult {
  return render(<AllProviders>{ui}</AllProviders>)
}
