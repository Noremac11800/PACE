---
trigger: always_on
---

## Reactivity and runes
- When working with Svelte components, always use the `$state` and `$derived` macros for reactive state management. Never use plain `let` with the expectation of reactivity. The `$state` rune manages state like a signal with a clear API, replacing Svelte's old `let` variable assignment model.
- Use `$derived` for computed values, not `$effect` with a manual variable update. `$derived` makes dependencies explicit and enables better type inference.
- Prefer `$derived.by(() => ...)` for complex multi-line derived logic over cramming it into a single expression.
- Avoid `$effect` for state derivation — it's for side effects only (DOM manipulation, logging, external subscriptions). Misusing it for derived state leads to update cycles.
- Do not read and write the same `$state` inside a single `$effect` — this creates infinite reactive loops.
- Clean up side effects — `$effect` returns a cleanup function; always return teardown logic for subscriptions, timers, and event listeners.
- Prioritize using Svelte's built-in reactivity system over external state management libraries.
- Prioritize creating a <component>.svelte.ts file for any logic that is too complex for the component. The file should be placed in the same directory as the component. The file should contain a props interface for the component and any complex logic.
- When importing *.svelte.ts files, always include the .ts extension in the import statement.
- Use `$state.raw` for large objects where you want to opt out of deep reactivity for performance reasons — e.g. large read-only data sets.
- Avoid deeply nested `$state` objects unless you need deep reactivity. Flatten state where possible.

## Props and component interface
- Always use `$props()` to declare component props — never export `let` (Svelte 4 legacy pattern).
- Provide default values inline in the destructure, not separately.
- Use TypeScript types directly in the `$props()` destructure for full type safety.
- Use `$bindable()` explicitly when a prop is intended to support two-way binding via `bind:`. Don't make all props bindable by default.
- Never mutate props directly unless they are `$bindable`. Treat all other props as read-only.
- Use rest props (`...rest`) sparingly and document which attributes are being spread.

## Component structure
- One component per file, named in PascalCase (e.g. UserCard.svelte).
- Keep components small and focused — if a component exceeds ~150 lines it likely needs to be split.
- Extract reusable logic into .svelte.ts rune modules (not plain .ts files) when the logic uses runes — runes only work in .svelte or .svelte.ts files.
- Use <script lang="ts"> always — avoid plain JS components in a TypeScript project.
- Order the <script> block content consistently: imports → props → state → derived → effects → functions → exports.
- Keep the template logic minimal — complex conditionals or transforms belong in $derived or helper functions, not inline in the markup.

## Snippets and slots
- Prefer {#snippet} over slots for reusable template fragments within a file or passed as props. Snippets are more composable and type-safe.
- Use `{@render snippet()}` explicitly — don't rely on default slot fallback behaviour when a snippet is expected.
- Type your snippets using the `Snippet` type from `svelte`:
```ts
import type { Snippet } from 'svelte';
let { header }: { header: Snippet<[string]> } = $props();
```
- Avoid overusing slots for things that could just be props — pass simple values as props, use snippets for template content.

## Events
- Use callback props instead of createEventDispatcher — Svelte 5 deprecates the event dispatcher in favour of passing functions as props:
```ts
let { onCustomEvent }: { onCustomEvent: (payload: string) => void } = $props();
```
- Emit events with `onCustomEvent('payload')` directly — no need for `dispatch('custom-event', payload)`.
- Use native DOM event attributes (e.g. onclick, oninput) on DOM elements directly — Svelte 5 passes these through natively.
- Avoid on: directive syntax — it's legacy. Use the attribute-style event handlers instead.

## State management (App-level)
- Prefer rune-based state modules over Svelte stores for new code. A .svelte.ts file with exported $state variables is cleaner and doesn't require .subscribe() boilerplate.
- Use Svelte stores (writable, readable) only when interoperating with legacy code or third-party libraries that expect them.
- Co-locate state with the component that owns it — lift state up only when genuinely needed by multiple components.
- Avoid global state sprawl — centralise shared state in a dedicated state/ or stores/ directory with clear ownership.

## Typescript
- Explicitly type all props, state, and function signatures — don't rely on inference for public component interfaces.
- Use `ComponentProps<typeof MyComponent>` to extract prop types when building wrapper components.
- Avoid `any` — use `unknown` and narrow it, or define proper types.
- Use `satisfies` where you want to validate a value against a type without widening it.

## Performance
- Avoid creating new objects/arrays inside $derived on every tick unless necessary — this breaks referential equality and causes unnecessary downstream updates.
- Use {#key expr} to force re-mounting a component when its identity fundamentally changes (e.g. switching between different user profiles).
- Prefer {#each items as item (item.id)} — always provide a key to {#each} blocks to enable efficient DOM reconciliation.
- Lazy-load heavy components using dynamic imports where they aren't needed on initial render.
- Avoid reactive reads inside tight loops in derived or effect contexts — pull values out first.

## Styling
- Use scoped component styles by default — put styles in the component's <style> block, not global CSS, unless it truly needs to be global.
- Use :global() sparingly and only for third-party component overrides or truly global resets.
- Prefer Tailwind utility classes over component <style> blocks for layout and spacing — reserve <style> for complex or dynamic styles that Tailwind can't express cleanly.
- Avoid inline style="" attributes for anything beyond truly dynamic values (e.g. calculated widths).
- Use CSS custom properties to bridge Svelte component theming with a design system.

## File and project organisation
```
src/
  lib/
    components/     # Shared UI components (PascalCase.svelte)
    state/          # App-level rune state modules (.svelte.ts)
    utils/          # Pure functions, no runes (.ts)
    types/          # Shared TypeScript types (.ts)
  routes/           # (or pages/) — top-level page components
```
- Never import from ../../../ more than 2 levels deep — use $lib/ path alias instead.
- Keep utility functions in plain .ts files (no runes needed) for portability and testability.
- Keep rune-dependent logic in .svelte.ts files — the compiler needs to know to process them.
