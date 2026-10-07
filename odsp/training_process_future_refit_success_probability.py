"""Lower confidence bound for future-refit success probability.

This route is distinct from both fixed-set all-refit robustness and the qualified
v5 process-mean route.  Its estimand is

    p_success = P_R(all required validation-population gains for one future
                    refit drawn from the frozen training process exceed the
                    declared tolerance).

The one-sided error budget is split into two prospective stages.

1. Validation uncertainty: validation blocks are bootstrapped while the observed
   refits are held fixed.  Every observed refit x group x contrast cell belongs
   to one simultaneous one-sided max-t family.  Within a validation group, the
   same block draw is shared across every refit and contrast.

2. Training-process sampling: a refit is counted as a certified success only
   when every required simultaneous validation lower bound exceeds the tolerance.
   The certified count K is then passed to an exact one-sided binomial
   (Clopper-Pearson) lower bound.

On the simultaneous validation coverage event the certified count cannot exceed
the number of truly successful observed refits.  The exact binomial lower bound
is monotone in K, so a union bound controls overall overstatement by
alpha_validation + alpha_process.

The raw numerical routine does not establish that the supplied refits are iid
draws from a prospectively frozen process.  A future primary wrapper must verify
that provenance separately.
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
)
from .information_transfer import (
    InformationLevelScore,
    InformationTransferStep,
    validate_information_filtration,
)
from .positive_transfer_bootstrap_t import (
    one_sided_lower_bounds,
    one_sided_lower_max_t_critical_value,
)
from .refit_information_transfer import (
    RefitInformationLevelScores,
    _labels,
    _refit_ids,
    _score_matrices,
    _weights,
)
from .training_process_positive_transfer import _process_identity


METHOD_VERSION = "training_process_future_refit_success_probability_v1"
VALIDATION_ALPHA = 0.025
PROCESS_ALPHA = 0.025
OVERALL_ALPHA = VALIDATION_ALPHA + PROCESS_ALPHA


@dataclass(frozen=True)
class FutureRefitSuccessCell:
    refit_id: str
    group: object
    contrast: str
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float | None
    studentizing_standard_error: float | None
    lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FutureRefitSuccessRefit:
    refit_id: str
    certified_success: bool
    all_required_cells_estimable: bool
    robust_positive_cell_count: int
    required_cell_count: int
    minimum_lower_bound: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FutureRefitSuccessProbabilityAudit:
    schema_version: int
    method_version: str
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_count: int
    refit_ids: tuple[str, ...]
    group_count: int
    contrast_count: int
    required_cell_count_per_refit: int
    total_validation_family_cell_count: int
    validation_alpha: float
    validation_familywise_lower_confidence_level: float
    process_alpha: float
    overall_one_sided_alpha: float
    bootstrap_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    validation_bootstrap_t_critical_value: float | None
    certified_success_count: int
    uncertified_refit_count: int
    all_observed_refits_evaluable: bool
    future_refit_success_probability_lower_bound: float
    maximum_possible_lower_bound_if_all_observed_refits_certified: float
    observed_certified_success_fraction: float
    validation_blocks_resampled: bool
    training_refits_resampled_in_validation_stage: bool
    same_validation_block_draw_shared_across_refits_and_contrasts_within_group: bool
    validation_groups_resampled_independently: bool
    exact_binomial_process_bound_used: bool
    bonferroni_error_budget_used: bool
    process_mean_is_estimand: bool
    individual_future_refit_success_probability_is_estimand: bool
    all_future_refits_positive_claimed: bool
    original_training_source_population_generalization_claimed: bool
    fixed_set_intersection_used: bool
    historical_fixed_set_results_reclassified: bool
    cells: tuple[FutureRefitSuccessCell, ...]
    per_refit: tuple[FutureRefitSuccessRefit, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["refit_ids"] = list(self.refit_ids)
        payload["cells"] = [row.as_dict() for row in self.cells]
        payload["per_refit"] = [row.as_dict() for row in self.per_refit]
        return payload


@dataclass(frozen=True)
class FutureRefitSuccessProbabilityInformationCertification:
    schema_version: int
    method_version: str
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    information_filtration_validated: bool
    success_definition: str
    audit: FutureRefitSuccessProbabilityAudit

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "method_version": self.method_version,
            "score_name": self.score_name,
            "levels": list(self.levels),
            "steps": [row.as_dict() for row in self.steps],
            "information_filtration_validated": self.information_filtration_validated,
            "success_definition": self.success_definition,
            "audit": self.audit.as_dict(),
        }


def _integer(value: object, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    out = int(value)
    if out < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return out


def _stable_group_seed(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|future-refit-success-probability-v1|blocks|{group!r}".encode(
            "utf-8"
        )
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _binomial_survival(success_threshold: int, total: int, probability: float) -> float:
    """P[X >= success_threshold] for X~Binomial(total, probability)."""

    if success_threshold <= 0:
        return 1.0
    if success_threshold > total:
        return 0.0
    p = float(probability)
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    q = 1.0 - p
    return float(
        sum(
            math.comb(total, value)
            * (p ** value)
            * (q ** (total - value))
            for value in range(success_threshold, total + 1)
        )
    )


def exact_binomial_success_probability_lower_bound(
    successes: int,
    total: int,
    *,
    alpha: float = PROCESS_ALPHA,
) -> float:
    """One-sided exact Clopper-Pearson lower bound for a binomial probability."""

    k = _integer(successes, name="successes", minimum=0)
    n = _integer(total, name="total", minimum=1)
    if k > n:
        raise ValueError("successes must not exceed total")
    if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between zero and one")
    if k == 0:
        return 0.0
    if k == n:
        return float(alpha ** (1.0 / n))

    # The exact lower limit solves P_p[X >= k] = alpha.  The survival
    # probability is monotone increasing in p.
    lower = 0.0
    upper = float(k) / float(n)
    if _binomial_survival(k, n, upper) < alpha:
        upper = 1.0
    for _ in range(100):
        midpoint = 0.5 * (lower + upper)
        if _binomial_survival(k, n, midpoint) < alpha:
            lower = midpoint
        else:
            upper = midpoint
    return float(0.5 * (lower + upper))


def _validate_error_budget(
    validation_alpha: float,
    process_alpha: float,
) -> tuple[float, float, float]:
    values = (float(validation_alpha), float(process_alpha))
    if any(not math.isfinite(value) or not 0.0 < value < 1.0 for value in values):
        raise ValueError("validation_alpha and process_alpha must lie in (0, 1)")
    overall = values[0] + values[1]
    if not overall < 1.0:
        raise ValueError("validation_alpha + process_alpha must be less than one")
    return values[0], values[1], overall


def certify_future_refit_success_probability_v1(
    row_gain_by_refit: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    validation_alpha: float = VALIDATION_ALPHA,
    process_alpha: float = PROCESS_ALPHA,
    bootstrap_draws: int = 4000,
    seed: int = 20261016,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> FutureRefitSuccessProbabilityAudit:
    """Return a lower bound for one future refit's all-cell success probability."""

    process_id, process_sha = _process_identity(
        training_process_id,
        training_process_manifest_sha256,
    )
    gain = np.asarray(row_gain_by_refit, dtype=float)
    if gain.ndim == 2:
        gain = gain[:, :, None]
    if gain.ndim != 3 or 0 in gain.shape:
        raise ValueError(
            "row_gain_by_refit must be non-empty [refit, row, contrast]"
        )
    if np.isnan(gain).any() or np.isposinf(gain).any():
        raise ValueError(
            "row gains may contain finite values or -inf, but not NaN or +inf"
        )

    refit_count, n, contrast_count = gain.shape
    ids, order = _refit_ids(refit_ids, refit_count)
    gain = gain[order]
    group = _labels(groups, n, name="groups")
    block = _labels(blocks, n, name="blocks")
    weight = _weights(sample_weight, n)

    validation_alpha, process_alpha, overall_alpha = _validate_error_budget(
        validation_alpha,
        process_alpha,
    )
    bootstrap_draws = _integer(
        bootstrap_draws, name="bootstrap_draws", minimum=500
    )
    seed = _integer(seed, name="seed", minimum=0)
    minimum_refits = _integer(
        minimum_refits, name="minimum_refits", minimum=2
    )
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group,
        name="minimum_blocks_per_group",
        minimum=2,
    )
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0.0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    if contrast_names is None:
        names = tuple(f"contrast-{index:03d}" for index in range(contrast_count))
    else:
        if len(contrast_names) != contrast_count:
            raise ValueError("contrast_names must contain one name per contrast")
        names = tuple(str(value).strip() for value in contrast_names)
        if any(not value for value in names) or len(set(names)) != len(names):
            raise ValueError("contrast_names must be non-empty and unique")

    group_order = tuple(
        sorted(
            set(group.tolist()),
            key=lambda value: (type(value).__name__, repr(value)),
        )
    )
    enough_refits = refit_count >= minimum_refits

    # Records are keyed by (refit position, group position, contrast position).
    records: dict[tuple[int, int, int], dict[str, object]] = {}
    eligible_keys: list[tuple[int, int, int]] = []
    sampled_mean_columns: list[np.ndarray] = []
    sampled_se_columns: list[np.ndarray] = []
    point_means: list[float] = []
    point_ses: list[float] = []

    for group_index, group_value in enumerate(group_order):
        mask = group == group_value
        local_gain = gain[:, mask, :]
        local_weight = weight[mask]
        local_block = block[mask]
        positive = local_weight > 0
        if not np.any(positive):
            raise ValueError(f"group {group_value!r} has zero positive score weight")

        block_order = tuple(
            sorted(
                set(local_block[positive].tolist()),
                key=lambda value: (type(value).__name__, repr(value)),
            )
        )
        block_count = len(block_order)
        finite = np.all(np.isfinite(local_gain[:, positive, :]), axis=1)
        block_weight = np.empty(block_count, dtype=float)
        block_numerator = np.zeros(
            (block_count, refit_count, contrast_count), dtype=float
        )
        safe_gain = np.where(np.isfinite(local_gain), local_gain, 0.0)
        for block_index, block_value in enumerate(block_order):
            block_mask = (local_block == block_value) & positive
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0.0:
                raise ValueError(
                    "every declared positive-support block must have positive mass"
                )
            block_weight[block_index] = mass
            block_numerator[block_index] = np.sum(
                safe_gain[:, block_mask, :]
                * local_weight[block_mask][None, :, None],
                axis=1,
            )

        finite_pairs = [
            (refit_index, contrast_index)
            for refit_index in range(refit_count)
            for contrast_index in range(contrast_count)
            if bool(finite[refit_index, contrast_index])
        ]
        pair_position = {pair: index for index, pair in enumerate(finite_pairs)}

        point = np.full((refit_count, contrast_count), np.nan, dtype=float)
        se = np.full((refit_count, contrast_count), np.nan, dtype=float)
        sampled_means: np.ndarray | None = None
        sampled_ses: np.ndarray | None = None

        if finite_pairs:
            flat = np.column_stack(
                [
                    block_numerator[:, refit_index, contrast_index]
                    for refit_index, contrast_index in finite_pairs
                ]
            )
            local_point, local_se = ratio_mean_and_cluster_se(flat, block_weight)
            for position, pair in enumerate(finite_pairs):
                point[pair] = float(local_point[position])
                se[pair] = float(local_se[position])

            if block_count >= minimum_blocks_per_group:
                rng = np.random.default_rng(
                    _stable_group_seed(seed, group_value)
                )
                sampled_blocks = rng.integers(
                    0,
                    block_count,
                    size=(bootstrap_draws, block_count),
                )
                sampled_means, sampled_ses = (
                    bootstrap_ratio_mean_and_cluster_se(
                        flat,
                        block_weight,
                        sampled_blocks,
                    )
                )

        for refit_index, refit_id in enumerate(ids):
            for contrast_index, contrast in enumerate(names):
                key = (refit_index, group_index, contrast_index)
                is_finite = bool(finite[refit_index, contrast_index])
                estimable = bool(
                    is_finite
                    and enough_refits
                    and block_count >= minimum_blocks_per_group
                )
                records[key] = {
                    "refit_id": refit_id,
                    "group": group_value,
                    "contrast": contrast,
                    "row_count": int(np.count_nonzero(mask)),
                    "block_count": block_count,
                    "total_weight": float(np.sum(local_weight[positive])),
                    "mean_gain": (
                        float(point[refit_index, contrast_index])
                        if is_finite
                        else None
                    ),
                    "studentizing_standard_error": (
                        float(se[refit_index, contrast_index])
                        if is_finite
                        else None
                    ),
                    "lower_bound": None,
                    "status": "unavailable",
                    "estimable": estimable,
                }
                if estimable:
                    assert sampled_means is not None and sampled_ses is not None
                    position = pair_position[(refit_index, contrast_index)]
                    eligible_keys.append(key)
                    sampled_mean_columns.append(sampled_means[:, position])
                    sampled_se_columns.append(sampled_ses[:, position])
                    point_means.append(float(point[refit_index, contrast_index]))
                    point_ses.append(float(se[refit_index, contrast_index]))

    critical: float | None = None
    if sampled_mean_columns:
        bootstrap_mean = np.column_stack(sampled_mean_columns)
        bootstrap_se = np.column_stack(sampled_se_columns)
        point_mean = np.asarray(point_means, dtype=float)
        point_se = np.asarray(point_ses, dtype=float)
        critical = one_sided_lower_max_t_critical_value(
            bootstrap_mean,
            bootstrap_se,
            point_mean,
            confidence_level=1.0 - validation_alpha,
        )
        lower = one_sided_lower_bounds(point_mean, point_se, critical)
        for column, key in enumerate(eligible_keys):
            lo = float(lower[column])
            records[key]["lower_bound"] = lo
            records[key]["status"] = (
                "robust_positive"
                if lo > gain_tolerance
                else "not_robust_positive"
            )

    required_per_refit = len(group_order) * contrast_count
    per_refit: list[FutureRefitSuccessRefit] = []
    certified_count = 0
    for refit_index, refit_id in enumerate(ids):
        local_records = [
            records[(refit_index, group_index, contrast_index)]
            for group_index in range(len(group_order))
            for contrast_index in range(contrast_count)
        ]
        all_estimable = all(bool(row["estimable"]) for row in local_records)
        robust_count = sum(
            row["status"] == "robust_positive" for row in local_records
        )
        certified = bool(
            all_estimable and robust_count == required_per_refit
        )
        certified_count += int(certified)
        lower_values = [
            float(row["lower_bound"])
            for row in local_records
            if row["lower_bound"] is not None
        ]
        per_refit.append(
            FutureRefitSuccessRefit(
                refit_id=refit_id,
                certified_success=certified,
                all_required_cells_estimable=all_estimable,
                robust_positive_cell_count=robust_count,
                required_cell_count=required_per_refit,
                minimum_lower_bound=(
                    min(lower_values)
                    if len(lower_values) == required_per_refit
                    else None
                ),
            )
        )

    probability_lower = exact_binomial_success_probability_lower_bound(
        certified_count,
        refit_count,
        alpha=process_alpha,
    )
    maximum_possible = exact_binomial_success_probability_lower_bound(
        refit_count,
        refit_count,
        alpha=process_alpha,
    )
    ordered_cells = tuple(
        FutureRefitSuccessCell(**records[key])
        for key in sorted(records)
    )

    return FutureRefitSuccessProbabilityAudit(
        schema_version=1,
        method_version=METHOD_VERSION,
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        inference_target=(
            "probability that one future iid refit drawn from the frozen "
            "training process has every required validation-population gain "
            "above the declared tolerance"
        ),
        refit_count=refit_count,
        refit_ids=ids,
        group_count=len(group_order),
        contrast_count=contrast_count,
        required_cell_count_per_refit=required_per_refit,
        total_validation_family_cell_count=(
            refit_count * required_per_refit
        ),
        validation_alpha=validation_alpha,
        validation_familywise_lower_confidence_level=1.0 - validation_alpha,
        process_alpha=process_alpha,
        overall_one_sided_alpha=overall_alpha,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        validation_bootstrap_t_critical_value=critical,
        certified_success_count=certified_count,
        uncertified_refit_count=refit_count - certified_count,
        all_observed_refits_evaluable=all(
            row.all_required_cells_estimable for row in per_refit
        ),
        future_refit_success_probability_lower_bound=probability_lower,
        maximum_possible_lower_bound_if_all_observed_refits_certified=(
            maximum_possible
        ),
        observed_certified_success_fraction=(
            float(certified_count) / float(refit_count)
        ),
        validation_blocks_resampled=True,
        training_refits_resampled_in_validation_stage=False,
        same_validation_block_draw_shared_across_refits_and_contrasts_within_group=True,
        validation_groups_resampled_independently=True,
        exact_binomial_process_bound_used=True,
        bonferroni_error_budget_used=True,
        process_mean_is_estimand=False,
        individual_future_refit_success_probability_is_estimand=True,
        all_future_refits_positive_claimed=False,
        original_training_source_population_generalization_claimed=False,
        fixed_set_intersection_used=False,
        historical_fixed_set_results_reclassified=False,
        cells=ordered_cells,
        per_refit=tuple(per_refit),
    )


