<script lang="ts">
  import { CloudUpload } from "@lucide/svelte";
</script>

<div class="h-full flex flex-col p-4">
  <div class="flex items-center gap-2 mb-4">
    <CloudUpload size={18} class="text-primary-500" />
    <span class="font-semibold text-surface-900-100">Upload Configuration</span>
  </div>
  <div class="card bg-surface-50-950 p-6 flex flex-col gap-4">
    <p class="text-sm text-surface-600-400">
      Configure artifact upload destinations.
    </p>
    <div class="flex flex-col gap-3">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-600-400">S3 Bucket</label
        >
        <input
          type="text"
          class="input text-sm"
          placeholder="s3://my-bucket/releases"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-600-400"
          >Azure Blob Storage</label
        >
        <input
          type="text"
          class="input text-sm"
          placeholder="https://myaccount.blob.core.windows.net"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-600-400"
          >Internal Server URL</label
        >
        <input
          type="text"
          class="input text-sm"
          placeholder="https://releases.company.com"
        />
      </div>
    </div>
  </div>
</div>
