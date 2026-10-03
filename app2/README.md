# PACE Desktop

A desktop-only Tauri 2 / Svelte 5 app for `pacev2`, using the Survey123 design
system. The original `app/` and the Python CLI are unchanged.

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

## .NET operations

Requires the updated pacev2 module and .NET SDK **9.0.200 or newer**, with any
SDKs/workloads your projects need. Check availability in Settings, or run
**.NET SDK information** from Command activity.

The form supports Build, Test, Restore, Pack, Publish, Clean, and Custom command.
Choose Debug/Release, an optional target framework, and the options supported by
that task. Restore uses `-p:Configuration=...`; it does not receive build-only
`-f` or `--no-restore` switches. Pack does not receive `-f`.

**Rebuild all outputs** adds `-t:Rebuild` rather than deleting `bin`/`obj` manually
or calling the unimplemented PACE clean command. It is useful with **Summarize
build warnings**, which places `-w` before the dotnet subcommand. Summaries and
the log filename appear in Command activity; pacev2 writes the log under
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

Options survive navigation to Command activity and back during the session.
Reset options restores defaults; changing the active config resets options and
property overrides. Configuration edits must be saved before execution.
The shared runner streams output and reports the actual exit code without
inventing a build-progress percentage. Commands must finish before the app closes.

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
