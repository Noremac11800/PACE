# PACE v2

A Typer CLI for the Project Automation and Configuration Engine, using uv, Ruff,
ty, and pytest. Configuration handling, version reporting, parallel Git commands,
and solution-based dotnet commands are implemented.

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

`clean`, `upload`, `update`, and `--debug` remain placeholders. These
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

## Machine-readable progress

Put the global `--monitor` option **before** the command:

```sh
pacev2 --monitor git status
pacev2 -C workspace.toml --monitor dotnet build -c Release
pacev2 --monitor dotnet publish
pacev2 --monitor dotnet -w test --no-build
```

Git replaces its live table and repeated final output with **JSON Lines on
stdout**, flushed after every event. Dotnet wraps its streamed logs in the same
protocol; `build`, `publish`, and MSBuild-based `test` additionally report real
project/stage progress, even with `--verbosity quiet`. Normal invocations are
unchanged. Help, version, and commands that have not opted into monitoring retain
their normal output. Leading configuration print flags write to stderr in monitor
mode so they do not corrupt the event stream. Preparation messages, configuration
warnings, and `-w` warning summaries also remain available on stderr.

Every record has `protocol: "pace.monitor"`, `version: 1`, a consecutive
`sequence` starting at 1, a UTC ISO-8601 `timestamp`, a `command` (such as `git` or
`dotnet.build`), and an `event`:

| Event | Additional fields |
| --- | --- |
| `start` | Begins one command's stream. |
| `project` | Full snapshot: `id`, `name`, `path` (nullable), `status`, `detail`, `stages` (stage name to status). |
| `log` | `text` (may contain embedded newlines), `project_id` (nullable). |
| `finish` | `status`, `returncode`, and project `counts` for succeeded/failed/skipped/incomplete. |

For example, a project snapshot is a single line:

```json
{"protocol":"pace.monitor","version":1,"sequence":8,"timestamp":"2026-10-04T00:00:00+00:00","command":"dotnet.build","event":"project","id":"/repos/app/App.csproj","name":"app","path":"/repos/app/App.csproj","status":"running","detail":"Build: succeeded","stages":{"compile":"succeeded","build":"succeeded"}}
```

Project statuses are `queued`, `running`, `succeeded`, `failed`, `skipped`, or
`incomplete`. Consumers should replace a project's snapshot by `id`, rather than
append duplicate rows. Git uses configured project names as IDs; .NET uses resolved
project-file paths and discovers referenced projects outside the selected scope.
Events from parallel workers are serialized; stdout and stderr ordering relative
to each other is not guaranteed. Parse stdout one line at a time, preserve `log`
events and stderr, and check the actual process exit code. An interrupted process
may not emit `finish`; do not infer success from its last project event.

The reusable `Monitor` in `monitor.py` provides `project()`, `log()`, and `finish()`;
commands can opt in via `ctx.meta["monitor"]`. `run_parallel(..., monitor=...)`
reuses the same project lifecycle for future parallel commands.

### .NET stage semantics

The bundled, read-only MSBuild logger observes `Restore`, `CoreCompile`, `Build`,
`Publish`, and `VSTest` targets (reported as `restore`, `compile`, `build`, `publish`,
and `test`). Only targets actually observed on a project appear. Solution-wide
restore does not necessarily produce a per-project Restore target. A test-stage
success means the MSBuild test target completed; it is **not** a test count and
does not imply a library contained tests. The newer Microsoft.Testing.Platform
CLI mode is not an MSBuild invocation and is not supported by this monitor.

Stages update during execution. Multi-framework/repeated target instances are
aggregated, failures are retained, and a project remains in progress until the
command ends so an earlier framework's success cannot hide a later failure.
Missing/framework-incompatible projects are skipped. A project without a matching
command target is skipped on a successful run, or incomplete on an unsuccessful
run; completed stages remain visible. There is deliberately no estimated
percentage. MSBuild still owns the solution graph and runs it once; monitoring
does not rewrite project files or run competing per-project builds.

On first use per SDK/source version, PACE compiles the small bundled logger
against the installed SDK's `Microsoft.Build.Framework` and caches it in
`~/.pace/cache/msbuild-monitor`. This uses local framework references, without
NuGet package dependencies or downloads. Compiler/cache errors are reported, not
silently replaced with guessed progress. A private temporary event file is tailed
alongside stdout and removed afterward. Monitor mode disables MSBuild's terminal
logger; other forwarded arguments and exit codes are preserved.

