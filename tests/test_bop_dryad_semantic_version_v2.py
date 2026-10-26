from __future__ import annotations

import copy
import json

import pytest

from scripts.bop_dryad_semantic_version_v2 import (
    DATASET_URL,VERSIONS_URL,_check_url,load_contract,
    parse_file_inventory,run_v2,semantic_fingerprint,
    semantic_version_identity,
)


def _fixture():
    return {
        "identifier":"doi:10.5061/dryad.n8pk0p398",
        "license":"https://spdx.org/licenses/CC0-1.0.html",
        "curationStatus":"Published",
        "versionNumber":3,
        "publicationDate":"2026-08-17",
        "lastModificationDate":"2026-10-26",
        "downloadCount":123,
        "_links":{"stash:version":{"href":"/api/v2/versions/820101"}}
    },{
        "total":2,"count":2,
        "_embedded":{"stash:versions":[
            {"versionNumber":2,"publicationDate":"2026-01-01",
             "curationStatus":"Published",
             "_links":{"self":{"href":"/api/v2/versions/819990"}},
             "lastModificationDate":"2026-02-01","downloadCount":13},
            {"versionNumber":3,"publicationDate":"2026-08-17",
             "curationStatus":"Published",
             "_links":{"self":{"href":"/api/v2/versions/820101"}},
             "lastModificationDate":"2026-10-26","downloadCount":500},
        ]}
    },{
        "total":5,"count":5,
        "_embedded":{"stash:files":[
            {"path":"README.md","size":8100,"downloadCount":40},
            {"path":"Study_areas_bounding_boxes.csv","size":564},
            {"path":"Complete_succesful_breeding_seasons.csv","size":6090},
            {"path":"Data_1a.csv","size":888160000},
            {"path":"Data_2a.csv","size":2160000000},
        ]}
    }


def _fetcher(dataset,versions,files):
    observed=[]
    def read(url,*,max_bytes=131072,latest_version_id=None):
        observed.append((url,latest_version_id))
        if url==DATASET_URL:return copy.deepcopy(dataset)
        if url==VERSIONS_URL:return copy.deepcopy(versions)
        if url=="https://datadryad.org/api/v2/versions/820101/files?per_page=100":
            assert latest_version_id==820101
            return copy.deepcopy(files)
        raise AssertionError("forbidden network route / GPS file read")
    return read,observed


def test_semantic_version_identity_ignores_byte_level_volatile_fields():
    ds,vs,files=_fixture()
    contract=load_contract()
    a=semantic_version_identity(ds,vs,contract)
    fp=semantic_fingerprint(a,parse_file_inventory(files,820101))
    assert a["doi"]=="doi:10.5061/dryad.n8pk0p398"
    assert a["published_version_id"]==820101
    assert len(fp)==64
    changed=copy.deepcopy((ds,vs,files))
    changed_ds,changed_vs,changed_files=changed
    changed_ds["lastModificationDate"]="2027-12-30"
    changed_ds["downloadCount"]=999999
    changed_vs["_embedded"]["stash:versions"][-1]["downloadCount"]=12345678
    changed_vs["count"]=208
    changed_files["_embedded"]["stash:files"][0]["downloadCount"]=9000000
    b=semantic_version_identity(changed_ds,changed_vs,contract)
    assert semantic_fingerprint(b,parse_file_inventory(changed_files,820101))==fp
    changed_files["_embedded"]["stash:files"][0]["size"]=9000
    assert semantic_fingerprint(b,parse_file_inventory(changed_files,820101))!=fp


def test_prospective_known_truth_v2_full_source_only_path():
    ds,vs,files=_fixture()
    read,calls=_fetcher(ds,vs,files)
    out=run_v2(fetcher=read)
    assert out["source_status"]=="SEMANTIC_METADATA_VERSION_VERIFIED_ONLY"
    assert out["external_candidate_admitted"] is False
    assert out["original_BOP_RF_directly_usable"] is False
    assert out["historical_BOP"]=="empirical_state_prediction_mixed"
    assert out["historical_90pct_new_animal_coverage_inferred"] is False
    assert out["v1_replay_raw_metadata_drift_not_erased"] is True
    assert out["raw_GPS_event_data_downloaded"] is False
    assert out["stable_published_version"]["published_version_id"]==820101
    assert {r["name"] for r in out["file_inventory"]}=={
        "README.md","Study_areas_bounding_boxes.csv",
        "Complete_succesful_breeding_seasons.csv","Data_1a.csv","Data_2a.csv"
    }
    assert len(calls)==3
    assert all("/download" not in u and "/file_stream" not in u for u,_ in calls)
    assert len(out["semantic_fingerprint_sha256"])==64


