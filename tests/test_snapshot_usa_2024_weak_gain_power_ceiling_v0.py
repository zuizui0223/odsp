from __future__ import annotations

import itertools
import json
import math

import pytest

from odsp.snapshot_usa_2024_weak_gain_power_ceiling_v0 import (
    MIX,
    TEST_ALPHA,
    fixed_betting_component_power_upper,
    min_certificates_for_q,
    snapshot_usa_2024_weak_gain_ceiling,
)


def test_published_rounded_array_mix_forces_nonforest_upper_bound():
    audit=snapshot_usa_2024_weak_gain_ceiling()
    assert audit.published_total_arrays==184
    assert audit.reported_forest_fraction==.77
    assert audit.max_nonforest_arrays_under_rounding==43
    assert audit.grassland_arrays_upper_bound==43
    assert audit.required_certified_for_q==20
    assert audit.iid_array_blocks_assumed_not_verified is True
    assert audit.actual_deployment_rows_read is False
    assert audit.ecological_prediction_claim is False
    assert audit.original_routes_reclassified is False
    assert audit.q_decision_power_upper_bound==pytest.approx(
        .008808381,abs=2e-6
    )
    json.dumps(audit.as_dict(),allow_nan=False)


def test_power_upper_is_alternative_expectation_not_constant_observation_requirement():
    # For iid alternative X in {-1,+1}, mean mu=.05, factor means match.
    # This is independent of the distribution's variance.
    B,mu=8,.05
    expectation=sum((1+lam*mu)**B for lam in MIX)/len(MIX)
    actual_upper=fixed_betting_component_power_upper(B,mu)
    assert actual_upper==pytest.approx(TEST_ALPHA*expectation,abs=1e-14)


def test_strong_signal_bound_is_not_spuriously_small():
    assert fixed_betting_component_power_upper(12,.95)==1.
    assert fixed_betting_component_power_upper(43,.05)<.009
    assert fixed_betting_component_power_upper(50,.05)<.012
    assert fixed_betting_component_power_upper(43,.05)>fixed_betting_component_power_upper(12,.05)
    assert fixed_betting_component_power_upper(43,.10)>fixed_betting_component_power_upper(43,.05)


def test_fixed_shared_validation_q_threshold_and_monotonicity():
    assert min_certificates_for_q(8) is None
    assert min_certificates_for_q(15) is None
    assert min_certificates_for_q(20)==20
    assert min_certificates_for_q(30)==29
    assert min_certificates_for_q(50)==47


def test_frozen_method_identity_is_not_recalibrated_by_new_theorem():
    x=snapshot_usa_2024_weak_gain_ceiling(gain_cap=.05)
    assert x.post_statistical_panel_design_theory_only is True
    assert x.single_refit_certification_power_upper_bound==x.q_decision_power_upper_bound
    assert not x.original_routes_reclassified


@pytest.mark.parametrize("B,mu", [(0,.05),(8,math.nan),(8,-2.),(8,.05)])
def test_invalid_inputs_fail_closed_or_are_accepted_only_when_legal(B,mu):
    if B==8 and mu==.05:
        assert fixed_betting_component_power_upper(B,mu)>0
    else:
        with pytest.raises(ValueError):
            fixed_betting_component_power_upper(B,mu)
