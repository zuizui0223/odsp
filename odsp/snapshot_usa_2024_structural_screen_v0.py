"""Outcome-blind structural census of Snapshot USA 2024 camera deployments.

Only the 2024 deployment file is accepted; sequence/time/species records are
forbidden and are never fetched. Site counts, array counts, and habitat
distribution are STRUCTURAL support numbers, not iid ecological sample sizes.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

CONTRACT_FILE = "ODSP_SNAPSHOT_USA_2024_DEPLOYMENT_SCREEN_V0_CONTRACT.json"
REQUIRED_FIELDS = (
    "Project", "State", "Camera_Trap_Array", "Site_Name", "Deployment_ID",
    "Survey_Nights", "Habitat",
)
FORBIDDEN_FIELDS = frozenset(
    ("Sequence_ID", "Start_Time", "End_Time", "Species", "Common_Name",
     "Class", "Order", "Family", "Genus", "Behavior", "Group_Size")
)
ATTRACTORS = ("trail", "road", "water", "bait", "feeder", "salt")
CANONICAL_GROUPS = ("forest", "grassland")


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _habitat_group(value: str) -> str | None:
    label = value.strip().casefold()
    forest = "forest" in label
    grassland = "grassland" in label
    if forest == grassland:
        return None
    return "forest" if forest else "grassland"


def _parse_nights(value: str) -> float | None:
    v = value.strip()
    try:
        parsed = float(v)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0 else None


def _coord_key(latitude: str, longitude: str) -> tuple[float, float] | None:
    try:
        lat, lon = float(latitude), float(longitude)
    except ValueError:
        return None
    if not (math.isfinite(lat) and math.isfinite(lon)
            and -90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    # Only used for aggregate duplicate diagnostics; never returned.
    return round(lat, 4), round(lon, 4)


def _validate_contract(contract: dict[str, Any]) -> None:
    if (contract.get("schema_version") != 1
        or contract.get("contract_id") !=
          "odsp-snapshot-usa-2024-deployment-structural-screen-v0"
        or contract.get("source", None) is not None
        or contract.get("published_source", {}).get("metadata_filename")
            != "ssusa_2024_deployments.csv"
        or contract.get("published_source", {}).get("forbidden_sequence_filename")
            != "ssusa_2024_sequences.csv"
        or contract.get("predeclared_group_definition", {}).get("group_a")
            != "forest"
        or contract.get("predeclared_group_definition", {}).get("group_b")
            != "grassland"
        or contract.get("predeclared_group_definition", {}).get("per_site_minimum_survey_nights")
            != 30
        or contract.get("predeclared_group_definition", {}).get("per_group_minimum_distinct_arrays")
            != 8
        or contract.get("predeclared_group_definition", {}).get("per_group_minimum_distinct_sites")
            != 8
        or contract.get("counting_and_reporting", {}).get("report_only_aggregate_counts") is not True
        or contract.get("gate", {}).get("automatic_primary_route_promotion") is not False
        or contract.get("preexisting_exposure", {}).get("actual_deployment_csv_records_read_before_this_freeze") is not False):
        raise ValueError("frozen structural-screen contract differs from v0")
    fields = contract.get("allowed_columns_only")
    if not isinstance(fields, list) or any(x in FORBIDDEN_FIELDS for x in fields):
        raise ValueError("forbidden field in allowed-column list")
    if not set(REQUIRED_FIELDS).issubset(set(fields)):
        raise ValueError("required deployment columns not allowed")


def audit_deployment_bytes(
    raw: bytes,
    contract: dict[str, Any],
    *,
    contract_sha256: str,
) -> dict[str, Any]:
    """Aggregate only site deployment covariates, never individual outcomes."""
    _validate_contract(contract)
    if not isinstance(raw, bytes) or len(raw) < 50 or len(raw) > 10_000_000:
        raise ValueError("metadata bytes absent or exceed frozen 10 MB ceiling")
    try:
        data = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("deployment file must be UTF-8 CSV") from exc
    handle = io.StringIO(data, newline="")
    reader = csv.reader(handle)
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("empty deployment CSV") from None
    names = tuple(x.strip() for x in header)
    if len(names) != len(set(names)):
        raise ValueError("duplicated deployment column name")
    if FORBIDDEN_FIELDS.intersection(names):
        raise ValueError("response-bearing sequence column encountered in deployment CSV")
    missing = set(REQUIRED_FIELDS) - set(names)
    if missing:
        raise ValueError(f"deployment metadata lacks required columns {sorted(missing)}")
    allowed = frozenset(contract["allowed_columns_only"])
    positions = {name: i for i, name in enumerate(names) if name in allowed}

    # Do not even bind/inspect values in unlisted columns. Only allowed
    # deployment identities, effort and habitat/feature fields are read.
    sites: dict[tuple[str, str, str], dict[str, Any]] = {}
    total_rows = 0
    bad_csv_shape = 0
    missing_ids = 0
    missing_effort = 0
    duplicate_deployments = 0
    seen_deployments: set[str] = set()

    for row in reader:
        if not row or not any(x.strip() for x in row):
            continue
        total_rows += 1
        if len(row) != len(names):
            bad_csv_shape += 1
            continue
        obj = {name: _text(row[i]) for name, i in positions.items()}
        project = obj["Project"]
        array = obj["Camera_Trap_Array"]
        site = obj["Site_Name"]
        deployment = obj["Deployment_ID"]
        if not (project and array and site and deployment):
            missing_ids += 1
            continue
        source_id = (project, array, site)
        dep_key = f"{project}\0{deployment}"
        if dep_key in seen_deployments:
            duplicate_deployments += 1
        else:
            seen_deployments.add(dep_key)
        group = _habitat_group(obj.get("Habitat", ""))
        nights = _parse_nights(obj.get("Survey_Nights", ""))
        if nights is None:
            missing_effort += 1
        coord = _coord_key(obj.get("Latitude", ""), obj.get("Longitude", ""))
        state = obj["State"]
        physical_array = (project, array)
        feature = obj.get("Feature_Type", "").casefold()
        suspect_feature = any(token in feature for token in ATTRACTORS)

        record = sites.setdefault(source_id, {
            "groups": set(), "state_names": set(),
            "max_nights": None, "coordinates": set(),
            "missing_coordinates": False, "attraction_feature": False,
            "physical_array": physical_array,
            "rows": 0,
        })
        record["rows"] += 1
        record["groups"].add(group)
        if state:
            record["state_names"].add(state)
        if nights is not None:
            record["max_nights"] = (
                nights if record["max_nights"] is None
                else max(nights, record["max_nights"])
            )
        if coord is None:
            record["missing_coordinates"] = True
        else:
            record["coordinates"].add(coord)
        record["attraction_feature"] |= suspect_feature

    counts: dict[str, dict[str, object]] = {}
    site_group_ambiguous = 0
    site_coord_ambiguous = 0
    site_state_ambiguous = 0
    sites_without_coordinates = 0
    sites_without_effort = 0
    all_arrays = set()
    all_states = set()
    for key, info in sites.items():
        all_arrays.add(info["physical_array"])
        all_states.update(info["state_names"])
        site_coord_ambiguous += len(info["coordinates"]) > 1
        site_state_ambiguous += len(info["state_names"]) > 1
        sites_without_coordinates += info["missing_coordinates"]
        sites_without_effort += info["max_nights"] is None
        if len(info["groups"]) != 1 or None in info["groups"]:
            site_group_ambiguous += 1
            continue
        group = next(iter(info["groups"]))
        assert group in CANONICAL_GROUPS
        summary = counts.setdefault(group, {
            "selected_sites": 0,
            "effort_qualified_sites": 0,
            "effort_qualified_arrays": set(),
            "effort_qualified_states": set(),
            "effort_qualified_without_attraction_feature": 0,
            "feature_filtered_arrays": set(),
            "sites_missing_coordinates_after_effort_gate": 0,
        })
        summary["selected_sites"] += 1
        if (info["max_nights"] is None
                or info["max_nights"] < 30
                or len(info["state_names"]) != 1
                or len(info["coordinates"]) != 1):
            continue
        summary["effort_qualified_sites"] += 1
        summary["effort_qualified_arrays"].add(info["physical_array"])
        summary["effort_qualified_states"].update(info["state_names"])
        if info["missing_coordinates"]:
            summary["sites_missing_coordinates_after_effort_gate"] += 1
        if not info["attraction_feature"]:
            summary["effort_qualified_without_attraction_feature"] += 1
            summary["feature_filtered_arrays"].add(info["physical_array"])

    output_groups = {}
    for group in CANONICAL_GROUPS:
        result = counts.get(group, {})
        output_groups[group] = {
            "all_selected_sites_before_effort_gate": result.get("selected_sites", 0),
            "sites_after_max_deployment_nights_ge30": result.get("effort_qualified_sites", 0),
            "distinct_arrays_after_effort_gate": len(result.get("effort_qualified_arrays", set())),
            "distinct_states_after_effort_gate": len(result.get("effort_qualified_states", set())),
            "sites_not_flagged_attraction_feature": result.get("effort_qualified_without_attraction_feature", 0),
            "arrays_not_flagged_attraction_feature": len(result.get("feature_filtered_arrays", set())),
            "sites_with_one_missing_coordinate_deployment": result.get("sites_missing_coordinates_after_effort_gate", 0),
        }
    valid_minima = all(
        output_groups[g]["sites_after_max_deployment_nights_ge30"] >= 8
        and output_groups[g]["distinct_arrays_after_effort_gate"] >= 8
        for g in CANONICAL_GROUPS
    )
    return {
        "schema_version":1,
        "screen":"outcome_blind_snapshot_usa_2024_deployment_structural_screen_v0",
        "status":"STRUCTURAL_COUNTS_ONLY_UNVERIFIED_INDEPENDENCE" if valid_minima
                 else "HOLD_INSUFFICIENT_STRUCTURAL_COUNTS",
        "contract_sha256":contract_sha256,
        "source_deployment_csv_sha256":hashlib.sha256(raw).hexdigest(),
        "source_file_bytes":len(raw),
        "response_sequence_file_opened":False,
        "species_taxon_or_sequence_time_values_accessed":False,
        "observation_detection_outcomes_accessed":False,
        "site_or_camera_precise_coordinates_exposed_in_receipt":False,
        "deployment_record_count":total_rows,
        "bad_csv_shape_rows":bad_csv_shape,
        "missing_composite_ids_rows":missing_ids,
        "missing_nights_rows":missing_effort,
        "duplicate_deployment_id_rows":duplicate_deployments,
        "distinct_composite_sites":len(sites),
        "distinct_composite_arrays":len(all_arrays),
        "distinct_nonempty_states":len(all_states),
        "sites_with_ambiguous_or_unselected_habitat":site_group_ambiguous,
        "sites_with_multiple_rounded_coordinates":site_coord_ambiguous,
        "sites_with_multiple_states":site_state_ambiguous,
        "sites_with_any_missing_coordinate_row":sites_without_coordinates,
        "sites_without_valid_deployment_nights":sites_without_effort,
        "predeclared_habitat_groups":output_groups,
        "group_count_gate_met":valid_minima,
        "iid_camera_site_selection_verified":False,
        "iid_array_sampling_verified":False,
        "site_spatial_autocorrelation_verified_absent":False,
        "cross_year_original_training_site_overlap_excluded":False,
        "full_original_source_frame_disjoint_verified":False,
        "outcome_freeze_and_model_provenance_verified":False,
        "eligible_for_primary_confirmatory_route":False,
        "prior_empirical_results_reclassified":False,
    }


def read_and_audit_deployment_file(
    path: Path, contract_path: Path
) -> dict[str, Any]:
    raw_contract=contract_path.read_bytes()
    contract=json.loads(raw_contract)
    return audit_deployment_bytes(
        path.read_bytes(), contract,
        contract_sha256=hashlib.sha256(raw_contract).hexdigest(),
    )
