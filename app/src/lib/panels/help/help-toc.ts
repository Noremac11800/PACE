export interface TocEntry {
  id: string;
  label: string;
  children?: TocEntry[];
}

export const helpToc: TocEntry[] = [
  { id: "about", label: "About PACE" },
  {
    id: "quick-start",
    label: "Quick Start",
    children: [
      { id: "qs-install", label: "Install PACE" },
      { id: "qs-config", label: "Create a config" },
      { id: "qs-build", label: "Run your first build" },
    ],
  },
  {
    id: "concepts",
    label: "Core Concepts",
    children: [
      { id: "concept-graph", label: "Project graph" },
      { id: "concept-chains", label: "Dependency chains" },
      { id: "concept-groups", label: "Solution groups" },
      { id: "concept-profiles", label: "Config profiles" },
    ],
  },
  {
    id: "cli",
    label: "CLI Reference",
    children: [
      { id: "cli-global", label: "Global options" },
      { id: "cli-clean", label: "pace clean" },
      { id: "cli-dotnet", label: "pace dotnet" },
      { id: "cli-git", label: "pace git" },
      { id: "cli-upload", label: "pace upload" },
      { id: "cli-demo", label: "pace demo" },
    ],
  },
  {
    id: "gui",
    label: "GUI Guide",
    children: [
      { id: "gui-dependencies", label: "Dependencies" },
      { id: "gui-graph", label: "Project Graph" },
      { id: "gui-build-props", label: "Directory.Build.props" },
      { id: "gui-orchestrator", label: "Orchestrator" },
      { id: "gui-console", label: "Console" },
      { id: "gui-settings", label: "Settings" },
      { id: "gui-updates", label: "Updates" },
    ],
  },
  {
    id: "config",
    label: "Configuration",
    children: [
      { id: "config-location", label: "File location" },
      { id: "config-structure", label: "Structure" },
      { id: "config-fields", label: "Field reference" },
      { id: "config-env", label: "Environment variables" },
    ],
  },
  { id: "workflows", label: "Common Workflows" },
  { id: "locations", label: "Files & Caches" },
  { id: "troubleshooting", label: "Troubleshooting" },
  { id: "resources", label: "Resources" },
];

/** Flattened list of every section + subsection id, in document order. */
export const helpSectionIds: string[] = helpToc.flatMap((entry) => [
  entry.id,
  ...(entry.children?.map((child) => child.id) ?? []),
]);
