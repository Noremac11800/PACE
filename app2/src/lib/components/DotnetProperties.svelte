<script lang="ts">
    import type { BuildProperty } from "$lib/domain/dotnet";
    import { app } from "$lib/state/app.svelte";
    import { chooseDirectory } from "$lib/services/desktop";
    import Button from "./ui/Button.svelte";
    import Checkbox from "./ui/Checkbox.svelte";
    import Input from "./ui/Input.svelte";

    let {
        properties,
        values = $bindable<Record<string, string>>({}),
        disabled = false,
        compact = false,
    }: {
        properties: BuildProperty[];
        values?: Record<string, string>;
        disabled?: boolean;
        compact?: boolean;
    } = $props();

    function enable(property: BuildProperty, enabled: boolean) {
        if (enabled) {
            values = { ...values, [property.name]: String(property.default) };
        } else {
            const updated = { ...values };
            delete updated[property.name];
            values = updated;
        }
    }

    async function browse(name: string) {
        try {
            const path = await chooseDirectory();
            if (path) values = { ...values, [name]: path };
        } catch (error) {
            app.error(error);
        }
    }
</script>

<section class={compact ? "border-t border-border-tertiary" : "panel"}>
    {#if !compact}
        <div class="panel-heading">
            <div>
                <h2 class="text-title-small">MSBuild properties</h2>
                <p class="mt-1 text-caption leading-relaxed text-text-tertiary">
                    Enable a property to pass it explicitly to this command.
                    Disabled properties use the project's own settings.
                </p>
            </div>
        </div>
    {/if}
    <div class="divide-y divide-border-tertiary">
        {#each properties as property, index (`${index}-${property.name}`)}
            {@const enabled = Object.hasOwn(values, property.name)}
            <div
                class={compact
                    ? "grid gap-3 p-4"
                    : "grid items-center gap-4 p-5 lg:grid-cols-[minmax(180px,1fr)_minmax(0,1.5fr)]"}
            >
                <div class="min-w-0">
                    <Checkbox
                        label={property.name}
                        checked={enabled}
                        {disabled}
                        onchange={(event) =>
                            enable(property, event.currentTarget.checked)}
                        class="break-all text-body-small"
                    />
                    <p class="ml-6 mt-1 text-caption text-text-tertiary">
                        {property.datatype} · Config default: {String(
                            property.default,
                        ) || "(empty)"}
                    </p>
                </div>
                {#if property.datatype === "boolean"}
                    <select
                        class="field-select"
                        aria-label={`${property.name} value`}
                        value={values[property.name] ??
                            String(property.default)}
                        disabled={disabled || !enabled}
                        onchange={(event) =>
                            (values = {
                                ...values,
                                [property.name]: event.currentTarget.value,
                            })}
                    >
                        <option value="true">true</option>
                        <option value="false">false</option>
                    </select>
                {:else}
                    <div class="flex min-w-0 items-center gap-2">
                        <Input
                            label={`${property.name} value`}
                            hideLabel
                            variant="general"
                            clearable={false}
                            value={values[property.name] ??
                                String(property.default)}
                            disabled={disabled || !enabled}
                            placeholder={property.datatype === "path"
                                ? "Path to a directory"
                                : "Property value"}
                            oninput={(event) =>
                                (values = {
                                    ...values,
                                    [property.name]: event.currentTarget.value,
                                })}
                            class="min-w-0 flex-1"
                        />
                        {#if property.datatype === "path"}<Button
                                kind="neutral"
                                appearance="outline-fill"
                                scale="s"
                                icon="folder-open"
                                label={`Browse for ${property.name}`}
                                disabled={disabled || !enabled}
                                onclick={() => browse(property.name)}
                            />{/if}
                    </div>
                {/if}
            </div>
        {/each}
    </div>
</section>
