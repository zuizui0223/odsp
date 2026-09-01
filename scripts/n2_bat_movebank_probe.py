#!/usr/bin/env python3
"""Probe the selected Movebank bat source without opening altitude outcomes.

The script fetches only source metadata/schema plus the minimum event columns
needed for structural support. Numerical height values are never parsed,
summarized, logged, or written to the receipt; only presence/missingness is
used by :mod:`odsp.n2_bat_preflight`.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

from pyproj import Transformer

from odsp.n2_bat_preflight import (
    resolve_native_height_field,
    summarize_bat_structural_preflight,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_BAT_STRUCTURAL_PREFLIGHT_CONTRACT.json"
BASE_URL = "https://www.movebank.org/movebank/service/direct-read"


class TransportError(RuntimeError):
    pass


def fetch_movebank(params: dict[str, object]) -> bytes:
    query = urllib.parse.urlencode(params, doseq=True)
    url = f"{BASE_URL}?{query}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "odsp-n2-bat-structural-preflight/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise TransportError(f"movebank_http_status_{exc.code}") from exc
    except urllib.error.URLError as exc:
        raise TransportError("movebank_network_error") from exc
    # Public data can still be configured to return an HTML license page.
    if b"License Terms:" in data or data.lstrip().lower().startswith(b"<html"):
        raise TransportError("movebank_license_or_html_response_requires_resolution")
    return data


def parse_csv(data: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("Movebank response has no CSV header")
    return list(reader.fieldnames), [dict(row) for row in reader]


def _single_row(rows: list[dict[str, str]], label: str) -> dict[str, str]:
    if len(rows) != 1:
        raise ValueError(f"expected exactly one {label} row, observed {len(rows)}")
    return rows[0]


def build_report() -> dict[str, object]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = contract["source"]
    study_id = int(source["movebank_study_id"])
    sensor_type_id = int(source["movebank_gps_sensor_type_id"])

    study_bytes = fetch_movebank(
        {
            "entity_type": "study",
            "study_id": study_id,
            "attributes": (
                "id,name,license_type,number_of_individuals,"
                "number_of_deployed_locations,sensor_type_ids"
            ),
        }
    )
    _, study_rows = parse_csv(study_bytes)
    study = _single_row(study_rows, "study metadata")
    if str(study.get("id", "")).strip() != str(study_id):
        raise ValueError("Movebank study ID mismatch")
    expected_license = str(source["license_expected_from_public_catalog"])
    observed_license = str(study.get("license_type", "")).strip()
    if observed_license and observed_license != expected_license:
        raise ValueError(
            f"Movebank license changed: expected {expected_license}, got {observed_license}"
        )

    attribute_bytes = fetch_movebank(
        {
            "entity_type": "study_attribute",
            "study_id": study_id,
            "sensor_type_id": sensor_type_id,
        }
    )
    _, attribute_rows = parse_csv(attribute_bytes)
    attribute_names = sorted(
        {
            str(row.get("short_name", "")).strip()
            for row in attribute_rows
            if str(row.get("short_name", "")).strip()
        }
    )
    native_height_field = resolve_native_height_field(attribute_names)

    requested_attributes = [
        "timestamp",
        "location_lat",
        "location_long",
        "individual_local_identifier",
        "individual_id",
        "visible",
        native_height_field,
    ]
    event_bytes = fetch_movebank(
        {
            "entity_type": "event",
            "study_id": study_id,
            "sensor_type_id": sensor_type_id,
            "attributes": ",".join(requested_attributes),
        }
    )
    event_header, event_rows = parse_csv(event_bytes)
    missing_columns = sorted(set(requested_attributes) - set(event_header))
    if missing_columns:
        raise ValueError(f"Movebank event response lacks required columns: {missing_columns}")

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
    summary = summarize_bat_structural_preflight(
        event_rows,
        native_height_field=native_height_field,
        projector=transformer.transform,
        cell_size_m=float(contract["horizontal_grid"]["primary_cell_size_m"]),
        minimum_events_per_cell=int(
            contract["structural_cell_gate"]["minimum_events_per_cell"]
        ),
        minimum_distinct_model_individuals_per_cell=int(
            contract["structural_cell_gate"][
                "minimum_distinct_model_individuals_per_cell"
            ]
        ),
        minimum_estimable_primary_cells=int(
            contract["structural_cell_gate"]["minimum_estimable_primary_cells"]
        ),
        minimum_total_individuals_with_xy_and_height=int(
            contract["structural_cell_gate"][
                "minimum_total_public_individuals_with_xy_and_native_height_presence"
            ]
        ),
    )

    terminal = (
        "structurally_available"
        if summary.structural_available
        else "bat_empirical_lane_structurally_unavailable"
    )
    return {
        "preflight_id": "odsp-n2-bat-movebank-structural-preflight-v1",
        "contract_id": contract["contract_id"],
        "architecture_selection_boundary_commit": contract[
            "architecture_selection_boundary_commit"
        ],
        "study_id": study_id,
        "movebank_repository_doi": source["movebank_repository_doi"],
        "source_transport": "Movebank direct-read public endpoint",
        "study_response_sha256": hashlib.sha256(study_bytes).hexdigest(),
        "study_attribute_response_sha256": hashlib.sha256(attribute_bytes).hexdigest(),
        "event_response_sha256": hashlib.sha256(event_bytes).hexdigest(),
        "observed_license_type": observed_license,
        "gps_sensor_type_id": sensor_type_id,
        "native_height_field": native_height_field,
        "event_columns_requested": requested_attributes,
        "event_row_count": len(event_rows),
        "structural_summary": summary.as_dict(),
        "terminal_category": terminal,
        "outcome_metrics_computed": False,
        "forbidden_metrics_confirmed_absent": contract[
            "forbidden_preflight_reads_or_outputs"
        ],
        "raw_event_values_persisted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build_report()
    except TransportError as exc:
        print(
            json.dumps(
                {
                    "transport_probe": "unresolved",
                    "reason": str(exc),
                    "scientific_terminal_decision": False,
                    "outcome_metrics_computed": False,
                },
                sort_keys=True,
            )
        )
        return 2
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
                "event_row_count": report["event_row_count"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
