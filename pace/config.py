"""Pydantic models for PACE configuration."""

import os
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

import tomli
from pydantic import BaseModel, model_validator


class Project(BaseModel):
    """Project model for PACE.

    Attributes:
        name: Name of the project.
        csproj_path: Path to the project file.
        repo_url: URL of the repository. (Optional)
    """

    name: str
    csproj_path: Path
    repo_url: str | None = None


class Config(BaseModel):
    """Configuration model for PACE.

    Attributes:
        repodir: Directory where repositories are cloned.
        projects: List of projects.
    """

    repodir: Path = Path()
    projects: list[Project]

    @model_validator(mode="after")
    def apply_env_overrides(self) -> "Config":
        """Apply environment variable overrides to the configuration."""
        env_repodir = os.getenv("REPODIR")
        if env_repodir is not None:
            self.repodir = Path(env_repodir)

        if self.repodir.exists() and self.repodir != Path():
            return self
        try:
            self.repodir.mkdir(parents=True, exist_ok=True)
            return self
        except Exception:  # noqa: BLE001
            raise RuntimeError(
                f"Repository directory {self.repodir} does not exist and could not be created."
            ) from None


def load_config(file_path: Path | Traversable | None = None) -> Config:
    """Load a TOML file and return its contents as a Config object.

    Args:
        file_path: Path to the TOML file.

    Returns:
        Config: Configuration object.
    """
    if file_path is None:
        file_path = files("pace.data").joinpath("pace.toml")

    try:
        with file_path.open("rb") as f:
            data = tomli.load(f)
            return Config(**data)
    except Exception as e:
        raise ValueError(f"Failed to load configuration file {file_path} with error:\n{e}") from e
