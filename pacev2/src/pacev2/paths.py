# Copyright (c) 2026

"""Path handling shared by configuration fields and CLI references."""

from pathlib import Path, PureWindowsPath


def normalize_path(value: object) -> Path:
    """Accept either separator style and expand the current user's home."""
    if not isinstance(value, (str, Path)):
        raise ValueError("Expected a path string")  # noqa: TRY004 - Pydantic wraps ValueError, not TypeError.
    text = str(value)
    if not text or "\0" in text:
        raise ValueError("Paths must be non-empty and contain no null characters")
    try:
        return Path(text.replace("\\", "/")).expanduser()
    except RuntimeError as error:
        raise ValueError(str(error)) from error


def project_directory(repodir: Path, name: str) -> Path:
    """Keep configured project names inside the repository directory."""
    if (
        not name.strip()
        or name in {".", ".."}
        or any(character in name for character in ("/", "\\", "\0"))
        or PureWindowsPath(name).drive
    ):
        raise ValueError(f"Project name '{name}' must be a single directory name")
    return repodir.resolve() / name
