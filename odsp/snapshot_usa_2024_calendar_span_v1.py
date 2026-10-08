"""Standalone predeclared Snapshot USA 2024 calendar-span structural screen v1.

Read DEPLOYMENT metadata only. Start_Date and End_Date describe the contributor's
physical camera installation and retrieval dates. Date difference is candidate
calendar exposure, NOT confirmation of camera uptime or observation effort.
Survey_Nights was derived from image times in the source paper; this v1 never
reads that field, even if it exists in the downloaded deployment CSV.

No species, detection, sequence timestamps, probability scores or ecological
outcomes are read. Structural support is not iid sampling or inference.
"""
from __future__ import annotations

import csv
from datetime import date
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Any

SCREEN_ID = "odsp-snapshot-usa-2024-calendar-span-deployment-screen-v1"
FROZEN_FILE = "ssusa_2024_deployments.csv"
FORBIDDEN_FILE = "ssusa_2024_sequences.csv"
CATEGORIES = ("forest", "grassland")
REQUIRED = frozenset((
    "Project", "State", "Camera_Trap_Array", "Site_Name",
    "Deployment_ID", "Start_Date", "End_Date", "Habitat"
))
ALLOWED = frozenset((
    "Project", "State", "Camera_Trap_Array", "Site_Name", "Deployment_ID",
    "Start_Date", "End_Date", "Habitat", "Development_Level", "Feature_Type",
    "Latitude", "Longitude"
))
FORBIDDEN = frozenset((
    "Sequence_ID", "Species", "Common_Name", "Start_Time", "End_Time",
    "Class", "Order", "Family", "Genus", "Image_Count", "Group_Size"
))
FEATURE_TOKENS = ("trail", "road", "water", "bait", "feeder", "salt")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
MINIMUM_CALENDAR_NIGHTS = 30
MINIMUM_SITES = 8
MINIMUM_ARRAYS = 8
MAX_CSV_BYTES = 10_000_000


def _str(value: str | None) -> str:
    return "" if value is None else value.strip()


def _positive_date(value: str) -> date | None:
    if not DATE_RE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _single_interval_nights(start: str, end: str) -> int | None:
    first = _positive_date(start)
    last = _positive_date(end)
    if first is None or last is None:
        return None
    nights = (last - first).days
    return nights if 0 <= nights <= 366 else None


def _coords(lat_raw: str, lon_raw: str) -> tuple[float, float] | None:
    try:
        lat, lon = float(lat_raw), float(lon_raw)
    except ValueError:
        return None
    if not math.isfinite(lat) or not math.isfinite(lon):
        return None
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        return None
    return round(lat, 4), round(lon, 4)


def _group(value: str) -> str | None:
    lower = value.casefold()
    is_forest = "forest" in lower
    is_grassland = "grassland" in lower
    if is_forest == is_grassland:
        return None
    return "forest" if is_forest else "grassland"


def validate_calendar_screen_contract(contract: dict[str, Any]) -> None:
    if (
        not isinstance(contract, dict)
        or contract.get("schema_version") != 1
        or contract.get("contract_id") != SCREEN_ID
        or contract.get("source", {}).get("file_name") != FROZEN_FILE
        or contract.get("source", {}).get("prohibited_file_name") != FORBIDDEN_FILE
        or contract.get("habitat_groups", {}).get("ordered") != list(CATEGORIES)
        or contract.get("habitat_groups", {}).get("minimum_calendar_span_nights")
            != MINIMUM_CALENDAR_NIGHTS
        or contract.get("habitat_groups", {}).get("minimum_unique_sites_per_group")
            != MINIMUM_SITES
        or contract.get("habitat_groups", {}).get("minimum_distinct_arrays_per_group")
            != MINIMUM_ARRAYS
        or contract.get("site_and_deployment", {}).get("site_counted_once") is not True
        or contract.get("primary_confirmatory_qualified") is not False
    ):
        raise ValueError("frozen calendar-span v1 contract mismatch")
    actual_allowed = contract.get("outcome_independent_input_only")
    if not isinstance(actual_allowed, list) or set(actual_allowed) != ALLOWED:
        raise ValueError("allowed deployment-only input fields changed")
    if FORBIDDEN.intersection(actual_allowed) or "Survey_Nights" in actual_allowed:
        raise ValueError("outcome-derived input is forbidden")


