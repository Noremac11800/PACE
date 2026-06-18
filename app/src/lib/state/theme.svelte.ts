import { browser } from "$app/environment";

let mode = $state<"light" | "dark">(
  browser
    ? localStorage.getItem("mode") === "dark"
      ? "dark"
      : "light"
    : "light",
);

export const theme = {
  get current() {
    return mode;
  },
  set: (value: "light" | "dark") => {
    if (browser) {
      localStorage.setItem("mode", value);
      document.documentElement.setAttribute("data-mode", value);
    }
    mode = value;
  },
  get: () => {
    if (!browser) return "light" as const;
    return localStorage.getItem("mode") === "dark"
      ? ("dark" as const)
      : ("light" as const);
  },
};
