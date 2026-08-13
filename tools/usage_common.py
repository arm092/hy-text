"""Shared validation and normalization for usage research."""

from __future__ import annotations

import ipaddress
import json
import re
import unicodedata
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
USAGE_ID_RE = re.compile(r"^USAGE-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
HOST_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
LEGACY_IPV4_PART_RE = re.compile(r"(?:0[xX][0-9A-Fa-f]+|0[0-7]*|[1-9][0-9]*|0)")
SPECIAL_USE_SUFFIXES = {
    "alt",
    "arpa",
    "corp",
    "example",
    "home",
    "internal",
    "invalid",
    "lan",
    "local",
    "localdomain",
    "localhost",
    "onion",
    "test",
}
RESERVED_DOMAINS = {"example.com", "example.net", "example.org", "home.arpa"}
IDNA_DEVIATION_CHARACTERS = {"ß", "ẞ", "ς"}


def normalize_evidence_text(value: object, field: str, *, max_length: int | None = None) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value).strip()
    if (
        not normalized
        or any(unicodedata.category(character).startswith("C") for character in normalized)
        or not any(
            not unicodedata.category(character).startswith("Z")
            for character in normalized
        )
    ):
        raise ValueError(f"{field} must contain meaningful text")
    if max_length is not None and len(normalized) > max_length:
        raise ValueError(f"{field} must not exceed {max_length} characters")
    return normalized


def normalize_verification_example(value: object, field: str) -> str:
    normalized = normalize_evidence_text(value, field, max_length=240)
    if not any(unicodedata.category(character)[0] in {"L", "N"} for character in normalized):
        raise ValueError(f"{field} must contain a letter or number")
    return normalized


def _canonical_ip(value: str) -> str | None:
    candidate = value[1:-1] if value.startswith("[") and value.endswith("]") else value
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    if isinstance(address, ipaddress.IPv6Address) and address.scope_id is not None:
        raise ValueError(f"domain must not use an IPv6 scope ID: {value!r}")
    if (
        not address.is_global
        or address.is_private
        or address.is_reserved
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
    ):
        raise ValueError(f"domain must be a public address: {value!r}")
    return address.compressed.lower()


def _parse_legacy_ipv4(value: str) -> ipaddress.IPv4Address | None:
    """Parse the historic numeric spellings that URL consumers still recognize."""

    parts = value.split(".")
    if not 1 <= len(parts) <= 4 or any(
        not LEGACY_IPV4_PART_RE.fullmatch(part) for part in parts
    ):
        return None

    numbers = []
    for part in parts:
        if part.lower().startswith("0x"):
            base = 16
        elif len(part) > 1 and part.startswith("0"):
            base = 8
        else:
            base = 10
        numbers.append(int(part, base))

    limits = {
        1: (0xFFFFFFFF,),
        2: (0xFF, 0xFFFFFF),
        3: (0xFF, 0xFF, 0xFFFF),
        4: (0xFF, 0xFF, 0xFF, 0xFF),
    }[len(numbers)]
    if any(number > limit for number, limit in zip(numbers, limits)):
        raise ValueError(f"invalid numeric address: {value!r}")

    if len(numbers) == 1:
        packed = numbers[0]
    elif len(numbers) == 2:
        packed = (numbers[0] << 24) | numbers[1]
    elif len(numbers) == 3:
        packed = (numbers[0] << 24) | (numbers[1] << 16) | numbers[2]
    else:
        packed = (
            (numbers[0] << 24)
            | (numbers[1] << 16)
            | (numbers[2] << 8)
            | numbers[3]
        )
    return ipaddress.IPv4Address(packed)


def _canonical_legacy_ipv4(value: str) -> str | None:
    address = _parse_legacy_ipv4(value)
    if address is None:
        return None
    return _canonical_ip(str(address))


