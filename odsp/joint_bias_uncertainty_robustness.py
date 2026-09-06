"""Joint block-bootstrap and bounded-reweighting robustness for transfer gains.

For each independent validation group, blocks are resampled with replacement.  In
every bootstrap draw ODSP then solves the worst and best weighted mean gain over the
caller-declared multiplicative row-weight envelope.  The resulting percentile
bounds therefore reflect both the declared block uncertainty and the declared
reweighting sensitivity envelope.

This is a sensitivity audit, not an exact finite-sample theorem or an inferred bias
correction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .bounded_reweighting_robustness import extreme_bounded_weighted_mean
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class JointBiasUncertaintyGroup:
    group_id: str
    row_count: int
    block_count: int
    total_base_weight: float
    point_mean_gain: float
    deterministic_worst_case_gain: float
    deterministic_best_case_gain: float
    worst_case_lower_bound: float | None
    worst_case_upper_bound: float | None
    best_case_lower_bound: float | None
    best_case_upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JointBiasUncertaintyAudit:
    row_count: int
    group_count: int
    gamma: float
    confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    point_transfer_category: str
    deterministic_envelope_category: str
    joint_robust_category: str
    joint_robust_admissible: bool
    unavailable_group_count: int
    uncertain_group_count: int
    envelope_sensitive_group_count: int
    joint_robust_positive_group_count: int
    joint_robust_nonpositive_group_count: int
    minimum_worst_case_lower_bound: float | None
    maximum_best_case_upper_bound: float | None
    pooled_mean_can_override_group_failure: bool
    automatic_bias_correction_performed: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[JointBiasUncertaintyGroup, ...]

    def as_dict(self) -> dict[str, object]:
        payload=asdict(self)
        payload["groups"]=[row.as_dict() for row in self.groups]
        return payload


def _validate_vector(values: Sequence[float], name: str, *, expected: int | None=None) -> np.ndarray:
    array=np.asarray(values,dtype=float)
    if array.ndim!=1 or array.size==0:
        raise ValueError(f"{name} must be a non-empty one-dimensional vector")
    if expected is not None and array.size!=expected:
        raise ValueError(f"{name} has an unexpected length")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _validate_weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n,dtype=float)
    weight=np.asarray(values,dtype=float)
    if weight.shape!=(n,):
        raise ValueError("base_weight must contain one value per row")
    if not np.isfinite(weight).all() or np.any(weight<0) or not np.any(weight>0):
        raise ValueError("base_weight must be finite, non-negative and positive in total")
    return weight


def _validate_labels(values: Sequence[object], n: int, name: str) -> tuple[str,...]:
    if len(values)!=n:
        raise ValueError(f"{name} must contain one value per row")
    labels=tuple(str(value).strip() for value in values)
    if any(not value for value in labels):
        raise ValueError(f"{name} labels must be non-empty")
    return labels


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    return float(np.sum(values*weight)/np.sum(weight))


def _stable_group_seed(seed: int, group_id: str) -> int:
    digest=hashlib.sha256(f"{seed}|{group_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8],"little",signed=False)


def _bootstrap_extreme_distributions(
    gain: np.ndarray,
    base_weight: np.ndarray,
    block_labels: tuple[str,...],
    *,
    gamma: float,
    draws: int,
    seed: int,
) -> tuple[np.ndarray,np.ndarray]:
    ordered_blocks=tuple(dict.fromkeys(block_labels))
    block_index={block:index for index,block in enumerate(ordered_blocks)}
    row_block=np.asarray([block_index[value] for value in block_labels],dtype=int)
    block_count=len(ordered_blocks)
    rng=np.random.default_rng(seed)
    sampled=rng.integers(0,block_count,size=(draws,block_count))
    counts=np.stack([np.bincount(row,minlength=block_count) for row in sampled],axis=0)
    multiplicity=counts[:,row_block]
    draw_weight=multiplicity*base_weight[None,:]

    order=np.argsort(gain,kind="mergesort")
    g=gain[order]
    w=draw_weight[:,order]
    wg=w*g[None,:]
    prefix_w=np.concatenate([np.zeros((draws,1)),np.cumsum(w,axis=1)],axis=1)
    prefix_wg=np.concatenate([np.zeros((draws,1)),np.cumsum(wg,axis=1)],axis=1)
    total_w=prefix_w[:,-1:]
    total_wg=prefix_wg[:,-1:]
    low=1.0/gamma
    high=gamma

    min_num=high*prefix_wg + low*(total_wg-prefix_wg)
    min_den=high*prefix_w + low*(total_w-prefix_w)
    worst=np.min(min_num/min_den,axis=1)

    max_num=low*prefix_wg + high*(total_wg-prefix_wg)
    max_den=low*prefix_w + high*(total_w-prefix_w)
    best=np.max(max_num/max_den,axis=1)
    return worst,best


def audit_joint_bias_uncertainty_robustness(
    row_gain: Sequence[float],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    base_weight: Sequence[float] | None=None,
    gamma: float=2.0,
    confidence_level: float=0.95,
    bootstrap_draws: int=1000,
    seed: int=20260906,
    minimum_blocks_per_group: int=8,
    gain_tolerance: float=0.0,
) -> JointBiasUncertaintyAudit:
    gain=_validate_vector(row_gain,"row_gain")
    n=int(gain.size)
    group_labels=_validate_labels(groups,n,"groups")
    block_labels=_validate_labels(blocks,n,"blocks")
    weight=_validate_weights(base_weight,n)
    gamma_value=float(gamma)
    if not math.isfinite(gamma_value) or gamma_value<1.0:
        raise ValueError("gamma must be finite and >= 1")
    if not math.isfinite(confidence_level) or not 0.0<confidence_level<1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")
    if not isinstance(bootstrap_draws,int) or bootstrap_draws<100:
        raise ValueError("bootstrap_draws must be an integer >= 100")
    if not isinstance(minimum_blocks_per_group,int) or minimum_blocks_per_group<2:
        raise ValueError("minimum_blocks_per_group must be an integer >= 2")
    if not isinstance(seed,int):
        raise ValueError("seed must be an integer")
    if not math.isfinite(gain_tolerance) or gain_tolerance<0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    group_array=np.asarray(group_labels,dtype=object)
    block_array=np.asarray(block_labels,dtype=object)
    ordered_groups=tuple(dict.fromkeys(group_labels))
    alpha=1.0-confidence_level
    rows=[]
    point_gains=[]
    deterministic_statuses=[]

    for group_id in ordered_groups:
        mask=group_array==group_id
        local_gain=gain[mask]
        local_weight=weight[mask]
        local_blocks=tuple(str(value) for value in block_array[mask])
        block_count=len(tuple(dict.fromkeys(local_blocks)))
        point=_weighted_mean(local_gain,local_weight)
        worst=extreme_bounded_weighted_mean(local_gain,base_weight=local_weight,gamma=gamma_value,minimize=True)
        best=extreme_bounded_weighted_mean(local_gain,base_weight=local_weight,gamma=gamma_value,minimize=False)
        point_gains.append(point)
        if worst>gain_tolerance:
            deterministic_statuses.append("robust_positive")
        elif best<=gain_tolerance:
            deterministic_statuses.append("robust_nonpositive")
        else:
            deterministic_statuses.append("bound_sensitive")

        if block_count<minimum_blocks_per_group:
            rows.append(JointBiasUncertaintyGroup(
                group_id=group_id,row_count=int(np.count_nonzero(mask)),block_count=block_count,
                total_base_weight=float(np.sum(local_weight)),point_mean_gain=point,
                deterministic_worst_case_gain=float(worst),deterministic_best_case_gain=float(best),
                worst_case_lower_bound=None,worst_case_upper_bound=None,
                best_case_lower_bound=None,best_case_upper_bound=None,
                status="unavailable",estimable=False,
            ))
            continue

        worst_samples,best_samples=_bootstrap_extreme_distributions(
            local_gain,local_weight,local_blocks,gamma=gamma_value,draws=bootstrap_draws,
            seed=_stable_group_seed(seed,group_id),
        )
        worst_lower,worst_upper=np.quantile(worst_samples,[alpha/2.0,1.0-alpha/2.0])
        best_lower,best_upper=np.quantile(best_samples,[alpha/2.0,1.0-alpha/2.0])
        if worst_lower>gain_tolerance:
            status="joint_robust_positive"
        elif best_upper<=gain_tolerance:
            status="joint_robust_nonpositive"
        elif worst<=gain_tolerance<best:
            status="envelope_sensitive"
        else:
            status="uncertain"
        rows.append(JointBiasUncertaintyGroup(
            group_id=group_id,row_count=int(np.count_nonzero(mask)),block_count=block_count,
            total_base_weight=float(np.sum(local_weight)),point_mean_gain=point,
            deterministic_worst_case_gain=float(worst),deterministic_best_case_gain=float(best),
            worst_case_lower_bound=float(worst_lower),worst_case_upper_bound=float(worst_upper),
            best_case_lower_bound=float(best_lower),best_case_upper_bound=float(best_upper),
            status=status,estimable=True,
        ))

    if all(value=="robust_positive" for value in deterministic_statuses):
        deterministic_category="gamma_robust_generalizing"
    elif all(value=="robust_nonpositive" for value in deterministic_statuses):
        deterministic_category="gamma_robust_non_generalizing"
    elif any(value=="bound_sensitive" for value in deterministic_statuses):
        deterministic_category="gamma_sensitive"
    else:
        deterministic_category="gamma_mixed"

    statuses=[row.status for row in rows]
    if "unavailable" in statuses:
        joint_category="unavailable"
    elif all(value=="joint_robust_positive" for value in statuses):
        joint_category="joint_robust_generalizing"
    elif all(value=="joint_robust_nonpositive" for value in statuses):
        joint_category="joint_robust_non_generalizing"
    elif "envelope_sensitive" in statuses:
        joint_category="envelope_sensitive"
    elif "uncertain" in statuses:
        joint_category="uncertain"
    else:
        joint_category="mixed"

    available=[row for row in rows if row.estimable]
    lower_values=[row.worst_case_lower_bound for row in available if row.worst_case_lower_bound is not None]
    upper_values=[row.best_case_upper_bound for row in available if row.best_case_upper_bound is not None]
    return JointBiasUncertaintyAudit(
        row_count=n,group_count=len(rows),gamma=gamma_value,confidence_level=float(confidence_level),
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=minimum_blocks_per_group,
        point_transfer_category=classify_independent_gains(point_gains,tolerance=gain_tolerance),
        deterministic_envelope_category=deterministic_category,
        joint_robust_category=joint_category,
        joint_robust_admissible=bool(joint_category=="joint_robust_generalizing"),
        unavailable_group_count=statuses.count("unavailable"),
        uncertain_group_count=statuses.count("uncertain"),
        envelope_sensitive_group_count=statuses.count("envelope_sensitive"),
        joint_robust_positive_group_count=statuses.count("joint_robust_positive"),
        joint_robust_nonpositive_group_count=statuses.count("joint_robust_nonpositive"),
        minimum_worst_case_lower_bound=(float(min(lower_values)) if lower_values else None),
        maximum_best_case_upper_bound=(float(max(upper_values)) if upper_values else None),
        pooled_mean_can_override_group_failure=False,
        automatic_bias_correction_performed=False,
        aggregate_confidence_score_emitted=False,
        groups=tuple(rows),
    )
