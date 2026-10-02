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

---

## Phase E + F Additions

### SCRIPT pattern — auto-detect HEAD

Beginning with E.1, every phase script auto-detects the current HEAD
and verifies the context (last commit subject) instead of using a
hardcoded REF_HEAD hash:

```bash
BEFORE_HEAD=$(git rev-parse HEAD)
LAST_SUBJECT=$(git log -1 --pretty=%s)
if ! echo "$LAST_SUBJECT" | grep -q "Expected context"; then
  echo "FAIL: wrong starting commit"; exit 1
fi
```

This avoids the recurring "REF_HEAD stale after previous commit" failure.

### Exit-code capture — the pipe trap

NEVER do this:
```bash
# bad — $? is the exit of tail (always 0)
npm run typecheck 2>&1 | tail -n 10 || true
TC=$?
```

ALWAYS do this:
```bash
# good
run_check() {
  local log="/tmp/check.log"
  if "$@" > "$log" 2>&1; then
    return 0
  else
    local ec=$?
    tail -n 20 "$log"
    return $ec
  fi
}
run_check "typecheck" npm run --silent typecheck || TC_OK=1
```

### i18n label collisions

Any label that appears in BOTH a metric card and a table caption
(e.g. "Active Policies", "Pending Approvals") will fail `getByText`.
Use `getAllByText(...).length > 0` in tests:

```ts
// bad
expect(screen.getByText("Active Policies")).toBeTruthy()

// good
expect(screen.getAllByText("Active Policies").length).toBeGreaterThan(0)
```

When it is ambiguous whether a label appears once or many times,
prefer `getAllByText` — it never fails for the wrong reason.

### Unused imports break build, not tests

Vitest does not check imports. `tsc` and ESLint do. If a component
compiles at runtime but the build fails, check for unused imports
and unused `const` declarations first.

Rule: always run `npm run typecheck` before commit, even when
`npm run test` is green.

### Page pattern (Phase E)

Every real page follows the same skeleton:

1. `src/features/<name>/<Name>Page.tsx` — the page component
2. `src/features/<name>/index.ts` — barrel export
3. `src/features/<name>/<Name>Page.test.tsx` — 15-25 tests
4. `src/i18n/locales/{en,ar}/<name>.json` — bilingual strings
5. Register namespace in `src/i18n/index.ts`
6. Add route in `src/app/router.tsx` via the ternary chain
7. Append CSS in `src/app/styles.css`

Pages always use `WorkspaceHeader` + `ContextStrip` at the top, and
end with a `.eg-note` when the backend is not connected.

### No fake data — the rule is absolute

Every page in UI-01 has `backendConnected = false`. Metrics render as
—, charts render empty, tables render empty, badges say "Unknown",
and state indicators say "Not Connected". This is not a placeholder
pattern — it is the honest state. The same pages will show real data
without code changes when the backend arrives.

### Full page inventory (Phase E + F)

| Path | Feature | Notes |
|---|---|---|
| `/` | Overview | Situation Room with doctrine strip |
| `/evidence` | Evidence | EvidenceIndicator + TechnicalIdentifier |
| `/decisions` | Decision Intelligence | DecisionChain (3 tiers, 8 stages) |
| `/governance` | Governance | DangerousActionDialog integration |
| `/health` | System Health | MetricCards + ChartFrames + Services table |
| `/sibb` | SIBB Trust Core | TrustChainVisual (Merkle) |
| `/provenance` | Provenance | Legend + EvidenceIndicator per row |

### Components added in Phase E+F

| File | Purpose |
|---|---|
| `components/security/DecisionChain.tsx` | 3-tier ADIE pipeline visualization |
| `components/security/TrustChainVisual.tsx` | Cinematic Merkle chain |

### Golden rule — router.tsx ternary chain

The route builder uses a single ternary chain. When adding a page:

```tsx
const element =
  spec.path === "/" ? <OverviewPage />
  : spec.path === "/evidence" ? <EvidencePage />
  : spec.path === "/new" ? <NewPage />       // add here
  : <PageShell titleKey={spec.titleKey} groupKey={spec.groupKey} />
```

Never replace with a switch or a map — the ternary form is greppable
and unambiguous.