def audit_calendar_metadata(
    raw: bytes,
    contract: dict[str, Any],
    *,
    contract_sha256: str,
) -> dict[str, Any]:
    """Return aggregate-only structural counts from placement/retrieval dates."""
    validate_calendar_screen_contract(contract)
    if not isinstance(raw, bytes) or len(raw) < 40 or len(raw) > MAX_CSV_BYTES:
        raise ValueError("invalid or oversized deployment CSV")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("metadata must be UTF-8 CSV") from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = tuple(col.strip() for col in next(reader))
    except StopIteration:
        raise ValueError("empty deployment metadata") from None
    if len(header) != len(set(header)):
        raise ValueError("duplicate column names")
    if header and header[0].lstrip().startswith("<"):
        raise ValueError("HTML is not metadata CSV")
    if FORBIDDEN.intersection(header):
        raise ValueError("response/timestamp sequence column in metadata")
    if not REQUIRED.issubset(header):
        raise ValueError("missing frozen required deployment columns")
    # Header discovery is allowed but content is read ONLY in the frozen
    # physical-placement columns. Survey_Nights is deliberately not accessed.
    indexes = {field: header.index(field) for field in ALLOWED if field in header}
    sites: dict[tuple[str, str, str], dict[str, Any]] = {}
    deployment_to_site: dict[tuple[str, str], tuple[str, str, str]] = {}
    conflicting_deployments: set[tuple[str, str]] = set()
    all_rows = malformed_rows = missing_ids = invalid_date_rows = 0
    same_deployment_repeat_rows = 0
    bad_coordinate_rows = 0

    for row in reader:
        if not row or not any(col.strip() for col in row):
            continue
        all_rows += 1
        if len(row) != len(header):
            malformed_rows += 1
            continue
        data = {key: _str(row[index]) for key, index in indexes.items()}
        project, array = data["Project"], data["Camera_Trap_Array"]
        site, dep = data["Site_Name"], data["Deployment_ID"]
        if not all((project, array, site, dep)):
            missing_ids += 1
            continue
        site_key = (project, array, site)
        deployment_key = (project, dep)
        earlier = deployment_to_site.setdefault(deployment_key, site_key)
        if earlier != site_key:
            conflicting_deployments.add(deployment_key)
        else:
            # Repeated rows, possibly multiple uploaded batches from one
            # deployment, never create a new independent physical site.
            if (earlier == site_key and
                    deployment_key in deployment_to_site and
                    sites.get(site_key, {}).get("deployment_keys", set())
                    and deployment_key in sites[site_key]["deployment_keys"]):
                same_deployment_repeat_rows += 1

        nights = _single_interval_nights(
            data.get("Start_Date", ""), data.get("End_Date", "")
        )
        if nights is None:
            invalid_date_rows += 1
        position = _coords(
            data.get("Latitude", ""), data.get("Longitude", "")
        )
        if position is None:
            bad_coordinate_rows += 1
        group = _group(data.get("Habitat", ""))
        state = data.get("State", "")
        feature = data.get("Feature_Type", "").casefold()
        entry = sites.setdefault(site_key, {
            "states": set(), "groups": set(), "locations": set(),
            "any_bad_coordinate": False, "max_single_span": None,
            "flagged_feature": False, "deployment_keys": set(),
        })
        entry["deployment_keys"].add(deployment_key)
        entry["states"].add(state)
        entry["groups"].add(group)
        if position is None:
            entry["any_bad_coordinate"] = True
        else:
            entry["locations"].add(position)
        if nights is not None:
            entry["max_single_span"] = (
                nights if entry["max_single_span"] is None
                else max(nights, entry["max_single_span"])
            )
        entry["flagged_feature"] |= any(t in feature for t in FEATURE_TOKENS)

    conflict_site_keys: set[tuple[str, str, str]] = set()
    for dep in conflicting_deployments:
        for key, site in deployment_to_site.items():
            if key == dep:
                conflict_site_keys.add(site)
        # The reused deployment ID could also appear in a second site.
        # Rather than trusting the first match, we retain an explicit
        # set of encountered sites below, recorded on a second pass.
    # A single scan must preserve ALL sites with conflicting deployment
    # IDs, including later appearances (handled in the table below).

    groups = {
        group: {"all_matching_sites": 0, "eligible_sites": 0,
                "eligible_arrays": set(), "eligible_states": set(),
                "secondary_no_feature_sites": 0,
                "secondary_no_feature_arrays": set()}
        for group in CATEGORIES
    }
    all_arrays = {(p, a) for (p, a, s) in sites}
    all_states: set[str] = set()
    conflict_habitat = conflict_coordinates = conflict_states = 0
    sites_missing_valid_interval = 0
    sites_missing_coordinates = 0
    sites_with_conflicting_deployment_ids = 0

    for site_key, info in sites.items():
        all_states.update(s for s in info["states"] if s)
        conflict_habitat += len(info["groups"]) != 1 or None in info["groups"]
        conflict_coordinates += len(info["locations"]) > 1
        conflict_states += len(info["states"]) != 1 or "" in info["states"]
        sites_missing_valid_interval += info["max_single_span"] is None
        sites_missing_coordinates += info["any_bad_coordinate"]
        has_deployment_conflict = bool(info["deployment_keys"] & conflicting_deployments)
        sites_with_conflicting_deployment_ids += has_deployment_conflict

        if len(info["groups"]) != 1 or None in info["groups"]:
            continue
        group = next(iter(info["groups"]))
        groups[group]["all_matching_sites"] += 1
        if (
            len(info["states"]) != 1 or "" in info["states"]
            or len(info["locations"]) != 1 or info["any_bad_coordinate"]
            or info["max_single_span"] is None
            or info["max_single_span"] < MINIMUM_CALENDAR_NIGHTS
            or has_deployment_conflict
        ):
            continue
        entry = groups[group]
        entry["eligible_sites"] += 1
        entry["eligible_arrays"].add(site_key[:2])
        entry["eligible_states"].update(info["states"])
        if not info["flagged_feature"]:
            entry["secondary_no_feature_sites"] += 1
            entry["secondary_no_feature_arrays"].add(site_key[:2])

    aggregate = {
        group: {
            "habitat_matching_sites": groups[group]["all_matching_sites"],
            "sites_with_one_calendar_interval_ge30": groups[group]["eligible_sites"],
            "distinct_arrays": len(groups[group]["eligible_arrays"]),
            "distinct_states": len(groups[group]["eligible_states"]),
            "secondary_no_trail_road_water_bait_sites":
                groups[group]["secondary_no_feature_sites"],
            "secondary_no_trail_road_water_bait_arrays":
                len(groups[group]["secondary_no_feature_arrays"]),
        }
        for group in CATEGORIES
    }
    structural_pass = all(
        aggregate[g]["sites_with_one_calendar_interval_ge30"] >= MINIMUM_SITES
        and aggregate[g]["distinct_arrays"] >= MINIMUM_ARRAYS
        for g in CATEGORIES
    )
    return {
        "schema_version": 1,
        "screen_id": SCREEN_ID,
        "structural_status": (
            "CALENDAR_SPAN_STRUCTURAL_COUNTS_UNVERIFIED_IID"
            if structural_pass else "HOLD_CALENDAR_SPAN_STRUCTURE_INSUFFICIENT"
        ),
        "contract_sha256": contract_sha256,
        "deployment_csv_sha256": hashlib.sha256(raw).hexdigest(),
        "deployment_source_bytes": len(raw),
        "deployment_row_count": all_rows,
        "malformed_csv_row_count": malformed_rows,
        "missing_identity_row_count": missing_ids,
        "invalid_placement_retrieval_date_row_count": invalid_date_rows,
        "invalid_coordinate_row_count": bad_coordinate_rows,
        "repeated_deployment_rows": same_deployment_repeat_rows,
        "conflicted_deployment_ids": len(conflicting_deployments),
        "sites_containing_conflicted_deployment_ids": sites_with_conflicting_deployment_ids,
        "distinct_site_count": len(sites),
        "distinct_array_count": len(all_arrays),
        "distinct_state_count": len(all_states),
        "sites_with_ambiguous_habitat": conflict_habitat,
        "sites_with_ambiguous_coordinates": conflict_coordinates,
        "sites_with_ambiguous_state": conflict_states,
        "sites_with_no_valid_single_calendar_interval": sites_missing_valid_interval,
        "sites_with_any_invalid_coordinates": sites_missing_coordinates,
        "predeclared_groups": aggregate,
        "group_count_gate_met": structural_pass,
        "source_sequence_csv_accessed": False,
        "sequence_labels_timestamps_accessed": False,
        "source_survey_nights_image_derived_column_read": False,
        "true_active_camera_effort_verified": False,
        "sites_iid_verified": False,
        "arrays_iid_verified": False,
        "full_training_validation_physical_unit_disjointness_verified": False,
        "unseen_model_to_score_provenance_verified": False,
        "primary_confirmatory_qualified": False,
        "historical_v0_or_empirical_routes_reclassified": False,
        "precise_camera_coordinates_or_site_ids_in_output": False,
    }


def audit_calendar_file(path: Path, contract_path: Path) -> dict[str, Any]:
    frozen = contract_path.read_bytes()
    return audit_calendar_metadata(
        path.read_bytes(), json.loads(frozen),
        contract_sha256=hashlib.sha256(frozen).hexdigest(),
    )