def certify_training_process_future_refit_success_probability_v1(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    validation_alpha: float = VALIDATION_ALPHA,
    process_alpha: float = PROCESS_ALPHA,
    bootstrap_draws: int = 4000,
    seed: int = 20261016,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> FutureRefitSuccessProbabilityInformationCertification:
    """Certify the initial two-contrast future-refit success-probability route."""

    name = str(score_name).strip()
    if not name:
        raise ValueError("score_name must be non-empty")

    rows, matrices = _score_matrices(levels)
    if len(rows) != 3:
        raise ValueError(
            "future-refit success-probability v1 is frozen to exactly "
            "three ordered information levels (two contrasts)"
        )
    refit_count, n = matrices[0].shape
    ids, order = _refit_ids(refit_ids, refit_count)
    matrices = tuple(matrix[order] for matrix in matrices)
    weight = _weights(sample_weight, n)
    positive = weight > 0

    for row, matrix in zip(rows[:-1], matrices[:-1]):
        if not np.isfinite(matrix[:, positive]).all():
            raise ValueError(
                f"comparator level {row.name!r} must be finite on every "
                "positive-weight row for every refit"
            )

    steps = validate_information_filtration(
        [
            InformationLevelScore(row.name, row.information, [0.0])
            for row in rows
        ]
    )
    if len(steps) != 2:
        raise AssertionError("three ordered levels must produce two steps")

    gains = np.stack(
        [
            matrices[index + 1] - matrices[index]
            for index in range(len(steps))
        ],
        axis=2,
    )
    audit = certify_future_refit_success_probability_v1(
        gains,
        groups,
        blocks=blocks,
        refit_ids=ids,
        training_process_id=training_process_id,
        training_process_manifest_sha256=training_process_manifest_sha256,
        contrast_names=tuple(
            f"{step.lower_level}->{step.upper_level}" for step in steps
        ),
        sample_weight=weight,
        validation_alpha=validation_alpha,
        process_alpha=process_alpha,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    return FutureRefitSuccessProbabilityInformationCertification(
        schema_version=1,
        method_version=METHOD_VERSION,
        score_name=name,
        levels=tuple(row.name for row in rows),
        steps=steps,
        information_filtration_validated=True,
        success_definition=(
            "one future refit has gain above tolerance in every validation "
            "group for both ordered information steps"
        ),
        audit=audit,
    )
