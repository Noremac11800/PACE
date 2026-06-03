<script lang="ts">
  import { Rocket, FileSignature, Globe, CloudUpload } from "@lucide/svelte";
  import CodesigningConfig from "./CodesigningConfig.svelte";
  import PublishingConfig from "./PublishingConfig.svelte";
  import UploadConfig from "./UploadConfig.svelte";

  let activeSection = $state<"codesigning" | "publishing" | "upload">(
    "publishing",
  );

  const sections = {
    publishing: { icon: Globe, label: "Publishing" },
    upload: { icon: CloudUpload, label: "Upload" },
    codesigning: { icon: FileSignature, label: "Code signing" },
  };
</script>

<div class="h-full flex flex-col">
  <!-- Main Header -->
  <div
    class="flex items-center gap-2 px-4 py-3 border-b border-surface-200-800 bg-surface-50-950 shrink-0"
  >
    <Rocket size={20} class="text-primary-500" />
    <span class="font-semibold text-surface-900-100">Deploy</span>
  </div>

  <!-- Section Tabs -->
  <div class="flex border-b border-surface-200-800 bg-surface-50-950 shrink-0">
    {#each Object.entries(sections) as [sectionId, { icon: Icon, label }]}
      <button
        class="flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap {activeSection ===
        sectionId
          ? 'text-primary-500 border-b-2 border-primary-500 bg-surface-100-900/50'
          : 'text-surface-600-400 hover:text-surface-900-100 hover:bg-surface-100-900/30'}"
        onclick={() => (activeSection = sectionId as typeof activeSection)}
      >
        <Icon size={16} />
        {label}
      </button>
    {/each}
  </div>

  <!-- Section Content -->
  <div class="flex-1 overflow-hidden relative">
    <div
      class="absolute inset-0"
      class:hidden={activeSection !== "codesigning"}
    >
      <CodesigningConfig />
    </div>
    <div class="absolute inset-0" class:hidden={activeSection !== "publishing"}>
      <PublishingConfig />
    </div>
    <div class="absolute inset-0" class:hidden={activeSection !== "upload"}>
      <UploadConfig />
    </div>
  </div>
</div>
