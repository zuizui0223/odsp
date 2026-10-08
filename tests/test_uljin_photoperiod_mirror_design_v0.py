"""Synthetic calendar-only tests; no field event data are accessed."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from odsp.uljin_photoperiod_mirror_design_v0 import (
    apparent_daylength_hours,
    generate_preoutcome_2022_mirror_calendar,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"


def frozen():
    return json.loads(PLAN.read_text(encoding="utf-8"))


def test_source_provenance_and_two_region_clustering_are_not_prequalified():
    plan=frozen()
    assert plan["source"]["published_event_count"]==4623
    assert plan["source"]["published_station_count"]==82
    assert plan["source"]["published_inactive_camera_nights"]==560
    assert not plan["source"]["raw_data_download_link_verified"]
    assert not plan["source"]["original_camera_log_not_modified_using_detection_outcomes_verified"]
    assert plan["preoutcome_feasibility_gates"]["minimum_independent_study_regions_for_between_region_population_claim"]==3
    assert plan["preoutcome_feasibility_gates"]["observed_published_region_count"]==2
    assert plan["preoutcome_feasibility_gates"]["exact_operating_time_by_local_clock_category_required"] is True


def test_daylength_changes_astronomically_not_in_response_to_animal_detections():
    latitude=36.85
    winter=apparent_daylength_hours(date(2022,12,21),latitude)
    summer=apparent_daylength_hours(date(2022,6,21),latitude)
    assert 9 < winter < 11
    assert 14 < summer < 16
    assert summer-winter>4
    assert apparent_daylength_hours(date(2022,5,1),latitude)<apparent_daylength_hours(date(2022,6,10),latitude)
    assert apparent_daylength_hours(date(2022,7,1),latitude)>apparent_daylength_hours(date(2022,8,31),latitude)


def test_frozen_mirror_pairing_is_deterministic_and_one_to_one():
    first=generate_preoutcome_2022_mirror_calendar(frozen())
    second=generate_preoutcome_2022_mirror_calendar(frozen())
    assert first==second
    assert first["status"]=="PREDECLARED_ASTRONOMICAL_DATE_PAIR_CATALOG_ONLY"
    assert first["candidate_ascending_dates"]==41
    assert first["candidate_descending_dates"]==62
    assert first["selected_nonoverlapping_calendar_day_pairs"]>=20
    rows=first["matched_dates"]
    assert len(rows)==first["selected_nonoverlapping_calendar_day_pairs"]
    assert len({row["ascending_date"] for row in rows})==len(rows)
    assert len({row["descending_date"] for row in rows})==len(rows)
    assert all(0<=row["daylength_difference_minutes"]<=9.0+1e-8 for row in rows)
    assert all(row["calendar_gap_days"]>=21 for row in rows)
    assert all(row["ascending_date"]<row["descending_date"] for row in rows)
    assert not first["source_operational_log_or_animal_events_accessed"]
    assert not first["actual_station_pairwise_observation_support_verified"]
    assert not first["active_camera_hourly_effort_verified"]
    assert not first["hysteresis_effect_in_wildlife_inferred"]
    json.dumps(first,allow_nan=False)


def test_no_postresult_date_threshold_habitat_or_effort_shortcut():
    plan=frozen()
    plan["preoutcome_structural_pairing"]["pair_absolute_daylength_difference_max_hours"]=1.0
    with pytest.raises(ValueError,match="pairing rules differ"):
        generate_preoutcome_2022_mirror_calendar(plan)
    plan=frozen()
    plan["preoutcome_feasibility_gates"]["exact_operating_time_by_local_clock_category_required"]=False
    with pytest.raises(ValueError,match="effort provenance"):
        generate_preoutcome_2022_mirror_calendar(plan)


def test_polar_latitude_is_not_silently_treated_like_korean_study():
    with pytest.raises(ValueError,match="nonpolar"):
        apparent_daylength_hours(date(2022,12,21),85.0)
    with pytest.raises(ValueError,match="zenith"):
        apparent_daylength_hours(
            date(2022,12,21),36.85,apparent_zenith_degrees=90.0
        )
