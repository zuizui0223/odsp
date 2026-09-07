"""Refit-ensemble sensitivity plus held-out block uncertainty.

Each Monte Carlo draw selects ONE supplied refit for all validation groups, then
resamples validation blocks independently within groups. The spread is over the
empirical refit mixture, not the standard error of an average of R fitted models.
These are conditional sensitivity intervals, not exact population guarantees.
No fitting, hyperparameter selection, or calibration is performed on these rows.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .simultaneous_group_certification import (
    SimultaneousGroupCertificationAudit,
    _category,
    _interval_status,
    _stable_seed,
    audit_simultaneous_group_certification,
)
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class ModelRefitTransferRow:
    group_id: str
    row_count: int
    block_count: int
    ensemble_mean_gain: float
    refit_mean_gains: tuple[float, ...]
    positive_refit_count: int
    nonpositive_refit_count: int
    between_refit_standard_deviation: float
    nested_standard_error: float | None
    nested_marginal_lower_bound: float | None
    nested_marginal_upper_bound: float | None
    nested_max_t_lower_bound: float | None
    nested_max_t_upper_bound: float | None
    nested_marginal_status: str
    nested_max_t_status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ModelRefitTransferAudit:
    row_count: int
    group_count: int
    refit_count: int
    refit_ids: tuple[str, ...]
    reference_refit_id: str
    familywise_confidence_level: float
    nested_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    point_transfer_category: str
    reference_fit_category: str
    refit_point_categories: tuple[str, ...]
    refit_sign_stability: str
    nested_marginal_category: str
    refit_aware_category: str
    refit_aware_admissible: bool
    nested_max_t_critical_value: float | None
    unavailable_group_count: int
    selected_refit_draw_counts: tuple[int, ...]
    identical_refits: bool
    same_selected_refit_shared_across_groups: bool
    reference_fit_can_override_refit_aware_failure: bool
    pooled_gain_can_override_group_failure: bool
    automatic_refit_scheme_inference: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[ModelRefitTransferRow, ...]
    reference_audit: SimultaneousGroupCertificationAudit

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload['groups'] = [row.as_dict() for row in self.groups]
        payload['reference_audit'] = self.reference_audit.as_dict()
        return payload


def _labels(values: Sequence[object], n: int, name: str) -> tuple[str, ...]:
    if len(values) != n:
        raise ValueError(f'{name} must contain one label per corresponding axis entry')
    if any(value is None for value in values):
        raise ValueError(f'{name} labels must not be missing')
    labels = tuple(str(value).strip() for value in values)
    if any(not value for value in labels):
        raise ValueError(f'{name} labels must be non-empty')
    return labels


def _integer(value: int, name: str, lower: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < lower:
        raise ValueError(f'{name} must be an integer >= {lower}')
    return int(value)


def _shared_refit_draws(seed: int, count: int, draws: int) -> np.ndarray:
    digest = hashlib.sha256(f'{seed}|model-refit|shared'.encode('utf-8')).digest()
    refit_seed = int.from_bytes(digest[:8], 'little')
    return np.random.default_rng(refit_seed).integers(0, count, size=draws)


def _nested_group_samples(
    block_weighted_gain: np.ndarray,
    block_weight: np.ndarray,
    selected_refits: np.ndarray,
    *,
    seed: int,
) -> np.ndarray:
    """Select paired numerator/denominator blocks; retain shared refit identity."""
    count = block_weight.size
    indices = np.random.default_rng(seed).integers(
        0, count, size=(selected_refits.size, count)
    )
    numerator = np.sum(block_weighted_gain[selected_refits[:, None], indices], axis=1)
    denominator = np.sum(block_weight[indices], axis=1)
    result = numerator / denominator
    if not np.isfinite(result).all():
        raise ValueError('nested resampling produced non-finite gains')
    return result


def audit_model_refit_transfer_uncertainty(
    refit_row_gain: Sequence[Sequence[float]],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object] | None = None,
    reference_refit_id: object | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    nested_draws: int = 4000,
    seed: int = 20260906,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> ModelRefitTransferAudit:
    """Audit an aligned [refit, held-out row] gain matrix without refitting.

    Refit IDs are sorted before sampling. The reference defaults to the first ID
    in this canonical order; declare ``reference_refit_id`` to choose another.
    IDs must be unique, but this does NOT establish independence of model fits.
    Supply gains against the appropriately paired, training-only comparator.
    All rows must refer to the same untouched validation observations. Alignment,
    training/validation separation and scientific block validity remain the
    caller's responsibility: they cannot be inferred from a numeric gain matrix.

    Zero row weights are supported within positive-mass blocks. Empty-mass blocks
    or groups are rejected rather than generating undefined bootstrap ratios.
    No division by sqrt(refit_count) is applied to the nested spread.
    """
    gain = np.asarray(refit_row_gain, dtype=float)
    if gain.ndim != 2 or 0 in gain.shape or not np.isfinite(gain).all():
        raise ValueError('refit_row_gain must be a non-empty finite refits x rows matrix')
    count, n = gain.shape
    group_labels = _labels(groups, n, 'groups')
    block_labels = _labels(blocks, n, 'blocks')
    ids = (_labels(refit_ids, count, 'refit_ids') if refit_ids is not None else
           tuple(f'refit-{i:09d}' for i in range(count)))
    if len(set(ids)) != count:
        raise ValueError('refit_ids must be unique')
    order = np.argsort(np.asarray(ids), kind='stable')
    ids = tuple(ids[int(i)] for i in order)
    gain = gain[order]
    reference_id = ids[0] if reference_refit_id is None else str(reference_refit_id).strip()
    if reference_id not in ids:
        raise ValueError('reference_refit_id must identify one supplied refit')
    reference_index = ids.index(reference_id)
    nested_draws = _integer(nested_draws, 'nested_draws', 500)
    minimum_refits = _integer(minimum_refits, 'minimum_refits', 2)
    minimum_blocks_per_group = _integer(minimum_blocks_per_group, 'minimum_blocks_per_group', 2)
    seed = _integer(seed, 'seed', 0)
    if not math.isfinite(familywise_confidence_level) or not 0 < familywise_confidence_level < 1:
        raise ValueError('familywise_confidence_level must lie strictly between zero and one')
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError('gain_tolerance must be finite and non-negative')
    weight = np.ones(n) if sample_weight is None else np.asarray(sample_weight, dtype=float)
    if (weight.shape != (n,) or not np.isfinite(weight).all() or
            np.any(weight < 0) or not np.any(weight > 0)):
        raise ValueError('sample_weight must be finite, non-negative, aligned and positive in total')
    # Work with relative weights to avoid overflow from arbitrary weight units.
    weight = weight / np.max(weight)
    group_array = np.asarray(group_labels, dtype=object)
    block_array = np.asarray(block_labels, dtype=object)
    group_order = tuple(sorted(set(group_labels)))
    prepared = []
    refit_group_means = []
    for gid in group_order:
        mask = group_array == gid
        local_gain, local_weight = gain[:, mask], weight[mask]
        local_blocks = block_array[mask]
        block_order = tuple(sorted(set(local_blocks)))
        block_weights, numerators = [], []
        for bid in block_order:
            bm = local_blocks == bid
            bw = math.fsum(local_weight[bm].tolist())
            if bw <= 0:
                raise ValueError('every declared block must have positive total weight')
            block_weights.append(bw)
            # Sorting summands removes row-order effects without changing pairing.
            products = np.sort(local_gain[:, bm] * local_weight[bm], axis=1)
            numerators.append(np.sum(products, axis=1))
        bw_array = np.asarray(block_weights)
        numerator_array = np.column_stack(numerators)
        means = np.sum(numerator_array, axis=1) / np.sum(bw_array)
        if not np.isfinite(means).all():
            raise ValueError('weighted refit means are not finite')
        prepared.append((gid, int(mask.sum()), bw_array, numerator_array, means))
        refit_group_means.append(means)
    reference = audit_simultaneous_group_certification(
        gain[reference_index], group_labels, blocks=block_labels,
        sample_weight=weight, familywise_confidence_level=familywise_confidence_level,
        bootstrap_draws=nested_draws, seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group, gain_tolerance=gain_tolerance,
    )
    mean_matrix = np.column_stack(refit_group_means)
    categories = tuple(classify_independent_gains(row.tolist(), tolerance=gain_tolerance)
                       for row in mean_matrix)
    signs = mean_matrix > gain_tolerance
    sign_change = bool(np.any(np.any(signs, axis=0) & ~np.all(signs, axis=0)))
    stability = ('refit_sensitive' if sign_change else
                 'stable_generalizing' if np.all(signs) else
                 'stable_non_generalizing' if not np.any(signs) else 'stable_mixed')
    point_means = mean_matrix.mean(axis=0)
    selected = _shared_refit_draws(seed, count, nested_draws)
    enough_refits = count >= minimum_refits
    alpha = 1.0 - familywise_confidence_level
    records = []
    sample_columns, sample_points, sample_ses, eligible_indices = [], [], [], []
    for gid, rows, bw, bn, means in prepared:
        positive = int(np.count_nonzero(means > gain_tolerance))
        estimable = enough_refits and bw.size >= minimum_blocks_per_group
        record = dict(
            group_id=gid, row_count=rows, block_count=int(bw.size),
            ensemble_mean_gain=float(np.mean(means)),
            refit_mean_gains=tuple(float(x) for x in means),
            positive_refit_count=positive, nonpositive_refit_count=count-positive,
            between_refit_standard_deviation=float(np.std(means, ddof=0)),
            nested_standard_error=None, nested_marginal_lower_bound=None,
            nested_marginal_upper_bound=None, nested_max_t_lower_bound=None,
            nested_max_t_upper_bound=None, nested_marginal_status='unavailable',
            nested_max_t_status='unavailable', estimable=bool(estimable),
        )
        if estimable:
            samples = _nested_group_samples(bn, bw, selected, seed=_stable_seed(seed, gid))
            se = float(np.std(samples, ddof=1))
            lower, upper = np.quantile(samples, [alpha/2, 1-alpha/2])
            record.update(nested_standard_error=se,
                          nested_marginal_lower_bound=float(lower),
                          nested_marginal_upper_bound=float(upper),
                          nested_marginal_status=_interval_status(float(lower), float(upper), gain_tolerance))
            eligible_indices.append(len(records))
            sample_columns.append(samples)
            sample_points.append(float(np.mean(means)))
            sample_ses.append(se)
        records.append(record)
    critical = None
    if sample_columns:
        sample_matrix = np.column_stack(sample_columns)
        points, ses = np.asarray(sample_points), np.asarray(sample_ses)
        standardized = np.zeros_like(sample_matrix)
        nonzero = ses > 1e-15
        standardized[:, nonzero] = np.abs(sample_matrix[:, nonzero] - points[nonzero]) / ses[nonzero]
        critical = float(np.quantile(np.max(standardized, axis=1), familywise_confidence_level))
        for j, index in enumerate(eligible_indices):
            lower, upper = float(points[j] - critical*ses[j]), float(points[j] + critical*ses[j])
            records[index].update(nested_max_t_lower_bound=lower, nested_max_t_upper_bound=upper,
                                  nested_max_t_status=_interval_status(lower, upper, gain_tolerance))
    result_rows = tuple(ModelRefitTransferRow(**record) for record in records)
    category = _category([row.nested_max_t_status for row in result_rows])
    return ModelRefitTransferAudit(
        row_count=n, group_count=len(result_rows), refit_count=count, refit_ids=ids,
        reference_refit_id=reference_id, familywise_confidence_level=float(familywise_confidence_level),
        nested_draws=nested_draws, seed=seed, minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group, gain_tolerance=float(gain_tolerance),
        point_transfer_category=classify_independent_gains(point_means.tolist(), tolerance=gain_tolerance),
        reference_fit_category=reference.max_t_transfer_category,
        refit_point_categories=categories, refit_sign_stability=stability,
        nested_marginal_category=_category([row.nested_marginal_status for row in result_rows]),
        refit_aware_category=category, refit_aware_admissible=category == 'robust_generalizing',
        nested_max_t_critical_value=critical,
        unavailable_group_count=sum(not row.estimable for row in result_rows),
        selected_refit_draw_counts=tuple(int(x) for x in np.bincount(selected, minlength=count)) if enough_refits else (),
        identical_refits=bool(np.all(gain == gain[0])),
        same_selected_refit_shared_across_groups=True,
        reference_fit_can_override_refit_aware_failure=False, pooled_gain_can_override_group_failure=False,
        automatic_refit_scheme_inference=False, aggregate_confidence_score_emitted=False,
        groups=result_rows, reference_audit=reference,
    )
