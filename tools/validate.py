#!/usr/bin/env python3
"""Validate the hy-text corpus using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path


RULE_RE = re.compile(r"^## (HY-[A-Z]{2,4}-\d{3})$", re.MULTILINE)
SOURCE_RE = re.compile(r"\bSRC-[A-Z0-9-]+\b")
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py"}
REQUIRED_FIELDS = (
    "**Կանոն։**",
    "**Կիրառություն։**",
    "**Սխալ։**",
    "**Ճիշտ։**",
    "**Բացառություն։**",
    "**Խստություն։**",
    "**Հիմք։**",
)


def text_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
    ]


def validate_nfc(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if text != unicodedata.normalize("NFC", text):
            errors.append(f"{path}: text is not Unicode NFC")
    return errors


def validate_rule_ids(paths: list[Path]) -> list[str]:
    errors = []
    homes: dict[str, Path] = {}
    for path in paths:
        for rule_id in RULE_RE.findall(path.read_text(encoding="utf-8")):
            if rule_id in homes:
                errors.append(f"duplicate rule ID {rule_id}: {homes[rule_id]} and {path}")
            else:
                homes[rule_id] = path
    return errors


def validate_rule_fields(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        chunks = re.split(r"(?=^## HY-)", text, flags=re.MULTILINE)[1:]
        for chunk in chunks:
            rule_id = chunk.splitlines()[0].removeprefix("## ")
            for field in REQUIRED_FIELDS:
                if field not in chunk:
                    errors.append(f"{path}: {rule_id} is missing {field}")
    return errors


def validate_source_ids(rule_paths: list[Path], source_path: Path) -> list[str]:
    known = set(SOURCE_RE.findall(source_path.read_text(encoding="utf-8")))
    errors = []
    for path in rule_paths:
        for source_id in sorted(set(SOURCE_RE.findall(path.read_text(encoding="utf-8")))):
            if source_id not in known:
                errors.append(f"{path}: unknown source ID {source_id}")
    return errors


def validate_versions(root: Path) -> list[str]:
    manifests = [
        root / ".codex-plugin" / "plugin.json",
        root / ".claude-plugin" / "plugin.json",
        root / ".cursor-plugin" / "plugin.json",
        root / "gemini-extension.json",
        root / "openclaw.plugin.json",
    ]
    missing = [str(path) for path in manifests if not path.is_file()]
    if missing:
        return [f"missing manifest: {path}" for path in missing]
    versions = {json.loads(path.read_text(encoding="utf-8"))["version"] for path in manifests}
    return [] if len(versions) == 1 else [f"manifest versions differ: {sorted(versions)}"]


def validate_placeholders(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if "[" + "TODO:" in text or "TODO" + " placeholder" in text:
            errors.append(f"{path}: unresolved placeholder")
    return errors


def validate_usage_aggregates(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        try:
            aggregate = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: cannot read usage aggregate: {error}")
            continue
        if not isinstance(aggregate, dict):
            errors.append(f"{path}: usage aggregate must be an object")
            continue

        total = aggregate.get("total")
        if not isinstance(total, int) or isinstance(total, bool) or total < 100:
            errors.append(f"{path}: usage aggregate total must be at least 100")

        domains = aggregate.get("domains")
        if not isinstance(domains, list) or not all(
            isinstance(domain, str) and domain for domain in domains
        ):
            errors.append(f"{path}: usage aggregate domains must be non-empty strings")
        else:
            if len(domains) != len(set(domains)):
                errors.append(f"{path}: usage aggregate contains duplicate domains")
            if len(set(domains)) < 20:
                errors.append(f"{path}: usage aggregate requires at least 20 domains")

        layers = aggregate.get("layers")
        if not isinstance(layers, dict) or not all(
            isinstance(count, int) and not isinstance(count, bool) and count >= 0
            for count in layers.values()
        ):
            errors.append(f"{path}: usage aggregate layers must contain non-negative counts")
        elif sum(count > 0 for count in layers.values()) < 3:
            errors.append(f"{path}: usage aggregate requires three positive layers")

        variants = aggregate.get("variants")
        if not isinstance(variants, dict) or not all(
            isinstance(count, int) and not isinstance(count, bool) and count >= 0
            for count in variants.values()
        ):
            errors.append(f"{path}: usage aggregate variants must contain non-negative counts")
        elif (
            isinstance(total, int)
            and not isinstance(total, bool)
            and sum(variants.values()) != total
        ):
            errors.append(f"{path}: usage aggregate total differs from variant counts")

        collected_at = aggregate.get("collected_at")
        if not isinstance(collected_at, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", collected_at
        ):
            errors.append(f"{path}: usage aggregate has a malformed collection date")
        else:
            try:
                date.fromisoformat(collected_at)
            except ValueError:
                errors.append(f"{path}: usage aggregate has a malformed collection date")

        examples = aggregate.get("examples")
        if not isinstance(examples, list) or not all(
            isinstance(example, str) and len(example) <= 240 for example in examples
        ):
            errors.append(f"{path}: usage aggregate examples must not exceed 240 characters")
    return errors


def validate_repository(root: Path) -> list[str]:
    files = text_files(root)
    references = root / "skills" / "hy-text" / "references"
    rule_paths = [
        path
        for path in references.glob("*.md")
        if path.name not in {"scoring.md", "sources.md"}
    ]
    errors = []
    errors.extend(validate_nfc(files))
    errors.extend(validate_rule_ids(rule_paths))
    errors.extend(validate_rule_fields(rule_paths))
    errors.extend(validate_source_ids(rule_paths, references / "sources.md"))
    errors.extend(validate_versions(root))
    errors.extend(validate_placeholders(files))
    aggregate_paths = sorted((root / "research" / "aggregates").glob("*.json"))
    errors.extend(validate_usage_aggregates(aggregate_paths))
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("hy-text validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
