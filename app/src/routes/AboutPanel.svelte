<script lang="ts">
  import { PanelRightClose, PanelRightOpen } from "@lucide/svelte";
  import { slide } from "svelte/transition";

  const version = "v0.1.0-alpha";

  interface TocEntry {
    id: string;
    label: string;
    children?: TocEntry[];
  }

  const toc: TocEntry[] = [
    { id: "about", label: "About PACE" },
    {
      id: "getting-started",
      label: "Getting Started",
      children: [
        { id: "installation", label: "Installation" },
        { id: "configuration", label: "Configuration" },
      ],
    },
    {
      id: "cli-usage",
      label: "CLI Usage",
      children: [
        { id: "global-options", label: "Global Options" },
        { id: "cmd-dotnet", label: "dotnet Command" },
        { id: "cmd-git", label: "git Command" },
        { id: "cmd-demo", label: "demo Command" },
      ],
    },
    {
      id: "gui-usage",
      label: "GUI Usage",
      children: [
        { id: "gui-dependencies", label: "Dependencies Panel" },
        { id: "gui-build-props", label: "Directory.Build.props Editor" },
        { id: "gui-console", label: "Console Panel" },
      ],
    },
    { id: "config-file", label: "Configuration File" },
  ];

  let activeSection = $state("about");
  let tocOpen = $state(true);

  function scrollTo(id: string) {
    activeSection = id;
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
</script>

<div
  class="h-full grid overflow-hidden transition-[grid-template-columns] duration-300 ease-in-out"
  style="grid-template-columns: 1fr {tocOpen ? '220px' : '48px'};"
>
  <!-- Main Content -->
  <div class="overflow-auto p-6 space-y-8" id="docs-content">
    <!-- About -->
    <section id="about">
      <div class="flex items-center gap-4 mb-4">
        <img src="/appicon.svg" alt="PACE" class="h-12 w-12" />
        <div>
          <h1 class="h2 text-primary-500">PACE</h1>
          <p class="text-sm text-surface-700-300">Version {version}</p>
        </div>
      </div>
      <p class="text-surface-700-300">
        <strong>Project Automation and Configuration Engine</strong> — a tool for
        managing multi-repository .NET projects. PACE provides both a CLI and a GUI
        to orchestrate builds, manage git operations, and configure shared build
        properties across your project graph.
      </p>
    </section>

    <!-- Getting Started -->
    <section id="getting-started">
      <h2 class="h3 text-primary-500 mb-3 border-b border-surface-200-800 pb-2">
        Getting Started
      </h2>

      <div id="installation" class="mb-6">
        <h3 class="h4 mb-2">Installation</h3>
        <p class="text-sm text-surface-700-300 mb-2">
          PACE requires <strong>Python 3.11+</strong>, <strong>Git</strong>, and
          <strong>pipx</strong>. Install PACE from the repository root:
        </p>
        <pre
          class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto">pipx install --editable /path/to/PACE</pre>
        <p class="text-xs text-surface-500 mt-2">
          Use the <strong>Dependencies</strong> panel in the GUI to check and install
          all prerequisites automatically.
        </p>
      </div>

      <div id="configuration" class="mb-6">
        <h3 class="h4 mb-2">Configuration</h3>
        <p class="text-sm text-surface-700-300 mb-2">
          PACE uses a TOML configuration file to define the project graph. By
          default it loads an internal <code class="text-primary-500"
            >pace.toml</code
          >, but you can specify a custom config:
        </p>
        <pre
          class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto">pace -C /path/to/config.toml [command]</pre>
        <p class="text-sm text-surface-700-300 mt-2">
          The <code class="text-primary-500">REPODIR</code> environment variable
          can override the
          <code class="text-primary-500">repodir</code> setting in the config file.
        </p>
      </div>
    </section>

    <!-- CLI Usage -->
    <section id="cli-usage">
      <h2 class="h3 text-primary-500 mb-3 border-b border-surface-200-800 pb-2">
        CLI Usage
      </h2>
      <pre
        class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto mb-4">usage: pace [-h] [-C &lt;path&gt;] [OPTIONS] command...</pre>

      <div id="global-options" class="mb-6">
        <h3 class="h4 mb-2">Global Options</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-surface-200-800">
                <th class="text-left py-2 pr-4 text-surface-500 font-medium"
                  >Option</th
                >
                <th class="text-left py-2 text-surface-500 font-medium"
                  >Description</th
                >
              </tr>
            </thead>
            <tbody>
              <tr class="border-b border-surface-200-800">
                <td class="py-2 pr-4 font-mono text-primary-500">-h, --help</td>
                <td class="py-2 text-surface-700-300"
                  >Show help message and exit</td
                >
              </tr>
              <tr class="border-b border-surface-200-800">
                <td class="py-2 pr-4 font-mono text-primary-500"
                  >-v, --version</td
                >
                <td class="py-2 text-surface-700-300"
                  >Print the version and exit</td
                >
              </tr>
              <tr class="border-b border-surface-200-800">
                <td class="py-2 pr-4 font-mono text-primary-500"
                  >-C, --config &lt;path&gt;</td
                >
                <td class="py-2 text-surface-700-300"
                  >Path to configuration file (defaults to internal pace.toml)</td
                >
              </tr>
              <tr class="border-b border-surface-200-800">
                <td class="py-2 pr-4 font-mono text-primary-500">--debug</td>
                <td class="py-2 text-surface-700-300"
                  >Enable debug mode with full tracebacks</td
                >
              </tr>
              <tr>
                <td class="py-2 pr-4 font-mono text-primary-500"
                  >--print-config</td
                >
                <td class="py-2 text-surface-700-300"
                  >Print the loaded configuration and exit</td
                >
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div id="cmd-dotnet" class="mb-6">
        <h3 class="h4 mb-2">dotnet Command</h3>
        <p class="text-sm text-surface-700-300 mb-2">
          Execute dotnet build commands across the project graph. PACE creates a
          temporary solution file containing all configured projects and runs
          <code class="text-primary-500">dotnet build</code> against it.
        </p>
        <pre
          class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto mb-2">pace dotnet [-- dotnet-args...]</pre>
        <p class="text-sm text-surface-700-300 mb-2">
          <strong>Framework filtering:</strong>
        </p>
        <pre
          class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto mb-2"># Build only iOS-compatible projects
pace dotnet -- -f net8.0-ios</pre>
        <p class="text-xs text-surface-500">
          Supported framework filters: <code>ios</code>, <code>android</code>,
          <code>windows</code>, <code>maccatalyst</code>
        </p>
      </div>

      <div id="cmd-git" class="mb-6">
        <h3 class="h4 mb-2">git Command</h3>
        <p class="text-sm text-surface-700-300 mb-2">
          Execute git operations across all repositories in parallel with live
          status updates.
        </p>
        <pre
          class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto mb-2">pace git clone   # Clone all repositories
pace git pull    # Pull latest for all repositories</pre>
        <p class="text-xs text-surface-500">
          Repositories are defined per-project in the config file via the
          <code>repo_url</code> field.
        </p>
      </div>

      <div id="cmd-demo" class="mb-6">
        <h3 class="h4 mb-2">demo Command</h3>
        <p class="text-sm text-surface-700-300 mb-2">
          Run built-in Rich demos for development and testing purposes.
        </p>
        <pre
          class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto mb-2">pace demo columns
pace demo progress_bar</pre>
      </div>
    </section>

    <!-- GUI Usage -->
    <section id="gui-usage">
      <h2 class="h3 text-primary-500 mb-3 border-b border-surface-200-800 pb-2">
        GUI Usage
      </h2>
      <p class="text-sm text-surface-700-300 mb-4">
        The PACE GUI provides visual access to the same functionality as the
        CLI, plus additional features. Navigate between panels using the
        sidebar.
      </p>

      <div id="gui-dependencies" class="mb-6">
        <h3 class="h4 mb-2">Dependencies Panel</h3>
        <p class="text-sm text-surface-700-300">
          Checks for required dependencies (Python, Git, pipx) and allows you to
          install PACE directly from the GUI. If PACE is not installed, other
          panels will be disabled and a warning badge will appear on this
          button.
        </p>
      </div>

      <div id="gui-build-props" class="mb-6">
        <h3 class="h4 mb-2">Directory.Build.props Editor</h3>
        <p class="text-sm text-surface-700-300 mb-2">
          Create and manage MSBuild properties that apply to all .NET projects
          in a directory tree.
        </p>
        <ul
          class="text-sm text-surface-700-300 list-disc list-inside space-y-1"
        >
          <li>
            <strong>Add/Edit/Delete</strong> properties with name-value pairs
          </li>
          <li><strong>Search</strong> to filter the property list</li>
          <li>
            <strong>Save</strong> writes a
            <code class="text-primary-500">Directory.Build.props</code> file to the
            target directory
          </li>
          <li>
            <strong>Load</strong> reads an existing file from the target directory
          </li>
          <li>
            <strong>Copy XML</strong> copies the generated XML to clipboard
          </li>
        </ul>
      </div>

      <div id="gui-console" class="mb-6">
        <h3 class="h4 mb-2">Console Panel</h3>
        <p class="text-sm text-surface-700-300">
          Displays command output and logs from PACE operations. Use this to
          monitor build progress, git operations, and other long-running tasks.
        </p>
      </div>
    </section>

    <!-- Configuration File -->
    <section id="config-file">
      <h2 class="h3 text-primary-500 mb-3 border-b border-surface-200-800 pb-2">
        Configuration File
      </h2>
      <p class="text-sm text-surface-700-300 mb-3">
        The PACE config file is written in TOML. It defines the repository root
        directory and a list of projects with their paths and repository URLs.
      </p>
      <h3 class="h4 mb-2">Structure</h3>
      <pre
        class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-sm font-mono overflow-x-auto mb-4">repodir = "/path/to/repos"

[[projects]]
name = "my-project"
csproj_path = "src/MyProject/MyProject.csproj"
repo_url = "git@github.com:org/my-project.git"</pre>

      <h3 class="h4 mb-2">Fields</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-surface-200-800">
              <th class="text-left py-2 pr-4 text-surface-500 font-medium"
                >Field</th
              >
              <th class="text-left py-2 pr-4 text-surface-500 font-medium"
                >Type</th
              >
              <th class="text-left py-2 text-surface-500 font-medium"
                >Description</th
              >
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-surface-200-800">
              <td class="py-2 pr-4 font-mono text-primary-500">repodir</td>
              <td class="py-2 pr-4 text-surface-700-300">string</td>
              <td class="py-2 text-surface-700-300"
                >Root directory where repositories are cloned</td
              >
            </tr>
            <tr class="border-b border-surface-200-800">
              <td class="py-2 pr-4 font-mono text-primary-500"
                >projects[].name</td
              >
              <td class="py-2 pr-4 text-surface-700-300">string</td>
              <td class="py-2 text-surface-700-300"
                >Project identifier (also the subdirectory name)</td
              >
            </tr>
            <tr class="border-b border-surface-200-800">
              <td class="py-2 pr-4 font-mono text-primary-500"
                >projects[].csproj_path</td
              >
              <td class="py-2 pr-4 text-surface-700-300">string</td>
              <td class="py-2 text-surface-700-300"
                >Relative path to the .csproj file within the project</td
              >
            </tr>
            <tr>
              <td class="py-2 pr-4 font-mono text-primary-500"
                >projects[].repo_url</td
              >
              <td class="py-2 pr-4 text-surface-700-300">string?</td>
              <td class="py-2 text-surface-700-300"
                >Git remote URL (optional, required for clone/pull)</td
              >
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <!-- Table of Contents Sidebar -->
  <nav
    class="overflow-auto border-l border-surface-200-800 p-4 bg-surface-50-950 flex flex-col"
  >
    <div class="flex items-center justify-between mb-3">
      {#if tocOpen}
        <h4 class="text-xs font-bold uppercase tracking-wider text-surface-500">
          Table of Contents
        </h4>
      {/if}
      <button
        class="btn preset-tonal p-1"
        onclick={() => (tocOpen = !tocOpen)}
        title={tocOpen ? "Collapse TOC" : "Expand TOC"}
      >
        {#if tocOpen}
          <PanelRightClose size={14} />
        {:else}
          <PanelRightOpen size={14} />
        {/if}
      </button>
    </div>
    {#if tocOpen}
      <ul class="space-y-1" transition:slide={{ duration: 200 }}>
        {#each toc as entry}
          <li>
            <button
              class="text-left text-sm w-full px-2 py-1 rounded hover:bg-surface-200-800 transition-colors
              {activeSection === entry.id
                ? 'text-primary-500 font-medium'
                : 'text-surface-700-300'}"
              onclick={() => scrollTo(entry.id)}
            >
              {entry.label}
            </button>
            {#if entry.children}
              <ul class="ml-3 space-y-0.5">
                {#each entry.children as child}
                  <li>
                    <button
                      class="text-left text-xs w-full px-2 py-0.5 rounded hover:bg-surface-200-800 transition-colors
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
      </ul>
    {/if}
  </nav>
</div>
