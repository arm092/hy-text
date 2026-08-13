#!/usr/bin/env python3
"""Build deterministic usage aggregates from verified JSONL observations."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import tempfile

try:
    from usage_common import (
        ALLOWED_LAYERS,
        REQUIRED_FIELDS,
        USAGE_ID_RE,
        build_aggregate,
        canonical_usage_domain,
        load_observations,
        normalized_public_url,
    )
except ModuleNotFoundError:
    from tools.usage_common import (
        ALLOWED_LAYERS,
        REQUIRED_FIELDS,
        USAGE_ID_RE,
        build_aggregate,
        canonical_usage_domain,
        load_observations,
        normalized_public_url,
    )


def paths_refer_to_same_file(input_path: Path, output_path: Path) -> bool:
    if input_path.resolve() == output_path.resolve():
        return True
    if input_path.exists() and output_path.exists():
        return os.path.samefile(input_path, output_path)
    return False


def write_aggregate_atomic(path: Path, aggregate: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(aggregate, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--id", required=True, dest="aggregate_id")
    parser.add_argument("--query", required=True)
    args = parser.parse_args(argv)

    try:
        if paths_refer_to_same_file(args.input, args.output):
            raise ValueError("input and output refer to the same file")
        aggregate = build_aggregate(
            load_observations(args.input),
            args.aggregate_id,
            args.query,
        )
        write_aggregate_atomic(args.output, aggregate)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
