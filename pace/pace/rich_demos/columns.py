"""Columns demo for PACE."""

import pathlib

from rich.columns import Columns
from rich.console import Console

from pace.console_helpers import print_caught_exception


def run(console: Console, args: list[str]) -> None:
    """Display styled directory contents in columns.

    Args:
        console: Rich console instance for output
        args: Command line arguments (expected: directory path)
    """
    try:
        directory = sorted(pathlib.Path(args[0]).iterdir(), key=lambda x: x.is_dir())
        styled_items: list[str] = []
        for item in directory:
            if item.is_dir():
                styled_items.append(f":file_folder: [green][bold]{item.name}[/bold][/green]")
            else:
                styled_items.append(f":page_facing_up: [blue][bold]{item.name}[/bold][/blue]")

        console.print(Columns(styled_items, padding=(0, 4)))
    except IndexError:
        print_caught_exception(console, custom_message="Error: No directory specified")
        console.print("Usage: pace demo columns <directory_path>")
        return
    except FileNotFoundError:
        print_caught_exception(console, custom_message=f"Error: Directory '{args[0]}' not found")
        console.print("Usage: pace demo columns <directory_path>")
        return
