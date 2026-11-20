"""No-RDS, no-outcome tamper tests for the official first strict-prior-year result."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.verify_bop_swiss_ranger_focal_prior_year_first_v1 import (
    CONTRACT,RECEIPT,PAIRED,MEANS,verify_first
)

def original():
    return json.loads(RECEIPT.read_text(encoding="utf-8")),json.loads(CONTRACT.read_text(encoding="utf-8"))

def test_original_focal_chronology_source_result_and_16_seed_model_proof():
    receipt,contract=original()
    output=verify_first(receipt,contract)
    assert output["status"]=="FROZEN_FIRST_FOCAL_PRIOR_YEAR_RANGER_SOURCE_AND_PAIRS_VERIFIED"
    assert output["original_first_run"]==44516904222
    assert output["test_50_birds_later_year_fixed"] is True
    assert output["prior_exposure_older_for_all_50_test_birds"] is True
    assert output["n_original_models"]==64
    assert output["n_paired_comparisons"]==32
    assert output["HR_exposed_minus_safe_log_loss"]==.005757
    assert output["nest_exposed_minus_safe_log_loss"]==.000371
    assert output["no_external_independent_generalization_certificate"] is True
    assert receipt["chronology_gate"]["source_year_range"]==[2016,2022]
    assert receipt["first_actions"]["original_artifact_ZIP_sha256"]=="23f6128024bc6476c56a90d2acef2a08f49e48de321257449197c3d2b703dbb6"

@pytest.mark.parametrize("path,value",[
    (("first_actions","run_id"),0),
    (("first_actions","source_job_conclusion"),"failure"),
    (("first_actions","original_artifact_ZIP_sha256"),"0"*64),
    (("first_actions","members",2,"sha256"),"0"*64),
    (("chronology_gate","n_two_season_ids_with_distinct_years"),50),
    (("chronology_gate","source_year_range",0),2015),
    (("chronology_gate","outcome_values_inspected_before_gate"),True),
    (("model","n_models"),63),
    (("model","n_pairs"),31),
    (("model","test_rows_identical_within_seed"),False),
    (("model","all_focal_exposed_train_years_strictly_earlier_than_test_years"),False),
    (("model","predeclared_seeds",0),20261119),
    (("model","mean_metrics_by_target_and_mode",0,"log_loss"),.999),
    (("model","paired_effects_exposed_minus_safe",0,"log_loss"),0),
    (("model","paired_seed_deltas","HR",0,1),0),
    (("model","paired_seed_deltas","nest",6,3),0),
    (("claim_ceiling","no_untouched_external_validation"),False),
    (("claim_ceiling","only_focal_test_bird_prior_year_chronology_not_global_forward_holdout"),False),
    (("claim_ceiling","no_pure_causal_identity_conclusion"),False),
    (("claim_ceiling","success_response_not_opened"),False),
    (("claim_ceiling","original_BOP"),"generalizing"),
    (("claim_ceiling","redkite_new_group"),"ADMITTED")
])
def test_first_source_or_scientific_overclaim_mutations_fail(path,value):
    receipt,contract=original()
    bad=deepcopy(receipt)
    element=bad
    for key in path[:-1]:
        element=element[key]
    element[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(bad,contract)

def test_original_protocol_is_matched_size_but_only_focal_chronological():
    receipt,contract=original()
    verify_first(receipt,contract)
    assert contract["sample_design"]["same_exact_50_test_year_ids_between_two_models_for_each_seed"] is True
    assert contract["sample_design"]["common_training_seasons_from_non_test_birds"]==438
    assert contract["sample_design"]["training_seasons_for_each_arm"]==488
    assert contract["guardrails"]["not_independent_untouched_validation"] is True
    assert contract["guardrails"]["only_focal_test_bird_prior_year_earlier_not_global_training_data_chronology"] is True
    assert MEANS[("HR","disjoint_other_birds")][0]==.9425
    assert MEANS[("HR","same_bird_other_year_exposure")][0]==.9425
    assert MEANS[("nest","disjoint_other_birds")][0]==.9025
    assert MEANS[("nest","same_bird_other_year_exposure")][0]==.90375
    assert PAIRED["HR"][-1]==12 and PAIRED["nest"][-1]==9

def test_false_original_artifact_zip_rejected_without_data_access():
    receipt,contract=original()
    with pytest.raises(ValueError,match="not the original"):
        verify_first(receipt,contract,raw_zip=b"NOT_ORIGINAL_SOURCE_ARCHIVE")
