import importlib.util
import json
import os
import subprocess
import sys
import tempfile
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
