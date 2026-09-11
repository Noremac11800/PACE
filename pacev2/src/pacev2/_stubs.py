"""Shared reporting for CLI features awaiting implementation."""

from typing import NoReturn

import typer


def not_implemented(feature: str) -> NoReturn:
    typer.echo(f"{feature} is not implemented yet in pacev2.", err=True)
    raise typer.Exit(code=1)
