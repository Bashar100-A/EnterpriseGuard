import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// UI-01.B.1 — minimal Vite configuration for React + TypeScript.
// No backend, no API, no telemetry, no business logic.
export default defineConfig({
  plugins: [react()],
})
