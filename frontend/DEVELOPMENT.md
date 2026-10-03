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

---

## Phase G Additions

### The 19-page invariant

As of Phase G, ALL 19 routes under `ROUTE_SPECS` in `src/app/router.tsx`
have real page components. `PageShell` remains only as the fallback for
routes added in later phases.

Full inventory:

| Path | Feature directory |
|---|---|
| `/` | `features/overview` |
| `/operations` | `features/operations` |
| `/intelligence` | `features/threat` |
| `/decisions` | `features/decisions` |
| `/evidence` | `features/evidence` |
| `/provenance` | `features/provenance` |
| `/sibb` | `features/sibb` |
| `/policies` | `features/policies` |
| `/governance` | `features/governance` |
| `/approvals` | `features/approvals` |
| `/manifests` | `features/manifests` |
| `/health` | `features/health` |
| `/inspection` | `features/inspection` |
| `/maintenance` | `features/maintenance` |
| `/analytics` | `features/analytics` |
| `/reports` | `features/reports` |
| `/audit` | `features/audit` |
| `/access` | `features/access` |
| `/settings` | `features/config` |

### The 7-step page pattern (canonical)

Every Phase G page follows this exact order:

1. `src/i18n/locales/en/<name>.json`
2. `src/i18n/locales/ar/<name>.json`
3. Patch `src/i18n/index.ts` — add imports, NAMESPACES entry, and resources
4. Create `src/features/<name>/<Name>Page.tsx`
5. Create `src/features/<name>/index.ts` (barrel export)
6. Patch `src/app/router.tsx` — add one ternary branch
7. Create `src/features/<name>/<Name>Page.test.tsx`
8. Append CSS to `src/app/styles.css`

(Steps 6 and 7 can be swapped; step 8 is always last.)

### Idempotent i18n patching

The single-shot conditional `if "enAccess" not in s:` fails on partial
prior application. Use per-line checks instead:

```python
if "import enConfig from" not in s:
    s = s.replace(...)
if "\x27config\x27," not in s:
    s = s.replace(...)
if "config: enConfig," not in s:
    s = s.replace(...)
```

Each line is independently checkable and idempotent. Rerun safely.

### i18n label collision — always use getAllByText for shared labels

In Phase G we saw the same collision repeat several times. Any label that
appears in BOTH a MetricCard and a Table caption must use `getAllByText`:

```ts
// Bad — fails when label appears twice
expect(screen.getByText("Roles")).toBeTruthy()

// Good — always safe
expect(screen.getAllByText("Roles").length).toBeGreaterThan(0)
```

Rule: when in doubt, use getAllByText for any label that could appear
in more than one place. The list of known collisions includes:
- "Roles", "Active Policies", "Pending Approvals"
- "Settings", "Feature Flags", "Verified", "Unknown"

### Three-part page structure

Every Phase G page follows the same structural rhythm:

1. **Metrics row** — 4 MetricCards in a responsive grid
2. **Optional feature block** — chips, panels, or charts depending on the
   page (scopes, capability chips, dimensions, filters, matrix note)
3. **Tables** — one or two EnterpriseTables
4. **Backend note** — a `.eg-note` paragraph explaining the honest state

Not every page needs step 2. Overview, Evidence, and Health skip it.

### The disabled-action pattern

When a page offers an action that the backend does not yet support,
the button is rendered disabled with a descriptive title:

```tsx
<button disabled title={t("run.unavailable")} data-testid="...run">
  {t("run.label")}
</button>
```

Examples: Inspection (Run Inspection), Audit (Apply / Clear filters).
The UI never pretends a disabled action has fired.

### Backend note wording — non-negotiable

Each page ends with `.eg-note` that describes, in one sentence, what the
backend must eventually provide. The pattern is:

> "Backend integration comes in a later phase. [what is not fabricated].
>  [what the UI does not do]."

Examples:
- Policies: "No policies are fabricated. This page reflects the honest current state."
- Manifests: "A manifest is a plan — only the backend can execute it."
- Access: "Accounts, roles, and permissions are managed by the backend identity service."
- Config: "The UI never writes configuration."
- Audit: "The UI never writes to the audit trail."

This is a design contract, not decoration. It documents the boundary.

### Total inventory at end of Phase G

| Category | Count |
|---|---|
| Real pages | 19 |
| Primitives (security) | 9 |
| Primitives (data-display) | 3 |
| Primitives (states) | 1 |
| Layout components | 5 |
| Overlay components | 2 |
| Hooks | 5 |
| i18n namespaces | 27 (en + ar each) |

### Quality bars (all met at Phase G close)

- `npm run typecheck` — clean
- `npm run lint` — 0 warnings
- `npm run test` — 708 tests passing across 47 files
- `npm run build` — clean
- All pages render in EN + AR, LTR + RTL, dark + light
- Zero fabricated data anywhere in the UI

---

## Phase H Additions

### Interaction layer — what Phase H adds

Phase H turns the interface from a collection of pages into an
interactive application. The five interaction primitives:

| Component | Purpose |
|---|---|
| Command Palette (Ctrl+K) | Fuzzy-searchable command surface |
| Global Shortcuts | ? / Ctrl+/ / Ctrl+B / Ctrl+Shift+A / Ctrl+J |
| Toast System | Unified notifications via `useToast()` |
| Drawer | Contextual side panel with focus trap |
| URL State | Shareable filter state via query string |

