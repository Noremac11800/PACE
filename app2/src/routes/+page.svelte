<script lang="ts">
    import { onMount } from "svelte";
    import { getCurrentWindow } from "@tauri-apps/api/window";
    import type { UnlistenFn } from "@tauri-apps/api/event";
    import { app } from "$lib/state/app.svelte";
    import { desktop } from "$lib/services/desktop";
    import type { View } from "$lib/domain/types";
    import type { IconName } from "$lib/components/ui/icons";
    import ThemeToggle from "$lib/components/ThemeToggle.svelte";
    import AppGlyph from "$lib/components/AppGlyph.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import Spinner from "$lib/components/ui/Spinner.svelte";
    import Dialog from "$lib/components/ui/Dialog.svelte";
    import EmptyState from "$lib/components/EmptyState.svelte";
    import Overview from "$lib/views/Overview.svelte";
    import Repositories from "$lib/views/Repositories.svelte";
    import Dependencies from "$lib/views/Dependencies.svelte";
    import Git from "$lib/views/Git.svelte";
    import Dotnet from "$lib/views/Dotnet.svelte";
    import Configuration from "$lib/views/Configuration.svelte";
    import Activity from "$lib/views/Activity.svelte";
    import Settings from "$lib/views/Settings.svelte";

    const navigation: {
        label: string;
        items: { view: View; label: string; icon: IconName }[];
    }[] = [
        {
            label: "Workspace",
            items: [
                { view: "overview", label: "Overview", icon: "dashboard" },
                {
                    view: "repositories",
                    label: "Repositories",
                    icon: "folders",
                },
                {
                    view: "dependencies",
                    label: "Dependency map",
                    icon: "code-branch",
                },
            ],
        },
        {
            label: "Operations",
            items: [
                { view: "git", label: "Git operations", icon: "refresh" },
                { view: "dotnet", label: ".NET operations", icon: "gear" },
                {
                    view: "activity",
                    label: "Command activity",
                    icon: "console",
                },
            ],
        },
        {
            label: "Manage",
            items: [
                {
                    view: "configuration",
                    label: "Configuration",
                    icon: "file-code",
                },
            ],
        },
    ];
    let main = $state<HTMLElement>();

    $effect(() => {
        app.view;
        if (main) main.scrollTop = 0;
    });

    onMount(() => {
        app.initialize();
        let unlisten: UnlistenFn | undefined;
        let disposed = false;
        if (desktop)
            getCurrentWindow()
                .onCloseRequested(async (event) => {
                    if (app.locked) {
                        event.preventDefault();
                        app.notify(
                            "Wait for the current operation to finish before closing PACE.",
                            "info",
                        );
                    } else if (app.dirty) {
                        event.preventDefault();
                        if (await app.canReplace()) {
                            try {
                                await getCurrentWindow().destroy();
                            } catch (error) {
                                app.error(error);
                            }
                        }
                    }
                })
                .then((listener) => {
                    if (disposed) listener();
                    else unlisten = listener;
                })
                .catch((error) => app.error(error));
        return () => {
            disposed = true;
            unlisten?.();
        };
    });

    function beforeUnload(event: BeforeUnloadEvent) {
        if (app.dirty || app.running) {
            event.preventDefault();
            event.returnValue = "";
        }
    }
</script>

<svelte:window onbeforeunload={beforeUnload} />
<svelte:head
    ><title>PACE · {app.name}</title><meta
        name="description"
        content="A desktop workspace for managing .NET repositories with pacev2."
    /></svelte:head
>

<a
    href="#main-content"
    class="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-foreground-primary focus:p-3"
    >Skip to content</a
>
<div
    class="grid h-dvh min-w-[960px] grid-cols-[228px_minmax(0,1fr)] grid-rows-[64px_minmax(0,1fr)_30px] overflow-hidden"
