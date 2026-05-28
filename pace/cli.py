"""CLI entry point for PACE."""

import argparse
import sys
from argparse import Namespace
from importlib.resources import files
from pathlib import Path
from typing import Any

import rich
from rich.console import Console
from rich.traceback import install

from pace.commands import dotnet, git
from pace.config import Config, load_config
from pace.rich_demos import columns, progress_bar

_DEMOS = {
    "columns": columns.run,
    "progress_bar": progress_bar.run,
}


class _Option:
    def __init__(self, short: str, long: str, description: str, metavar: str | None = None) -> None:
        self.short = short
        self.long = long
        self.metavar = metavar
        self.description = description


class _Options:
    DEBUG = _Option("", "--debug", "Enable debug mode with full tracebacks")
    CONFIG = _Option(
        "-C",
        "--config",
        "Path to configuration file. Defaults to an internal pace.toml file.",
        metavar="<path>",
    )
    PRINT_CONFIG = _Option("", "--print-config", "Print the configuration and exit")
    PRINT_CONFIG_PATH = _Option(
        "", "--print-config-path", "Print the path to the configuration file and exit"
    )
    VERSION = _Option("-v", "--version", "Print the version and exit")


class PaceFormatter(argparse.HelpFormatter):
    """Custom help formatter for PACE CLI."""

    def _format_usage(self, usage: Any, actions: Any, groups: Any, prefix: Any) -> str:  # noqa: ARG002
        """Override usage formatting to match the desired style."""
        return f"usage: [-h] [{_Options.CONFIG.short} {_Options.CONFIG.metavar}] [OPTIONS] command...\n\n"  # noqa: E501


def main() -> int:
    """Main entry point for the PACE CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    console = Console()

    parser = argparse.ArgumentParser(
        description="PACE - Project Automation and Configuration Engine",
        formatter_class=PaceFormatter,
    )

    parser.add_argument(
        _Options.DEBUG.long,
        action="store_true",
        default=False,
        help="Enable debug mode with full tracebacks",
    )
    parser.add_argument(
        _Options.CONFIG.short,
        _Options.CONFIG.long,
        metavar=_Options.CONFIG.metavar,
        help="Path to configuration file. Defaults to an internal pace.toml file.",
        type=Path,
    )
    parser.add_argument(
        _Options.PRINT_CONFIG.long,
        action="store_true",
        help="Print the loaded configuration",
        default=False,
    )
    parser.add_argument(
        _Options.PRINT_CONFIG_PATH.long,
        action="store_true",
        help="Print the path to the configuration file and exit",
        default=False,
    )
    parser.add_argument(_Options.VERSION.long, action="version", version="pace 0.1.0")

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    subparsers.add_parser("dotnet", help="Execute dotnet commands across the project graph")
    _git_parser = subparsers.add_parser("git", help="Execute git commands across all repositories")

    demo_parser = subparsers.add_parser("demo", help="Run a built-in demo")
    demo_parser.add_argument(
        "name",
        choices=list(_DEMOS),
        metavar="name",
        help=f"Demo to run. Choices: {', '.join(_DEMOS)}",
    )

    args: Namespace
    unknownargs: list[str]
    args, unknownargs = parser.parse_known_args()

    if args.debug:
        install(show_locals=True, suppress=[rich])

    try:
        return _run(console, args, unknownargs, parser)
    except Exception as e:
        if args.debug:
            raise
        console.print(f"[red]error:[/red] {e}")
        return 1


def process_options(console: Console, config: Config, args: Namespace) -> bool:
    """Process configuration options and return True if any were given.

    Args:
        console: Rich console for output
        config: Loaded configuration
        args: Parsed command line arguments

    Returns:
        True if any configuration option was given, False otherwise
    """
    config_path = args.config or files("pace.data").joinpath("pace.toml")

    was_option_given = False
    if args.print_config_path:
        console.print(config_path)
        was_option_given = True

    if args.print_config:
        console.print(config)
        was_option_given = True

    return was_option_given


def _run(
    console: Console, args: Namespace, unknownargs: list[str], parser: argparse.ArgumentParser
) -> int:
    if args.config is not None:
        if args.config.exists():
            config = load_config(args.config)
        else:
            console.print(f"Configuration file {args.config} does not exist")
            return 1
    else:
        config = load_config()

    was_option_given = process_options(console, config, args)

    match args.command:
        case "dotnet":
            dotnet.run(console, config, unknownargs)
        case "git":
            git.run(console, config, unknownargs)
        case "demo":
            _DEMOS[args.name](console, unknownargs)
        case _:
            if not was_option_given:
                parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
