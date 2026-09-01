#!/usr/bin/env python3
"""Execute the frozen N2 bat thickness endpoint exactly once.

All source/schema/provenance checks are completed before the numeric-height
marker is written. After that marker, numeric ``height_above_msl`` values may be
parsed only under the already-merged thickness contract and fixed engine.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import urllib.request

from odsp.n2_bat_preflight import deterministic_individual_split
from odsp.n2_bat_thickness import (
    evaluate_thickness_configuration,
    finite_height_fraction_among_structural_joint_events,
    height_present,
    individual_id,
    structural_eligible_cells,
    terminal_category_from_primary,
    xy_value,
)

ROOT = Path(__file__).resolve().parents[1]
AUTH_PATH = ROOT / "N2_BAT_THICKNESS_EXECUTION_AUTHORIZATION.json"
CONTRACT_PATH = ROOT / "N2_BAT_THICKNESS_CONTRACT.json"
MANIFEST_PATH = ROOT / "N2_BAT_REPOSITORY_SOURCE_MANIFEST.json"


def canonical_name(name: str) -> str:
    value = name.strip().lower().replace("-", "_").replace(" ", "_")
    return re.sub(r"_+", "_", value).strip("_")


def download(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "odsp-n2-bat-thickness-v1/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def verify_source(data: bytes, spec: dict[str, object]) -> None:
    expected_size = int(spec["size_bytes"])
    if len(data) != expected_size:
        raise RuntimeError(
            f"source size mismatch: expected {expected_size}, observed {len(data)}"
        )
    if str(spec["checksum_type"]).upper() != "MD5":
        raise RuntimeError("frozen source checksum type is not MD5")
    digest = hashlib.md5(data).hexdigest()
    if digest != str(spec["checksum"]):
        raise RuntimeError(
            f"source checksum mismatch: expected {spec['checksum']}, observed {digest}"
        )


def parse_csv(data: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("tracking CSV has no header")
    original = [str(value) for value in reader.fieldnames]
    canonical = [canonical_name(value) for value in original]
    if len(set(canonical)) != len(canonical):
        raise ValueError("tracking header canonicalization produced duplicates")
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


def tracking_spec(manifest: dict[str, object]) -> dict[str, object]:
    files = manifest.get("selected_files")
    if not isinstance(files, list):
        raise ValueError("source manifest selected_files is not a list")
    matched = [
        item
        for item in files
        if isinstance(item, dict) and item.get("role") == "primary_tracking_event_stream"
    ]
    if len(matched) != 1:
        raise ValueError("source manifest does not contain exactly one primary tracking stream")
    return matched[0]


def parse_edges(values: list[object]) -> tuple[float, ...]:
    result = []
    for value in values:
        if value == "-inf":
            result.append(-math.inf)
        elif value == "inf":
            result.append(math.inf)
        else:
            result.append(float(value))
    if len(result) < 2 or not all(a < b for a, b in zip(result, result[1:])):
        raise ValueError("frozen z edges are not strictly increasing")
    return tuple(result)


def edge_labels(edges: tuple[float, ...]) -> list[object]:
    values: list[object] = []
    for value in edges:
        if math.isinf(value):
            values.append("inf" if value > 0 else "-inf")
        else:
            values.append(value)
    return values


def _outlier_values(rows: list[dict[str, str]]) -> list[str]:
    allowed = {"", "false", "0", "no", "n", "f", "true", "1", "yes", "y", "t"}
    values = sorted(
        {
            str(row.get("manually_marked_outlier", "")).strip().lower()
            for row in rows
        }
    )
    unknown = [value for value in values if value not in allowed]
    if unknown:
        raise ValueError(f"unexpected manually_marked_outlier encoding: {unknown}")
    return values


def compact_result(result, *, include_local: bool) -> dict[str, object]:
    payload = {
        "cell_size_m": result.cell_size_m,
        "z_edges": edge_labels(result.z_edges),
        "eligible_cell_count": result.eligible_cell_count,
        "model_individual_count_with_eligible_events": result.model_individual_count_with_eligible_events,
        "sealed_individual_count": result.sealed_individual_count,
        "information_nats": result.information_nats,
        "effective_vertical_states": result.effective_vertical_states,
        "sealed_scores": [score.as_dict() for score in result.sealed_scores],
        "sealed_mean_log_score_gain": result.sealed_mean_log_score_gain,
        "answer_check_category": result.answer_check_category,
        "evaluable": result.evaluable,
        "unavailable_reasons": list(result.unavailable_reasons),
        "fingerprint": result.fingerprint,
    }
    if include_local:
        payload["local_cells"] = list(result.local_cells)
    return payload


def compact_sensitivity(result, *, minimum_cells: int = 5) -> dict[str, object]:
    payload = compact_result(result, include_local=False)
    if result.eligible_cell_count < minimum_cells:
        payload["sensitivity_status"] = "not_evaluable_underpowered"
    elif not result.evaluable:
        payload["sensitivity_status"] = "not_evaluable"
    else:
        payload["sensitivity_status"] = "evaluable"
    payload["cannot_override_primary"] = True
    return payload


def load_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    authorization = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if authorization["contract_id"] != contract["contract_id"]:
        raise ValueError("authorization/contract ID mismatch")
    if authorization["source_manifest_id"] != manifest["manifest_id"]:
        raise ValueError("authorization/source-manifest ID mismatch")
    if authorization["contract_boundary_commit"] != "8250331209cbabf85afdcf92672104e8543816c7":
        raise ValueError("unexpected contract boundary")
    if authorization["engine_boundary_commit"] != "e99022ffe7a904d3f9917d9315d85ba4cdc91d5c":
        raise ValueError("unexpected engine boundary")
    if not authorization["execute_numeric_height_once"]:
        raise ValueError("numeric height execution is not authorized")
    if authorization["post_outcome_retuning"] is not False or contract["post_outcome_retuning"] is not False:
        raise ValueError("post-outcome retuning boundary is not frozen")
    return authorization, contract, manifest


def pre_numeric_phase():
    authorization, contract, manifest = load_inputs()
    spec = tracking_spec(manifest)
    if spec["bitstream_id"] != authorization["tracking_bitstream_id"]:
        raise ValueError("tracking bitstream ID mismatch")
    if spec["checksum"] != authorization["tracking_md5"]:
        raise ValueError("tracking checksum mismatch between authorization and manifest")

    data = download(str(spec["content_url"]))
    verify_source(data, spec)
    headers, rows = parse_csv(data)

    expected = authorization["expected_pre_numeric_provenance"]
    height_field = str(expected["height_field"])
    required = {
        "timestamp",
        "location_long",
        "location_lat",
        "individual_local_identifier",
        "manually_marked_outlier",
        height_field,
    }
    missing = sorted(required - set(headers))
    if missing:
        raise ValueError(f"tracking schema missing frozen fields: {missing}")
    outlier_encodings = _outlier_values(rows)

    if len(rows) != int(expected["tracking_row_count"]):
        raise ValueError("tracking row-count provenance mismatch")
    ids = sorted({individual_id(row) for row in rows})
    if len(ids) != int(expected["individual_count"]):
        raise ValueError("individual-count provenance mismatch")
    split = deterministic_individual_split(ids)
    model_ids = sorted(iid for iid, role in split.items() if role == "model")
    sealed_ids = sorted(iid for iid, role in split.items() if role == "sealed")
    if len(model_ids) != int(expected["model_individual_count"]):
        raise ValueError("model-individual split provenance mismatch")
    if len(sealed_ids) != int(expected["sealed_individual_count"]):
        raise ValueError("sealed-individual split provenance mismatch")

    finite_xy_count = sum(xy_value(row) is not None for row in rows)
    height_present_count = sum(height_present(row, height_field) for row in rows)
    if finite_xy_count != int(expected["events_with_finite_xy"]):
        raise ValueError("finite-x-y provenance mismatch")
    if height_present_count != int(expected["events_with_height_present"]):
        raise ValueError("height-presence provenance mismatch")

    from pyproj import Transformer

    transformer = Transformer.from_crs(
        "EPSG:4326",
        str(contract["primary_horizontal_grid"]["crs"]),
        always_xy=True,
    )
    primary_cells, _ = structural_eligible_cells(
        rows,
        height_field=height_field,
        projector=transformer.transform,
        cell_size_m=float(contract["primary_horizontal_grid"]["cell_size_m"]),
        minimum_events_per_cell=int(
            contract["primary_horizontal_grid"]["minimum_model_events_per_cell"]
        ),
        minimum_distinct_model_individuals_per_cell=int(
            contract["primary_horizontal_grid"][
                "minimum_distinct_model_individuals_per_cell"
            ]
        ),
        split=split,
    )
    if len(primary_cells) != int(expected["primary_structural_eligible_cell_count"]):
        raise ValueError("primary structural eligible-cell provenance mismatch")

    provenance = {
        "tracking_bitstream_id": spec["bitstream_id"],
        "tracking_md5": hashlib.md5(data).hexdigest(),
        "tracking_row_count": len(rows),
        "canonical_headers": headers,
        "individual_count": len(ids),
        "model_individual_ids": model_ids,
        "sealed_individual_ids": sealed_ids,
        "events_with_finite_xy": finite_xy_count,
        "events_with_height_present": height_present_count,
        "primary_structural_eligible_cell_count": len(primary_cells),
        "primary_structural_eligible_cells": [
            f"{cell[0]}:{cell[1]}" for cell in sorted(primary_cells)
        ],
        "outlier_flag_encodings": outlier_encodings,
        "numeric_height_values_parsed": False,
    }
    return authorization, contract, rows, split, primary_cells, transformer.transform, provenance


def execute_numeric_phase(
    *,
    authorization: dict[str, object],
    contract: dict[str, object],
    rows: list[dict[str, str]],
    split: dict[str, str],
    primary_cells,
    projector,
    provenance: dict[str, object],
) -> dict[str, object]:
    height_field = str(contract["axis_semantics"]["z_field"])
    finite_n, structural_joint_n, finite_fraction = (
        finite_height_fraction_among_structural_joint_events(
            rows,
            height_field=height_field,
        )
    )
    qc = contract["numeric_qc"]
    qc_threshold = float(qc["minimum_fraction_finite_height_among_structurally_joint_events"])
    primary_edges = parse_edges(contract["z_discretization"]["primary_edges_m"])
    grid = contract["primary_horizontal_grid"]
    minimum_scored = int(
        contract["sealed_answer_check"]["minimum_scored_events_per_sealed_individual"]
    )

    if finite_fraction is None or finite_fraction < qc_threshold:
        return {
            "authorization_id": authorization["authorization_id"],
            "contract_id": contract["contract_id"],
            "terminal_category": "empirical_n2_thickness_unavailable",
            "numeric_qc": {
                "finite_height_count": finite_n,
                "structural_joint_event_count": structural_joint_n,
                "finite_height_fraction": finite_fraction,
                "minimum_required_fraction": qc_threshold,
                "passes": False,
            },
            "primary": None,
            "sensitivities": {
                "status": "not_evaluable_due_primary_numeric_qc"
            },
            "primary_decision_not_overridden_by_sensitivity": True,
            "raw_numeric_height_values_persisted": False,
            "post_outcome_retuning": False,
            "pre_numeric_provenance": provenance,
        }

    primary = evaluate_thickness_configuration(
        rows,
        height_field=height_field,
        projector=projector,
        cell_size_m=float(grid["cell_size_m"]),
        z_edges=primary_edges,
        minimum_events_per_cell=int(grid["minimum_model_events_per_cell"]),
        minimum_distinct_model_individuals_per_cell=int(
            grid["minimum_distinct_model_individuals_per_cell"]
        ),
        minimum_scored_events_per_sealed_individual=minimum_scored,
        jeffreys_alpha=0.5,
        split=split,
        fixed_eligible_cells=set(primary_cells),
        exclude_marked_outliers=False,
    )
    terminal = terminal_category_from_primary(
        finite_height_fraction=finite_fraction,
        minimum_finite_height_fraction=qc_threshold,
        primary=primary,
    )

    grid_sensitivities: dict[str, object] = {}
    for cell_size in contract["grid_sensitivity"]["cell_sizes_m"]:
        result = evaluate_thickness_configuration(
            rows,
            height_field=height_field,
            projector=projector,
            cell_size_m=float(cell_size),
            z_edges=primary_edges,
            minimum_events_per_cell=int(grid["minimum_model_events_per_cell"]),
            minimum_distinct_model_individuals_per_cell=int(
                grid["minimum_distinct_model_individuals_per_cell"]
            ),
            minimum_scored_events_per_sealed_individual=minimum_scored,
            jeffreys_alpha=0.5,
            split=split,
            fixed_eligible_cells=None,
            exclude_marked_outliers=False,
        )
        grid_sensitivities[str(int(cell_size))] = compact_sensitivity(result)

    bin_sensitivities: list[dict[str, object]] = []
    for index, values in enumerate(contract["z_discretization"]["sensitivity_edges_m"], start=1):
        edges = parse_edges(values)
        result = evaluate_thickness_configuration(
            rows,
            height_field=height_field,
            projector=projector,
            cell_size_m=float(grid["cell_size_m"]),
            z_edges=edges,
            minimum_events_per_cell=int(grid["minimum_model_events_per_cell"]),
            minimum_distinct_model_individuals_per_cell=int(
                grid["minimum_distinct_model_individuals_per_cell"]
            ),
            minimum_scored_events_per_sealed_individual=minimum_scored,
            jeffreys_alpha=0.5,
            split=split,
            fixed_eligible_cells=set(primary_cells),
            exclude_marked_outliers=False,
        )
        payload = compact_sensitivity(result)
        payload["sensitivity_index"] = index
        bin_sensitivities.append(payload)

    outlier_result = evaluate_thickness_configuration(
        rows,
        height_field=height_field,
        projector=projector,
        cell_size_m=float(grid["cell_size_m"]),
        z_edges=primary_edges,
        minimum_events_per_cell=int(grid["minimum_model_events_per_cell"]),
        minimum_distinct_model_individuals_per_cell=int(
            grid["minimum_distinct_model_individuals_per_cell"]
        ),
        minimum_scored_events_per_sealed_individual=minimum_scored,
        jeffreys_alpha=0.5,
        split=split,
        fixed_eligible_cells=set(primary_cells),
        exclude_marked_outliers=True,
    )

    return {
        "authorization_id": authorization["authorization_id"],
        "contract_id": contract["contract_id"],
        "terminal_category": terminal,
        "numeric_qc": {
            "finite_height_count": finite_n,
            "structural_joint_event_count": structural_joint_n,
            "finite_height_fraction": finite_fraction,
            "minimum_required_fraction": qc_threshold,
            "passes": True,
        },
        "primary": compact_result(primary, include_local=True),
        "sensitivities": {
            "grid": grid_sensitivities,
            "z_bins": bin_sensitivities,
            "source_marked_outlier_exclusion": compact_sensitivity(outlier_result),
            "cannot_override_primary": True,
        },
        "primary_decision_not_overridden_by_sensitivity": True,
        "raw_numeric_height_values_persisted": False,
        "height_summary_statistics_persisted": False,
        "post_outcome_retuning": False,
        "predecessor_tawaki_result": "empirical_gate_d_unavailable",
        "pre_numeric_provenance": provenance,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pre_failure = args.output_dir / "pre_numeric_failure.json"
    marker = args.output_dir / "numeric_open_marker.json"
    receipt_path = args.output_dir / "n2_bat_thickness_terminal_receipt.json"
    invalid_path = args.output_dir / "numeric_open_invalid_execution.json"

    try:
        authorization, contract, rows, split, primary_cells, projector, provenance = pre_numeric_phase()
    except Exception as exc:  # pre-outcome technical lane; numeric height not opened
        write_json(
            pre_failure,
            {
                "authorization_id": "odsp-n2-bat-thickness-execution-v1",
                "pre_numeric_status": "failed",
                "reason_type": type(exc).__name__,
                "reason": str(exc),
                "numeric_height_opened": False,
                "scientific_terminal_decision": False,
            },
        )
        print(json.dumps({"pre_numeric_status": "failed", "numeric_height_opened": False}))
        return 2

    write_json(
        marker,
        {
            "authorization_id": authorization["authorization_id"],
            "contract_id": contract["contract_id"],
            "numeric_height_open_started": True,
            "source_md5": provenance["tracking_md5"],
            "pre_numeric_provenance_fingerprint": hashlib.sha256(
                json.dumps(provenance, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "scientific_terminal_decision": False,
        },
    )

    try:
        receipt = execute_numeric_phase(
            authorization=authorization,
            contract=contract,
            rows=rows,
            split=split,
            primary_cells=primary_cells,
            projector=projector,
            provenance=provenance,
        )
        receipt["scientific_terminal_decision"] = True
        receipt["numeric_open_marker_present"] = True
        write_json(receipt_path, receipt)
    except Exception as exc:  # no rerun permitted after this point
        write_json(
            invalid_path,
            {
                "authorization_id": authorization["authorization_id"],
                "contract_id": contract["contract_id"],
                "numeric_height_open_started": True,
                "scientific_terminal_decision": False,
                "execution_status": "invalid_after_numeric_open_no_rerun",
                "reason_type": type(exc).__name__,
                "reason": str(exc),
                "post_outcome_retuning": False,
            },
        )
        print(json.dumps({"execution_status": "invalid_after_numeric_open_no_rerun"}))
        return 3

    print(
        json.dumps(
            {
                "authorization_id": authorization["authorization_id"],
                "terminal_category": receipt["terminal_category"],
                "scientific_terminal_decision": True,
                "output": str(receipt_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
