"""Conditional species×recording-stratum partial-identification calculations.

*Post-outcome* Gomes v5 sensitivity, not a confirmatory experiment.
The latent-intensity formulas are exact for strictly positive expected detected
rates y=q*lambda and q_s,z in [1/Gamma, 1]. On finite observed counts they
are illustrated with Jeffreys-smoothed plug-in counts (NOT actual calibrated q).
"""
from __future__ import annotations
from collections import Counter
import math
from typing import Mapping, Sequence

DEFAULT_GAMMAS = (1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0)
DEFAULT_ALPHA = 0.5


def _positive_rates(
    counts: Mapping[str, Mapping[str, float]], alpha: float
) -> dict[str, tuple[float, float]]:
    if not math.isfinite(alpha) or alpha < 0:
        raise ValueError("alpha must be finite and nonnegative")
    if len(counts) < 2:
        raise ValueError("need at least two acoustic-class labels")
    rates: dict[str, tuple[float, float]] = {}
    for label, d in counts.items():
        try:
            a = float(d.get("above", 0.0))
            b = float(d.get("below", 0.0))
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid count cell") from exc
        if not (math.isfinite(a) and math.isfinite(b)) or a < 0 or b < 0:
            raise ValueError("detected counts must be finite and nonnegative")
        if a + alpha <= 0 or b + alpha <= 0:
            raise ValueError("positive expected rates or explicit smoothing required")
        rates[str(label)] = (a + alpha, b + alpha)
    return rates


def interval_above_fraction(above: float, below: float, gamma: float) -> tuple[float, float]:
    """Exact p(above) feasible interval conditional on a bounded detector q."""
    if not (math.isfinite(above) and above > 0 and math.isfinite(below) and below > 0):
        raise ValueError("strictly positive expected detected rates required")
    if not math.isfinite(gamma) or gamma < 1:
        raise ValueError("detector probability ratio Gamma must be >=1")
    low = above / (above + gamma * below)
    high = gamma * above / (gamma * above + below)
    return low, high


def unavoidable_pair_difference(
    one: tuple[float, float], other: tuple[float, float]
) -> float:
    """Sharp minimum |p1-p2| across two independent feasible p intervals."""
    if any(not (0 <= a <= b <= 1) for a, b in (one, other)):
        raise ValueError("invalid probability interval")
    return max(0.0, one[0] - other[1], other[0] - one[1])


def gamma_min_for_common_vertical_profile(
    counts: Mapping[str, Mapping[str, float]], *, alpha: float = DEFAULT_ALPHA
) -> float:
    """Exactly the global Gamma needed to make all class-odds intervals intersect."""
    rates = _positive_rates(counts, alpha)
    odds = [a / b for a, b in rates.values()]
    return math.sqrt(max(odds) / min(odds))


def bound_at_gamma(
    counts: Mapping[str, Mapping[str, float]],
    gamma: float,
    *,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, float | int | bool]:
    rates = _positive_rates(counts, alpha)
    if not math.isfinite(gamma) or gamma < 1:
        raise ValueError("Gamma must be a finite number >=1")
    intervals = {label: interval_above_fraction(a, b, gamma) for label, (a, b) in rates.items()}
    weights = {label: sum(pair) for label, pair in rates.items()}
    n = len(rates)
    mass = sum(weights.values())
    labels = sorted(rates)
    nonzero = 0
    maximum = 0.0
    dsum = 0.0
    lower_I = 0.0
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            d = unavoidable_pair_difference(intervals[a], intervals[b])
            if d > 1e-12:
                nonzero += 1
            maximum = max(maximum, d)
            dsum += d
            # Pinsker + universal lower bound on latent species intensity shares.
            lower_I += 2.0 * weights[a] * weights[b] * d * d / (gamma * gamma * mass * mass)
    n_pairs = n * (n - 1) // 2
    return {
        "assumed_max_detection_probability_ratio_gamma": float(gamma),
        "number_of_acoustic_labels": n,
        "total_label_pairs": n_pairs,
        "pairs_with_necessarily_different_latent_above_fractions": nonzero,
        "pair_fraction_with_necessarily_different_latent_above_fractions": nonzero / n_pairs,
        "max_necessary_pair_absolute_stratum_fraction_difference": maximum,
        "mean_necessary_pair_absolute_stratum_fraction_difference": dsum / n_pairs,
        "lower_bound_true_label_layer_mutual_info_nats_conditional_on_model": max(0.0, lower_I),
        "all_equal_latent_vertical_profiles_possible_given_gamma": nonzero == 0,
    }


def curve(
    counts: Mapping[str, Mapping[str, float]],
    *,
    gamma_values: Sequence[float] = DEFAULT_GAMMAS,
    alpha: float = DEFAULT_ALPHA,
) -> dict:
    gamma_min = gamma_min_for_common_vertical_profile(counts, alpha=alpha)
    curve_rows = [bound_at_gamma(counts, gamma, alpha=alpha) for gamma in gamma_values]
    return {
        "analysis": "finite_count_jeffreys_plugin_detection_partial_identification",
        "not_empirically_calibrated": True,
        "source_data_already_opened_before_v5_design": True,
        "source_frame": "one_source_recorded_above_vs_below_sonar_activity_counts",
        "assumed_detector_ratio_upper_bounds_not_measured": list(gamma_values),
        "gamma_min_erase_all_label_profiles_plugin": gamma_min,
        "smoothing_per_label_stratum_count": alpha,
        "scenario_rows": curve_rows,
        "interpretation": "conditional plug-in sensitivity only, not latent ecological SDM or a statistical confidence bound",
    }


def table_from_weighted_cells(cells, *, eligible_labels: set[str] | None = None) -> dict[str, Counter]:
    by_label: dict[str, Counter] = {}
    for cell in cells:
        if eligible_labels is not None and cell.label not in eligible_labels:
            continue
        if cell.position not in ("above", "below"):
            raise ValueError("only two original recording positions allowed")
        if not isinstance(cell.number, int) or cell.number < 0:
            raise ValueError("invalid integer source count")
        by_label.setdefault(cell.label, Counter())[cell.position] += cell.number
    if len(by_label) < 2:
        raise ValueError("need >=2 source labels")
    return by_label
