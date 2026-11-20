"""Source-free checks of the frozen focal-bird year direction analysis."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from random import Random
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_SWISS_RANGER_FOCAL_PRIOR_YEAR_V1_CONTRACT.json"
SCRIPT=ROOT/"scripts/bop_swiss_ranger_focal_prior_year_v1.R"
GATE=ROOT/"scripts/bop_swiss_ranger_focal_prior_year_schema_v1.R"

def freeze():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def fake_population():
    h={1:66,2:51,3:62,4:56,5:20,6:2,7:1}
    birds=[]; years=[]
    for k,n in h.items():
        for i in range(n):
            for y in range(k):
                birds.append(f"fake_{k}_{i}")
                years.append(2010+y)
    return birds,years

def test_source_scientific_freeze_before_label_access():
    c=freeze()
    assert c["contract_id"]=="bop-swiss-ranger-focal-prior-year-later-test-v1"
    assert c["freeze_date"]=="2026-11-19"
    assert c["origin"]["previous_first_ranger_receipt"]=="BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_FIRST_RECEIPT.json"
    assert c["origin"]["source_RDS_git_blob_sha1"]=="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
    assert c["outcome_blind_gate"]["require_source_yearid_regex"]=="^[12][0-9]{3}_.+$"
    assert c["outcome_blind_gate"]["source_year_field_if_present_must_equal_prefix_year"] is True
    assert c["outcome_blind_gate"]["all_51_two_season_birds_have_two_distinct_calendar_years"] is True
    assert c["guardrails"]["previous_RDS_target_labels_have_already_been_opened_in_PR295_and_PR296"] is True
    assert c["guardrails"]["not_independent_untouched_validation"] is True

def test_source_free_matched_size_pair_is_chronologically_ordered():
    birds,years=fake_population()
    assert len(birds)==697 and len(set(birds))==258
    counts=Counter(birds)
    assert Counter(counts.values())==Counter({1:66,2:51,3:62,4:56,5:20,6:2,7:1})
    twoyears=sorted(b for b,k in counts.items() if k==2)
    assert len(twoyears)==51
    for seed in range(20261201,20261217):
        rng=Random(seed)
        focal=set(rng.sample(twoyears,50))
        test=[]; prior=[]
        for bird in sorted(focal):
            indices=[i for i,k in enumerate(birds) if k==bird]
            assert len(indices)==2
            older,newer=sorted(indices,key=lambda i:years[i])
            assert years[older]<years[newer]
            prior.append(older);test.append(newer)
        outsider=[i for i,b in enumerate(birds) if b not in focal]
        assert len(outsider)==597
        common=set(rng.sample(outsider,438))
        others=[i for i in outsider if i not in common]
        filler=set(rng.sample(others,50))
        disjoint=common|filler
        exposed=common|set(prior)
        assert len(test)==50 and len(disjoint)==len(exposed)==488
        assert len(disjoint&exposed)==438
        assert not(set(test)&disjoint)
        assert not(set(test)&exposed)
        assert not(set(birds[i] for i in disjoint)&focal)
        assert set(birds[i] for i in exposed)&focal==focal
        assert all(years[prior_i]<years[test_i] for prior_i,test_i in zip(prior,test))

def test_frozen_model_identical_other_than_focal_chronological_choice():
    c=freeze()
    d=c["sample_design"]
    m=c["model_locked"]
    assert d["seeds"]==list(range(20261201,20261217))
    assert d["same_exact_50_test_year_ids_between_two_models_for_each_seed"] is True
    assert d["training_seasons_for_each_arm"]==488
    assert d["common_training_seasons_from_non_test_birds"]==438
    assert d["unrelated_control_filler_seasons"]==50
    assert d["older_same_bird_exposed_filler_seasons"]==50
    assert d["disjoint_control_test_bird_overlap"]==0
    assert d["prior_exposure_test_bird_overlap"]==50
    assert m["family"]=="R_ranger_probability_RF"
    assert m["ntrees"]==500 and m["mtry"]==5 and m["min_node_size"]==10
    assert m["n_fits"]==64 and m["responses"]==["HR","nest"]
    assert c["guardrails"]["only_focal_test_bird_prior_year_earlier_not_global_training_data_chronology"] is True
    assert c["guardrails"]["swapping_50_train_rows_confounds_individual_familiarity_with_feature_label_distributions"] is True

def test_R_source_requires_calendar_year_before_binary_labels():
    s=SCRIPT.read_text(encoding="utf-8")
    assert "parse_focal_calendar_years <- function(dat)" in s
    assert 'source_years_from_id' not in s
    assert 'all(grepl("^[12][0-9]{3}_.+$",ids))' in s
    assert "test[[i]]<-idx[which.max(years[idx])]" in s
    assert "exposed_earlier_or_later[[i]]<-idx[which.min(years[idx])]" in s
    assert "chronological_years<-parse_focal_calendar_years(dat)" in s
    assert s.index("chronological_years<-parse_focal_calendar_years(dat)")<s.index("targets<-binary_targets(dat)")
    assert "focal_test_bird_prior_year_verified_in_training=TRUE" in s
    assert "no_global_forward_validation_claim=TRUE" in s
    assert "source_HR_nest_already_opened_in_prior_PRS=TRUE" in s
    assert 'dat[["success"]]' not in s
    assert 'dat$success' not in s

def test_outcome_blind_R_gate_does_not_inspect_binary_labels():
    s=GATE.read_text(encoding="utf-8")
    assert "check_schema(dat)" in s
    assert "parse_focal_calendar_years(dat)" in s
    assert "length(exactly_two)==51L" in s
    assert "outcome_values_inspected=FALSE" in s
    assert "model_fitted=FALSE" in s
    assert 'dat[["HR"]]' not in s and 'dat[["nest"]]' not in s
    assert 'dat[["success"]]' not in s
