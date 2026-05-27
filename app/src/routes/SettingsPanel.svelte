<script lang="ts">
  import { Settings } from "@lucide/svelte";
</script>

<div class="h-full flex flex-col overflow-hidden">
  <div
    class="flex items-center gap-2 p-4 bg-surface-50-950 border-b border-surface-200-800"
  >
    <Settings size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Settings</h2>
  </div>
  <div class="flex-1 min-h-0 flex items-center justify-center">
    <p class="text-surface-500">Settings will appear here.</p>
  </div>
</div>
