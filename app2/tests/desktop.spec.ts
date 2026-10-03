import { expect, test } from "@playwright/test";
import { execFileSync, spawnSync } from "node:child_process";
import {
    mkdtempSync,
    mkdirSync,
    readFileSync,
    rmSync,
    writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { resolve, join } from "node:path";

const python = resolve(
    "../pacev2/.venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
let directory: string;
let configPath: string;

test.beforeEach(async ({ page }) => {
    directory = mkdtempSync(join(tmpdir(), "pace-ui-"));
    configPath = join(directory, "workspace.toml");
    writeFileSync(
        configPath,
        `# Test workspace\nrepodir = "./repos"\n` +
            [
                ["foundation", "Libraries", []],
                ["services", "Libraries", ["foundation"]],
                ["desktop-client", "Applications", ["services"]],
                ["web-client", "Applications", ["services"]],
            ]
                .map(
                    ([name, group, dependencies]) =>
                        `[[projects]]\nname = "${name}"\ncsproj_path = "${name}/${name}.csproj"\nsln_group = "${group}"\nrepo_url = "https://example.invalid/${name}.git"\ndepends_on = ${JSON.stringify(dependencies)}\n`,
                )
                .join("\n"),
    );
    mkdirSync(join(directory, ".pace"));
    writeFileSync(
        join(directory, ".pace/settings.json"),
        JSON.stringify({ lastActiveConfig: configPath }),
    );
    mkdirSync(join(directory, "repos/foundation"), { recursive: true });
    execFileSync("git", [
        "init",
        "--quiet",
        join(directory, "repos/foundation"),
    ]);
    const env = {
        ...process.env,
        HOME: directory,
        USERPROFILE: directory,
        NO_COLOR: "1",
        PYTHONIOENCODING: "utf-8",
        TERM: "dumb",
    };

    // Only the native IPC transport is replaced. Config and Git requests use real pacev2.
    await page.exposeFunction(
        "testInvoke",
        (command: string, payload: Record<string, unknown>) => {
            if (command === "environment")
                return { python, directory, appVersion: "0.1.0" };
            if (command === "bridge") {
                const result = spawnSync(
                    python,
                    [resolve("src-tauri/bridge.py")],
                    {
                        input: JSON.stringify(payload.request),
                        encoding: "utf8",
                        cwd: directory,
                        env,
                    },
                );
                if (result.error) throw result.error;
                if (result.status !== 0) throw new Error(result.stderr);
                return {
                    data: JSON.parse(result.stdout),
                    warnings: result.stderr,
                };
            }
            if (command === "run_pace") {
                const args = payload.args as string[];
                const result = spawnSync(python, ["-m", "pacev2", ...args], {
                    encoding: "utf8",
                    cwd: directory,
                    env,
                });
                if (result.error) throw result.error;
                return {
                    code: result.status,
                    text: result.stdout + result.stderr,
                };
            }
            if (command === "plugin:event|listen") return 1;
            if (command === "plugin:event|unlisten") return null;
            throw new Error(`Unexpected native request: ${command}`);
        },
    );
    await page.addInitScript(() => {
        const callbacks = new Map<number, (message: unknown) => void>();
        let nextId = 0;
        Object.assign(window, {
            isTauri: true,
            __TAURI_INTERNALS__: {
                metadata: { currentWindow: { label: "main" } },
                transformCallback(callback: (message: unknown) => void) {
                    callbacks.set(++nextId, callback);
                    return nextId;
                },
                unregisterCallback(id: number) {
                    callbacks.delete(id);
                },
                async invoke(
                    command: string,
                    payload: Record<string, unknown>,
                ) {
                    const transport = Reflect.get(window, "testInvoke") as (
                        command: string,
                        payload: unknown,
                    ) => Promise<unknown>;
                    const result = await transport(
                        command,
                        JSON.parse(JSON.stringify(payload ?? {})),
                    );
                    if (command === "run_pace") {
                        const { code, text } = result as {
                            code: number;
                            text: string;
                        };
                        const channel = payload.output as { id: number };
                        callbacks.get(channel.id)?.({
                            index: 0,
                            message: { stream: "stdout", text },
                        });
                        callbacks.get(channel.id)?.({ index: 1, end: true });
                        return code;
                    }
                    return result;
                },
            },
            __TAURI_EVENT_PLUGIN_INTERNALS__: { unregisterListener() {} },
        });
    });
    await page.goto("/");
    await expect(
        page.getByRole("heading", { name: "Workspace overview" }),
    ).toBeVisible();
    await expect(page.getByText("CLI connected")).toBeVisible();
});

test.afterEach(() => {
    // Only the exact fixture directory created by this test is removed.
    rmSync(directory, { recursive: true, force: true });
});

test("desktop navigation, real scope filtering, and persistent light/dark themes", async ({
    page,
}, testInfo) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.getByRole("radio", { name: "Light", exact: true }).click();
    await expect(
        page.getByRole("radio", { name: "Light", exact: true }),
    ).toHaveAttribute("aria-checked", "true");
    await page.screenshot({
        path: testInfo.outputPath("overview-light.png"),
        animations: "disabled",
    });
    await page.getByRole("radio", { name: "Dark", exact: true }).click();
    await expect(
        page.getByRole("radio", { name: "Dark", exact: true }),
    ).toHaveAttribute("aria-checked", "true");
    await page.screenshot({
        path: testInfo.outputPath("overview-dark.png"),
        animations: "disabled",
    });
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page
        .getByRole("button", { name: "Repositories", exact: false })
        .first()
        .click();
    await page
        .getByRole("textbox", { name: "Search repositories", exact: true })
        .fill("desktop");
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await page
        .getByRole("textbox", { name: "Search repositories", exact: true })
        .fill("");
    await page
        .getByRole("combobox", { name: "From", exact: true })
        .selectOption("services");
    await page
        .getByRole("combobox", { name: "To", exact: true })
        .selectOption("desktop-client");
    await expect(page.locator("tbody tr")).toHaveCount(2);
    await page
        .getByRole("button", { name: "Dependency map", exact: true })
        .click();
    await expect(
        page.getByRole("heading", { name: "Project layers" }),
    ).toBeVisible();
    await page.screenshot({
        path: testInfo.outputPath("dependencies-dark.png"),
    });
    for (const name of [
        "Git operations",
        "Command activity",
        "Configuration",
        "Settings",
    ]) {
        await page.getByRole("button", { name, exact: true }).click();
        await expect(
            page.getByRole("heading", { name, exact: true }),
        ).toBeVisible();
        await page.screenshot({
            path: testInfo.outputPath(
                `${name.toLowerCase().replaceAll(" ", "-")}-dark.png`,
            ),
            animations: "disabled",
        });
    }
    await page.setViewportSize({ width: 960, height: 640 });
    expect(
        await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
    ).toBe(true);
    for (const name of ["Overview", "Repositories", "Git operations"]) {
        await page
            .getByRole("navigation")
            .getByRole("button", { name, exact: false })
            .click();
        expect(
            await page
                .locator("main")
                .evaluate((main) => main.scrollWidth <= main.clientWidth),
        ).toBe(true);
    }
    expect(errors).toEqual([]);
});

test("theme follows system changes and repository details use an accessible dialog", async ({
    page,
}) => {
    await page.getByRole("radio", { name: "System", exact: true }).click();
    await page.emulateMedia({ colorScheme: "dark" });
    await expect
        .poll(() =>
            page
                .locator("body")
                .evaluate((body) => getComputedStyle(body).backgroundColor),
        )
        .toBe("rgb(53, 53, 53)");
    await page.emulateMedia({ colorScheme: "light" });
    await expect
        .poll(() =>
            page
                .locator("body")
                .evaluate((body) => getComputedStyle(body).backgroundColor),
        )
        .toBe("rgb(248, 248, 248)");
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Repositories" })
        .click();
    await page.getByRole("button", { name: "Details for foundation" }).click();
    await expect(page.getByRole("dialog")).toContainText("foundation.csproj");
    await page
        .getByRole("dialog")
        .getByRole("button", { name: "Close", exact: true })
        .click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
});

test("unsaved edits survive navigation and invalid files cannot be saved", async ({
    page,
}) => {
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    const editor = page.getByLabel("TOML configuration source");
    const original = await editor.inputValue();
    await editor.fill(original + "\ninvalid = [");
    await page
        .getByRole("button", { name: "Save changes", exact: true })
        .click();
    await expect(page.getByRole("alert")).toBeVisible();
    expect(readFileSync(configPath, "utf8")).toBe(original);
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await expect(
        page.getByRole("button", { name: "Check status", exact: true }),
    ).toBeDisabled();
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    await expect(editor).toHaveValue(original + "\ninvalid = [");
    await page.getByRole("button", { name: "Reload from disk" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page
        .getByRole("button", { name: "Discard changes", exact: true })
        .click();
    await expect(editor).toHaveValue(original);
    await editor.fill(original + "\n# saved through the app\n");
    await page
        .getByRole("button", { name: "Save changes", exact: true })
        .click();
    await expect(
        page.getByText("Configuration saved and loaded."),
    ).toBeVisible();
    expect(readFileSync(configPath, "utf8")).toContain(
        "# saved through the app",
    );
});

test("Git status and a failed custom command report real CLI results", async ({
    page,
}, testInfo) => {
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Check status", exact: true })
        .click();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await expect(
        page.getByRole("region", { name: "Command output" }),
    ).toContainText("foundation");
    await page.screenshot({ path: testInfo.outputPath("command-output.png") });
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await page.getByLabel("Git arguments").fill("not-a-real-git-command");
    await page
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    await page
        .getByRole("dialog")
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    await expect(page.getByText("Failed", { exact: true })).toBeVisible();
    await expect(
        page.getByRole("region", { name: "Command output" }),
    ).toContainText("not-a-real-git-command");
});
