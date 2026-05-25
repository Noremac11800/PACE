<script lang="ts">
  import { getContext, onMount } from "svelte";
  import type { LayoutProps } from "./+layout.svelte";

  const data = getContext<LayoutProps>("data");
  const chipNames = ["layout", "input", "navigation", "overlay"];

  onMount(() => {
    data.title = "Sandbox";
  });
</script>

{#snippet chip(name: string)}
  {#if name === chipNames[0]}
    <span class="chip preset-filled-primary-50-950">{name}</span>
  {:else if name === chipNames[1]}
    <span class="chip preset-filled-warning-50-950">{name}</span>
  {:else if name === chipNames[2]}
    <span class="chip preset-filled-tertiary-50-950">{name}</span>
  {:else if name === chipNames[3]}
    <span class="chip preset-filled-success-50-950">{name}</span>
  {/if}
{/snippet}

{#snippet card(
  name: string,
  route: string,
  description: string,
  chipCategories: string[],
)}
  <a
    href="/sandbox/{route}"
    class="flex flex-col gap-2 card card-hover p-4 bg-surface-50-950 shadow-md"
  >
    <h4 class="h4 text-primary-500">{name}</h4>
    <p class="text-sm text-surface-700-300">{description}</p>
    <div class="flex-1"></div>
    <div class="flex flex-wrap gap-2">
      {#each chipCategories as chipCategory}
        {@render chip(chipCategory)}
      {/each}
    </div>
  </a>
{/snippet}

<main class="flex flex-col gap-4 p-8">
  <div class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
    {@render card(
      "Avatar",
      "avatar",
      "Display profile images with customisable shapes and sizes",
      ["navigation"],
    )}
    {@render card(
      "Badges",
      "badges",
      "Small status indicators or labels for displaying information like counts or states",
      ["layout"],
    )}
    {@render card(
      "Bottom Sheet",
      "bottom-sheet",
      "A blocking notification component for displaying content in a modal at the bottom of the screen",
      ["overlay"],
    )}
    {@render card(
      "Button",
      "button",
      "A versatile button component with various styles and sizes",
      ["input"],
    )}
    {@render card(
      "Callout",
      "callout",
      "An attention-grabbing component for highlighting important information",
      ["layout"],
    )}
    {@render card(
      "Carousel",
      "carousel",
      "A rotating slideshow component for displaying multiple items",
      ["layout", "navigation"],
    )}
    {@render card(
      "Combo Box",
      "combo-box",
      "A dropdown input that allows selection from a list or free text entry",
      ["input"],
    )}
    {@render card(
      "Date Picker",
      "date-picker",
      "A calendar interface for selecting dates",
      ["input"],
    )}
    {@render card(
      "Dialog",
      "dialog",
      "Modal windows for displaying content or prompting user interaction",
      ["overlay"],
    )}
    {@render card(
      "i18n",
      "i18n",
      "Demo using svelte-i18n with your existing locale JSON files",
      ["layout"],
    )}
    {@render card("Input", "input", "Input box component for user input", [
      "input",
    ])}
    {@render card(
      "Menu",
      "menu",
      "Navigation or action lists that appear on demand",
      ["navigation"],
    )}
    {@render card(
      "Popover",
      "popover",
      "Floating content containers that appear next to elements",
      ["overlay"],
    )}
    {@render card(
      "Progress Bars",
      "progress-bars",
      "Visual indicators showing the completion status of a task",
      ["input"],
    )}
    {@render card(
      "Slider",
      "slider",
      "Interactive controls for selecting a value from a range",
      ["input"],
    )}
    {@render card(
      "Switch",
      "switch",
      "Toggle controls for on/off or true/false states",
      ["input"],
    )}
    {@render card(
      "Tables",
      "tables",
      "Structured data display with rows and columns for organizing information",
      ["layout"],
    )}
    {@render card(
      "Tabs",
      "tabs",
      "Organized content sections with clickable headers",
      ["navigation"],
    )}
    {@render card(
      "Toast",
      "toast",
      "A non-blocking notification component for displaying messages",
      ["overlay"],
    )}
    {@render card(
      "Tool Tip",
      "tool-tip",
      "Informative text that appears on hover or focus",
      ["overlay"],
    )}
    {@render card(
      "Tree View",
      "tree-view",
      "Hierarchical lists for displaying nested data structures",
      ["layout"],
    )}
  </div>
</main>
