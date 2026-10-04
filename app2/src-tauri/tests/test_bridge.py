import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

BRIDGE = Path(__file__).resolve().parents[1] / "bridge.py"
spec = importlib.util.spec_from_file_location("desktop_bridge", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

CONFIG = """# Keep this comment
repodir = "./repositories"
[[projects]]
name = "core"
csproj_path = "core.csproj"
[[projects]]
name = "app"
csproj_path = "app.csproj"
depends_on = ["core"]
"""


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = patch.object(Path, "home", return_value=self.root)
        self.home.start()
        self.addCleanup(self.home.stop)
        self.environment = patch.dict(
            os.environ, {"HOME": str(self.root), "USERPROFILE": str(self.root)}
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.path = self.root / "workspace.toml"

    def test_save_and_history_preserve_source(self):
        result = bridge.dispatch(
            {"action": "save", "path": str(self.path), "content": CONFIG}
        )
        self.assertEqual(result["content"], CONFIG)
        self.assertEqual(result["config"]["projects"][1]["depends_on"], ["core"])
        settings = json.loads((self.root / ".pace/settings.json").read_text())
        self.assertEqual(settings["lastActiveConfig"], str(self.path))
        self.assertEqual(bridge.workspace()["path"], str(self.path))

    def test_validation_does_not_write_or_initialize_history(self):
        bridge.dispatch({"action": "validate", "content": CONFIG})
        self.assertFalse((self.root / ".pace").exists())

    def edit(self, content, change):
        return bridge.dispatch(
            {"action": "edit-configuration", "content": content, "change": change}
        )

    def test_property_edits_preserve_unrelated_source_and_do_not_write(self):
        original = (
            CONFIG
            + """
# Shared build settings
[[build-props]]
name = 'Feature'
datatype = "boolean"
default = false # keep this explanation

[[build-props]]
name = "Label"
default = 'unchanged'
"""
        )
        self.path.write_text(original)
        changed = self.edit(
            original,
            {
                "kind": "build-property",
                "index": 0,
                "property": {
                    "name": "NewFeature",
                    "datatype": "boolean",
                    "default": True,
                },
            },
        )
        self.assertTrue(changed.startswith(CONFIG))
        self.assertIn("# Shared build settings", changed)
        self.assertIn("default = true # keep this explanation", changed)
        self.assertIn("default = 'unchanged'", changed)
        added = self.edit(
            changed,
            {
                "kind": "build-property",
                "index": None,
                "property": {
                    "name": "OutputPath",
                    "datatype": "path",
                    "default": 'C:\\build "quoted"\\output',
                },
            },
        )
        properties = tomllib.loads(added)["build-props"]
        self.assertEqual(properties[2]["default"], 'C:\\build "quoted"\\output')
        deleted = self.edit(added, {"kind": "delete-build-property", "index": 1})
        self.assertEqual(
            [item["name"] for item in tomllib.loads(deleted)["build-props"]],
            ["NewFeature", "OutputPath"],
        )
        self.assertEqual(self.path.read_text(), original)
        self.assertFalse((self.root / ".pace").exists())

    def test_property_edits_support_empty_arrays_inline_tables_and_aliases(self):
        for declaration in ("", "build-props = []\n", "build_props = []\n"):
            with self.subTest(declaration=declaration):
                content = declaration + CONFIG
                key = "build_props" if "build_props" in declaration else "build-props"
                added = self.edit(
                    content,
                    {
                        "kind": "build-property",
                        "index": None,
                        "property": {
                            "name": "Flag",
                            "datatype": "boolean",
                            "default": False,
                        },
                    },
                )
                self.assertIs(tomllib.loads(added)[key][0]["default"], False)
                modified = self.edit(
                    added,
                    {
                        "kind": "build-property",
                        "index": 0,
                        "property": {
                            "name": "Label",
                            "datatype": "string",
                            "default": "",
                        },
                    },
                )
                self.assertEqual(tomllib.loads(modified)[key][0]["default"], "")
                deleted = self.edit(
                    modified, {"kind": "delete-build-property", "index": 0}
                )
                self.assertEqual(tomllib.loads(deleted).get(key, []), [])
                self.assertEqual(
                    bridge.configuration_fields(deleted)["build_props"], []
                )

    def test_paths_preserve_literals_and_remove_optional_cache(self):
        original = CONFIG.replace(
            'repodir = "./repositories"',
            "repodir = './repositories' # root comment\nnuget_cache_path = './cache'",
        )
        changed = self.edit(
            original,
            {
                "kind": "paths",
                "repodir": r"~\new repositories",
                "nuget_cache_path": "./packages",
            },
        )
        self.assertIn("# root comment", changed)
        self.assertTrue(changed.endswith(CONFIG[CONFIG.index("[[projects]]") :]))
        fields = bridge.configuration_fields(changed)
        self.assertEqual(fields["repodir"], r"~\new repositories")
        self.assertEqual(fields["repoRoot"], str(self.root / "new repositories"))
        self.assertEqual(fields["nuget_cache_path"], "./packages")
        self.assertEqual(fields["nugetCacheRoot"], str(Path("packages").resolve()))
        removed = self.edit(
            changed,
            {
                "kind": "paths",
                "repodir": r"~\new repositories",
                "nuget_cache_path": None,
            },
        )
        self.assertNotIn("nuget_cache_path", tomllib.loads(removed))
        self.assertIsNone(bridge.configuration_fields(removed)["nugetCacheRoot"])
        self.assertFalse((self.root / "new repositories").exists())

    def test_fields_show_draft_defaults_without_normalizing_editable_path_strings(self):
        content = (
            CONFIG
            + """
[[build-props]]
name = "Output"
datatype = "path"
default = '~/build'
[[build-props]]
name = "Label"
"""
        )
        fields = bridge.configuration_fields(content)
        self.assertEqual(fields["build_props"][0]["default"], "~/build")
        self.assertEqual(fields["build_props"][1]["datatype"], "string")
        self.assertEqual(fields["build_props"][1]["default"], "")

    def test_edits_reject_invalid_values_indices_and_duplicate_properties(self):
        content = CONFIG + '\n[[build-props]]\nname = "Feature"\ndefault = false\n'
        for index in (-1, 1, True, 0.5, None):
            with (
                self.subTest(index=index),
                self.assertRaisesRegex(ValueError, "no longer exists"),
            ):
                self.edit(content, {"kind": "delete-build-property", "index": index})
        for change in [
            {
                "kind": "build-property",
                "index": None,
                "property": {"name": "feature", "datatype": "string", "default": ""},
            },
            {
                "kind": "build-property",
                "index": 0,
                "property": {"name": "", "datatype": "string", "default": ""},
            },
            {"kind": "paths", "repodir": "", "nuget_cache_path": None},
            {"kind": "paths", "repodir": "bad\0path", "nuget_cache_path": None},
            {"kind": "unsupported"},
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.edit(content, change)
        with self.assertRaises(ValueError):
            self.edit(
                "invalid = [",
                {"kind": "paths", "repodir": ".", "nuget_cache_path": None},
            )

    def test_invalid_configuration_never_overwrites(self):
        self.path.write_text(CONFIG)
        for invalid in [
            CONFIG + "unknown = true\n",
            CONFIG.replace('["core"]', '["missing"]'),
            "invalid = [",
        ]:
            with self.assertRaises(ValueError):
                bridge.save_config(
                    {"path": str(self.path), "content": invalid, "expected": CONFIG}
                )
            self.assertEqual(self.path.read_text(), CONFIG)

    def test_save_copy_never_overwrites(self):
        self.path.write_text(CONFIG)
        with self.assertRaises(FileExistsError):
            bridge.save_config({"path": str(self.path), "content": CONFIG})

    def test_external_edits_require_reload(self):
        self.path.write_text(CONFIG + "\n# external edit")
        with self.assertRaisesRegex(ValueError, "changed on disk"):
            bridge.save_config(
                {"path": str(self.path), "content": CONFIG, "expected": CONFIG}
            )
        with self.assertRaisesRegex(ValueError, "changed on disk"):
            bridge.dispatch(
                {"action": "verify", "path": str(self.path), "expected": CONFIG}
            )

    def test_atomic_edit_keeps_comments_and_other_history_settings(self):
        self.path.write_text(CONFIG)
        settings = self.root / ".pace/settings.json"
        settings.parent.mkdir()
        settings.write_text('{"otherSetting": true}')
        updated = CONFIG.replace("repositories", "new-repositories")
        bridge.save_config(
            {"path": str(self.path), "content": updated, "expected": CONFIG}
        )
        self.assertEqual(self.path.read_text(), updated)
        self.assertTrue(json.loads(settings.read_text())["otherSetting"])

    def test_filters_use_pace_model_semantics(self):
        config = bridge.dispatch({"action": "validate", "content": CONFIG})
        self.assertEqual(
            bridge.dispatch(
                {"action": "filter", "config": config, "from": "core", "to": "app"}
            ),
            ["core", "app"],
        )
        self.assertEqual(
            bridge.dispatch(
                {"action": "filter", "config": config, "from": "app", "to": "core"}
            ),
            [],
        )
        with self.assertRaises(ValueError):
            bridge.dispatch({"action": "filter", "config": config, "from": "missing"})

    def test_git_status_through_real_cli(self):
        repository = self.root / "repositories/core"
        repository.mkdir(parents=True)
        subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
        self.path.write_text(
            CONFIG.replace("./repositories", str(self.root / "repositories"))
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pacev2",
                "-C",
                str(self.path),
                "git",
                "status",
                "--short",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(self.root), "NO_COLOR": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("core", result.stdout)
        self.assertIn("app", result.stdout)

    def test_protocol_reports_invalid_input_as_failure(self):
        result = subprocess.run(
            [sys.executable, str(BRIDGE)],
            input=json.dumps({"action": "validate", "content": "invalid = ["}),
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
