"""Known-truth mock API metadata tests: NO biological responses, GPS or nests."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from scripts.bop_red_kite_source_inventory_v1 import (
    CONTRACT, _pinned_contract, _provider_get_exact_metadata,
    classify_zenodo_inventory,
)


def _mock():
    c=_pinned_contract()
    rec={
        "id":13736049,
        "doi":"10.5281/zenodo.13736049",
        "is_published":True,
        "metadata":{"license":{"id":"cc-by-4.0"},"version":"1.0.0"},
        "files":[
            {"key":f["key"],"checksum":"md5:"+f["md5"],"size":n+6000}
            for n,f in enumerate(c["expected_files"])
        ],
    }
    return c,rec


def test_preaccess_contract_never_authorizes_outcome_or_tracking_download():
    c=_pinned_contract()
    assert c["target_source"]["allowed_metadata_api"]=="https://zenodo.org/api/records/13736049"
    assert c["target_source"]["allow_event_or_summary_csv_download"] is False
    assert c["target_source"]["allow_file_content_download"] is False
    assert c["target_source"]["allow_altitude_or_location_access"] is False
    assert c["already_published_paper_metadata_only"]["Swiss_model_training_birds_reported"]==258
    assert c["already_published_paper_metadata_only"]["German_source_birds_meeting_minimum_800_locations"]==63
    assert c["already_published_paper_metadata_only"]["published_German_outcome_model_accuracy_already_seen"] is True
    assert c["criteria"]["biology_terminal_always"]=="HOLD_NEW_NEST_STATE_TARGET_AND_AUTHENTIC_GROUP_ROSTER_NOT_YET_FROZEN"
    assert "GER_indseasondata.csv" in [f["key"] for f in c["expected_files"]]


def test_exact_six_provider_file_manifest_gives_metadata_only_status():
    c,obj=_mock()
    out=classify_zenodo_inventory(obj,c,raw_metadata=b'{"synthetic":true}')
    assert out["source_doi"]=="10.5281/zenodo.13736049"
    assert out["file_count"]==6
    assert out["official_file_inventory_verified"] is True
    assert out["source_inventory_terminal"]=="SOURCE_FILE_INVENTORY_VERIFIED_ONLY"
    assert out["biology_terminal"]=="HOLD_NEW_NEST_STATE_TARGET_AND_AUTHENTIC_GROUP_ROSTER_NOT_YET_FROZEN"
    assert out["provider_license_id"]=="cc-by-4.0"
    assert out["read_actions"]==["EXACT_PUBLIC_ZENODO_METADATA_API_ONLY"]
    assert out["outcome_rows_accessed"] is False
    assert out["real_external_group_gain_estimated"] is False
    assert out["German_sample_roster_opened"] is False
    assert out["historical_BOP_mixed_preserved"] is True
    assert all(f["file_bytes_downloaded"] is False for f in out["declared_file_list"])
    assert not any("animal_id" in f for f in out["declared_file_list"])
    assert out["metadata_sha256"]==__import__("hashlib").sha256(b'{"synthetic":true}').hexdigest()
    json.dumps(out,ensure_ascii=False,allow_nan=False)


@pytest.mark.parametrize("problem,expected",[
    ("wrong_record","identity mismatch"),
    ("wrong_doi","not pinned"),
    ("extra_file","roster differs"),
    ("missing_file","roster differs"),
    ("wrong_md5","MD5 differs"),
    ("missing_md5","MD5 malformed"),
    ("duplicate_name","duplicated"),
    ("not_published","not explicitly published"),
    ("negative_size","file size"),
    ("unexpected_nonobject","manifest row malformed"),
])
def test_provider_changes_do_not_rescue_or_misrepresent_source(problem,expected):
    c,rec=_mock()
    if problem=="wrong_record":
        rec["id"]=13736048
    elif problem=="wrong_doi":
        rec["doi"]="10.5281/zenodo.10055071"
    elif problem=="extra_file":
        rec["files"].append({"key":"actual-height-above-msl.csv",
                             "checksum":"md5:"+"0"*32,"size":1000})
    elif problem=="missing_file":
        rec["files"].pop()
    elif problem=="wrong_md5":
        rec["files"][0]["checksum"]="md5:"+"0"*32
    elif problem=="missing_md5":
        rec["files"][0]["checksum"]=""
    elif problem=="duplicate_name":
        rec["files"].append(deepcopy(rec["files"][0]))
    elif problem=="not_published":
        rec["is_published"]=False
        rec["status"]="draft"
    elif problem=="negative_size":
        rec["files"][0]["size"]=-1
    elif problem=="unexpected_nonobject":
        rec["files"][0]=None
    with pytest.raises(ValueError,match=expected):
        classify_zenodo_inventory(rec,c,raw_metadata=b'{"synthetic":true}')


def test_provider_access_url_must_be_exactly_frozen_api_before_any_network_call():
    with pytest.raises(ValueError,match="unapproved source URL"):
        _provider_get_exact_metadata(
            "https://zenodo.org/records/13736049/files/GER_indseasondata.csv",
            500000
        )


def test_original_BOP_state_and_archived_publication_are_not_reclassified():
    c,rec=_mock()
    out=classify_zenodo_inventory(rec,c,raw_metadata=b'{"synthetic":true}')
    assert "altitude" not in out["source_inventory_terminal"]
    assert out["original_BOP_RF_altitude_validation"] is False
    assert out["old_Dryad_original_RF_gate_reopened"] is False
    assert c["original_scientific_endpoints_immutable"]["historical_BOP"]=="empirical_state_prediction_mixed"
    assert c["original_scientific_endpoints_immutable"]["Dryad"]=="NOT_ADMITTED"
    assert c["already_published_paper_metadata_only"]["source_response_axis"]=="nesting_behaviour_breeding_initiation_success_NOT_altitude"
