import { defineConfig } from "@playwright/test";

export default defineConfig({
    testDir: "./tests",
    workers: 1,
    use: {
        baseURL: "http://127.0.0.1:1420",
        channel: "chrome",
        viewport: { width: 1360, height: 900 },
        screenshot: "only-on-failure",
    },
    webServer: {
        command: "bun run dev",
        url: "http://127.0.0.1:1420",
        reuseExistingServer: !process.env.CI,
    },
});
