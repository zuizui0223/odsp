"""Pre-result synthetic checks for calendar-span structural screen v1.

No real deployment records or animal detections are used.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from odsp.snapshot_usa_2024_calendar_span_v1 import (
    SCREEN_ID,
    audit_calendar_metadata,
    validate_calendar_screen_contract,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ODSP_SNAPSHOT_USA_2024_CALENDAR_SPAN_V1_CONTRACT.json"
HEADERS=[
    "Project","State","Camera_Trap_Array","Site_Name","Deployment_ID",
    "Start_Date","End_Date","Habitat","Development_Level","Feature_Type",
    "Latitude","Longitude","Survey_Nights",
]


def _plan():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _csv(rows, *, header=HEADERS):
    handle=io.StringIO(newline="")
    writer=csv.writer(handle)
    writer.writerow(header)
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def _row(i, habitat, *, project="P", array=None, site=None,
         deployment=None, start="2024-09-01", end="2024-10-01",
         lat=None, lon=None, nights="30", feature="", state="WI"):
    return [
        project,state,array or f"array-{habitat}-{i:03d}",
        site or f"site-{habitat}-{i:03d}",
        deployment or f"deployment-{habitat}-{i:03d}",
        start,end,habitat,"rural",feature,
        str(42.+i*.01 if lat is None else lat),
        str(-89.-i*.01 if lon is None else lon),
        nights,
    ]


def _fixture():
    return [_row(i,g) for g in ("forest","grassland") for i in range(8)]


def _audit(rows, *, header=HEADERS):
    return audit_calendar_metadata(
        _csv(rows,header=header),_plan(),
        contract_sha256=hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
    )


def test_predeclared_new_version_does_not_inherit_old_image_effort_rule():
    plan=_plan()
    validate_calendar_screen_contract(plan)
    assert plan["contract_id"]==SCREEN_ID
    assert plan["relationship"]["new_separate_route"]
    assert plan["relationship"]["v0_selection_or_results_modified"] is False
    assert "Survey_Nights" not in plan["outcome_independent_input_only"]
    assert "Start_Date" in plan["outcome_independent_input_only"]
    assert "End_Date" in plan["outcome_independent_input_only"]
    assert plan["prior_exposure_and_claim_ceiling"]["installation_interval_is_camera_uptime_or_detection_effort"] is False
    assert plan["primary_confirmatory_qualified"] is False


def test_two_eligible_groups_are_only_candidate_site_array_counts():
    outcome=_audit(_fixture())
    assert outcome["structural_status"]=="CALENDAR_SPAN_STRUCTURAL_COUNTS_UNVERIFIED_IID"
    assert outcome["group_count_gate_met"] is True
    assert outcome["deployment_row_count"]==16
    assert outcome["distinct_site_count"]==16
    assert outcome["distinct_array_count"]==16
    for group in ("forest","grassland"):
        assert outcome["predeclared_groups"][group]["sites_with_one_calendar_interval_ge30"]==8
        assert outcome["predeclared_groups"][group]["distinct_arrays"]==8
    assert outcome["source_sequence_csv_accessed"] is False
    assert outcome["source_survey_nights_image_derived_column_read"] is False
    assert outcome["true_active_camera_effort_verified"] is False
    assert outcome["sites_iid_verified"] is False
    assert outcome["primary_confirmatory_qualified"] is False
    assert outcome["precise_camera_coordinates_or_site_ids_in_output"] is False
    raw=json.dumps(outcome,allow_nan=False)
    assert "site-grassland-000" not in raw
    assert "Latitude" not in raw


def test_image_derived_survey_nights_and_extra_non_allowed_columns_cannot_change_selection():
    rows=_fixture()
    before=_audit(rows)
    for row in rows:
        row[-1]="0"
    after=_audit(rows)
    for key in ("predeclared_groups","group_count_gate_met","distinct_site_count","distinct_array_count"):
        assert before[key]==after[key]
    assert before["deployment_csv_sha256"] != after["deployment_csv_sha256"]


def test_placement_retrieval_difference_is_calendar_not_actual_camera_uptime():
    rows=_fixture()
    rows[0][6]="2024-09-30"   # 29 days
    rows[1][6]="2024-10-01"   # 30 days
    rows[2][6]="2024-10-02"   # 31 days
    out=_audit(rows)
    assert out["predeclared_groups"]["forest"]["sites_with_one_calendar_interval_ge30"]==7
    assert out["true_active_camera_effort_verified"] is False
    assert out["structural_status"]=="HOLD_CALENDAR_SPAN_STRUCTURE_INSUFFICIENT"


def test_two_deployments_at_one_site_count_once_without_summing():
    rows=_fixture()
    rows[0][6]="2024-09-20"  # 19 calendar nights
    rows.append(_row(0,"forest",deployment="extra-uploaded-batch",
                     start="2024-09-20",end="2024-10-03",nights="111"))
    out=_audit(rows)
    assert out["deployment_row_count"]==17
    assert out["distinct_site_count"]==16
    assert out["predeclared_groups"]["forest"]["sites_with_one_calendar_interval_ge30"]==7
    assert out["group_count_gate_met"] is False


def test_duplicate_deployment_id_at_distinct_sites_invalidates_both():
    rows=_fixture()
    rows[1][4]=rows[0][4]
    out=_audit(rows)
    assert out["conflicted_deployment_ids"]==1
    assert out["sites_containing_conflicted_deployment_ids"]==2
    assert out["predeclared_groups"]["forest"]["sites_with_one_calendar_interval_ge30"]==6


def test_many_sites_in_one_array_not_mistaken_for_independent_arrays():
    rows=_fixture()
    for i in range(8):
        rows[i][2]="forest-shared-array"
    out=_audit(rows)
    assert out["predeclared_groups"]["forest"]["sites_with_one_calendar_interval_ge30"]==8
    assert out["predeclared_groups"]["forest"]["distinct_arrays"]==1
    assert out["group_count_gate_met"] is False


def test_calendar_date_habitat_and_coordinate_metadata_fail_closed():
    rows=_fixture()
    rows[0][5]="2024-11-30"
    rows[0][6]="2024-11-01"
    rows[1][5]="bad"
    rows[2][7]="forest and grassland"
    rows[3][10]="999"
    rows[4][6]="2024-09-29"  # 28 nights
    out=_audit(rows)
    assert out["invalid_placement_retrieval_date_row_count"]==2
    assert out["sites_with_ambiguous_habitat"]>=1
    assert out["sites_with_any_invalid_coordinates"]>=1
    assert out["predeclared_groups"]["forest"]["sites_with_one_calendar_interval_ge30"]==3


def test_two_geographies_for_the_same_site_exclude_it():
    rows=_fixture()
    rows.append(_row(0,"forest",deployment="extra-valid-deployment",
                     lat=46.,lon=-71.))
    out=_audit(rows)
    assert out["distinct_site_count"]==16
    assert out["sites_with_ambiguous_coordinates"]==1
    assert out["predeclared_groups"]["forest"]["sites_with_one_calendar_interval_ge30"]==7


def test_secondary_camera_feature_filter_does_not_change_primary_count():
    rows=_fixture()
    rows[0][9]="on a hiking trail"
    rows[1][9]="water source"
    out=_audit(rows)
    forest=out["predeclared_groups"]["forest"]
    assert forest["sites_with_one_calendar_interval_ge30"]==8
    assert forest["secondary_no_trail_road_water_bait_sites"]==6
    assert out["group_count_gate_met"] is True


def test_sequence_response_columns_and_missing_required_dates_are_rejected():
    rows=_fixture()
    with pytest.raises(ValueError,match="response/timestamp"):
        _audit([row+["bear"] for row in rows],header=HEADERS+["Species"])
    with pytest.raises(ValueError,match="response/timestamp"):
        _audit([row+["13:12:01"] for row in rows],header=HEADERS+["Start_Time"])
    with pytest.raises(ValueError,match="missing frozen required"):
        _audit([row[:6]+row[7:] for row in rows],
               header=HEADERS[:6]+HEADERS[7:])


def test_contract_metadata_rule_not_adjustable_after_screen():
    p=_plan()
    p["habitat_groups"]["minimum_calendar_span_nights"]=10
    with pytest.raises(ValueError,match="frozen calendar-span"):
        validate_calendar_screen_contract(p)
    p=_plan()
    p["outcome_independent_input_only"].append("Survey_Nights")
    with pytest.raises(ValueError,match="allowed deployment-only"):
        validate_calendar_screen_contract(p)
