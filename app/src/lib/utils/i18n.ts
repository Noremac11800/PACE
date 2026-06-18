import { getLocaleFromNavigator, init, register, locale, t } from "svelte-i18n";

const translations = import.meta.glob<{
  default: Record<string, unknown>;
}>("../i18n/*.json");

export const defaultLocale = "en";

export const supportedLocales = Object.keys(translations)
  .map((path) => path.split("/").pop()?.replace(".json", ""))
  .filter((v): v is string => Boolean(v))
  .sort((a, b) => a.localeCompare(b));

const rtlLanguageCodes = new Set([
  "ar",
  "fa",
  "he",
  "ur",
  "ps",
  "dv",
  "ku",
  "yi",
]);

export function isRtlLocale(localeCode: string) {
  const base = localeCode.split(/[-_]/)[0]?.toLowerCase();
  if (!base) return false;
  return rtlLanguageCodes.has(base);
}

export async function loadLocaleResource(localeCode: string) {
  const normalized = localeCode.replace("_", "-");

  const directPath = `../i18n/${normalized}.json`;
  const base = normalized.split("-")[0];
  const basePath = base ? `../i18n/${base}.json` : "";

  const direct = translations[directPath];
  if (direct) return (await direct()).default;

  const fallback = basePath ? translations[basePath] : undefined;
  if (fallback) return (await fallback()).default;

  return null;
}

let isInitialized = false;

export function initI18n() {
  if (isInitialized) return;
  isInitialized = true;

  for (const [path, loader] of Object.entries(translations)) {
    const code = path.split("/").pop()?.replace(".json", "");
    if (!code) continue;
    register(code, async () => (await loader()).default);
  }

  init({
    fallbackLocale: defaultLocale,
    initialLocale: getLocaleFromNavigator(),
  });
}

export { locale, t };
