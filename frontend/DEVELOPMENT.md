# UI-01 Development Guide

Golden rules learned during Phases B and C.

## Files
- JSX in file -> use .tsx. No JSX -> .ts.
- Component test files -> .test.tsx.

## Imports (relative)
Walk up from the file directory to src/, then append the target.
- From src/components/nav/X.test.tsx to src/i18n: ../../i18n
- From src/app/Y.tsx to src/theme: ../theme

## Test Helpers (src/test/renderWithProviders.tsx)
- renderWithProviders(<Comp />) - mounts Comp inside MemoryRouter + ThemeProvider.
- renderWithThemeOnly(<Comp />) - ThemeProvider only, no router.
- renderApp(["/path"]) - full app tree (RootLayout + routes).
- Never use rerender with these; split into separate tests.

## Vitest 2 Notes
- Use vi.fn<(x: T) => R>() (v2 syntax).
- Always import describe/it/expect from "vitest".
- RTL auto-cleanup is NOT enabled: add afterEach(cleanup) in every test.

## Adding a Namespace to i18n
1. Create src/i18n/locales/en/<ns>.json and ar/<ns>.json.
2. Import both in src/i18n/index.ts.
3. Add to NAMESPACES array and both resource objects.

## Adding a Route
1. Add a spec to ROUTE_SPECS in src/app/router.tsx.
2. Add a nav item to ITEMS in src/components/navigation/NavigationRail.tsx.
3. Ensure navigation.items.<key> exists in both locale files.

## RTL / LTR
- Use logical properties: margin-inline, padding-inline, border-inline-*, inset-inline-*.
- Avoid margin-left/right, padding-left/right, left/right.
- .eg-mono class forces direction: ltr for hashes and technical IDs.

## Semantic Colors
Use CSS variables from src/app/styles.css, never raw hex:
- --eg-trust-emerald: verified / healthy / integrity
- --eg-signal-blue: information / pending / neutral
- --eg-warning-amber: review / degraded / stale
- --eg-critical-red: confirmed critical / failure
- --eg-unknown-gray: unknown / unavailable / not evaluated

Unknown never becomes Healthy silently.

## No Fake Data
- Default to Unknown / Not Connected when no backend data exists.
- Fixtures must be named designFixtures, never realData.
- No fake KPIs, no fake telemetry, no Live labels without a real source.

## Before Commit
- npm run typecheck
- npm run lint
- npm run test
- npm run build
- npm run coverage (informational)
