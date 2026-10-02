/* eslint-disable react-refresh/only-export-components */
import type { ReactElement, ReactNode } from 'react'
import { render, type RenderResult } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { ThemeProvider } from '../theme'
import { createTestRouter } from '../app/router'
import '../i18n'

interface ThemeOnlyProps {
  children: ReactNode
}

function ThemeOnly({ children }: ThemeOnlyProps): ReactElement {
  return <ThemeProvider>{children}</ThemeProvider>
}

/**
 * Render a single component wrapped in ThemeProvider + MemoryRouter.
 *
 * The MemoryRouter provides router context (useNavigate, useLocation)
 * without rendering the app's route tree. Use this for component tests
 * that need router context but should mount only the component under test.
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
      <RouterProvider router={router} />
    </ThemeProvider>,
  )
}

/**
 * Render a bare component wrapped only in ThemeProvider (no router).
 * Use this for components that do not require router context.
 */
export function renderWithThemeOnly(ui: ReactElement): RenderResult {
  return render(<ThemeOnly>{ui}</ThemeOnly>)
}

/**
 * Mount the full app route tree (RootLayout + AppShell + all routes).
 * Use this for router-level and integration tests.
 */
export function renderApp(initialEntries: string[] = ['/']): RenderResult {
  const router = createTestRouter(initialEntries)
  return render(
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>,
  )
}
