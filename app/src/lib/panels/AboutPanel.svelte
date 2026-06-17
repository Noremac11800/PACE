<script lang="ts">
  import { onMount } from "svelte";
  import {
    Github,
    ExternalLink,
    Code,
    Package,
    Globe,
    Zap,
    Layers,
    Shield,
    Sparkles,
    Rocket,
    Heart,
  } from "@lucide/svelte";
  import { open } from "@tauri-apps/plugin-shell";
  import { fetchAppVersion, appVersion } from "$lib/app-version.svelte";

  let { class: classname = "" } = $props();

  let version = $derived(`v${appVersion.version}`);

  onMount(() => {
    fetchAppVersion();
  });

  const techStack = [
    {
      name: "Svelte 5",
      description:
        "Modern reactive web framework with runes for fine-grained reactivity",
      color: "text-orange-500",
      link: "https://svelte.dev",
      features: [
        "Runes",
        "Fine-grained reactivity",
        "Compile-time optimizations",
      ],
      logo: "/svelte.svg",
    },
    {
      name: "Tauri",
      description:
        "Build secure, fast, and cross-platform desktop apps with web technologies",
      color: "text-blue-500",
      link: "https://tauri.app",
      features: ["Rust backend", "Security-first", "Small bundle sizes"],
      logo: "/tauri.svg",
    },
    {
      name: "Tailwind CSS",
      description: "Utility-first CSS framework for rapid UI development",
      color: "text-cyan-500",
      link: "https://tailwindcss.com",
      features: ["Utility classes", "Responsive design", "Dark mode support"],
      logo: "/tailwindcss.svg",
    },
    {
      name: "Lucide Svelte",
      description: "Beautiful & consistent icon toolkit for modern interfaces",
      color: "text-purple-500",
      link: "https://lucide.dev",
      features: ["400+ icons", "Consistent design", "Tree-shakeable"],
      logo: "/lucide.svg",
    },
    {
      name: "Python",
      description: "Backend CLI implementation with Rich terminal output",
      color: "text-green-500",
      link: "https://python.org",
      features: ["Rich CLI", "Async operations", "Cross-platform"],
      logo: "/python.svg",
    },
    {
      name: "Rust",
      description: "Systems programming language powering the Tauri backend",
      color: "text-orange-600",
      link: "https://rust-lang.org",
      features: ["Memory safety", "Performance", "WebAssembly"],
      logo: "/rust.svg",
    },
  ];

  const features = [
    {
      title: "Cross-Platform",
      description: "Runs on Windows, macOS, and Linux with native performance",
      icon: Globe,
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      title: "Modern Stack",
      description: "Built with the latest web technologies and best practices",
      icon: Layers,
      gradient: "from-purple-500 to-pink-500",
    },
    {
      title: "Secure by Design",
      description: "Tauri's security model keeps your data safe and private",
      icon: Shield,
      gradient: "from-green-500 to-emerald-500",
    },
    {
      title: "High Performance",
      description: "Lightweight and fast with minimal resource usage",
      icon: Rocket,
      gradient: "from-orange-500 to-red-500",
    },
  ];

  const stats = $derived([
    { label: "Technologies", value: "6+", icon: Sparkles },
    { label: "Platforms", value: "3", icon: Globe },
    { label: "Open Source", value: "MIT", icon: Heart },
    { label: "Version", value: version, icon: Package },
  ]);

  async function openLink(url: string) {
    await open(url);
  }

  const techGradients: Record<string, string> = {
    "text-orange-500": "from-orange-400 to-orange-600",
    "text-blue-500": "from-blue-400 to-blue-600",
    "text-cyan-500": "from-cyan-400 to-cyan-600",
    "text-purple-500": "from-purple-400 to-purple-600",
    "text-green-500": "from-green-400 to-green-600",
  };

  function techGradient(color: string): string {
    return techGradients[color] ?? "from-orange-500 to-orange-600";
  }
</script>