### Command Palette — real commands

The palette never invents commands. `useCommands()` assembles them from:
  1. The 19 routes (with translated labels)
  2. The 2 supported languages
  3. The 3 theme modes
  4. Optional UI toggles (rail, assurance panel)

Navigation commands carry three keyword sources:
- the route path (`/evidence`)
- the route key (`evidence`)
- the translated page description (from `usePageDescriptions`)

This is what lets Fuse.js match content-level queries like
"observation execution" → "Go to Decision Intelligence".

### Fuse.js configuration (canonical)

```ts
const FUSE_OPTIONS = {
  keys: [
    { name: "label", weight: 0.7 },
    { name: "keywords", weight: 0.3 },
  ],
  threshold: 0.4,
  ignoreLocation: true,
  minMatchCharLength: 2,
}
```

Threshold 0.4 is tuned to allow typos ("evidance" → "evidence")
without being so loose that unrelated terms match.

### Keyboard shortcuts — the input-suppression rule

Bare-key shortcuts (`?`) must NOT fire when the user is typing in
an `<input>`, `<textarea>`, `<select>`, or `contenteditable` element.
Modifier shortcuts (Ctrl+B, Ctrl+J) always fire.

The check lives in `useKeyboardShortcuts`:

```ts
const hasModifier = e.ctrlKey || e.metaKey || e.altKey
if (!hasModifier && isInInput(e.target)) continue
```

### Testing event.target — dispatch from the target

When a hook depends on `event.target`, the test must dispatch from
the target element, not from `window`:

```ts
// Bad — e.target === window even though input has focus
window.dispatchEvent(new KeyboardEvent("keydown", { key: "?" }))

// Good — e.target === input, bubbles:true reaches window listener
input.dispatchEvent(new KeyboardEvent("keydown", { key: "?", bubbles: true }))
```

Focus alone does not change the event target. This bit us in H.2.

### Fake timers and waitFor do not mix

When `vi.useFakeTimers()` is active, `waitFor()` will hang because
it internally polls using the same timers. Use direct assertions
after `act(() => vi.advanceTimersByTime(n))`:

```ts
// Bad — times out
act(() => vi.advanceTimersByTime(1000))
await waitFor(() => expect(screen.queryByText("x")).toBeNull())

// Good
act(() => vi.advanceTimersByTime(1000))
expect(screen.queryByText("x")).toBeNull()
```

### Toast — API and defaults

```tsx
const toast = useToast()
toast.info("Message")
toast.success("Saved", { description: "Policy POL-042" })
toast.warning("Stale", { action: { label: "Refresh", onClick: refresh } })
toast.error("Failed", { duration: 0 })  // 0 = never auto-dismiss
```

Default durations:
- info, success — 4000 ms
- warning — 6000 ms
- error — 8000 ms

The toast viewport has `role="region"` + `aria-live="polite"`;
individual warning/error toasts use `role="alert"`. Never remove this —
it is the accessibility contract for live notifications.

### Drawer — focus discipline

The drawer:
- remembers the previously-focused element and restores it on close
- traps Tab/Shift+Tab inside the panel
- uses logical sides (`start` / `end`) so it mirrors automatically in RTL

Use `useDrawer<T>()` for typed payloads instead of managing open + payload
separately.

### URL state — the encoding pitfall

`URLSearchParams.set("k", "a,b")` encodes the comma as `%2C`:
`?k=a%2Cb`. This is standards-compliant and harmless in production —
`URLSearchParams.get()` decodes automatically — but it surprises tests
that read `location.search` directly.

In tests, decode before comparing:

```ts
function useSearch(): string {
  return decodeURIComponent(useLocation().search)
}
```

Never re-implement URL encoding manually — that path leads to bugs.

### URL state — behaviour contract

`useUrlState(key, defaultValue)`: a single value.
`useUrlListState(key, defaultValue?)`: a comma-separated list.

Both:
- remove the key entirely when the value equals the default
- preserve all unrelated query parameters
- use `replace: true` by default (no history pollution)
- must be used inside a Router

Example URLs after typical filter use:
  /evidence                                  (no filter)
  /evidence?state=verified                   (one filter)
  /evidence?state=verified&severity=high     (two filters)
  /evidence?severity=high                    (removed state)

The list form accepts both `?k=a,b` and `?k=a&k=b` on read.

### Total inventory at end of Phase H

| Category | Count |
|---|---|
| Real pages | 19 |
| Security primitives | 9 |
| Data-display primitives | 3 |
| State primitives | 1 |
| Layout components | 5 |
| Overlays (command, shortcuts, dangerous, drawer) | 4 |
| Notification components | 1 (ToastProvider) |
| Hooks (custom) | 9 |
| i18n namespaces | 29 (en + ar each) |

Hooks at Phase H close:
- useDirection
- useRailExpanded
- useAssuranceOpen
- useCommandPalette
- useCommands
- usePageDescriptions
- useKeyboardShortcuts
- useGlobalShortcuts
- useUrlState, useUrlListState
- useToast
- useDrawer

### Quality bars (all met at Phase H close)

- `npm run typecheck` — clean
- `npm run lint` — 0 warnings
- `npm run test` — 818 tests passing across 56 files
- `npm run build` — clean
- All interactions work in EN + AR, LTR + RTL, dark + light
- Zero fabricated data anywhere in the UI
