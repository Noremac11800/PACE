"""Git command interface."""

from typing import Annotated

import typer

from pacev2._stubs import not_implemented


def run(
    git_args: Annotated[
        list[str] | None,
        typer.Argument(
            metavar="... <git-args>",
            help="Git command and arguments (e.g., 'pull', 'clone', or 'checkout main')",
        ),
    ] = None,
) -> None:
    """Execute git commands across all repositories."""
    not_implemented("git")
