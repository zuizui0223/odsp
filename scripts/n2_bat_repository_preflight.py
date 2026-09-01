#!/usr/bin/env python3
"""Run the frozen N2 bat structural preflight from pinned repository bitstreams.

The selected tracking CSV is opened only after its filename, bitstream UUID,
size, and MD5 checksum have been frozen. Numerical native-height values are not
parsed, summarized, binned, logged, or persisted. Only height presence/missingness
is passed to the existing structural preflight core.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request

from pyproj import Transformer

from odsp.n2_bat_preflight import (
    resolve_native_height_field,
    summarize_bat_structural_preflight,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "N2_BAT_REPOSITORY_SOURCE_MANIFEST.json"
CONTRACT = ROOT / "N2_BAT_STRUCTURAL_PREFLIGHT_CONTRACT.json"


def download(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "odsp-n2-bat-repository-preflight/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def verify_source(data: bytes, spec: dict[str, object]) -> None:
    expected_size = int(spec["size_bytes"])
    if len(data) != expected_size:
        raise RuntimeError(
            f"source size mismatch for {spec['filename']}: "
            f"expected {expected_size}, got {len(data)}"
        )
    if str(spec["checksum_type"]).upper() != "MD5":
        raise RuntimeError("only the frozen MD5 source checksum is supported")
    actual = hashlib.md5(data).hexdigest()
    if actual != str(spec["checksum"]):
        raise RuntimeError(
            f"source checksum mismatch for {spec['filename']}: "
            f"expected {spec['checksum']}, got {actual}"
        )


def canonical_name(name: str) -> str:
    value = name.strip().lower().replace("-", "_").replace(" ", "_")
    return re.sub(r"_+", "_", value).strip("_")


def parse_csv(data: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header")
    original = [str(name) for name in reader.fieldnames]
    canonical = [canonical_name(name) for name in original]
    if len(set(canonical)) != len(canonical):
        raise ValueError("header canonicalization produced duplicate fields")
    rows: list[dict[str, str]] = []
    for raw in reader:
        rows.append(
            {
                canonical_name(str(key)): ("" if value is None else str(value))
                for key, value in raw.items()
                if key is not None
            }
        )
    return canonical, rows


def _by_role(manifest: dict[str, object], role: str) -> dict[str, object]:
    files = manifest.get("selected_files")
    if not isinstance(files, list):
        raise ValueError("manifest selected_files must be a list")
    matched = [item for item in files if isinstance(item, dict) and item.get("role") == role]
    if len(matched) != 1:
        raise ValueError(f"manifest requires exactly one {role} file")
    return matched[0]


def build_report() -> dict[str, object]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tracking_spec = _by_role(manifest, "primary_tracking_event_stream")
    reference_spec = _by_role(manifest, "reference_metadata")

    tracking_bytes = download(str(tracking_spec["content_url"]))
    verify_source(tracking_bytes, tracking_spec)
    reference_bytes = download(str(reference_spec["content_url"]))
    verify_source(reference_bytes, reference_spec)

    event_headers, event_rows = parse_csv(tracking_bytes)
    reference_headers, reference_rows = parse_csv(reference_bytes)

    native_height_field = resolve_native_height_field(event_headers)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
    gate = contract["structural_cell_gate"]
    grid = contract["horizontal_grid"]

    summary = summarize_bat_structural_preflight(
        event_rows,
        native_height_field=native_height_field,
        projector=transformer.transform,
        cell_size_m=float(grid["primary_cell_size_m"]),
        minimum_events_per_cell=int(gate["minimum_events_per_cell"]),
        minimum_distinct_model_individuals_per_cell=int(
            gate["minimum_distinct_model_individuals_per_cell"]
        ),
        minimum_estimable_primary_cells=int(gate["minimum_estimable_primary_cells"]),
        minimum_total_individuals_with_xy_and_height=int(
            gate["minimum_total_public_individuals_with_xy_and_native_height_presence"]
        ),
    )

    terminal = (
        "structurally_available"
        if summary.structural_available
        else "bat_empirical_lane_structurally_unavailable"
    )
    return {
        "preflight_id": "odsp-n2-bat-repository-structural-preflight-v1",
        "contract_id": contract["contract_id"],
        "source_manifest_id": manifest["manifest_id"],
        "repository_inventory_boundary_commit": manifest[
            "repository_inventory_boundary_commit"
        ],
        "source_files": {
            "tracking": {
                "bitstream_id": tracking_spec["bitstream_id"],
                "filename": tracking_spec["filename"],
                "size_bytes": len(tracking_bytes),
                "md5": hashlib.md5(tracking_bytes).hexdigest(),
                "row_count": len(event_rows),
                "canonical_headers": event_headers,
            },
            "reference": {
                "bitstream_id": reference_spec["bitstream_id"],
                "filename": reference_spec["filename"],
                "size_bytes": len(reference_bytes),
                "md5": hashlib.md5(reference_bytes).hexdigest(),
                "row_count": len(reference_rows),
                "canonical_headers": reference_headers,
            },
        },
        "native_height_field": native_height_field,
        "structural_summary": summary.as_dict(),
        "terminal_category": terminal,
        "scientific_terminal_decision": True,
        "outcome_metrics_computed": False,
        "numeric_height_values_parsed": False,
        "raw_event_values_persisted": False,
        "forbidden_metrics_confirmed_absent": contract[
            "forbidden_preflight_reads_or_outputs"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "preflight_id": report["preflight_id"],
                "terminal_category": report["terminal_category"],
                "outcome_metrics_computed": False,
                "numeric_height_values_parsed": False,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
