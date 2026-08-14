import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.smoke_install import CONTRACTS, SmokeError, smoke_all, smoke_format


ROOT = Path(__file__).resolve().parents[1]
FORMATS = ("agent-skills", "claude", "codex", "cursor", "gemini", "openclaw")


class SmokeInstallTest(unittest.TestCase):
    def _fixture_root(self, destination: Path) -> Path:
        root = destination / "source"
        root.mkdir()
        for relative in (
            "skills",
            "assets",
            ".claude-plugin",
            ".codex-plugin",
            ".cursor-plugin",
        ):
            shutil.copytree(ROOT / relative, root / relative)
        for relative in ("gemini-extension.json", "openclaw.plugin.json"):
            shutil.copy2(ROOT / relative, root / relative)
        return root

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _mutate_reference(self, root: Path, package: str, value: str) -> dict | None:
        if package in {"agent-skills", "gemini"}:
            contract = copy.deepcopy(CONTRACTS[package])
            contract["skill_paths"] = (value, *contract["skill_paths"][1:])
            return contract
        if package == "claude":
            path = root / ".claude-plugin" / "marketplace.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["plugins"][0]["source"] = value
        elif package == "codex":
            path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["skills"] = value
        elif package == "cursor":
            path = root / ".cursor-plugin" / "plugin.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["logo"] = value
        else:
            path = root / "openclaw.plugin.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["skills"][0] = value
        self._write_json(path, manifest)
        return None

    def test_smoke_all_installs_six_packages_in_isolated_homes(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp_root = Path(temporary)
            results = smoke_all(ROOT, temp_root)

            self.assertEqual(list(FORMATS), [result["package"] for result in results])
            for result in results:
                self.assertEqual("passed", result["hermetic"])
                self.assertIn(result["live_cli"], {"available", "unavailable"})
                package_root = temp_root / result["package"] / "hy-text"
                self.assertTrue(package_root.is_dir())
                self.assertGreater(result["installed_files"], 0)
                self.assertFalse((package_root / ".git").exists())

    def test_every_format_rejects_a_missing_reference(self):
        for package in FORMATS:
            with self.subTest(package=package), tempfile.TemporaryDirectory() as temporary:
                temporary_root = Path(temporary)
                root = self._fixture_root(temporary_root)
                contract = self._mutate_reference(root, package, "missing/package-target")

                with self.assertRaisesRegex(SmokeError, "missing"):
                    smoke_format(root, temporary_root / "homes", package, contract)

    def test_every_format_rejects_an_escaping_reference(self):
        for package in FORMATS:
            with self.subTest(package=package), tempfile.TemporaryDirectory() as temporary:
                temporary_root = Path(temporary)
                root = self._fixture_root(temporary_root)
                contract = self._mutate_reference(root, package, "../../outside")

                with self.assertRaisesRegex(SmokeError, "escapes package root"):
                    smoke_format(root, temporary_root / "homes", package, contract)

    def test_existing_home_is_never_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp_root = Path(temporary)
            (temp_root / "agent-skills").mkdir()

            with self.assertRaisesRegex(SmokeError, "fresh temporary home"):
                smoke_format(ROOT, temp_root, "agent-skills")


if __name__ == "__main__":
    unittest.main()
