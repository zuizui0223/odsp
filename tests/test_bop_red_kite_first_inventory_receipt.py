"""Evidence lock for first, response-free red-kite Zenodo metadata verification."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.verify_bop_red_kite_source_inventory_v1 import (
    CONTRACT,RECEIPT,verify_first_source_only,
)


def _first_summary():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    r=json.loads(RECEIPT.read_text(encoding="utf-8"))
    first=r["initial_verified_actions"]
    manifest=r["source_manifest_observation"]
    out={
        "schema_version":1,
        "source_doi":manifest["source_doi"],
        "record_id":manifest["source_record_id"],
        "published":True,
        "provider_license_id":manifest["provider_license_id"],
        "metadata_version":manifest["manifest_version_string"],
        "metadata_sha256":first["raw_official_metadata_sha256"],
        "file_count":manifest["source_file_count"],
        "official_file_inventory_verified":True,
        "declared_file_list":[
            {
                "key":f["key"],
                "manifest_md5":f["md5"],
                "provider_size_bytes":f["bytes"],
                "role":next(
                    v["role"] for v in c["expected_files"] if v["key"]==f["key"]
                ),
                "file_bytes_downloaded":False,
            }
            for f in manifest["manifest"]
        ],
        "total_provider_file_bytes":manifest["total_manifest_bytes"],
        "read_actions":["EXACT_PUBLIC_ZENODO_METADATA_API_ONLY"],
        "source_inventory_terminal":"SOURCE_FILE_INVENTORY_VERIFIED_ONLY",
        "biology_terminal":r["scientific_terminal"]["biological"],
        "outcome_rows_accessed":False,
        "historical_BOP_mixed_preserved":True,
        "original_BOP_RF_altitude_validation":False,
        "German_sample_roster_opened":False,
        "published_sample_count_not_validated_against_files":True,
        "real_external_group_gain_estimated":False,
        "old_Dryad_original_RF_gate_reopened":False,
    }
    return out,r,c


def test_first_source_inventory_exactly_pinned_to_md5_manifest_and_licence():
    summary,receipt,contract=_first_summary()
    status=verify_first_source_only(summary,receipt,contract)
    assert status["first_metadata_result_verified"] is True
    assert status["original_workflow"]==40636304599
    assert status["pinned_manifest_files"]==6
    assert status["license"]=="cc-by-4.0"
    assert status["source_inventory_status"]=="SOURCE_FILE_INVENTORY_VERIFIED_ONLY"
    assert status["nest_state_biology_status"].startswith("HOLD_")
    assert status["data_files_or_GPS_accessed"] is False
    assert status["new_empirical_prediction_scored"] is False
    assert receipt["initial_verified_actions"]["workflow_artifact_id"]==12792739938
    assert receipt["initial_verified_actions"]["first_result_bytes"]==2403
    assert receipt["source_manifest_observation"]["total_manifest_bytes"]==326617369


@pytest.mark.parametrize("variant,pattern",[
    ("incorrect_biological_state","metadata-only manifest promoted"),
    ("invented_inclusion","metadata-only manifest promoted"),
    ("breeding_rows_read","metadata-only manifest promoted"),
    ("false_downloaded_md5","provider source file MD5"),
    ("extra_data_file","source file manifest name mismatch"),
    ("mutated_source_file_bytes","provider source file MD5"),
    ("changed_licence","metadata-only manifest promoted"),
    ("changed_old_BOP_receipt","original BOP"),
    ("changed_first_artifact","first official metadata archive"),
    ("changed_frozen_API","first official metadata archive"),
])
def test_false_evidence_promotion_or_source_mutation_rejected(variant,pattern):
    result,receipt,contract=_first_summary()
    result=deepcopy(result);receipt=deepcopy(receipt);contract=deepcopy(contract)
    if variant=="incorrect_biological_state":
        result["biology_terminal"]="EXTERNAL_BREEDING_GENERALIZED"
    elif variant=="invented_inclusion":
        result["published_sample_count_not_validated_against_files"]=False
    elif variant=="breeding_rows_read":
        result["outcome_rows_accessed"]=True
    elif variant=="false_downloaded_md5":
        result["declared_file_list"][0]["file_bytes_downloaded"]=True
    elif variant=="extra_data_file":
        result["declared_file_list"][0]["key"]="OUTCOME_STATES.csv"
    elif variant=="mutated_source_file_bytes":
        result["declared_file_list"][0]["manifest_md5"]="0"*32
    elif variant=="changed_licence":
        result["provider_license_id"]="CC0"
    elif variant=="changed_old_BOP_receipt":
        receipt["scientific_terminal"]["historical_BOP"]="generalizing"
    elif variant=="changed_first_artifact":
        receipt["initial_verified_actions"]["workflow_artifact_id"]=0
    elif variant=="changed_frozen_API":
        contract["target_source"]["allowed_metadata_api"]+="?download=1"
    with pytest.raises(ValueError,match=pattern):
        verify_first_source_only(result,receipt,contract)


def test_original_json_bytes_and_metadata_api_sha_are_separate():
    output,receipt,contract=_first_summary()
    with pytest.raises(ValueError,match="first Actions JSON changed"):
        verify_first_source_only(output,receipt,contract,raw_result=b'{"outcomes":true}')
    assert receipt["initial_verified_actions"]["raw_official_metadata_sha256"]!=(
        receipt["initial_verified_actions"]["first_result_sha256"]
    )


def test_manuscript_source_coverage_still_unavailable_after_an_inventory_pass():
    receipt=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["scientific_terminal"]["original_BOP_RF_altitude_validation"] if "original_BOP_RF_altitude_validation" in receipt["scientific_terminal"] else True
    assert receipt["scientific_terminal"]["external_real_German_sample_admitted"] is False
    assert receipt["scientific_terminal"]["new_group_gain_calibration_performed"] is False
    assert receipt["scientific_terminal"]["no_breeding_success_outcomes_accessed"] is True
    assert receipt["scientific_terminal"]["no_tracking_CSVs_or_GPS_accessed"] is True
