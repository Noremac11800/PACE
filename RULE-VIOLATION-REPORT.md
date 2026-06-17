# Rule Violation Fix Plan

Steps are ordered from smallest/safest to largest/most impactful. Complete each step and check it off before moving to the next.

---

## Phase 1 — Trivial One-Liners (no logic changes)

- [x] **1.1** `Toasts.svelte:1` — Add `lang="ts"` to `<script module>` → `<script module lang="ts">`
- [x] **1.2** `UpdatesPanel.svelte:251-255` — Replace raw `<svg>` GitHub mark with `<Github size={16} />` from `@lucide/svelte`
- [x] **1.3** `DependenciesPanel.svelte:2` — Change `import DepChecks from "./DepChecks.svelte"` → `import DepChecks from "$lib/panels/DepChecks.svelte"`
- [x] **1.4** `ConfigSelector.svelte:191` — Replace `style="right: 1rem; top: 4.5rem;"` with Tailwind classes `right-4 top-[4.5rem]`
- [x] **1.5** `AnimatedBackground.svelte:95-103` — Add `shadow-[0_0_10px_currentColor]` Tailwind class to node `<div>` and remove the static `box-shadow` from the inline `style`

---

## Phase 2 — Import Consistency (mechanical find-and-replace)

- [x] **2.1** `BuildTab.svelte:16` — Change `from "./command-status.svelte"` → `from "$lib/orchestrator/command-status.svelte"`
- [x] **2.2** `PublishingConfig.svelte:38-39` — Change `from "./publishing.svelte"` → `from "$lib/orchestrator/publishing.svelte"` and `from "./command-status.svelte"` → `from "$lib/orchestrator/command-status.svelte"`
- [x] **2.3** `CodesigningConfig.svelte` — N/A: file has no `./` sibling imports
- [x] **2.4** `UploadConfig.svelte:35` — Change `from "./command-status.svelte"` → `from "$lib/orchestrator/command-status.svelte"`

---

## Phase 3 — `{#each}` Keys (add keys across all files)

- [x] **3.1** `AboutPanel.svelte:161` — `{#each stats as stat}` → `{#each stats as stat (stat.label)}`
- [x] **3.2** `AboutPanel.svelte:197` — `{#each techStack as tech, index}` → `{#each techStack as tech (tech.name)}`
- [x] **3.3** `AboutPanel.svelte:245` — `{#each tech.features as feature}` → `{#each tech.features as feature (feature)}`
- [x] **3.4** `AboutPanel.svelte:290` — `{#each features as feature}` → `{#each features as feature (feature.title)}`
- [x] **3.5** `SettingsPanel.svelte:290` — `{#each toc as entry}` → `{#each toc as entry (entry.id)}`
- [x] **3.6** `LanguageSwitcher.svelte:104` — `{#each supportedLocales as code}` → `{#each supportedLocales as code (code)}`
- [x] **3.7** `SettingsSnippets.svelte:205` — `{#each options as option}` (SettingSelect) → `{#each options as option (option.value)}`
- [x] **3.8** `SettingsSnippets.svelte:229` — `{#each options as option}` (SettingRadioGroup) → `{#each options as option (option.value)}`
- [x] **3.9** `AnimatedBackground.svelte:71,72,92` — Add index-based keys to all three `{#each nodes ...}` loops, e.g. `{#each nodes as node, i (i)}`
- [x] **3.10** `ProjectGraphPanel.svelte:231` — `{#each groupLegend as entry}` → `{#each groupLegend as entry (entry.label)}`
- [x] **3.11** `DeployTab.svelte:35` — `{#each Object.entries(sections) as [sectionId, ...]}` → add `(sectionId)` as key

---

## Phase 4 — Tailwind Color Syntax (replace `dark:` variants) + Lucide deprecated icons

