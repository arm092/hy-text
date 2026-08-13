#!/usr/bin/env python3
"""Build deterministic usage aggregates from verified JSONL observations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ALLOWED_LAYERS = {
    "commercial",
    "community",
    "government",
    "media",
    "professional",
}
REQUIRED_FIELDS = {"url", "domain", "layer", "variant", "observed_at", "example"}
USAGE_ID_RE = re.compile(r"^USAGE-[A-Z0-9-]+$")


def load_observations(path: Path) -> list[dict]:
    observations = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            observation = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {error.msg}") from error
        if not isinstance(observation, dict):
            raise ValueError(f"{path}:{line_number}: observation must be an object")
        observations.append(observation)
    return observations


def _normalize_domain(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("domain must be a non-empty string")
    parsed = urlsplit(f"//{value.strip()}")
    if parsed.username or parsed.password or parsed.port or not parsed.hostname:
        raise ValueError(f"invalid domain: {value!r}")
    domain = parsed.hostname.lower().rstrip(".")
    return domain.removeprefix("www.")


def _normalize_url(value: str) -> tuple[str, str]:
    if not isinstance(value, str):
        raise ValueError("url must be a string")
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"invalid public URL: {value!r}")
    if parsed.username or parsed.password:
        raise ValueError(f"invalid public URL: {value!r}")

    domain = _normalize_domain(parsed.hostname)
    port = parsed.port
    default_port = (parsed.scheme.lower() == "http" and port == 80) or (
        parsed.scheme.lower() == "https" and port == 443
    )
    netloc = domain if port is None or default_port else f"{domain}:{port}"
    normalized = urlunsplit(
        (parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, "")
    )
    return normalized, domain


def _parse_date(value: object, field: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{field} must be a YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a valid date") from error


def build_aggregate(observations: list[dict], aggregate_id: str, query: str) -> dict:
    if not USAGE_ID_RE.fullmatch(aggregate_id):
        raise ValueError("aggregate ID must match USAGE-[A-Z0-9-]+")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    domains = set()
    seen_urls = set()
    variants = Counter()
    layers = Counter()
    examples = []
    observed_dates = []

    for index, observation in enumerate(observations, 1):
        if not isinstance(observation, dict):
            raise ValueError(f"observation {index} must be an object")
        missing = REQUIRED_FIELDS - observation.keys()
        if missing:
            raise ValueError(f"observation {index} is missing {sorted(missing)}")

        normalized_url, url_domain = _normalize_url(observation["url"])
        supplied_domain = _normalize_domain(observation["domain"])
        if supplied_domain != url_domain:
            raise ValueError(f"observation {index} domain does not match its URL")
        if normalized_url in seen_urls:
            raise ValueError(f"duplicate URL: {normalized_url}")
        seen_urls.add(normalized_url)
        domains.add(url_domain)

        layer = observation["layer"]
        if layer not in ALLOWED_LAYERS:
            raise ValueError(f"observation {index} has an invalid layer")
        layers[layer] += 1

        variant = observation["variant"]
        if not isinstance(variant, str) or not variant.strip():
            raise ValueError(f"observation {index} has an invalid variant")
        variants[variant.strip()] += 1

        example = observation["example"]
        if not isinstance(example, str) or not example.strip() or len(example) > 240:
            raise ValueError(f"observation {index} example must contain 1 to 240 characters")
        examples.append(example.strip())
        observed_dates.append(_parse_date(observation["observed_at"], "observed_at"))

    if len(observations) < 100:
        raise ValueError("usage aggregate requires at least 100 observations")
    if len(domains) < 20:
        raise ValueError("usage aggregate requires at least 20 domains")
    if len(layers) < 3:
        raise ValueError("usage aggregate requires at least three layers")

    return {
        "id": aggregate_id,
        "collected_at": max(observed_dates).isoformat(),
        "query": query.strip(),
        "variants": dict(sorted(variants.items())),
        "total": len(observations),
        "domains": sorted(domains),
        "layers": dict(sorted(layers.items())),
        "exclusions": [],
        "examples": sorted(examples),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--id", required=True, dest="aggregate_id")
    parser.add_argument("--query", required=True)
    args = parser.parse_args(argv)

    try:
        aggregate = build_aggregate(
            load_observations(args.input),
            args.aggregate_id,
            args.query,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
