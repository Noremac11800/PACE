import { defaultDotnetOptions } from "$lib/domain/dotnet";

// Keep options across navigation without leaking overrides to another config.
export const dotnetForm = $state({
    configPath: "",
    options: defaultDotnetOptions(),
    propertiesOpen: false,
});
