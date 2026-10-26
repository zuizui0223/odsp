from __future__ import annotations

import csv
import io
import json
import urllib.error
from pathlib import Path

import pytest

from scripts.bop_dryad_external_schema_preflight_v1 import (
    CONTRACT, ORIGINAL_BOP, EXPECTED_DATADRYAD_API,
    EXPECTED_DOI, _parse_small_non_gps_file,
    _safe_source_attempt, _strict_official_url,
    feature_compatibility, load_contract, run_preflight,
)


def test_pinned_source_schema_finds_true_original_RF_incompatibility():
    contract=load_contract()
    original=json.loads(ORIGINAL_BOP.read_text(encoding="utf-8"))
    result=feature_compatibility(contract,original)
    assert result["original_bop_rf_direct_external_scoring_admissible"] is False
    assert result["documented_missing_required_features"]==["external-temperature"]
    assert result["precision_changed_features"]==["location-lat","location-long"]
    assert result["source_column_correspondences"]["height-above-msl"] == (
        "raw_AMSL_data_1a_only_no_outcome_opened"
    )
    assert result["original_RF_rerun_performed"] is False
    assert result["schema_only_not_verified_against_raw_GPS_header"] is True
    assert contract["candidate"]["readme_public_metadata"]["data_1a_distinct_individuals"]==271
    assert contract["candidate"]["readme_public_metadata"]["dataset_total_tagged_individuals"]==280


def _fake_provider():
    calls=[]
    def fetch(url,max_bytes,*,small_id=None):
        calls.append((url,small_id))
        if url==EXPECTED_DATADRYAD_API:
            return json.dumps({"identifier":"doi:"+EXPECTED_DOI,
                               "license":"CC0-1.0","_links":{}}).encode()
        if url==EXPECTED_DATADRYAD_API+"/versions":
            return json.dumps({"count":1,"_embedded":{"stash:versions":[]}}).encode()
        if small_id==4917192:
            return b"# Metadata only\nData_1a\nData_2a\n"
        if small_id==4917158:
            return (
                b"bb_name_2,lat_min,lat_max,long_min,long_max\n"
                b"Fictitious_A,0,1,2,3\nFictitious_B,4,5,6,7\n"
            )
        if small_id==4917159:
            return (
                b"individual.global.identifier,year,nest_ID\n"
                b"private-001,2020,1\nprivate-001,2021,1\n"
                b"private-002,2022,1\n"
            )
        raise AssertionError("unexpected/forbidden provider URL")
    return fetch,calls


def test_only_whitelisted_metadata_and_non_gps_sidecars_are_requested():
    fake,calls=_fake_provider()
    report=run_preflight(fetcher=fake)
    assert report["candidate_admission"]=="NOT_ADMITTED"
    assert report["metadata_source_status"]=="AT_LEAST_ONE_OFFICIAL_SOURCE_READ"
    assert report["official_metadata_api"]["dataset"]["status"]=="SOURCE_READ"
    assert report["official_metadata_api"]["dataset"]["explicit_provider_license"]=="CC0-1.0"
    assert report["feature_compatibility"]["original_bop_rf_direct_external_scoring_admissible"] is False
    assert len(calls)==5
    assert all("Data_1a.csv" not in url and "Data_2a.csv" not in url for url,_ in calls)
    assert {file_id for _,file_id in calls if file_id is not None}=={4917192,4917158,4917159}
    assert report["raw_gps_or_height_outcomes_accessed"] is False
    assert report["BOP_existing_mixed_terminal_reclassified"] is False
    assert report["BOP_2026_same_study_count_gate_reopened"] is False
    assert report["small_non_gps_file_checks"]["Study_areas_bounding_boxes.csv"]["parsed_non_gps"]["distinct_study_area_labels"]==2
    assert report["small_non_gps_file_checks"]["Complete_succesful_breeding_seasons.csv"]["parsed_non_gps"]["subset_distinct_individual_ids"]==2
    assert "private-001" not in json.dumps(report)
    assert "Fictitious_A" not in json.dumps(report)
    assert report["documented_common_BOP_taxa_total"]==217
    json.dumps(report,allow_nan=False)


