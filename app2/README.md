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
- Stream command output, inspect exit codes, copy results, and run CLI help,
  version, and configuration-printing commands.
- Switch between system, light, and dark themes; inspect runtime/tool versions.

Build, clean, NuGet management, publishing, uploading, and updates are
deliberately not presented as working features: pacev2 has not implemented those
operations. Build properties are editable in TOML and viewable in the UI, but
are not applied to project files.

Configuration history is shared with the CLI in `~/.pace/settings.json`. Relative
configuration paths resolve against the configured working directory (the home
directory by default), **not** the TOML file's parent directory. The resolved
repository root is visible in the UI. Opening a config may initialize the CLI's
standard editable template, just as running pacev2 does.

Configuration edits survive navigation between views. Switching configurations,
reloading, reconnecting, or closing prompts before discarding edits. Commands
require saved, unchanged-on-disk configuration. Scope applies to Git and
configuration-print commands; table search/group filters are display-only.
Commands run one at a time and must finish before closing the app. Session
history retains 20 commands and the last 250,000 output characters per command;
truncation is explicitly marked. History is not persisted after closing.

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

Buttons, inputs, labels, chips, cards, tabs, dialogs, spinners, theme controls,
semantic color tokens, and Avenir Next typography were copied from
`Survey123-tauri`. There is no runtime dependency on that checkout and no i18n
dependency. The copied font assets retain the reference project's licensing;
ensure your distribution is covered by those font licenses.

Calcite icons use the reference app's SVG sprite approach. Add icon names to
`scripts/generate-icons.js`, then run `bun run icons`. Only the used subset is
bundled; generated files are also refreshed by `bun install`.

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
pacev2 commands against temporary repositories. They do not modify your workspace
or `~/.pace` history.
