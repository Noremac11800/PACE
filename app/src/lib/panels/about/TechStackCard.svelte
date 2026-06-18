<script lang="ts">
  import { ExternalLink } from "@lucide/svelte";
  import type { TechItem } from "./types.ts";

  let {
    tech,
    onlearnMore,
  }: {
    tech: TechItem;
    onlearnMore: (link: string) => void;
  } = $props();

  const techGradients: Record<string, string> = {
    "text-orange-500": "from-orange-400 to-orange-600",
    "text-blue-500": "from-blue-400 to-blue-600",
    "text-cyan-500": "from-cyan-400 to-cyan-600",
    "text-purple-500": "from-purple-400 to-purple-600",
    "text-green-500": "from-green-400 to-green-600",
  };

  let gradient = $derived(
    techGradients[tech.color] ?? "from-orange-500 to-orange-600",
  );
</script>

<div class="group relative">
  <!-- Card -->
  <div
    class="card bg-linear-to-br from-surface-50-950 to-surface-100-900 border border-surface-200-800 p-6 md:p-10 hover:shadow-2xl transition-all duration-500 group-hover:scale-[1.02] group-hover:border-primary-300-700"
  >
    <!-- Icon with enhanced background -->
    <div class="relative mb-6 md:mb-8">
      <div
        class="absolute inset-0 bg-gradient-to-br {gradient} opacity-15 rounded-3xl blur-2xl group-hover:opacity-25 transition-all duration-500"
      ></div>
      <div
        class="relative bg-white border border-surface-200-800 shadow-lg rounded-3xl p-4 md:p-6 group-hover:shadow-2xl group-hover:scale-105 transition-all duration-300 flex items-center justify-center"
      >
        <img
          src={tech.logo}
          alt={tech.name}
          class="h-12 w-12 md:h-16 md:w-16 object-contain drop-shadow-sm"
        />
      </div>
    </div>

    <!-- Content -->
    <div class="space-y-6">
      <div>
        <h3
          class="h3 mb-3 group-hover:text-primary-500 transition-colors font-semibold"
        >
          {tech.name}
        </h3>
        <p class="text-surface-600-400 text-sm leading-relaxed">
          {tech.description}
        </p>
      </div>

      <!-- Features -->
      <div class="flex flex-wrap gap-2">
        {#each tech.features as feature (feature)}
          <span
            class="text-xs px-3 py-1.5 bg-linear-to-r from-surface-100-800 to-surface-200-700 text-surface-700-300 rounded-full border border-surface-200-800 font-medium"
          >
            {feature}
          </span>
        {/each}
      </div>

      <!-- Link -->
      <button
        class="flex items-center gap-2 text-sm text-primary-500 hover:text-primary-600 font-medium opacity-0 group-hover:opacity-100 transform translate-y-2 group-hover:translate-y-0 transition-all duration-300 hover:scale-105"
        onclick={() => onlearnMore(tech.link)}
      >
        <ExternalLink size={16} />
        Learn more
      </button>
    </div>
  </div>

  <!-- Decorative element -->
  <div
    class="absolute -top-4 -right-4 w-20 h-20 bg-gradient-to-br {tech.color} opacity-10 rounded-full blur-2xl group-hover:opacity-20 transition-opacity"
  ></div>
</div>