## Solution-based dotnet commands

PACE synchronizes `repodir/PACE.slnx` to the selected projects, then invokes
`dotnet <command> <absolute-path-to-PACE.slnx> <arguments>` **once**. MSBuild owns
dependency ordering, incremental builds, and parallelism; PACE does not start
competing builds per repository. Use a .NET SDK with `.slnx` support
(9.0.200 or newer), plus the SDKs/workloads required by your projects.

```powershell
uv run pacev2 dotnet build -c Release
uv run pacev2 dotnet -w build --no-restore
uv run pacev2 --to application dotnet test -c Release
uv run pacev2 --from common-lib --to application dotnet build -f net10.0
uv run pacev2 dotnet restore --ignore-failed-sources
uv run pacev2 dotnet pack -c Release
uv run pacev2 dotnet --info
```

Project files resolve as `repodir/<project-name>/<csproj_path>`; absolute project
paths are also accepted. Remote URLs are not required. Missing project files are
reported and omitted; inaccessible or invalid paths fail the invocation. An empty
`--from`/`--to` selection is a successful no-op and does not touch an existing
solution. A nonempty selection with no existing/compatible project files is an
error rather than a reason to build a stale solution.

Only selected projects are direct solution members. **MSBuild may still build
their referenced projects outside the selected range.** The actual
`ProjectReference` entries, not TOML `depends_on`, determine build dependencies;
keep both declarations consistent. PACE does not disable project-reference builds
or assume that excluded dependencies have already been built.

Solution membership is synchronized directly as XML, without `dotnet sln add`'s
SDK-dependent auto-inclusion of referenced projects. New projects use `sln_group`
as their solution folder. Existing folders, comments, and configuration metadata
are retained; stale/duplicate project entries are removed. Unchanged solutions
are not rewritten. Writes use atomic replacement. A malformed existing solution
is reported and left untouched, not deleted or overwritten.

`-f FRAMEWORK`, `--framework FRAMEWORK`, and `--framework=FRAMEWORK` filter
solution membership using MSBuild-evaluated `TargetFramework` and
`TargetFrameworks`, including imported properties and conditions. The match is
against the full target framework, not just its platform suffix. Configuration,
runtime, and explicit MSBuild property arguments are included during evaluation.
Evaluation errors stop the command, and incompatible projects are reported.
There is no persisted framework cache to go stale when imported files change.

Arguments are forwarded individually without a shell. Do not supply another
project or solution target: PACE supplies `PACE.slnx`. Commands run in the caller's
working directory, preserving relative argument paths, with stdin closed and
merged stdout/stderr streamed to the console. The underlying dotnet exit code is
returned; preparation/process-launch failures exit with code 1. This wrapper is
intended for solution-capable commands such as `build`, `restore`, `test`, `pack`,
`publish`, `clean`, and `msbuild`; dotnet itself reports unsupported combinations.
The standalone `pacev2 clean` command is still a placeholder.

SDK information flags (`--info`, `--version`, `--list-sdks`, `--list-runtimes`),
`dotnet help`, and forwarded dotnet help run without loading configuration or
creating a solution. `pacev2 dotnet --help` displays the wrapper's help; use
`pacev2 dotnet -- --help` to forward a leading help flag to dotnet.

Place `-w` / `--summarize-warnings` **before** the dotnet subcommand. It reports
warnings by code, project, and repository, deduplicating MSBuild's repeated
diagnostic lines, and writes a plain-text summary to
`~/.pace/logs/warnings-<timestamp>.log`. It also summarizes warnings from failed
builds without changing their exit code. No log is created when there are no
warnings; log-write failures are reported without masking the build result.
Configuration `build-props` are not automatically applied or written to
`Directory.Build.props`; pass explicit `-p:Name=Value` arguments as needed.

## CLI parity

The executable remains `pacev2`, so it can coexist with the original `pace`.
Global options precede the command:

| Option | Value |
| --- | --- |
| `--debug` | Flag |
| `--monitor` | Stream JSON Lines from supported commands |
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