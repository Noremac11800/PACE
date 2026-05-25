import { writable } from "svelte/store";
import { browser } from "$app/environment";

const themeStore = writable<"light" | "dark">("light");

if (browser) {
  const initial = localStorage.getItem("mode") === "dark" ? "dark" : "light";
  themeStore.set(initial);
}

export const theme = {
  subscribe: themeStore.subscribe,
  set: (mode: "light" | "dark") => {
    if (browser) {
      localStorage.setItem("mode", mode);
      document.documentElement.setAttribute("data-mode", mode);
    }
    themeStore.set(mode);
  },
  get: () => {
    if (!browser) return "light";
    return localStorage.getItem("mode") === "dark" ? "dark" : "light";
  },
};
