"""Header-only source integrity regression: synthetic column names, no CSV rows."""
from __future__ import annotations

from copy import deepcopy
import csv
import json

import pytest

from scripts.bop_red_kite_header_only_preflight_v1 import (
    CONTRACT,PRIOR,_pinned,_parse_header,_read_exact_first_physical_line,
    classify_headers,
)


def _source_headers(spec):
    headers={
        "GER_indseasondata.csv":b"year_id,id,HR,nest,success,age_cy,sex\n",
        "SUI_indseasondata.csv":b"year_id,id,HR,nest,success,age_cy,sex\n",
        "GER_trackingdata.csv":b"year_id,timestamp,long_wgs,lat_wgs,long_eea,lat_eea\n",
        "SUI_trackingdata.csv":b"year_id,timestamp,long_wgs,lat_wgs,long_eea,lat_eea\n",
    }
    assert set(headers)=={x["key"] for x in spec["authorized_header_requests"]}
    return {name:(value,206) for name,value in headers.items()}


def test_frozen_source_access_is_four_first_physical_lines_only():
    c,r=_pinned()
    assert c["frozen_date"]=="2026-10-28"
    assert c["technical_access"]["send_HTTP_Range"]=="bytes=0-4095"
    assert c["technical_access"]["max_header_bytes_per_file"]==4096
    assert c["technical_access"]["never_read_GPS_event_rows"] is True
    assert c["technical_access"]["never_read_NestTool_individual_season_data_rows"] is True
    assert c["technical_access"]["no_complete_content_MD5_reattestation"] is True
    assert c["predeclared_interpretation"]["publication_already_used_German_external_outcomes"] is True
    assert r["initial_verified_actions"]["workflow_artifact_id"]==12792739938
    assert r["scientific_terminal"]["biological"]=="HOLD_NEW_NEST_STATE_TARGET_AND_AUTHENTIC_GROUP_ROSTER_NOT_YET_FROZEN"
    assert len(c["authorized_header_requests"])==4


def test_header_recording_never_exposes_individual_rows_or_outcome_values():
    c,prior=_pinned()
    out=classify_headers(_source_headers(c),c,prior)
    assert out["file_count"]==4
    assert out["all_four_sources_have_year_id"] is True
    assert out["individual_season_headers_have_candidate_animal_key"] is True
    assert out["structural_header_status"]=="SOURCE_HEADERS_RECORDED_NO_FULL_DATA_ACCESS"
    assert out["scientific_terminal"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    assert out["source_role"]=="OBSERVED_CSV_HEADERS_ONLY_NO_RESPONSES"
    assert out["outcome_values_parsed"] is False
    assert out["GPS_event_values_parsed"] is False
    assert out["source_file_content_MD5_verified"] is False
    assert out["per_animal_source_counts_verified"] is False
    assert out["real_external_probability_gain_scored"] is False
    assert out["published_German_bird_count_63_admitted"] is False
    assert all(x["source_full_content_MD5_verified"] is False for x in out["header_fields"])
    assert all(x["GPS_or_breeding_outcome_row_parsed"] is False for x in out["header_fields"])
    assert [x["file"] for x in out["header_fields"]]==[
        "GER_indseasondata.csv","SUI_indseasondata.csv",
        "GER_trackingdata.csv","SUI_trackingdata.csv"
    ]
    assert "nest" in out["header_fields"][0]["candidate_outcome_field_names_only"]
    assert "id" in out["header_fields"][0]["candidate_animal_ID_field_aliases"]
    payload=json.dumps(out,sort_keys=True)
    assert "actual_bird_123" not in payload
    assert "GPS,longitude" not in payload


def test_missing_canonical_animal_field_requires_source_schema_hold_not_pooled_seasons():
    c,prior=_pinned()
    items=_source_headers(c)
    items["GER_indseasondata.csv"]=(b"year_id,nest,success\n",206)
    out=classify_headers(items,c,prior)
    assert out["individual_season_headers_have_candidate_animal_key"] is False
    assert out["structural_header_status"]=="HOLD_MISSING_YEAR_OR_ANIMAL_IDENTIFIER_SCHEMA"
    assert out["published_German_bird_count_63_admitted"] is False


def test_missing_season_link_key_requires_hold():
    c,prior=_pinned()
    items=_source_headers(c)
    items["SUI_trackingdata.csv"]=(b"timestamp,lat_wgs,long_wgs\n",206)
    out=classify_headers(items,c,prior)
    assert out["all_four_sources_have_year_id"] is False
    assert out["structural_header_status"]=="HOLD_MISSING_YEAR_OR_ANIMAL_IDENTIFIER_SCHEMA"


@pytest.mark.parametrize("raw",[
    b"\n",b",year_id,nest\n",b"id,id,year_id\n",
    b" year_id,id,nest\n",b"year_id,id,nest\nextra_row,YES,YES\n",
    b"\x00\x01year_id,id,nest\n",
])
def test_malformed_physical_header_never_becomes_original_outcome_result(raw):
    with pytest.raises((ValueError,csv.Error)):
        _parse_header(raw)


def test_never_fetch_unpinned_GPS_or_metadata_csv():
    with pytest.raises(ValueError,match="not an authorized header-only source URL"):
        _read_exact_first_physical_line(
            "https://zenodo.org/records/13736049/files/SUI_trackingdata.csv?download=0",
            "SUI_trackingdata.csv",4096
        )


def test_cross_source_extra_file_and_header_length_tampering_rejected():
    c,prior=_pinned()
    items=_source_headers(c)
    items["extra_indseason.csv"]=(b"year_id,id,nest\n",206)
    with pytest.raises(ValueError,match="exact four"):
        classify_headers(items,c,prior)
    items=_source_headers(c)
    items["GER_indseasondata.csv"]=(b"year_id,id,nest,"+b"x"*4098+b"\n",206)
    with pytest.raises(ValueError,match="header source exceeded"):
        classify_headers(items,c,prior)


def test_frozen_ancestor_source_metadata_remains_first_provider_inventory():
    c,p=_pinned()
    assert c["upstream"]["source_doi"]==p["source_manifest_observation"]["source_doi"]
    assert c["upstream"]["file_manifest_MD5s_only_not_data_content_verified"] is True
    assert p["scientific_terminal"]["historical_BOP"]=="empirical_state_prediction_mixed"
    assert p["scientific_terminal"]["external_real_German_sample_admitted"] is False
