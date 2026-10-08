"""Known-structure tests; never read 2024 sequence observations."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from odsp.snapshot_usa_2024_structural_screen_v0 import (
    audit_deployment_bytes,
    _validate_contract,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ODSP_SNAPSHOT_USA_2024_DEPLOYMENT_SCREEN_V0_CONTRACT.json"
NAMES=[
    "Project","State","Camera_Trap_Array","Site_Name","Deployment_ID",
    "Survey_Nights","Latitude","Longitude","Habitat",
    "Development_Level","Feature_Type",
]


def _plan():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _lines(rows, headers=NAMES):
    stream=io.StringIO(newline="")
    writer=csv.writer(stream)
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _row(i, group, *, project="P", array=None, site=None, nights="40", feature="",
         state="NC", lat=None, lon=None, deploy=None):
    return [
        project,state,array or f"array-{group}-{i}",
        site or f"site-{group}-{i}",
        deploy or f"deployment-{group}-{i}",
        nights,str(35.0+i*0.01 if lat is None else lat),
        str(-80.0-i*0.01 if lon is None else lon),
        group,"rural",feature,
    ]


def _fixture():
    rows=[
        _row(i,group)
        for group in ("forest","grassland")
        for i in range(8)
    ]
    return rows


def _audit(rows, headers=NAMES):
    return audit_deployment_bytes(
        _lines(rows,headers),_plan(),
        contract_sha256=hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
    )


def test_prospective_contract_precedes_metadata_contents():
    contract=_plan()
    _validate_contract(contract)
    assert contract["status"]=="PRE_DEPLOYMENT_CSV_CONTENT_ACCESS_DESIGN_FREEZE"
    assert contract["preexisting_exposure"]["actual_deployment_csv_records_read_before_this_freeze"] is False
    assert contract["preexisting_exposure"]["complete_prior_historical_outcome_nonaccess_attested"] is False
    assert contract["gate"]["automatic_primary_route_promotion"] is False
    assert contract["published_source"]["metadata_filename"]=="ssusa_2024_deployments.csv"
    assert "Species" not in contract["allowed_columns_only"]
    assert "Start_Time" not in contract["allowed_columns_only"]


def test_stratified_site_array_counts_are_not_called_iid():
    out=_audit(_fixture())
    assert out["status"]=="STRUCTURAL_COUNTS_ONLY_UNVERIFIED_INDEPENDENCE"
    assert out["deployment_record_count"]==16
    assert out["distinct_composite_sites"]==16
    assert out["distinct_composite_arrays"]==16
    for group in ("forest","grassland"):
        g=out["predeclared_habitat_groups"][group]
        assert g["sites_after_max_deployment_nights_ge30"]==8
        assert g["distinct_arrays_after_effort_gate"]==8
    assert out["group_count_gate_met"]
    assert not out["iid_camera_site_selection_verified"]
    assert not out["iid_array_sampling_verified"]
    assert not out["full_original_source_frame_disjoint_verified"]
    assert not out["eligible_for_primary_confirmatory_route"]
    assert not out["species_taxon_or_sequence_time_values_accessed"]
    assert not out["observation_detection_outcomes_accessed"]
    assert "site-forest-0" not in json.dumps(out)
    assert "Latitude" not in json.dumps(out)


def test_repeated_deployments_of_same_site_do_not_inflate_physical_replication():
    rows=_fixture()
    repeated=_row(0,"forest",deploy="different-batch-deployment",nights="120",
                  lat=35.0,lon=-80.0)
    rows.append(repeated)
    out=_audit(rows)
    assert out["deployment_record_count"]==17
    assert out["distinct_composite_sites"]==16
    assert out["predeclared_habitat_groups"]["forest"]["sites_after_max_deployment_nights_ge30"]==8
    assert out["predeclared_habitat_groups"]["forest"]["distinct_arrays_after_effort_gate"]==8


def test_eight_camera_sites_same_array_do_not_count_as_eight_arrays():
    rows=_fixture()
    for i in range(8):
        rows[i][2]="one_shared_array"
    out=_audit(rows)
    assert out["predeclared_habitat_groups"]["forest"]["sites_after_max_deployment_nights_ge30"]==8
    assert out["predeclared_habitat_groups"]["forest"]["distinct_arrays_after_effort_gate"]==1
    assert out["group_count_gate_met"] is False
    assert out["status"]=="HOLD_INSUFFICIENT_STRUCTURAL_COUNTS"


def test_effort_floor_and_attractor_filter_do_not_move_frozen_primary_groups():
    rows=_fixture()
    rows[0][5]="29"
    rows[1][10]="near a hiking trail"
    rows[2][10]="water source"
    out=_audit(rows)
    fg=out["predeclared_habitat_groups"]["forest"]
    assert fg["sites_after_max_deployment_nights_ge30"]==7
    assert fg["sites_not_flagged_attraction_feature"]==5
    assert out["status"]=="HOLD_INSUFFICIENT_STRUCTURAL_COUNTS"


def test_missing_identity_and_ambiguous_habitat_not_counted():
    rows=_fixture()
    rows[0][3]=""
    rows[1][8]="mix of forest and grassland"
    rows[2][8]="unknown"
    out=_audit(rows)
    assert out["missing_composite_ids_rows"]==1
    assert out["sites_with_ambiguous_or_unselected_habitat"]==2
    assert out["predeclared_habitat_groups"]["forest"]["sites_after_max_deployment_nights_ge30"]==5


def test_source_with_sequence_outcome_schema_is_rejected_before_any_row_scoring():
    rows=_fixture()
    with pytest.raises(ValueError,match="response-bearing"):
        _audit([row+["lion"] for row in rows],headers=NAMES+["Species"])
    with pytest.raises(ValueError,match="response-bearing"):
        _audit([row+["2024-10-01 10:05"] for row in rows],
               headers=NAMES+["Start_Time"])


def test_missing_deployment_columns_and_garbled_csv_fail_closed():
    with pytest.raises(ValueError,match="required columns"):
        _audit([row[1:] for row in _fixture()],headers=NAMES[1:])
    with pytest.raises(ValueError,match="metadata bytes"):
        audit_deployment_bytes(b"",_plan(),contract_sha256="x")


def test_site_qualifications_do_not_count_conflicting_geolocations_as_new_sites():
    rows=_fixture()
    other=_row(0,"forest",deploy="extra",lat=45.0,lon=-72.0)
    rows.append(other)
    result=_audit(rows)
    assert result["sites_with_multiple_rounded_coordinates"]==1
    assert result["predeclared_habitat_groups"]["forest"]["sites_after_max_deployment_nights_ge30"]==7


def test_wrong_posthoc_group_or_minimum_nights_is_not_accepted():
    p=_plan()
    p["predeclared_group_definition"]["group_a"]="shrubland"
    with pytest.raises(ValueError,match="frozen structural-screen"):
        _validate_contract(p)
    p=_plan()
    p["predeclared_group_definition"]["per_site_minimum_survey_nights"]=5
    with pytest.raises(ValueError,match="frozen structural-screen"):
        _validate_contract(p)
