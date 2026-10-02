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

---

## Phase D Additions

### TypeScript strictness

- `noUncheckedIndexedAccess` makes `Record<string, number>` unsafe to increment.
  Use a typed interface instead:
  ```ts
  // ❌ fails under strict
  const calls: Record<string, number> = { a: 0 }
  calls.a++  // number | undefined

  // ✅ explicit shape
  interface Calls { a: number }
  const calls: Calls = { a: 0 }
  calls.a += 1
ETE"
fi

echo
echo "Report: OUT"echo"Baseline:OUT"echo"Baseline:BASELINE_FILE"

---

## Phase D Additions

### TypeScript strictness

- `noUncheckedIndexedAccess` makes `Record<string, number>` unsafe to increment.
  Use a typed interface instead:
  ```ts
  // fails under strict
  const calls: Record<string, number> = { a: 0 }
  calls.a++  // number | undefined

  // explicit shape
  interface Calls { a: number }
  const calls: Calls = { a: 0 }
  calls.a += 1
  ```

- `exactOptionalPropertyTypes` requires `prop?: T | undefined` for
  properties that may be explicitly passed `undefined`:
  ```ts
  // fails
  interface P { onRetry?: () => void }
  <Comp onRetry={maybeUndefined} />

  // explicit
  interface P { onRetry?: (() => void) | undefined }
  ```

### Test helpers

- Never pass a bare arrow function as a default handler in test helpers.
  If any test asserts `.toHaveBeenCalled*` on it, the assertion fails with
  "not a spy or a call to a spy".
  ```ts
  // bad
  const onClose = handlers.onClose ?? (() => {})

  // good
  const onClose = handlers.onClose ?? vi.fn()
  ```

- When a word can appear in two places (label + state badge),
  use `getAllByText(...)` instead of `getByText(...)` to avoid
  "multiple elements found" failures.

- When two texts are similar but distinct (e.g. "Stale" vs "Chart data is stale"),
  use the full exact string in `getByText(...)` — never `/stale/i` which matches both.

- `getByRole(\"button\", { name: X })` matches both the visible label and
  `aria-label`. If a button has a visible label AND another button has the
  same accessible name via `aria-label`, use a class selector instead:
  ```ts
  const xBtn = document.querySelector(\".eg-danger__close\")
  ```

### i18n key hygiene

- For any component that renders both a short state badge and a
  long placeholder message, keep them in separate key groups:
  ```json
  {
    \"chart\": {
      \"state\": { \"empty\": \"Empty\" },
      \"frame\": { \"empty\": \"No chart data available\" }
    }
  }
  ```
  This prevents DOM text collisions that break `getByText`.

- When adding a state-driven component, always map every value of the
  source union (`DataStateValue`, `ChartState`, etc.) in the locale files.
  Missing keys silently fall back to the key name.

### Removed / deprecated

- `within` from Testing Library should only be imported when actually used —
  ESLint flags unused imports as errors in this project.

### Phase D primitives (for reference)

| File | Purpose |
|---|---|
| `components/security/tone.ts` | `SemanticTone` contract + all mappings |
| `components/security/StatusBadge.tsx` | Categorical status (18 keys to 5 tones) |
| `components/security/SeverityBadge.tsx` | Ordered severity (5 levels to 3 tones) |
| `components/security/StateIndicator.tsx` | Dot + label, compact |
| `components/security/VerificationBadge.tsx` | Evidence proof state |
| `components/security/EnvironmentBadge.tsx` | Deployment environment (no tone) |
| `components/security/EvidenceIndicator.tsx` | Evidence state + optional count |
| `components/security/TechnicalIdentifier.tsx` | Mono, LTR-forced, copyable |
| `components/states/DataState.tsx` | Honest data wrapper (9 states) |
| `components/data-display/MetricCard.tsx` | Full-provenance metric |
| `components/data-display/ChartFrame.tsx` | Chart wrapper (8 states) |
| `components/data-display/EnterpriseTable.tsx` | Generic table primitive |
| `components/command/CommandPalette.tsx` | Ctrl+K palette |
| `components/command/useCommandPalette.ts` | Palette state + shortcut |
| `components/dangerous/DangerousActionDialog.tsx` | Intent to Impact to Authority to Confirm |
