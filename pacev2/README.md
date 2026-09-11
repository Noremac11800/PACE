# PACE v2

A Typer CLI for the Project Automation and Configuration Engine, using uv, Ruff,
ty, and pytest. Configuration handling, version reporting, and parallel Git
commands are implemented; other project operations remain placeholders.

## Run

From the repository root:

```powershell
Set-Location pacev2
uv run pacev2 --help
uv run pacev2 --version
uv run pacev2 clean --help
uv run python -m pacev2 --help
```

No arguments, `-h`, and `--help` display help. With no subcommand, `-v` and
`--version` print `pacev2 <version>` and exit successfully. The version comes from
installed package metadata generated from `project.version` in `pyproject.toml`,
with no network requests or configuration loading.

`clean`, `dotnet`, `upload`, `update`, and `--debug` remain placeholders. These
commands report **not implemented** and exit with code 1 after any requested
configuration processing.

## Configuration

`-C` / `--config` selects a TOML file and remembers it in
`~/.pace/settings.json`, sharing the original PACE history. A bare filename is
looked up in the current directory first, then `~/.pace/configs`. Explicit paths
may be absolute, relative, or home-relative.

Without `--config`, PACE uses the last active file. If there is no history, or the
remembered file cannot be accessed, it uses `~/.pace/configs/template.toml`,
creating an editable copy of the bundled template if necessary. Existing copies
are never overwritten. The template lives in `src/pacev2/data/template.toml` so it
is included in installations. `data/applications-melbourne.toml` is only an
example: it is neither selected automatically nor bundled.

An explicitly selected missing or invalid config is an error, not a reason to
silently fall back. A malformed remembered config also reports an error.
Unreadable or malformed history produces a warning and is left untouched;
failures to save history are reported as warnings.

`--print-config` prints the parsed, filtered model as indented JSON, including
projects, solution groups, and build properties. `--print-config-path` prints
the absolute source filename. When both are given, the path is printed first.
Both validate the same selection and filters; filtering changes the in-memory
projects, not the source file or its path.

```powershell
uv run pacev2 --print-config-path
uv run pacev2 -C .\my-config.toml --print-config
uv run pacev2 --from common-lib --to application --print-config
```

`--from NAME` includes that project and all its transitive dependents;
`--to NAME` includes that project and all its transitive dependencies. Together
they include projects on dependency paths from `NAME` to the target. Endpoints
are inclusive, names are case-sensitive, and declaration order is preserved.
Disconnected endpoints produce an empty project list. Dependency declarations
are retained even when an upstream project falls outside the selected range.
Filters are not saved in history and never rewrite the TOML.

The Pydantic model accepts `repodir`, `nuget_cache_path`, `projects`, and
`build-props`. Each project has a name and `csproj_path`, with optional
`repo_url`, `sln_group`, and `depends_on`. Build properties have a name,
`datatype` (`boolean`, `string`, or `path`), and a default value. Unknown fields,
duplicate project names, missing dependencies, and dependency cycles are errors.

Path fields accept either `/` or `\` separators and expand `~`. This includes
path-valued build-property defaults; an empty default stays empty. Relative paths
remain relative, and parsing does not create repository or cache directories.
Use TOML literal strings for Windows paths (`'C:\Repositories'`) or escape
backslashes inside double quotes (`"C:\\Repositories"`). Separator normalization
does not map Windows drive letters to Unix mount points.

`clean`, `dotnet`, and `git` receive the filtered `Config` through the Typer
context. Print flags can also precede these commands. `upload` loads configuration
only when global config options are
provided, while `update` bypasses them, matching the original CLI. PACE's own help and
standalone version reporting never load or initialize configuration.

## Parallel Git commands

Git runs against the active, filtered project list in parallel. Each checkout
lives at `repodir/<project-name>`; the configured project name, not the URL's
basename, determines its directory.

```powershell
uv run pacev2 git status
uv run pacev2 git clone
uv run pacev2 git clone --branch main --depth 1
uv run pacev2 git pull --ff-only
uv run pacev2 git checkout main
uv run pacev2 --from common-lib --to application git status --short
uv run pacev2 git -c alias.recent="log -5 --oneline" recent
```

Subcommands, aliases, options, and their values are forwarded as individual
arguments, without a shell or a command allowlist. For bulk `clone`, provide only
clone options: PACE appends each project's `repo_url` and absolute destination.
Already-cloned projects are skipped; an existing empty directory can be cloned
into, while Git reports an error for a non-empty, non-repository destination.

A project without a non-empty `repo_url` is skipped with a warning. For commands
other than `clone`, a missing checkout is also skipped with a warning to clone
first. An existing directory that is not a Git checkout is an error: PACE will
not accidentally run Git against an enclosing repository.

The Rich table shows queued, running, succeeded, failed, and skipped projects,
along with their latest output. Complete stdout/stderr follows the final table,
grouped in config order, including failures and exit codes. A failed command or
process-launch error makes PACE exit with code 1 after the other projects finish.
Warnings and skips alone do not fail the invocation.

This is a non-interactive batch runner: stdin, Git credential prompts, pagers,
and commit/rebase editors are disabled. Configure authentication beforehand and
provide non-interactive arguments such as `commit -m "message"` or `--no-edit`.
Commands that require interactive input are not suitable for parallel execution.

`pacev2 git -h` / `--help` shows PACE's Git help. Help flags following Git
arguments are forwarded, so `pacev2 git status -h` asks Git for status help.
Use `pacev2 git -- --help` to forward a leading help flag to Git itself.

`execution.py` supplies the reusable task runner and streaming subprocess helper;
other project commands can reuse its reporting and failure aggregation.

## CLI parity

The executable remains `pacev2`, so it can coexist with the original `pace`.
Global options precede the command:

| Option | Value |
| --- | --- |
| `--debug` | Flag |
| `-C`, `--config` | Configuration file path |
| `--print-config` | Flag |
| `--print-config-path` | Flag |
| `-v`, `--version` | Flag |
| `--from` | Starting repository name |
| `--to` | Ending repository name |

| Command | Arguments and options |
| --- | --- |
| `clean` | `--cache`, `--custom-cache`, `--project`, `-n` / `--dry-run` |
| `dotnet` | `-w` / `--summarize-warnings`, followed by dotnet arguments |
| `git` | Git arguments, such as `pull`, `clone`, or `checkout main` |
| `upload` | Package path; required `--username`, `--app-name`, `--platform`, `--release-type`, `--version`, `--endpoint`; optional `-n` / `--build-description`, `-N` / `--build-description-from-file` |
| `demo` | `columns` or `progress_bar`, followed by demo arguments |
| `update` | No command-specific options |

Upload platform choices are `iOS`, `Android`, and `Windows`; release types are
`Debug` and `Release`. Choices are case-sensitive, matching `pace`.

`dotnet`, `git`, and `demo` accept trailing tool or demo arguments. For example,
`dotnet -w build -c Release` parses the PACE warning-summary flag, while
`dotnet build -w` leaves `-w` in the dotnet arguments. Git forwards all arguments
after the initial wrapper help position; demo invocations still recognize
`-h` / `--help` after their arguments.
The `columns` demo accepts a directory path after its name.

`init`, `test`, and `format` are not exposed because the original CLI does not
register those modules. Typer supplies its standard help layout and usage errors;
this scaffold does not reproduce argparse's silent handling of unrelated unknown
options.

## Development

From `pacev2`:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```