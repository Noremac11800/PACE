<script lang="ts">
  import { Terminal } from "@lucide/svelte";
</script>

<div class="min-h-full flex items-center justify-center">
  <div class="card bg-surface-50-950 shadow-md p-8 text-center max-w-md">
    <Terminal size={48} class="mx-auto mb-4 text-primary-500" />
    <h2 class="h2 text-primary-500 mb-2">Console</h2>
    <p class="text-surface-700-300">
      Command output and logs will appear here.
    </p>
  </div>
</div>
