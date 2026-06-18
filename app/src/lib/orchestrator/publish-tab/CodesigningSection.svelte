<script lang="ts">
  import { ChevronDown } from "@lucide/svelte";
  import type {
    CodesigningData,
    AndroidCodesignInfo,
  } from "$lib/orchestrator/publishing.svelte";
  import type { Platform } from "./platforms";

  let {
    selectedPlatforms,
    codesigningConfig,
    androidCodesignInfo,
    iosBundleId = $bindable("*"),
    windowsKey = $bindable("*"),
    androidKey = $bindable("*"),
  }: {
    selectedPlatforms: Platform[];
    codesigningConfig: CodesigningData;
    androidCodesignInfo: AndroidCodesignInfo;
    iosBundleId?: string;
    windowsKey?: string;
    androidKey?: string;
  } = $props();

  const iosBundleIds = $derived(Object.keys(codesigningConfig.ios));
  const windowsKeys = $derived(Object.keys(codesigningConfig.windows));
  const androidKeys = $derived(Object.keys(codesigningConfig.android));
</script>

<div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
  <span class="font-semibold text-surface-900-100 text-sm">Codesigning</span>
  <div class="grid gap-3">
    {#if selectedPlatforms.includes("ios")}
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-600-400" for="ios-bundle"
          >iOS Bundle</label
        >
        <div class="relative">
          <select
            id="ios-bundle"
            bind:value={iosBundleId}
            class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-1.5 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
            style="background-image:none"
          >
            <option value="*">— Default (*) —</option>
            {#each iosBundleIds.filter((id) => id !== "*") as bundleId (bundleId)}
              <option value={bundleId}>{bundleId}</option>
            {/each}
          </select>
          <ChevronDown
            size={14}
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
          />
        </div>
      </div>
    {/if}

    {#if selectedPlatforms.includes("windows")}
      <div class="flex flex-col gap-2">
        <div class="flex flex-col gap-1">
          <label
            class="text-xs font-medium text-surface-600-400"
            for="windows-cert">Windows Cert</label
          >
          <div class="relative">
            <select
              id="windows-cert"
              bind:value={windowsKey}
              class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-1.5 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
              style="background-image:none"
            >
              <option value="*">— Default (*) —</option>
              {#each windowsKeys.filter((k) => k !== "*") as key (key)}
                <option value={key}>{key}</option>
              {/each}
            </select>
            <ChevronDown
              size={14}
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
            />
          </div>
        </div>
        {#if windowsKey && windowsKey !== "*"}
          {@const config = codesigningConfig.windows[windowsKey]}
          <div class="flex flex-col gap-1 text-xs">
            <span class="font-medium text-surface-600-400">Thumbprint</span>
            <span
              class="px-2 py-1.5 bg-surface-100-900 rounded border border-surface-300-700 font-mono break-all {config?.PackageCertificateThumbprint
                ? 'text-surface-900-100'
                : 'text-surface-500-400 italic'}"
            >
              {config?.PackageCertificateThumbprint || "Not configured"}
            </span>
          </div>
        {/if}
      </div>
    {/if}

    {#if selectedPlatforms.includes("android")}
      <div class="flex flex-col gap-2">
        <div class="flex flex-col gap-1">
          <label
            class="text-xs font-medium text-surface-600-400"
            for="android-keystore">Android Keystore</label
          >
          <div class="relative">
            <select
              id="android-keystore"
              bind:value={androidKey}
              class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-1.5 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
              style="background-image:none"
            >
              <option value="*">— Default (*) —</option>
              {#each androidKeys.filter((k) => k !== "*") as key (key)}
                <option value={key}>{key}</option>
              {/each}
            </select>
            <ChevronDown
              size={14}
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
            />
          </div>
        </div>
        {#if androidKey && androidKey !== "*"}
          {@const config = codesigningConfig.android[androidKey]}
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="flex flex-col gap-1">
              <span class="font-medium text-surface-600-400">Alias</span>
              <span
                class="px-2 py-1.5 bg-surface-100-900 rounded border border-surface-300-700 {androidCodesignInfo?.Alias
                  ? 'text-surface-900-100'
                  : 'text-surface-500-400 italic'}"
              >
                {androidCodesignInfo?.Alias || "Not loaded"}
              </span>
            </div>
            <div class="flex flex-col gap-1">
              <span class="font-medium text-surface-600-400">Key Pass</span>
              <span
                class="px-2 py-1.5 bg-surface-100-900 rounded border border-surface-300-700 {androidCodesignInfo?.KeyPass
                  ? 'text-surface-900-100'
                  : 'text-surface-500-400 italic'}"
              >
                {androidCodesignInfo?.KeyPass ? "••••••" : "Not loaded"}
              </span>
            </div>
            <div class="flex flex-col gap-1 col-span-2">
              <span class="font-medium text-surface-600-400">Store Pass</span>
              <span
                class="px-2 py-1.5 bg-surface-100-900 rounded border border-surface-300-700 {androidCodesignInfo?.StorePass
                  ? 'text-surface-900-100'
                  : 'text-surface-500-400 italic'}"
              >
                {androidCodesignInfo?.StorePass ? "••••••" : "Not loaded"}
              </span>
            </div>
            {#if !androidCodesignInfo?.Alias && config?.CodesignInfoTxtPath}
              <div class="col-span-2 text-xs text-surface-500-400">
                Info file: {config.CodesignInfoTxtPath}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
