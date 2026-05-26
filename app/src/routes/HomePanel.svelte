<script lang="ts">
  import AnimatedBackground from "./AnimatedBackground.svelte";
</script>

<div class="relative min-h-full flex items-center justify-center">
  <AnimatedBackground />
  <div
    class="card bg-surface-50-950/90 shadow-md p-8 text-center max-w-md relative z-10"
  >
    <img src="/appicon.svg" alt="PACE" class="h-16 w-16 mx-auto mb-4" />
    <h1 class="h1 text-primary-500 mb-2">Welcome to PACE</h1>
    <p class="text-surface-700-300 mb-4">
      Project Automation and Configuration Engine
    </p>
    <p class="text-sm text-surface-700-300">
      Use the sidebar to navigate between views.
    </p>
  </div>
</div>
