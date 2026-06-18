<script lang="ts">
  import type { FeatureItem } from "./types.ts";

  let { feature }: { feature: FeatureItem } = $props();
  const Icon = $derived(feature.icon);
</script>

<div class="text-center">
  <div class="relative mb-6">
    <div
      class="absolute inset-0 bg-gradient-to-r {feature.gradient} opacity-20 rounded-full blur-2xl"
    ></div>
    <div
      class="relative bg-gradient-to-r {feature.gradient} rounded-full p-6"
    >
      <Icon size={32} class="text-white" />
    </div>
  </div>
  <h3 class="h4 mb-2">
    {feature.title}
  </h3>
  <p class="text-surface-600-400 text-sm">{feature.description}</p>
</div>
