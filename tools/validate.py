#!/usr/bin/env python3
"""Validate the hy-text corpus using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


RULE_RE = re.compile(r"^## (HY-[A-Z]{2,4}-\d{3})$", re.MULTILINE)
SOURCE_RE = re.compile(r"\bSRC-[A-Z0-9-]+\b")
USAGE_ID_RE = re.compile(r"^USAGE-[A-Z0-9-]+$")
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py"}
ALLOWED_USAGE_LAYERS = {
    "commercial",
    "community",
    "government",
    "media",
    "professional",
}
AGGREGATE_FIELDS = {
    "collected_at",
    "domains",
    "examples",
    "exclusions",
    "id",
    "layers",
    "query",
    "total",
    "variants",
}
OBSERVATION_FIELDS = {"domain", "example", "layer", "observed_at", "url", "variant"}
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


def canonical_usage_domain(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("domain must be a non-empty string")
    parsed = urlsplit(f"//{value.strip()}")
    if (
        parsed.username
        or parsed.password
        or parsed.port
        or not parsed.hostname
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("domain must be a hostname without a port or path")
    return parsed.hostname.lower().rstrip(".").removeprefix("www.")


def normalized_public_url(value: object) -> tuple[str, str]:
    if not isinstance(value, str):
        raise ValueError("URL must be a string")
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("URL must be public HTTP or HTTPS")
    hostname = canonical_usage_domain(parsed.hostname)
    port = parsed.port
    default_port = (parsed.scheme.lower() == "http" and port == 80) or (
        parsed.scheme.lower() == "https" and port == 443
    )
    netloc = hostname if port is None or default_port else f"{hostname}:{port}"
    normalized = urlunsplit(
        (parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, "")
    )
    return normalized, hostname


def valid_usage_date(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_usage_observations(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        seen_urls = set()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            errors.append(f"{path}: cannot read usage observations: {error}")
            continue
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            location = f"{path}:{line_number}"
            try:
                observation = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"{location}: invalid observation JSON: {error.msg}")
                continue
            if not isinstance(observation, dict):
                errors.append(f"{location}: observation must be an object")
                continue

            missing = OBSERVATION_FIELDS - observation.keys()
            if missing:
                errors.append(f"{location}: observation is missing {sorted(missing)}")
            extra = observation.keys() - OBSERVATION_FIELDS
            if extra:
                errors.append(f"{location}: observation has unexpected fields: {sorted(extra)}")

            try:
                normalized_url, url_hostname = normalized_public_url(
                    observation.get("url")
                )
                independence_key = canonical_usage_domain(observation.get("domain"))
            except ValueError as error:
                errors.append(f"{location}: {error}")
            else:
                if url_hostname != independence_key and not url_hostname.endswith(
                    f".{independence_key}"
                ):
                    errors.append(f"{location}: domain does not match URL hostname")
                if normalized_url in seen_urls:
                    errors.append(f"{location}: duplicate URL {normalized_url}")
                seen_urls.add(normalized_url)

            if observation.get("layer") not in ALLOWED_USAGE_LAYERS:
                errors.append(f"{location}: observation has an invalid layer")
            variant = observation.get("variant")
            if not isinstance(variant, str) or not variant.strip():
                errors.append(f"{location}: observation has an invalid variant")
            if not valid_usage_date(observation.get("observed_at")):
                errors.append(f"{location}: observation has a malformed date")
            example = observation.get("example")
            if (
                not isinstance(example, str)
                or not example.strip()
                or len(example) > 240
            ):
                errors.append(f"{location}: example must contain 1 to 240 characters")
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

        missing = AGGREGATE_FIELDS - aggregate.keys()
        if missing:
            errors.append(f"{path}: usage aggregate is missing {sorted(missing)}")
        extra = aggregate.keys() - AGGREGATE_FIELDS
        if extra:
            errors.append(f"{path}: usage aggregate has unexpected fields: {sorted(extra)}")

        aggregate_id = aggregate.get("id")
        if not isinstance(aggregate_id, str) or not USAGE_ID_RE.fullmatch(aggregate_id):
            errors.append(f"{path}: usage aggregate has an invalid ID")

        query = aggregate.get("query")
        if not isinstance(query, str) or not query.strip():
            errors.append(f"{path}: usage aggregate query must be a non-empty string")

        exclusions = aggregate.get("exclusions")
        if not isinstance(exclusions, list) or not all(
            isinstance(exclusion, str) for exclusion in exclusions
        ):
            errors.append(f"{path}: usage aggregate exclusions must be strings")

        total = aggregate.get("total")
        if not isinstance(total, int) or isinstance(total, bool) or total < 100:
            errors.append(f"{path}: usage aggregate total must be at least 100")

        domains = aggregate.get("domains")
        if not isinstance(domains, list):
            errors.append(f"{path}: usage aggregate domains must be non-empty strings")
        else:
            try:
                canonical_domains = [canonical_usage_domain(domain) for domain in domains]
            except ValueError:
                errors.append(f"{path}: usage aggregate domains must be valid hostnames")
            else:
                unique_domains = set(canonical_domains)
                if len(canonical_domains) != len(unique_domains):
                    errors.append(f"{path}: usage aggregate contains duplicate domains")
                if len(unique_domains) < 20:
                    errors.append(f"{path}: usage aggregate requires at least 20 domains")

        layers = aggregate.get("layers")
        if (
            not isinstance(layers, dict)
            or not set(layers).issubset(ALLOWED_USAGE_LAYERS)
            or not all(
                isinstance(count, int) and not isinstance(count, bool) and count >= 0
                for count in layers.values()
            )
        ):
            errors.append(f"{path}: usage aggregate layers must contain non-negative counts")
        else:
            if sum(count > 0 for count in layers.values()) < 3:
                errors.append(f"{path}: usage aggregate requires three positive layers")
            if (
                isinstance(total, int)
                and not isinstance(total, bool)
                and sum(layers.values()) != total
            ):
                errors.append(f"{path}: usage aggregate total differs from layer counts")

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

        if not valid_usage_date(aggregate.get("collected_at")):
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
    observation_paths = sorted((root / "research" / "observations").glob("*.jsonl"))
    errors.extend(validate_usage_aggregates(aggregate_paths))
    errors.extend(validate_usage_observations(observation_paths))
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
