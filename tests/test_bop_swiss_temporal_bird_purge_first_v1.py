"""No biological labels/identifiers; immutable Swiss forward-year source receipt tests."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.verify_bop_swiss_temporal_bird_purge_first_v1 import (
    CONTRACT,RECEIPT,MEAN_EXPECT,EXPECTED_ROWS,verify_first,
)

def originals():
    return (json.loads(RECEIPT.read_text(encoding="utf-8")),
            json.loads(CONTRACT.read_text(encoding="utf-8")))

def test_original_source_provenance_and_primary_2021_true_forward_bird_purge():
    r,c=originals()
    status=verify_first(r,c)
    assert status["status"]=="FIRST_RETROSPECTIVE_GLOBAL_FORWARD_BIRD_PURGE_SOURCE_VERIFIED"
    assert status["original_run_id"]==44746545177
    assert status["original_artifact_id"]==14633317139
    assert status["source_models_scored"]==96
    assert status["primary_year_cutoff"]==2021
    assert status["primary_HR_purged_AUC"]==.933179
    assert status["primary_nest_purged_AUC"]==.881147
    assert status["source_2022_test_negative_per_outcome"]==4
    assert status["original_BOP"]=="empirical_state_prediction_mixed"
    assert status["redkite_external"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    assert r["source_gate"]["row_counts_by_cutoff"][1]["purged_train_rows"]==396
    assert r["source_gate"]["row_counts_by_cutoff"][1]["test_rows"]==117
    assert r["source_gate"]["row_counts_by_cutoff"][1]["purged_train_test_overlap_birds"]==0
    assert len(r["first_models"]["all_twelve_cell_means"])==12

@pytest.mark.parametrize("path,value",[
    (("first_actions","original_zip_sha256"),"0"*64),
    (("first_actions","original_artifact_members",2,"sha256"),"0"*64),
    (("first_actions","run_id"),0),
    (("first_actions","source_job_conclusion"),"failure"),
    (("original_provenance","frozen_contract_git_blob"),"0"*40),
    (("source_gate","row_counts_by_cutoff",1,"purged_train_rows"),397),
    (("source_gate","row_counts_by_cutoff",1,"test_rows"),118),
    (("source_gate","row_counts_by_cutoff",1,"purged_train_test_overlap_birds"),1),
    (("source_gate","primary_cutoff"),2022),
    (("first_models","original_models_scored"),95),
    (("first_models","all_twelve_cell_means",5,7),0.1),
    (("first_models","all_twelve_cell_means",11,8),0.9),
    (("first_models","source_2022_test_nest_negatives"),5),
    (("scientific_ceiling","small_2022_sample_with_only_4_negatives_no_mechanism_established"),False),
    (("scientific_ceiling","train_N_differs_between_two_modes_not_pure_causal_identity_effect"),False),
    (("scientific_ceiling","source_HR_nest_outcomes_previously_accessed_not_untouched_validation"),False),
    (("scientific_ceiling","no_independent_German_or_future_population_external_validation"),False),
    (("scientific_ceiling","redkite_external"),"EXTERNALLY_GENERALIZING")
])
def test_prespecified_source_result_or_evidence_promotion_mutation_rejected(path,value):
    r,c=originals()
    obj=deepcopy(r)
    node=obj
    for key in path[:-1]:
        node=node[key]
    node[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(obj,c)

def test_model_2022_auc_below_half_is_not_automatically_ecological_regime_change():
    r,c=originals()
    verify_first(r,c)
    assert len(MEAN_EXPECT)==12
    assert set(EXPECTED_ROWS)=={2020,2021,2022}
    for target in ("HR","nest"):
        vals=MEAN_EXPECT[(2022,target,"bird_purged_forward")]
        assert vals[4]<.5  # rank AUC, not evidence of mechanism or causal change
        assert vals[7]==.875
    assert r["scientific_ceiling"]["small_2022_sample_with_only_4_negatives_no_mechanism_established"]
    assert c["design"]["primary_cutoff"]==2021
    assert c["design"]["all_cutoffs_reported_even_if_infeasible"] is True
    assert c["model"]["descriptive_model_seed_variability_not_independent_validation"] is True

def test_malicious_second_source_zip_is_rejected_without_opening_data():
    r,c=originals()
    with pytest.raises(ValueError,match="original official"):
        verify_first(r,c,raw_zip=b"NOT_GITHUB_FIRST_ORIGINAL")