def test_official_http_403_is_source_hold_not_a_new_data_discovery():
    called=[]
    def forbid(url,max_bytes,*,small_id=None):
        called.append(url)
        raise urllib.error.HTTPError(url,403,"Forbidden",{},None)
    report=run_preflight(fetcher=forbid)
    assert len(called)==5
    assert report["metadata_source_status"]=="OFFICIAL_METADATA_SOURCE_HOLD"
    assert all(s["status"]=="SOURCE_HOLD" for s in report["official_metadata_api"].values())
    assert all(v["error_code"]=="HTTP_403" for v in report["small_non_gps_file_checks"].values())
    assert report["candidate_admission"]=="NOT_ADMITTED"
    assert report["original_BOP_RF_direct_external_transfer_status"]=="ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"


@pytest.mark.parametrize("url,small_id",[
    ("https://another.site/api/v2/datasets/doi",None),
    ("http://datadryad.org/api/v2/datasets/doi",None),
    ("https://datadryad.org/downloads/file_stream/4917190",4917190),
    ("https://datadryad.org/downloads/file_stream/4917192",4917158),
    ("https://datadryad.org/api/v2/datasets/anything-else",None),
])
def test_strict_source_allowlist_rejects_any_data_file_or_origin_substitution(url,small_id):
    with pytest.raises(ValueError,match="only|GPS/source-data"):
        _strict_official_url(url,small_id=small_id)


def test_injected_fetcher_does_not_bypass_no_GPS_allowlist():
    called=[]
    def reader(url,limit,*,small_id=None):
        called.append(url)
        return b"GPS data"
    with pytest.raises(ValueError):
        _safe_source_attempt(
            "https://datadryad.org/downloads/file_stream/4917190",
            4096,small_id=4917190,fetcher=reader)
    assert called==[]


def test_breeding_sidecar_subset_is_never_the_whole_animal_roster():
    result=_parse_small_non_gps_file(
        "Complete_succesful_breeding_seasons.csv",
        b"individual.global.identifier,year,nest_ID\nidA,2021,1\nidA,2022,2\nidB,2022,1\n")
    assert result["subset_rows"]==3
    assert result["subset_distinct_individual_ids"]==2
    assert result["not_whole_dataset_roster"] is True
    assert result["not_proof_of_BOP_independence"] is True


@pytest.mark.parametrize("path_key",["candidate","crosswalk","sidecar"])
def test_mutated_scientific_frozen_contract_fails_closed(tmp_path:Path,path_key):
    old=load_contract()
    content=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if path_key=="candidate":
        content["candidate"]["api_dataset_url"]="https://otherhost.invalid/data"
    elif path_key=="crosswalk":
        content["frozen_feature_crosswalk"][3]["condition"]="supported"
    else:
        content["candidate"]["expected_files"][0]["file_stream_id"]=4917190
    p=tmp_path/"mutated.json"
    p.write_text(json.dumps(content),encoding="utf-8")
    if path_key=="crosswalk":
        mutation=load_contract(p)
        with pytest.raises(ValueError,match="missing required original BOP"):
            feature_compatibility(mutation,json.loads(ORIGINAL_BOP.read_text()))
    else:
        with pytest.raises(ValueError,match="contract selection"):
            load_contract(p)


def test_invalid_Dryad_schema_not_silently_promoted():
    contract=load_contract()
    original=json.loads(ORIGINAL_BOP.read_text(encoding="utf-8"))
    altered={**original,"contract_id":"prospective_new_RF"}
    with pytest.raises(ValueError,match="historical BOP"):
        feature_compatibility(contract,altered)
    changed=json.loads(CONTRACT.read_text())
    changed["dryad_data_1a_documented_columns"].remove("height.above.msl")
    with pytest.raises(ValueError,match="absent"):
        feature_compatibility(changed,original)
