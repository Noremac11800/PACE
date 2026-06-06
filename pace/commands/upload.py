"""pace upload command - Upload app packages to the deployment server."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console

VALID_PLATFORMS = ["iOS", "Android", "Windows"]
VALID_RELEASE_TYPES = ["Debug", "Release"]


def _validate_inputs(
    package_path: Path,
    platform: str,
    release_type: str,
    console: Console,
) -> None:
    """Validate all input parameters."""
    if not package_path.exists():
        console.print(f"[red]Error: Package file not found: {package_path}[/red]")
        sys.exit(1)

    if platform not in VALID_PLATFORMS:
        console.print(
            f"[red]Error: Invalid platform '{platform}'. Must be one of: {', '.join(VALID_PLATFORMS)}[/red]"
        )
        sys.exit(1)

    if release_type not in VALID_RELEASE_TYPES:
        console.print(
            f"[red]Error: Invalid release type '{release_type}'. Must be one of: {', '.join(VALID_RELEASE_TYPES)}[/red]"
        )
        sys.exit(1)


def _build_curl_command(
    package_path: Path,
    app_name: str,
    version: str,
    username: str,
    platform: str,
    build_description: str | None,
    endpoint: str,
) -> list[str]:
    """Build the curl command arguments."""
    curl_args = [
        "curl",
        "--fail-with-body",
        "-#",
        "-X",
        "POST",
        f"{endpoint}/api/upload",
        "-F",
        f"build=@{package_path}",
        "-F",
        f"appname={app_name}",
        "-F",
        f"version={version}",
        "-F",
        f"uploader={username}",
        "-F",
        f"platform={platform}",
    ]

    if build_description:
        curl_args.extend(["-F", f"build_notes={build_description}"])

    return curl_args


def _print_upload_info(
    console: Console,
    package_path: Path,
    platform: str,
    release_type: str,
    app_name: str,
    version: str,
    username: str,
    build_description: str | None,
) -> None:
    """Print upload information to console."""
    console.print(f"Uploading [cyan]{package_path.name}[/cyan]...")
    console.print(f"  Platform: [green]{platform}[/green]")
    console.print(f"  Configuration: [green]{release_type}[/green]")
    console.print(f"  App Name: [green]{app_name}[/green]")
    console.print(f"  Version: [green]{version}[/green]")
    console.print(f"  Uploader: [green]{username}[/green]")
    if build_description:
        console.print(f"  Build Notes: [green]{build_description}[/green]")


def _execute_upload(
    console: Console,
    curl_args: list[str],
    package_path: Path,
) -> None:
    """Execute the curl upload command."""
    try:
        result = subprocess.run(
            curl_args,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        console.print("[red]Error: curl command not found. Please ensure curl is installed.[/red]")
        sys.exit(1)
    except subprocess.SubprocessError as e:
        console.print(f"[red]Error during upload: {e}[/red]")
        sys.exit(1)

    if result.returncode == 0:
        console.print(f"[green]Successfully uploaded {package_path.name}![/green]")
        if result.stdout:
            console.print(result.stdout)
        return

    console.print(f"[red]Upload failed with exit code {result.returncode}[/red]")
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")
    if result.stdout:
        console.print(result.stdout)
    sys.exit(1)


def run(
    console: Console,
    package_path: Path,
    username: str,
    app_name: str,
    platform: str,
    release_type: str,
    version: str,
    endpoint: str,
    build_description: str | None = None,
) -> None:
    """Upload an app package to the deployment server.

    Args:
        console: Rich console instance for output.
        package_path: Path to the app package file (.ipa, .msix, .aab, .apk).
        username: Name of the uploader.
        app_name: Name of the application.
        platform: Target platform (iOS, Android, Windows).
        release_type: Build configuration (Debug or Release).
        version: Version number or identifier.
        endpoint: Base URL of the deployment server.
        build_description: Optional build notes/description.
    """
    _validate_inputs(package_path, platform, release_type, console)
    _print_upload_info(
        console,
        package_path,
        platform,
        release_type,
        app_name,
        version,
        username,
        build_description,
    )
    curl_args = _build_curl_command(
        package_path, app_name, version, username, platform, build_description, endpoint
    )
    _execute_upload(console, curl_args, package_path)
