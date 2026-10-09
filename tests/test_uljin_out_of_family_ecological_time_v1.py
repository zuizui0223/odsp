"""Ecological mechanism misspecification and detector observational equivalence."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pytest

from odsp.uljin_out_of_family_ecological_time_v1 import (
    TRUTHS,COUNTS,SEEDS,truth_probabilities,
    score_frozen_out_of_family,
)
from odsp.uljin_common_clock_mechanistic_comparison_v0 import (
    original_days,precompute_profiles,KINDS,
)

ROOT=Path(__file__).resolve().parents[1]
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())
PLAN=json.loads((ROOT/"ULJIN_OUT_OF_FAMILY_ECOLOGICAL_TIME_V1_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_COMMON_CLOCK_MECHANISTIC_COMPARISON_V0_FIRST_RESULT_LEDGER.json").read_text())


def test_same_observational_law_has_opposite_latent_seasonal_interpretation():
    days,branch=original_days(CAL)
    arrays=precompute_profiles(days)
    seasonal,life=truth_probabilities(arrays,branch,"real_seasonal_activity")
    detector,apparatus=truth_probabilities(arrays,branch,"seasonal_detector_only")
    assert np.array_equal(seasonal,detector)
    assert not life["latent_animal_phase_stable_across_branches"]
    assert apparatus["latent_animal_phase_stable_across_branches"]
    assert not life["detection_probability_branch_time_varies"]
    assert apparatus["detection_probability_branch_time_varies"]


def test_genuine_out_of_family_mixed_and_crepuscular_truths():
    days,branch=original_days(CAL)
    models=precompute_profiles(days)
    for kind in ("bimodal_sunrise_sunset","mixed_clock_and_solar",
                 "weak_seasonal_phase_shift"):
        p,labels=truth_probabilities(models,branch,kind)
        assert p.shape==(82,96)
        assert np.all(p>0)
        assert np.allclose(p.sum(axis=1),1,atol=1e-10)
        assert np.isfinite(p).all()
    with pytest.raises(ValueError):
        truth_probabilities(models,branch,"post_outcome_new_peak")


def test_all_30_pre_frozen_worlds_include_expected_KL_regret_and_holdout():
    result=score_frozen_out_of_family(CAL,PLAN,PARENT)
    assert result["status"]=="SOURCE_FREE_ECOLOGICAL_MISSPECIFICATION_AND_DETECTION_ALIAS"
    assert result["original_frozen_astronomical_day_pairs"]==41
    assert result["same_96_civil_bins_and_site_split_as_parent"]
    assert len(result["all_30_synthetic_scenarios"])==len(TRUTHS)*len(COUNTS)*len(SEEDS)
    assert result["seasonal_biological_shift_and_detector_only_observed_laws_exactly_equal"]
    assert result["seasonal_biological_shift_and_detector_only_observed_counts_exactly_equal_with_paired_rng"]
    by={(x["truth_world"],x["counts_per_site_date"],x["seed"]):x
        for x in result["all_30_synthetic_scenarios"]}
    for n in COUNTS:
        for seed in SEEDS:
            a=by["real_seasonal_activity",n,seed]
            b=by["seasonal_detector_only",n,seed]
            assert a["synthetic_observed_counts_digest"]==b["synthetic_observed_counts_digest"]
            assert a["all_common_96bin_heldout_scores"]==b["all_common_96bin_heldout_scores"]
            assert a["all_expected_conditional_KL_regrets_nats_per_event"]==b["all_expected_conditional_KL_regrets_nats_per_event"]
    for row in result["all_30_synthetic_scenarios"]:
        assert set(row["all_common_96bin_heldout_scores"])==set(KINDS)
        assert set(row["all_expected_conditional_KL_regrets_nats_per_event"])==set(KINDS)
        assert all(x>=0 for x in row["all_expected_conditional_KL_regrets_nats_per_event"].values())
        assert row["best_descriptive_heldout_family"] in KINDS
    assert not result["biological_causality_claimed"]
    assert not result["real_ecological_source_or_camera_operation_accessed"]
    json.dumps(result,allow_nan=False)


def test_contract_and_prior_outcome_cannot_be_rewritten():
    revised=json.loads(json.dumps(PLAN))
    revised["site_date_event_counts"]=[100,200]
    with pytest.raises(ValueError,match="contract"):
        score_frozen_out_of_family(CAL,revised,PARENT)
    prior=json.loads(json.dumps(PARENT))
    prior["first_ci_run"]=1
    with pytest.raises(ValueError,match="contract"):
        score_frozen_out_of_family(CAL,PLAN,prior)
