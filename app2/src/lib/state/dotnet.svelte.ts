import { defaultDotnetOptions } from "$lib/domain/dotnet";

// Keep a command's options when switching to activity and back, without leaking overrides to another config.
export const dotnetForm = $state({
    configPath: "",
    options: defaultDotnetOptions(),
});