>
    <header
        class="col-span-2 flex items-center border-b border-border-tertiary bg-foreground-primary"
    >
        <button
            class="flex h-full w-[228px] shrink-0 items-center gap-3 border-r border-border-tertiary px-6 text-left"
            onclick={() => (app.view = "overview")}
            aria-label="PACE overview"
        >
            <AppGlyph class="size-8" />
            <div>
                <span class="text-title-medium tracking-wide">PACE</span><span
                    class="mt-0.5 block text-[10px] font-medium uppercase tracking-[0.16em] text-text-tertiary"
                    >Workspace</span
                >
            </div>
        </button>
        <div
            class="flex min-w-0 flex-1 items-center gap-2 px-6 text-body-small"
        >
            <Icon name="folder" size={16} class="text-text-tertiary" /><span
                class="truncate text-text-secondary">{app.name}</span
            >{#if app.dirty}<span
                    class="size-1.5 rounded-full bg-status-warning"
                    title="Unsaved configuration changes"
                ></span>{/if}
        </div>
        <div class="flex items-center gap-5 pr-5">
            <span
                class="flex items-center gap-2 text-caption text-text-secondary"
                ><span
                    class={[
                        "size-1.5 rounded-full",
                        app.workspace ? "bg-brand" : "bg-text-tertiary",
                    ]}
                ></span>{app.workspace
                    ? "CLI connected"
                    : desktop
                      ? "Not connected"
                      : "Browser preview"}</span
            ><ThemeToggle labelled={false} />
        </div>
    </header>

    <aside
        class="flex min-h-0 flex-col border-r border-border-tertiary bg-foreground-primary"
    >
        <div class="border-b border-border-tertiary p-4">
            <label for="workspace-select" class="eyebrow mb-2 block"
                >Configuration</label
            >
            <select
                id="workspace-select"
                class="field-select text-body-small"
                value={app.workspace?.path ?? ""}
                disabled={!desktop || app.locked || !app.workspace}
                onchange={(event) => {
                    const path = event.currentTarget.value;
                    event.currentTarget.value = app.workspace?.path ?? "";
                    app.load(path);
                }}
            >
                {#if !app.workspace}<option value=""
                        >Select a configuration</option
                    >{/if}
                {#each app.workspace?.configs ?? [] as config}<option
                        value={config.path}>{config.name}</option
                    >{/each}
            </select>
            <div class="mt-2 flex gap-1">
                <Button
                    kind="neutral"
                    appearance="transparent"
                    scale="s"
                    iconStart="folder-open"
                    disabled={!desktop || app.locked}
                    onclick={() => app.open()}>Open</Button
                ><Button
                    kind="neutral"
                    appearance="transparent"
                    scale="s"
                    iconStart="plus"
                    disabled={!desktop || app.locked}
                    onclick={() => app.create()}>New</Button
                >
            </div>
        </div>
        <nav
            class="flex-1 space-y-6 overflow-y-auto px-3 py-5"
            aria-label="Main navigation"
        >
            {#each navigation as group}
                <div>
                    <p class="eyebrow mb-2 px-3">{group.label}</p>
                    <div class="space-y-1">
                        {#each group.items as item}
                            <button
                                aria-current={app.view === item.view
                                    ? "page"
                                    : undefined}
                                onclick={() => (app.view = item.view)}
                                class={[
                                    "flex h-11 w-full items-center gap-3 rounded px-3 text-left text-label-medium transition-colors",
                                    app.view === item.view
                                        ? "bg-foreground-current text-text-primary"
                                        : "text-text-secondary hover:bg-transparent-hover",
                                ]}
                            >
                                <Icon
                                    name={item.icon}
                                    size={20}
                                    class={app.view === item.view
                                        ? "text-brand"
                                        : ""}
                                /><span class="flex-1">{item.label}</span>
                                {#if item.view === "repositories" && app.workspace}<span
                                        class="text-caption text-text-tertiary"
                                        >{app.workspace.config.projects
                                            .length}</span
                                    >{/if}
                                {#if item.view === "activity" && app.running}<Spinner
                                        scale="s"
                                    />{/if}
                            </button>
                        {/each}
                    </div>
                </div>
            {/each}
        </nav>
        <div class="border-t border-border-tertiary p-3">
            <button
                aria-current={app.view === "settings" ? "page" : undefined}
                class={[
                    "flex h-11 w-full items-center gap-3 rounded px-3 text-label-medium",
                    app.view === "settings"
                        ? "bg-foreground-current"
                        : "text-text-secondary hover:bg-transparent-hover",
                ]}
                onclick={() => (app.view = "settings")}
                ><Icon name="gear" size={20} />Settings</button
            >
            <div
                class="mt-3 flex items-center justify-between px-3 pb-1 text-caption text-text-tertiary"
            >
                <span>PACE Desktop</span><span>v{app.appVersion}</span>
            </div>
        </div>
    </aside>

    <main
        bind:this={main}
        id="main-content"
        tabindex="-1"
        class="min-w-0 overflow-y-auto outline-none"
    >
        <div class="mx-auto max-w-[1440px] p-7 xl:p-9">
            {#if app.notice}
                <div
                    role={app.notice.tone === "error" ? "alert" : "status"}
                    class={[
                        "mb-6 flex items-start gap-3 rounded border p-4",
                        app.notice.tone === "error"
                            ? "border-status-danger bg-required-background"
                            : app.notice.tone === "success"
                              ? "border-border-tertiary bg-foreground-current"
                              : "border-border-tertiary bg-warning-background",
                    ]}
                >
                    <Icon
                        name={app.notice.tone === "error"
                            ? "exclamation-mark-triangle"
                            : "information"}
                        size={18}
                        class={app.notice.tone === "error"
                            ? "text-status-danger"
                            : "text-brand"}
                    />
                    <p
                        class="min-w-0 flex-1 whitespace-pre-wrap break-words text-body-small leading-relaxed"
                    >
                        {app.notice.text}
                    </p>
                    <Button
                        icon="x"
                        label="Dismiss notification"
                        kind="neutral"
                        appearance="transparent"
                        scale="xs"
                        onclick={() => (app.notice = null)}
                    />
                </div>
            {/if}
            {#if !app.initialized}
                <div
                    class="flex items-center justify-center gap-3 py-28 text-text-secondary"
                >
                    <Spinner scale="m" />Connecting to pacev2...
                </div>
            {:else if !app.workspace && !["overview", "activity", "settings"].includes(app.view)}
                <EmptyState
                    title="Open a configuration to continue"
                    description="This view uses the repositories and dependencies in your active PACE configuration."
                >
                    {#snippet actions()}<Button
                            iconStart="folder-open"
                            disabled={!desktop || app.locked}
                            onclick={() => app.open()}
                            >Open configuration</Button
                        ><Button
                            kind="neutral"
                            appearance="outline-fill"
                            onclick={() => (app.view = "settings")}
                            >Runtime settings</Button
                        >{/snippet}
                </EmptyState>
            {:else if app.view === "overview"}<Overview />
            {:else if app.view === "repositories"}<Repositories />
            {:else if app.view === "dependencies"}<Dependencies />
            {:else if app.view === "git"}<Git />
            {:else if app.view === "dotnet"}<Dotnet />
            {:else if app.view === "configuration"}<Configuration />
            {:else if app.view === "activity"}<Activity />
            {:else if app.view === "settings"}<Settings />{/if}
        </div>
    </main>
    <footer
        class="col-span-2 flex items-center gap-4 border-t border-border-tertiary bg-foreground-primary px-4 text-caption text-text-tertiary"
    >
        <span class="flex shrink-0 items-center gap-1.5"
            >{#if app.locked}<Spinner scale="s" />{app.running
                    ? "Command running"
                    : "Working..."}{:else}<span
                    class="size-1.5 rounded-full bg-brand"
                ></span>{desktop ? "Ready" : "Preview only"}{/if}</span
        >
        <span class="truncate"
            >{app.workspace?.repoRoot ??
                "Project Automation and Configuration Engine"}</span
        >
        <span class="ml-auto shrink-0"
            >{app.workspace
                ? `${app.selectedNames.length} repositories in scope`
                : "Desktop · pacev2"}</span
        >
    </footer>
</div>
<Dialog
    open={!!app.confirmation}
    heading={app.confirmation?.heading}
    description={app.confirmation?.description}
    onclose={() => app.answer(false)}
>
    {#snippet actions()}<Button
            kind="neutral"
            appearance="outline-fill"
            scale="s"
            onclick={() => app.answer(false)}>Cancel</Button
        ><Button scale="s" onclick={() => app.answer(true)}
            >{app.confirmation?.accept ?? "Continue"}</Button
        >{/snippet}
</Dialog>
