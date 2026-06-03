<script lang="ts">
  import { onMount } from "svelte";
  import {
    Plus,
    Trash2,
    Apple,
    Monitor,
    Smartphone,
    FolderOpen,
    Check,
    AlertCircle,
    Eye,
    EyeOff,
    Upload,
    FileSignature,
  } from "@lucide/svelte";
  import {
    BaseDirectory,
    readTextFile,
    writeTextFile,
    exists,
  } from "@tauri-apps/plugin-fs";
  import { open } from "@tauri-apps/plugin-dialog";
  import { openPath } from "@tauri-apps/plugin-opener";
  import { homeDir, join } from "@tauri-apps/api/path";

  // Types
  type iOSConfig = { CodesignKey: string; CodesignProvision: string };
  type WindowsConfig = { PackageCertificateThumbprint: string };
  type AndroidConfig = { KeystorePath: string; CodesignInfoTxtPath: string };
  type CodesigningData = {
    ios: Record<string, iOSConfig>;
    windows: Record<string, WindowsConfig>;
    android: Record<string, AndroidConfig>;
  };

  const defaultConfig: CodesigningData = {
    ios: { "*": { CodesignKey: "", CodesignProvision: "" } },
    windows: { "*": { PackageCertificateThumbprint: "" } },
    android: { "*": { KeystorePath: "", CodesignInfoTxtPath: "" } },
  };

  // State
  let config = $state<CodesigningData>(defaultConfig);
  let importStatus = $state<"idle" | "importing" | "success" | "error">("idle");
  let importError = $state<string>("");
  let activeTab = $state<"ios" | "windows" | "android">("ios");
  let iosBundleIds = $state<string[]>(["*"]);
  let showProvision = $state<Record<string, boolean>>({});
  let showThumbprint = $state<Record<string, boolean>>({});
  let windowsKeys = $state<string[]>(["*"]);
  let androidKeys = $state<string[]>(["*"]);

  const CODESIGNING_PATH = ".pace/codesigning.json";

  onMount(async () => {
    await loadConfig();
  });

  async function loadConfig() {
    try {
      const fileExists = await exists(CODESIGNING_PATH, {
        baseDir: BaseDirectory.Home,
      });
      if (fileExists) {
        const content = await readTextFile(CODESIGNING_PATH, {
          baseDir: BaseDirectory.Home,
        });
        const parsed = JSON.parse(content) as CodesigningData;
        config = { ...defaultConfig, ...parsed };
        if (!config.ios)
          config.ios = { "*": { CodesignKey: "", CodesignProvision: "" } };
        if (!config.windows)
          config.windows = { "*": { PackageCertificateThumbprint: "" } };
        if (!config.android)
          config.android = {
            "*": { KeystorePath: "", CodesignInfoTxtPath: "" },
          };
        if (!config.ios["*"])
          config.ios["*"] = { CodesignKey: "", CodesignProvision: "" };
        if (!config.windows["*"])
          config.windows["*"] = { PackageCertificateThumbprint: "" };
        if (!config.android["*"])
          config.android["*"] = { KeystorePath: "", CodesignInfoTxtPath: "" };
        iosBundleIds = Object.keys(config.ios);
        windowsKeys = Object.keys(config.windows);
        androidKeys = Object.keys(config.android);
      }
    } catch (error) {
      console.error("Failed to load codesigning config:", error);
    }
  }

  async function saveConfig() {
    try {
      await writeTextFile(CODESIGNING_PATH, JSON.stringify(config, null, 2), {
        baseDir: BaseDirectory.Home,
      });
    } catch (error) {
      console.error("Failed to save codesigning config:", error);
    }
  }

  async function openCodesigningFolder() {
    try {
      const home = await homeDir();
      await openPath(await join(home, ".pace"));
    } catch (error) {
      console.error("Failed to open codesigning folder:", error);
    }
  }

  function validateCodesigningData(data: unknown): {
    valid: boolean;
    error?: string;
  } {
    if (typeof data !== "object" || data === null)
      return { valid: false, error: "File must contain a JSON object" };
    const d = data as Record<string, unknown>;
    const hasIOS = d.ios !== undefined;
    const hasWindows = d.windows !== undefined;
    const hasAndroid = d.android !== undefined;
    if (!hasIOS && !hasWindows && !hasAndroid)
      return {
        valid: false,
        error: "Must contain at least one of: ios, windows, or android",
      };
    const allowedKeys = ["ios", "windows", "android"];
    const unknownKeys = Object.keys(d).filter((k) => !allowedKeys.includes(k));
    if (unknownKeys.length > 0)
      return { valid: false, error: `Unknown keys: ${unknownKeys.join(", ")}` };
    if (hasIOS) {
      if (typeof d.ios !== "object" || d.ios === null)
        return { valid: false, error: "ios must be an object" };
      const iosEntries = Object.entries(d.ios);
      if (iosEntries.length === 0)
        return { valid: false, error: "ios must have at least one entry" };
      for (const [key, value] of iosEntries) {
        if (typeof value !== "object" || value === null)
          return { valid: false, error: `ios["${key}"] must be an object` };
        const v = value as Record<string, unknown>;
        const unknownIOSKeys = Object.keys(v).filter(
          (k) => !["CodesignKey", "CodesignProvision"].includes(k),
        );
        if (unknownIOSKeys.length > 0)
          return {
            valid: false,
            error: `ios["${key}"] has unknown keys: ${unknownIOSKeys.join(", ")}`,
          };
        if (v.CodesignKey !== undefined && typeof v.CodesignKey !== "string")
          return {
            valid: false,
            error: `ios["${key}"].CodesignKey must be a string`,
          };
        if (
          v.CodesignProvision !== undefined &&
          typeof v.CodesignProvision !== "string"
        )
          return {
            valid: false,
            error: `ios["${key}"].CodesignProvision must be a string`,
          };
      }
    }
    if (hasWindows) {
      if (typeof d.windows !== "object" || d.windows === null)
        return { valid: false, error: "windows must be an object" };
      const windowsEntries = Object.entries(d.windows);
      if (windowsEntries.length === 0)
        return { valid: false, error: "windows must have at least one entry" };
      for (const [key, value] of windowsEntries) {
        if (typeof value !== "object" || value === null)
          return { valid: false, error: `windows["${key}"] must be an object` };
        const v = value as Record<string, unknown>;
        const unknownWindowsKeys = Object.keys(v).filter(
          (k) => !["PackageCertificateThumbprint"].includes(k),
        );
        if (unknownWindowsKeys.length > 0)
          return {
            valid: false,
            error: `windows["${key}"] has unknown keys: ${unknownWindowsKeys.join(", ")}`,
          };
        if (
          v.PackageCertificateThumbprint !== undefined &&
          typeof v.PackageCertificateThumbprint !== "string"
        )
          return {
            valid: false,
            error: `windows["${key}"].PackageCertificateThumbprint must be a string`,
          };
      }
    }
    if (hasAndroid) {
      if (typeof d.android !== "object" || d.android === null)
        return { valid: false, error: "android must be an object" };
      const androidEntries = Object.entries(d.android);
      if (androidEntries.length === 0)
        return { valid: false, error: "android must have at least one entry" };
      for (const [key, value] of androidEntries) {
        if (typeof value !== "object" || value === null)
          return { valid: false, error: `android["${key}"] must be an object` };
        const v = value as Record<string, unknown>;
        const unknownAndroidKeys = Object.keys(v).filter(
          (k) => !["KeystorePath", "CodesignInfoTxtPath"].includes(k),
        );
        if (unknownAndroidKeys.length > 0)
          return {
            valid: false,
            error: `android["${key}"] has unknown keys: ${unknownAndroidKeys.join(", ")}`,
          };
        if (v.KeystorePath !== undefined && typeof v.KeystorePath !== "string")
          return {
            valid: false,
            error: `android["${key}"].KeystorePath must be a string`,
          };
        if (
          v.CodesignInfoTxtPath !== undefined &&
          typeof v.CodesignInfoTxtPath !== "string"
        )
          return {
            valid: false,
            error: `android["${key}"].CodesignInfoTxtPath must be a string`,
          };
      }
    }
    return { valid: true };
  }

  async function importConfig() {
    importStatus = "importing";
    importError = "";
    try {
      const selected = await open({
        multiple: false,
        directory: false,
        filters: [{ name: "JSON", extensions: ["json"] }],
      });
      if (!selected || typeof selected !== "string") {
        importStatus = "idle";
        return;
      }
      const content = await readTextFile(selected);
      let parsed: unknown;
      try {
        parsed = JSON.parse(content);
      } catch {
        importError = "Invalid JSON file";
        importStatus = "error";
        setTimeout(() => (importStatus = "idle"), 3000);
        return;
      }
      const validation = validateCodesigningData(parsed);
      if (!validation.valid) {
        importError = validation.error || "Invalid codesigning.json structure";
        importStatus = "error";
        setTimeout(() => (importStatus = "idle"), 3000);
        return;
      }
      const parsedConfig = parsed as CodesigningData;
      const merged: CodesigningData = { ...defaultConfig, ...parsedConfig };
      config = merged;
      iosBundleIds = Object.keys(config.ios);
      windowsKeys = Object.keys(config.windows);
      androidKeys = Object.keys(config.android);
      await writeTextFile(CODESIGNING_PATH, JSON.stringify(config, null, 2), {
        baseDir: BaseDirectory.Home,
      });
      importStatus = "success";
      setTimeout(() => (importStatus = "idle"), 2000);
    } catch (error) {
      console.error("Failed to import config:", error);
      importError = error instanceof Error ? error.message : "Unknown error";
      importStatus = "error";
      setTimeout(() => (importStatus = "idle"), 3000);
    }
  }

  function addiOSBundleId() {
    const newId = "com.example.app";
    if (!iosBundleIds.includes(newId)) {
      iosBundleIds = [...iosBundleIds, newId];
      config.ios[newId] = { CodesignKey: "", CodesignProvision: "" };
      saveConfig();
    }
  }
  function removeiOSBundleId(bundleId: string) {
    if (bundleId === "*") return;
    iosBundleIds = iosBundleIds.filter((id) => id !== bundleId);
    delete config.ios[bundleId];
    config = { ...config };
    saveConfig();
  }
  function addWindowsKey() {
    const newKey = "new-cert";
    if (!windowsKeys.includes(newKey)) {
      windowsKeys = [...windowsKeys, newKey];
      config.windows[newKey] = { PackageCertificateThumbprint: "" };
      saveConfig();
    }
  }
  function removeWindowsKey(key: string) {
    if (key === "*") return;
    windowsKeys = windowsKeys.filter((k) => k !== key);
    delete config.windows[key];
    config = { ...config };
    saveConfig();
  }
  function updateWindowsKey(oldKey: string, newKey: string) {
    if (oldKey === newKey || newKey === "*" || windowsKeys.includes(newKey))
      return;
    const index = windowsKeys.indexOf(oldKey);
    if (index === -1) return;
    const oldConfig = config.windows[oldKey];
    delete config.windows[oldKey];
    config.windows[newKey] = oldConfig;
    windowsKeys[index] = newKey;
    windowsKeys = [...windowsKeys];
    config = { ...config };
    saveConfig();
  }
  function addAndroidKey() {
    const newKey = "new-keystore";
    if (!androidKeys.includes(newKey)) {
      androidKeys = [...androidKeys, newKey];
      config.android[newKey] = { KeystorePath: "", CodesignInfoTxtPath: "" };
      saveConfig();
    }
  }
  function removeAndroidKey(key: string) {
    if (key === "*") return;
    androidKeys = androidKeys.filter((k) => k !== key);
    delete config.android[key];
    config = { ...config };
    saveConfig();
  }
  function updateAndroidKey(oldKey: string, newKey: string) {
    if (oldKey === newKey || newKey === "*" || androidKeys.includes(newKey))
      return;
    const index = androidKeys.indexOf(oldKey);
    if (index === -1) return;
    const oldConfig = config.android[oldKey];
    delete config.android[oldKey];
    config.android[newKey] = oldConfig;
    androidKeys[index] = newKey;
    androidKeys = [...androidKeys];
    config = { ...config };
    saveConfig();
  }
  function updateiOSBundleId(oldId: string, newId: string) {
    if (oldId === newId || newId === "*" || iosBundleIds.includes(newId))
      return;
    const index = iosBundleIds.indexOf(oldId);
    if (index === -1) return;
    const oldConfig = config.ios[oldId];
    delete config.ios[oldId];
    config.ios[newId] = oldConfig;
    iosBundleIds[index] = newId;
    iosBundleIds = [...iosBundleIds];
    config = { ...config };
    saveConfig();
  }
  async function pickFile(
    key: keyof AndroidConfig,
    target: "*" | string = "*",
  ) {
    const selected = await open({ multiple: false, directory: false });
    if (selected && typeof selected === "string") {
      config.android[target][key] = selected;
      config = { ...config };
      saveConfig();
    }
  }
  const tabConfig = {
    ios: { icon: Apple, label: "iOS", color: "text-surface-900-100" },
    windows: { icon: Monitor, label: "Windows", color: "text-surface-900-100" },
    android: { icon: Smartphone, label: "Android", color: "text-success-500" },
  };
