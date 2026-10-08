"""All-original-41 date pairs: smooth phase-stationary geometric clock aliasing.

SOURCE-FREE EXPECTED MEASURES, NOT animal detections or a hypothesis test.

Under exactly invariant solar phase intensity lambda(phi), the expected count
in a civil clock interval I at date d is

  mu_{d,I} = integral_I lambda(phi_d(t)) phi'_d(t) dt.

Use independently computed expected counts for each branch and phase/clock bin
to evaluate population conditional-binomial oracle logscore gain. This is an
upper envelope (saturated bin alternatives), NOT held-out fit or test power.
"""
from __future__ import annotations

from datetime import date
from typing import Mapping
import math

import numpy as np

from .uljin_original_pairs_equation_of_time_v0 import civil_solar_geometry
from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)

METHOD = "uljin_all_41_smooth_solar_phase_aliasing_v0"
GL_ORDER = 96
_NODES, _WEIGHTS = np.polynomial.legendre.leggauss(GL_ORDER)
_PROFILES = (
    ("uniform_phase", 0.0, 0.0, 0.0),
    ("broad_morning", 0.5, 1.0, 8.0),
    ("smooth_morning", 1.0, 2.0, 8.0),
    ("smooth_midday", 1.0, 2.0, 12.0),
    ("smooth_evening", 1.0, 2.0, 19.0),
)
_BINS = tuple((float(k*4), float(k*4+4)) for k in range(6))


def _verify_frozen_contract(contract: Mapping[str, object]) -> None:
    if (
        contract.get("schema_version") != 1
        or contract.get("contract_id") != METHOD
        or contract.get("stage") != "PRE_RESULT_FROZEN_SOURCE_FREE_ORACLE_SCREEN"
        or contract.get("parent_pr") != 233
        or contract.get("original_calendar_contract")
        != "ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
        or contract.get("integration") != {
            "method": "Gauss-Legendre",
            "nodes_per_smooth_piece": GL_ORDER,
            "civil_splits": ["sunrise", "sunset"],
            "phase_splits": [6, 18],
            "relative_mass_tolerance": 2e-10,
            "solar_gain_tolerance": 1e-10,
        }
        or contract.get("representative_solar_context")
        != {"lat": 36.85, "lon": 129.2, "timezone": "Asia/Seoul",
            "station_coords": False}
        or contract.get("fixed_bins_hours") != [list(x) for x in _BINS]
        or contract.get("profiles") != [
            {"name": name, "amplitude": amp, "kappa": kappa, "peak": peak}
            for name, amp, kappa, peak in _PROFILES
        ]
        or contract.get("source_access")
        != {"animal_events": False, "real_device_operation_log": False,
            "actual_physical_station_coordinates": False}
    ):
        raise ValueError("new pre-result source-free 41-pair contract changed")


def _rate(phi: np.ndarray, profile: tuple[str, float, float, float]
          ) -> np.ndarray:
    _, amplitude, kappa, peak = profile
    phase = 2.0 * np.pi * (phi - peak) / 24.0
    return 1.0 + amplitude * np.exp(kappa * (np.cos(phase) - 1.0))


def _gl_integrate(lo: float, hi: float, fn) -> float:
    if not lo < hi:
        raise ValueError("integration interval must be positive")
    midpoint, radius = 0.5*(lo+hi), 0.5*(hi-lo)
    t = midpoint + radius * _NODES
    return float(radius * np.dot(_WEIGHTS, fn(t)))


def _geometry(day: date) -> tuple[float, float]:
    if type(day) is not date or day.year != 2022:
        raise ValueError("original matched 2022 calendar only")
    g = civil_solar_geometry(day, 36.85, 129.2)
    sr, ss = g["sunrise_clock_minute"]/60., g["sunset_clock_minute"]/60.
    if not 0 < sr < ss < 24:
        raise ValueError("expected sunrise and sunset in local civil day")
    return float(sr), float(ss)


def _civil_expected_counts(day: date, profile: tuple[str, float, float, float]
                           ) -> tuple[float, ...]:
    sr, ss = _geometry(day)
    dl = ss - sr
    night = 24.0 - dl

    def point_intensity(t: np.ndarray) -> np.ndarray:
        is_day = (t >= sr) & (t < ss)
        adj = np.where(t >= ss, t, t + 24.0)
        phi = np.where(is_day,
                       6.0 + (t - sr) * (12.0 / dl),
                       (18.0 + (adj - ss) * (12.0 / night)) % 24.0)
        jac = np.where(is_day, 12.0/dl, 12.0/night)
        return _rate(phi, profile) * jac

    counts = []
    for lo, hi in _BINS:
        points = [lo] + [x for x in (sr, ss) if lo < x < hi] + [hi]
        counts.append(sum(_gl_integrate(a,b,point_intensity)
                          for a,b in zip(points[:-1],points[1:])))
    return tuple(counts)


