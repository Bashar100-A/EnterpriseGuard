import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'

import './i18n'
import { ThemeProvider } from './theme'
import { ToastProvider } from './components/toast'
import { router } from './app/router'
import './app/styles.css'

const rootEl = document.getElementById('root')
if (!rootEl) {
  throw new Error('Root element #root not found in index.html')
}

createRoot(rootEl).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)
