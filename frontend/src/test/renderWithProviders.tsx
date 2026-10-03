/* eslint-disable react-refresh/only-export-components */
import type { ReactElement, ReactNode } from 'react'
import { render, type RenderResult } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { ThemeProvider } from '../theme'
import { ToastProvider } from '../components/toast'
import { createTestRouter } from '../app/router'
import '../i18n'

interface ThemeOnlyProps {
  children: ReactNode
}

function ThemeAndToast({ children }: ThemeOnlyProps): ReactElement {
  return (
    <ThemeProvider>
      <ToastProvider>{children}</ToastProvider>
    </ThemeProvider>
  )
}

/**
 * Render a single component wrapped in ThemeProvider + MemoryRouter + ToastProvider.
 */
export function renderWithProviders(
  ui: ReactElement,
  options: { initialEntries?: string[] } = {},
): RenderResult {
  const router = createMemoryRouter(
    [{ path: '*', element: <>{ui}</> }],
    { initialEntries: options.initialEntries ?? ['/'] },
  )
  return render(
    <ThemeProvider>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </ThemeProvider>,
  )
}

/**
 * Render a bare component wrapped only in ThemeProvider + ToastProvider (no router).
 */
export function renderWithThemeOnly(ui: ReactElement): RenderResult {
  return render(<ThemeAndToast>{ui}</ThemeAndToast>)
}

/**
 * Mount the full app route tree (RootLayout + AppShell + all routes).
 */
export function renderApp(initialEntries: string[] = ['/']): RenderResult {
  const router = createTestRouter(initialEntries)
  return render(
    <ThemeProvider>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </ThemeProvider>,
  )
}