- [x] **4.1** `AboutPanel.svelte:201` — Replace `from-surface-50 to-surface-100 dark:from-surface-950 dark:to-surface-900` → `from-surface-50-950 to-surface-100-900`
- [x] **4.2** `AboutPanel.svelte:247` — Replace `from-surface-100 to-surface-200 dark:from-surface-800 dark:to-surface-700` → `from-surface-100-900 to-surface-200-800`
- [x] **4.3** Replace all deprecated Lucide icons with their non-deprecated equivalents in all files that use Lucide icons

---

## Phase 5 — TypeScript Strictness

- [x] **5.1** `ConsolePanel.svelte:23` — Replace `let currentProcess: any = null` with the proper typed union from `@tauri-apps/plugin-shell` (e.g. `Child | null`)
- [x] **5.2** `DepChecks.svelte:93,155` — Replace `error as string` casts with `String(error)` or `error instanceof Error ? error.message : String(error)`
- [x] **5.3** Remove all unused imports and variables in all files

---

## Phase 6 — `$effect` Misuse: State Derivation → `$derived`

- [ ] **6.1** `ThemeSwitch.svelte:11-13` — Replace `$effect(() => { checked = $theme === "dark"; })` with `let checked = $derived($theme === "dark")`
- [ ] **6.2** `ProjectsTab.svelte:21-26` — Replace `$effect(() => { if (config) { expandedGroups = new Set(); } })` with a `$derived` or a reset triggered by a key change
- [ ] **6.3** `OrchestratorPanel.svelte:80-84` — Replace the `$effect` that reads and writes `activeTab` with a `$derived` for `activeTab` that clamps to `"projects"` when `isDefaultConfig` is true

---

## Phase 7 — `$effect` Missing Cleanup / Teardown

- [ ] **7.1** `+layout.svelte:37-39` — Add `return () => { html.removeAttribute('lang'); html.removeAttribute('dir'); }` cleanup to the locale `$effect`
- [ ] **7.2** `SettingsPanel.svelte:49-94` — Add `return () => { if (saveTimeout) clearTimeout(saveTimeout); }` at the end of the settings `$effect`
- [ ] **7.3** `BuildTab.svelte:51-68` — Add a cleanup return to the settings-save `$effect` (cancel any pending async work if needed)

---

## Phase 8 — `$effect` Refactor: Dependency Tracking

- [ ] **8.1** `SettingsPanel.svelte:49-94` — Extract the dependency tracking reads into a `$derived` snapshot object, then use a single `$effect(() => { snapshot; saveSettings(); })` on that derived value instead of the current verbose per-field reads

---

## Phase 9 — `export function` & Props Mutation (Svelte 4 patterns)

- [ ] **9.1** `Callout.svelte:32-35` — Remove `export function toggle()`. Replace with a callback prop `ontoggle?: () => void` in `$props()`, or expose toggle state via `$bindable` only and let the parent control it
- [ ] **9.2** `ProjectCard.svelte:25-46` — Either declare `project` as `$bindable()` in props, or emit mutation events via callback props (`onUpdate: (patch: Partial<PaceProject>) => void`) instead of mutating the prop object directly

---

## Phase 10 — Svelte Store → Rune Module

- [ ] **10.1** `network-status.ts` — Convert from `readable` store to a `.svelte.ts` module using `$state` and `$effect` for the `online`/`offline` event listeners. Update all consumers to drop the `$` store auto-subscribe syntax
- [ ] **10.2** `theme.ts` — Confirm it is a Svelte store, then convert to a `.svelte.ts` rune module. Update `ThemeSwitch.svelte` and `Sidebar.svelte` to use the rune directly (no `$` sigil)

---

## Phase 11 — Skeleton UI: Replace Custom Implementations

- [ ] **11.1** `SettingsSnippets.svelte:36-52` — Replace the hand-rolled `SettingSwitch` toggle button with Skeleton's `<Switch>` component
- [ ] **11.2** `SettingsSnippets.svelte:199-210` — Replace the raw `<select>` in `SettingSelect` with Skeleton's `Select` component

