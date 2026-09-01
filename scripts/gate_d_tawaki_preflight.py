#!/usr/bin/env python3
"""Run the outcome-blind Tawaki Gate-D structural preflight.

This script intentionally stops before any depth-bin frequency, entropy,
projection-loss or sealed score is calculated. Cross-table bird identity
reconciliation is restricted to the exact predeclared alias manifest.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

from pyproj import Transformer

from odsp.gate_d_contract import PRIMARY_GRID_M, cell_eligibility, validate_columns
from odsp.gate_d_preflight import (
    build_identity_alias_index,
    canonical_linked_identity,
    frozen_split_from_all_dives,
    git_blob_sha1,
    infer_bird_year_sites,
    linked_row_qualifies,
    row_has_finite_xy,
    sha256_hex,
    summarize_dive_strata,
    summarize_location_coverage,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "GATE_D_TAWAKI_SOURCE_MANIFEST.json"
ALIASES = ROOT / "GATE_D_TAWAKI_ID_ALIASES.json"


def download_raw(repo: str, commit: str, path: str) -> bytes:
    quoted_path = urllib.parse.quote(path, safe="/")
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{quoted_path}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "odsp-gate-d-tawaki-preflight/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def parse_csv(data: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header")
    rows = [dict(row) for row in reader]
    return list(reader.fieldnames), rows


def _text(row: dict[str, str], key: str) -> str:
    return str(row.get(key, "")).strip()


def _trip_id(row: dict[str, str], *, bird_id: str) -> str:
    return f"{bird_id}|{_text(row, 'TripNumber')}"


def build_report() -> dict[str, object]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    alias_manifest = json.loads(ALIASES.read_text(encoding="utf-8"))
    repo = manifest["external_repository"]
    commit = manifest["external_commit"]

    if alias_manifest["contract_id"] != manifest["contract_id"]:
        raise RuntimeError("alias manifest contract_id disagrees with source manifest")
    if alias_manifest["source_manifest_id"] != manifest["manifest_id"]:
        raise RuntimeError("alias manifest source_manifest_id disagrees with source manifest")
    if alias_manifest["external_repository"] != repo:
        raise RuntimeError("alias manifest external repository disagrees with source manifest")
    if alias_manifest["external_commit"] != commit:
        raise RuntimeError("alias manifest external commit disagrees with source manifest")
    if not alias_manifest.get("strict_explicit_aliases_only"):
        raise RuntimeError("alias manifest must require strict explicit aliases")
    if not alias_manifest.get("global_normalization_forbidden"):
        raise RuntimeError("alias manifest must forbid global normalization")
    if not alias_manifest.get("fuzzy_matching_forbidden"):
        raise RuntimeError("alias manifest must forbid fuzzy matching")
    if not alias_manifest.get("post_outcome_aliasing_forbidden"):
        raise RuntimeError("alias manifest must forbid post-outcome aliasing")

    source_rows: dict[str, list[dict[str, str]]] = {}
    source_info: dict[str, dict[str, object]] = {}

    for spec in manifest["files"]:
        data = download_raw(repo, commit, spec["path"])
        actual_blob = git_blob_sha1(data)
        if actual_blob != spec["git_blob_sha1"]:
            raise RuntimeError(
                f"source blob mismatch for {spec['path']}: "
                f"expected {spec['git_blob_sha1']}, got {actual_blob}"
            )
        header, rows = parse_csv(data)
        role = spec["role"]
        source_rows[role] = rows
        source_info[role] = {
            "path": spec["path"],
            "git_blob_sha1": actual_blob,
            "sha256": sha256_hex(data),
            "bytes": len(data),
            "rows": len(rows),
            "columns": header,
        }

    dive_rows = source_rows["all_processed_dive_denominator"]
    linked_rows = source_rows["location_linked_dive_events_for_structural_preflight"]
    validate_columns(source_info["all_processed_dive_denominator"]["columns"], table="dives")
    validate_columns(
        source_info["location_linked_dive_events_for_structural_preflight"]["columns"],
        table="linked",
    )
    if "DiveTime" not in source_info["location_linked_dive_events_for_structural_preflight"]["columns"]:
        raise RuntimeError("linked source lacks DiveTime required by frozen >=5 s filter")

    alias_index = build_identity_alias_index(
        alias_manifest["aliases"],
        dive_rows=dive_rows,
        linked_rows=linked_rows,
    )
    strata = summarize_dive_strata(dive_rows)
    coverage = summarize_location_coverage(
        dive_rows,
        linked_rows,
        alias_index=alias_index,
    )
    bird_sites = infer_bird_year_sites(dive_rows)
    split = frozen_split_from_all_dives(dive_rows)

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2193", always_xy=True)
    cell_buckets: dict[tuple[str, str, str], dict[str, object]] = defaultdict(
        lambda: {"events": 0, "bird_trips": set(), "birds": set()}
    )
    unresolved_linked_bird_years: set[str] = set()
    location_resolved_qualifying_rows = 0
    model_location_resolved_rows = 0

    for row in linked_rows:
        if not linked_row_qualifies(row) or not row_has_finite_xy(row):
            continue
        location_resolved_qualifying_rows += 1
        source_site = _text(row, "Site") or _text(row, "Colony")
        year = _text(row, "Year")
        canonical_site, bird = canonical_linked_identity(row, alias_index)
        source_key = (bird, year)
        if source_key not in bird_sites:
            unresolved_linked_bird_years.add(
                f"{source_site}|{year}|{_text(row, 'birdID')} -> {canonical_site}|{year}|{bird}"
            )
            continue
        if bird_sites[source_key] != canonical_site:
            raise RuntimeError(
                f"canonical site mismatch for {source_key}: "
                f"linked={canonical_site}, all-dive={bird_sites[source_key]}"
            )
        site = bird_sites[source_key]
        assignment = split.get((site, year, bird))
        if assignment != "model":
            continue
        lon = float(row["Lon"])
        lat = float(row["Lat"])
        easting, northing = transformer.transform(lon, lat)
        if not (math.isfinite(easting) and math.isfinite(northing)):
            raise RuntimeError("finite lon/lat produced non-finite NZTM coordinates")
        cell = f"{math.floor(easting / PRIMARY_GRID_M)}:{math.floor(northing / PRIMARY_GRID_M)}"
        bucket = cell_buckets[(site, year, cell)]
        bucket["events"] += 1
        bucket["bird_trips"].add(_trip_id(row, bird_id=bird))
        bucket["birds"].add(bird)
        model_location_resolved_rows += 1

    if unresolved_linked_bird_years:
        raise RuntimeError(
            "linked source contains bird-years absent from all-dive denominator after exact alias reconciliation: "
            + ", ".join(sorted(unresolved_linked_bird_years))
        )

    cells_by_stratum: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"cells": 0, "eligible": 0, "eligible_ids": []}
    )
    for (site, year, cell), bucket in sorted(cell_buckets.items()):
        status = cell_eligibility(
            n_events=int(bucket["events"]),
            bird_trip_ids=sorted(bucket["bird_trips"]),
            bird_ids=sorted(bucket["birds"]),
        )
        summary = cells_by_stratum[(site, year)]
        summary["cells"] += 1
        if status.estimable:
            summary["eligible"] += 1
            summary["eligible_ids"].append(cell)

    stratum_lookup = {(item.site, item.year): item for item in strata}
    cell_report: list[dict[str, object]] = []
    for key in sorted(stratum_lookup):
        site, year = key
        summary = cells_by_stratum.get(key, {"cells": 0, "eligible": 0, "eligible_ids": []})
        eligible_ids = sorted(summary["eligible_ids"])
        digest = hashlib.sha256("\n".join(eligible_ids).encode("utf-8")).hexdigest()
        source = stratum_lookup[key]
        cell_report.append(
            {
                "site": site,
                "year": year,
                "model_pool_cells_with_any_located_event": int(summary["cells"]),
                "model_pool_estimable_cells": int(summary["eligible"]),
                "model_pool_unavailable_cells": int(summary["cells"] - summary["eligible"]),
                "eligible_cell_ids_sha256": digest,
                "site_year_summary_gate": bool(
                    int(summary["eligible"]) >= 5 and source.birds >= 4
                ),
            }
        )

    split_rows = [
        {"site": site, "year": year, "birdID": bird, "assignment": assignment}
        for (site, year, bird), assignment in sorted(split.items())
    ]
    split_digest = hashlib.sha256(
        json.dumps(split_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    alias_rows = [
        {
            "source_site": source_site,
            "year": year,
            "source_birdID": source_bird,
            "canonical_site": target[0],
            "canonical_birdID": target[1],
        }
        for (source_site, year, source_bird), target in sorted(alias_index.items())
    ]
    alias_digest = hashlib.sha256(
        json.dumps(alias_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    total_qualifying = sum(item.qualifying_rows for item in strata)
    total_located = sum(item.location_resolved_rows for item in coverage)
    if total_located != location_resolved_qualifying_rows:
        raise RuntimeError("coverage numerator disagrees with linked-row structural count")

    return {
        "preflight_id": "odsp-gate-d-tawaki-preflight-v1",
        "contract_id": "odsp-gate-d-tawaki-v1",
        "contract_boundary_commit": "1278fffafbd3d5e55dc4d5d894c361149c2cd8cd",
        "external_repository": repo,
        "external_commit": commit,
        "outcome_metrics_computed": False,
        "forbidden_metrics_confirmed_absent": [
            "depth_bin_frequency_distribution",
            "H(Z|X,Y)",
            "exp(H(Z|X,Y))",
            "axis_thickness_map_values",
            "projection_loss_values",
            "sealed_log_score",
        ],
        "identity_reconciliation": {
            "alias_manifest_id": alias_manifest["alias_manifest_id"],
            "strict_explicit_aliases_only": True,
            "fuzzy_matching_forbidden": True,
            "global_normalization_forbidden": True,
            "post_outcome_aliasing_forbidden": True,
            "alias_count": len(alias_rows),
            "assignment_sha256": alias_digest,
            "aliases": alias_rows,
        },
        "source_files": source_info,
        "all_dive_denominators_by_site_year": [item.as_dict() for item in strata],
        "location_coverage_by_site_year": [item.as_dict() for item in coverage],
        "overall": {
            "qualifying_dive_rows": total_qualifying,
            "location_resolved_qualifying_rows": total_located,
            "location_coverage_fraction": (
                None if total_qualifying == 0 else total_located / total_qualifying
            ),
            "model_location_resolved_rows_used_for_cell_counts": model_location_resolved_rows,
        },
        "bird_split": {
            "algorithm": "frozen SHA-256 whole-bird split within site-year",
            "assignment_sha256": split_digest,
            "assignments": split_rows,
        },
        "primary_5km_model_pool_cell_preflight": cell_report,
        "all_site_year_summary_gates_pass": bool(
            cell_report and all(item["site_year_summary_gate"] for item in cell_report)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = build_report()
    target = args.output / "gate_d_tawaki_preflight.json"
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "preflight_id": report["preflight_id"],
                "outcome_metrics_computed": report["outcome_metrics_computed"],
                "source_file_count": len(report["source_files"]),
                "site_year_strata": len(report["all_dive_denominators_by_site_year"]),
                "all_site_year_summary_gates_pass": report["all_site_year_summary_gates_pass"],
                "output": str(target),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
