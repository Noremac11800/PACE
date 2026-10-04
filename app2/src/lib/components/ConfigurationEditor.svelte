<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import { chooseDirectory, request } from "$lib/services/desktop";
    import type {
        ConfigurationEdit,
        ConfigurationFields,
        PaceConfig,
    } from "$lib/domain/types";
    import Button from "./ui/Button.svelte";
    import Chip from "./ui/Chip.svelte";
    import Dialog from "./ui/Dialog.svelte";
    import Input from "./ui/Input.svelte";

    let { section }: { section: "properties" | "paths" } = $props();
    let fields = $state<ConfigurationFields | null>(null);
    let loadedSource = $state("");
    let loadError = $state("");
    let editError = $state("");
    let open = $state(false);
    let mode = $state<"property" | "paths" | "directory">("property");
    let index = $state<number | null>(null);
    let editSource = "";
    let property = $state<PaceConfig["build_props"][number]>({
        name: "",
        datatype: "string",
        default: "",
    });
    let repodir = $state("");
    let cache = $state("");
    let directory = $state("");

    $effect(() => {
        const content = app.draft;
        const options = $state.snapshot(app.options);
        let current = true;
        fields = null;
        loadError = "";
        request<ConfigurationFields>(options, {
            action: "configuration-fields",
            content,
        }).then(
            (result) => {
                if (!current) return;
                fields = result.data;
                loadedSource = content;
                if (result.warnings) app.notify(result.warnings, "info");
            },
            (error: unknown) => {
                if (current)
                    loadError =
                        error instanceof Error ? error.message : String(error);
            },
        );
        return () => {
            current = false;
        };
    });

    function startEdit(kind: typeof mode, position: number | null = null) {
        if (!fields || app.locked) return;
        mode = kind;
        index = position;
        editSource = loadedSource;
        editError = "";
        property =
            position === null
                ? { name: "", datatype: "string", default: "" }
                : { ...fields.build_props[position] };
        repodir = fields.repodir;
        cache = fields.nuget_cache_path ?? "";
        directory = app.options.directory;
        open = true;
    }

    async function apply(change: ConfigurationEdit) {
        if (app.locked) return;
        app.busy = true;
        app.notice = null;
        editError = "";
        try {
            if (app.draft !== editSource)
                throw new Error(
                    "The draft changed. Reopen the editor before applying changes.",
                );
            const content = await app.call<string>({
                action: "edit-configuration",
                content: editSource,
                change,
            });
            if (app.draft !== editSource)
                throw new Error(
                    "The draft changed. Reopen the editor before applying changes.",
                );
            app.draft = content;
            open = false;
        } catch (error) {
            editError = error instanceof Error ? error.message : String(error);
            app.error(error);
        } finally {
            app.busy = false;
        }
    }

    async function remove(position: number) {
        if (!fields || app.locked) return;
        editSource = loadedSource;
        if (
            await app.confirm(
                `Delete ${fields.build_props[position].name}?`,
                "This removes the property from the draft. Save changes to update the configuration file.",
                "Delete property",
            )
        )
            await apply({ kind: "delete-build-property", index: position });
    }

    async function browse(
        target: "property" | "repodir" | "cache" | "directory",
    ) {
        try {
            const path = await chooseDirectory(
                {
                    property: "Build property directory",
                    repodir: "Repository directory",
                    cache: "NuGet cache directory",
                    directory: "Working directory",
                }[target],
            );
            if (path) {
                if (target === "property") property.default = path;
                else if (target === "repodir") repodir = path;
                else if (target === "cache") cache = path;
                else directory = path;
            }
        } catch (error) {
            editError = error instanceof Error ? error.message : String(error);
            app.error(error);
        }
    }

    async function submit() {
        editError = "";
        if (mode === "directory") {
            if (await app.connect({ ...app.options, directory })) open = false;
            else
                editError =
                    app.notice?.text ??
                    "The working directory was not changed.";
        } else if (mode === "paths") {
            await apply({
                kind: "paths",
                repodir,
                nuget_cache_path: cache || null,
            });
        } else {
            await apply({
                kind: "build-property",
                index,
                property: $state.snapshot(property),
            });
        }
    }
</script>

