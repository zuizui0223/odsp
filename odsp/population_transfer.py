"""Population-level summaries of realized information-transfer gains.

The estimand is the equal-weight mean across independent groups.  When a
higher-level population cluster is declared, uncertainty must not silently become
more optimistic merely because only a few clusters are available.  For fewer than
10 declared clusters, mean intervals therefore use an intercept-only CR1
cluster-robust standard error with a Student-t critical value on G-1 degrees of
freedom.  Positive-group prevalence retains its group-level Wilson bound and,
when clustered, also computes a cluster-aware lower bound; the reported lower
bound is the more conservative of the two.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from statistics import NormalDist
from typing import Mapping, Sequence

import numpy as np

from .information_transfer import InformationTransferResult


FEW_RESAMPLING_UNIT_THRESHOLD = 10


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
    mean_gain_status: str
    mean_gain_interval_method: str
    positive_group_count: int
    positive_group_fraction: float
    positive_fraction_lower: float
    positive_fraction_lower_method: str
    positive_fraction_wilson_lower: float
    positive_fraction_cluster_aware_lower: float | None
    positive_fraction_cluster_aware_method: str | None
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
    few_resampling_unit_threshold: int
    few_cluster_fallback_applied: bool
    total_gain: PopulationTransferStep
    steps: tuple[PopulationTransferStep, ...]
    population_mean_supported_ceiling: str

    def as_dict(self) -> dict[str, object]:
        if self.cluster_variable_declared and self.few_cluster_fallback_applied:
            mean_method = "cluster_robust_t_cr1"
            limitation = (
                "fewer than 10 declared population clusters; cluster percentile "
                "bootstrap is not used for the population mean"
            )
        elif self.cluster_variable_declared:
            mean_method = "cluster_percentile_bootstrap"
            limitation = None
        elif self.group_count < self.few_resampling_unit_threshold:
            mean_method = "student_t"
            limitation = None
        else:
            mean_method = "group_percentile_bootstrap"
            limitation = None
        return {
            "estimand": self.estimand,
            "role": self.role,
            "familywise_confirmatory_claim": False,
            "gain_tolerance": self.gain_tolerance,
            "group_count": self.group_count,
            "cluster_count": self.cluster_count,
            "cluster_variable_declared": self.cluster_variable_declared,
            "uncertainty": {
                "mean_interval_method": mean_method,
                "confidence_level": self.confidence_level,
                "bootstrap_draws": self.bootstrap_draws,
                "seed": self.seed,
                "resampling_unit": self.resampling_unit,
                "few_resampling_unit_threshold": self.few_resampling_unit_threshold,
                "few_cluster_fallback_applied": self.few_cluster_fallback_applied,
                "within_group_refit_uncertainty_propagated": False,
                "cluster_bootstrap_limitation": limitation,
            },
            "total_gain": self.total_gain.as_dict(),
            "steps": [step.as_dict() for step in self.steps],
            "population_mean_supported_ceiling": self.population_mean_supported_ceiling,
        }


def _wilson_lower(successes: int, n: int, confidence_level: float) -> float:
    if n <= 0:
        raise ValueError("Wilson interval requires at least one group")
    alpha = 1.0 - confidence_level
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    p = successes / n
    denominator = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    radius = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return float(max(0.0, (centre - radius) / denominator))


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    max_iterations = 300
    eps = 3e-14
    fpmin = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for iteration in range(1, max_iterations + 1):
        m2 = 2 * iteration
        aa = (
            iteration
            * (b - iteration)
            * x
            / ((qam + m2) * (a + m2))
        )
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(
            (a + iteration)
            * (qab + iteration)
            * x
            / ((a + m2) * (qap + m2))
        )
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) <= eps:
            return h
    raise ArithmeticError("incomplete-beta continued fraction did not converge")


def _regularized_incomplete_beta(x: float, a: float, b: float) -> float:
    if not 0.0 <= x <= 1.0 or a <= 0.0 or b <= 0.0:
        raise ValueError("invalid incomplete-beta arguments")
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0
    log_prefactor = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    prefactor = math.exp(log_prefactor)
    if x < (a + 1.0) / (a + b + 2.0):
        return float(
            prefactor * _beta_continued_fraction(a, b, x) / a
        )
    return float(
        1.0
        - prefactor
        * _beta_continued_fraction(b, a, 1.0 - x)
        / b
    )


def _student_t_cdf(value: float, df: int) -> float:
    if isinstance(df, bool) or int(df) < 1:
        raise ValueError("Student-t degrees of freedom must be positive")
    value = float(value)
    if value == 0.0:
        return 0.5
    x = float(df) / (float(df) + value * value)
    ibeta = _regularized_incomplete_beta(x, float(df) / 2.0, 0.5)
    if value > 0.0:
        return float(1.0 - 0.5 * ibeta)
    return float(0.5 * ibeta)


def _student_t_quantile(probability: float, df: int) -> float:
    if not 0.0 < probability < 1.0:
        raise ValueError("Student-t probability must lie strictly between zero and one")
    if probability == 0.5:
        return 0.0
    if probability < 0.5:
        return -_student_t_quantile(1.0 - probability, df)
    lower = 0.0
    upper = 1.0
    while _student_t_cdf(upper, df) < probability:
        upper *= 2.0
        if upper > 1e8:
            raise ArithmeticError("failed to bracket Student-t quantile")
    for _ in range(100):
        midpoint = 0.5 * (lower + upper)
        if _student_t_cdf(midpoint, df) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return float(0.5 * (lower + upper))


def _cluster_robust_se_cr1(
    values: np.ndarray,
    cluster_indices: Mapping[object, np.ndarray],
) -> float:
    data = np.asarray(values, dtype=float)
    cluster_count = len(cluster_indices)
    if cluster_count < 2:
        raise ValueError(
            "cluster-aware population inference requires at least two clusters"
        )
    mean = float(np.mean(data))
    residual = data - mean
    cluster_scores = np.asarray(
        [
            float(np.sum(residual[np.asarray(indices, dtype=int)]))
            for indices in cluster_indices.values()
        ],
        dtype=float,
    )
    variance = (
        cluster_count
        / (cluster_count - 1.0)
        * float(np.sum(cluster_scores * cluster_scores))
        / (data.size * data.size)
    )
    return float(math.sqrt(max(0.0, variance)))


def _student_t_mean_interval(
    values: np.ndarray,
    confidence_level: float,
) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    if data.size < 2:
        raise ValueError("Student-t mean interval requires at least two groups")
    mean = float(np.mean(data))
    se = float(np.std(data, ddof=1) / math.sqrt(data.size))
    critical = _student_t_quantile(
        1.0 - (1.0 - confidence_level) / 2.0,
        int(data.size - 1),
    )
    return float(mean - critical * se), float(mean + critical * se)


def _cluster_robust_t_interval(
    values: np.ndarray,
    cluster_indices: Mapping[object, np.ndarray],
    confidence_level: float,
) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    mean = float(np.mean(data))
    cluster_count = len(cluster_indices)
    se = _cluster_robust_se_cr1(data, cluster_indices)
    critical = _student_t_quantile(
        1.0 - (1.0 - confidence_level) / 2.0,
        cluster_count - 1,
    )
    return float(mean - critical * se), float(mean + critical * se)


def _bootstrap_intervals(
    values: np.ndarray,
    *,
    cluster_labels: tuple[object, ...],
    cluster_indices: Mapping[object, np.ndarray],
    cluster_variable_declared: bool,
    bootstrap_draws: int,
    seed: int,
    gain_tolerance: float,
    confidence_level: float,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    alpha = 1.0 - confidence_level
    boot_means = np.empty(bootstrap_draws, dtype=float)
    boot_positive = np.empty(bootstrap_draws, dtype=float)
    for draw in range(bootstrap_draws):
        if cluster_variable_declared:
            sampled_cluster_indices = rng.integers(
                0, len(cluster_labels), size=len(cluster_labels)
            )
            sampled = np.concatenate(
                [
                    cluster_indices[cluster_labels[int(cluster_index)]]
                    for cluster_index in sampled_cluster_indices
                ]
            )
        else:
            sampled = rng.integers(0, values.size, size=values.size)
        draw_gains = values[sampled]
        boot_means[draw] = float(np.mean(draw_gains))
        boot_positive[draw] = float(np.mean(draw_gains > gain_tolerance))
    lower, upper = np.quantile(
        boot_means, [alpha / 2.0, 1.0 - alpha / 2.0]
    )
    positive_lower = float(np.quantile(boot_positive, alpha / 2.0))
    return float(lower), float(upper), positive_lower


def _status(lower: float, upper: float, tolerance: float) -> str:
    if lower > tolerance:
        return "positive"
    if upper <= tolerance:
        return "nonpositive"
    return "uncertain"


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

    mean_gain = float(np.mean(values))
    cluster_count = len(cluster_labels)
    few_units = (
        cluster_count < FEW_RESAMPLING_UNIT_THRESHOLD
        if cluster_variable_declared
        else values.size < FEW_RESAMPLING_UNIT_THRESHOLD
    )

    bootstrap_positive_lower: float | None = None
    if cluster_variable_declared and few_units:
        lower, upper = _cluster_robust_t_interval(
            values, cluster_indices, confidence_level
        )
        mean_method = "cluster_robust_t_cr1"
    elif not cluster_variable_declared and few_units:
        lower, upper = _student_t_mean_interval(values, confidence_level)
        mean_method = "student_t"
    else:
        lower, upper, bootstrap_positive_lower = _bootstrap_intervals(
            values,
            cluster_labels=cluster_labels,
            cluster_indices=cluster_indices,
            cluster_variable_declared=cluster_variable_declared,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            gain_tolerance=gain_tolerance,
            confidence_level=confidence_level,
        )
        mean_method = (
            "cluster_percentile_bootstrap"
            if cluster_variable_declared
            else "group_percentile_bootstrap"
        )

    positive_count = int(np.count_nonzero(values > gain_tolerance))
    positive_fraction = float(positive_count / values.size)
    wilson_lower = _wilson_lower(
        positive_count, int(values.size), confidence_level
    )
    cluster_aware_lower: float | None = None
    cluster_aware_method: str | None = None
    if cluster_variable_declared:
        indicator = (values > gain_tolerance).astype(float)
        if few_units:
            indicator_lower, _ = _cluster_robust_t_interval(
                indicator, cluster_indices, confidence_level
            )
            cluster_aware_lower = float(max(0.0, indicator_lower))
            cluster_aware_method = "cluster_robust_t_cr1"
        else:
            if bootstrap_positive_lower is None:
                raise AssertionError("cluster bootstrap prevalence lower bound missing")
            cluster_aware_lower = float(bootstrap_positive_lower)
            cluster_aware_method = "cluster_percentile_bootstrap"
        positive_lower = float(min(wilson_lower, cluster_aware_lower))
        positive_method = (
            "minimum_of_wilson_score_and_" + cluster_aware_method
        )
    else:
        positive_lower = wilson_lower
        positive_method = "wilson_score"

    sd = float(np.std(values, ddof=1)) if values.size >= 2 else None
    if sd is not None:
        alpha = 1.0 - confidence_level
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
        cluster_count=cluster_count,
        bootstrap_seed=int(seed),
        mean_gain=mean_gain,
        mean_gain_lower=float(lower),
        mean_gain_upper=float(upper),
        mean_gain_status=_status(float(lower), float(upper), gain_tolerance),
        mean_gain_interval_method=mean_method,
        positive_group_count=positive_count,
        positive_group_fraction=positive_fraction,
        positive_fraction_lower=positive_lower,
        positive_fraction_lower_method=positive_method,
        positive_fraction_wilson_lower=wilson_lower,
        positive_fraction_cluster_aware_lower=cluster_aware_lower,
        positive_fraction_cluster_aware_method=cluster_aware_method,
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
    if declared and len(cluster_labels) < 2:
        raise ValueError(
            "declared population-cluster inference requires at least two clusters"
        )
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

    few_cluster_fallback = bool(
        declared and len(cluster_labels) < FEW_RESAMPLING_UNIT_THRESHOLD
    )
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
        few_resampling_unit_threshold=FEW_RESAMPLING_UNIT_THRESHOLD,
        few_cluster_fallback_applied=few_cluster_fallback,
        total_gain=total_gain,
        steps=step_rows,
        population_mean_supported_ceiling=ceiling,
    )
