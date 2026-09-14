"""Reusable cluster bootstrap-t primitives for ODSP simultaneous inference.

The historical ODSP v1 simultaneous interval standardized outer bootstrap
replicates by one fixed bootstrap standard deviation.  That is a useful
standardized max-deviation sensitivity analysis, but it is not a genuine
bootstrap-t because the studentizer is not recomputed inside each bootstrap
replicate.

This module implements replicate-specific studentization for ratio-of-sums
estimators built from exchangeable validation blocks.  For block ``b`` with
weighted numerator ``N_b`` and weight mass ``W_b``, the point estimator is

    theta = sum_b N_b / sum_b W_b.

Its cluster plug-in standard error is based on the ratio influence residual
``N_b - theta W_b``.  The same standard error is recomputed from the resampled
blocks inside every bootstrap replicate before the max-t statistic is formed.
"""
from __future__ import annotations

import math

import numpy as np


_EPS = 1e-15


def _validate_block_arrays(
    block_numerator: np.ndarray,
    block_weight: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    numerator = np.asarray(block_numerator, dtype=float)
    weight = np.asarray(block_weight, dtype=float)
    if numerator.ndim == 1:
        numerator = numerator[:, None]
    if numerator.ndim != 2 or numerator.shape[0] < 2 or numerator.shape[1] == 0:
        raise ValueError(
            "block_numerator must be a blocks x contrasts matrix with at least two blocks"
        )
    if weight.shape != (numerator.shape[0],):
        raise ValueError("block_weight must contain one weight per block")
    if not np.isfinite(numerator).all():
        raise ValueError("block_numerator must be finite")
    if not np.isfinite(weight).all() or np.any(weight <= 0):
        raise ValueError("block_weight must be finite and strictly positive")
    return numerator, weight


def ratio_mean_and_cluster_se(
    block_numerator: np.ndarray,
    block_weight: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ratio-of-sums means and cluster plug-in standard errors.

    The standard error treats the supplied blocks as the exchangeable sampling
    units.  It is invariant to multiplying all block weights and numerators by
    the same positive constant.
    """

    numerator, weight = _validate_block_arrays(block_numerator, block_weight)
    block_count = numerator.shape[0]
    denominator = float(np.sum(weight))
    mean = np.sum(numerator, axis=0) / denominator
    residual = numerator - weight[:, None] * mean[None, :]
    variance_numerator = (
        float(block_count) / float(block_count - 1)
    ) * np.sum(residual * residual, axis=0)
    se = np.sqrt(np.maximum(variance_numerator, 0.0)) / denominator
    return mean.astype(float), se.astype(float)


def bootstrap_ratio_mean_and_cluster_se(
    block_numerator: np.ndarray,
    block_weight: np.ndarray,
    sampled_blocks: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Recompute ratio means and studentizers inside every bootstrap draw.

    ``sampled_blocks`` has shape ``draws x B`` and contains integer positions in
    ``0..B-1``.  Every draw must contain exactly ``B`` sampled blocks so the
    bootstrap mirrors the original cluster sample size.
    """

    numerator, weight = _validate_block_arrays(block_numerator, block_weight)
    sampled = np.asarray(sampled_blocks)
    block_count = numerator.shape[0]
    if (
        sampled.ndim != 2
        or sampled.shape[1] != block_count
        or sampled.shape[0] == 0
        or not np.issubdtype(sampled.dtype, np.integer)
        or np.any(sampled < 0)
        or np.any(sampled >= block_count)
    ):
        raise ValueError(
            "sampled_blocks must be a non-empty draws x block_count integer matrix"
        )

    sampled_weight = weight[sampled]  # draws x blocks
    sampled_numerator = numerator[sampled, :]  # draws x blocks x contrasts
    denominator = np.sum(sampled_weight, axis=1)
    mean = np.sum(sampled_numerator, axis=1) / denominator[:, None]
    residual = (
        sampled_numerator
        - sampled_weight[:, :, None] * mean[:, None, :]
    )
    variance_numerator = (
        float(block_count) / float(block_count - 1)
    ) * np.sum(residual * residual, axis=1)
    se = np.sqrt(np.maximum(variance_numerator, 0.0)) / denominator[:, None]
    return mean.astype(float), se.astype(float)


def studentized_max_t_critical_value(
    bootstrap_mean: np.ndarray,
    bootstrap_se: np.ndarray,
    point_mean: np.ndarray,
    *,
    confidence_level: float,
    epsilon: float = _EPS,
) -> float:
    """Return a two-sided max-t critical value with replicate-specific SEs.

    A zero bootstrap SE contributes t=0 only when the corresponding bootstrap
    estimate also equals the point estimate to numerical tolerance.  A zero SE
    with a non-zero displacement contributes infinity, making the resulting
    interval fail conservatively rather than silently dividing by zero.

    The critical value is the conservative empirical quantile (`method='higher'`)
    rather than a linearly interpolated quantile.  This is especially important
    when some fail-closed bootstrap statistics are infinite: interpolation
    between a finite statistic and infinity is undefined and must not create NaN.
    """

    means = np.asarray(bootstrap_mean, dtype=float)
    ses = np.asarray(bootstrap_se, dtype=float)
    point = np.asarray(point_mean, dtype=float)
    if means.ndim != 2 or ses.shape != means.shape:
        raise ValueError("bootstrap_mean and bootstrap_se must share draws x cells shape")
    if point.shape != (means.shape[1],):
        raise ValueError("point_mean must contain one value per bootstrap cell")
    if not np.isfinite(means).all() or not np.isfinite(ses).all() or np.any(ses < 0):
        raise ValueError("bootstrap means and standard errors must be finite and SEs non-negative")
    if not np.isfinite(point).all():
        raise ValueError("point_mean must be finite")
    if not math.isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")

    displacement = np.abs(means - point[None, :])
    statistic = np.zeros_like(displacement)
    positive_se = ses > epsilon
    statistic[positive_se] = displacement[positive_se] / ses[positive_se]
    degenerate_moved = (~positive_se) & (displacement > epsilon)
    statistic[degenerate_moved] = np.inf
    maxima = np.max(statistic, axis=1)
    return float(np.quantile(maxima, confidence_level, method="higher"))


def simultaneous_bootstrap_t_bounds(
    point_mean: np.ndarray,
    point_se: np.ndarray,
    critical_value: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Construct symmetric bootstrap-t bounds on the original estimator scale."""

    mean = np.asarray(point_mean, dtype=float)
    se = np.asarray(point_se, dtype=float)
    if mean.ndim != 1 or se.shape != mean.shape:
        raise ValueError("point_mean and point_se must be aligned one-dimensional vectors")
    if not np.isfinite(mean).all() or not np.isfinite(se).all() or np.any(se < 0):
        raise ValueError("point means and standard errors must be finite and SEs non-negative")
    if math.isnan(critical_value) or critical_value < 0:
        raise ValueError("critical_value must be non-negative")
    if math.isinf(critical_value):
        lower = np.full_like(mean, -np.inf)
        upper = np.full_like(mean, np.inf)
        zero = se <= _EPS
        lower[zero] = mean[zero]
        upper[zero] = mean[zero]
        return lower, upper
    return mean - critical_value * se, mean + critical_value * se
