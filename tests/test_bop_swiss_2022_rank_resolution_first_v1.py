"""Immutable source-free 2022 four-negative finite-rank Actions proof."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest

from scripts.verify_bop_swiss_2022_rank_resolution_first_v1 import (
    RECEIPT,verify_first
)

def first():
    return json.loads(RECEIPT.read_text(encoding="utf-8"))

def test_original_source_free_2022_finite_rank_first_result_and_stop():
    r=verify_first(first())
    assert r["status"]=="FIRST_EXACT_2022_FOUR_NEGATIVE_RANK_DIAGNOSTIC_VERIFIED"
    assert r["first_run"]==44752203435
    assert r["first_artifact"]==14636041683
    assert (r["n_test_positive"],r["n_test_negative"])==(28,4)
    assert r["exact_tie_free_rank_configurations"]==35960
    assert r["central_95_random_rank_reference"]==[.196428571,.803571429]
    assert r["2022_purged_HR_mean_AUC"]==.373884
    assert r["2022_purged_nest_mean_AUC"]==.313616
    assert r["2022_test_majority_accuracy"]==.875
    assert r["not_a_p_value_for_repeated_eight_seed_model_means"] is True
    assert r["original_BOP"]=="empirical_state_prediction_mixed"
    assert r["external_redkite"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"

@pytest.mark.parametrize("path,value",[
    (("contract_freeze_commit",),"0"*40),
    (("frozen_contract_git_blob_sha1",),"0"*40),
    (("original_source_unchanged","original_receipt_git_blob_sha1"),"0"*40),
    (("original_source_unchanged","no_2024_prepared_RDS_or_raw_HR_nest_labels_read"),False),
    (("first_actions","run_id"),0),
    (("first_actions","first_zip_sha256"),"0"*64),
    (("first_actions","first_json_sha256"),"0"*64),
    (("first_actions","source_free_python_3_10_3_12_3_13_succeeded"),False),
    (("fixed_reference","exact_tie_free_label_placements"),35959),
    (("fixed_reference","exact_tie_free_random_rank_central_95",0),.5),
    (("fixed_reference","four_original_auc_and_lower_reference",1,3),0.05),
    (("fixed_reference","all_twelve_original_accuracy_vs_test_majority_oracle",8,5),.2),
    (("scientific_limits","not_exact_8_seed_mean_auc_significance_test"),False),
    (("scientific_limits","actual_RF_probs_may_have_ties"),False),
    (("scientific_limits","diagnostic_oracle_majority_uses_test_prevalence_not_valid_forecast_baseline"),False),
    (("scientific_limits","four_negative_2022_cohort_no_ecological_regime_shift_inference"),False),
    (("scientific_limits","no_new_independent_outcome_labels_or_source_model_fits"),False),
    (("scientific_limits","original_BOP"),"CONFORMAL_CERTIFICATE"),
    (("scientific_limits","redkite_external"),"EXTERNALLY_VALIDATED"),
])
def test_modification_of_first_source_free_evidence_or_claim_fails(path,value):
    r=deepcopy(first())
    node=r
    for k in path[:-1]:
        node=node[k]
    node[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(r)

def test_false_first_zip_is_rejected_without_network():
    with pytest.raises(ValueError,match="does not match first artifact"):
        verify_first(first(),zip_data=b"FALSE_ZIP")

def test_no_repeat_original_source_or_model_is_requested():
    r=first()
    verify_first(r)
    assert r["original_source_unchanged"]["prior_first_run_id"]==44746545177
    assert r["original_source_unchanged"]["no_individual_predictions_or_IDs_read"] is True
    assert r["scientific_limits"]["repeated_8_forest_seeds_same_32_birds"] is True
    assert len(r["fixed_reference"]["all_twelve_original_accuracy_vs_test_majority_oracle"])==12
    assert len(r["fixed_reference"]["four_original_auc_and_lower_reference"])==4
