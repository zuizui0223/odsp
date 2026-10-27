from __future__ import annotations

import json

import pytest

from scripts.validate_bop_managed_first_result_v1 import (
    CONTRACT, RECEIPT, validate_first_managed_result,
)


def _first_result_fixture():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    raw = CONTRACT.read_bytes()
    import hashlib
    n=receipt["fixed_design"]["validation_group_count_per_scenario"]
    same=receipt["observed_first_result"]["same_process_covered_groups"]
    shift=receipt["observed_first_result"]["shifted_covered_groups"]
    audit=[]
    for index in range(64):
        audit.append({
            "world_index":index,
            "plan_sha256":f"{index+1:064x}",
            "training_source_sha256":f"{index+100:064x}",
            "model_sha256":f"{index+200:064x}",
            "reference_sha256":f"{index+300:064x}",
            "feature_roster_sha256":f"{index+400:064x}",
            "calibration_sha256":f"{index+500:064x}",
            "training_groups":80,
            "calibration_groups":156,
            "validation_groups":160,
            "same_covered":same//64+int(index < same%64),
            "shift_covered":shift//64+int(index < shift%64),
            "trained_only_before_calibration":True,
            "generated_forecasts_directly_from_model_artifacts":True,
            "validation_labels_not_used_to_adjust_model_or_calibration":True,
        })
    data={
        "role":"prospective_known_truth_method_validation_not_real_BOP",
        "contract_id":"bop-managed-source-model-forecast-v1-knowntruth",
        "contract_sha256":hashlib.sha256(raw).hexdigest(),
        "worlds":64,
        "validation_group_units_each_condition":n,
        "same_process_coverage":same/n,
        "shifted_validation_coverage":shift/n,
        "checks":receipt["observed_first_result"]["checks"].copy(),
        "passed":True,
        "biological_BOP_endpoint_recomputed":False,
        "frozen_BOP_terminal":"empirical_state_prediction_mixed",
        "world_audit":audit,
    }
    return data,receipt,raw


def test_first_record_is_sha_pinned_and_replay_fields_validate():
    r,receipt,raw=_first_result_fixture()
    assert receipt["contract"]["freeze_commit_sha"]=="df24eeb0e3802bf203287ce47ee89e4f2b3fd91d"
    assert receipt["first_run"]["artifact_id"]==12627243315
    assert receipt["first_run"]["workflow_run_id"]==40268692658
    verdict=validate_first_managed_result(r,receipt,raw)
    assert verdict["validated"] is True
    assert verdict["same_covered_groups"]==9129
    assert verdict["shifted_covered_groups"]==1318


@pytest.mark.parametrize("mode,expected", [
    ("contract_mutation","Git blob SHA mismatch"),
    ("coverage_changed","observed coverage changed"),
    ("missing_world","provenance missing"),
    ("duplicate_world","indices missing"),
    ("source_to_model_status","group units"),
    ("model_digest_corrupt","SHA256 hexadecimal"),
    ("coverage_inconsistent","per-world outcomes disagree"),
    ("BOP_classification_changed","not the frozen known-truth"),
])
def test_tamper_or_attempted_BOP_promotion_fail_closed(mode,expected):
    result,receipt,raw=_first_result_fixture()
    if mode=="contract_mutation":
        raw+=b" "
    elif mode=="coverage_changed":
        result["same_process_coverage"]=0.9
    elif mode=="missing_world":
        result["world_audit"].pop()
    elif mode=="duplicate_world":
        result["world_audit"][1]["world_index"]=0
    elif mode=="source_to_model_status":
        result["world_audit"][0]["generated_forecasts_directly_from_model_artifacts"]=False
    elif mode=="model_digest_corrupt":
        result["world_audit"][0]["model_sha256"]="nothash"
    elif mode=="coverage_inconsistent":
        result["world_audit"][0]["same_covered"]-=1
    elif mode=="BOP_classification_changed":
        result["frozen_BOP_terminal"]="empirical_generalizing"
    with pytest.raises(ValueError,match=expected):
        validate_first_managed_result(result,receipt,raw)
