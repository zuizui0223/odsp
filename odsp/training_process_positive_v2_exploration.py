"""Post-v1-failure exploration of a PSD-clipped two-way studentizer.

This is deliberately NOT qualification evidence. It compares a successor
studentizer after the frozen v1 power gate failed. The candidate keeps the
Cameron-Gelbach-Miller inclusion-exclusion variance but applies only the scalar
positive-semidefinite correction max(raw_two_way_variance, 0), rather than v1's
additional max-with-each-one-way-component safeguard.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np

from .positive_transfer_bootstrap_t import (
    _stable_group_seed,
    one_sided_lower_bounds,
    one_sided_lower_max_t_critical_value,
)
from .refit_information_transfer import _labels, _refit_ids, _weights
from .training_process_positive_transfer import _shared_process_refit_draws


@dataclass(frozen=True)
class PSDCandidateResult:
    lower_bounds: tuple[float, ...]
    critical_value: float
    point_negative_raw_variance_fraction: float
    bootstrap_nonpositive_raw_variance_fraction: float
    infinite_critical_value: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "lower_bounds": list(self.lower_bounds),
            "critical_value": self.critical_value,
            "point_negative_raw_variance_fraction": self.point_negative_raw_variance_fraction,
            "bootstrap_nonpositive_raw_variance_fraction": self.bootstrap_nonpositive_raw_variance_fraction,
            "infinite_critical_value": self.infinite_critical_value,
        }


def _raw_two_way_components(
    numerator: np.ndarray,
    weight: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    r, b, c = numerator.shape
    mass = float(np.sum(weight))
    denominator = float(r) * mass
    mean = np.sum(numerator, axis=(0, 1)) / denominator
    residual = numerator - weight[None, :, None] * mean[None, None, :]

    refit_cluster = np.sum(residual, axis=1)
    vr = (float(r) / float(r - 1)) * np.sum(
        refit_cluster * refit_cluster, axis=0
    ) / (denominator**2)

    block_cluster = np.sum(residual, axis=0)
    vb = (float(b) / float(b - 1)) * np.sum(
        block_cluster * block_cluster, axis=0
    ) / (denominator**2)

    cells = r * b
    vi = (float(cells) / float(cells - 1)) * np.sum(
        residual * residual, axis=(0, 1)
    ) / (denominator**2)
    raw = vr + vb - vi
    return mean, raw


def _bootstrap_psd(
    numerator: np.ndarray,
    weight: np.ndarray,
    refit_draws: np.ndarray,
    block_draws: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    draws, r = refit_draws.shape
    b = block_draws.shape[1]
    c = numerator.shape[2]
    means = np.empty((draws, c), dtype=float)
    ses = np.empty((draws, c), dtype=float)
    nonpositive = 0
    total = draws * c

    cells_per_draw = max(r * b * c, 1)
    chunk_size = max(1, min(draws, 2_000_000 // cells_per_draw))
    for start in range(0, draws, chunk_size):
        end = min(start + chunk_size, draws)
        rr = refit_draws[start:end]
        bb = block_draws[start:end]
        local = numerator[rr[:, :, None], bb[:, None, :], :]
        local_weight = weight[bb]
        mass = np.sum(local_weight, axis=1)
        denominator = float(r) * mass
        mean = np.sum(local, axis=(1, 2)) / denominator[:, None]
        residual = local - local_weight[:, None, :, None] * mean[:, None, None, :]

        refit_cluster = np.sum(residual, axis=2)
        vr = (float(r) / float(r - 1)) * np.sum(
            refit_cluster * refit_cluster, axis=1
        ) / (denominator[:, None] ** 2)

        block_cluster = np.sum(residual, axis=1)
        vb = (float(b) / float(b - 1)) * np.sum(
            block_cluster * block_cluster, axis=1
        ) / (denominator[:, None] ** 2)

        cells = r * b
        vi = (float(cells) / float(cells - 1)) * np.sum(
            residual * residual, axis=(1, 2)
        ) / (denominator[:, None] ** 2)
        raw = vr + vb - vi
        nonpositive += int(np.count_nonzero(raw <= 0.0))
        means[start:end] = mean
        ses[start:end] = np.sqrt(np.maximum(raw, 0.0))

    return means, ses, nonpositive, total


def evaluate_psd_candidate(
    row_gain_by_refit: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    sample_weight: Sequence[float] | None = None,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 500,
    seed: int = 20261007,
) -> PSDCandidateResult:
    gain = np.asarray(row_gain_by_refit, dtype=float)
    if gain.ndim == 2:
        gain = gain[:, :, None]
    if gain.ndim != 3 or 0 in gain.shape or not np.isfinite(gain).all():
        raise ValueError("candidate requires a finite non-empty refit x row x contrast tensor")
    r, n, c = gain.shape
    if r < 2:
        raise ValueError("candidate requires at least two refits")
    if bootstrap_draws < 100:
        raise ValueError("bootstrap_draws must be >= 100")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")

    ids, order = _refit_ids(refit_ids, r)
    gain = gain[order]
    group = _labels(groups, n, name="groups")
    block = _labels(blocks, n, name="blocks")
    weight = _weights(sample_weight, n)
    refit_draws = _shared_process_refit_draws(seed, r, bootstrap_draws)

    point_means: list[float] = []
    point_ses: list[float] = []
    bootstrap_means: list[np.ndarray] = []
    bootstrap_ses: list[np.ndarray] = []
    point_negative = 0
    point_total = 0
    bootstrap_nonpositive = 0
    bootstrap_total = 0

    group_order = tuple(
        sorted(set(group.tolist()), key=lambda value: (type(value).__name__, repr(value)))
    )
    for group_value in group_order:
        mask = group == group_value
        local_gain = gain[:, mask, :]
        local_weight = weight[mask]
        local_block = block[mask]
        positive = local_weight > 0
        block_order = tuple(
            sorted(
                set(local_block[positive].tolist()),
                key=lambda value: (type(value).__name__, repr(value)),
            )
        )
        b = len(block_order)
        if b < 2:
            raise ValueError("candidate requires at least two positive-mass blocks per group")
        block_weight = np.empty(b, dtype=float)
        numerator = np.zeros((r, b, c), dtype=float)
        for j, block_value in enumerate(block_order):
            bm = (local_block == block_value) & positive
            block_weight[j] = float(np.sum(local_weight[bm]))
            numerator[:, j, :] = np.sum(
                local_gain[:, bm, :] * local_weight[bm][None, :, None],
                axis=1,
            )

        mean, raw = _raw_two_way_components(numerator, block_weight)
        point_negative += int(np.count_nonzero(raw < 0.0))
        point_total += c
        se = np.sqrt(np.maximum(raw, 0.0))

        rng = np.random.default_rng(_stable_group_seed(seed, group_value))
        block_draws = rng.integers(0, b, size=(bootstrap_draws, b))
        bm, bs, nonpositive, total = _bootstrap_psd(
            numerator, block_weight, refit_draws, block_draws
        )
        bootstrap_nonpositive += nonpositive
        bootstrap_total += total

        for k in range(c):
            point_means.append(float(mean[k]))
            point_ses.append(float(se[k]))
            bootstrap_means.append(bm[:, k])
            bootstrap_ses.append(bs[:, k])

    bmean = np.column_stack(bootstrap_means)
    bse = np.column_stack(bootstrap_ses)
    pmean = np.asarray(point_means, dtype=float)
    pse = np.asarray(point_ses, dtype=float)
    critical = one_sided_lower_max_t_critical_value(
        bmean,
        bse,
        pmean,
        confidence_level=confidence_level,
    )
    lower = one_sided_lower_bounds(pmean, pse, critical)
    return PSDCandidateResult(
        lower_bounds=tuple(float(value) for value in lower),
        critical_value=float(critical),
        point_negative_raw_variance_fraction=float(point_negative / point_total),
        bootstrap_nonpositive_raw_variance_fraction=float(
            bootstrap_nonpositive / bootstrap_total
        ),
        infinite_critical_value=bool(math.isinf(critical)),
    )
