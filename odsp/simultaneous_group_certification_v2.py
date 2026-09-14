"""Genuine block bootstrap-t familywise certification across validation groups.

Version 1 of the ODSP simultaneous-group audit is retained unchanged for frozen
receipt provenance.  This version-2 method is prospective.  It recomputes a
cluster ratio standard error inside every outer bootstrap draw and uses those
replicate-specific studentizers to form a two-sided max-t family.

Independent validation groups are resampled independently.  Within a group the
caller-declared blocks are the exchangeable sampling units.  Upstream learner
refit uncertainty remains outside this validation-sample confidence procedure.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .bootstrap_t import (
    bootstrap_ratio_mean_and_cluster_se,
    ratio_mean_and_cluster_se,
    simultaneous_bootstrap_t_bounds,
    studentized_max_t_critical_value,
)
from .simultaneous_group_certification import (
    _category,
    _interval_status,
    _labels,
    _weighted_mean,
    _weights,
)
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class SimultaneousGroupCertificationV2Row:
    group_id: str
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float
    bootstrap_standard_error: float | None
    studentizing_standard_error: float | None
    marginal_lower_bound: float | None
    marginal_upper_bound: float | None
    bonferroni_lower_bound: float | None
    bonferroni_upper_bound: float | None
    bootstrap_t_lower_bound: float | None
    bootstrap_t_upper_bound: float | None
    marginal_status: str
    bonferroni_status: str
    bootstrap_t_status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SimultaneousGroupCertificationV2Audit:
    schema_version: int
    row_count: int
    group_count: int
    familywise_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    row_independence_assumed: bool
    mean_gain: float
    point_transfer_category: str
    marginal_interval_category: str
    bonferroni_transfer_category: str
    bootstrap_t_transfer_category: str
    simultaneous_admissible: bool
    bootstrap_t_critical_value: float | None
    bootstrap_t_method: str
    replicate_studentization_recomputed: bool
    point_studentizer: str
    bonferroni_per_tail_alpha: float
    unavailable_group_count: int
    bootstrap_t_uncertain_group_count: int
    bootstrap_t_robust_positive_group_count: int
    bootstrap_t_robust_nonpositive_group_count: int
    pooled_mean_can_override_group_failure: bool
    marginal_interval_can_override_simultaneous_failure: bool
    bonferroni_is_primary: bool
    upstream_refit_uncertainty_included: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[SimultaneousGroupCertificationV2Row, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


def _stable_seed(seed: int, group_id: str) -> int:
    digest = hashlib.sha256(
        f"{seed}|simultaneous-group-v2|bootstrap-t|{group_id}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _block_arrays(
    gain: np.ndarray,
    weight: np.ndarray,
    block_labels: Sequence[object],
) -> tuple[np.ndarray, np.ndarray]:
    labels = np.asarray(list(block_labels), dtype=object)
    ordered = tuple(sorted(set(labels.tolist()), key=str))
    block_weight: list[float] = []
    block_numerator: list[float] = []
    for block_id in ordered:
        mask = labels == block_id
        local_weight = weight[mask]
        mass = float(np.sum(local_weight))
        if mass <= 0:
            continue
        block_weight.append(mass)
        block_numerator.append(float(np.sum(gain[mask] * local_weight)))
    if not block_weight:
        raise ValueError("every validation group must contain positive-mass blocks")
    return (
        np.asarray(block_numerator, dtype=float)[:, None],
        np.asarray(block_weight, dtype=float),
    )


def audit_simultaneous_group_certification_v2(
    row_gain: Sequence[float],
    groups: Sequence[object],
    *,
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260914,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> SimultaneousGroupCertificationV2Audit:
    """Certify independent-group gain signs with replicate-studentized max-t.

    The familywise interpretation is conditional on the supplied held-out
    predictions and on the declared block exchangeability/group-independence
    assumptions.  The procedure does not refit an upstream predictive model.
    """

    gain = np.asarray(row_gain, dtype=float)
    if gain.ndim != 1 or gain.size == 0 or not np.isfinite(gain).all():
        raise ValueError("row_gain must be a non-empty finite one-dimensional vector")
    n = int(gain.size)
    group_labels = _labels(groups, n, "groups")
    weight = _weights(sample_weight, n)
    if not math.isfinite(familywise_confidence_level) or not 0 < familywise_confidence_level < 1:
        raise ValueError("familywise_confidence_level must lie strictly between zero and one")
    if isinstance(bootstrap_draws, bool) or not isinstance(bootstrap_draws, int) or bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be an integer >= 500")
    if (
        isinstance(minimum_blocks_per_group, bool)
        or not isinstance(minimum_blocks_per_group, int)
        or minimum_blocks_per_group < 2
    ):
        raise ValueError("minimum_blocks_per_group must be an integer >= 2")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    row_independence_assumed = blocks is None
    if blocks is None:
        block_labels = tuple(f"row-{index:09d}" for index in range(n))
    else:
        block_labels = _labels(blocks, n, "blocks")

    ordered_groups = tuple(sorted(set(group_labels)))
    group_array = np.asarray(group_labels, dtype=object)
    block_array = np.asarray(block_labels, dtype=object)
    alpha = 1.0 - familywise_confidence_level
    bonf_tail = alpha / (2.0 * len(ordered_groups))

    intermediate: list[dict[str, object]] = []
    point_gains: list[float] = []
    estimable_indices: list[int] = []
    bootstrap_means: list[np.ndarray] = []
    bootstrap_ses: list[np.ndarray] = []
    point_means: list[float] = []
    point_ses: list[float] = []

    for group_id in ordered_groups:
        mask = group_array == group_id
        local_gain = gain[mask]
        local_weight = weight[mask]
        local_blocks = block_array[mask]
        point = _weighted_mean(local_gain, local_weight)
        point_gains.append(point)
        numerator, block_weight = _block_arrays(
            local_gain,
            local_weight,
            local_blocks,
        )
        block_count = int(block_weight.size)
        record: dict[str, object] = {
            "group_id": group_id,
            "row_count": int(np.count_nonzero(mask)),
            "block_count": block_count,
            "total_weight": float(np.sum(local_weight)),
            "mean_gain": float(point),
            "estimable": bool(block_count >= minimum_blocks_per_group),
        }
        if block_count < minimum_blocks_per_group:
            record.update(
                bootstrap_standard_error=None,
                studentizing_standard_error=None,
                marginal_lower_bound=None,
                marginal_upper_bound=None,
                bonferroni_lower_bound=None,
                bonferroni_upper_bound=None,
                bootstrap_t_lower_bound=None,
                bootstrap_t_upper_bound=None,
                marginal_status="unavailable",
                bonferroni_status="unavailable",
                bootstrap_t_status="unavailable",
            )
            intermediate.append(record)
            continue

        local_point, local_point_se = ratio_mean_and_cluster_se(
            numerator,
            block_weight,
        )
        if abs(float(local_point[0]) - point) > 1e-12:
            raise AssertionError("block ratio point estimate disagrees with row-weighted mean")
        rng = np.random.default_rng(_stable_seed(seed, group_id))
        sampled = rng.integers(
            0,
            block_count,
            size=(bootstrap_draws, block_count),
        )
        sample_mean, sample_se = bootstrap_ratio_mean_and_cluster_se(
            numerator,
            block_weight,
            sampled,
        )
        samples = sample_mean[:, 0]
        studentizers = sample_se[:, 0]
        bootstrap_sd = float(np.std(samples, ddof=1))
        marginal_lower, marginal_upper = np.quantile(
            samples,
            [alpha / 2.0, 1.0 - alpha / 2.0],
        )
        bonf_lower, bonf_upper = np.quantile(
            samples,
            [bonf_tail, 1.0 - bonf_tail],
        )
        record.update(
            bootstrap_standard_error=bootstrap_sd,
            studentizing_standard_error=float(local_point_se[0]),
            marginal_lower_bound=float(marginal_lower),
            marginal_upper_bound=float(marginal_upper),
            bonferroni_lower_bound=float(bonf_lower),
            bonferroni_upper_bound=float(bonf_upper),
            bootstrap_t_lower_bound=None,
            bootstrap_t_upper_bound=None,
            marginal_status=_interval_status(
                float(marginal_lower), float(marginal_upper), gain_tolerance
            ),
            bonferroni_status=_interval_status(
                float(bonf_lower), float(bonf_upper), gain_tolerance
            ),
            bootstrap_t_status="pending",
        )
        estimable_indices.append(len(intermediate))
        bootstrap_means.append(samples)
        bootstrap_ses.append(studentizers)
        point_means.append(float(local_point[0]))
        point_ses.append(float(local_point_se[0]))
        intermediate.append(record)

    critical: float | None = None
    if bootstrap_means:
        mean_matrix = np.column_stack(bootstrap_means)
        se_matrix = np.column_stack(bootstrap_ses)
        point_vector = np.asarray(point_means, dtype=float)
        point_se_vector = np.asarray(point_ses, dtype=float)
        critical = studentized_max_t_critical_value(
            mean_matrix,
            se_matrix,
            point_vector,
            confidence_level=familywise_confidence_level,
        )
        lower, upper = simultaneous_bootstrap_t_bounds(
            point_vector,
            point_se_vector,
            critical,
        )
        for matrix_index, record_index in enumerate(estimable_indices):
            lo = float(lower[matrix_index])
            hi = float(upper[matrix_index])
            intermediate[record_index]["bootstrap_t_lower_bound"] = lo
            intermediate[record_index]["bootstrap_t_upper_bound"] = hi
            intermediate[record_index]["bootstrap_t_status"] = _interval_status(
                lo,
                hi,
                gain_tolerance,
            )

    rows = tuple(
        SimultaneousGroupCertificationV2Row(**record)
        for record in intermediate
    )
    marginal_category = _category([row.marginal_status for row in rows])
    bonf_category = _category([row.bonferroni_status for row in rows])
    bootstrap_t_category = _category([row.bootstrap_t_status for row in rows])
    statuses = [row.bootstrap_t_status for row in rows]

    return SimultaneousGroupCertificationV2Audit(
        schema_version=2,
        row_count=n,
        group_count=len(rows),
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        row_independence_assumed=bool(row_independence_assumed),
        mean_gain=_weighted_mean(gain, weight),
        point_transfer_category=classify_independent_gains(
            point_gains,
            tolerance=gain_tolerance,
        ),
        marginal_interval_category=marginal_category,
        bonferroni_transfer_category=bonf_category,
        bootstrap_t_transfer_category=bootstrap_t_category,
        simultaneous_admissible=bool(
            bootstrap_t_category == "robust_generalizing"
        ),
        bootstrap_t_critical_value=critical,
        bootstrap_t_method="replicate_studentized_cluster_ratio_bootstrap_t",
        replicate_studentization_recomputed=True,
        point_studentizer="cluster_ratio_influence_standard_error",
        bonferroni_per_tail_alpha=float(bonf_tail),
        unavailable_group_count=statuses.count("unavailable"),
        bootstrap_t_uncertain_group_count=statuses.count("uncertain"),
        bootstrap_t_robust_positive_group_count=statuses.count("robust_positive"),
        bootstrap_t_robust_nonpositive_group_count=statuses.count(
            "robust_nonpositive"
        ),
        pooled_mean_can_override_group_failure=False,
        marginal_interval_can_override_simultaneous_failure=False,
        bonferroni_is_primary=False,
        upstream_refit_uncertainty_included=False,
        aggregate_confidence_score_emitted=False,
        groups=rows,
    )
