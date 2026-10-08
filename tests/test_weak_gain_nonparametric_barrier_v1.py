"""Theory-only point-null counterexample, no ecological outcome data used."""
from __future__ import annotations

import json
import math

import pytest

from odsp.weak_gain_nonparametric_barrier_v1 import (
    point_alternative_distribution_free_barrier,
)


def test_exact_weak_gain_barrier_for_fortythree_iid_array_blocks():
    b=point_alternative_distribution_free_barrier(43,.05)
    assert b.null_mass_at_positive_gain==pytest.approx(1/1.05)
    assert b.null_mass_at_score_lower_bound==pytest.approx(.05/1.05)
    assert (
        b.null_mass_at_positive_gain*.05+
        b.null_mass_at_score_lower_bound*(-1.)
    )==pytest.approx(0.,abs=1e-14)
    assert b.null_probability_of_all_positive_blocks==pytest.approx(
        .12270440108,abs=1e-10
    )
    assert b.max_randomized_power_for_any_distribution_free_level_alpha_test==pytest.approx(
        .0162993338657,abs=1e-10
    )
    assert b.any_nonrandomized_level_alpha_test_can_reject_all_positive_blocks is False
    assert b.minimum_iid_blocks_per_group_to_allow_nonrandomized_point_alternative_rejection==128
    assert b.observational_result is False
    assert b.ecological_sampling_iid_verified is False
    assert b.applies_only_to_particular_constant_gain_alternative
    assert b.existing_methods_or_empirical_endpoints_reclassified is False
    json.dumps(b.as_dict(),allow_nan=False)


@pytest.mark.parametrize("d,minimum",[
    (.02,314),(.05,128),(.10,66),(.20,35)
])
def test_exact_small_gain_sample_size_boundary(d,minimum):
    before=point_alternative_distribution_free_barrier(minimum-1,d)
    after=point_alternative_distribution_free_barrier(minimum,d)
    assert not before.any_nonrandomized_level_alpha_test_can_reject_all_positive_blocks
    assert after.any_nonrandomized_level_alpha_test_can_reject_all_positive_blocks
    assert before.null_probability_of_all_positive_blocks > .002
    assert after.null_probability_of_all_positive_blocks <= .002
    assert after.minimum_iid_blocks_per_group_to_allow_nonrandomized_point_alternative_rejection==minimum


def test_null_is_valid_for_the_full_distribution_free_one_sided_family():
    # General threshold tau=.1 and lower L=-2; positive d=.4.
    b=point_alternative_distribution_free_barrier(
        17,.4,score_lower_bound=-2.,score_upper_bound=2.,
        null_threshold=.1,component_test_alpha=.025,
    )
    mean=(
        b.null_mass_at_positive_gain*b.constant_positive_gain+
        b.null_mass_at_score_lower_bound*b.score_lower_bound
    )
    assert mean==pytest.approx(.1)
    assert b.null_probability_of_all_positive_blocks==pytest.approx(
        b.null_mass_at_positive_gain**17
    )


def test_randomization_bound_was_not_mistaken_for_expected_method_power():
    b=point_alternative_distribution_free_barrier(43,.05)
    assert b.max_randomized_power_for_any_distribution_free_level_alpha_test>0
    assert b.max_randomized_power_for_any_distribution_free_level_alpha_test<.02
    assert not b.any_nonrandomized_level_alpha_test_can_reject_all_positive_blocks
    # Existence of statistical randomization does not make the ecological
    # predictive gain or sampling design identified.
    assert not b.observational_result


@pytest.mark.parametrize("n,d,low,high,tau,a",[
    (0,.05,-1.,1.,0.,.002),
    (43,0.,-1.,1.,0.,.002),
    (43,-.1,-1.,1.,0.,.002),
    (43,1.1,-1.,1.,0.,.002),
    (43,.05,0.,1.,0.,.002),
    (43,.05,-1.,1.,0.,1.),
    (43,math.nan,-1.,1.,0.,.002),
    (43,.05,-1.,1.,0.,math.nan),
])
def test_invalid_theory_domains_fail_closed(n,d,low,high,tau,a):
    with pytest.raises(ValueError):
        point_alternative_distribution_free_barrier(
            n,d,score_lower_bound=low,score_upper_bound=high,
            null_threshold=tau,component_test_alpha=a
        )