def _phase_expected_counts(profile: tuple[str, float, float, float]
                           ) -> tuple[float, ...]:
    result=[]
    for lo,hi in _BINS:
        points=[lo]+[x for x in (6.0,18.0) if lo<x<hi]+[hi]
        result.append(sum(_gl_integrate(a,b,lambda t:_rate(t,profile))
                          for a,b in zip(points[:-1],points[1:])))
    return tuple(result)


def _oracle_gain(a: tuple[float, ...], d: tuple[float, ...]) -> float:
    if (len(a) != 6 or len(d) != 6
        or not all(math.isfinite(v) and v > 0 for v in a+d)):
        raise ValueError("each branch requires six positive expected cells")
    total_a,total_d = sum(a),sum(d)
    p0=total_d/(total_a+total_d)
    values = []
    for rising, falling in zip(a, d):
        p=falling/(rising+falling)
        values.append(falling*math.log(p/p0) + rising*math.log((1-p)/(1-p0)))
    gain=math.fsum(values)
    if gain < -1e-10:
        raise ValueError("oracle conditional KL gain cannot be negative")
    return max(0.0,gain)


def evaluate_all_41_smooth_solar_aliasing(
    original_contract: Mapping[str,object],
    smooth_contract: Mapping[str,object],
) -> dict[str,object]:
    """No source request, no wildlife rows; deterministic population oracles."""
    _verify_frozen_contract(smooth_contract)
    original=generate_preoutcome_2022_mirror_calendar(original_contract)
    dates=original["matched_dates"]
    if (len(dates)!=41
        or len({p["ascending_date"] for p in dates})!=41
        or len({p["descending_date"] for p in dates})!=41):
        raise ValueError("unchanged original 41 one-to-one date pairs required")
    all_results={}
    for profile in _PROFILES:
        name=profile[0]
        solar_expected=_phase_expected_counts(profile)
        solar_gain=_oracle_gain(solar_expected,solar_expected)
        pair_results=[]
        for p in dates:
            rising_date=date.fromisoformat(p["ascending_date"])
            falling_date=date.fromisoformat(p["descending_date"])
            rising=_civil_expected_counts(rising_date,profile)
            falling=_civil_expected_counts(falling_date,profile)
            clock_gain=_oracle_gain(rising,falling)
            total_solar=sum(solar_expected)
            if (max(abs(sum(rising)-total_solar),
                    abs(sum(falling)-total_solar)) >
                2e-10 * total_solar):
                raise ValueError("change-of-measure mass not conserved")
            if abs(solar_gain)>1e-10:
                raise ValueError("unchanged solar-phase density produced branch gain")
            pair_results.append({
                "ascending_date":p["ascending_date"],
                "descending_date":p["descending_date"],
                "matched_daylength_difference_minutes":
                    p["daylength_difference_minutes"],
                "expected_detections_each_date":total_solar,
                "oracle_clock_gain_nats":clock_gain,
                "oracle_clock_gain_per_expected_event_nats":
                    clock_gain / (sum(rising)+sum(falling)),
                "oracle_solar_gain_nats":solar_gain,
            })
        raw=np.array([p["oracle_clock_gain_nats"] for p in pair_results])
        normalized=np.array([p["oracle_clock_gain_per_expected_event_nats"]
                             for p in pair_results])
        all_results[name]={
            "rate_profile":{"amplitude":profile[1],"kappa":profile[2],
                            "peak_phase_hour":profile[3]},
            "pair_count":len(pair_results),
            "positive_clock_oracle_pair_count":int(np.count_nonzero(raw>1e-12)),
            "min_clock_gain_nats":float(raw.min()),
            "median_clock_gain_nats":float(np.median(raw)),
            "mean_clock_gain_nats":float(raw.mean()),
            "max_clock_gain_nats":float(raw.max()),
            "min_clock_gain_per_expected_event_nats":float(normalized.min()),
            "median_clock_gain_per_expected_event_nats":float(np.median(normalized)),
            "max_clock_gain_per_expected_event_nats":float(normalized.max()),
            "maximum_abs_solar_oracle_gain_nats":solar_gain,
            "all_41_original_pairs":pair_results,
        }
    if not any(all_results[x]["max_clock_gain_nats"]>1e-12
               for x in ("broad_morning","smooth_morning",
                         "smooth_midday","smooth_evening")):
        raise ValueError("no smooth rate generated a geometric clock alias")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_ALL_41_SMOOTH_ORACLE_SCREEN_ONLY",
        "original_unchanged_calendar_pairs":41,
        "profiles":all_results,
        "outcome_records_read":False,
        "real_operation_log_records_read":False,
        "original_ODSP_qualified_routes_modified":False,
        "heldout_empirical_gain_computed":False,
        "ecological_effect_detected":False,
        "iid_pvalues_or_type_i_error_computed":False,
    }
