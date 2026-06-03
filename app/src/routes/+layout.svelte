<script lang="ts">
  import { X } from "@lucide/svelte";
  import "../app.css";
  import { createToaster } from "@skeletonlabs/skeleton-svelte";
  import { Toast } from "@skeletonlabs/skeleton-svelte";
  import { setContext } from "svelte";
  import { initI18n, isRtlLocale, locale } from "$lib/i18n";
  import { setToaster } from "$lib/toaster";
  import { fly } from "svelte/transition";
  import { page } from "$app/state";
  import { beforeNavigate } from "$app/navigation";
  import { onMount } from "svelte";
  import { initializeApp, applyFontSize } from "$lib/app-init";
  import { settings } from "$lib/settings.svelte";

  const { children } = $props();

  const toaster = createToaster({ placement: "bottom-end" });
  setContext("toaster", toaster);
  setToaster(toaster);

  initI18n();

  onMount(() => {
    initializeApp();
  });

  let transitionParams = $state({ x: 0, duration: 300 });

  $effect(() => {
    const html = document.documentElement;
    const currentLocale = $locale ?? "en";
    html.lang = currentLocale;
    html.dir = isRtlLocale(currentLocale) ? "rtl" : "ltr";
  });

  $effect(() => {
    applyFontSize(settings.appearance.fontSize);
  });

  beforeNavigate((navigation) => {
    const oldPath = navigation.from?.url.pathname ?? "";
    const newPath = navigation.to?.url.pathname ?? "";
    if (newPath && newPath !== oldPath) {
      const oldSegments = oldPath.split("/").filter(Boolean);
      const newSegments = newPath.split("/").filter(Boolean);
      if (newSegments.length >= oldSegments.length) {
        transitionParams = { x: -100, duration: 300 };
      } else if (newSegments.length < oldSegments.length) {
        transitionParams = { x: 100, duration: 300 };
      } else {
        transitionParams = { x: 0, duration: 300 };
      }
    }
  });
</script>

{#key page.url.pathname}
  <main class="app-shell flex flex-col" transition:fly={transitionParams}>
    {@render children()}
  </main>
{/key}

<Toast.Group {toaster}>
  {#snippet children(toast)}
    <Toast {toast}>
      {#snippet element(attributes)}
        <div
          {...attributes}
          class="flex flex-row items-center gap-4 pr-12 border-0 border-t-2 border-t-primary-200-800 rounded-sm shadow-md"
        >
          <div class="w-6 h-6 {toast.meta?.icon == null ? 'hidden' : ''}">
            {@render toast.meta?.icon?.()}
          </div>

          <div class="flex flex-col gap-2">
            {#if toast.title}
              <Toast.Title>
                {#snippet element(attributes)}
                  <div {...attributes}>
                    <h6 class="h6 text-sm">
                      {toast.title}
                    </h6>
                  </div>
                {/snippet}
              </Toast.Title>
            {/if}

            {#if toast.description}
              <Toast.Description>
                {#snippet element(attributes)}
                  <div {...attributes}>
                    <p
                      class="text-xs text-surface-600-400 {toast.description ==
                      ''
                        ? 'hidden'
                        : ''}"
                    >
                      {toast.description}
                    </p>
                  </div>
                {/snippet}
              </Toast.Description>
            {/if}
          </div>

          <Toast.ActionTrigger>
            {#snippet element(attributes)}
              <button {...attributes} class="hidden"></button>
            {/snippet}
          </Toast.ActionTrigger>
          <Toast.CloseTrigger>
            {#snippet element(attributes)}
              <button {...attributes} class="btn absolute right-2 p-2">
                <X size={16} />
              </button>
            {/snippet}
          </Toast.CloseTrigger>
        </div>
      {/snippet}
    </Toast>
  {/snippet}
</Toast.Group>
