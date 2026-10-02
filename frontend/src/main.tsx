import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './i18n'
import { ThemeProvider } from './theme'
import App from './app/App'
import './app/styles.css'

const rootEl = document.getElementById('root')
if (!rootEl) {
  throw new Error('Root element #root not found in index.html')
}

createRoot(rootEl).render(
  <StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </StrictMode>,
)
