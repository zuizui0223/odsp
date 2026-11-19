"""Outcome-blind known-truth audit of the frozen 50-bird paired same-test design.

These tests run in the standard ODSP Python test environment without numpy,
pandas, sklearn, ranger, R or source animal/response data.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from random import Random
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_CONTRACT.json"
RSCRIPT=ROOT/"scripts/bop_swiss_ranger_paired_other_year_exposure_v1.R"

def frozen():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def synthetic_original_histogram():
    h={"1":66,"2":51,"3":62,"4":56,"5":20,"6":2,"7":1}
    source=[f"synthetic-bird-{k}-{i}" for k,num in h.items()
            for i in range(num) for _ in range(int(k))]
    return source,h

def test_first_freeze_and_source_safety():
    c=frozen()
    assert c["contract_id"]=="bop-swiss-ranger-same-test-bird-other-year-exposure-v1"
    assert c["freeze_date"]=="2026-11-19"
    assert c["immutable_source"]["git_blob_sha1"]=="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
    assert c["immutable_source"]["byte_length"]==53709803
    assert c["source_gate"]["exact_h_1_to_7"]=={"1":66,"2":51,"3":62,"4":56,"5":20,"6":2,"7":1}
    assert c["source_gate"]["exactly_two_season_bird_pool_size"]==51
    assert len(c["source_gate"]["exact_34_predictors"])==34
    assert c["source_gate"]["allowed_response_columns"]==["HR","nest"]
    assert c["source_gate"]["success_response_must_never_be_accessed"] is True
    assert c["controls"]["model_hyperparams_frozen_before_any_source_download"] is True

def test_known_truth_paired_equal_test_set_and_488_training_rows_feasible():
    source,h=synthetic_original_histogram()
    assert len(source)==697 and len(set(source))==258
    assert Counter(Counter(source).values())==Counter({int(k):v for k,v in h.items()})
    pool=sorted(x for x,n in Counter(source).items() if n==2)
    assert len(pool)==51
    for seed in range(20261119,20261135):
        rng=Random(seed)
        chosen=set(rng.sample(pool,50))
        test=[]
        exposed=[]
        for bird in sorted(chosen):
            indices=[i for i,x in enumerate(source) if x==bird]
            assert len(indices)==2
            test_index=rng.choice(indices)
            test.append(test_index)
            exposed.append(next(i for i in indices if i!=test_index))
        outsiders=[i for i,bird in enumerate(source) if bird not in chosen]
        assert len(outsiders)==597
        common=set(rng.sample(outsiders,438))
        remaining=[x for x in outsiders if x not in common]
        assert len(remaining)==159
        control=set(rng.sample(remaining,50))
        safe=common|control
        exposed_train=common|set(exposed)
        assert len(test)==50
        assert len(safe)==len(exposed_train)==488
        assert len(safe&exposed_train)==438
        assert not(set(test)&safe)
        assert not(set(test)&exposed_train)
        assert len(set(source[i] for i in safe)&chosen)==0
        assert len(set(source[i] for i in exposed_train)&chosen)==50

def test_ranger_fixed_model_and_no_original_retraining_claim():
    c=frozen()
    d=c["paired_fixed_design"]
    m=c["fixed_R_ranger_model"]
    assert len(d["seeds"])==16
    assert d["seeds"]==list(range(20261119,20261135))
    assert d["train_total_seasons_each_arm"]==488
    assert d["common_training_seasons_from_all_other_birds"]==438
    assert d["control_filler_seasons_from_unused_other_birds"]==50
    assert d["exposed_filler_seasons_one_other_year_from_each_test_bird"]==50
    assert d["same_test_year_ids_exactly_in_both_arms"] is True
    assert d["no_pretense_that_other_season_is_chronologically_earlier"] is True
    assert d["no_training_on_test_row_in_either_arm"] is True
    assert m["package"]=="ranger"
    assert m["n_trees"]==500 and m["mtry"]==5
    assert m["minimum_terminal_node_size"]==10
    assert m["probability"] is True
    assert m["models_n_per_run"]==64
    assert m["no_OOB_tuning_or_test_tuning"] is True
    assert m["exact_original_2024_tuned_hyperparameters_not_reproduced"] is True
    assert c["inference_limit"]["this_replacement_changes_training_feature_and_label_distribution_even_when_sample_sizes_match"] is True
    assert c["inference_limit"]["do_not_claim_pure_causal_leakage_effect"] is True
    assert c["inference_limit"]["redkite_biological_external"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"

def test_actual_R_source_contains_explicit_frozen_splits_and_ranger_and_no_success():
    src=RSCRIPT.read_text(encoding="utf-8")
    for required in [
        "make_paired_split <- function(bird,seed)",
        "exactly_two<-sort(names(all_counts)[as.integer(all_counts)==2L])",
        "selected<-sample(exactly_two,50L,replace=FALSE)",
        "common<-sample(outsiders,438L,replace=FALSE)",
        "control_filler<-sample(control_pool,50L,replace=FALSE)",
        "disjoint_train<-c(common,control_filler)",
        "exposed_train<-c(common,exposed_earlier_or_later)",
        "length(intersect(disjoint_train,exposed_train))==438L",
        "ranger::ranger(",
        "probability=TRUE",
        "num.trees=500L",
        "mtry=5L",
        "min.node.size=10L",
        'model_family="R_ranger_fixed_500_trees_mtry_5_node_10_not_original_tuned_RF"',
        "no_2024_original_model_reproduction_or_accuracy_bias_causality_claim=TRUE",
    ]:
        assert required in src,required
    assert 'dat[["success"]]' not in src
    assert 'dat$success' not in src
    assert "sample(labels" not in src

def test_optional_ci_source_must_be_frozen_before_any_original_RDS_read():
    c=frozen()
    assert c["controls"]["after_first_source_success_CI_must_be_offline_only"] is True
    assert c["controls"]["only_two_labels_ever_read"]==["HR","nest"]
    assert c["controls"]["no_raw_or_hashed_bird_or_year_ID_exports"] is True
    assert c["inference_limit"]["repeated_splits_not_independent_studies"] is True
    assert c["inference_limit"]["Swiss_to_Germany_original_external_not_recomputed"] is True
