<script lang="ts">
  import { ChevronDown, Languages, RotateCcw } from "@lucide/svelte";
  import BottomSheet from "$lib/components/BottomSheet.svelte";
  import {
    defaultLocale,
    loadLocaleResource,
    locale,
    supportedLocales,
  } from "$lib/i18n";

  type LocaleMeta = {
    locale?: string;
    name?: string;
  };

  let localeNamesByCode = $state<Record<string, string>>({});

  async function getLocaleName(code: string) {
    const loaded = await loadLocaleResource(code);
    const meta = (loaded as { meta?: LocaleMeta } | null)?.meta;
    return meta?.name ?? code;
  }

  async function hydrateLocaleNames() {
    const entries = await Promise.all(
      supportedLocales.map(
        async (code) => [code, await getLocaleName(code)] as const,
      ),
    );

    localeNamesByCode = Object.fromEntries(entries);
  }

  $effect(() => {
    void hydrateLocaleNames();
  });

  const flagByLocale: Record<string, string> = {
    ar: "🇸🇦",
    cs: "🇨🇿",
    da: "🇩🇰",
    de: "🇩🇪",
    el: "🇬🇷",
    en: "🇦🇺",
    es: "🇪🇸",
    fa: "🇮🇷",
    fi: "🇫🇮",
    fr: "🇫🇷",
    he: "🇮🇱",
    hi: "🇮🇳",
    hu: "🇭🇺",
    id: "🇮🇩",
    it: "🇮🇹",
    ja: "🇯🇵",
    ko: "🇰🇷",
    ms: "🇲🇾",
    nl: "🇳🇱",
    no: "🇳🇴",
    pl: "🇵🇱",
    pt: "🇵🇹",
    "pt-BR": "🇧🇷",
    ro: "🇷🇴",
    ru: "🇷🇺",
    sv: "🇸🇪",
    th: "🇹🇭",
    tl: "🇵🇭",
    tr: "🇹🇷",
    uk: "🇺🇦",
    ur: "🇵🇰",
    vi: "🇻🇳",
    "zh-CN": "🇨🇳",
    "zh-TW": "🇹🇼",
  };

  function getFlagEmoji(code: string) {
    return flagByLocale[code] ?? flagByLocale[code.split("-")[0] ?? ""] ?? "🏳️";
  }

  function resetToDefault() {
    locale.set(defaultLocale);
  }
</script>

{#snippet languageSwitcher()}
  <button
    class="btn preset-outlined-surface-500 p-1 self-center flex items-center gap-2"
  >
    <Languages size={20} color="var(--color-primary-500)" />
    <span aria-hidden="true">{getFlagEmoji($locale ?? defaultLocale)}</span>
    <ChevronDown size={20} />
  </button>
{/snippet}

{#snippet languagePickerContent()}
  <div class="flex flex-col gap-2">
    <button
      class="btn justify-start preset-tonal-surface-500"
      onclick={resetToDefault}
    >
      <RotateCcw class="mr-2" />
      Reset to default ({defaultLocale})
    </button>

    {#each supportedLocales as code (code)}
      <button
        class="btn justify-start {code === $locale
          ? 'preset-filled-primary-500'
          : 'preset-tonal-surface-500'}"
        onclick={() => locale.set(code)}
      >
        <span class="mr-2" aria-hidden="true">{getFlagEmoji(code)}</span>
        {localeNamesByCode[code] ?? code} ({code})
      </button>
    {/each}
  </div>
{/snippet}

<BottomSheet
  trigger={languageSwitcher}
  title="Select a language"
  content={languagePickerContent}
/>
