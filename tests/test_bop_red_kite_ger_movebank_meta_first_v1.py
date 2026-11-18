"""Check original HTTPError source HOLD immutability without any HTTP access."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.verify_bop_red_kite_ger_movebank_meta_first_v1 import CONTRACT,RECEIPT,verify_first

def originals():
    return json.loads(RECEIPT.read_text(encoding="utf-8")),json.loads(CONTRACT.read_text(encoding="utf-8"))

def test_original_first_access_hold_is_reproducible_without_provider_recontact():
    r,c=originals()
    x=verify_first(r,c)
    assert x["first_source_result_verified_offline"] is True
    assert x["status"]=="STUDY_METADATA_ACCESS_HOLD"
    assert x["reason"]=="HTTPError_STATUS_CODE_NOT_CAPTURED"
    assert x["first_actions_run_id"]==44299216766
    assert x["first_actions_artifact_id"]==14425263270
    assert x["original_2024_99_63_verified"] is False
    assert x["previous_Zenodo_99_49_unchanged"] is True
    assert x["provider_recontacted"] is False

@pytest.mark.parametrize("path,value",[
    (("original_actions","original_JSON_sha256"),"0"*64),
    (("original_actions","first_actions_artifact_ZIP_sha256"),"0"*64),
    (("original_actions","offline_python_safety_versions_success"),["3.12"]),
    (("observed_first_source_result","no_provider_current_individual_count_verified"),False),
    (("observed_first_source_result","status"),"CURRENT_MOVEBANK_STUDY_METADATA_ONLY"),
    (("observed_first_source_result","original_2024_163_65_roster_verified"),True),
    (("scientific_limits","HTTPError_does_not_establish_permission_denial_vs_other_server_error"),False),
    (("scientific_limits","no_second_url_retry_or_credentials_in_followup_CI"),False),
    (("scientific_limits","current_Movebank_count_unavailable"),False),
    (("scientific_limits","redkite_biological_terminal"),"GENERALIZING"),
    (("first_original_source_output","error_type"),"None"),
])
def test_unfounded_success_or_source_provenance_mutation_fails(path,value):
    r,c=originals()
    obj=deepcopy(r)
    cur=obj
    for k in path[:-1]:
        cur=cur[k]
    cur[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(obj,c)

def test_fake_source_data_cannot_replace_original_fail_result():
    r,c=originals()
    with pytest.raises(ValueError,match="differs"):
        verify_first(r,c,raw=b'{"status":"CURRENT_MOVEBANK_STUDY_METADATA_ONLY"}\n')
