<script lang="ts">
  import {
    Rocket,
    Lightbulb,
    Terminal,
    LayoutGrid,
    FileCog,
    Workflow,
    FolderTree,
    LifeBuoy,
    Link as LinkIcon,
    Package,
    Network,
    FileCode,
    Cog,
    Settings,
    Download,
  } from "@lucide/svelte";
  import { openUrl } from "@tauri-apps/plugin-opener";
  import Callout from "$lib/components/Callout.svelte";
  import { CodeBlock, RefTable } from "$lib/snippets/HelpSnippets.svelte";

  let { version = "v0.1.0-alpha" }: { version?: string } = $props();

  const REPO_URL = "https://github.com/Noremac11800/PACE";

  async function openExternal(url: string) {
    try {
      await openUrl(url);
    } catch (e) {
      console.error("Failed to open URL:", e);
    }
  }
</script>

{#snippet sectionTitle(Icon: typeof Rocket, title: string)}
  <h2
    class="h3 text-primary-500 mb-4 border-b border-surface-200-800 pb-2 flex items-center gap-2"
  >
    <Icon size={22} />
    {title}
  </h2>
{/snippet}

<div class="space-y-12">
  <!-- ===================== ABOUT ===================== -->
  <section id="about">
    <div class="flex items-center gap-4 mb-4">
      <img src="/appicon.svg" alt="PACE" class="h-14 w-14" />
      <div>
        <h1 class="h2 text-primary-500">PACE</h1>
        <p class="text-sm text-surface-700-300">
          Project Automation and Configuration Engine
          <span class="text-surface-500">· {version}</span>
        </p>
      </div>
    </div>
    <p class="text-surface-700-300 leading-relaxed">
      <strong>PACE</strong> orchestrates bulk operations across a multi-repository
      .NET/MAUI ecosystem. Instead of cloning, building, signing and publishing dozens
      of interdependent projects one-by-one, you describe the project graph once
      in a config file and let PACE drive Git, the .NET SDK, and your deployment
      pipeline in parallel.
    </p>
    <p class="text-surface-700-300 leading-relaxed mt-3">
      PACE ships as two complementary surfaces that share the same configuration
      and engine:
    </p>
    <div class="grid sm:grid-cols-2 gap-3 mt-4">
      <div class="card bg-surface-50-950 p-4">
        <div class="flex items-center gap-2 mb-1">
          <Terminal size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100">The CLI</span>
        </div>
        <p class="text-sm text-surface-700-300">
          A scriptable Python command-line tool (<code class="text-primary-500"
            >pace</code
          >) ideal for automation and CI.
        </p>
      </div>
      <div class="card bg-surface-50-950 p-4">
        <div class="flex items-center gap-2 mb-1">
          <LayoutGrid size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100">The Desktop App</span
          >
        </div>
        <p class="text-sm text-surface-700-300">
          A visual orchestrator (this app) for interactive builds, signing and
          uploads.
        </p>
      </div>
    </div>
  </section>

  <!-- ===================== QUICK START ===================== -->
  <section id="quick-start">
    {@render sectionTitle(Rocket, "Quick Start")}

    <div id="qs-install" class="mb-8">
      <h3 class="h4 mb-2">1. Install PACE</h3>
      <p class="text-sm text-surface-700-300 mb-2">
        PACE requires <strong>Python 3.11+</strong>, <strong>Git</strong>, and
        the <strong>.NET SDK</strong>. The CLI is installed with
        <strong>pipx</strong>:
      </p>
      {@render CodeBlock("pipx install --editable /path/to/PACE")}
      <Callout type="tip" message="Let the app do it for you">
        <p class="text-sm text-surface-700-300">
          Open the <strong>Dependencies</strong> panel (package icon in the sidebar).
          It detects Python, Git and pipx, then installs the PACE CLI with one click.
          Until the CLI is detected, most panels stay disabled and a warning badge
          appears on the icon.
        </p>
      </Callout>
    </div>

    <div id="qs-config" class="mb-8">
      <h3 class="h4 mb-2">2. Create a config</h3>
      <p class="text-sm text-surface-700-300 mb-2">
        A config describes your repository root and the projects in your graph.
        In the app, open the <strong>Orchestrator</strong> and use the config
        picker to create one — it is saved to
        <code class="text-primary-500">~/.pace/configs/</code>. For the CLI,
        point at any TOML file:
      </p>
      {@render CodeBlock(`pace -C ~/.pace/configs/myteam.toml --print-config`)}
    </div>

    <div id="qs-build">
      <h3 class="h4 mb-2">3. Run your first build</h3>
      <p class="text-sm text-surface-700-300 mb-2">
        Clone every repository, then build the whole graph through a generated
        solution file:
      </p>
      {@render CodeBlock(`pace git clone
pace dotnet build -c Release`)}
      <p class="text-sm text-surface-700-300 mt-2">
        Prefer buttons? The <strong>Orchestrator → Git</strong> tab clones/pulls
        in parallel, and <strong>Orchestrator → Build</strong> runs builds with a
        live command preview and progress bar.
      </p>
    </div>
  </section>

  <!-- ===================== CONCEPTS ===================== -->
  <section id="concepts">
    {@render sectionTitle(Lightbulb, "Core Concepts")}

    <div id="concept-graph" class="mb-6">
      <h3 class="h4 mb-2">Project graph</h3>
      <p class="text-sm text-surface-700-300">
        Every project declares which other projects it
        <code class="text-primary-500">depends_on</code>. Together these form a
        directed dependency graph that PACE uses to order operations and to
        scope commands. Visualize it any time in the
        <strong>Project Graph</strong> panel.
      </p>
    </div>

    <div id="concept-chains" class="mb-6">
      <h3 class="h4 mb-2">
        Dependency chains — <code>--from</code> / <code>--to</code>
      </h3>
      <p class="text-sm text-surface-700-300 mb-2">
        Most commands accept <code class="text-primary-500">--from</code> and
        <code class="text-primary-500">--to</code> to operate on a slice of the graph
        rather than everything:
      </p>
      {@render RefTable(
        ["Flag", "Effect"],
        [
          {
            cells: [
              { text: "--from <repo>", mono: true, accent: true },
              {
                text: "Include <repo> and everything downstream that (transitively) depends on it.",
              },
            ],
          },
          {
            cells: [
              { text: "--to <repo>", mono: true, accent: true },
              {
                text: "Include <repo> and all of its (transitive) dependencies.",
              },
            ],
          },
          {
            cells: [
              { text: "--from A --to B", mono: true, accent: true },
              {
                text: "Include only the projects that lie on a dependency path between A and B.",
              },
            ],
          },
        ],
      )}
      {@render CodeBlock(
        "# Rebuild common-lib and everything that consumes it\npace --from common-lib dotnet build",
      )}
    </div>

    <div id="concept-groups" class="mb-6">
      <h3 class="h4 mb-2">Solution groups</h3>
      <p class="text-sm text-surface-700-300">
        Each project may set a <code class="text-primary-500">sln_group</code>
        (e.g. <em>Libraries</em>, <em>Modules</em>, <em>Apps</em>). Groups are
        purely organizational — the Projects and Git tabs collapse projects by
        group so large graphs stay readable.
      </p>
    </div>

    <div id="concept-profiles">
      <h3 class="h4 mb-2">Config profiles</h3>
      <p class="text-sm text-surface-700-300">
        You can keep multiple config files side-by-side (one per team, branch or
        experiment) under <code class="text-primary-500">~/.pace/configs/</code
        >. The app remembers your last active profile; the CLI selects one with
        <code class="text-primary-500">-C</code>. A built-in
        <code class="text-primary-500">default.toml</code> profile is read-only,
        so its Config Editor tab is hidden.
      </p>
    </div>
  </section>

  <!-- ===================== CLI ===================== -->
  <section id="cli">
    {@render sectionTitle(Terminal, "CLI Reference")}
    {@render CodeBlock("pace [-h] [-C <path>] [OPTIONS] command ...")}

    <div id="cli-global" class="mb-8 mt-4">
      <h3 class="h4 mb-2">Global options</h3>
      <p class="text-sm text-surface-700-300 mb-3">
        These apply to every command and must come before the subcommand.
      </p>
      {@render RefTable(
        ["Option", "Description"],
        [
          {
            cells: [
              { text: "-h, --help", mono: true, accent: true },
              { text: "Show help and exit." },
            ],
          },
          {
            cells: [
              { text: "-v, --version", mono: true, accent: true },
              { text: "Print the version and exit." },
            ],
          },
          {
            cells: [
              { text: "-C, --config <path>", mono: true, accent: true },
              {
                text: "Path to a TOML config. Defaults to the bundled pace.toml.",
              },
            ],
          },
          {
            cells: [
              { text: "--from <repo>", mono: true, accent: true },
              { text: "Start of the dependency chain to operate on." },
            ],
          },
          {
            cells: [
              { text: "--to <repo>", mono: true, accent: true },
              { text: "End of the dependency chain to operate on." },
            ],
          },
          {
            cells: [
              { text: "--debug", mono: true, accent: true },
              { text: "Enable full Python tracebacks on error." },
            ],
          },
          {
            cells: [
              { text: "--print-config", mono: true, accent: true },
              { text: "Print the resolved configuration and exit." },
            ],
          },
          {
            cells: [
              { text: "--print-config-path", mono: true, accent: true },
              { text: "Print the path of the active config file and exit." },
            ],
          },
        ],
      )}
    </div>

    <div id="cli-clean" class="mb-8">
      <h3 class="h4 mb-2"><code class="text-primary-500">pace clean</code></h3>
      <p class="text-sm text-surface-700-300 mb-2">
        Delete build artifacts and cached NuGet packages across the graph, in
        parallel, with a live status table. With <strong
          >no flags it cleans everything</strong
        >; pass flags to scope it.
      </p>
      {@render RefTable(
        ["Flag", "Removes"],
        [
          {
            cells: [
              { text: "--project", mono: true, accent: true },
              { text: "bin/ and obj/ directories for each project." },
            ],
          },
          {
            cells: [
              { text: "--cache", mono: true, accent: true },
              { text: "Matching packages from ~/.nuget/packages." },
            ],
          },
          {
            cells: [
              { text: "--custom-cache", mono: true, accent: true },
              {
                text: "Matching packages from the configured nuget_cache_path.",
              },
            ],
          },
          {
            cells: [
              { text: "-n, --dry-run", mono: true, accent: true },
              {
                text: "Show exactly what would be deleted without removing it.",
              },
            ],
          },
        ],
      )}
      {@render CodeBlock(`# Preview a full clean
pace clean --dry-run

# Only nuke local build output
pace clean --project`)}
    </div>

    <div id="cli-dotnet" class="mb-8">
      <h3 class="h4 mb-2"><code class="text-primary-500">pace dotnet</code></h3>
      <p class="text-sm text-surface-700-300 mb-2">
        PACE generates/syncs a single solution file (<code
          class="text-primary-500">PACE.slnx</code
        >) in the repo root that contains every configured project, then runs
        your
        <code>dotnet</code> subcommand against it. Anything after the subcommand
        is forwarded verbatim to the .NET SDK.
      </p>
      {@render CodeBlock(`# Build the whole solution in Release
pace dotnet build -c Release

# Restore only
pace dotnet restore`)}
      <p class="text-sm text-surface-700-300 mt-2 mb-2">
        <strong>Framework filtering.</strong> When you pass
        <code>-f</code>/<code>--framework</code>, PACE evaluates each project's
        <code>TargetFrameworks</code> (results cached under
        <code class="text-primary-500">~/.pace/cache/</code>) and includes only
        the projects that support that platform:
      </p>
      {@render CodeBlock(
        "# Build only iOS-capable projects\npace dotnet build -f net8.0-ios",
      )}
      <p class="text-xs text-surface-500">
        Recognized platform keywords: <code>ios</code>, <code>android</code>,
        <code>windows</code>, <code>maccatalyst</code>.
      </p>
    </div>

    <div id="cli-git" class="mb-8">
      <h3 class="h4 mb-2"><code class="text-primary-500">pace git</code></h3>
      <p class="text-sm text-surface-700-300 mb-2">
        Run Git operations across every repository that defines a
        <code class="text-primary-500">repo_url</code>, in parallel, with a live
        per-repo status table.
      </p>
      {@render RefTable(
        ["Subcommand", "Action"],
        [
          {
            cells: [
              { text: "clone", mono: true, accent: true },
              { text: "Clone all repos (existing ones are skipped)." },
            ],
          },
          {
            cells: [
              { text: "pull", mono: true, accent: true },
              { text: "Pull the latest changes for all repos." },
            ],
          },
          {
            cells: [
              { text: "checkout <branch>", mono: true, accent: true },
              { text: "Check out <branch> in every cloned repo." },
            ],
          },
        ],
      )}
      {@render CodeBlock(`pace git clone
pace git pull
pace git checkout develop`)}
    </div>

    <div id="cli-upload" class="mb-8">
      <h3 class="h4 mb-2"><code class="text-primary-500">pace upload</code></h3>
      <p class="text-sm text-surface-700-300 mb-2">
        Upload a built app package (<code>.ipa</code>, <code>.apk</code>,
        <code>.msix</code>, <code>.aab</code>) to the deployment server.
      </p>
      {@render RefTable(
        ["Argument", "Required", "Description"],
        [
          {
            cells: [
              { text: "<path-to-app-package>", mono: true, accent: true },
              { text: "yes" },
              { text: "Path to the package file to upload." },
            ],
          },
          {
            cells: [
              { text: "--username", mono: true, accent: true },
              { text: "yes" },
              { text: "Name of the uploader." },
            ],
          },
          {
            cells: [
              { text: "--app-name", mono: true, accent: true },
              { text: "yes" },
              { text: "Application name." },
            ],
          },
          {
            cells: [
              { text: "--platform", mono: true, accent: true },
              { text: "yes" },
              { text: "iOS · Android · Windows." },
            ],
          },
          {
            cells: [
              { text: "--release-type", mono: true, accent: true },
              { text: "yes" },
              { text: "Debug · Release." },
            ],
          },
          {
            cells: [
              { text: "--version", mono: true, accent: true },
              { text: "yes" },
              { text: "Version number or identifier." },
            ],
          },
          {
            cells: [
              { text: "-n, --build-description", mono: true, accent: true },
              { text: "no" },
              { text: "Inline build notes." },
            ],
          },
          {
            cells: [
              {
                text: "-N, --build-description-from-file",
                mono: true,
                accent: true,
              },
              { text: "no" },
              { text: "Read build notes from a file." },
            ],
          },
        ],
      )}
      {@render CodeBlock(
        `pace upload ./MyApp.ipa \\
  --username jane --app-name "MyApp" \\
  --platform iOS --release-type Release --version 1.2.0`,
      )}
      <Callout type="note" message="Prefer the Deploy → Upload tab">
        <p class="text-sm text-surface-700-300">
          The app scans your build output for packages, lets you pick several,
          and uploads them in parallel — building the same
          <code>pace upload</code> command for you. The destination is set by
          the
          <strong>Storage Endpoint URL</strong> in Settings.
        </p>
      </Callout>
    </div>

    <div id="cli-demo">
      <h3 class="h4 mb-2"><code class="text-primary-500">pace demo</code></h3>
      <p class="text-sm text-surface-700-300 mb-2">
        Run built-in Rich rendering demos — handy for verifying terminal output.
      </p>
      {@render CodeBlock(`pace demo columns
pace demo progress_bar`)}
    </div>
  </section>

  <!-- ===================== GUI ===================== -->
  <section id="gui">
    {@render sectionTitle(LayoutGrid, "GUI Guide")}
    <p class="text-sm text-surface-700-300 mb-4">
      The left sidebar switches between panels. Panels that require the CLI stay
      disabled until PACE is installed.
    </p>

    <div id="gui-dependencies" class="mb-6">
      <h3 class="h4 mb-2 flex items-center gap-2">
        <Package size={16} class="text-primary-500" /> Dependencies
      </h3>
      <p class="text-sm text-surface-700-300">
        Detects Python, Git and pipx, shows each version, and installs/updates
        the PACE CLI directly from the app. A red warning badge on the sidebar
        icon means the CLI is not yet available.
      </p>
    </div>

    <div id="gui-graph" class="mb-6">
      <h3 class="h4 mb-2 flex items-center gap-2">
        <Network size={16} class="text-primary-500" /> Project Graph
      </h3>
      <p class="text-sm text-surface-700-300">
        An interactive node-link diagram of the active config's dependency
        graph, laid out automatically. Use it to sanity-check
        <code>depends_on</code> relationships before running chained commands.
      </p>
    </div>

    <div id="gui-build-props" class="mb-6">
      <h3 class="h4 mb-2 flex items-center gap-2">
        <FileCode size={16} class="text-primary-500" /> Directory.Build.props editor
      </h3>
      <p class="text-sm text-surface-700-300 mb-2">
        Create and manage MSBuild properties shared by every project in a
        directory tree, then write them to a
        <code class="text-primary-500">Directory.Build.props</code> file.
      </p>
      <ul class="text-sm text-surface-700-300 list-disc list-inside space-y-1">
        <li><strong>Add / Edit / Delete</strong> name–value property pairs.</li>
        <li><strong>Search</strong> to filter long property lists.</li>
        <li><strong>Save / Load</strong> the file in the target directory.</li>
        <li>
          <strong>XML Preview</strong> with <strong>Copy XML</strong> to clipboard.
        </li>
      </ul>
    </div>

    <div id="gui-orchestrator" class="mb-6">
      <h3 class="h4 mb-2 flex items-center gap-2">
        <Cog size={16} class="text-primary-500" /> Orchestrator
      </h3>
      <p class="text-sm text-surface-700-300 mb-3">
        The control center. Pick a config profile in the header (refresh or open
        its folder with the adjacent buttons), then work across these tabs. A
        spinning sidebar icon indicates a build or deploy is running.
      </p>
      {@render RefTable(
        ["Tab", "What it does"],
        [
          {
            cells: [
              { text: "Projects", accent: true },
              {
                text: "Repo root, NuGet cache path and a grouped overview of every project; open any folder in your file manager.",
              },
            ],
          },
          {
            cells: [
              { text: "NuGet", accent: true },
              {
                text: "Inspect configured NuGet sources and browse packages in the global and custom caches.",
              },
            ],
          },
          {
            cells: [
              { text: "Git", accent: true },
              {
                text: "Clone / Pull all repos, refresh statuses, and see per-repo branch, ahead/behind and uncommitted state by group.",
              },
            ],
          },
          {
            cells: [
              { text: "Build", accent: true },
              {
                text: "Run dotnet builds with config/framework/no-restore options, a live command preview, progress bar and output log.",
              },
            ],
          },
          {
            cells: [
              { text: "Deploy", accent: true },
              {
                text: "Publishing, Upload and Code signing sub-sections (see below).",
              },
            ],
          },
          {
            cells: [
              { text: "Config editor", accent: true },
              {
                text: "Edit the active profile (repodir, NuGet cache, groups, projects and dependencies). Hidden for the read-only default profile.",
              },
            ],
          },
        ],
      )}
      <p class="text-sm font-semibold text-surface-900-100 mt-4 mb-1">
        Deploy sub-sections
      </p>
      {@render RefTable(
        ["Section", "Purpose"],
        [
          {
            cells: [
              { text: "Publishing", accent: true },
              {
                text: "Select a project + platforms (iOS/Android/Windows), build config and MSBuild props, then dotnet publish with the right runtime, framework and signing args. Live progress per platform.",
              },
            ],
          },
          {
            cells: [
              { text: "Upload", accent: true },
              {
                text: "Auto-scans build output for .ipa/.apk/.msix packages, then uploads selected ones in parallel via pace upload.",
              },
            ],
          },
          {
            cells: [
              { text: "Code signing", accent: true },
              {
                text: "Manage signing identities per platform — iOS bundle IDs (key + provision), Windows cert thumbprints, Android keystores. Saved to ~/.pace/codesigning.json; import existing files.",
              },
            ],
          },
        ],
      )}
      <Callout type="tip" message="Wildcard signing defaults">
        <p class="text-sm text-surface-700-300">
          In Code signing, the <code class="text-primary-500">*</code> entry is the
          default applied to any bundle ID / certificate / keystore that has no explicit
          match — set it once and only override the exceptions.
        </p>
      </Callout>
    </div>

    <div id="gui-console" class="mb-6">
      <h3 class="h4 mb-2 flex items-center gap-2">
        <Terminal size={16} class="text-primary-500" /> Console
      </h3>
      <p class="text-sm text-surface-700-300">
        An embedded terminal for ad-hoc commands with command history (<kbd
          class="px-1 rounded bg-surface-200-800 text-xs">↑</kbd
        >/<kbd class="px-1 rounded bg-surface-200-800 text-xs">↓</kbd>), ANSI
        color rendering, optional timestamps, a configurable working directory,
        and the ability to copy or export the log.
      </p>
    </div>

    <div id="gui-settings" class="mb-6">
      <h3 class="h4 mb-2 flex items-center gap-2">
        <Settings size={16} class="text-primary-500" /> Settings
      </h3>
      <ul class="text-sm text-surface-700-300 list-disc list-inside space-y-1">
        <li>
          <strong>General</strong> — application language and auto-check-for-updates
          on startup.
        </li>
        <li>
          <strong>Appearance</strong> — Light / Dark / System theme and base font
          size.
        </li>
        <li>
          <strong>Storage</strong> — the Application Storage Endpoint URL used by
          uploads.
        </li>
      </ul>
      <p class="text-xs text-surface-500 mt-2">
        Settings auto-save as you change them; <strong>Reset to default</strong>
        is in the header.
      </p>
    </div>

    <div id="gui-updates">
      <h3 class="h4 mb-2 flex items-center gap-2">
        <Download size={16} class="text-primary-500" /> Updates
      </h3>
      <p class="text-sm text-surface-700-300">
        Shows the installed and latest versions of both the PACE CLI and the
        app, and lets you update. The sidebar icon carries a green check when
        you're up to date, or a warning badge when an update is available.
      </p>
    </div>
  </section>

  <!-- ===================== CONFIG ===================== -->
  <section id="config">
    {@render sectionTitle(FileCog, "Configuration")}

    <div id="config-location" class="mb-6">
      <h3 class="h4 mb-2">File location</h3>
      <p class="text-sm text-surface-700-300">
        Config files are TOML. The app stores profiles in
        <code class="text-primary-500">~/.pace/configs/*.toml</code> and you can
        create, duplicate, rename, import or delete them from the config picker.
        The CLI uses <code class="text-primary-500">-C &lt;path&gt;</code>,
        falling back to a bundled <code>pace.toml</code> when omitted.
      </p>
    </div>

    <div id="config-structure" class="mb-6">
      <h3 class="h4 mb-2">Structure</h3>
      {@render CodeBlock(`repodir = "/path/to/repos"
nuget_cache_path = "/path/to/nuget-packages"   # optional

[[projects]]
name = "common-lib"
csproj_path = "src/CommonLib/CommonLib.csproj"
repo_url = "git@github.com:org/common-lib.git"  # optional
sln_group = "Libraries"                          # optional
explicit_frameworks = []
depends_on = ["versioning-lib"]

[[projects]]
name = "my-app"
csproj_path = "src/MyApp/MyApp.csproj"
repo_url = "git@github.com:org/my-app.git"
sln_group = "Apps"
depends_on = ["common-lib"]

[[build-props]]
name = "GeneratePackageOnBuild"
datatype = "boolean"
default = false`)}
    </div>

    <div id="config-fields" class="mb-6">
      <h3 class="h4 mb-2">Field reference</h3>
      <p class="text-sm font-semibold text-surface-900-100 mb-1">Top level</p>
      {@render RefTable(
        ["Field", "Type", "Description"],
        [
          {
            cells: [
              { text: "repodir", mono: true, accent: true },
              { text: "string" },
              {
                text: "Root directory where repositories are cloned. Created if missing.",
              },
            ],
          },
          {
            cells: [
              { text: "nuget_cache_path", mono: true, accent: true },
              { text: "path?" },
              {
                text: "Custom NuGet cache, used by clean --custom-cache and the NuGet tab.",
              },
            ],
          },
        ],
      )}
      <p class="text-sm font-semibold text-surface-900-100 mb-1 mt-4">
        [[projects]]
      </p>
      {@render RefTable(
        ["Field", "Type", "Description"],
        [
          {
            cells: [
              { text: "name", mono: true, accent: true },
              { text: "string" },
              {
                text: "Project identifier; also the subdirectory under repodir.",
              },
            ],
          },
          {
            cells: [
              { text: "csproj_path", mono: true, accent: true },
              { text: "string" },
              { text: "Path to the .csproj relative to the project's repo." },
            ],
          },
          {
            cells: [
              { text: "repo_url", mono: true, accent: true },
              { text: "string?" },
              { text: "Git remote; required for clone / pull / checkout." },
            ],
          },
          {
            cells: [
              { text: "sln_group", mono: true, accent: true },
              { text: "string?" },
              { text: "Grouping label used to organize the UI." },
            ],
          },
          {
            cells: [
              { text: "explicit_frameworks", mono: true, accent: true },
              { text: "string[]" },
              {
                text: "Force specific target frameworks (overrides detection).",
              },
            ],
          },
          {
            cells: [
              { text: "depends_on", mono: true, accent: true },
              { text: "string[]" },
              {
                text: "Names of projects this one depends on — defines the graph.",
              },
            ],
          },
        ],
      )}
      <p class="text-sm font-semibold text-surface-900-100 mb-1 mt-4">
        [[build-props]]
      </p>
      {@render RefTable(
        ["Field", "Type", "Description"],
        [
          {
            cells: [
              { text: "name", mono: true, accent: true },
              { text: "string" },
              { text: "MSBuild property name (e.g. GeneratePackageOnBuild)." },
            ],
          },
          {
            cells: [
              { text: "datatype", mono: true, accent: true },
              { text: "string" },
              {
                text: '"boolean" · "string" · "path" — controls the input widget.',
              },
            ],
          },
          {
            cells: [
              { text: "default", mono: true, accent: true },
              { text: "bool/str/path" },
              { text: "Default value, pre-filled in the Publishing tab." },
            ],
          },
        ],
      )}
    </div>

    <div id="config-env">
      <h3 class="h4 mb-2">Environment variables</h3>
      {@render RefTable(
        ["Variable", "Effect"],
        [
          {
            cells: [
              { text: "REPODIR", mono: true, accent: true },
              { text: "Overrides repodir from the config file at runtime." },
            ],
          },
        ],
      )}
    </div>
  </section>

  <!-- ===================== WORKFLOWS ===================== -->
  <section id="workflows">
    {@render sectionTitle(Workflow, "Common Workflows")}

    <p class="text-sm font-semibold text-surface-900-100 mb-1">
      Fresh checkout → Release build
    </p>
    {@render CodeBlock(`pace git clone
pace dotnet build -c Release`)}

    <p class="text-sm font-semibold text-surface-900-100 mb-1 mt-4">
      Rebuild only what changed in a library
    </p>
    {@render CodeBlock(`pace clean --project --from common-lib
pace --from common-lib dotnet build -c Release`)}

    <p class="text-sm font-semibold text-surface-900-100 mb-1 mt-4">
      Free up disk space
    </p>
    {@render CodeBlock(`pace clean --dry-run   # review first
pace clean             # then remove artifacts + caches`)}

    <p class="text-sm font-semibold text-surface-900-100 mb-1 mt-4">
      Switch every repo to a feature branch
    </p>
    {@render CodeBlock("pace git checkout feature/new-maps")}
  </section>

  <!-- ===================== LOCATIONS ===================== -->
  <section id="locations">
    {@render sectionTitle(FolderTree, "Files & Caches")}
    {@render RefTable(
      ["Path", "Contents"],
      [
        {
          cells: [
            { text: "~/.pace/configs/", mono: true, accent: true },
            { text: "Your saved configuration profiles (*.toml)." },
          ],
        },
        {
          cells: [
            { text: "~/.pace/codesigning.json", mono: true, accent: true },
            { text: "Per-platform code signing identities." },
          ],
        },
        {
          cells: [
            {
              text: "~/.pace/cache/dotnet_cache.json",
              mono: true,
              accent: true,
            },
            { text: "Cached TargetFrameworks for fast framework filtering." },
          ],
        },
        {
          cells: [
            { text: "<repodir>/PACE.slnx", mono: true, accent: true },
            {
              text: "Auto-generated solution containing all configured projects.",
            },
          ],
        },
        {
          cells: [
            { text: "~/.nuget/packages", mono: true, accent: true },
            { text: "Global NuGet cache targeted by clean --cache." },
          ],
        },
      ],
    )}
  </section>

  <!-- ===================== TROUBLESHOOTING ===================== -->
  <section id="troubleshooting">
    {@render sectionTitle(LifeBuoy, "Troubleshooting")}

    <Callout type="warning" message="Panels are greyed out">
      <p class="text-sm text-surface-700-300">
        The PACE CLI isn't detected. Open <strong>Dependencies</strong>, resolve
        any missing prerequisites, then install PACE. A warning badge on the
        package icon confirms this state.
      </p>
    </Callout>

    <div class="mt-3">
      <Callout type="warning" message="git clone / pull fails">
        <p class="text-sm text-surface-700-300">
          Verify each <code>repo_url</code> and that your SSH keys or credentials
          are configured. The failing repositories and their error messages are listed
          at the end of the run.
        </p>
      </Callout>
    </div>

    <div class="mt-3">
      <Callout type="warning" message="A build skips projects unexpectedly">
        <p class="text-sm text-surface-700-300">
          Framework filtering relies on cached <code>TargetFrameworks</code>. If
          a project's frameworks changed, the cache key (file mtime) refreshes
          automatically — but you can delete
          <code class="text-primary-500">~/.pace/cache/dotnet_cache.json</code> to
          force a rebuild of the cache.
        </p>
      </Callout>
    </div>

    <div class="mt-3">
      <Callout type="note" message="Get a full error trace">
        <p class="text-sm text-surface-700-300">
          Re-run any CLI command with <code class="text-primary-500"
            >--debug</code
          >
          to see the complete Python traceback, and
          <code class="text-primary-500">--print-config</code> to confirm which projects
          PACE actually resolved.
        </p>
      </Callout>
    </div>
  </section>

  <!-- ===================== RESOURCES ===================== -->
  <section id="resources">
    {@render sectionTitle(LinkIcon, "Resources")}
    <div class="flex flex-col gap-2">
      <button
        class="btn preset-tonal justify-start gap-2 hover:preset-filled-primary-500 transition-colors w-fit"
        onclick={() => openExternal(REPO_URL)}
      >
        <LinkIcon size={16} /> GitHub repository
      </button>
      <button
        class="btn preset-tonal justify-start gap-2 hover:preset-filled-primary-500 transition-colors w-fit"
        onclick={() => openExternal(`${REPO_URL}/issues`)}
      >
        <LifeBuoy size={16} /> Report an issue
      </button>
    </div>
    <p class="text-xs text-surface-500 mt-4">
      PACE {version} · Project Automation and Configuration Engine · MIT License
    </p>
  </section>
</div>
