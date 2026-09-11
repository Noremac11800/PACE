"""Deferred CLI configuration so help never requires a usable config."""

from dataclasses import dataclass
from pathlib import Path

import typer

from pacev2.config import ConfigStore


@dataclass
class ConfigOptions:
    path: Path | None = None
    print_config: bool = False
    print_config_path: bool = False
    from_repo: str | None = None
    to_repo: str | None = None

    @property
    def requested(self) -> bool:
        return (
            self.path is not None
            or self.print_config
            or self.print_config_path
            or self.from_repo is not None
            or self.to_repo is not None
        )


def configure(ctx: typer.Context, *, required: bool = False) -> None:
    options = ctx.find_object(ConfigOptions)
    if options is None:
        raise RuntimeError("Global configuration options are missing from the CLI context")
    if not required and not options.requested:
        return

    try:
        path, config = ConfigStore().load(options.path, options.from_repo, options.to_repo)
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(code=1) from error

    ctx.obj = config
    ctx.meta["config_path"] = path
    if options.print_config_path:
        typer.echo(str(path))
    if options.print_config:
        typer.echo(config.model_dump_json(indent=2, by_alias=True))
