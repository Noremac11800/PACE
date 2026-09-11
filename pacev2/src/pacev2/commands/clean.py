"""Build artifact and package cache cleanup command."""

from typing import Annotated

import typer

from pacev2._context import configure
from pacev2._stubs import not_implemented


def run(
    ctx: typer.Context,
    cache: Annotated[
        bool,
        typer.Option("--cache", help="Clean NuGet packages from ~/.nuget/packages"),
    ] = False,
    custom_cache: Annotated[
        bool,
        typer.Option(
            "--custom-cache",
            help=(
                "Clean NuGet packages from the custom cache path configured "
                "in nuget_cache_path"
            ),
        ),
    ] = False,
    project: Annotated[
        bool,
        typer.Option(
            "--project",
            help="Clean project bin/, obj/, and AppPackages/ directories",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be deleted without actually deleting",
        ),
    ] = False,
) -> None:
    """Delete build artifacts and NuGet cache for all projects."""
    configure(ctx, required=True)
    not_implemented("clean")
