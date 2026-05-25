<script lang="ts">
  import { getContext, onMount } from "svelte";
  import type { LayoutProps } from "../+layout.svelte";
  import { loadLocaleResource, locale } from "$lib/i18n";

  const data = getContext<LayoutProps>("data");

  type JsonValue =
    | string
    | number
    | boolean
    | null
    | { [key: string]: JsonValue }
    | JsonValue[];
  type JsonObject = { [key: string]: JsonValue };

  const categoryOrder = [
    "meta",
    "common",
    "nav",
    "auth",
    "forms",
    "validation",
    "errors",
    "emptyStates",
    "dates",
    "toast",
    "confirmations",
  ] as const;

  let resource = $state<JsonObject | null>(null);

  async function refreshResource() {
    const currentLocale = $locale ?? "en";
    const loaded = await loadLocaleResource(currentLocale);
    resource = (loaded ?? null) as JsonObject | null;
  }

  $effect(() => {
    void refreshResource();
  });

  onMount(() => {
    data.title = "i18n";
  });

  function isPlainObject(value: unknown): value is JsonObject {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function entriesOrdered(obj: JsonObject) {
    return Object.entries(obj).sort(([a], [b]) => a.localeCompare(b));
  }

  function flattenToRows(
    value: JsonValue,
    prefix: string,
  ): Array<{ key: string; value: string }> {
    if (typeof value === "string") return [{ key: prefix, value }];
    if (
      typeof value === "number" ||
      typeof value === "boolean" ||
      value == null
    ) {
      return [{ key: prefix, value: String(value) }];
    }

    if (Array.isArray(value)) {
      return value.flatMap((item, idx) =>
        flattenToRows(item as JsonValue, `${prefix}[${idx}]`),
      );
    }

    if (isPlainObject(value)) {
      return entriesOrdered(value).flatMap(([k, v]) =>
        flattenToRows(v, prefix ? `${prefix}.${k}` : k),
      );
    }

    return [{ key: prefix, value: String(value) }];
  }
</script>

<main class="flex flex-col gap-6 p-8">
  <nav class="card p-3 bg-surface-50-950 shadow-md space-y-2">
    <p class="text-sm font-semibold text-surface-700-300">Contents</p>
    <div class="flex flex-wrap gap-2">
      {#each categoryOrder as category}
        <a
          class="btn preset-tonal-surface-500 py-1 px-3 text-xs rounded-full hover:preset-filled-primary-500"
          href={`#section-${category}`}
        >
          {category}
        </a>
      {/each}
    </div>
  </nav>

  {#if resource == null}
    <div class="card p-4 bg-surface-50-950 shadow-md">
      <p class="text-sm text-surface-700-300">No locale resource loaded.</p>
    </div>
  {:else}
    <div class="space-y-4">
      {#each categoryOrder as category}
        <section class="space-y-2" id={`section-${category}`}>
          <h4 class="h4">{category}</h4>

          {#if (resource as JsonObject)[category] == null}
            <div class="card p-4 bg-surface-50-950 shadow-md">
              <p class="text-sm text-surface-700-300">Missing category.</p>
            </div>
          {:else}
            {@const rows = flattenToRows(
              (resource as JsonObject)[category] as JsonValue,
              category,
            )}
            <div class="card p-4 bg-surface-50-950 shadow-md">
              <div class="flex flex-col divide-y divide-surface-200-800">
                {#each rows as row}
                  <div class="py-2 flex flex-col gap-1">
                    <span class="font-mono text-xs text-surface-700-300">
                      {row.key}
                    </span>
                    <span class="text-sm font-medium whitespace-pre-line">
                      {row.value}
                    </span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </section>
      {/each}
    </div>
  {/if}
</main>
