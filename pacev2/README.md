# PACE v2

A Typer CLI for the Project Automation and Configuration Engine, using uv, Ruff,
ty, and pytest. Configuration handling and version reporting are implemented;
project operations remain placeholders.

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

Commands and `--debug` remain placeholders. Commands report **not implemented**
and exit with code 1 after any requested configuration processing. Nothing reads
build notes, deletes project files, runs external commands, contacts servers,
checks for newer versions, or installs updates.

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
context; their operations are still stubs. Print flags can also precede these
commands. `upload` loads configuration only when global config options are
provided, while `update` bypasses them, matching the original CLI. Help and
standalone version reporting never load or initialize configuration.

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
`dotnet build -w` leaves `-w` in the dotnet arguments. Git and demo invocations
still recognize `-h` / `--help` after their arguments, matching the original CLI.
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