"""CLI entry point for PACE."""

import argparse
import os
import sys
from argparse import Namespace
from importlib.metadata import version as get_version
from importlib.resources import files
from pathlib import Path
from typing import Any

# Get version from package metadata
try:
    __version__ = get_version("pace-dotnet")
except Exception:
    __version__ = "0.1.0"

# Force UTF-8 encoding for stdout/stderr to avoid encoding issues on Windows
os.environ["PYTHONIOENCODING"] = "utf-8:replace"
if sys.platform == "win32":
    # Reconfigure stdout/stderr to use UTF-8 with replace error handling
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

import rich
from rich.console import Console
from rich.traceback import install

from pace.commands import clean, dotnet, git, upload
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
    FROM_REPO = _Option(
        "",
        "--from",
        "Starting repository name. Only projects in the dependency chain from this repo will be included.",
        metavar="<reponame>",
    )
    TO_REPO = _Option(
        "",
        "--to",
        "Ending repository name. Only projects in the dependency chain up to this repo will be included.",
        metavar="<reponame>",
    )


class PaceFormatter(argparse.HelpFormatter):
    """Custom help formatter for PACE CLI."""

    def _format_usage(self, usage: Any, actions: Any, groups: Any, prefix: Any) -> str:  # noqa: ARG002
        """Override usage formatting to match the desired style."""
        return f"usage: [-h] [{_Options.CONFIG.short} {_Options.CONFIG.metavar}] [OPTIONS] command...\n\n"


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
    parser.add_argument(
        _Options.VERSION.long,
        _Options.VERSION.short,
        action="version",
        version=f"pace {__version__}",
    )
    parser.add_argument(
        _Options.FROM_REPO.long,
        dest="from_repo",
        metavar=_Options.FROM_REPO.metavar,
        help=_Options.FROM_REPO.description,
        default=None,
    )
    parser.add_argument(
        _Options.TO_REPO.long,
        dest="to_repo",
        metavar=_Options.TO_REPO.metavar,
        help=_Options.TO_REPO.description,
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    clean_parser = subparsers.add_parser(
        "clean", help="Delete build artifacts and NuGet cache for all projects"
    )
    clean_parser.add_argument(
        "--cache",
        action="store_true",
        help="Clean NuGet packages from ~/.nuget/packages",
        default=False,
    )
    clean_parser.add_argument(
        "--custom-cache",
        action="store_true",
        help="Clean NuGet packages from the custom cache path configured in nuget_cache_path",
        default=False,
    )
    clean_parser.add_argument(
        "--project",
        action="store_true",
        help="Clean project bin/ and obj/ directories",
        default=False,
    )
    clean_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
        default=False,
    )
    dotnet_parser = subparsers.add_parser(
        "dotnet", help="Execute dotnet commands across the project graph"
    )
    dotnet_parser.add_argument(
        "dotnet_args",
        metavar="... <dotnet-args>",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to dotnet (e.g., 'build -c Release')",
    )
    _git_parser = subparsers.add_parser("git", help="Execute git commands across all repositories")

    # Upload command with arguments
    upload_parser = subparsers.add_parser(
        "upload", help="Upload app packages to the deployment server"
    )
    upload_parser.add_argument(
        "package_path",
        metavar="<path-to-app-package>",
        help="Path to the app package file (.ipa, .msix, .aab, .apk)",
        type=Path,
    )
    upload_parser.add_argument(
        "--username",
        required=True,
        help="Name of the uploader",
        metavar="<username>",
    )
    upload_parser.add_argument(
        "--app-name",
        required=True,
        help="Name of the application",
        metavar="<appname>",
    )
    upload_parser.add_argument(
        "--platform",
        required=True,
        choices=["iOS", "Android", "Windows"],
        help="Target platform",
        metavar="<platform>",
    )
    upload_parser.add_argument(
        "--release-type",
        required=True,
        choices=["Debug", "Release"],
        help="Build configuration",
        metavar="<type>",
    )
    upload_parser.add_argument(
        "--version",
        required=True,
        help="Version number or identifier",
        metavar="<version>",
    )
    upload_parser.add_argument(
        "--endpoint",
        required=True,
        help="Base URL of the deployment server",
        metavar="<url>",
    )
    upload_parser.add_argument(
        "-n",
        "--build-description",
        help="Build notes/description",
        metavar="<description>",
        default=None,
    )
    upload_parser.add_argument(
        "-N",
        "--build-description-from-file",
        help="Read build description from file",
        metavar="<filepath>",
        type=Path,
        default=None,
    )

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
            config = load_config(args.config, from_repo=args.from_repo, to_repo=args.to_repo)
        else:
            return 1
    else:
        config = load_config(from_repo=args.from_repo, to_repo=args.to_repo)

    was_option_given = process_options(console, config, args)

    match args.command:
        case "clean":
            clean.run(
                console,
                config,
                cache=args.cache,
                custom_cache=args.custom_cache,
                project=args.project,
                dry_run=args.dry_run,
            )
        case "dotnet":
            return dotnet.run(console, config, args.dotnet_args)
        case "git":
            return git.run(console, config, unknownargs)
        case "upload":
            # Handle build description from file if provided
            build_description = args.build_description
            if args.build_description_from_file:
                try:
                    build_description = args.build_description_from_file.read_text()
                except Exception as e:
                    console.print(f"[red]Error reading build description file: {e}[/red]")
                    return 1
            upload.run(
                console,
                args.package_path,
                args.username,
                args.app_name,
                args.platform,
                args.release_type,
                args.version,
                args.endpoint,
                build_description,
            )
        case "demo":
            _DEMOS[args.name](console, unknownargs)
        case _:
            if not was_option_given:
                parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