def canonical_usage_domain(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("domain must be a non-empty string")
    raw = value.strip().rstrip(".")
    if not raw or any(
        character.isspace() or unicodedata.category(character).startswith("C")
        for character in raw
    ):
        raise ValueError(f"invalid domain: {value!r}")
    if any(character in IDNA_DEVIATION_CHARACTERS for character in raw):
        raise ValueError(
            f"domain contains a character with ambiguous standard-library IDNA mapping: {value!r}"
        )

    canonical_ip = _canonical_ip(raw)
    if canonical_ip is not None:
        return canonical_ip
    canonical_legacy_ipv4 = _canonical_legacy_ipv4(raw)
    if canonical_legacy_ipv4 is not None:
        return canonical_legacy_ipv4
    if any(character in raw for character in "/\\@?#:"):
        raise ValueError(f"invalid domain: {value!r}")

    try:
        labels = [label.encode("idna").decode("ascii").lower() for label in raw.split(".")]
    except UnicodeError as error:
        raise ValueError(f"invalid domain: {value!r}") from error
    try:
        for label in labels:
            if label.startswith("xn--"):
                label.encode("ascii").decode("idna")
    except UnicodeError as error:
        raise ValueError(f"invalid IDNA hostname: {value!r}") from error
    complete_domain = ".".join(labels)
    if len(complete_domain.encode("ascii")) > 253:
        raise ValueError(f"domain exceeds the DNS length limit: {value!r}")
    if labels and labels[0] == "www":
        labels = labels[1:]
    if len(labels) < 2 or any(not HOST_LABEL_RE.fullmatch(label) for label in labels):
        raise ValueError(f"domain must be a public multi-label hostname: {value!r}")

    domain = ".".join(labels)
    canonical_ip = _canonical_ip(domain)
    if canonical_ip is not None:
        return canonical_ip
    canonical_legacy_ipv4 = _canonical_legacy_ipv4(domain)
    if canonical_legacy_ipv4 is not None:
        return canonical_legacy_ipv4
    if labels[-1] in SPECIAL_USE_SUFFIXES or any(
        domain == reserved or domain.endswith(f".{reserved}")
        for reserved in RESERVED_DOMAINS
    ):
        raise ValueError(f"domain must be a public hostname: {value!r}")
    return domain


def normalized_public_url(value: object) -> tuple[str, str]:
    if not isinstance(value, str):
        raise ValueError("URL must be a string")
    stripped = value.strip()
    if not stripped or any(
        character.isspace() or unicodedata.category(character).startswith("C")
        for character in stripped
    ):
        raise ValueError("URL must be public HTTP or HTTPS")

    parsed = urlsplit(stripped)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("URL must be public HTTP or HTTPS")
    hostname = canonical_usage_domain(parsed.hostname)
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("URL has an invalid port") from error
    default_port = (parsed.scheme.lower() == "http" and port == 80) or (
        parsed.scheme.lower() == "https" and port == 443
    )
    rendered_hostname = f"[{hostname}]" if ":" in hostname else hostname
    netloc = (
        rendered_hostname
        if port is None or default_port
        else f"{rendered_hostname}:{port}"
    )
    normalized = urlunsplit(
        (parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, "")
    )
    return normalized, hostname


def parse_usage_date(value: object, field: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{field} must be a YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a valid date") from error


def load_observations(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{path}: invalid UTF-8") from error
    observations = []
    for line_number, line in enumerate(text.splitlines(), 1):
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


def build_aggregate(observations: list[dict], aggregate_id: str, query: str) -> dict:
    if not isinstance(aggregate_id, str) or not USAGE_ID_RE.fullmatch(aggregate_id):
        raise ValueError("aggregate ID must match USAGE-[A-Z0-9]+(?:-[A-Z0-9]+)*")
    normalized_query = normalize_evidence_text(query, "query")

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
        extra = observation.keys() - REQUIRED_FIELDS
        if extra:
            raise ValueError(f"observation {index} has unexpected fields: {sorted(extra)}")

        normalized_url, url_hostname = normalized_public_url(observation["url"])
        independence_key = canonical_usage_domain(observation["domain"])
        if url_hostname != independence_key and not url_hostname.endswith(
            f".{independence_key}"
        ):
            raise ValueError(f"observation {index} domain does not match its URL")
        if normalized_url in seen_urls:
            raise ValueError(f"duplicate URL: {normalized_url}")
        seen_urls.add(normalized_url)
        domains.add(independence_key)

        layer = observation["layer"]
        if layer not in ALLOWED_LAYERS:
            raise ValueError(f"observation {index} has an invalid layer")
        layers[layer] += 1

        variant = normalize_evidence_text(observation["variant"], f"observation {index} variant")
        variants[variant] += 1

        example = normalize_verification_example(
            observation["example"],
            f"observation {index} example",
        )
        examples.append(example)
        observed_dates.append(parse_usage_date(observation["observed_at"], "observed_at"))

    if len(observations) < 100:
        raise ValueError("usage aggregate requires at least 100 observations")
    if len(domains) < 20:
        raise ValueError("usage aggregate requires at least 20 domains")
    if len(layers) < 3:
        raise ValueError("usage aggregate requires at least three layers")

    return {
        "id": aggregate_id,
        "collected_at": max(observed_dates).isoformat(),
        "query": normalized_query,
        "variants": dict(sorted(variants.items())),
        "total": len(observations),
        "domains": sorted(domains),
        "layers": dict(sorted(layers.items())),
        "exclusions": [],
        "examples": sorted(examples),
    }
