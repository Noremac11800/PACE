<script lang="ts">
  import { Network } from "@lucide/svelte";
  import { onMount } from "svelte";
  import cytoscape from "cytoscape";
  import cytoscapeDagre from "cytoscape-dagre";

  cytoscape.use(cytoscapeDagre);

  let containerEl: HTMLDivElement;

  const mockElements: cytoscape.ElementDefinition[] = [
    // Nodes - Toolkit (global deps)
    {
      data: {
        id: "toolkit-msbuild",
        label: "tk-msbuild",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-versioning",
        label: "tk-versioning",
        group: "toolkit",
      },
    },
    // Nodes - Toolkit (root projects)
    {
      data: {
        id: "toolkit-maui-appconfig",
        label: "tk-maui-appconfig",
        group: "toolkit",
      },
    },
    { data: { id: "toolkit-core", label: "tk-core", group: "toolkit" } },
    {
      data: {
        id: "toolkit-maui-calcite",
        label: "tk-maui-calcite",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-mvvm",
        label: "tk-maui-mvvm",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-core",
        label: "tk-maui-core",
        group: "toolkit",
      },
    },
    { data: { id: "toolkit-data", label: "tk-data", group: "toolkit" } },
    // Nodes - Toolkit (composites)
    {
      data: {
        id: "toolkit-maui-media",
        label: "tk-maui-media",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-sensors",
        label: "tk-maui-sensors",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-devices",
        label: "tk-maui-devices",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-controls",
        label: "tk-maui-controls",
        group: "toolkit",
      },
    },
    { data: { id: "toolkit-maui", label: "tk-maui", group: "toolkit" } },
    {
      data: {
        id: "toolkit-maui-localization",
        label: "tk-maui-localization",
        group: "toolkit",
      },
    },
    {
      data: {
        id: "toolkit-maui-maps",
        label: "tk-maui-maps",
        group: "toolkit",
      },
    },
    // Nodes - AppModule
    {
      data: {
        id: "appmodule-resources",
        label: "am-resources",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-core",
        label: "am-core",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-content",
        label: "am-content",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-data",
        label: "am-data",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-location",
        label: "am-location",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-toolkit",
        label: "am-toolkit",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-survey123",
        label: "am-survey123",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-featureforms",
        label: "am-featureforms",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-quickcapture",
        label: "am-quickcapture",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-webforms",
        label: "am-webforms",
        group: "appmodule",
      },
    },
    {
      data: {
        id: "appmodule-mapping",
        label: "am-mapping",
        group: "appmodule",
      },
    },
    // Nodes - App
    { data: { id: "apps-sdk", label: "apps-sdk", group: "appmodule" } },
    { data: { id: "Survey123", label: "Survey123", group: "app" } },
    {
      data: { id: "Survey123-Studio", label: "Survey123-Studio", group: "app" },
    },
    // Edges - toolkit-maui-appconfig
    {
      data: { source: "toolkit-versioning", target: "toolkit-maui-appconfig" },
    },
    { data: { source: "toolkit-msbuild", target: "toolkit-maui-appconfig" } },
    // Edges - toolkit-core
    { data: { source: "toolkit-versioning", target: "toolkit-core" } },
    { data: { source: "toolkit-msbuild", target: "toolkit-core" } },
    // Edges - toolkit-maui-calcite
    { data: { source: "toolkit-versioning", target: "toolkit-maui-calcite" } },
    { data: { source: "toolkit-msbuild", target: "toolkit-maui-calcite" } },
    // Edges - toolkit-maui-mvvm
    { data: { source: "toolkit-versioning", target: "toolkit-maui-mvvm" } },
    { data: { source: "toolkit-msbuild", target: "toolkit-maui-mvvm" } },
    // Edges - toolkit-maui-core
    { data: { source: "toolkit-versioning", target: "toolkit-maui-core" } },
    { data: { source: "toolkit-msbuild", target: "toolkit-maui-core" } },
    // Edges - toolkit-data
    { data: { source: "toolkit-versioning", target: "toolkit-data" } },
    { data: { source: "toolkit-msbuild", target: "toolkit-data" } },
    // Edges - toolkit-maui-media
    { data: { source: "toolkit-maui-calcite", target: "toolkit-maui-media" } },
    { data: { source: "toolkit-maui-mvvm", target: "toolkit-maui-media" } },
    { data: { source: "toolkit-maui-core", target: "toolkit-maui-media" } },
    // Edges - toolkit-maui-sensors
    {
      data: { source: "toolkit-maui-calcite", target: "toolkit-maui-sensors" },
    },
    { data: { source: "toolkit-maui-mvvm", target: "toolkit-maui-sensors" } },
    { data: { source: "toolkit-maui-core", target: "toolkit-maui-sensors" } },
    // Edges - toolkit-maui-devices
    {
      data: { source: "toolkit-maui-calcite", target: "toolkit-maui-devices" },
    },
    { data: { source: "toolkit-maui-mvvm", target: "toolkit-maui-devices" } },
    { data: { source: "toolkit-maui-core", target: "toolkit-maui-devices" } },
    // Edges - toolkit-maui-controls
    { data: { source: "toolkit-maui-mvvm", target: "toolkit-maui-controls" } },
    // Edges - toolkit-maui
    { data: { source: "toolkit-maui-media", target: "toolkit-maui" } },
    { data: { source: "toolkit-maui-sensors", target: "toolkit-maui" } },
    { data: { source: "toolkit-maui-devices", target: "toolkit-maui" } },
    { data: { source: "toolkit-maui-controls", target: "toolkit-maui" } },
    // Edges - toolkit-maui-localization
    {
      data: {
        source: "toolkit-maui-core",
        target: "toolkit-maui-localization",
      },
    },
    // Edges - toolkit-maui-maps
    {
      data: {
        source: "toolkit-maui-localization",
        target: "toolkit-maui-maps",
      },
    },
    // Edges - appmodule-resources
    { data: { source: "toolkit-maui", target: "appmodule-resources" } },
    {
      data: {
        source: "toolkit-maui-localization",
        target: "appmodule-resources",
      },
    },
    // Edges - appmodule-core
    { data: { source: "toolkit-data", target: "appmodule-core" } },
    { data: { source: "toolkit-maui-maps", target: "appmodule-core" } },
    { data: { source: "appmodule-resources", target: "appmodule-core" } },
    // Edges - appmodule-content
    { data: { source: "appmodule-core", target: "appmodule-content" } },
    // Edges - appmodule-data
    { data: { source: "appmodule-core", target: "appmodule-data" } },
    // Edges - appmodule-location
    { data: { source: "appmodule-core", target: "appmodule-location" } },
    // Edges - appmodule-toolkit
    { data: { source: "appmodule-content", target: "appmodule-toolkit" } },
    { data: { source: "appmodule-data", target: "appmodule-toolkit" } },
    { data: { source: "appmodule-location", target: "appmodule-toolkit" } },
    // Edges - appmodule-survey123
    { data: { source: "appmodule-toolkit", target: "appmodule-survey123" } },
    // Edges - appmodule-featureforms
    { data: { source: "appmodule-toolkit", target: "appmodule-featureforms" } },
    // Edges - appmodule-quickcapture
    { data: { source: "appmodule-toolkit", target: "appmodule-quickcapture" } },
    // Edges - appmodule-webforms
    { data: { source: "appmodule-toolkit", target: "appmodule-webforms" } },
    // Edges - appmodule-mapping
    { data: { source: "appmodule-survey123", target: "appmodule-mapping" } },
    // Edges - apps-sdk
    { data: { source: "appmodule-survey123", target: "apps-sdk" } },
    { data: { source: "appmodule-featureforms", target: "apps-sdk" } },
    { data: { source: "appmodule-quickcapture", target: "apps-sdk" } },
    { data: { source: "appmodule-webforms", target: "apps-sdk" } },
    // Edges - Survey123
    { data: { source: "apps-sdk", target: "Survey123" } },
    // Edges - Survey123-Studio
    { data: { source: "apps-sdk", target: "Survey123-Studio" } },
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
        nodeSep: 80,
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
