"""Proof that equal six-bin parameter count does NOT mean equal support."""
from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from odsp.ri_solar_phase_projection_capacity_v0 import capacity_bounds_for_day
from odsp.ri_solar_clock_transfer_v0 import (
    solar_phase_to_civil_bin_matrix,sunrise_sunset_local,
)


def test_true_equal_sunrise_sunset_coordinate_is_permutation_identity():
    M=solar_phase_to_civil_bin_matrix(6.,18.)
    assert np.allclose(M,np.eye(6),atol=1e-12)
    assert np.allclose(M.max(axis=0),1.,atol=1e-12)


@pytest.mark.parametrize("day,cap_max",[
    (date(2022,12,21),.7),
    (date(2022,6,21),.5),
])
def test_source_geometry_limits_an_evening_clock_bin(day,cap_max):
    # Illustrative site near the study region, not an observed camera.
    audit=capacity_bounds_for_day(day,41.5,-71.5)
    maxima=audit["maximum_possible_solar_model_probability_per_clock_bin"]
    assert maxima[4]<cap_max  # 16:00-20:00 civil-clock bin
    assert audit["number_of_clock_bins_with_unreachable_probability_one"]>=3
    assert audit["same_parameter_count_proves_same_clock_space_expressivity"] is False
    assert audit["solar_coordinate_histogram_projection_restriction_present"] is True
    assert audit["empirical_animal_activity_inferred"] is False
    assert audit["original_ecological_v2_results_reclassified"] is False


def test_convex_hull_upper_bound_is_exact_for_any_phase_histogram():
    for day in (date(2022,12,21),date(2022,6,21)):
        sr,ss=sunrise_sunset_local(day,41.5,-71.5)
        M=solar_phase_to_civil_bin_matrix(sr,ss)
        upper=M.max(axis=0)
        rng=np.random.default_rng(12345)
        for _ in range(200):
            p=rng.dirichlet(np.ones(6))
            predicted=p@M
            assert np.all(predicted<=upper+1e-12)
            assert np.all(predicted>=-1e-12)
            assert np.isclose(predicted.sum(),1.,atol=1e-12)
        # Each individual column bound is attained at a simplex vertex.
        for j in range(6):
            k=np.argmax(M[:,j])
            assert (np.eye(6)[k]@M)[j]==pytest.approx(upper[j])


def test_original_solar_projection_cannot_equal_arbitrary_clock_distribution():
    sr,ss=sunrise_sunset_local(date(2022,6,21),41.5,-71.5)
    M=solar_phase_to_civil_bin_matrix(sr,ss)
    # A fixed-clock histogram can concentrate arbitrarily near 1 in
    # the 16-20 category. No solar-pushforward categorical histogram can.
    j=4
    assert np.max(M[:,j])<.5
    fixed_clock=np.eye(6)[j]
    assert fixed_clock[j]==1.
    assert all(row[j]<fixed_clock[j] for row in M)