<div class="overflow-auto h-full bg-surface-50-950 {classname}">
  <!-- Hero Section -->
  <div class="relative overflow-hidden">
    <!-- Background gradient -->
    <div
      class="absolute inset-0 bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700"
    ></div>
    <!-- Pattern overlay -->
    <div class="absolute inset-0 opacity-10">
      <div
        class="absolute inset-0"
        style="background-image: radial-gradient(circle, white 1px, transparent 1px); background-size: 60px 60px;"
      ></div>
    </div>

    <!-- Content -->
    <div class="relative z-10 px-6 py-6 text-center">
      <div class="flex justify-center mb-3">
        <div class="relative">
          <div
            class="bg-white/20 backdrop-blur-sm rounded-2xl p-3 border border-white/30"
          >
            <img src="/appglyph.svg" alt="PACE" class="h-12 w-12" />
          </div>
          <div
            class="absolute -bottom-1 -right-1 bg-gradient-to-r from-orange-500 to-pink-500 rounded-full p-1"
          >
            <Sparkles size={12} class="text-white" />
          </div>
        </div>
      </div>

      <h1 class="h2 text-white mb-2">About PACE</h1>
      <p class="text-primary-100 text-base mb-3 max-w-xl mx-auto">
        Project Automation & Configuration Engine
      </p>

      <div class="flex flex-wrap justify-center gap-2 mb-3">
        {#each stats as stat (stat.label)}
          <div
            class="flex items-center gap-1 bg-white/10 backdrop-blur-sm rounded-full px-2 py-1 border border-white/20"
          >
            <stat.icon size={12} class="text-white" />
            <span class="text-white text-sm font-medium">{stat.value}</span>
            <span class="text-primary-200 text-xs">{stat.label}</span>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- Main Content -->
  <div class="max-w-7xl mx-auto p-4 md:p-8 space-y-8 md:space-y-16">
    <!-- Tech Stack Section -->
    <section>
      <div class="text-center mb-6 md:mb-12">
        <div
          class="inline-flex items-center gap-2 bg-primary-100-900 text-primary-600-400 px-3 py-1.5 rounded-full mb-3"
        >
          <Code size={14} />
          <span class="font-medium text-sm">Technology Stack</span>
        </div>
        <h2 class="h3 text-surface-900-100 mb-3">
          Built with Modern Technologies
        </h2>
        <p class="text-surface-600-400 text-sm md:text-lg max-w-2xl mx-auto">
          PACE leverages cutting-edge web technologies to deliver a powerful,
          secure, and performant experience
        </p>
      </div>

      <div
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-8"
      >
        {#each techStack as tech (tech.name)}
          <div class="group relative">
            <!-- Card -->
            <div
              class="card bg-linear-to-br from-surface-50-950 to-surface-100-900 border border-surface-200-800 p-6 md:p-10 hover:shadow-2xl transition-all duration-500 group-hover:scale-[1.02] group-hover:border-primary-300-700"
            >
              <!-- Icon with enhanced background -->
              <div class="relative mb-6 md:mb-8">
                <div
                  class="absolute inset-0 bg-gradient-to-br {techGradient(
                    tech.color,
                  )} opacity-15 rounded-3xl blur-2xl group-hover:opacity-25 transition-all duration-500"
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
                  onclick={() => openLink(tech.link)}
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
        {/each}
      </div>
    </section>

    <!-- Features Section -->
    <section>
      <div class="text-center mb-12">
        <div
          class="inline-flex items-center gap-2 bg-success-100-900 text-success-600-400 px-4 py-2 rounded-full mb-4"
        >
          <Zap size={16} />
          <span class="font-medium">Key Features</span>
        </div>
        <h2 class="h2 text-surface-900-100 mb-4">What Makes PACE Special</h2>
        <p class="text-surface-600-400 text-lg max-w-2xl mx-auto">
          Designed with modern development workflows in mind
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {#each features as feature (feature.title)}
          <div class="text-center">
            <div class="relative mb-6">
              <div
                class="absolute inset-0 bg-gradient-to-r {feature.gradient} opacity-20 rounded-full blur-2xl"
              ></div>
              <div
                class="relative bg-gradient-to-r {feature.gradient} rounded-full p-6"
              >
                <feature.icon size={32} class="text-white" />
              </div>
            </div>
            <h3 class="h4 mb-2">
              {feature.title}
            </h3>
            <p class="text-surface-600-400 text-sm">{feature.description}</p>
          </div>
        {/each}
      </div>
    </section>

    <!-- Repository Section -->
    <section class="relative">
      <!-- Background decoration -->
      <div
        class="absolute inset-0 bg-gradient-to-r from-surface-100-900 via-surface-50-950 to-surface-100-900"
      ></div>

      <div
        class="relative z-10 bg-gradient-to-r from-primary-500 to-primary-600 rounded-3xl p-12 text-center border border-primary-400-600"
      >
        <div class="max-w-4xl mx-auto">
          <div
            class="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 mb-6"
          >
            <Github size={16} class="text-white" />
            <span class="text-white font-medium">Open Source</span>
          </div>

          <h2 class="h2 text-white mb-4">Get Involved</h2>
          <p class="text-primary-100 text-lg mb-8 max-w-2xl mx-auto">
            PACE is open source and contributions are welcome! Whether you want
            to report a bug, suggest a feature, or submit a pull request, we'd
            love to hear from you.
          </p>

          <div
            class="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8"
          >
            <button
              class="bg-white text-primary-600 hover:bg-primary-50 flex items-center gap-2 px-8 py-4 rounded-xl font-medium transition-all duration-300 hover:scale-105 hover:shadow-xl"
              onclick={() => openLink("https://github.com/Noremac11800/PACE")}
            >
              <Github size={20} />
              View Repository
            </button>

            <button
              class="bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 border border-white/30 flex items-center gap-2 px-8 py-4 rounded-xl font-medium transition-all duration-300 hover:scale-105"
              onclick={() =>
                openLink("https://github.com/Noremac11800/PACE/issues")}
            >
              <Package size={20} />
              Report Issues
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- License Section -->
    <section class="text-center py-12 border-t border-surface-200-800">
      <div class="flex items-center justify-center gap-2 mb-4">
        <span class="text-surface-600-400 font-medium">Made with</span>
        <Heart size={20} class="text-red-500" />
      </div>
      <p class="text-surface-600-400 mb-2">
        PACE is licensed under the MIT License
      </p>
    </section>
  </div>
</div>
