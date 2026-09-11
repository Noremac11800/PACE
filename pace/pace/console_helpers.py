"""Console helper functions for PACE."""

from rich.console import Console
from rich.panel import Panel
from rich.traceback import Traceback


def print_caught_exception(console: Console, custom_message: str = "") -> None:
    """Print the current exception as a yellow-outlined panel to indicate it was caught."""
    tb = Traceback(show_locals=True)
    custom_message = f": {custom_message}" if custom_message else ""
    console.print(
        Panel(tb, title=f"[yellow]Caught Exception{custom_message}[/yellow]", border_style="yellow")
    )
