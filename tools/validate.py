#!/usr/bin/env python3
"""Validate the hy-text corpus using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

try:
    from usage_common import (
        ALLOWED_LAYERS,
        REQUIRED_FIELDS as USAGE_OBSERVATION_FIELDS,
        USAGE_ID_RE,
        build_aggregate,
        canonical_usage_domain,
        load_observations,
        normalize_evidence_text,
        normalize_verification_example,
        normalized_public_url,
        parse_usage_date,
    )
except ModuleNotFoundError:
    from tools.usage_common import (
        ALLOWED_LAYERS,
        REQUIRED_FIELDS as USAGE_OBSERVATION_FIELDS,
        USAGE_ID_RE,
        build_aggregate,
        canonical_usage_domain,
        load_observations,
        normalize_evidence_text,
        normalize_verification_example,
        normalized_public_url,
        parse_usage_date,
    )


RULE_RE = re.compile(r"^## (HY-[A-Z]{2,4}-\d{3})$", re.MULTILINE)
SOURCE_RE = re.compile(r"\bSRC-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
USAGE_REFERENCE_RE = re.compile(r"\bUSAGE-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
STUDY_STEM_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MODERN_USAGE_BASIS = "ժամանակակից գործածություն"
MODERN_USAGE_WORDS = tuple(MODERN_USAGE_BASIS.split())
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".py"}
ALLOWED_USAGE_LAYERS = ALLOWED_LAYERS
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
OBSERVATION_FIELDS = USAGE_OBSERVATION_FIELDS
DERIVED_AGGREGATE_FIELDS = {
    "collected_at",
    "domains",
    "examples",
    "layers",
    "total",
    "variants",
}
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
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{path}: text is not valid UTF-8")
            continue
        except OSError as error:
            errors.append(f"{path}: cannot read text: {error}")
            continue
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


def valid_usage_date(value: object) -> bool:
    try:
        parse_usage_date(value, "date")
    except ValueError:
        return False
    return True


def validate_usage_observations(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        seen_urls = set()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            errors.append(f"{path}: usage observations are not valid UTF-8")
            continue
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
            try:
                normalize_evidence_text(observation.get("variant"), "variant")
            except ValueError as error:
                errors.append(f"{location}: {error}")
            if not valid_usage_date(observation.get("observed_at")):
                errors.append(f"{location}: observation has a malformed date")
            try:
                normalize_verification_example(
                    observation.get("example"),
                    "example",
                )
            except ValueError as error:
                errors.append(f"{location}: {error}")
    return errors


def validate_usage_aggregates(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        try:
            aggregate = json.loads(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            errors.append(f"{path}: usage aggregate is not valid UTF-8")
            continue
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
        try:
            normalized_query = normalize_evidence_text(query, "query")
        except ValueError as error:
            errors.append(f"{path}: usage aggregate {error}")
        else:
            if query != normalized_query:
                errors.append(f"{path}: usage aggregate query must be canonical NFC text")

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
                isinstance(count, int) and not isinstance(count, bool) and count > 0
                for count in layers.values()
            )
        ):
            errors.append(f"{path}: usage aggregate layers must contain positive counts")
        else:
            if len(layers) < 3:
                errors.append(f"{path}: usage aggregate requires three positive layers")
            if (
                isinstance(total, int)
                and not isinstance(total, bool)
                and sum(layers.values()) != total
            ):
                errors.append(f"{path}: usage aggregate total differs from layer counts")

        variants = aggregate.get("variants")
        variants_valid = isinstance(variants, dict) and bool(variants)
        if variants_valid:
            for label, count in variants.items():
                try:
                    normalized_label = normalize_evidence_text(label, "variant label")
                except ValueError:
                    variants_valid = False
                    break
                if (
                    label != normalized_label
                    or not isinstance(count, int)
                    or isinstance(count, bool)
                    or count <= 0
                ):
                    variants_valid = False
                    break
        if not variants_valid:
            errors.append(
                f"{path}: usage aggregate variants require canonical meaningful labels and positive counts"
            )
        elif (
            isinstance(total, int)
            and not isinstance(total, bool)
            and sum(variants.values()) != total
        ):
            errors.append(f"{path}: usage aggregate total differs from variant counts")

        if not valid_usage_date(aggregate.get("collected_at")):
            errors.append(f"{path}: usage aggregate has a malformed collection date")

        examples = aggregate.get("examples")
        examples_valid = isinstance(examples, list) and bool(examples)
        if examples_valid:
            for example in examples:
                try:
                    normalized_example = normalize_verification_example(
                        example,
                        "example",
                    )
                except ValueError:
                    examples_valid = False
                    break
                if example != normalized_example:
                    examples_valid = False
                    break
        if not examples_valid:
            errors.append(
                f"{path}: usage aggregate requires canonical short verification examples"
            )
    return errors


def _usage_registry(source_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors = []
    try:
        lines = source_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return [], [f"{source_path}: usage registry is not valid UTF-8"]
    except OSError as error:
        return [], [f"{source_path}: cannot read usage registry: {error}"]

    header = "| Usage ID | Aggregate | Observations | Scope |"
    try:
        header_index = lines.index(header)
    except ValueError:
        return [], [f"{source_path}: missing usage aggregate registry table"]

    rows = []
    for line_number, line in enumerate(lines[header_index + 2 :], header_index + 3):
        if not line.startswith("| USAGE-"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            errors.append(f"{source_path}:{line_number}: malformed usage registry row")
            continue
        aggregate_id, aggregate_cell, observation_cell, scope = cells
        if not aggregate_cell.startswith("`") or not aggregate_cell.endswith("`"):
            errors.append(f"{source_path}:{line_number}: aggregate path must be in backticks")
            continue
        if not observation_cell.startswith("`") or not observation_cell.endswith("`"):
            errors.append(f"{source_path}:{line_number}: observation path must be in backticks")
            continue
        rows.append(
            {
                "id": aggregate_id,
                "aggregate": aggregate_cell[1:-1],
                "observations": observation_cell[1:-1],
                "scope": scope,
            }
        )
    return rows, errors


def _expected_usage_id(stem: str) -> str | None:
    if not STUDY_STEM_RE.fullmatch(stem):
        return None
    return f"USAGE-{stem.upper()}"


def _rule_basis_blocks(chunk: str) -> list[str]:
    """Return basis field bodies independently of Markdown line decoration."""

    field_markers = "|".join(re.escape(field) for field in REQUIRED_FIELDS)
    pattern = re.compile(
        rf"\*\*Հիմք։\*\*(.*?)(?=(?:{field_markers})|\Z)",
        flags=re.DOTALL,
    )
    return pattern.findall(chunk)


def _armenian_basis_signature(value: str) -> list[str]:
    """Return Armenian-only tokens from a raw basis field.

    This is deliberately conservative: Armenian text in comments, link metadata,
    or other markup still creates a custody obligation. Markup, entities, URLs,
    combining marks, and non-whitespace controls cannot hide or manufacture an
    Armenian affix. Actual layout whitespace and adjacent Markdown labels retain
    boundary information; every other non-Armenian character is discarded.
    """

    normalized = unicodedata.normalize("NFKC", value).casefold()
    signature = []
    gap = []
    first_target_character = MODERN_USAGE_WORDS[0][0]
    for character in normalized:
        is_armenian_letter = (
            "\u0531" <= character <= "\u0587"
            and unicodedata.category(character).startswith("L")
        )
        if not is_armenian_letter:
            gap.append(character)
            continue

        if signature and gap:
            gap_text = "".join(gap)
            has_layout_whitespace = any(
                item in "\t\n\v\f\r"
                or unicodedata.category(item).startswith("Z")
                for item in gap
            )
            stripped_gap = gap_text.strip()
            enclosed_markup = (
                len(stripped_gap) >= 2
                and (stripped_gap[0], stripped_gap[-1])
                in {("<", ">"), ("(", ")"), ("[", "]")}
            )
            label_transition = "][" in gap_text and character == first_target_character
            if (has_layout_whitespace and not enclosed_markup) or label_transition:
                signature.append(" ")
        signature.append(character)
        gap.clear()
    return "".join(signature).split()


def _contains_modern_usage_basis(value: str) -> bool:
    words = _armenian_basis_signature(value)
    first_word, second_word = MODERN_USAGE_WORDS
    if any(
        left == first_word and right == second_word
        for left, right in zip(words, words[1:])
    ):
        return True

    combined = first_word + second_word
    return combined in words


def validate_usage_chain(root: Path, rule_paths: list[Path], source_path: Path) -> list[str]:
    """Connect modern-usage rules to registered, reproducible evidence pairs."""

    errors = []
    registry_rows, registry_errors = _usage_registry(source_path)
    errors.extend(registry_errors)
    registry_by_id: dict[str, dict[str, str]] = {}
    for row in registry_rows:
        aggregate_id = row["id"]
        if not USAGE_ID_RE.fullmatch(aggregate_id):
            errors.append(f"{source_path}: invalid usage registry ID {aggregate_id}")
            continue
        if aggregate_id in registry_by_id:
            errors.append(f"{source_path}: duplicate usage registry ID {aggregate_id}")
            continue
        registry_by_id[aggregate_id] = row

        stem = aggregate_id.removeprefix("USAGE-").lower()
        expected_aggregate = f"research/aggregates/{stem}.json"
        expected_observations = f"research/observations/{stem}.jsonl"
        if row["aggregate"] != expected_aggregate or row["observations"] != expected_observations:
            errors.append(
                f"{source_path}: {aggregate_id} registry paths must be "
                f"{expected_aggregate} and {expected_observations}"
            )
        if not row["scope"].strip():
            errors.append(f"{source_path}: {aggregate_id} registry scope must be non-empty")

    aggregate_paths = sorted((root / "research" / "aggregates").glob("*.json"))
    observation_directory = root / "research" / "observations"
    aggregate_by_id: dict[str, Path] = {}
    for aggregate_path in aggregate_paths:
        expected_id = _expected_usage_id(aggregate_path.stem)
        try:
            aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            errors.append(f"{aggregate_path}: usage aggregate is not valid UTF-8")
            continue
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{aggregate_path}: cannot inspect usage aggregate custody: {error}")
            continue
        if not isinstance(aggregate, dict):
            continue
        aggregate_id = aggregate.get("id")
        if not isinstance(aggregate_id, str) or not USAGE_ID_RE.fullmatch(aggregate_id):
            continue
        if aggregate_id in aggregate_by_id:
            errors.append(
                f"{aggregate_path}: duplicate aggregate ID {aggregate_id}; "
                f"already used by {aggregate_by_id[aggregate_id]}"
            )
        else:
            aggregate_by_id[aggregate_id] = aggregate_path

        if expected_id is None or aggregate_id != expected_id:
            errors.append(
                f"{aggregate_path}: filename must map to {aggregate_id} by the lowercase kebab convention"
            )

        observation_path = observation_directory / f"{aggregate_path.stem}.jsonl"
        if not observation_path.is_file():
            errors.append(f"{aggregate_path}: missing paired observations {observation_path}")
        else:
            try:
                rebuilt = build_aggregate(
                    load_observations(observation_path),
                    aggregate_id,
                    aggregate.get("query"),
                )
            except (OSError, ValueError) as error:
                errors.append(f"{aggregate_path}: cannot recompute from paired observations: {error}")
            else:
                mismatches = sorted(
                    field
                    for field in DERIVED_AGGREGATE_FIELDS
                    if aggregate.get(field) != rebuilt[field]
                )
                if mismatches:
                    errors.append(
                        f"{aggregate_path}: committed aggregate differs from recomputed "
                        f"fields {mismatches}"
                    )

        if aggregate_id not in registry_by_id:
            errors.append(f"{aggregate_path}: aggregate {aggregate_id} is not registered")

    for aggregate_id, row in registry_by_id.items():
        stem = aggregate_id.removeprefix("USAGE-").lower()
        expected_aggregate_relative = f"research/aggregates/{stem}.json"
        expected_observation_relative = f"research/observations/{stem}.jsonl"
        if (
            row["aggregate"] != expected_aggregate_relative
            or row["observations"] != expected_observation_relative
        ):
            continue
        aggregate_path = root / Path(row["aggregate"])
        observation_path = root / Path(row["observations"])
        if not aggregate_path.is_file():
            errors.append(
                f"{source_path}: registered aggregate {aggregate_id} does not exist at {aggregate_path}"
            )
        if not observation_path.is_file():
            errors.append(
                f"{source_path}: registered observations for {aggregate_id} do not exist at {observation_path}"
            )
        if aggregate_id not in aggregate_by_id and aggregate_path.is_file():
            errors.append(f"{aggregate_path}: registered ID {aggregate_id} does not match file content")

    for rule_path in rule_paths:
        try:
            text = rule_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        chunks = re.split(r"(?=^## HY-)", text, flags=re.MULTILINE)[1:]
        for chunk in chunks:
            rule_id = chunk.splitlines()[0].removeprefix("## ")
            rule_aggregate_ids = set(USAGE_REFERENCE_RE.findall(chunk))
            for aggregate_id in sorted(rule_aggregate_ids):
                if aggregate_id not in registry_by_id or aggregate_id not in aggregate_by_id:
                    errors.append(
                        f"{rule_path}: {rule_id} references unregistered or missing aggregate {aggregate_id}"
                    )

            basis_blocks = _rule_basis_blocks(chunk)
            for basis_block in basis_blocks:
                if not _contains_modern_usage_basis(basis_block):
                    continue
                aggregate_ids = USAGE_REFERENCE_RE.findall(basis_block)
                if not aggregate_ids:
                    errors.append(
                        f"{rule_path}: {rule_id} modern usage must reference a USAGE-* aggregate"
                    )
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
    nfc_errors = validate_nfc(files)
    errors.extend(nfc_errors)
    if any("not valid UTF-8" in error for error in nfc_errors):
        return errors
    errors.extend(validate_rule_ids(rule_paths))
    errors.extend(validate_rule_fields(rule_paths))
    errors.extend(validate_source_ids(rule_paths, references / "sources.md"))
    errors.extend(validate_versions(root))
    errors.extend(validate_placeholders(files))
    aggregate_paths = sorted((root / "research" / "aggregates").glob("*.json"))
    observation_paths = sorted((root / "research" / "observations").glob("*.jsonl"))
    errors.extend(validate_usage_aggregates(aggregate_paths))
    errors.extend(validate_usage_observations(observation_paths))
    errors.extend(
        validate_usage_chain(
            root,
            rule_paths,
            references / "sources.md",
        )
    )
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
