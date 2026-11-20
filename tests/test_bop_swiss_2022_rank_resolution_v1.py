"""Known-truth exact tie-free rank-reference and immutable retrospective ceiling."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import math
import json
import pytest

from scripts.bop_swiss_2022_rank_resolution_v1 import (
    CONTRACT,PRIOR,frozen,random_rank_distribution,rank_quantile,
    lower_reference,run,
)

def test_binds_predeclared_source_first_receipt_without_provider_contact():
    c,r=frozen()
    assert c["source"]["original_first_run"]==44746545177
    assert c["source"]["original_first_artifact_id"]==14633317139
    assert c["source"]["no_HR_nest_labels_or_individual_predictions_reopen"] is True
    assert c["rank_reference"]["this_is_not_an_exact_p_value_for_8_seed_average_or_actual_tied_RF_scores"] is True
    assert r["first_models"]["original_models_scored"]==96
    assert r["first_models"]["source_2022_test_HR_negatives"]==4
    assert r["first_models"]["source_2022_test_nest_negatives"]==4
    assert r["scientific_ceiling"]["no_independent_German_or_future_population_external_validation"] is True

def test_exact_combinatorial_rank_reference_normalization_symmetry():
    d=random_rank_distribution(28,4)
    assert sum(d.values())==math.comb(32,4)==35960
    assert len(d)==113 and min(d)==0 and max(d)==112
    assert d[0]==d[112]==1
    assert all(d[i]==d[112-i] for i in range(113))
    assert sum(i*c for i,c in d.items())==56*35960
    assert lower_reference(d,.0)==1/35960
    assert lower_reference(d,1)==1
    with pytest.raises(ValueError):
        random_rank_distribution(28,0)

def test_nearest_rank_quantiles_and_expected_symmetric_small_group_uncertainty():
    d=random_rank_distribution(28,4)
    assert rank_quantile(d,.025)==pytest.approx(22/112)
    assert rank_quantile(d,.05)==pytest.approx(27/112)
    assert rank_quantile(d,.95)==pytest.approx(85/112)
    assert rank_quantile(d,.975)==pytest.approx(90/112)
    assert lower_reference(d,.373884)==pytest.approx(.2118186874304783)
    assert lower_reference(d,.313616)==pytest.approx(.12686318131256952)
    assert lower_reference(d,.415736)==pytest.approx(.30077864293659623)
    with pytest.raises(ValueError):
        rank_quantile(d,0)

def test_all_twelve_predeclared_cutoff_baselines_and_2022_false_high_accuracy():
    v=run()
    assert v["status"]=="SWISS_2022_FOUR_NEGATIVES_SOURCE_FREE_RANK_REFERENCE_ONLY"
    assert v["exact_tie_free_random_rank_label_placements"]==35960
    assert v["number_of_positive_negative_rank_pairs_per_single_forest"]==112
    assert v["one_negative_moved_past_all_28_positives_can_change_AUC_by"]==.25
    assert v["random_rank_central_90_reference"]==[
        round(27/112,9),round(85/112,9)]
    assert v["random_rank_central_95_reference"]==[
        round(22/112,9),round(90/112,9)]
    assert v["original_2022_seed_average_not_one_realized_ranking_and_may_have_score_ties"] is True
    assert len(v["four_original_2022_mean_AUC_random_rank_lower_reference"])==4
    assert len(v["all_twelve_model_accuracies_vs_test_majority_oracle_DIAGNOSTIC_ONLY"])==12
    cells={(x["cutoff"],x["target"],x["mode"]):x
          for x in v["all_twelve_model_accuracies_vs_test_majority_oracle_DIAGNOSTIC_ONLY"]}
    assert all(cells[(2022,t,m)]["source_test_majority_class_accuracy_DIAGNOSTIC_ONLY"]==.875
       for t in ("HR","nest") for m in ("full_forward","bird_purged_forward"))
    assert cells[(2022,"HR","bird_purged_forward")]["fixed_R_RF_accuracy_minus_oracle_majority_benchmark"]==0
    assert cells[(2022,"nest","bird_purged_forward")]["fixed_R_RF_accuracy_minus_oracle_majority_benchmark"]==-0.125
    assert cells[(2021,"HR","bird_purged_forward")]["fixed_R_RF_accuracy_minus_oracle_majority_benchmark"]>0.30
    assert cells[(2021,"nest","bird_purged_forward")]["fixed_R_RF_accuracy_minus_oracle_majority_benchmark"]>0.30
    assert v["original_model_results_unchanged"] is True
    assert v["no_new_source_or_outcome_or_probability_access"] is True
    assert v["historical_BOP_terminal"]=="empirical_state_prediction_mixed"
    assert v["redkite_external_terminal"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    assert v["no_actual_2022_causal_regime_shift_inferred"] is True
