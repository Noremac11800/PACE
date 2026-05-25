<script lang="ts">
  import {
    Info,
    Lightbulb,
    MessageSquareWarning,
    MessageSquareX,
    TriangleAlert,
    ChevronUp,
    ChevronDown,
    Component,
  } from "@lucide/svelte";
  import { slide } from "svelte/transition";

  let {
    type = "note",
    message,
    isCollapsible = false,
    isOpen = $bindable(true),
    isBackgroundVisible = false,
    children,
  }: {
    type?: "note" | "tip" | "important" | "warning" | "error";
    message?: string;
    isCollapsible?: boolean;
    isOpen?: boolean;
    isBackgroundVisible?: boolean;
    children: () => any;
  } = $props();

  const calloutBaseClass = "flex flex-col border-l-2 p-4 rounded-r-md";

  export function toggle() {
    if (!isCollapsible) return;
    isOpen = !isOpen;
  }
</script>

{#snippet calloutBody(icon: typeof Component, color: string)}
  <header>
    <button
      class="w-full flex items-center gap-2 {isCollapsible
        ? 'cursor-pointer'
        : 'cursor-default'}"
      onclick={toggle}
      tabindex={isCollapsible ? 0 : -1}
      aria-disabled={!isCollapsible}
    >
      {#if icon}
        {@const Icon = icon}
        <Icon {color} />
      {/if}
      <h6 class="h6">{message}</h6>
      {#if isCollapsible}
        <div class="flex-1"></div>
        {#if isOpen}
          <ChevronUp />
        {:else}
          <ChevronDown />
        {/if}
      {/if}
    </button>
  </header>
  {#if isOpen}
    <main class="mt-2" transition:slide>
      {@render children()}
    </main>
  {/if}
{/snippet}

{#if type === "note"}
  <div
    class="{calloutBaseClass} border-l-primary-500 {isBackgroundVisible
      ? 'bg-primary-500/25'
      : ''}"
  >
    {@render calloutBody(Info, "var(--color-primary-500)")}
  </div>
{:else if type === "tip"}
  <div
    class="{calloutBaseClass} border-l-success-500 {isBackgroundVisible
      ? 'bg-success-500/25'
      : ''}"
  >
    {@render calloutBody(Lightbulb, "var(--color-success-500)")}
  </div>
{:else if type === "important"}
  <div
    class="{calloutBaseClass} border-l-tertiary-500 {isBackgroundVisible
      ? 'bg-tertiary-500/25'
      : ''}"
  >
    {@render calloutBody(MessageSquareWarning, "var(--color-tertiary-500)")}
  </div>
{:else if type === "warning"}
  <div
    class="{calloutBaseClass} border-l-warning-500 {isBackgroundVisible
      ? 'bg-warning-500/25'
      : ''}"
  >
    {@render calloutBody(TriangleAlert, "var(--color-warning-500)")}
  </div>
{:else if type === "error"}
  <div
    class="{calloutBaseClass} border-l-error-500 {isBackgroundVisible
      ? 'bg-error-500/25'
      : ''}"
  >
    {@render calloutBody(MessageSquareX, "var(--color-error-500)")}
  </div>
{/if}
