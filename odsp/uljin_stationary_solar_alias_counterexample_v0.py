"""Source-free constructive solar/clock aliasing negative control for Uljin.

This is an ORACLE EXPECTED-COUNT counterexample, NOT a wildlife estimate and
NOT a calibrated hypothesis test. A single fixed detection intensity per
solar-phase hour is integrated over two original mirror dates. It can yield
a strictly positive clock-bin branch-shape improvement although its phase-bin
branch-shape improvement is zero. No stochastic fit or observations are used.
"""
from __future__ import annotations

from datetime import date
import math

from .uljin_original_pairs_equation_of_time_v0 import civil_solar_geometry
from .uljin_solar_phase_device_exposure_v0 import (
    clock_to_phase,
    phase_to_clock,
    solar_phase_operating_exposure,
)

ASCENDING = date(2022, 5, 1)
DESCENDING = date(2022, 8, 13)
CENTER_RISING_CLOCK = 7.94
HOTSPOT_PHASE_HALF_WIDTH = 0.01
BASE_RATE_PER_PHASE_HOUR = 1.0
HOTSPOT_ADDITIONAL_RATE_PER_PHASE_HOUR = 1000.0


def _phase_target() -> tuple[float, float, float]:
    mid = clock_to_phase(CENTER_RISING_CLOCK, ASCENDING)
    lo, hi = mid - HOTSPOT_PHASE_HALF_WIDTH, mid + HOTSPOT_PHASE_HALF_WIDTH
    if not 8 < lo < hi < 12:
        raise ValueError("counterexample hotspot must fit inside solar bin 8-12")
    return mid, lo, hi


def _civil_expected_counts(day: date) -> tuple[float, ...]:
    """Integrate an identical solar-phase Poisson intensity in CIVIL bins."""
    _, lo, hi = _phase_target()
    start, end = phase_to_clock(lo, day), phase_to_clock(hi, day)
    geometry = civil_solar_geometry(day, 36.85, 129.2)
    sr = geometry["sunrise_clock_minute"] / 60.0
    ss = geometry["sunset_clock_minute"] / 60.0
    if not sr < start < end < ss:
        raise ValueError("hotspot must stay in daylight and not cross midnight")
    day_jac = 12.0 / (ss - sr)
    out = []
    for k in range(6):
        a, b = 4.0 * k, 4.0 * (k + 1)
        phase_measure = sum(solar_phase_operating_exposure(day, [(a, b)]))
        hotspot_clock_overlap = max(0.0, min(b, end) - max(a, start))
        out.append(
            BASE_RATE_PER_PHASE_HOUR * phase_measure
            + HOTSPOT_ADDITIONAL_RATE_PER_PHASE_HOUR
            * day_jac * hotspot_clock_overlap
        )
    return tuple(out)


def _solar_expected_counts() -> tuple[float, ...]:
    """Integrate the same intensity in solar bins, with exact phase uptime."""
    _, lo, hi = _phase_target()
    return tuple(
        BASE_RATE_PER_PHASE_HOUR * 4.0
        + HOTSPOT_ADDITIONAL_RATE_PER_PHASE_HOUR
        * max(0.0, min(4.0 * (k + 1), hi) - max(4.0 * k, lo))
        for k in range(6)
    )


def _oracle_branch_shape_log_gain(
    ascending: tuple[float, ...], descending: tuple[float, ...]
) -> float:
    """Population expected conditional likelihood advantage.

    With full operation on both dates, the exposed phase-bin or clock-bin
    measures are identical within each date-pair bin. Common-beta null fits
    the global descending fraction; saturated bin-specific beta fits each
    bin's descending fraction. No sample, fitted model or p-value is involved.
    """
    if (
        len(ascending) != 6
        or len(descending) != 6
        or not all(math.isfinite(v) and v > 0 for v in ascending + descending)
    ):
        raise ValueError("expected counts must be six positive finite cells")
    p0 = sum(descending) / (sum(ascending) + sum(descending))
    gain = 0.0
    for a, d in zip(ascending, descending):
        p = d / (a + d)
        gain += d * math.log(p / p0) + a * math.log((1 - p) / (1 - p0))
    return max(0.0, gain) if gain > -1e-10 else gain


def stationary_solar_aliasing_control() -> dict[str, object]:
    mid, lo, hi = _phase_target()
    rise_center, fall_center = (
        phase_to_clock(mid, ASCENDING),
        phase_to_clock(mid, DESCENDING),
    )
    if not rise_center < 8.0 <= fall_center:
        raise ValueError("the frozen crossing control no longer holds")
    ac, dc = _civil_expected_counts(ASCENDING), _civil_expected_counts(DESCENDING)
    sp = _solar_expected_counts()
    civil_gain = _oracle_branch_shape_log_gain(ac, dc)
    solar_gain = _oracle_branch_shape_log_gain(sp, sp)
    expected_total = (
        24.0 * BASE_RATE_PER_PHASE_HOUR
        + 2.0 * HOTSPOT_PHASE_HALF_WIDTH
        * HOTSPOT_ADDITIONAL_RATE_PER_PHASE_HOUR
    )
    if (
        civil_gain <= 0
        or abs(solar_gain) > 1e-10
        or any(abs(sum(x) - expected_total) > 1e-8 for x in (ac, dc, sp))
    ):
        raise ValueError("stationary solar rate must conserve mass and show alias")
    return {
        "schema_version": 1,
        "method": "uljin_stationary_solar_alias_counterexample_v0",
        "status": "SOURCE_FREE_GEOMETRIC_ALIASING_DEMONSTRATED_NOT_EMPIRICAL",
        "ascending_date": ASCENDING.isoformat(),
        "descending_date": DESCENDING.isoformat(),
        "invariant_solar_phase_intensity_on_both_dates": True,
        "full_continuous_camera_uptime_assumed": True,
        "hotspot_solar_phase_hour": mid,
        "hotspot_phase_start": lo,
        "hotspot_phase_end": hi,
        "hotspot_rising_clock_hour": rise_center,
        "hotspot_falling_clock_hour": fall_center,
        "civil_clock_expected_ascending": list(ac),
        "civil_clock_expected_descending": list(dc),
        "solar_phase_expected_each_branch": list(sp),
        "expected_event_mass_each_branch": expected_total,
        "oracle_clock_bin_shape_logscore_advantage": civil_gain,
        "oracle_solar_bin_shape_logscore_advantage": solar_gain,
        "null_allows_global_branch_rate_difference": True,
        "counts_are_analytic_expectations_not_observations": True,
        "valid_type_i_error_or_power_estimate": False,
        "actual_camera_operation_log_read": False,
        "actual_ungulate_event_data_read": False,
        "confounding_ruled_out_for_real_stations": False,
        "previous_qualified_ODSP_routes_modified": False,
    }
