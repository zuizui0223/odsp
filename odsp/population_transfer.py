"""Population-level summaries of realized information-transfer gains."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from statistics import NormalDist
from typing import Mapping, Sequence

import numpy as np

from .information_transfer import InformationTransferResult


_SMALL_CLUSTER_THRESHOLD = 10
_T95 = {
    1: 12.7062047364,
    2: 4.30265272975,
    3: 3.18244630528,
    4: 2.77644510520,
    5: 2.57058183564,
    6: 2.44691184879,
    7: 2.36462425101,
    8: 2.30600413503,
}


@dataclass(frozen=True)
class PopulationTransferStep:
    lower_level: str
    upper_level: str
    group_count: int
    cluster_count: int
    bootstrap_seed: int
    mean_gain: float
    mean_gain_lower: float
    mean_gain_upper: float
    mean_gain_interval_method: str
    mean_gain_interval_df: int | None
    mean_gain_status: str
    positive_group_count: int
    positive_group_fraction: float
    positive_fraction_lower: float
    positive_fraction_lower_method: str
    group_gain_sd: float | None
    prediction_lower: float | None
    prediction_upper: float | None
    prediction_method: str | None
    prediction_assumption: str | None
    empirical_p10: float
    empirical_p50: float
    empirical_p90: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PopulationTransferSummary:
    estimand: str
    role: str
    gain_tolerance: float
    confidence_level: float
    bootstrap_draws: int
    seed: int
    group_count: int
    cluster_count: int
    cluster_variable_declared: bool
    resampling_unit: str
    total_gain: PopulationTransferStep
    steps: tuple[PopulationTransferStep, ...]
    population_mean_supported_ceiling: str

    def as_dict(self) -> dict[str, object]:
        return {
            "estimand": self.estimand,
            "role": self.role,
            "familywise_confirmatory_claim": False,
            "gain_tolerance": self.gain_tolerance,
            "group_count": self.group_count,
            "cluster_count": self.cluster_count,
            "cluster_variable_declared": self.cluster_variable_declared,
            "uncertainty": {
                "mean_interval_method": (
                    "cluster_robust_t_cr1"
                    if self.cluster_variable_declared
                    and self.cluster_count < _SMALL_CLUSTER_THRESHOLD
                    else (
                        "cluster_percentile_bootstrap"
                        if self.cluster_variable_declared
                        else "group_percentile_bootstrap"
                    )
                ),
                "confidence_level": self.confidence_level,
                "bootstrap_draws": self.bootstrap_draws,
                "seed": self.seed,
                "resampling_unit": self.resampling_unit,
                "within_group_refit_uncertainty_propagated": False,
                "small_cluster_threshold": _SMALL_CLUSTER_THRESHOLD,
                "small_cluster_policy": (
                    "for fewer than 10 declared population clusters, mean-gain intervals use CR1 cluster-robust standard errors with a Student t critical value on G-1 df; positive-fraction cluster bounds are unavailable and the reported lower bound is a descriptive group-level Wilson fallback"
                    if self.cluster_variable_declared
                    and self.cluster_count < _SMALL_CLUSTER_THRESHOLD
                    else None
                ),
                "cluster_bootstrap_limitation": (
                    "cluster bootstrap is used only with at least 10 declared population clusters"
                    if self.cluster_variable_declared
                    else None
                ),
            },
            "total_gain": self.total_gain.as_dict(),
            "steps": [step.as_dict() for step in self.steps],
            "population_mean_supported_ceiling": self.population_mean_supported_ceiling,
        }


def _wilson_lower(successes: int, n: int, confidence_level: float) -> float:
    alpha = 1.0 - confidence_level
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    p = successes / n
    denominator = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    radius = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return float(max(0.0, (centre - radius) / denominator))


def _status(lower: float, upper: float, tolerance: float) -> str:
    if lower > tolerance:
        return "positive"
    if upper <= tolerance:
        return "nonpositive"
    return "uncertain"


def _cluster_robust_t_interval(
    values: np.ndarray,
    *,
    cluster_labels: tuple[object, ...],
    cluster_indices: Mapping[object, np.ndarray],
    confidence_level: float,
) -> tuple[float, float, int]:
    cluster_count = len(cluster_labels)
    if cluster_count < 2:
        raise ValueError(
            "at least two declared population clusters are required for clustered mean uncertainty"
        )
    if confidence_level != 0.95:
        raise ValueError(
            "small-cluster CR1 Student t fallback is frozen for 95% confidence only"
        )
    df = cluster_count - 1
    if df not in _T95:
        raise ValueError("small-cluster Student t critical value is unavailable")
    estimate = float(np.mean(values))
    residual = values - estimate
    cluster_scores = np.asarray(
        [
            float(np.sum(residual[cluster_indices[cluster]]))
            for cluster in cluster_labels
        ],
        dtype=float,
    )
    variance = (
        cluster_count
        / (cluster_count - 1.0)
        * float(np.sum(cluster_scores * cluster_scores))
        / float(values.size * values.size)
    )
    se = math.sqrt(max(0.0, variance))
    half_width = _T95[df] * se
    return estimate - half_width, estimate + half_width, df


def _summarize_gain_vector(
    gains: Sequence[float],
    *,
    lower_level: str,
    upper_level: str,
    cluster_labels: tuple[object, ...],
    cluster_indices: Mapping[object, np.ndarray],
    cluster_variable_declared: bool,
    confidence_level: float,
    bootstrap_draws: int,
    seed: int,
    gain_tolerance: float,
) -> PopulationTransferStep:
    values = np.asarray(gains, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("population summary requires finite non-empty group gains")

    alpha = 1.0 - confidence_level
    mean_gain = float(np.mean(values))
    positive_count = int(np.count_nonzero(values > gain_tolerance))
    positive_fraction = float(positive_count / values.size)
    interval_df: int | None = None

    if cluster_variable_declared and len(cluster_labels) < _SMALL_CLUSTER_THRESHOLD:
        lower, upper, interval_df = _cluster_robust_t_interval(
            values,
            cluster_labels=cluster_labels,
            cluster_indices=cluster_indices,
            confidence_level=confidence_level,
        )
        mean_interval_method = "cluster_robust_t_cr1"
        positive_lower = _wilson_lower(
            positive_count, int(values.size), confidence_level
        )
        positive_method = "wilson_score_group_level_small_cluster_fallback"
    else:
        rng = np.random.default_rng(seed)
        boot_means = np.empty(bootstrap_draws, dtype=float)
        boot_positive = np.empty(bootstrap_draws, dtype=float)
        for draw in range(bootstrap_draws):
            sampled_cluster_indices = rng.integers(
                0, len(cluster_labels), size=len(cluster_labels), endpoint=False
            )
            sampled = np.concatenate(
                [
                    cluster_indices[cluster_labels[int(cluster_index)]]
                    for cluster_index in sampled_cluster_indices
                ]
            )
            draw_gains = values[sampled]
            boot_means[draw] = float(np.mean(draw_gains))
            boot_positive[draw] = float(np.mean(draw_gains > gain_tolerance))
        lower, upper = np.quantile(
            boot_means, [alpha / 2.0, 1.0 - alpha / 2.0]
        )
        if cluster_variable_declared:
            mean_interval_method = "cluster_percentile_bootstrap"
            positive_lower = float(np.quantile(boot_positive, alpha / 2.0))
            positive_method = "cluster_percentile_bootstrap"
        else:
            mean_interval_method = "group_percentile_bootstrap"
            positive_lower = _wilson_lower(
                positive_count, int(values.size), confidence_level
            )
            positive_method = "wilson_score"

    sd = float(np.std(values, ddof=1)) if values.size >= 2 else None
    if sd is not None:
        z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
        half_width = z * sd * math.sqrt(1.0 + 1.0 / values.size)
        prediction_lower = float(mean_gain - half_width)
        prediction_upper = float(mean_gain + half_width)
        prediction_method = "normal_theory"
        prediction_assumption = "approximately_normal_group_gain_distribution"
    else:
        prediction_lower = prediction_upper = None
        prediction_method = prediction_assumption = None

    p10, p50, p90 = np.quantile(values, [0.1, 0.5, 0.9])
    return PopulationTransferStep(
        lower_level=lower_level,
        upper_level=upper_level,
        group_count=int(values.size),
        cluster_count=len(cluster_labels),
        bootstrap_seed=int(seed),
        mean_gain=mean_gain,
        mean_gain_lower=float(lower),
        mean_gain_upper=float(upper),
        mean_gain_status=_status(float(lower), float(upper), gain_tolerance),
        positive_group_count=positive_count,
        positive_group_fraction=positive_fraction,
        positive_fraction_lower=positive_lower,
        positive_fraction_lower_method=positive_method,
        group_gain_sd=sd,
        prediction_lower=prediction_lower,
        prediction_upper=prediction_upper,
        prediction_method=prediction_method,
        prediction_assumption=prediction_assumption,
        empirical_p10=float(p10),
        empirical_p50=float(p50),
        empirical_p90=float(p90),
    )


def summarize_population_transfer(
    result: InformationTransferResult,
    *,
    group_clusters: Mapping[object, object] | None = None,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260913,
    gain_tolerance: float = 0.0,
) -> PopulationTransferSummary:
    """Summarize total and adjacent gains for a population of independent groups."""
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0.0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    groups = result.predictive_result.groups
    if not groups:
        raise ValueError("population transfer requires at least one independent group")
    labels = tuple(row.group for row in groups)

    if group_clusters is None:
        cluster_for = {label: label for label in labels}
        declared = False
        resampling_unit = "group"
    else:
        missing = [label for label in labels if label not in group_clusters]
        if missing:
            raise ValueError(f"group_clusters is missing groups: {missing!r}")
        cluster_for = {label: group_clusters[label] for label in labels}
        for label, cluster in cluster_for.items():
            if cluster is None:
                raise ValueError(f"group {label!r} has a missing population cluster")
            try:
                hash(cluster)
            except TypeError as exc:
                raise ValueError("population cluster labels must be hashable") from exc
        declared = True
        resampling_unit = "declared_population_cluster"

    cluster_labels = tuple(dict.fromkeys(cluster_for[label] for label in labels))
    cluster_indices = {
        cluster: np.asarray(
            [index for index, label in enumerate(labels) if cluster_for[label] == cluster],
            dtype=int,
        )
        for cluster in cluster_labels
    }

    levels = result.predictive_result.levels
    total_gain = _summarize_gain_vector(
        [row.total_gain for row in groups],
        lower_level=levels[0],
        upper_level=levels[-1],
        cluster_labels=cluster_labels,
        cluster_indices=cluster_indices,
        cluster_variable_declared=declared,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        gain_tolerance=gain_tolerance,
    )

    step_rows = tuple(
        _summarize_gain_vector(
            [row.increments[step_index].mean_gain for row in groups],
            lower_level=step.lower_level,
            upper_level=step.upper_level,
            cluster_labels=cluster_labels,
            cluster_indices=cluster_indices,
            cluster_variable_declared=declared,
            confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed + step_index + 1,
            gain_tolerance=gain_tolerance,
        )
        for step_index, step in enumerate(result.steps)
    )

    ceiling = levels[0]
    for index, row in enumerate(step_rows):
        if row.mean_gain_status == "positive":
            ceiling = levels[index + 1]
        else:
            break

    return PopulationTransferSummary(
        estimand="equal_weight_mean_gain_across_groups",
        role="descriptive_population_level_secondary_summary",
        gain_tolerance=float(gain_tolerance),
        confidence_level=float(confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        seed=int(seed),
        group_count=len(groups),
        cluster_count=len(cluster_labels),
        cluster_variable_declared=declared,
        resampling_unit=resampling_unit,
        total_gain=total_gain,
        steps=step_rows,
        population_mean_supported_ceiling=ceiling,
    )
