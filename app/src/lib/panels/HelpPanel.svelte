<script lang="ts">
  import { onMount } from "svelte";
  import { slide } from "svelte/transition";
  import {
    PanelRightClose,
    PanelRightOpen,
    Search,
    Info,
    Rocket,
    Lightbulb,
    Terminal,
    LayoutGrid,
    FileCog,
    Workflow,
    FolderTree,
    LifeBuoy,
    Link as LinkIcon,
  } from "@lucide/svelte";
  import HelpContent from "$lib/panels/help/HelpContent.svelte";
  import {
    helpToc,
    helpSectionIds,
    type TocEntry,
  } from "$lib/panels/help/help-toc";
  import { getFormattedVersion } from "$lib/app-version.svelte";

  const version = getFormattedVersion();

  const sectionIcons: Record<string, typeof Info> = {
    about: Info,
    "quick-start": Rocket,
    concepts: Lightbulb,
    cli: Terminal,
    gui: LayoutGrid,
    config: FileCog,
    workflows: Workflow,
    locations: FolderTree,
    troubleshooting: LifeBuoy,
    resources: LinkIcon,
  };

  let activeSection = $state("about");
  let tocOpen = $state(true);
  let query = $state("");

  const filteredToc = $derived.by<TocEntry[]>(() => {
    const q = query.trim().toLowerCase();
    if (!q) return helpToc;
    const result: TocEntry[] = [];
    for (const entry of helpToc) {
      const selfMatch = entry.label.toLowerCase().includes(q);
      const kids =
        entry.children?.filter((c) => c.label.toLowerCase().includes(q)) ?? [];
      if (selfMatch) result.push(entry);
      else if (kids.length) result.push({ ...entry, children: kids });
    }
    return result;
  });

  function scrollTo(id: string) {
    activeSection = id;
    document
      .getElementById(id)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  onMount(() => {
    const root = document.getElementById("docs-content");
    if (!root) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) activeSection = e.target.id;
        }
      },
      { root, rootMargin: "0px 0px -75% 0px", threshold: 0 },
    );
    for (const id of helpSectionIds) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  });
</script>

<div
  class="h-full grid overflow-hidden transition-[grid-template-columns] duration-300 ease-in-out"
  style="grid-template-columns: 1fr {tocOpen ? '260px' : '48px'};"
>
  <!-- Main Content -->
  <div class="overflow-auto p-6 md:p-8" id="docs-content">
    <div class="max-w-3xl mx-auto">
      <HelpContent {version} />
    </div>
  </div>

  <!-- Table of Contents Sidebar -->
  <nav
    class="overflow-hidden border-l border-surface-200-800 bg-surface-50-950 flex flex-col"
  >
    <div class="flex items-center justify-between gap-2 p-3 shrink-0">
      {#if tocOpen}
        <h4 class="text-xs font-bold uppercase tracking-wider text-surface-500">
          On this page
        </h4>
      {/if}
      <button
        class="btn preset-tonal p-1.5"
        onclick={() => (tocOpen = !tocOpen)}
        title={tocOpen ? "Collapse" : "Expand"}
      >
        {#if tocOpen}
          <PanelRightClose size={16} />
        {:else}
          <PanelRightOpen size={16} />
        {/if}
      </button>
    </div>

    {#if tocOpen}
      <div class="px-3 pb-2 shrink-0" transition:slide={{ duration: 150 }}>
        <div class="input-group grid grid-cols-[auto_1fr] items-center">
          <div class="ig-cell px-2 text-surface-500"><Search size={14} /></div>
          <input
            class="ig-input text-sm py-1.5"
            type="text"
            placeholder="Search help..."
            bind:value={query}
          />
        </div>
      </div>

      <ul
        class="flex-1 overflow-auto px-2 pb-4 space-y-0.5"
        transition:slide={{ duration: 150 }}
      >
        {#each filteredToc as entry (entry.id)}
          {@const Icon = sectionIcons[entry.id] ?? Info}
          <li>
            <button
              class="flex items-center gap-2 text-left text-sm w-full px-2 py-1.5 rounded transition-colors hover:bg-surface-200-800
              {activeSection === entry.id
                ? 'text-primary-500 font-medium bg-surface-200-800/60'
                : 'text-surface-700-300'}"
              onclick={() => scrollTo(entry.id)}
            >
              <Icon size={15} class="shrink-0" />
              <span class="truncate">{entry.label}</span>
            </button>
            {#if entry.children}
              <ul
                class="ml-4 border-l border-surface-200-800 pl-2 mt-0.5 space-y-0.5"
              >
                {#each entry.children as child (child.id)}
                  <li>
                    <button
                      class="text-left text-xs w-full px-2 py-1 rounded transition-colors hover:bg-surface-200-800
                      {activeSection === child.id
                        ? 'text-primary-500 font-medium'
                        : 'text-surface-500'}"
                      onclick={() => scrollTo(child.id)}
                    >
                      {child.label}
                    </button>
                  </li>
                {/each}
              </ul>
            {/if}
          </li>
        {/each}
        {#if filteredToc.length === 0}
          <li class="px-2 py-3 text-xs text-surface-500">No matches.</li>
        {/if}
      </ul>
    {/if}
  </nav>
</div>
