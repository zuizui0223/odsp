from __future__ import annotations

import copy
import json

import pytest

from scripts.validate_bop_dryad_external_schema_first_result_v1 import (
    CONTRACT,FIRST,RECEIPT,validate_dryad_first_result,
)


def _fixture():
    raw=FIRST.read_bytes()
    return (
        json.loads(raw),json.loads(RECEIPT.read_text(encoding="utf-8")),
        CONTRACT.read_bytes(),raw
    )


def test_first_official_Dryad_metadata_is_source_pinned_and_not_a_RF_trial():
    outcome,receipt,contract,original=_fixture()
    result=validate_dryad_first_result(outcome,receipt,contract,original)
    assert result["validated"] is True
    assert result["original_RF"]=="ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"
    assert result["provider_license"]=="CC0-1.0"
    assert result["GPS_or_BOP_outcome_data_accessed"] is False
    assert result["historical_BOP_terminal_changed"] is False
    assert receipt["frozen_contract"]["frozen_commit_sha"]=="c2798438a55a23562bb076bfb2fe247ec9e93a59"
    assert receipt["first_official_execution"]["artifact_id"]==12630760184
    assert outcome["metadata_source_status"]=="AT_LEAST_ONE_OFFICIAL_SOURCE_READ"
    assert outcome["documented_common_BOP_taxa_total"]==217
    assert outcome["documented_data_1a_individuals"]==271
    assert set(outcome["small_non_gps_file_checks"])=={
        "README.md","Study_areas_bounding_boxes.csv","Complete_succesful_breeding_seasons.csv"
    }
    assert all(v["error_code"]=="HTTP_403" for v in outcome["small_non_gps_file_checks"].values())


@pytest.mark.parametrize("modify,match",[
    ("contract","contract drifted"),
    ("first_copy","first-result semantic-copy bytes drifted"),
    ("source_api","replay differs"),
    ("provider_license","replay differs"),
    ("small_file","replay differs"),
    ("historical_BOP","replay differs"),
    ("admission","replay differs"),
    ("file_artifact_identity","source-evidence identity"),
])
def test_no_post_result_promotion_or_external_source_selection(modify,match):
    outcome,receipt,contract,original=_fixture()
    if modify=="contract":
        contract+=b"\n"
    elif modify=="first_copy":
        original+=b"\n"
    elif modify=="source_api":
        outcome["official_metadata_api"]["dataset"]["status"]="SOURCE_HOLD"
    elif modify=="provider_license":
        outcome["official_metadata_api"]["dataset"]["explicit_provider_license"]="Unknown"
    elif modify=="small_file":
        outcome["small_non_gps_file_checks"]["README.md"]["status"]="SOURCE_READ"
    elif modify=="historical_BOP":
        outcome["BOP_existing_mixed_terminal_reclassified"]=True
    elif modify=="admission":
        outcome["candidate_admission"]="EXTERNAL_CONFIRMATORY"
    elif modify=="file_artifact_identity":
        receipt["first_official_execution"]["artifact_id"]=1000
    with pytest.raises(ValueError,match=match):
        validate_dryad_first_result(outcome,receipt,contract,original)


def test_original_bop_2026_source_gate_stays_closed():
    outcome,receipt,contract,original=_fixture()
    assert outcome["BOP_2026_same_study_count_gate_reopened"] is False
    assert receipt["terminal"]["earlier_BOP_2026_same_study_gate"]==(
        "NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT"
    )
    assert receipt["original_model_compatibility"]["independent_animal_and_study_overlap_unknown"] is True
