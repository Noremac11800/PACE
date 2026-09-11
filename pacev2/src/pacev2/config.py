"""TOML loading, active-config history, and editable template initialization."""

import json
import logging
import tomllib
from importlib.resources import files
from pathlib import Path
from tempfile import NamedTemporaryFile

from pacev2.models import Config
from pacev2.paths import normalize_path

logger = logging.getLogger(__name__)
LAST_ACTIVE_CONFIG_KEY = "lastActiveConfig"


def load_config(path: Path) -> Config:
    try:
        with path.open("rb") as stream:
            return Config.model_validate(tomllib.load(stream))
    except ValueError as error:
        raise ValueError(f"Invalid configuration in '{path}': {error}") from error


class ConfigStore:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory if directory is not None else Path.home() / ".pace"
        self.configs_dir = self.directory / "configs"
        self.settings_path = self.directory / "settings.json"

    def resolve_path(self, value: str | Path, *, use_cwd: bool = True) -> Path:
        path = normalize_path(value)
        if path.parent == Path() and (not use_cwd or not path.exists()):
            path = self.configs_dir / path
        return path.resolve()

    def load(
        self,
        value: str | Path | None = None,
        from_repo: str | None = None,
        to_repo: str | None = None,
    ) -> tuple[Path, Config]:
        settings = self._read_settings()
        path, config = self._select_config(value, settings)
        config = config.filtered(from_repo, to_repo)
        if settings is not None:
            self._remember(path, settings)
        return path, config

    def _select_config(
        self, value: str | Path | None, settings: dict[str, object] | None
    ) -> tuple[Path, Config]:
        if value is not None:
            path = self.resolve_path(value)
            return path, load_config(path)

        last_active = (
            settings.get(LAST_ACTIVE_CONFIG_KEY) if settings is not None else None
        )
        if isinstance(last_active, str):
            try:
                path = self.resolve_path(last_active, use_cwd=False)
                return path, load_config(path)
            except OSError as error:
                logger.warning(
                    "Cannot access the last active config '%s': %s. Using the template.",
                    last_active,
                    error,
                )

        path = self._default_path()
        return path, load_config(path)

    def _default_path(self) -> Path:
        path = self.configs_dir / "template.toml"
        if not path.exists():
            content = files("pacev2.data").joinpath("template.toml").read_bytes()
            self.configs_dir.mkdir(parents=True, exist_ok=True)
            try:
                with path.open("xb") as stream:
                    stream.write(content)
            except FileExistsError:
                pass  # Another invocation may have initialized the template first.
        return path.resolve()

    def _read_settings(self) -> dict[str, object] | None:
        try:
            loaded: object = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise TypeError("Settings must be a JSON object")
            last_active = loaded.get(LAST_ACTIVE_CONFIG_KEY)
            if last_active is not None and (
                not isinstance(last_active, str) or not last_active
            ):
                raise ValueError(f"{LAST_ACTIVE_CONFIG_KEY} must be a non-empty string")
            return loaded
        except FileNotFoundError:
            return {}
        except (OSError, TypeError, ValueError) as error:
            logger.warning(
                "Cannot read config history at '%s': %s. History will not be updated.",
                self.settings_path,
                error,
            )
            return None

    def _remember(self, path: Path, settings: dict[str, object]) -> None:
        value = path.name if path.parent == self.configs_dir.resolve() else str(path)
        if settings.get(LAST_ACTIVE_CONFIG_KEY) == value:
            return

        updated = {**settings, LAST_ACTIVE_CONFIG_KEY: value}
        temporary_path: Path | None = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.directory,
                prefix="settings-",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                json.dump(updated, stream, indent=2)
                stream.write("\n")
            temporary_path.replace(self.settings_path)
        except OSError as error:
            logger.warning(
                "Could not save config history at '%s': %s", self.settings_path, error
            )
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as error:
                    logger.warning("Could not remove '%s': %s", temporary_path, error)
