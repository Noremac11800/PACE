# PACE Desktop

A desktop-only Tauri 2 / Svelte 5 app for `pacev2`, using the Survey123 design
system. The original `app/` is unchanged; this app uses the `pacev2` CLI.

## Development

Install the [Tauri desktop prerequisites](https://v2.tauri.app/start/prerequisites/),
Python 3.13+, uv, and Bun. From the PACE repository root:

```sh
uv sync --project pacev2
cd app2
bun install
bun run tauri dev
```

The development build detects `../pacev2/.venv` (including the Windows
`Scripts/python.exe` layout). The frontend uses port **1420**. `bun run dev`
alone is an explicitly disconnected browser preview; it cannot access local
configurations or run commands.

For packaged builds, install pacev2 into a Python environment, then choose that
environment's **Python executable** under Settings. PACE invokes
`python -m pacev2`, never the legacy `pace` command. The interpreter and working
directory are saved locally. Python and pacev2 are not bundled in the installer.

```sh
bun run tauri build
```

## Supported workflows

- Open existing TOML files, create configurations, and save copies.
- Edit the original TOML without losing comments or formatting. Validate and
  save using the actual pacev2 Pydantic models. Invalid input and external file
  changes prevent saving. Copies never overwrite existing files.
- Add, edit, and delete build properties and change workspace paths using
  form editors that update the same TOML draft.
- Browse and search repositories, inspect solution groups and project details,
  reveal checkout folders, and explore dependency layers.
- Select inclusive `--from` / `--to` ranges, resolved by pacev2 itself.
- Run parallel Git status, clone, fast-forward pull, or custom Git arguments.
  Mutating presets and custom commands require confirmation. Arguments are
  passed without a shell; Git remains non-interactive.
- Run solution-based dotnet builds, tests, restores, packs, publishes, cleans,
  and custom commands with configuration/framework options and warning summaries.
- Stream command output, inspect exit codes, copy results, and run CLI help,
  version, and configuration-printing commands.
- Use `--monitor` automatically for Git and dotnet commands. Each operation
  workspace owns its live results; starting or finishing a command never changes views.
- Switch between system, light, and dark themes; inspect runtime/tool versions.

The separate PACE clean, upload, and update commands remain unimplemented. The
**Clean** task in .NET operations runs `pacev2 dotnet clean`, not `pacev2 clean`.
Build properties can be passed as explicit command-line overrides; no project
files or `Directory.Build.props` files are rewritten.

Configuration history is shared with the CLI in `~/.pace/settings.json`. Relative
configuration paths resolve against the configured working directory (the home
directory by default), **not** the TOML file's parent directory. The resolved
repository root is visible in the UI. Opening a config may initialize the CLI's
standard editable template, just as running pacev2 does.

Configuration edits survive navigation between views. Switching configurations,
reloading, reconnecting, or closing prompts before discarding edits. Commands
require saved, unchanged-on-disk configuration. Scope applies to Git, dotnet, and
configuration-print commands; table search/group filters are display-only.
Commands run one at a time and must finish before closing the app. Session
history retains 20 commands and the last 250,000 output characters per command;
truncation is explicitly marked. History is not persisted after closing.

## Configuration editing

**Build properties** supports adding, renaming, changing the type/default, and
deleting properties. String and path defaults may be empty; boolean defaults have
a true/false selector, and path defaults have a directory picker. Property names
must be unique, ignoring case. Deletion asks for confirmation.

**Workspace paths** edits the repository directory and optional NuGet cache.
Clear the cache field to use NuGet's default cache. Resolved paths reflect the
current draft and CLI working directory. Editing paths does not move any files.
The separate **Change working directory** action saves a device-wide runtime
setting and reconnects, retaining the active configuration. Save or discard any
configuration edits before changing this runtime setting.

Choose **Apply to draft** in a form, then **Save changes** (or **Save a copy**) to
write the file. Cancel leaves the draft untouched. Forms and TOML source share
the same draft, which survives navigation. Invalid source must be repaired in
the source editor before using forms. The desktop adapter uses `tomlkit` (included
in the updated pacev2 dependencies) to preserve unrelated comments and formatting;
it still uses pacev2's models for validation and existing file-conflict safeguards.
Saving changed or deleted property definitions clears their .NET command overrides;
unchanged definitions retain their overrides and other command options.

## Operation workspaces

The layout follows the original app's in-place operation workflow, without
duplicating its CLI or inferring progress from terminal output.

**Git operations** puts Check status, Clone missing, and Pull latest in a compact
toolbar. Repositories are grouped by solution group, including an Ungrouped
section. Select a repository to see its own streamed output and operation status;
these statuses describe the command, not an inferred clean/dirty working tree.
Custom Git arguments are available in an expandable section and survive navigation,
as does the selected repository. The full command log remains available below.

**.NET operations** keeps command options in a left column and the current/last
run, live project-stage matrix, and log in the right column. MSBuild properties
are expandable, leaving common controls readily accessible. Missing stage events
are shown as not reported, rather than invented progress. Restore/Pack/Clean and
other commands without project events still show their live output in place.

Git and .NET each have their own recent-command selector. A run captures its
configuration, selected repositories, dependency range, and executed command.
Changing options or scope prepares the **next** command; it does not relabel
existing results. Results from another configuration do not appear in the active
workspace. A navigation indicator and a clickable running-command footer let you
return to an operation after navigating elsewhere, without automatic tab changes.

**Command history** is a secondary archive and home for CLI help, version, config,
and SDK-information tools. Opening an archived run in its matching workspace is
explicit. Clearing history also clears inline results, without resetting form
options. In addition to the shared output limit, Git's repository-specific logs
share a 250,000-character buffer per command; truncation is marked.

## .NET operations

Requires the updated pacev2 module and .NET SDK **9.0.200 or newer**, with any
SDKs/workloads your projects need. Check availability in Settings, or run
**.NET SDK information** from Command history.

The form supports Build, Test, Restore, Pack, Publish, Clean, and Custom command.
Choose Debug/Release, an optional target framework, and the options supported by
that task. Restore uses `-p:Configuration=...`; it does not receive build-only
`-f` or `--no-restore` switches. Pack does not receive `-f`.

**Rebuild all outputs** adds `-t:Rebuild` rather than deleting `bin`/`obj` manually
or calling the unimplemented PACE clean command. It is useful with **Summarize
build warnings**, which places `-w` before the dotnet subcommand. Summaries and
the log filename appear beside the .NET options; pacev2 writes the log under
`~/.pace/logs`. Incremental builds may not re-emit existing compiler warnings.

Configured MSBuild properties are opt-in. Enable a property to pass its value
(including a configured default, `false`, or an empty string) as `-p:Name=Value`.
Path properties have a directory picker. These overrides affect only the command,
not the TOML or project files. MSBuild delimiters in form property values are
escaped; additional/custom arguments are forwarded as entered, with quote-aware
argument splitting and no shell.

Additional arguments are appended after form options. Custom mode accepts the
arguments after `dotnet` and ignores the hidden structured form settings, except
the warning-summary switch. Do not supply a project/solution target: pacev2
supplies `PACE.slnx`. Rebuild, Clean, Publish, custom commands, and commands with
additional arguments require confirmation.

Options and results survive navigation during the session.
Reset options restores defaults; changing the active config resets options and
property overrides. Configuration edits must be saved before execution.
The shared runner uses pacev2's versioned JSON Lines monitor protocol. The .NET
workspace shows queued/running/succeeded/failed/skipped/incomplete projects, plus
observed restore, compile, build, publish, and test stages for build/publish/test.
Stage counts update while the command runs, even at quiet verbosity. Referenced
projects discovered by MSBuild appear too. Projects remain in progress until
command completion because another framework or target can still fail. Stages
describe MSBuild targets, not individual tests or a guessed percentage.

Human-readable logs, stderr, warning summaries, and the actual process exit code
remain available beneath the progress table; Copy output copies the readable log,
not JSON envelopes. Progress survives log truncation and stays with each command
in session history. Broken/unsupported event streams and unexpected process exits
are reported explicitly; unfinished projects are marked incomplete.

Use an updated pacev2 installation with `--monitor` support. The first monitored
.NET build/publish/test compiles a small bundled MSBuild logger locally and caches
it under `~/.pace/cache/msbuild-monitor`; no NuGet package downloads are needed.
MSBuild-based `dotnet test` is supported, not the Microsoft.Testing.Platform CLI
mode. Other dotnet tasks retain streamed logs without fabricated project stages.
Commands must finish before the app closes.

The selected range determines the direct members of `PACE.slnx`. MSBuild may
also build project references outside that range; it owns dependency ordering
and parallelism. Search/group filters in the repository table do not affect it.

## Structure

| Location                                   | Responsibility                                             |
| ------------------------------------------ | ---------------------------------------------------------- |
| `src/lib/components/ui/`                   | Copied Survey123 primitives, with English labels           |
| `src/lib/styles/`, `src/lib/assets/fonts/` | Original semantic tokens, type scale, and fonts            |
| `src/lib/views/`                           | Focused desktop feature views                              |
| `src/lib/state/app.svelte.ts`              | Workspace, scope, command lifecycle, and notifications     |
| `src/lib/services/desktop.ts`              | Typed Tauri boundary and native dialogs                    |
| `src/lib/domain/`                          | Types, argument parsing, and dependency-layer presentation |
| `src-tauri/src/runtime.rs`                 | Python process invocation and streamed output              |
| `src-tauri/bridge.py`                      | Small adapter around pacev2 config models and history      |

The Python adapter is embedded into the Rust binary; it imports the installed
pacev2 package rather than duplicating its validation or filtering rules.
Frontend components do not spawn processes directly.

### Design system

Buttons, inputs, labels, chips, cards, tabs, dialogs, spinners, switches, checkboxes, theme controls,
semantic color tokens, and Avenir Next typography were copied from
`Survey123-tauri`. There is no runtime dependency on that checkout and no i18n
dependency. The copied font assets retain the reference project's licensing;
ensure your distribution is covered by those font licenses.

Calcite icons use the reference app's SVG sprite approach. Add icon names to
`scripts/generate-icons.js`, then run `bun run icons`. Only the used subset is
bundled; generated files are also refreshed by `bun install`.

Application artwork lives in `static/`: `appglyph-dark.svg` is the dark-colored
glyph for light backgrounds, `appglyph.svg` is the white glyph for dark
backgrounds, and `appicon.svg` supplies the favicon. Native desktop icons under
`src-tauri/icons/` are generated from `appicon.svg` with Tauri's icon generator.

## Checks

From `app2`:

```sh
bun run check
bun run test
bun run test:ui
bun run build
cargo check --manifest-path src-tauri/Cargo.toml
cargo test --manifest-path src-tauri/Cargo.toml --lib
../pacev2/.venv/bin/python -m unittest discover -s src-tauri/tests -v
```

On Windows, use `../pacev2/.venv/Scripts/python.exe` for the final command. Python
tests use temporary directories and isolated configuration history.
UI tests use installed Google Chrome and a test-only IPC transport that runs real
pacev2 commands against temporary repositories. Dotnet UI tests also require a
compatible installed .NET SDK and compile temporary class libraries with intentional
warnings. They do not modify your workspace
or `~/.pace` history.
