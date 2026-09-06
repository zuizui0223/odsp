"""Block-aware uncertainty for independent-group transfer gains.

ODSP's ordinary transfer rule classifies the sign of each independent group's
held-out conditional-minus-marginal log-score gain.  This module adds a separate
uncertainty audit.  Caller-declared blocks are resampled with replacement within
each validation group while rows inside a block stay together.  A group is
robustly positive only when the lower percentile bound is above zero.

The bootstrap is an empirical uncertainty procedure, not an exact finite-sample
guarantee.  Its validity depends on a scientifically defensible block definition.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class TransferGainUncertaintyRow:
    group_id: str
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BlockAwareTransferAudit:
    row_count: int
    group_count: int
    confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    row_independence_assumed: bool
    mean_gain: float
    point_transfer_category: str
    robust_transfer_category: str
    robust_admissible: bool
    unavailable_group_count: int
    uncertain_group_count: int
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    pooled_mean_can_override_group_failure: bool
    point_estimate_can_override_uncertainty: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[TransferGainUncertaintyRow, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


def _weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    weight = np.asarray(values, dtype=float)
    if weight.shape != (n,):
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(weight).all() or np.any(weight < 0) or not np.any(weight > 0):
        raise ValueError("sample_weight must be finite, non-negative and positive in total")
    return weight


def _labels(values: Sequence[object], n: int, name: str) -> tuple[str, ...]:
    if len(values) != n:
        raise ValueError(f"{name} must contain one value per row")
    labels = tuple(str(value).strip() for value in values)
    if any(not value for value in labels):
        raise ValueError(f"{name} labels must be non-empty")
    return labels


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    total = float(np.sum(weight))
    if not total > 0:
        raise ValueError("weights must have positive total mass")
    return float(np.sum(values * weight) / total)


def _stable_group_seed(seed: int, group_id: str) -> int:
    digest = hashlib.sha256(f"{seed}|{group_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _bootstrap_group_mean(
    gain: np.ndarray,
    weight: np.ndarray,
    block_labels: tuple[str, ...],
    *,
    draws: int,
    seed: int,
) -> np.ndarray:
    ordered_blocks = tuple(dict.fromkeys(block_labels))
    block_weight = np.empty(len(ordered_blocks), dtype=float)
    block_weighted_gain = np.empty(len(ordered_blocks), dtype=float)
    label_array = np.asarray(block_labels, dtype=object)
    for index, block_id in enumerate(ordered_blocks):
        mask = label_array == block_id
        local_weight = weight[mask]
        block_weight[index] = np.sum(local_weight)
        block_weighted_gain[index] = np.sum(gain[mask] * local_weight)

    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, len(ordered_blocks), size=(draws, len(ordered_blocks)))
    sampled_weight = block_weight[sampled]
    sampled_weighted_gain = block_weighted_gain[sampled]
    denominator = np.sum(sampled_weight, axis=1)
    numerator = np.sum(sampled_weighted_gain, axis=1)
    return numerator / denominator


def audit_block_aware_transfer_uncertainty(
    row_gain: Sequence[float],
    groups: Sequence[object],
    *,
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 2000,
    seed: int = 20260906,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> BlockAwareTransferAudit:
    """Audit independent-group gain uncertainty with a paired block bootstrap."""

    gain = np.asarray(row_gain, dtype=float)
    if gain.ndim != 1 or gain.size == 0 or not np.isfinite(gain).all():
        raise ValueError("row_gain must be a non-empty finite one-dimensional vector")
    n = int(gain.size)
    group_labels = _labels(groups, n, "groups")
    weight = _weights(sample_weight, n)
    if not math.isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")
    if not isinstance(bootstrap_draws, int) or bootstrap_draws < 100:
        raise ValueError("bootstrap_draws must be an integer >= 100")
    if not isinstance(minimum_blocks_per_group, int) or minimum_blocks_per_group < 2:
        raise ValueError("minimum_blocks_per_group must be an integer >= 2")
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    row_independence_assumed = blocks is None
    if blocks is None:
        block_labels = tuple(f"row-{index}" for index in range(n))
    else:
        block_labels = _labels(blocks, n, "blocks")

    ordered_groups = tuple(dict.fromkeys(group_labels))
    group_array = np.asarray(group_labels, dtype=object)
    block_array = np.asarray(block_labels, dtype=object)
    rows: list[TransferGainUncertaintyRow] = []
    point_gains: list[float] = []
    alpha = 1.0 - float(confidence_level)

    for group_id in ordered_groups:
        mask = group_array == group_id
        local_gain = gain[mask]
        local_weight = weight[mask]
        local_blocks = tuple(str(value) for value in block_array[mask])
        ordered_blocks = tuple(dict.fromkeys(local_blocks))
        point = _weighted_mean(local_gain, local_weight)
        point_gains.append(point)
        estimable = len(ordered_blocks) >= minimum_blocks_per_group
        if not estimable:
            rows.append(
                TransferGainUncertaintyRow(
                    group_id=group_id,
                    row_count=int(np.count_nonzero(mask)),
                    block_count=len(ordered_blocks),
                    total_weight=float(np.sum(local_weight)),
                    mean_gain=float(point),
                    lower_bound=None,
                    upper_bound=None,
                    status="unavailable",
                    estimable=False,
                )
            )
            continue

        samples = _bootstrap_group_mean(
            local_gain,
            local_weight,
            local_blocks,
            draws=bootstrap_draws,
            seed=_stable_group_seed(seed, group_id),
        )
        lower, upper = np.quantile(samples, [alpha / 2.0, 1.0 - alpha / 2.0])
        if lower > gain_tolerance:
            status = "robust_positive"
        elif upper <= gain_tolerance:
            status = "robust_nonpositive"
        else:
            status = "uncertain"
        rows.append(
            TransferGainUncertaintyRow(
                group_id=group_id,
                row_count=int(np.count_nonzero(mask)),
                block_count=len(ordered_blocks),
                total_weight=float(np.sum(local_weight)),
                mean_gain=float(point),
                lower_bound=float(lower),
                upper_bound=float(upper),
                status=status,
                estimable=True,
            )
        )

    statuses = [row.status for row in rows]
    unavailable = statuses.count("unavailable")
    uncertain = statuses.count("uncertain")
    positive = statuses.count("robust_positive")
    nonpositive = statuses.count("robust_nonpositive")
    if unavailable:
        robust_category = "unavailable"
    elif positive == len(rows):
        robust_category = "robust_generalizing"
    elif nonpositive == len(rows):
        robust_category = "robust_non_generalizing"
    elif uncertain:
        robust_category = "uncertain"
    else:
        robust_category = "mixed"

    return BlockAwareTransferAudit(
        row_count=n,
        group_count=len(rows),
        confidence_level=float(confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        seed=int(seed),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        row_independence_assumed=bool(row_independence_assumed),
        mean_gain=_weighted_mean(gain, weight),
        point_transfer_category=classify_independent_gains(point_gains, tolerance=gain_tolerance),
        robust_transfer_category=robust_category,
        robust_admissible=bool(robust_category == "robust_generalizing"),
        unavailable_group_count=int(unavailable),
        uncertain_group_count=int(uncertain),
        robust_positive_group_count=int(positive),
        robust_nonpositive_group_count=int(nonpositive),
        pooled_mean_can_override_group_failure=False,
        point_estimate_can_override_uncertainty=False,
        aggregate_confidence_score_emitted=False,
        groups=tuple(rows),
    )
