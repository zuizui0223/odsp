"""Tamper tests for the first actual Swiss prepared-source bird-heldout RF result."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from scripts.verify_bop_nesttool_swiss_birdheldout_refit_first_v1 import (
    CONTRACT,RECEIPT,verify_first,
)

def originals():
    return (json.loads(RECEIPT.read_text(encoding="utf-8")),
            json.loads(CONTRACT.read_text(encoding="utf-8")))

def test_first_historical_prepared_source_and_32_seed_panels_are_locked():
    receipt,contract=originals()
    result=verify_first(receipt,contract)
    assert result["first_real_prepared_source_verified"] is True
    assert result["result_status"]=="MATCHED_TEST_SIZE_SEASON_VS_BIRD_RF_DESIGN_SENSITIVITY"
    assert result["predeclared_eight_seed_panels"]==32
    assert result["year_split_mean_overlapping_birds"]==120.375
    assert result["bird_split_mean_overlapping_birds"]==0
    assert result["HR_year_vs_bird_test_accuracy"]==[.968301,.96232]
    assert result["nest_year_vs_bird_test_accuracy"]==[.947368,.940192]
    assert result["HR_year_vs_bird_brier"]==[.029506,.030738]
    assert result["nest_year_vs_bird_brier"]==[.046422,.048585]
    assert result["not_replication_of_original_2024_random_seed_or_original_ranger"] is True
    assert result["redkite_future_animal"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"

@pytest.mark.parametrize("path,value",[
    (("actions","run_id"),0),
    (("actions","source_schema_job_status"),"failure"),
    (("actions","first_schema_json_sha256"),"0"*64),
    (("actions","first_model_json_sha256"),"0"*64),
    (("actions","frozen_contract_sha256"),"0"*64),
    (("first_schema_result","distinct_bird_ID_strings"),257),
    (("first_schema_result","histogram_1_to_7",0),65),
    (("first_schema_result","outcome_label_values_inspected"),True),
    (("frozen_first_source_and_model_result","eight_precommitted_seeds",0),1),
    (("frozen_first_source_and_model_result","model_metrics_per_seed_aggregate_only",0,"train_n"),487),
    (("frozen_first_source_and_model_result","model_metrics_per_seed_aggregate_only",1,"overlapping_bird_ids"),15),
    (("frozen_first_source_and_model_result","mode_by_target_summary",0,"summary","test_accuracy","mean"),.99),
    (("frozen_first_source_and_model_result","BOP_original_terminal"),"generalizing"),
    (("scientific_limit","original_2024_RF_training_test_random_assignment_not_recovered"),False),
    (("scientific_limit","experimental_RF_is_sklearn_not_original_tuned_ranger"),False),
    (("scientific_limit","group_split_zero_bird_ID_overlap_in_all_eight_seeds"),False),
    (("scientific_limit","no_formal_adjustment_to_original_paper_accuracy"),False),
    (("scientific_limit","redkite_real_external_gain_status"),"GENERALIZING"),
])
def test_tampered_first_artifact_or_biological_claim_fails(path,value):
    r,c=originals()
    bad=deepcopy(r)
    field=bad
    for key in path[:-1]:
        field=field[key]
    field[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(bad,c)

def test_rerun_artifact_is_not_silently_substituted_for_original_first_result():
    r,c=originals()
    with pytest.raises(ValueError,match="differs"):
        verify_first(r,c,raw=b'{"status":"SWISS_SAME_SOURCE_BIRD_DISJOINT_RF_REFIT_COMPARISON"}\n')

def test_only_aggregate_scores_and_no_person_or_year_ids_in_first_output():
    r,c=originals()
    data=r["frozen_first_source_and_model_result"]
    assert len(data["model_metrics_per_seed_aggregate_only"])==32
    assert {x["split_mode"] for x in data["model_metrics_per_seed_aggregate_only"]}=={"year_id","bird_id"}
    assert {x["target"] for x in data["model_metrics_per_seed_aggregate_only"]}=={"HR","nest"}
    assert "success" not in data["outcomes_used"]
    for p in data["model_metrics_per_seed_aggregate_only"]:
        assert "bird_id" not in p
        assert "year_id" not in p
        assert "individual_probability" not in p
        assert "actual_label" not in p
    assert data["no_event_data_or_real_bird_or_year_IDs_exported"] is True
    assert c["science_limits"]["Swiss_to_Germany_external_transfer_not_reassessed"] is True
