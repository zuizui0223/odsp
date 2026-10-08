"""No-outcome latitude envelope sensitivity for ORIGINAL 41 Uljin day pairs.

Public Uljin approximate geographic extent is 36.6-37.1°N;
individual protected-species station coordinates are withheld.
This checks the SAME frozen representative-latitude match on three
public LATITUDES without re-optimizing the date pairing. Astronomy
precision is not biological precision: actual station effort, calendar
availability and detection probability remain wholly unknown.
"""
from __future__ import annotations

from typing import Any, Mapping
from datetime import date

from .uljin_photoperiod_mirror_design_v0 import (
    apparent_daylength_hours,
    generate_preoutcome_2022_mirror_calendar,
)

CONTRACT_ID="odsp-uljin-2022-astronomical-pair-latitude-sensitivity-v0"


def original_pairs_latitude_sensitivity(
    original_calendar_plan:Mapping[str,object],
    frozen_sensitivity:Mapping[str,object],
)->dict[str,Any]:
    if (
        frozen_sensitivity.get("schema_version")!=1
        or frozen_sensitivity.get("contract_id")!=CONTRACT_ID
        or frozen_sensitivity.get("stage")!=
            "POST_FIRST_ASTRONOMY_ONLY_SOURCE_FREE_ROBUSTNESS"
        or frozen_sensitivity.get("fixed_public_area_latitudes")!=[36.6,36.85,37.1]
        or frozen_sensitivity.get("original_first_pair_count")!=41
        or frozen_sensitivity.get("initial_matching_latitude")!=36.85
        or frozen_sensitivity.get("worst_allowed_mismatch_minutes")!=9
        or frozen_sensitivity.get("sensitivity_same_41_original_pairs_no_rematching") is not True
        or frozen_sensitivity.get("no_original_pairing_rules_modified") is not True
    ):
        raise ValueError("original source-free latitude robustness plan changed")
    calendar=generate_preoutcome_2022_mirror_calendar(original_calendar_plan)
    original=calendar["matched_dates"]
    if len(original)!=41:
        raise ValueError("original 41 astronomically matched dates changed")
    by_lat={}
    for latitude in (36.6,36.85,37.1):
        discrepancies=[]
        for pair in original:
            a=apparent_daylength_hours(
                date.fromisoformat(pair["ascending_date"]),
                latitude,
            )
            b=apparent_daylength_hours(
                date.fromisoformat(pair["descending_date"]),
                latitude,
            )
            discrepancies.append(abs(a-b)*60)
        by_lat[f"{latitude:.2f}"]={
            "pair_count":len(discrepancies),
            "max_daylength_mismatch_minutes":max(discrepancies),
            "mean_daylength_mismatch_minutes":sum(discrepancies)/len(discrepancies),
            "number_over_original_nine_minute_ceiling":sum(
                e>9.0+1e-12 for e in discrepancies
            ),
        }
    return {
        "schema_version":1,
        "analysis_id":CONTRACT_ID,
        "status":"ASTRONOMICAL_LATITUDE_ENVELOPE_ONLY_NOT_AN_ECOLOGICAL_RESULT",
        "original_pair_count_retained_without_rematching":len(original),
        "original_first_pair_run_id":37771342454,
        "public_latitude_envelope":by_lat,
        "all_matched_pairs_within_frozen_daylength_tolerance":all(
            row["number_over_original_nine_minute_ceiling"]==0
            for row in by_lat.values()
        ),
        "individual_station_coordinates_inferred_or_read":False,
        "individual_camera_hourly_effort_verified":False,
        "animal_detection_rows_read":False,
        "source_operation_log_opened":False,
        "original_odsp_ecological_results_reclassified":False,
    }
