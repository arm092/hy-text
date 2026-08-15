import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.smoke_install import (
    CONTRACTS,
    SmokeError,
    main,
    smoke_all,
    smoke_format,
    smoke_in_temp_root,
)


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

    def test_release_smoke_uses_and_cleans_an_explicit_temporary_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            explicit_root = base / "explicit-smoke-root"
            explicit_root.mkdir()

            with mock.patch(
                "tools.smoke_install.tempfile.TemporaryDirectory",
                wraps=tempfile.TemporaryDirectory,
            ) as temporary_directory:
                results = smoke_in_temp_root(ROOT, explicit_root)

            self.assertEqual(list(FORMATS), [result["package"] for result in results])
            self.assertEqual(explicit_root.resolve(), temporary_directory.call_args.kwargs["dir"])
            self.assertEqual([], list(explicit_root.iterdir()))

    def test_release_smoke_rejects_missing_file_and_unusable_temporary_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            missing = base / "missing"
            with self.assertRaisesRegex(SmokeError, "temporary root is missing"):
                smoke_in_temp_root(ROOT, missing)

            regular_file = base / "not-a-directory"
            regular_file.write_text("not a directory", encoding="utf-8")
            with self.assertRaisesRegex(SmokeError, "temporary root is not a directory"):
                smoke_in_temp_root(ROOT, regular_file)

            explicit_root = base / "unusable"
            explicit_root.mkdir()
            with mock.patch(
                "tools.smoke_install.tempfile.TemporaryDirectory",
                side_effect=PermissionError("denied"),
            ), self.assertRaisesRegex(SmokeError, "temporary root is unusable"):
                smoke_in_temp_root(ROOT, explicit_root)

    def test_cli_requires_and_uses_explicit_temporary_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            output = base / "report.json"
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["--root", str(ROOT), "--output", str(output)])

            errors = io.StringIO()
            with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
                main(
                    [
                        "--root",
                        str(ROOT),
                        "--temp-root",
                        str(base / "missing"),
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(2, failure.exception.code)
            self.assertIn("temporary root is missing", errors.getvalue())
            self.assertNotIn("Traceback", errors.getvalue())

            explicit_root = base / "explicit"
            explicit_root.mkdir()
            with redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
                        [
                            "--root",
                            str(ROOT),
                            "--temp-root",
                            str(explicit_root),
                            "--output",
                            str(output),
                        ]
                    ),
                )
            self.assertTrue(output.is_file())
            self.assertEqual([], list(explicit_root.iterdir()))


if __name__ == "__main__":
    unittest.main()