@pytest.mark.parametrize("malformed,expected",[
    ("wrong_Dryad_DOI","DOI disagrees"),
    ("changed_license","license has changed"),
    ("retracted","publication-qualified"),
    ("unpublished_version","nonpublished state"),
    ("wrong_version_order","roster order"),
    ("latest_link_mismatch","latest-version link"),
    ("publication_changed","publication date"),
])
def test_semantic_version_identity_fails_on_material_change(malformed,expected):
    ds,vs,files=_fixture()
    if malformed=="wrong_Dryad_DOI":
        ds["identifier"]="doi:10.5061/dryad.invalid"
    elif malformed=="changed_license":
        ds["license"]="proprietary"
    elif malformed=="retracted":
        ds["curationStatus"]="Withdrawn"
    elif malformed=="unpublished_version":
        vs["_embedded"]["stash:versions"][-1]["curationStatus"]="Processing"
    elif malformed=="wrong_version_order":
        vs["_embedded"]["stash:versions"].reverse()
    elif malformed=="latest_link_mismatch":
        ds["_links"]["stash:version"]["href"]="/api/v2/versions/819990"
    elif malformed=="publication_changed":
        ds["publicationDate"]="2026-08-18"
    with pytest.raises(ValueError,match=expected):
        semantic_version_identity(ds,vs,load_contract())


@pytest.mark.parametrize("case,expected",[
    ("missing_file","file list"),
    ("duplicate_file","duplicate provider"),
    ("unexpected_file","path or size"),
    ("file_no_size","path or size"),
])
def test_file_inventory_no_GPS_file_download_or_missing_file_rescue(case,expected):
    ds,vs,files=_fixture()
    entries=files["_embedded"]["stash:files"]
    if case=="missing_file":
        entries.pop()
        files["total"]=4
    elif case=="duplicate_file":
        entries[-1]["path"]="README.md"
    elif case=="unexpected_file":
        entries[-1]["path"]="new_alternative_GPS.csv"
    elif case=="file_no_size":
        entries[-1].pop("size")
    with pytest.raises(ValueError,match=expected):
        parse_file_inventory(files,820101)


def test_only_frozen_dataset_versions_and_derived_inventory_api_permitted():
    _check_url(DATASET_URL)
    _check_url(VERSIONS_URL)
    _check_url("https://datadryad.org/api/v2/versions/820101/files?per_page=100",latest_version_id=820101)
    for url in [
        "https://datadryad.org/api/v2/versions/820101/download",
        "https://datadryad.org/downloads/file_stream/4917190",
        "https://datadryad.org/api/v2/versions/820102/files?per_page=100",
        "https://bad.host/api/v2/datasets/doi",
    ]:
        with pytest.raises(ValueError):
            _check_url(url,latest_version_id=820101)


def test_no_response_is_fail_closed_and_does_not_promote_external_sample():
    ds,vs,files=_fixture()
    def unavailable(url,**kwargs):
        raise TimeoutError("official public API unavailable")
    out=run_v2(fetcher=unavailable)
    assert out["source_status"]=="API_UNAVAILABLE"
    assert out["external_candidate_admitted"] is False
    assert out["raw_GPS_event_data_downloaded"] is False


def test_source_gets_distinct_hold_on_file_inventory_403():
    ds,vs,files=_fixture()
    def fail_files(url,**kwargs):
        if url==DATASET_URL:return ds
        if url==VERSIONS_URL:return vs
        raise PermissionError("403")
    out=run_v2(fetcher=fail_files)
    assert out["source_status"]=="FILE_INVENTORY_UNAVAILABLE"
    assert out["stable_published_version"]["published_version_id"]==820101
    assert out["external_candidate_admitted"] is False


def test_frozen_contract_retains_v1_sha_drift_history():
    c=load_contract()
    h=c["historical_first_result_unchanged"]
    assert h["original_source_only_run"]==40275944700
    assert h["observed_v1_replay_failure"]=="versions_endpoint_raw_bytes_not_identical"
    assert h["no_reinterpretation_of_historical_v1_replay_failure"] is True
    assert c["source"]["no_GPS_or_file_stream_access"] is True
