"""Config parsing, dependency filtering, and isolated history behavior."""

import json
from importlib.resources import files
from pathlib import Path
from unittest.mock import patch

import pytest
from pacev2.config import ConfigStore, load_config
from pacev2.models import Config
from pacev2.paths import normalize_path
from pydantic import ValidationError


def test_load_preserves_schema(config_file: Path, isolated_home: Path) -> None:
    config = load_config(config_file)

    assert config.repodir == Path("repositories")
    assert config.nuget_cache_path == isolated_home / "nuget-packages"
    assert config.projects[0].csproj_path == Path("src") / "App" / "App.csproj"
    assert config.projects[0].repo_url == "git@example.invalid:team/app.git"
    assert config.projects[0].sln_group == "Apps"
    assert config.projects[1].depends_on == []
    assert config.build_props[0].default is False
    assert config.build_props[1].default == isolated_home / "packages"
    assert config.build_props[2].default == ""
    assert config.build_props[3].datatype == "string"
    assert "build-props" in config.model_dump(by_alias=True)
    assert not config.repodir.exists()
    assert not config.nuget_cache_path.exists()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (r"src\My App\App.csproj", "src/My App/App.csproj"),
        ("src/My App/App.csproj", "src/My App/App.csproj"),
        (r"src\My App/App.csproj", "src/My App/App.csproj"),
        (r"C:\Repositories\App", "C:/Repositories/App"),
        ("C:/Repositories/App", "C:/Repositories/App"),
        (r"\\server\share\App", "//server/share/App"),
        ("/Applications/Pace", "/Applications/Pace"),
    ],
)
def test_model_normalizes_all_path_fields(value: str, expected: str) -> None:
    config = Config.model_validate(
        {
            "repodir": value,
            "nuget_cache_path": value,
            "projects": [{"name": "app", "csproj_path": value}],
            "build-props": [{"name": "Output", "datatype": "path", "default": value}],
        }
    )

    assert config.repodir == Path(expected)
    assert config.nuget_cache_path == Path(expected)
    assert config.projects[0].csproj_path == Path(expected)
    assert config.build_props[0].default == Path(expected)


@pytest.mark.parametrize("value", ["~/packages", r"~\packages"])
def test_paths_expand_home(value: str, isolated_home: Path) -> None:
    assert normalize_path(value) == isolated_home / "packages"


@pytest.mark.parametrize("value", ["", "invalid\0path", 12, True, None])
def test_paths_reject_invalid_values(value: object) -> None:
    with pytest.raises(ValueError):
        normalize_path(value)


@pytest.mark.parametrize(
    ("from_repo", "to_repo", "expected"),
    [
        (None, None, ["app", "base", "lib", "support", "other", "branch", "side"]),
        ("base", None, ["app", "base", "lib", "branch", "side"]),
        (None, "app", ["app", "base", "lib", "support", "branch"]),
        ("base", "app", ["app", "base", "lib", "branch"]),
        ("support", "app", ["app", "support"]),
        (None, "lib", ["base", "lib"]),
        ("base", "base", ["base"]),
        ("app", None, ["app"]),
        ("other", "app", []),
        ("app", "base", []),
    ],
)
def test_filter_selects_dependency_paths(
    config_file: Path, from_repo: str | None, to_repo: str | None, expected: list[str]
) -> None:
    config = load_config(config_file)
    original = config.model_dump()

    filtered = config.filtered(from_repo, to_repo)

    assert [project.name for project in filtered.projects] == expected
    assert config.model_dump() == original
    assert filtered.build_props == config.build_props
    assert filtered.repodir == config.repodir
    if filtered.projects and filtered.projects[0].name == "app":
        assert filtered.projects[0].depends_on == ["lib", "branch", "support"]