</script>

<div class="h-full flex flex-col p-4">
  <div class="flex items-center gap-2 mb-4">
    <FileSignature size={18} class="text-primary-500" />
    <span class="font-semibold text-surface-900-100"
      >Code Signing Configuration</span
    >
  </div>

  <div
    class="card bg-surface-50-950 p-6 flex flex-col gap-4 flex-1 overflow-hidden"
  >
    <!-- Import/Open buttons -->
    <div class="flex items-center gap-2">
      <button
        class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
        onclick={importConfig}
        disabled={importStatus === "importing"}
        title="Import codesigning.json"
      >
        {#if importStatus === "importing"}
          <span class="animate-spin">⟳</span> Importing...
        {:else if importStatus === "success"}
          <Check size={14} /> Imported
        {:else if importStatus === "error"}
          <AlertCircle size={14} /> Import failed
        {:else}
          <Upload size={14} /> Import
        {/if}
      </button>
      <button
        class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
        onclick={openCodesigningFolder}
        title="Open ~/.pace folder"
      >
        <FolderOpen size={14} /> Open folder
      </button>
    </div>

    {#if importStatus === "error" && importError}
      <div class="px-4 py-2 bg-error-500/10 border border-error-500/20 rounded">
        <div class="flex items-center gap-2 text-sm text-error-500">
          <AlertCircle size={16} />
          <span>{importError}</span>
        </div>
      </div>
    {/if}

    <!-- Tabs -->
    <div class="flex border-b border-surface-200-800">
      {#each Object.entries(tabConfig) as [tabId, { icon: Icon, label, color }]}
        <button
          class="flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap {activeTab ===
          tabId
            ? 'text-primary-500 border-b-2 border-primary-500 bg-surface-100-900/50'
            : 'text-surface-600-400 hover:text-surface-900-100 hover:bg-surface-100-900/30'}"
          onclick={() => (activeTab = tabId as typeof activeTab)}
        >
          <Icon
            size={16}
            class={activeTab === tabId ? "text-primary-500" : color}
          />
          {label}
        </button>
      {/each}
    </div>

    <!-- Tab Content -->
    <div class="flex-1 overflow-y-auto relative">
      <div
        class="absolute inset-0 flex flex-col gap-4"
        class:hidden={activeTab !== "ios"}
      >
        <p class="text-sm text-surface-600-400">
          Configure code signing settings for iOS apps. The "*" entry is used as
          the default for all bundle IDs.
        </p>
        {#each iosBundleIds as bundleId}
          <div
            class="flex flex-col gap-3 border-b border-surface-200-800 pb-4 last:border-0"
          >
            <div class="flex items-center gap-2">
              <span
                class="text-xs font-medium text-surface-600-400 uppercase tracking-wide"
                >Bundle ID</span
              >
              {#if bundleId !== "*"}
                <button
                  class="ml-auto btn-icon text-error-500 hover:text-error-600 transition-colors"
                  onclick={() => removeiOSBundleId(bundleId)}
                  title="Remove bundle ID"><Trash2 size={14} /></button
                >
              {/if}
            </div>
            <input
              type="text"
              class="input font-mono text-sm"
              value={bundleId}
              disabled={bundleId === "*"}
              placeholder="com.example.app"
              onchange={(e) =>
                updateiOSBundleId(
                  bundleId,
                  (e.target as HTMLInputElement).value,
                )}
            />
            <div class="flex flex-col gap-1">
              <label
                for="codesign-key-{bundleId}"
                class="text-xs font-medium text-surface-600-400"
                >Codesign Key</label
              >
              <input
                id="codesign-key-{bundleId}"
                type="text"
                class="input text-sm"
                placeholder="iPhone Distribution: Company Name"
                value={config.ios[bundleId]?.CodesignKey || ""}
                oninput={(e) => {
                  config.ios[bundleId].CodesignKey = (
                    e.target as HTMLInputElement
                  ).value;
                  config = { ...config };
                  saveConfig();
                }}
              />
            </div>
            <div class="flex flex-col gap-1">
              <div class="flex items-center justify-between">
                <label
                  for="codesign-provision-{bundleId}"
                  class="text-xs font-medium text-surface-600-400"
                  >Codesign Provision</label
                >
                <button
                  class="btn-icon text-surface-500-400 hover:text-surface-700-300"
                  onclick={() =>
                    (showProvision[bundleId] = !showProvision[bundleId])}
                  title={showProvision[bundleId] ? "Hide" : "Show"}
                >
                  {#if showProvision[bundleId]}<EyeOff size={14} />{:else}<Eye
                      size={14}
                    />{/if}
                </button>
              </div>
              <input
                id="codesign-provision-{bundleId}"
                type={showProvision[bundleId] ? "text" : "password"}
                class="input text-sm"
                placeholder="Provisioning profile identifier"
                value={config.ios[bundleId]?.CodesignProvision || ""}
                oninput={(e) => {
                  config.ios[bundleId].CodesignProvision = (
                    e.target as HTMLInputElement
                  ).value;
                  config = { ...config };
                  saveConfig();
                }}
              />
            </div>
          </div>
        {/each}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2 self-start"
          onclick={addiOSBundleId}
        >
          <Plus size={14} /> Add Bundle ID
        </button>
      </div>

      <div
        class="absolute inset-0 flex flex-col gap-4"
        class:hidden={activeTab !== "windows"}
      >
        <p class="text-sm text-surface-600-400">
          Configure code signing settings for Windows apps using certificate
          thumbprint. The "*" entry is used as the default.
        </p>
        {#each windowsKeys as key}
          <div
            class="flex flex-col gap-3 border-b border-surface-200-800 pb-4 last:border-0"
          >
            <div class="flex items-center gap-2">
              <span
                class="text-xs font-medium text-surface-600-400 uppercase tracking-wide"
                >Certificate Name</span
              >
              {#if key !== "*"}
                <button
                  class="ml-auto btn-icon text-error-500 hover:text-error-600 transition-colors"
                  onclick={() => removeWindowsKey(key)}
                  title="Remove certificate"><Trash2 size={14} /></button
                >
              {/if}
            </div>
            <input
              type="text"
              class="input font-mono text-sm"
              value={key}
              disabled={key === "*"}
              placeholder="cert-name"
              onchange={(e) =>
                updateWindowsKey(key, (e.target as HTMLInputElement).value)}
            />
            <div class="flex flex-col gap-1">
              <div class="flex items-center justify-between">
                <label
                  for="thumbprint-{key}"
                  class="text-xs font-medium text-surface-600-400"
                  >Package Certificate Thumbprint</label
                >
                <button
                  class="btn-icon text-surface-500-400 hover:text-surface-700-300"
                  onclick={() => (showThumbprint[key] = !showThumbprint[key])}
                  title={showThumbprint[key] ? "Hide" : "Show"}
                >
                  {#if showThumbprint[key]}<EyeOff size={14} />{:else}<Eye
                      size={14}
                    />{/if}
                </button>
              </div>
              <input
                id="thumbprint-{key}"
                type={showThumbprint[key] ? "text" : "password"}
                class="input font-mono text-sm"
                placeholder="Certificate thumbprint hash"
                value={config.windows[key]?.PackageCertificateThumbprint || ""}
                oninput={(e) => {
                  config.windows[key].PackageCertificateThumbprint = (
                    e.target as HTMLInputElement
                  ).value;
                  config = { ...config };
                  saveConfig();
                }}
              />
            </div>
          </div>
        {/each}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2 self-start"
          onclick={addWindowsKey}
        >
          <Plus size={14} /> Add Certificate
        </button>
      </div>

      <div
        class="absolute inset-0 flex flex-col gap-4"
        class:hidden={activeTab !== "android"}
      >
        <p class="text-sm text-surface-600-400">
          Configure code signing settings for Android apps using keystore files.
          The "*" entry is used as the default.
        </p>
        {#each androidKeys as key}
          <div
            class="flex flex-col gap-3 border-b border-surface-200-800 pb-4 last:border-0"
          >
            <div class="flex items-center gap-2">
              <span
                class="text-xs font-medium text-surface-600-400 uppercase tracking-wide"
                >Keystore Name</span
              >
              {#if key !== "*"}
                <button
                  class="ml-auto btn-icon text-error-500 hover:text-error-600 transition-colors"
                  onclick={() => removeAndroidKey(key)}
                  title="Remove keystore"><Trash2 size={14} /></button
                >
              {/if}
            </div>
            <input
              type="text"
              class="input font-mono text-sm"
              value={key}
              disabled={key === "*"}
              placeholder="keystore-name"
              onchange={(e) =>
                updateAndroidKey(key, (e.target as HTMLInputElement).value)}
            />
            <div class="flex flex-col gap-1">
              <label
                for="keystore-{key}"
                class="text-xs font-medium text-surface-600-400"
                >Keystore Path</label
              >
              <div class="input-group grid grid-cols-[1fr_auto]">
                <input
                  id="keystore-{key}"
                  type="text"
                  class="ig-input font-mono text-sm"
                  placeholder="$HOME/Certificates/myapp.keystore"
                  value={config.android[key]?.KeystorePath || ""}
                  oninput={(e) => {
                    config.android[key].KeystorePath = (
                      e.target as HTMLInputElement
                    ).value;
                    config = { ...config };
                    saveConfig();
                  }}
                />
                <button
                  class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
                  type="button"
                  onclick={() => pickFile("KeystorePath", key)}
                  title="Browse for keystore file"
                  ><FolderOpen size={16} /></button
                >
              </div>
            </div>
            <div class="flex flex-col gap-1">
              <label
                for="codesigninfo-{key}"
                class="text-xs font-medium text-surface-600-400"
                >Codesign Info Text Path</label
              >
              <div class="input-group grid grid-cols-[1fr_auto]">
                <input
                  id="codesigninfo-{key}"
                  type="text"
                  class="ig-input font-mono text-sm"
                  placeholder="$HOME/Certificates/myapp.txt"
                  value={config.android[key]?.CodesignInfoTxtPath || ""}
                  oninput={(e) => {
                    config.android[key].CodesignInfoTxtPath = (
                      e.target as HTMLInputElement
                    ).value;
                    config = { ...config };
                    saveConfig();
                  }}
                />
                <button
                  class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
                  type="button"
                  onclick={() => pickFile("CodesignInfoTxtPath", key)}
                  title="Browse for codesign info file"
                  ><FolderOpen size={16} /></button
                >
              </div>
              <p class="text-xs text-surface-500-400 mt-1">
                Text file containing keystore password and key alias
                information.
              </p>
            </div>
          </div>
        {/each}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2 self-start"
          onclick={addAndroidKey}
        >
          <Plus size={14} /> Add Keystore
        </button>
      </div>
    </div>
  </div>
</div>
