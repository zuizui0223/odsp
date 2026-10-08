"""Constructive, source-free calendar aliasing falsification checks."""
from datetime import date
import math

import pytest

from odsp.uljin_stationary_solar_alias_counterexample_v0 import (
    stationary_solar_aliasing_control,
    _civil_expected_counts,
    _solar_expected_counts,
    _oracle_branch_shape_log_gain,
    ASCENDING,
    DESCENDING,
)
from odsp.uljin_solar_phase_device_exposure_v0 import (
    clock_to_phase, phase_to_clock, solar_phase_operating_exposure,
)


def test_invariant_solar_behavior_can_create_civil_clock_shape_gain():
    out = stationary_solar_aliasing_control()
    assert out["status"] == "SOURCE_FREE_GEOMETRIC_ALIASING_DEMONSTRATED_NOT_EMPIRICAL"
    assert out["invariant_solar_phase_intensity_on_both_dates"]
    assert out["hotspot_rising_clock_hour"] < 8 <= out["hotspot_falling_clock_hour"]
    assert out["oracle_clock_bin_shape_logscore_advantage"] > 0.01
    assert out["oracle_solar_bin_shape_logscore_advantage"] == pytest.approx(0, abs=1e-10)
    assert not out["valid_type_i_error_or_power_estimate"]
    assert not out["actual_ungulate_event_data_read"]
    assert not out["actual_camera_operation_log_read"]


def test_expected_poisson_mass_and_same_phase_law_conserved():
    ac, dc = _civil_expected_counts(ASCENDING), _civil_expected_counts(DESCENDING)
    sp = _solar_expected_counts()
    assert sum(ac) == pytest.approx(sum(dc), abs=1e-8)
    assert sum(dc) == pytest.approx(sum(sp), abs=1e-8)
    assert _oracle_branch_shape_log_gain(sp, sp) == pytest.approx(0., abs=1e-10)
    assert _oracle_branch_shape_log_gain(ac, dc) >= 0
    assert all(x > 0 for x in ac + dc + sp)


def test_identical_phase_hotspot_is_in_adjacent_civil_bins():
    out = stationary_solar_aliasing_control()
    center = out["hotspot_solar_phase_hour"]
    assert phase_to_clock(center, ASCENDING) == pytest.approx(7.94, abs=1e-10)
    assert clock_to_phase(out["hotspot_falling_clock_hour"], DESCENDING) == pytest.approx(center, abs=1e-10)
    # All four hotspot endpoints sit strictly on different sides of 08:00.
    assert phase_to_clock(out["hotspot_phase_end"], ASCENDING) < 8
    assert phase_to_clock(out["hotspot_phase_start"], DESCENDING) > 8


def test_solar_phase_exposure_requires_jacobian_even_with_full_clock_bin():
    # A single physical 4h clock interval does not always equal 4h of solar phase.
    effort = solar_phase_operating_exposure(DESCENDING, [(4., 8.)])
    assert sum(effort) > 0
    assert not math.isclose(sum(effort), 4., abs_tol=1e-3)
    assert sum(solar_phase_operating_exposure(DESCENDING, [(0., 24.)])) == pytest.approx(24)


def test_non_positive_or_mismatched_expected_counts_fail_closed():
    with pytest.raises(ValueError):
        _oracle_branch_shape_log_gain((1.,) * 6, (0.,) * 6)
    with pytest.raises(ValueError):
        _oracle_branch_shape_log_gain((1.,) * 5, (1.,) * 6)
    with pytest.raises(ValueError):
        _oracle_branch_shape_log_gain((float("nan"),) + (1.,) * 5, (1.,) * 6)
