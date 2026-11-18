"""Immutable first official Zenodo 2024 code package parity receipt."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.verify_bop_red_kite_2024_package_code_first_v1 import (
    RECEIPT, CONTRACT, verify,
)

def originals():
    return (json.loads(RECEIPT.read_text(encoding="utf-8")),
            json.loads(CONTRACT.read_text(encoding="utf-8")))

def test_first_code_package_provenance_and_author_script_line_corrected():
    receipt, contract=originals()
    result=verify(receipt,contract)
    assert result["first_run"]==44288291609
    assert result["R_data_prep_byte_identical_to_prepublication_GitHub"] is True
    assert result["unfiltered_bird_count_original_script_line"]==501
    assert result["all_13_R_source_files_compared"] is False
    assert result["upstream_60min_method_known"] is False
    assert result["red_kite_real_biological_prediction_gain"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"

@pytest.mark.parametrize("path,value",[
    (("first_actions","workflow_run_id"),0),
    (("first_actions","original_JSON_sha256"),"0"*64),
    (("first_actions","original_artifact_ZIP_sha256"),"0"*64),
    (("first_actions","frozen_contract_sha256"),"0"*64),
    (("original_archived_provider","R_source_member_count"),14),
    (("original_archived_provider","code_ZIP_provider_MD5_verified"),False),
    (("original_archived_provider","archived_script_sha256"),"0"*64),
    (("code_parity","historical_reference_git_blob_sha1"),"0"*40),
    (("code_parity","exact_byte_equal"),False),
    (("code_parity","archived_script_unfiltered_count_expression_line"),486),
    (("code_parity","all_13_R_file_parity_checked"),True),
    (("code_parity","upstream_60min_resampling_code_found"),True),
    (("scientific_limit","author_counting_error_not_confirmed"),False),
    (("scientific_limit","no_GPS_CSV_or_breeding_labels_accessed_in_this_route"),False),
])
def test_source_code_or_scientific_claim_mutations_fail_closed(path,value):
    receipt,contract=originals()
    bad=deepcopy(receipt)
    node=bad
    for k in path[:-1]:
        node=node[k]
    node[path[-1]]=value
    with pytest.raises(ValueError):
        verify(bad,contract)

def test_fake_rerun_cannot_reclassify_original_code_package():
    r,c=originals()
    with pytest.raises(ValueError,match="not byte-identical"):
        verify(r,c,raw=b'{"status":"PACKAGE_CODE_EXACT_GIT_MATCH"}\n')

def test_first_receipt_has_only_code_digests_not_tracked_data():
    r,_=originals()
    assert r["scientific_limit"]["prior_frozen_German_source_after_primary_GPS"]=="99 season-ID strings / 49 bird-ID strings"
    assert r["original_archived_provider"]["R_source_member_count"]==13
    assert r["code_parity"]["prior_source_count_audit_line_486_needs_correction"] is True
