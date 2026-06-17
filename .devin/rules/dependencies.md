---
trigger: always_on
---

## Lucide
- Always prioritize the use of Lucide Svelte icons for glyphs and other icons. Never generate or use a raw SVG element unless Lucide is missing that icon.
- Never use deprecated Lucide icons

## Tailwindcss
- Always prioritise the use of Tailwindcss classes over setting the `style` attribute on HTML elements or creating a `<style>` block unless it is absolutely necessary
- Prioritise the `{class}-{color}-{light}-{dark}/{opacity}` syntax for color and opacity classes as opposed to the `{class}-color-{light} dark:{class}-color-{dark}` approach

## Svelte Skeleton UI V4.x
- Always prioritize the use of Svelte Skeleton UI components over custom implementations unless there is a specific reason to do otherwise
- Research can be conducted on the current official Svelte Skeleton UI documentation to ensure compatibility and proper usage from this link https://www.skeleton.dev/docs/svelte/get-started/introduction
