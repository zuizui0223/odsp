"""Post-failure diagnostic tests: invented source tables only."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp import ri_camera_v3_attrition_only_v0 as audit
from odsp.ri_solar_clock_schema_v1 import (
    DEPLOYMENT_HEADER,DETECTION_HEADER,
)

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/"RI_CAMERA_V3_ATTRITION_ONLY_CONTRACT.json").read_text())
V1=json.loads((ROOT/"RI_SOLAR_CLOCK_SCHEMA_V1_EXPLORATORY_CONTRACT.json").read_text())


def _row(cols,contents):
    return dict(zip(cols,contents))


def _tables():
    dep=[
        _row(DEPLOYMENT_HEADER,(
            "Winter2019","site-a","station-x","camera-1",
            "2019-01-02","2019-02-28","41.4","-71.5"
        ))
    ]
    det=[
        _row(DETECTION_HEADER,(
            "Winter2019","site-a","station-x","camera-1",
            "2019-02-01 12:30:00","2019-02-01","12:30:00",
            "red fox","Mammalia","Carnivora","Canidae",
            "Vulpes","vulpes","Vulpes vulpes","1"
        ))
    ]
    return dep,det


def _audit(monkeypatch,dep,det):
    monkeypatch.setattr(audit,"_member_zip_csv",lambda raw:{
        "RI_CameraSurvey_Deployments.csv":dep,
        "RI_CameraSurvey_Detections.csv":det,
    })
    return audit.inspect_source_attrition_without_ecological_scores(
        b"synthetic-archive",V1,P,
    )


def test_one_matched_event_reports_stage_counts_but_no_species_or_clock(monkeypatch):
    dep,det=_tables()
    r=_audit(monkeypatch,dep,det)
    assert r["deployment_rows"]==1
    assert r["detection_rows"]==1
    assert r["first_rejection_stage_counts"][
        "candidate_usable_raw_detection_rows"
    ]==1
    assert r["distinct_physical_primary_site_count_of_all_candidate_rows"]==1
    for flag in (
        "source_raw_species_taxa_values_exposed",
        "source_exact_photo_datetime_values_exposed",
        "source_site_station_camera_ids_exposed",
        "individual_clock_bins_or_solar_phases_computed",
        "prediction_models_fitted","ecological_gain_computed",
        "prior_terminal_v0_v1_reclassified",
    ):
        assert r[flag] is False
    text=json.dumps(r)
    assert "Vulpes vulpes" not in text
    assert "2019-02-01 12:30:00" not in text
    assert "site-a" not in text


def test_blank_time_unknown_yearseason_and_join_diagnosed_separately(monkeypatch):
    dep,det=_tables()
    unknown_year=dict(det[0])
    unknown_year["YearSeason"]="Winter.2019"
    wrong_camera=dict(det[0])
    wrong_camera["Camera.Name"]="camera-unmatched"
    invalid_date=dict(det[0])
    invalid_date["Date.Time"]="unparseable"
    det.extend([unknown_year,wrong_camera,invalid_date])
    r=_audit(monkeypatch,dep,det)
    c=r["first_rejection_stage_counts"]
    assert c["candidate_usable_raw_detection_rows"]==1
    assert c["first_reject_unknown_YearSeason_syntax"]==1
    assert c["first_reject_no_exact_deployment_join"]==1
    assert c["first_reject_unparseable_datetime"]==1
    assert r["detection_rows"]==4


def test_schema_recovered_yearseason_metadata_is_not_scored(monkeypatch):
    dep,det=_tables()
    det[0]["YearSeason"]="2019 Winter"
    result=_audit(monkeypatch,dep,det)
    assert result["first_rejection_stage_counts"][
        "first_reject_no_exact_deployment_join"
    ]==1
    assert result["detection_YearSeason_metadata_labels"]==[
        {"label":"2019 Winter","row_count":1}
    ]
    assert result["ecological_gain_computed"] is False


def test_contract_identity_fail_closed(monkeypatch):
    dep,det=_tables()
    plan=dict(P)
    plan["status"]="retuned"
    with pytest.raises(ValueError,match="unfrozen"):
        audit.inspect_source_attrition_without_ecological_scores(
            b"synthetic",V1,plan,
        )
