"""Known-truth, no-RDS audit of calendar-forward Swiss biological bird purge."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_CONTRACT.json"
MODEL=ROOT/"scripts/bop_swiss_temporal_bird_purge_ranger_v1.R"
SCHEMA=ROOT/"scripts/bop_swiss_temporal_bird_purge_schema_v1.R"

def contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def synthetic_full_histogram():
    h={1:66,2:51,3:62,4:56,5:20,6:2,7:1}
    birds=[];years=[]
    for k,n in h.items():
        for i in range(n):
            begin=2016 + (i%(8-k))
            for j in range(k):
                birds.append((k,i));years.append(begin+j)
    return birds,years

def test_explicit_prospective_method_but_not_new_source():
    c=contract()
    assert c["contract_id"]=="bop-swiss-temporal-forward-bird-purged-ranger-v1"
    assert c["freeze_date"]=="2026-11-20"
    assert c["previous_completed"]["original_outcome_labels_already_opened_prior_PRS"]==[295,296,297]
    assert c["previous_completed"]["not_first_outcome_exposure"] is True
    assert c["source"]["git_blob_sha1"]=="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
    assert c["source"]["size_bytes"]==53709803
    assert c["gate"]["rows"]==697
    assert c["gate"]["unique_bird_id_strings"]==258
    assert c["gate"]["minimum_year"]==2016 and c["gate"]["maximum_year"]==2022
    assert c["gate"]["source_multiseason_histogram"]=={"1":66,"2":51,"3":62,"4":56,"5":20,"6":2,"7":1}
    assert c["gate"]["outcome_value_unread_until_source_gate_passed"] is True

def test_full_group_purge_is_time_ordered_for_all_three_fixed_cutoffs():
    birds,years=synthetic_full_histogram()
    assert len(birds)==697 and len(set(birds))==258
    assert min(years)==2016 and max(years)==2022
    assert Counter(Counter(birds).values())==Counter({1:66,2:51,3:62,4:56,5:20,6:2,7:1})
    for cutoff in (2020,2021,2022):
        test=[i for i,y in enumerate(years) if y>=cutoff]
        past=[i for i,y in enumerate(years) if y<cutoff]
        test_birds={birds[i] for i in test}
        clean=[i for i in past if birds[i] not in test_birds]
        assert test and past
        assert not set(clean)&set(test)
        assert all(years[i]<cutoff for i in clean+past)
        assert all(years[i]>=cutoff for i in test)
        assert not({birds[i] for i in clean}&test_birds)
        assert len(clean)<=len(past)
        assert set(clean).issubset(past)
        assert max(years[i] for i in past)<min(years[i] for i in test)

def test_locked_cutoffs_require_no_posthoc_cutoff_selection():
    c=contract()
    d=c["design"]
    assert d["cutoffs"]==[2020,2021,2022]
    assert d["primary_cutoff"]==2021
    assert d["all_cutoffs_reported_even_if_infeasible"] is True
    assert d["no_cutoff_or_year_selected_by_performance"] is True
    assert d["purged_forward_bird_id_disjoint"] is True
    assert d["all_training_rows_strictly_earlier_than_all_test_rows"] is True
    assert d["identical_postcutoff_test_rows_both_models"] is True
    assert d["purged_training_may_have_fewer_seasons_than_full_forward"] is True
    assert d["minimum_each_class_train"]==5
    assert d["minimum_each_class_test"]==3
    assert d["predeclared_HOLD_per_cutoff_target_if_infeasible"] is True

def test_rf_model_is_same_original_family_and_all_seeds_included():
    c=contract()
    m=c["model"]
    assert m["source"]=="R_ranger"
    assert m["n_trees"]==500 and m["mtry"]==5 and m["min_node_size"]==10
    assert m["only_targets"]==["HR","nest"]
    assert m["no_success_model"] is True
    assert m["random_model_seeds"]==list(range(20261221,20261229))
    assert m["modes"]==["full_forward","bird_purged_forward"]
    assert m["max_total_models"]==96
    assert m["descriptive_model_seed_variability_not_independent_validation"] is True
    assert m["primary_claim_requires_bird_purged_primary_cutoff_result"] is True
    assert c["terminals"]["external_redkite"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"

def test_real_R_code_never_substitutes_source_or_tunes_to_labels():
    code=MODEL.read_text(encoding="utf-8")
    schema=SCHEMA.read_text(encoding="utf-8")
    for must in (
        'source("scripts/bop_swiss_ranger_focal_prior_year_v1.R",local=FALSE)',
        "frozen_cutoffs<-c(2020L,2021L,2022L)",
        "frozen_model_seeds<-as.integer(20261221:20261228)",
        "forward_purge_indices<-function(bird,years,cutoff)",
        "test<-which(years>=cutoff)",
        "full_train<-which(years<cutoff)",
        "purged_train<-full_train[!(bird[full_train] %in% test_bird)]",
        'source_panels[[counter]]<-list(',
        '"HOLD_INFEASIBLE_COHORT_OR_CLASS"',
        'fit_one(dat,y,train,test,target,effective_seed)',
        'no_external_country_or_untouched_future_validation_claim=TRUE',
    ):
        assert must in code,must
    assert code.index("years<-parse_focal_calendar_years(dat)") < code.index("y<-binary_targets(dat)")
    assert 'dat[["success"]]' not in code
    assert 'dat$success' not in code
    assert 'binary_targets(dat)' not in schema
    assert 'dat[["HR"]]' not in schema
    assert 'dat[["nest"]]' not in schema
    assert "outcome_values_accessed=FALSE" in schema
