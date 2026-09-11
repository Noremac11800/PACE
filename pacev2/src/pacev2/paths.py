"""Path handling shared by configuration fields and CLI references."""

from pathlib import Path


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