@pytest.mark.parametrize(
    ("from_repo", "to_repo"), [("missing", None), (None, "missing"), ("Base", "app")]
)
def test_filter_rejects_unknown_names(
    config_file: Path, from_repo: str | None, to_repo: str | None
) -> None:
    with pytest.raises(ValueError, match="not found in configuration"):
        load_config(config_file).filtered(from_repo, to_repo)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({}, "projects"),
        ({"projects": [], "unknown": True}, "Extra inputs"),
        (
            {"projects": [{"name": "app", "csproj_path": "App.csproj", "typo": True}]},
            "Extra inputs",
        ),
        (
            {
                "projects": [
                    {
                        "name": "app",
                        "csproj_path": "App.csproj",
                        "depends_on": ["missing"],
                    }
                ]
            },
            "unknown projects: missing",
        ),
        (
            {
                "projects": [
                    {"name": "app", "csproj_path": "App.csproj"},
                    {"name": "app", "csproj_path": "Other.csproj"},
                ]
            },
            "must be unique",
        ),
        (
            {
                "projects": [
                    {"name": "app", "csproj_path": "App.csproj", "depends_on": ["lib"]},
                    {"name": "lib", "csproj_path": "Lib.csproj", "depends_on": ["app"]},
                ]
            },
            "contain a cycle",
        ),
        (
            {
                "projects": [],
                "build-props": [{"name": "Output", "datatype": "number"}],
            },
            "datatype",
        ),
    ],
)
def test_model_rejects_invalid_configs(data: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Config.model_validate(data)


def test_model_defaults_are_independent() -> None:
    first = Config.model_validate(
        {"projects": [{"name": "one", "csproj_path": "One.csproj"}]}
    )
    second = Config.model_validate(
        {"projects": [{"name": "two", "csproj_path": "Two.csproj"}]}
    )

    first.projects[0].depends_on.append("later")

    assert second.projects[0].depends_on == []
    assert first.build_props == second.build_props == []
    assert first.build_props is not second.build_props


def test_first_use_creates_an_editable_template() -> None:
    store = ConfigStore()

    path, config = store.load()

    assert path == store.configs_dir / "template.toml"
    assert (
        path.read_bytes() == files("pacev2.data").joinpath("template.toml").read_bytes()
    )
    assert config.projects[0].name == "my-class-lib"
    assert json.loads(store.settings_path.read_text()) == {
        "lastActiveConfig": "template.toml"
    }
    assert list(store.configs_dir.iterdir()) == [path]


def test_existing_template_is_not_overwritten(config_file: Path) -> None:
    store = ConfigStore()
    store.configs_dir.mkdir(parents=True)
    template = store.configs_dir / "template.toml"
    original = config_file.read_bytes()
    template.write_bytes(original)

    path, config = store.load()

    assert path == template
    assert template.read_bytes() == original
    assert config.projects[0].name == "app"


def test_explicit_config_is_remembered_across_directories(
    config_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ConfigStore()
    relative = config_file.relative_to(Path.cwd())
    path, config = store.load(relative)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    remembered_path, remembered_config = ConfigStore().load()

    assert path == remembered_path == config_file
    assert config == remembered_config
    assert json.loads(store.settings_path.read_text())["lastActiveConfig"] == str(
        config_file
    )


def test_explicit_config_overrides_history(config_file: Path, tmp_path: Path) -> None:
    store = ConfigStore()
    store.load()
    custom = tmp_path / "custom.toml"
    custom.write_bytes(config_file.read_bytes())

    path, config = store.load(custom)

    assert path == custom
    assert config.projects[0].name == "app"
    assert ConfigStore().load()[0] == custom


def test_named_config_search_and_history(config_file: Path) -> None:
    store = ConfigStore()
    store.configs_dir.mkdir(parents=True)
    internal = store.configs_dir / "named.toml"
    internal.write_bytes(config_file.read_bytes())
    local = Path.cwd() / "named.toml"
    local.write_bytes(config_file.read_bytes())

    assert store.load("named.toml")[0] == local
    local.unlink()
    assert store.load("named.toml")[0] == internal
    assert (
        json.loads(store.settings_path.read_text())["lastActiveConfig"] == "named.toml"
    )

    local.write_text("not a valid config", encoding="utf-8")
    assert ConfigStore().load()[0] == internal


def test_history_preserves_other_settings_and_does_not_save_filters(
    config_file: Path,
) -> None:
    store = ConfigStore()
    store.directory.mkdir()
    store.settings_path.write_text('{"theme": "dark"}', encoding="utf-8")
    original = config_file.read_bytes()

    _, filtered = store.load(config_file, "base", "app")
    _, full = store.load()

    assert len(filtered.projects) == 4
    assert len(full.projects) == 7
    assert config_file.read_bytes() == original
    assert json.loads(store.settings_path.read_text()) == {
        "theme": "dark",
        "lastActiveConfig": str(config_file),
    }


def test_deleted_history_target_falls_back_with_a_warning(
    config_file: Path, caplog: pytest.LogCaptureFixture
) -> None:
    store = ConfigStore()
    store.load(config_file)
    config_file.unlink()

    path, config = store.load()

    assert path == store.configs_dir / "template.toml"
    assert config.projects[0].name == "my-class-lib"
    assert "Cannot access the last active config" in caplog.text


def test_inaccessible_history_target_falls_back(
    config_file: Path, caplog: pytest.LogCaptureFixture
) -> None:
    store = ConfigStore()
    store.load(config_file)

    def read_config(path: Path) -> Config:
        if path == config_file:
            raise PermissionError("Access denied")
        return load_config(path)

    with patch("pacev2.config.load_config", side_effect=read_config):
        path, config = store.load()

    assert path.name == "template.toml"
    assert config.projects[0].name == "my-class-lib"
    assert "Access denied" in caplog.text


@pytest.mark.parametrize("source", ["[broken", "projects = 42"])
def test_invalid_config_does_not_replace_history(
    config_file: Path, source: str
) -> None:
    store = ConfigStore()
    store.load(config_file)
    original_settings = store.settings_path.read_bytes()
    invalid = config_file.with_name("invalid.toml")
    invalid.write_text(source, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid configuration"):
        store.load(invalid)

    assert store.settings_path.read_bytes() == original_settings


def test_invalid_filter_does_not_replace_history(config_file: Path) -> None:
    store = ConfigStore()
    store.load()
    original_settings = store.settings_path.read_bytes()

    with pytest.raises(ValueError, match="not found"):
        store.load(config_file, from_repo="missing")

    assert store.settings_path.read_bytes() == original_settings


def test_malformed_remembered_config_does_not_fall_back(config_file: Path) -> None:
    store = ConfigStore()
    store.load(config_file)
    config_file.write_text("[broken", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid configuration"):
        store.load()

    assert not (store.configs_dir / "template.toml").exists()


def test_explicit_missing_config_never_falls_back() -> None:
    store = ConfigStore()

    with pytest.raises(FileNotFoundError):
        store.load("missing.toml")

    assert not store.directory.exists()


@pytest.mark.parametrize(
    "content", ["{broken", "[]", '{"lastActiveConfig": 42}', "\ufffd"]
)
def test_bad_history_is_reported_and_preserved(
    content: str, caplog: pytest.LogCaptureFixture
) -> None:
    store = ConfigStore()
    store.directory.mkdir()
    store.settings_path.write_text(content, encoding="utf-8")

    path, _ = store.load()

    assert path.name == "template.toml"
    assert "Cannot read config history" in caplog.text
    assert store.settings_path.read_text(encoding="utf-8") == content


def test_history_write_failure_is_reported_and_atomic(
    config_file: Path, caplog: pytest.LogCaptureFixture
) -> None:
    store = ConfigStore()
    store.load()
    original_settings = store.settings_path.read_bytes()

    with patch.object(Path, "replace", side_effect=PermissionError("Access denied")):
        path, config = store.load(config_file)

    assert path == config_file
    assert config.projects[0].name == "app"
    assert "Could not save config history" in caplog.text
    assert store.settings_path.read_bytes() == original_settings
    assert not list(store.directory.glob("settings-*.tmp"))
