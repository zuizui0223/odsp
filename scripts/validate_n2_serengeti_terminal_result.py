#!/usr/bin/env python3
"""Validate the frozen Snapshot Serengeti terminal JSON and emit its receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from odsp.serengeti_terminal import validate_serengeti_terminal_result


def _load_object(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read terminal JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("terminal JSON root must be an object")
    return value


def _canonical_receipt_text(result: Mapping[str, object]) -> str:
    receipt = validate_serengeti_terminal_result(result)
    return json.dumps(
        receipt.as_dict(),
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _write_immutable(path: Path, content: str) -> str:
    """Write once; an identical existing receipt is idempotent, drift fails closed."""

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != content:
            raise ValueError(
                f"receipt already exists with different content: {path}"
            )
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created"


def validate_file(input_path: Path, output_path: Path) -> dict[str, object]:
    result = _load_object(input_path)
    receipt_text = _canonical_receipt_text(result)
    status = _write_immutable(output_path, receipt_text)
    receipt = json.loads(receipt_text)
    return {
        "status": status,
        "output": str(output_path),
        "terminal_category": receipt["terminal_category"],
        "result_fingerprint_sha256": receipt["result_fingerprint_sha256"],
        "axis_resolved_state_allowed_for_empirical_n3": receipt[
            "axis_resolved_state_allowed_for_empirical_n3"
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summary = validate_file(args.input, args.output)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
