# PACE v2

A bare-bones Typer CLI for the Project Automation and Configuration Engine, using
uv, Ruff, ty, and pytest. It mirrors the command-line interface currently registered
in `pace`, without porting its implementations.

## Run

From the repository root:

```powershell
Set-Location pacev2
uv run pacev2 --help
uv run pacev2 clean --help
uv run python -m pacev2 --help
```

No arguments, `-h`, and `--help` display help. Commands and global options are
placeholders: they report **not implemented** and exit with code 1. Typer validates
argument types, required values, and choices, but nothing loads configuration,
reads build notes, deletes files, runs external commands, contacts servers, checks
versions, or installs updates. In particular, `--version` is also a placeholder.

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