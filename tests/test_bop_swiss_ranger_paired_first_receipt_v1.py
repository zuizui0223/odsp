"""Regression/tamper guards for the first same-test Swiss R ranger result.

Offline-only: original data/animal keys/HR/nest values are never loaded.
"""
from __future__ import annotations
from copy import deepcopy
import json
import pytest

from scripts.verify_bop_swiss_ranger_paired_first_v1 import (
    CONTRACT,RECEIPT,PAIRED,SCORES,verify_first,
)

def originals():
    return (json.loads(RECEIPT.read_text(encoding="utf-8")),
            json.loads(CONTRACT.read_text(encoding="utf-8")))

def test_source_first_model_and_sharp_identical_test_design_verified():
    receipt,contract=originals()
    v=verify_first(receipt,contract)
    assert v["status"]=="FIRST_PAIRED_RANGER_SOURCE_AND_AGGREGATES_VERIFIED"
    assert v["run_id"]==44476326291
    assert v["first_artifact_id"]==14506357960
    assert v["heldout_50_birds_on_identical_test_rows"] is True
    assert v["disjoint_bird_overlap"]==0
    assert v["exposed_other_year_bird_overlap"]==50
    assert v["paired_fits"]==64
    assert v["HR_exposed_minus_disjoint_log_loss"]==.021876
    assert v["nest_exposed_minus_disjoint_log_loss"]==-.000909
    assert v["no_external_new_group_generalization_certified"] is True
    assert len(receipt["first_model"]["per_seed_paired_delta_by_target"]["HR"])==16
    assert len(receipt["first_model"]["per_seed_paired_delta_by_target"]["nest"])==16

@pytest.mark.parametrize("path,new_value",[
    (("first_actions","workflow_run_id"),0),
    (("first_actions","source_job_status"),"failure"),
    (("first_actions","original_zip_sha256"),"0"*64),
    (("first_actions","model_sha256"),"0"*64),
    (("first_actions","schema_sha256"),"0"*64),
    (("original_source_schema","seasons"),696),
    (("original_source_schema","bird_ID_strings"),257),
    (("original_source_schema","first_gate_outcome_values_inspected"),True),
    (("first_model","test_rows_per_seed_mode"),49),
    (("first_model","training_rows_per_seed_mode"),487),
    (("first_model","common_training_rows_between_modes"),437),
    (("first_model","disjoint_mode_test_bird_ID_overlap"),1),
    (("first_model","exposed_mode_test_bird_ID_overlap"),49),
    (("first_model","number_of_original_fixed_model_panels"),63),
    (("first_model","seeds",0),20260000),
    (("first_model","mean_metrics_by_target_and_mode",0,"test_accuracy"),.9),
    (("first_model","per_seed_paired_delta_by_target","HR",7,1),0),
    (("first_model","per_seed_paired_delta_by_target","nest",2,2),.9),
    (("first_model","paired_mean_differences_exposed_minus_disjoint",0,"log_loss_higher_in_number_of_16_seeds"),0),
    (("scientific_limits","this_is_not_a_pure_causal_effect_of_individual_identity"),False),
    (("scientific_limits","breeder_success_response_not_read"),False),
    (("scientific_limits","original_ODSP_BOP_terminal"),"universal"),
    (("scientific_limits","redkite_external_new_group_terminal"),"RANK_SUCCESS"),
])
def test_tampering_source_first_model_or_claim_limits_rejected(path,new_value):
    orig,contract=originals()
    modified=deepcopy(orig)
    obj=modified
    for x in path[:-1]:
        obj=obj[x]
    obj[path[-1]]=new_value
    with pytest.raises(ValueError):
        verify_first(modified,contract)

def test_per_seed_paired_score_signs_source_mean():
    receipt,contract=originals()
    verify_first(receipt,contract)
    pairs=receipt["first_model"]["per_seed_paired_delta_by_target"]
    for target in ("HR","nest"):
        assert sum(x[1]>0 for x in pairs[target])==PAIRED[target][-1]
        assert all(x[3]==0 for x in pairs[target])
    assert SCORES[("HR","disjoint_other_birds")][0]==.97
    assert SCORES[("HR","same_bird_other_year_exposure")][0]==.97
    assert SCORES[("nest","disjoint_other_birds")][0]==.9475
    assert SCORES[("nest","same_bird_other_year_exposure")][0]==.9475

def test_source_artifact_mismatch_detected_before_zip_decode():
    orig,contract=originals()
    with pytest.raises(ValueError,match="not identical"):
        verify_first(orig,contract,raw_zip=b"ZIP_NOT_SOURCE")
