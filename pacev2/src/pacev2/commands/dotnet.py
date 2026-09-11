"""Dotnet command interface."""

from typing import Annotated

import typer

from pacev2._stubs import not_implemented


def run(
    dotnet_args: Annotated[
        list[str] | None,
        typer.Argument(
            metavar="... <dotnet-args>",
            help="Arguments to pass to dotnet (e.g., 'build -c Release')",
        ),
    ] = None,
    summarize_warnings: Annotated[
        bool,
        typer.Option(
            "--summarize-warnings",
            "-w",
            help=(
                "After the build completes, parse its output and print "
                "a warning summary by code and project"
            ),
        ),
    ] = False,
) -> None:
    """Execute dotnet commands across the project graph."""
    not_implemented("dotnet")
