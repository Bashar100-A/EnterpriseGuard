/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        trust: 'var(--eg-trust-emerald)',
        signal: 'var(--eg-signal-blue)',
        warning: 'var(--eg-warning-amber)',
        critical: 'var(--eg-critical-red)',
        unknown: 'var(--eg-unknown-gray)',
        'bg-app': 'var(--eg-bg)',
        'fg-app': 'var(--eg-fg)',
        'border-app': 'var(--eg-border)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
