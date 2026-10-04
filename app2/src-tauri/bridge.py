"""Desktop adapter; validation and active-config history belong to pacev2."""

import json
import logging
import os
import subprocess
import sys
import tempfile
import tomllib
from importlib.metadata import version
from pathlib import Path

import tomlkit
from pacev2.config import ConfigStore
from pacev2.models import BuildProp, Config
from tomlkit.items import AoT


def workspace(path: str | None = None) -> dict:
    store = ConfigStore()
    source, config = store.load(path)
    configs = sorted(store.configs_dir.glob("*.toml"))
    if source not in configs:
        configs.append(source)
    return {
        "path": str(source),
        "content": source.read_text(encoding="utf-8"),
        "config": config.model_dump(mode="json"),
        "configs": [{"path": str(item), "name": item.stem} for item in configs],
        "repoRoot": str(config.repodir.resolve()),
        "version": version("pacev2"),
    }


def save_config(request: dict) -> dict:
    path = Path(request["path"]).expanduser().resolve()
    content = request["content"]
    if path.suffix.lower() != ".toml":
        raise ValueError("Configuration files must use the .toml extension.")
    Config.model_validate(tomllib.loads(content))
    expected = request.get("expected")
    if expected is None:
        # Save a copy never overwrites an existing file.
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
    else:
        if path.read_text(encoding="utf-8") != expected:
            raise ValueError(
                "This file changed on disk. Reload it before saving to avoid losing changes."
            )
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            temporary.chmod(path.stat().st_mode)
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return workspace(str(path))


def configuration_fields(content: str) -> dict:
    raw = tomllib.loads(content)
    config = Config.model_validate(raw)
    properties = raw.get("build-props", raw.get("build_props", []))
    return {
        "repodir": raw.get("repodir", "."),
        "nuget_cache_path": raw.get("nuget_cache_path"),
        "build_props": [
            {
                **validated.model_dump(mode="json"),
                **(
                    {"default": original["default"]}
                    if isinstance(original.get("default"), (str, bool))
                    else {}
                ),
            }
            for original, validated in zip(properties, config.build_props, strict=True)
        ],
        "repoRoot": str(config.repodir.resolve()),
        "nugetCacheRoot": (
            str(config.nuget_cache_path.resolve()) if config.nuget_cache_path else None
        ),
    }


def edit_configuration(request: dict) -> str:
    document = tomlkit.parse(request["content"])
    Config.model_validate(document.unwrap())
    change = request["change"]
    kind = change["kind"]
    if kind == "paths":
        if document.get("repodir") != change["repodir"]:
            document["repodir"] = change["repodir"]
        if change["nuget_cache_path"] is None:
            document.pop("nuget_cache_path", None)
        elif document.get("nuget_cache_path") != change["nuget_cache_path"]:
            document["nuget_cache_path"] = change["nuget_cache_path"]
    elif kind in {"build-property", "delete-build-property"}:
        key = "build_props" if "build_props" in document else "build-props"
        properties = document.get(key, [])
        index = change["index"]
        if (kind == "delete-build-property" or index is not None) and (
            type(index) is not int or not 0 <= index < len(properties)
        ):
            raise ValueError("This build property no longer exists. Reopen the editor.")
        if kind == "delete-build-property":
            del properties[index]
        else:
            property_data = change["property"]
            property_model = BuildProp.model_validate(property_data)
            if any(
                item["name"].casefold() == property_model.name.casefold()
                for position, item in enumerate(properties)
                if position != index
            ):
                raise ValueError(
                    "Build property names must be unique (case-insensitive)."
                )
            if index is None:
                if key not in document:
                    document[key] = tomlkit.aot()
                properties = document[key]
                item = (
                    tomlkit.table()
                    if isinstance(properties, AoT)
                    else tomlkit.inline_table()
                )
                item.update(property_data)
                properties.append(item)
            else:
                item = properties[index]
                for field, value in property_data.items():
                    if item.get(field) != value:
                        item[field] = value
    else:
        raise ValueError(f"Unknown configuration edit: {kind}")
    content = tomlkit.dumps(document)
    Config.model_validate(tomllib.loads(content))
    return content


def diagnostics() -> list[dict]:
    results = [
        {"name": "Python", "version": sys.version.split()[0], "available": True},
        {"name": "pacev2", "version": version("pacev2"), "available": True},
    ]
    for name, executable in [("Git", "git"), (".NET SDK", "dotnet")]:
        try:
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=15,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            results.append(
                {
                    "name": name,
                    "available": result.returncode == 0,
                    "version": (result.stdout or result.stderr).strip()
                    or f"Exit code {result.returncode}",
                }
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            results.append({"name": name, "available": False, "version": str(error)})
    return results


def dispatch(request: dict):
    action = request["action"]
    if action == "workspace":
        return workspace(request.get("path"))
    if action == "save":
        return save_config(request)
    if action == "validate":
        config = Config.model_validate(tomllib.loads(request["content"]))
        return config.model_dump(mode="json")
    if action == "configuration-fields":
        return configuration_fields(request["content"])
    if action == "edit-configuration":
        return edit_configuration(request)
    if action == "verify":
        if Path(request["path"]).read_text(encoding="utf-8") != request["expected"]:
            raise ValueError(
                "The configuration changed on disk. Reload it before running a command."
            )
        return True
    if action == "filter":
        config = Config.model_validate(request["config"])
        return [
            project.name
            for project in config.filtered(
                request.get("from"), request.get("to")
            ).projects
        ]
    if action == "diagnostics":
        return diagnostics()
    raise ValueError(f"Unknown desktop request: {action}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    try:
        print(json.dumps(dispatch(json.load(sys.stdin))))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
