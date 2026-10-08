"""First source-free all-41-pair smooth-rate oracle admission tests."""
import json
from pathlib import Path
import pytest

from odsp.uljin_all_41_smooth_solar_alias_v0 import (
    evaluate_all_41_smooth_solar_aliasing,
    _civil_expected_counts,
    _phase_expected_counts,
    _oracle_gain,
    _PROFILES,
)
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())
PLAN=json.loads((ROOT/"ULJIN_ALL_41_SMOOTH_SOLAR_ALIAS_V0_CONTRACT.json").read_text())


def test_all_41_original_pairs_and_smooth_invariant_phase_have_zero_solar_gain():
    result=evaluate_all_41_smooth_solar_aliasing(ORIGINAL,PLAN)
    assert result["status"]=="SOURCE_FREE_ALL_41_SMOOTH_ORACLE_SCREEN_ONLY"
    assert result["original_unchanged_calendar_pairs"]==41
    assert set(result["profiles"])==set(x[0] for x in _PROFILES)
    for name,profile in result["profiles"].items():
        assert profile["pair_count"]==41
        assert len(profile["all_41_original_pairs"])==41
        assert profile["maximum_abs_solar_oracle_gain_nats"]==pytest.approx(0,abs=1e-10)
        assert all(p["oracle_solar_gain_nats"]==pytest.approx(0,abs=1e-10)
                   for p in profile["all_41_original_pairs"])
        assert all(p["oracle_clock_gain_nats"]>=0
                   for p in profile["all_41_original_pairs"])
    assert not result["outcome_records_read"]
    assert not result["real_operation_log_records_read"]
    assert not result["ecological_effect_detected"]
    assert not result["iid_pvalues_or_type_i_error_computed"]


def test_at_least_one_broad_or_smooth_profile_generates_synthetic_geometric_alias():
    result=evaluate_all_41_smooth_solar_aliasing(ORIGINAL,PLAN)
    assert max(result["profiles"][name]["max_clock_gain_nats"] for name in
               ["broad_morning","smooth_morning","smooth_midday","smooth_evening"])>1e-12
    assert all(0<=p["positive_clock_oracle_pair_count"]<=41
               for p in result["profiles"].values())


def test_phase_intensity_mass_conserved_for_rising_and_falling_dates():
    for profile in _PROFILES:
        true_mass=sum(_phase_expected_counts(profile))
        for day in [date(2022,5,1),date(2022,8,13),date(2022,6,10),
                    date(2022,7,1)]:
            clock=_civil_expected_counts(day,profile)
            assert sum(clock)==pytest.approx(true_mass,rel=2e-10)
            assert all(x>0 for x in clock)


def test_common_vs_saturated_oracle_has_no_alias_for_identical_bin_counts():
    for profile in _PROFILES:
        a=_phase_expected_counts(profile)
        assert _oracle_gain(a,a)==pytest.approx(0,abs=1e-10)
        assert _oracle_gain(a,a)==pytest.approx(_oracle_gain(tuple(a),tuple(a)))


def test_frozen_plan_and_original_date_pair_mutations_rejected():
    frozen=json.loads(json.dumps(PLAN))
    frozen["profiles"][1]["kappa"]=4
    with pytest.raises(ValueError,match="contract"):
        evaluate_all_41_smooth_solar_aliasing(ORIGINAL,frozen)
    orig=json.loads(json.dumps(ORIGINAL))
    orig["preoutcome_structural_pairing"]["pair_absolute_daylength_difference_max_hours"]=0.25
    with pytest.raises(ValueError,match="pairing"):
        evaluate_all_41_smooth_solar_aliasing(orig,PLAN)


def test_result_is_deterministic_no_random_models_or_live_source_access():
    result=evaluate_all_41_smooth_solar_aliasing(ORIGINAL,PLAN)
    again=evaluate_all_41_smooth_solar_aliasing(ORIGINAL,PLAN)
    assert json.dumps(result,sort_keys=True,allow_nan=False)==json.dumps(
        again,sort_keys=True,allow_nan=False)
