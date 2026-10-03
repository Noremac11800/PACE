import { MediaQuery } from "svelte/reactivity";

export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "theme";

const systemDark = new MediaQuery("(prefers-color-scheme: dark)", false);

class Theme {
    // Always 'system' during SSR/hydration; `restore()` syncs with storage once mounted.
    preference = $state<ThemePreference>("system");

    /** The theme on screen: the preference, or the device's when following the system */
    get resolved(): "light" | "dark" {
        if (this.preference !== "system") return this.preference;
        return systemDark.current ? "dark" : "light";
    }

    restore() {
        const saved = localStorage.getItem(STORAGE_KEY);
        this.preference =
            saved === "light" || saved === "dark" ? saved : "system";
    }

    set(preference: ThemePreference) {
        this.preference = preference;
        const root = document.documentElement;
        if (preference === "system") {
            delete root.dataset.theme;
            localStorage.removeItem(STORAGE_KEY);
        } else {
            root.dataset.theme = preference;
            localStorage.setItem(STORAGE_KEY, preference);
        }
    }
}

export const theme = new Theme();
