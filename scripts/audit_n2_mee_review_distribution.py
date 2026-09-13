#!/usr/bin/env python3
"""Audit an anonymous MEE review ZIP against an explicit scientific boundary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "N2_MEE_REVIEW_DISTRIBUTION_BOUNDARY.json"


def audit(bundle: Path, *, boundary_path: Path = BOUNDARY) -> dict[str, object]:
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    if not bundle.is_file():
        raise FileNotFoundError(bundle)
    with zipfile.ZipFile(bundle) as archive:
        paths = sorted(name for name in archive.namelist() if not name.endswith("/"))

    path_set = set(paths)
    missing = [path for path in boundary["required_scientific_files"] if path not in path_set]
    if missing:
        raise AssertionError("required scientific review files missing: " + ", ".join(missing))

    odsp_python = sorted(
        path for path in paths
        if path.startswith("odsp/") and path.endswith(".py")
    )
    expected = sorted(boundary["allowed_odsp_python_files"])
    unexpected_odsp = sorted(set(odsp_python) - set(expected))
    missing_allowed = sorted(set(expected) - set(odsp_python))
    if unexpected_odsp:
        raise AssertionError(
            "unexpected ODSP Python files entered review distribution: "
            + ", ".join(unexpected_odsp)
        )
    if missing_allowed:
        raise AssertionError(
            "declared review ODSP Python files missing: " + ", ".join(missing_allowed)
        )

    forbidden_hits: dict[str, list[str]] = {}
    for token in boundary["forbidden_path_tokens"]:
        matches = [path for path in paths if token.lower() in path.lower()]
        if matches:
            forbidden_hits[token] = matches
    if forbidden_hits:
        rendered = "; ".join(
            f"{token}: {', '.join(matches)}"
            for token, matches in forbidden_hits.items()
        )
        raise AssertionError("governance/internal paths entered review distribution: " + rendered)

    return {
        "schema_version": 1,
        "boundary_id": boundary["boundary_id"],
        "boundary": boundary_path.name,
        "bundle": bundle.as_posix(),
        "passed": True,
        "file_count": len(paths),
        "odsp_python_file_count": len(odsp_python),
        "odsp_python_files": odsp_python,
        "forbidden_path_hits": {},
        "required_scientific_files_present": True,
        "full_development_repository_is_review_distribution": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--boundary", type=Path, default=BOUNDARY)
    parser.add_argument("--out-json", type=Path)
    args = parser.parse_args()
    result = audit(args.bundle, boundary_path=args.boundary)
    if args.out_json is not None:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