---

## Phase 12 — Script Block Order

- [ ] **12.1** `AboutPanel.svelte:25` — Move the top-level `fetchAppVersion()` call into `onMount`
- [ ] **12.2** `HelpPanel.svelte:29` — Move the top-level `fetchAppVersion()` call into `onMount`

---

## Phase 13 — Complex Template Logic Extraction

- [ ] **13.1** `AboutPanel.svelte:206-217` — Extract the nested ternary gradient-colour class logic into a `$derived` map or helper function, then use it in the template
- [ ] **13.2** `DirectoryBuildPropsPanel.svelte:289-305` — Extract `saveResult.startsWith('Error')` and the load-result error checks into named `$derived` booleans (e.g. `let saveIsError = $derived(...)`)

---

## Phase 14 — Remaining Inline Styles → Tailwind

- [ ] **14.1** `AboutPanel.svelte:134` — Replace `style="background-image: radial-gradient(...)"` with a Tailwind arbitrary value or CSS custom property in `app.css`
- [ ] **14.2** `HelpPanel.svelte:90` — Replace `style="grid-template-columns: 1fr {tocOpen ? '260px' : '48px'};"` with a CSS custom property driven by a reactive variable and a Tailwind arbitrary class
- [ ] **14.3** `SettingsPanel.svelte:131` — Same pattern as 14.2: replace dynamic `grid-template-columns` inline style with a CSS custom property

---

## Phase 15 — Large Component Splits (structural refactors)

- [ ] **15.1** `DepChecks.svelte` (463 lines) — Extract individual dependency check rows into a `DepCheckRow.svelte` sub-component
- [ ] **15.2** `ConsolePanel.svelte` (460 lines) — Extract input/history area and output area into sub-components
- [ ] **15.3** `DirectoryBuildPropsPanel.svelte` (511 lines) — Extract the "add property" form and the property list into sub-components
- [ ] **15.4** `AboutPanel.svelte` (372 lines) — Extract tech stack cards and feature grid into sub-components
- [ ] **15.5** `ConfigSelector.svelte` (354 lines) — Extract the "create new config" form into a sub-component
- [ ] **15.6** `SettingsPanel.svelte` (315 lines) — Extract each settings section (`GeneralSection`, `AppearanceSection`, `StorageSection`) into sub-components
- [ ] **15.7** `GitTab.svelte` (388 lines) — Extract group rows and clone/pull action panels into sub-components
- [ ] **15.8** `NugetTab.svelte` (663 lines) — Extract sources list, cache panels, and local source panels into sub-components
- [ ] **15.9** `CodesigningConfig.svelte` (735 lines) — Extract iOS/Windows/Android tab content into separate sub-components
- [ ] **15.10** `BuildTab.svelte` (793 lines) — Extract build options form and output panel into sub-components
- [ ] **15.11** `UploadConfig.svelte` (857 lines) — Extract platform upload cards and output panel into sub-components
- [ ] **15.12** `PublishingConfig.svelte` (1114 lines) — Extract per-platform publishing forms and output panel into sub-components

---

## Phase 16 — File Organisation

> ⚠️ High-impact refactor — do last as it requires updating every import across the codebase.

- [ ] **16.1** Create `src/lib/state/` and move rune-based state modules into it: `app-version.svelte.ts`, `config-store.svelte.ts`, `git-status.svelte.ts`, `pace-status.svelte.ts`, `settings.svelte.ts`, `update-status.svelte.ts`
- [ ] **16.2** Create `src/lib/utils/` and move utility files into it: `dependency_utils.ts`, `app-init.ts`, `i18n.ts`, `toaster.ts`
- [ ] **16.3** Create `src/lib/types/` and move type-only files into it: `pace-config.ts`
- [ ] **16.4** Update all import paths across the codebase after the moves above