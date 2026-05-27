<script lang="ts">
  import { Network } from "@lucide/svelte";
  import { onMount } from "svelte";
  import cytoscape from "cytoscape";

  let containerEl: HTMLDivElement;

  const mockElements: cytoscape.ElementDefinition[] = [
    // Nodes - Toolkit
    { data: { id: "toolkit-core", label: "toolkit-core", group: "toolkit" } },
    { data: { id: "toolkit-data", label: "toolkit-data", group: "toolkit" } },
    {
      data: {
        id: "toolkit-msbuild",
        label: "toolkit-msbuild",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-versioning",
        label: "toolkit-versioning",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-core",
        label: "toolkit-maui-core",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-controls",
        label: "toolkit-maui-controls",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-maps",
        label: "toolkit-maui-maps",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-mvvm",
        label: "toolkit-maui-mvvm",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-devices",
        label: "toolkit-maui-devices",
        group: "toolkit",
      },
    },
    // Nodes - AppModule
    {
      data: {
        id: "appmodule-core",
        label: "appmodule-core",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-mapping",
        label: "appmodule-mapping",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-data",
        label: "appmodule-data",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-content",
        label: "appmodule-content",
        group: "appmodule",
      },
    },
    // Nodes - App
    { data: { id: "field-maps", label: "field-maps", group: "app" } },
    { data: { id: "quick-capture", label: "quick-capture", group: "app" } },
    // Edges
    { data: { source: "toolkit-maui-core", target: "toolkit-core" } },
    { data: { source: "toolkit-maui-controls", target: "toolkit-maui-core" } },
    { data: { source: "toolkit-maui-maps", target: "toolkit-maui-core" } },
    { data: { source: "toolkit-maui-mvvm", target: "toolkit-core" } },
    { data: { source: "toolkit-maui-devices", target: "toolkit-maui-core" } },
    { data: { source: "toolkit-data", target: "toolkit-core" } },
    { data: { source: "appmodule-core", target: "toolkit-core" } },
    { data: { source: "appmodule-core", target: "toolkit-maui-core" } },
    { data: { source: "appmodule-mapping", target: "appmodule-core" } },
    { data: { source: "appmodule-mapping", target: "toolkit-maui-maps" } },
    { data: { source: "appmodule-data", target: "appmodule-core" } },
    { data: { source: "appmodule-data", target: "toolkit-data" } },
    { data: { source: "appmodule-content", target: "appmodule-core" } },
    { data: { source: "field-maps", target: "appmodule-mapping" } },
    { data: { source: "field-maps", target: "appmodule-content" } },
    { data: { source: "quick-capture", target: "appmodule-core" } },
  ];

  onMount(() => {
    const cy = cytoscape({
      container: containerEl,
      elements: mockElements,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-valign": "bottom",
            "text-halign": "center",
            "font-size": "11px",
            "text-margin-y": 8,
            color: "#e2e8f0",
            "text-outline-color": "#1e293b",
            "text-outline-width": 2,
            "background-color": "#6366f1",
            width: 24,
            height: 24,
          },
        },
        {
          selector: "node[group='toolkit']",
          style: { "background-color": "#6366f1" },
        },
        {
          selector: "node[group='appmodule']",
          style: { "background-color": "#f59e0b" },
        },
        {
          selector: "node[group='app']",
          style: { "background-color": "#10b981" },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#475569",
            "target-arrow-color": "#475569",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            opacity: 1,
          },
        },
      ],
      layout: {
        name: "breadthfirst",
        directed: true,
        spacingFactor: 1.0,
        padding: 30,
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      wheelSensitivity: 3,
    });

    return () => {
      cy.destroy();
    };
  });
</script>

<div class="h-full flex flex-col overflow-hidden">
  <div class="flex items-center gap-2 p-4 border-b border-surface-200-800">
    <Network size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Project Graph</h2>
    <span class="text-xs text-surface-500 ml-2">(mocked data)</span>
  </div>
  <div class="flex-1 min-h-0" bind:this={containerEl}></div>
  <div
    class="flex items-center gap-4 px-4 py-2 border-t border-surface-200-800 text-xs text-surface-500"
  >
    <span class="flex items-center gap-1"
      ><span class="inline-block w-3 h-3 rounded-full bg-[#6366f1]"></span> Toolkit</span
    >
    <span class="flex items-center gap-1"
      ><span class="inline-block w-3 h-3 rounded-full bg-[#f59e0b]"></span> AppModule</span
    >
    <span class="flex items-center gap-1"
      ><span class="inline-block w-3 h-3 rounded-full bg-[#10b981]"></span> App</span
    >
  </div>
</div>