{#if loadError}
    <div
        role="alert"
        class="mb-5 rounded bg-warning-background p-4 text-body-small"
    >
        <p>
            Unable to read the configuration draft. Check the TOML source or
            runtime settings before editing these fields. Your draft has not
            been changed.
        </p>
        <pre
            class="mt-2 whitespace-pre-wrap break-all text-caption">{loadError}</pre>
    </div>
{:else if !fields}
    <p role="status" class="pb-5 text-body-small text-text-secondary">
        Reading configuration draft...
    </p>
{:else if section === "properties"}
    <div class="mb-4 flex items-start justify-between gap-4">
        <p
            class="max-w-2xl text-body-small leading-relaxed text-text-secondary"
        >
            Add, edit, or delete properties in the current draft, then Save
            changes. Enable overrides in .NET operations to pass them to a
            command. No Directory.Build.props files are generated.
        </p>
        <Button
            scale="s"
            iconStart="plus"
            disabled={app.locked}
            onclick={() => startEdit("property")}>Add property</Button
        >
    </div>
    <div class="mb-5 overflow-x-auto">
        <table class="w-full">
            <thead class="table-head"
                ><tr>
                    <th class="px-4 py-3">Property</th>
                    <th class="px-4 py-3">Type</th>
                    <th class="px-4 py-3">Default value</th>
                    <th class="px-4 py-3"
                        ><span class="sr-only">Actions</span></th
                    >
                </tr></thead
            >
            <tbody>
                {#each fields.build_props as item, position}
                    <tr>
                        <td class="table-cell mono break-all">{item.name}</td>
                        <td class="table-cell"
                            ><Chip
                                label={item.datatype}
                                scale="s"
                                appearance="none"
                            /></td
                        >
                        <td class="table-cell mono break-all"
                            >{String(item.default) || "(empty)"}</td
                        >
                        <td class="table-cell">
                            <div class="flex justify-end gap-1">
                                <Button
                                    scale="s"
                                    kind="neutral"
                                    appearance="transparent"
                                    icon="pencil"
                                    label={`Edit ${item.name}`}
                                    disabled={app.locked}
                                    onclick={() =>
                                        startEdit("property", position)}
                                />
                                <Button
                                    scale="s"
                                    kind="danger"
                                    appearance="transparent"
                                    icon="trash"
                                    label={`Delete ${item.name}`}
                                    disabled={app.locked}
                                    onclick={() => remove(position)}
                                />
                            </div>
                        </td>
                    </tr>
                {:else}
                    <tr
                        ><td
                            colspan="4"
                            class="p-6 text-center text-body-small text-text-tertiary"
                        >
                            No build properties configured. Add a property to
                            get started.
                        </td></tr
                    >
                {/each}
            </tbody>
        </table>
    </div>
{:else}
    <div class="mb-5 flex items-start justify-between gap-4">
        <p
            class="max-w-2xl text-body-small leading-relaxed text-text-secondary"
        >
            Paths below reflect the current draft. Relative paths resolve from
            the CLI working directory, not the configuration file. Changing
            paths does not move files.
        </p>
        <Button
            scale="s"
            iconStart="pencil"
            disabled={app.locked}
            onclick={() => startEdit("paths")}>Edit paths</Button
        >
    </div>
    <dl class="grid gap-5 pb-6 md:grid-cols-2">
        {#each [{ label: "Repository directory", value: fields.repodir }, { label: "Resolved repository directory", value: fields.repoRoot }, { label: "Custom NuGet cache", value: fields.nuget_cache_path || "Not configured" }, { label: "Resolved NuGet cache", value: fields.nugetCacheRoot || "Default NuGet cache" }] as path}
            <div>
                <dt class="eyebrow mb-2">{path.label}</dt>
                <dd class="mono break-all text-body-small leading-relaxed">
                    {path.value}
                </dd>
            </div>
        {/each}
    </dl>
    <div
        class="flex items-start justify-between gap-4 border-t border-border-tertiary py-5"
    >
        <div class="min-w-0">
            <h3 class="text-label-medium">CLI working directory</h3>
            <p class="mono mt-2 break-all text-body-small">
                {app.options.directory}
            </p>
            <p class="mt-2 text-caption leading-relaxed text-text-secondary">
                Saved on this device for all configurations, separately from the
                TOML.
                {#if app.dirty}Save or discard the configuration draft before
                    changing it.{/if}
            </p>
        </div>
        <Button
            scale="s"
            kind="neutral"
            appearance="outline-fill"
            disabled={app.locked || app.dirty}
            onclick={() => startEdit("directory")}
        >
            Change working directory</Button
        >
    </div>
{/if}
<Dialog
    bind:open
    width="wide"
    scrollable
    dismissible={!app.locked}
    heading={mode === "property"
        ? index === null
            ? "Add build property"
            : "Edit build property"
        : mode === "paths"
          ? "Edit workspace paths"
          : "Change CLI working directory"}
    description={mode === "directory"
        ? "Reconnect using this directory. Relative repository and cache paths will resolve from here."
        : "Apply to the draft, then Save changes to write the configuration file."}
>
    <form
        id="configuration-fields"
        class="space-y-4 py-2"
        onsubmit={(event) => {
            event.preventDefault();
            submit();
        }}
    >
        {#if mode === "property"}
            <Input
                label="Property name"
                variant="general"
                bind:value={property.name}
                clearable={false}
                required
                pattern="[A-Za-z_][A-Za-z0-9_.\-]*"
                hint="Use a unique MSBuild property name, such as TreatWarningsAsErrors."
                disabled={app.locked}
            />
            <label class="block space-y-2 text-body-small">
                <span class="block">Property type</span>
                <select
                    class="field-select"
                    value={property.datatype}
                    disabled={app.locked}
                    onchange={(event) => {
                        const value = event.currentTarget.value;
                        if (
                            value !== "string" &&
                            value !== "boolean" &&
                            value !== "path"
                        )
                            return;
                        property.datatype = value;
                        property.default =
                            value === "boolean"
                                ? String(property.default) === "true"
                                : String(property.default);
                    }}
                >
                    <option value="string">String</option>
                    <option value="boolean">Boolean</option>
                    <option value="path">Path</option>
                </select>
            </label>
            {#if property.datatype === "boolean"}
                <label class="block space-y-2 text-body-small">
                    <span class="block">Default value</span>
                    <select
                        class="field-select"
                        value={String(property.default)}
                        disabled={app.locked}
                        onchange={(event) =>
                            (property.default =
                                event.currentTarget.value === "true")}
                    >
                        {#if !["true", "false"].includes(String(property.default))}
                            <option value={String(property.default)}
                                >Existing: {String(property.default) ||
                                    "(empty)"}</option
                            >
                        {/if}
                        <option value="true">true</option>
                        <option value="false">false</option>
                    </select>
                </label>
            {:else}
                <div class="flex items-end gap-2">
                    <Input
                        label="Default value"
                        variant="general"
                        value={String(property.default)}
                        oninput={(event) =>
                            (property.default = event.currentTarget.value)}
                        clearable={false}
                        disabled={app.locked}
                        class="min-w-0 flex-1"
                    />
                    {#if property.datatype === "path"}
                        <Button
                            kind="neutral"
                            appearance="outline-fill"
                            icon="folder-open"
                            label="Browse for property directory"
                            disabled={app.locked}
                            onclick={() => browse("property")}
                        />
                    {/if}
                </div>
            {/if}
        {:else if mode === "paths"}
            <div class="flex items-end gap-2">
                <Input
                    label="Repository directory"
                    variant="general"
                    bind:value={repodir}
                    required
                    clearable={false}
                    disabled={app.locked}
                    class="min-w-0 flex-1"
                />
                <Button
                    kind="neutral"
                    appearance="outline-fill"
                    icon="folder-open"
                    label="Browse for repository directory"
                    disabled={app.locked}
                    onclick={() => browse("repodir")}
                />
            </div>
            <div class="flex items-end gap-2">
                <Input
                    label="NuGet cache directory (optional)"
                    variant="general"
                    bind:value={cache}
                    clearable={false}
                    disabled={app.locked}
                    class="min-w-0 flex-1"
                    hint="Leave empty to use the default NuGet cache."
                />
                <Button
                    kind="neutral"
                    appearance="outline-fill"
                    icon="folder-open"
                    label="Browse for NuGet cache directory"
                    disabled={app.locked}
                    onclick={() => browse("cache")}
                />
            </div>
        {:else}
            <div class="flex items-end gap-2">
                <Input
                    label="CLI working directory"
                    variant="general"
                    bind:value={directory}
                    required
                    clearable={false}
                    disabled={app.locked}
                    class="min-w-0 flex-1"
                />
                <Button
                    kind="neutral"
                    appearance="outline-fill"
                    icon="folder-open"
                    label="Browse for working directory"
                    disabled={app.locked}
                    onclick={() => browse("directory")}
                />
            </div>
        {/if}
        {#if editError}<p
                role="alert"
                class="text-body-small text-status-danger"
            >
                {editError}
            </p>{/if}
    </form>
    {#snippet actions()}
        <Button
            scale="s"
            kind="neutral"
            appearance="transparent"
            disabled={app.locked}
            onclick={() => (open = false)}>Cancel</Button
        >
        <Button
            scale="s"
            type="submit"
            form="configuration-fields"
            disabled={app.locked ||
                (mode === "paths" && !repodir.trim()) ||
                (mode === "directory" && !directory.trim()) ||
                (mode === "property" && !property.name.trim())}
        >
            {mode === "directory"
                ? "Save & reconnect"
                : "Apply to draft"}</Button
        >
    {/snippet}
</Dialog>
