<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Chip from "$lib/components/ui/Chip.svelte";
    import Tabs from "$lib/components/ui/Tabs.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import ConfigurationEditor from "$lib/components/ConfigurationEditor.svelte";
    let tab = $state("source");
</script>

<PageHeader
    title="Configuration"
    description="Edit build properties, workspace paths, or TOML source. All changes share one draft and are validated by pacev2 before saving."
>
    {#snippet actions()}
        <Button
            scale="s"
            kind="neutral"
            appearance="outline-fill"
            iconStart="copy"
            disabled={app.locked}
            onclick={() => app.save(true)}>Save a copy</Button
        >
        <Button
            scale="s"
            iconStart="save"
            disabled={app.locked || !app.dirty}
            onclick={() => app.save()}>Save changes</Button
        >
    {/snippet}
</PageHeader>
<section class="panel overflow-hidden">
    <div class="panel-heading">
        <div class="flex min-w-0 items-center gap-3">
            <Icon name="file-code" class="shrink-0 text-brand" />
            <div class="min-w-0">
                <h2 class="text-title-small">{app.name}.toml</h2>
                <p
                    class="mt-1 truncate text-caption text-text-tertiary"
                    title={app.workspace?.path}
                >
                    {app.workspace?.path}
                </p>
            </div>
        </div>
        <Chip
            label={app.dirty ? "Unsaved changes" : "Saved"}
            scale="s"
            tone={app.dirty ? "yellow" : "green"}
        />
    </div>
    <div class="px-5">
        <Tabs
            label="Configuration views"
            bind:value={tab}
            appearance="scrollable"
            tabs={[
                { value: "source", label: "TOML source" },
                { value: "properties", label: "Build properties" },
                { value: "paths", label: "Workspace paths" },
            ]}
        >
            {#snippet panel(value)}
                {#if value === "source"}
                    <label class="sr-only" for="config-source"
                        >TOML configuration source</label
                    >
                    <textarea
                        id="config-source"
                        class="mono min-h-96 w-full resize-y rounded-[2px] border border-border-input bg-foreground-secondary p-4 text-body-small leading-relaxed text-text-primary outline-offset-2"
                        spellcheck="false"
                        autocapitalize="off"
                        autocomplete="off"
                        bind:value={app.draft}
                        disabled={app.locked}></textarea>
                    <div
                        class="flex flex-wrap items-center justify-between gap-3 py-4"
                    >
                        <p class="text-caption text-text-tertiary">
                            Comments and formatting are preserved. Invalid
                            changes are never saved.
                        </p>
                        <div class="flex gap-2">
                            <Button
                                scale="s"
                                kind="neutral"
                                appearance="transparent"
                                iconStart="refresh"
                                disabled={app.locked}
                                onclick={() => app.load(app.workspace?.path)}
                                >Reload from disk</Button
                            ><Button
                                scale="s"
                                kind="neutral"
                                appearance="outline-fill"
                                iconStart="check-circle"
                                disabled={app.locked}
                                onclick={() => app.validate()}>Validate</Button
                            >
                        </div>
                    </div>
                {:else}
                    <ConfigurationEditor
                        section={value === "properties"
                            ? "properties"
                            : "paths"}
                    />
                {/if}
            {/snippet}
        </Tabs>
    </div>
</section>
<div
    class="mt-5 flex items-start gap-3 text-body-small leading-relaxed text-text-secondary"
>
    <Icon name="information" size={18} class="mt-0.5 text-status-info" />
    <p>
        PACE shares configuration history with the CLI in <code
            >~/.pace/settings.json</code
        >. Opening a file makes it the active configuration for both. Older
        PACE-only fields must be removed or migrated to the pacev2 schema before
        loading.
    </p>
</div>
