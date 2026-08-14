#!/usr/bin/env python3
"""Hermetically validate every supported hy-text package layout."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile


PACKAGE_ORDER = ("agent-skills", "claude", "codex", "cursor", "gemini", "openclaw")
SKILLS = ("skills/hy-text", "skills/hy-check", "skills/hy-score")
CONTRACTS = {
    "agent-skills": {
        "manifests": (),
        "skill_paths": SKILLS,
        "asset_paths": (),
        "executable": "npx",
    },
    "claude": {
        "manifests": (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"),
        "skill_paths": SKILLS,
        "asset_paths": (),
        "executable": "claude",
    },
    "codex": {
        "manifests": (".codex-plugin/plugin.json",),
        "skill_paths": (),
        "asset_paths": (),
        "executable": "codex",
    },
    "cursor": {
        "manifests": (".cursor-plugin/plugin.json",),
        "skill_paths": SKILLS,
        "asset_paths": (),
        "executable": "cursor",
    },
    "gemini": {
        "manifests": ("gemini-extension.json",),
        "skill_paths": SKILLS,
        "asset_paths": (),
        "executable": "gemini",
    },
    "openclaw": {
        "manifests": ("openclaw.plugin.json",),
        "skill_paths": (),
        "asset_paths": (),
        "executable": "openclaw",
    },
}


class SmokeError(ValueError):
    """A package manifest or installation layout is unsafe or incomplete."""


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SmokeError(f"cannot parse installed manifest {path}: {error}") from error
    if not isinstance(payload, dict):
        raise SmokeError(f"installed manifest must contain an object: {path}")
    return payload


def _safe_path(package_root: Path, base: Path, raw_path: str, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise SmokeError(f"{label} has an empty path")
    root = package_root.resolve()
    candidate = (base / raw_path).resolve()
    if not candidate.is_relative_to(root):
        raise SmokeError(f"{label} escapes package root: {raw_path}")
    if not candidate.exists():
        raise SmokeError(f"{label} is missing: {raw_path}")
    return candidate


def _copy_path(source_root: Path, package_root: Path, raw_path: str, label: str) -> None:
    source = _safe_path(source_root, source_root, raw_path, label)
    relative = source.relative_to(source_root.resolve())
    destination = package_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def _source_manifest(root: Path, relative: str) -> dict:
    path = _safe_path(root, root, relative, "manifest")
    return _load_json(path)


def _copy_contract(root: Path, package_root: Path, contract: dict) -> None:
    for relative in contract["manifests"]:
        _copy_path(root, package_root, relative, "manifest")
    for relative in contract["skill_paths"]:
        _copy_path(root, package_root, relative, "skill path")
    for relative in contract["asset_paths"]:
        _copy_path(root, package_root, relative, "asset path")


def _copy_manifest_references(root: Path, package_root: Path, package: str) -> None:
    if package == "claude":
        marketplace = _source_manifest(root, ".claude-plugin/marketplace.json")
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            raise SmokeError("Claude marketplace manifest is missing plugins")
        _safe_path(root, root, plugins[0].get("source"), "Claude plugin source")
    elif package == "codex":
        manifest = _source_manifest(root, ".codex-plugin/plugin.json")
        _copy_path(root, package_root, manifest.get("skills"), "Codex skills")
        interface = manifest.get("interface", {})
        for field in ("composerIcon", "logo", "logoDark"):
            _copy_path(root, package_root, interface.get(field), f"Codex {field}")
    elif package == "cursor":
        manifest = _source_manifest(root, ".cursor-plugin/plugin.json")
        logo = _safe_path(
            root,
            root / ".cursor-plugin",
            manifest.get("logo"),
            "Cursor logo",
        )
        relative = logo.relative_to(root.resolve())
        _copy_path(root, package_root, relative.as_posix(), "Cursor logo")
    elif package == "openclaw":
        manifest = _source_manifest(root, "openclaw.plugin.json")
        skills = manifest.get("skills")
        if not isinstance(skills, list) or not skills:
            raise SmokeError("OpenClaw manifest is missing skills")
        for skill in skills:
            _copy_path(root, package_root, f"skills/{skill}", "OpenClaw skill")


def _validate_skill_paths(package_root: Path, skill_paths: tuple[str, ...] | list[str]) -> None:
    for relative in skill_paths:
        skill = _safe_path(package_root, package_root, relative, "installed skill path")
        _safe_path(package_root, skill, "SKILL.md", "installed skill entrypoint")


def _validate_installed(package_root: Path, package: str, contract: dict) -> None:
    manifests = {
        relative: _load_json(_safe_path(package_root, package_root, relative, "installed manifest"))
        for relative in contract["manifests"]
    }
    _validate_skill_paths(package_root, contract["skill_paths"])
    for relative in contract["asset_paths"]:
        _safe_path(package_root, package_root, relative, "installed asset path")

    if package == "agent-skills":
        return
    if package == "claude":
        marketplace = manifests[".claude-plugin/marketplace.json"]
        source = marketplace["plugins"][0]["source"]
        _safe_path(package_root, package_root, source, "installed Claude plugin source")
        return
    if package == "codex":
        manifest = manifests[".codex-plugin/plugin.json"]
        skills = _safe_path(package_root, package_root, manifest["skills"], "installed Codex skills")
        for skill in SKILLS:
            _safe_path(package_root, package_root, skill, "installed Codex skill")
        interface = manifest["interface"]
        for field in ("composerIcon", "logo", "logoDark"):
            _safe_path(package_root, package_root, interface[field], f"installed Codex {field}")
        if not skills.is_dir():
            raise SmokeError("installed Codex skills path is not a directory")
        return
    if package == "cursor":
        manifest = manifests[".cursor-plugin/plugin.json"]
        _safe_path(
            package_root,
            package_root / ".cursor-plugin",
            manifest["logo"],
            "installed Cursor logo",
        )
        return
    if package == "gemini":
        return
    manifest = manifests["openclaw.plugin.json"]
    for skill in manifest["skills"]:
        _safe_path(package_root, package_root, f"skills/{skill}/SKILL.md", "installed OpenClaw skill")


def smoke_format(
    root: Path,
    temp_root: Path,
    package: str,
    contract: dict | None = None,
) -> dict:
    """Install and validate one format in a new isolated temporary home."""
    if package not in CONTRACTS:
        raise SmokeError(f"unknown package format: {package}")
    root = Path(root).resolve()
    temp_root = Path(temp_root)
    selected = contract if contract is not None else CONTRACTS[package]
    home = temp_root / package
    if home.exists():
        raise SmokeError(f"{package} requires a fresh temporary home")
    package_root = home / "hy-text"
    package_root.mkdir(parents=True)

    _copy_contract(root, package_root, selected)
    _copy_manifest_references(root, package_root, package)
    _validate_installed(package_root, package, selected)

    installed_files = sum(path.is_file() for path in package_root.rglob("*"))
    executable = selected["executable"]
    return {
        "package": package,
        "hermetic": "passed",
        "live_cli": "available" if shutil.which(executable) else "unavailable",
        "installed_files": installed_files,
    }


def smoke_all(root: Path, temp_root: Path) -> list[dict]:
    """Install every declared format into a separate fresh temporary home."""
    return [smoke_format(root, temp_root, package) for package in PACKAGE_ORDER]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="hy-text-smoke-") as temporary:
        results = smoke_all(arguments.root, Path(temporary))
    output = arguments.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
