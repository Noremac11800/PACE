# Copyright (c) 2026

"""Typer entry point mirroring the public PACE command-line interface."""

from importlib.metadata import version as get_version
from pathlib import Path
from typing import Annotated

import typer

from pacev2._context import ConfigOptions, configure
from pacev2._stubs import not_implemented
from pacev2.commands import clean, dotnet, git, update, upload

app = typer.Typer(
    help="PACE - Project Automation and Configuration Engine",
    add_completion=False,
    no_args_is_help=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def options(  # noqa: PLR0913, PLR0917 - Typer declares each public global option as a parameter.
    ctx: typer.Context,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug mode with full tracebacks"),
    ] = False,
    monitor: Annotated[
        bool,
        typer.Option("--monitor", help="Emit JSON Lines progress from supported commands"),
    ] = False,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-C",
            metavar="<path>",
            help=(
                "Path to configuration file. Defaults to the last active config "
                "recorded in ~/.pace/settings.json, or an editable template "
                "in ~/.pace/configs/template.toml."
            ),
        ),
    ] = None,
    print_config: Annotated[
        bool,
        typer.Option("--print-config", help="Print the loaded configuration"),
    ] = False,
    print_config_path: Annotated[
        bool,
        typer.Option(
            "--print-config-path",
            help="Print the path to the configuration file and exit",
        ),
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Print the version and exit"),
    ] = False,
    from_repo: Annotated[
        str | None,
        typer.Option(
            "--from",
            metavar="<reponame>",
            help=(
                "Starting repository name. Only projects in the dependency chain "
                "from this repo will be included."
            ),
        ),
    ] = None,
    to_repo: Annotated[
        str | None,
        typer.Option(
            "--to",
            metavar="<reponame>",
            help=(
                "Ending repository name. Only projects in the dependency chain "
                "up to this repo will be included."
            ),
        ),
    ] = None,
) -> None:
    """Configure global CLI options before dispatching a command."""
    ctx.meta["monitor"] = monitor
    if version and ctx.invoked_subcommand is None:
        typer.echo(f"pacev2 {get_version('pacev2')}")
        raise typer.Exit

    config_options = ConfigOptions(
        path=config,
        print_config=print_config,
        print_config_path=print_config_path,
        from_repo=from_repo,
        to_repo=to_repo,
    )
    ctx.obj = config_options
    if ctx.invoked_subcommand is not None:
        return

    configure(ctx)
    if print_config or print_config_path:
        return
    if debug and not config_options.requested:
        not_implemented("Global option handling")

    typer.echo(ctx.get_help())


app.command("clean")(clean.run)
# Dotnet stops parsing PACE options at its first argument, as with argparse.REMAINDER.
app.command(
    "dotnet",
    cls=dotnet.DotnetCommand,
    context_settings={"ignore_unknown_options": True, "allow_interspersed_args": False},
)(dotnet.run)
app.command("git", cls=git.GitCommand)(git.run)
app.command("upload")(upload.run)
app.command("update")(update.run)


def main() -> None:
    """Run the CLI through the installed pacev2 entry point."""
    app()
