"""Post-exposure RI v3 structural attrition audit, with NO ecological scores.

This reports only stagewise source-data quality. It never outputs any
individual animal species label, image date/time, site/station/device ID,
coordinate or phase/clock outcome. Earlier v0/v1 source failures remain
terminal; this audit is NOT a new inferential attempt.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import re
from typing import Mapping, Any

from .ri_solar_clock_schema_v1 import (
    SITE, STATION, CAMERA, SEASON, SPECIES, DATE_TIME,
    _key, _season, _datetime, _validate_contract,
    DEPLOYMENT_HEADER, DETECTION_HEADER, EXCLUDED_SPECIES,
)
from .ri_solar_source_v0 import (
    _member_zip_csv, _dst_clock_hour_maybe_invalid,
)

AUDIT_VERSION="odsp-ri-camera-v3-source-attrition-v0"


def _datetime_shape(raw: str)->str:
    value=raw.strip()
    if not value:
        return "blank"
    if re.match(r"^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}",value):
        return "YYYY-MM-DD prefix"
    if re.match(r"^[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}",value):
        return "slash date prefix"
    if re.match(r"^[0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4}",value):
        return "day-monthname-year prefix"
    if re.match(r"^[0-9]+(?:\\.[0-9]+)?$",value):
        return "numeric or spreadsheet serial"
    return "other format"


def inspect_source_attrition_without_ecological_scores(
    archived_bytes:bytes,
    v1_plan:Mapping[str,object],
    audit_plan:Mapping[str,object],
)->dict[str,Any]:
    if (audit_plan.get("audit_id")!=AUDIT_VERSION
        or audit_plan.get("status")!="FROZEN_AFTER_TWO_UNAVAILABLE_SOURCE_RUNS_POSTEXPOSURE_DATA_QUALITY_ONLY"):
        raise ValueError("unfrozen RI source attrition contract")
    _validate_contract(v1_plan)
    tables=_member_zip_csv(archived_bytes)
    deployments=tables["RI_CameraSurvey_Deployments.csv"]
    detections=tables["RI_CameraSurvey_Detections.csv"]
    if (not deployments or tuple(deployments[0])!=DEPLOYMENT_HEADER
        or not detections or tuple(detections[0])!=DETECTION_HEADER):
        raise ValueError("source header differs from pinned v1 field semantics")
    valid_deployments=set()
    dep_counts=Counter()
    dep_yearseason=Counter()
    for row in deployments:
        dep_counts["total"]+=1
        dep_yearseason[row[SEASON].strip()]+=1
        key=_key(row)
        if any(not x for x in key):
            dep_counts["blank_composite"]+=1
            continue
        try:
            lat,lon=float(row["Latitude"]),float(row["Longitude"])
        except (ValueError,TypeError):
            dep_counts["invalid_coordinate"]+=1
            continue
        if not math.isfinite(lat) or not math.isfinite(lon) or not 39<=lat<=43 or not -74<=lon<=-70:
            dep_counts["invalid_coordinate"]+=1
            continue
        valid_deployments.add(key)
        dep_counts["eligible_four_part_key"]+=1

    stage=Counter()
    independent_checks=Counter()
    season_categories=Counter()
    time_shapes=Counter()
    site_of_usable=set()
    for row in detections:
        stage["all_detection_rows"]+=1
        key=_key(row)
        season_categories[row[SEASON].strip()]+=1
        time_shapes[_datetime_shape(row.get(DATE_TIME) or "")]+=1
        key_ok=all(key)
        season_ok=_season(key[0]) is not None
        species_value=(row.get(SPECIES) or "").strip().casefold()
        species_ok=bool(species_value) and species_value not in EXCLUDED_SPECIES
        join_ok=key in valid_deployments
        timestamp=_datetime(row)
        datetime_ok=timestamp is not None
        daylight_ok=datetime_ok and not _dst_clock_hour_maybe_invalid(timestamp)
        if key_ok: independent_checks["complete_site_station_camera_season"]+=1
        if season_ok: independent_checks["recognized_yearseason_syntax"]+=1
        if species_ok: independent_checks["nonblank_named_species"]+=1
        if join_ok: independent_checks["exact_composite_deployment_join"]+=1
        if datetime_ok: independent_checks["parseable_Date_Time_or_fallback"]+=1
        if daylight_ok: independent_checks["nonambiguous_local_datetime"]+=1
        if not key_ok:
            stage["first_reject_missing_composite"]+=1
        elif not season_ok:
            stage["first_reject_unknown_YearSeason_syntax"]+=1
        elif not species_ok:
            stage["first_reject_blank_or_nontarget_species"]+=1
        elif not join_ok:
            stage["first_reject_no_exact_deployment_join"]+=1
        elif not datetime_ok:
            stage["first_reject_unparseable_datetime"]+=1
        elif not daylight_ok:
            stage["first_reject_dst_ambiguous_datetime"]+=1
        else:
            stage["candidate_usable_raw_detection_rows"]+=1
            site_of_usable.add(key[1])
    allowed=(
        "first_reject_missing_composite",
        "first_reject_unknown_YearSeason_syntax",
        "first_reject_blank_or_nontarget_species",
        "first_reject_no_exact_deployment_join",
        "first_reject_unparseable_datetime",
        "first_reject_dst_ambiguous_datetime",
        "candidate_usable_raw_detection_rows",
    )
    assert sum(stage[k] for k in allowed)==len(detections)
    def aggregate_labels(counter):
        return [
            {"label":key if key else "<blank>","row_count":n}
            for key,n in sorted(counter.items(),key=lambda x:(-x[1],x[0]))[:30]
        ]
    return {
        "schema_version":1,
        "audit_id":AUDIT_VERSION,
        "source_md5_hash_only":hashlib.md5(archived_bytes).hexdigest(),
        "deployment_rows":len(deployments),
        "detection_rows":len(detections),
        "deployment_structural_checks":dict(dep_counts),
        "independent_detection_pass_rates":{
            key:{"count":count,"fraction":count/len(detections)}
            for key,count in sorted(independent_checks.items())
        },
        "first_rejection_stage_counts":{key:stage[key] for key in allowed},
        "deployment_YearSeason_metadata_labels":aggregate_labels(dep_yearseason),
        "detection_YearSeason_metadata_labels":aggregate_labels(season_categories),
        "Date_Time_text_shape_counts":dict(sorted(time_shapes.items())),
        "distinct_physical_primary_site_count_of_all_candidate_rows":len(site_of_usable),
        "source_raw_species_taxa_values_exposed":False,
        "source_exact_photo_datetime_values_exposed":False,
        "source_site_station_camera_ids_exposed":False,
        "individual_clock_bins_or_solar_phases_computed":False,
        "prediction_models_fitted":False,
        "ecological_gain_computed":False,
        "prior_terminal_v0_v1_reclassified":False,
        "all_public_data_previously_unopened_claimed":False,
        "source_admission_allowed_from_this_report":False,
    }
