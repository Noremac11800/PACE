<script lang="ts">
  import { Network, MousePointerClick, Move, ZoomIn } from "@lucide/svelte";
  import { onMount } from "svelte";
  import cytoscape from "cytoscape";
  import cytoscapeDagre from "cytoscape-dagre";
  import { configStore } from "$lib/config-store.svelte";
  import type { PaceProject } from "$lib/pace-config";

  cytoscape.use(cytoscapeDagre);

  let containerEl: HTMLDivElement = $state(undefined as any);

  // Stable color palette assigned to sln_group values in order of first appearance
  const GROUP_COLORS = [
    "#6366f1",
    "#f59e0b",
    "#10b981",
    "#3b82f6",
    "#ec4899",
    "#8b5cf6",
    "#14b8a6",
    "#f97316",
  ];
  const NO_GROUP_COLOR = "#64748b";

  function getGroupOrder(projects: PaceProject[]): string[] {
    const order: string[] = [];
    for (const p of projects) {
      const g = p.sln_group ?? "";
      if (g && !order.includes(g)) order.push(g);
    }
    return order;
  }

  function buildElements(
    projects: PaceProject[],
  ): cytoscape.ElementDefinition[] {
    const nodes: cytoscape.ElementDefinition[] = projects.map((p) => ({
      data: {
        id: p.name,
        label: p.name,
        group: p.sln_group ?? "",
      },
    }));

    const edges: cytoscape.ElementDefinition[] = [];
    for (const p of projects) {
      for (const dep of p.depends_on ?? []) {
        edges.push({ data: { source: dep, target: p.name } });
      }
    }

    return [...nodes, ...edges];
  }

  function buildGroupStyles(
    projects: PaceProject[],
  ): cytoscape.StylesheetStyle[] {
    const groupOrder = getGroupOrder(projects);
    return groupOrder.map((g, i) => ({
      selector: `node[group='${g}']`,
      style: {
        "background-color": GROUP_COLORS[i % GROUP_COLORS.length],
      },
    }));
  }

  let groupLegend: { label: string; color: string }[] = $derived.by(() => {
    const projects = configStore.activeConfig?.projects ?? [];
    const groupOrder = getGroupOrder(projects);
    const entries = groupOrder.map((g, i) => ({
      label: g,
      color: GROUP_COLORS[i % GROUP_COLORS.length],
    }));
    const hasUngrouped = projects.some((p) => !p.sln_group);
    if (hasUngrouped) entries.push({ label: "Other", color: NO_GROUP_COLOR });
    return entries;
  });

  onMount(() => {
    const projects = configStore.activeConfig?.projects ?? [];
    const elements = buildElements(projects);
    const groupStyles = buildGroupStyles(projects);

    const cy = cytoscape({
      container: containerEl,
      elements,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-valign": "bottom",
            "text-halign": "center",
            "font-size": "18px",
            "text-margin-y": 8,
            "text-wrap": "wrap",
            "text-overflow-wrap": "anywhere",
            "text-max-width": "100px",
            color: "#e2e8f0",
            "text-outline-color": "#1e293b",
            "text-outline-width": 2,
            "background-color": NO_GROUP_COLOR,
            width: 24,
            height: 24,
          },
        },
        ...groupStyles,
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#475569",
            "target-arrow-color": "#64748b",
            "target-arrow-shape": "triangle",
            "curve-style": "taxi",
            "taxi-direction": "vertical",
            "taxi-turn": "50%",
            opacity: 0.6,
          },
        },
        {
          selector: ".highlighted",
          style: {
            "line-color": "#818cf8",
            "target-arrow-color": "#818cf8",
            opacity: 1,
            width: 3,
          },
        },
        {
          selector: "node.highlighted",
          style: {
            "border-width": 3,
            "border-color": "#818cf8",
          },
        },
        {
          selector: ".dimmed",
          style: {
            opacity: 0.15,
          },
        },
      ],
      layout: {
        name: "dagre",
        rankDir: "BT",
        nodeSep: 90,
        rankSep: 80,
        padding: 30,
      } as any,
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      wheelSensitivity: 3,
    });

    function highlightAncestors(node: cytoscape.NodeSingular) {
      const visited = new Set<string>();
      const queue = [node];
      const highlightedEles = cy.collection();

      while (queue.length > 0) {
        const current = queue.shift()!;
        if (visited.has(current.id())) continue;
        visited.add(current.id());
        highlightedEles.merge(current);

        const incomers = current.incomers();
        highlightedEles.merge(incomers.edges());
        for (const n of incomers.nodes()) queue.push(n);
      }

      cy.elements().addClass("dimmed");
      highlightedEles.removeClass("dimmed").addClass("highlighted");
    }

    cy.on("tap", "node", (e) => {
      highlightAncestors(e.target);
    });

    cy.on("tap", (e) => {
      if (e.target === cy) {
        cy.elements().removeClass("highlighted").removeClass("dimmed");
      }
    });

    return () => {
      cy.destroy();
    };
  });
</script>

<div class="h-full flex flex-col overflow-hidden">
  <div
    class="flex items-center gap-2 p-4 bg-surface-50-950 border-b border-surface-200-800"
  >
    <Network size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Project graph</h2>
  </div>
  {#if !configStore.activeConfig}
    <div
      class="flex-1 flex items-center justify-center text-surface-400 text-sm"
    >
      No config loaded. Select a config to view the project graph.
    </div>
  {:else if configStore.activeConfig.projects.length === 0}
    <div
      class="flex-1 flex items-center justify-center text-surface-400 text-sm"
    >
      No projects defined in the active config.
    </div>
  {:else}
    <div class="flex-1 min-h-0" bind:this={containerEl}></div>
  {/if}
  <div
    class="flex flex-col gap-1 px-4 py-2 border-t border-surface-200-800 text-xs text-surface-500"
  >
    <div class="flex items-center gap-4 text-surface-400">
      <span class="flex items-center gap-1"
        ><ZoomIn size={12} /> Scroll to zoom</span
      >
      <span class="flex items-center gap-1"><Move size={12} /> Drag to pan</span
      >
      <span class="flex items-center gap-1"
        ><MousePointerClick size={12} /> Click node to trace dependencies</span
      >
    </div>
    {#if groupLegend.length > 0}
      <div class="flex items-center gap-4 flex-wrap">
        {#each groupLegend as entry}
          <span class="flex items-center gap-1">
            <span
              class="inline-block w-3 h-3 rounded-full"
              style="background-color: {entry.color}"
            ></span>
            {entry.label}
          </span>
        {/each}
      </div>
    {/if}
  </div>
</div>
