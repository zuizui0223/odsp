"""Experimental shared-validation refit success probability.

All refits reuse one independent validation sample. Conditional on that
validation sample V, iid refits give iid certification indicators. For a
truly unsuccessful fixed refit, a bounded-score e-value IUT has conditional
false-certification probability at most a over the sample V. Markov bounds
the V-specific false-certification fraction by c=a/delta with failure
probability delta. A conditional binomial CP lower bound on the certificate
fraction, corrected by c, yields a one-sided lower confidence bound on
true future-refit success probability at level delta+process_alpha.

Population gains here are BLOCK-UNIFORM means. The input arrays cannot
verify iid validation blocks, prospective bounded score protocol, independent
training process draws, or absence of validation-based tuning.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .refit_information_transfer import _labels, _refit_ids, _weights
from .training_process_positive_transfer import _process_identity

METHOD_VERSION = "future_refit_shared_validation_evalue_v0"
COMPONENT_TEST_ALPHA = 0.002
VALIDATION_MARKOV_DELTA = 0.025
PROCESS_ALPHA = 0.025
BET_FRACTIONS = (0.25, 0.5, 0.75, 1.0)


def _number(v: object, name: str) -> float:
    if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.integer, np.floating)):
        raise ValueError(f"{name} must be a finite number")
    x = float(v)
    if not math.isfinite(x):
        raise ValueError(f"{name} must be a finite number")
    return x


def _integer(v: object, name: str, minimum: int) -> int:
    if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    x = int(v)
    if x < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return x


def _prob(v: object, name: str) -> float:
    x = _number(v, name)
    if not 0.0 < x < 1.0:
        raise ValueError(f"{name} must lie in (0,1)")
    return x


def _binomial_survival(k: int, n: int, p: float) -> float:
    if k <= 0:
        return 1.0
    if k > n or p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    log_p, log_q = math.log(p), math.log1p(-p)
    b = math.lgamma(n+1)
    terms = [b-math.lgamma(j+1)-math.lgamma(n-j+1)+j*log_p+(n-j)*log_q
             for j in range(k, n+1)]
    top = max(terms)
    return min(1.0, math.exp(top)*math.fsum(math.exp(t-top) for t in terms))


def certificate_probability_cp_lower(k: int, n: int, *, alpha: float = PROCESS_ALPHA) -> float:
    n = _integer(n, "n", 1)
    k = _integer(k, "k", 0)
    a = _prob(alpha, "alpha")
    if k > n:
        raise ValueError("certificates exceed refit count")
    if k == 0:
        return 0.0
    if k == n:
        return a**(1/n)
    low, high = 0.0, k/n
    for _ in range(90):
        mid = (low+high)/2
        if _binomial_survival(k, n, mid) < a:
            low = mid
        else:
            high = mid
    return (low+high)/2


def shared_validation_success_probability_lower(
    certified: int,
    refits: int,
    *,
    component_test_alpha: float = COMPONENT_TEST_ALPHA,
    validation_delta: float = VALIDATION_MARKOV_DELTA,
    process_alpha: float = PROCESS_ALPHA,
) -> float:
    a = _prob(component_test_alpha, "component_test_alpha")
    d = _prob(validation_delta, "validation_delta")
    pa = _prob(process_alpha, "process_alpha")
    if a >= d:
        raise ValueError("component_test_alpha must be below validation_delta")
    if d+pa > 0.05+1e-15:
        raise ValueError("validation_delta + process_alpha cannot exceed 0.05")
    c = a/d
    lo = certificate_probability_cp_lower(certified, refits, alpha=pa)
    return max(0.0, (lo-c)/(1-c))


def _log_mixture_betting_e_value(
    values: np.ndarray, *, lower: float, threshold: float
) -> float:
    """Mixture of fixed nonnegative betting test martingales.

    For any fixed lambda in (0,1], product_b
    (1+lambda*(X_b-threshold)/(threshold-lower)) has null expectation <=1
    when the bounded-below validation blocks are iid and mean <= threshold.
    """
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all() or np.any(a < lower):
        raise ValueError("invalid bounded block means")
    logs = []
    for lam in BET_FRACTIONS:
        factors = 1+lam*(a-threshold)/(threshold-lower)
        if np.any(factors < -1e-12):
            raise ValueError("negative e-factor")
        logs.append(-math.inf if np.any(factors <= 0) else float(np.log(factors).sum()))
    maximum = max(logs)
    if maximum == -math.inf:
        return -math.inf
    return maximum + math.log(math.fsum(math.exp(v-maximum) for v in logs)) - math.log(len(logs))


@dataclass(frozen=True)
class SharedValidationCell:
    refit_id: str
    group: object
    contrast: str
    block_count: int
    mean_block_gain: float | None
    log_e_value: float | None
    log_certification_threshold: float
    status: str

    def as_dict(self) -> dict[str, object]:
        obj = asdict(self)
        if self.log_e_value == -math.inf:
            obj["log_e_value"] = None
        return obj


@dataclass(frozen=True)
class SharedValidationRefit:
    refit_id: str
    certified_success: bool
    cells: tuple[SharedValidationCell, ...]

    def as_dict(self) -> dict[str, object]:
        return {"refit_id": self.refit_id,
                "certified_success": self.certified_success,
                "cells": [x.as_dict() for x in self.cells]}


@dataclass(frozen=True)
class SharedValidationAudit:
    schema_version: int
    method_version: str
    qualification_status: str
    raw_api_primary_confirmatory: bool
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_ids: tuple[str, ...]
    refit_count: int
    group_count: int
    component_test_alpha: float
    validation_markov_delta: float
    process_alpha: float
    overall_confidence_alpha: float
    maximum_bad_refit_false_certification_fraction: float
    gain_lower_bound: float
    gain_upper_bound: float
    gain_tolerance: float
    betting_fractions: tuple[float, ...]
    shared_validation_blocks_used: bool
    inner_validation_iut_used: bool
    block_uniform_population_target: bool
    validation_iid_blocks_verified: bool
    training_process_iid_verified: bool
    bounded_score_protocol_verified: bool
    model_to_score_provenance_verified: bool
    certified_success_count: int
    conditional_certificate_cp_lower: float
    true_future_refit_success_probability_lower: float
    maximum_possible_lower_bound: float
    unconditional_certificate_count_binomial_claimed: bool
    existing_results_reclassified: bool
    refits: tuple[SharedValidationRefit, ...]

    def as_dict(self) -> dict[str, object]:
        obj = asdict(self)
        obj["refit_ids"] = list(self.refit_ids)
        obj["betting_fractions"] = list(self.betting_fractions)
        obj["refits"] = [x.as_dict() for x in self.refits]
        return obj


def evaluate_future_refit_shared_validation_evalue_v0(
    row_gain_by_refit: np.ndarray | Sequence,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    contrast_names: Sequence[str] = ("coarse-vs-marginal", "fine-vs-coarse"),
    sample_weight: Sequence[float] | None = None,
    gain_lower_bound: float = -1.0,
    gain_upper_bound: float = 1.0,
    gain_tolerance: float = 0.0,
    component_test_alpha: float = COMPONENT_TEST_ALPHA,
    validation_delta: float = VALIDATION_MARKOV_DELTA,
    process_alpha: float = PROCESS_ALPHA,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
) -> SharedValidationAudit:
    """Unqualified score-only evaluator; it cannot prove its sampling assumptions."""
    pid, psha = _process_identity(training_process_id, training_process_manifest_sha256)
    data = np.asarray(row_gain_by_refit, dtype=float)
    if data.ndim != 3 or 0 in data.shape or data.shape[2] != 2:
        raise ValueError("gains must be nonempty [refit, row, 2]")
    if np.isnan(data).any() or np.isposinf(data).any():
        raise ValueError("gains cannot contain NaN or positive infinity")
    R, n, contrasts = data.shape
    minimum_refits = _integer(minimum_refits, "minimum_refits", 8)
    minimum_blocks_per_group = _integer(minimum_blocks_per_group, "minimum_blocks_per_group", 8)
    if R < minimum_refits:
        raise ValueError("insufficient iid process refits")
    low = _number(gain_lower_bound, "gain_lower_bound")
    high = _number(gain_upper_bound, "gain_upper_bound")
    tau = _number(gain_tolerance, "gain_tolerance")
    if not low < tau < high:
        raise ValueError("gain_lower_bound < gain_tolerance < gain_upper_bound required")
    a = _prob(component_test_alpha, "component_test_alpha")
    d = _prob(validation_delta, "validation_delta")
    ap = _prob(process_alpha, "process_alpha")
    if a >= d or d+ap > 0.05+1e-15:
        raise ValueError("invalid a, delta or process-alpha budget")
    names = tuple(str(c).strip() for c in contrast_names)
    if len(names) != 2 or len(set(names)) != 2 or not all(names):
        raise ValueError("two unique ordered contrast names required")
    ids, order = _refit_ids(refit_ids, R)
    data = data[order]
    gs = _labels(groups, n, name="groups")
    bs = _labels(blocks, n, name="blocks")
    w = _weights(sample_weight, n)
    group_order = tuple(sorted(set(gs.tolist()), key=lambda x: (type(x).__name__, repr(x))))
    if len(group_order) < 2:
        raise ValueError("at least two groups are required")
    positive = w > 0
    finite = np.isfinite(data)
    if np.any((finite & ((data < low) | (data > high))) & positive[None, :, None]):
        raise ValueError("row gain outside prospective bounds")
    cutoff = math.log(1/a)
    by_refit: list[list[SharedValidationCell]] = [[] for _ in range(R)]
    for g in group_order:
        mask = (gs == g) & positive
        group_blocks = tuple(sorted(set(bs[mask].tolist()), key=lambda x: (type(x).__name__, repr(x))))
        if len(group_blocks) < minimum_blocks_per_group:
            raise ValueError("insufficient independent validation blocks in group")
        block_values = np.empty((R, len(group_blocks), 2), dtype=float)
        for bi, b in enumerate(group_blocks):
            loc = mask & (bs == b)
            gains = data[:, loc, :]
            bw = w[loc]
            usable = np.all(np.isfinite(gains), axis=1)
            numerator = np.sum(np.where(np.isfinite(gains), gains, 0) * bw[None, :, None], axis=1)
            block_values[:, bi, :] = np.where(usable, numerator / float(bw.sum()), np.nan)
        for ri, rid in enumerate(ids):
            for ci, contrast in enumerate(names):
                values = block_values[ri, :, ci]
                if not np.isfinite(values).all():
                    log_e, mean, status = None, None, "unavailable"
                else:
                    log_e = _log_mixture_betting_e_value(values, lower=low, threshold=tau)
                    mean = float(np.mean(values))
                    status = "robust_positive" if log_e > cutoff else "not_robust_positive"
                by_refit[ri].append(SharedValidationCell(
                    refit_id=rid, group=g, contrast=contrast,
                    block_count=len(group_blocks), mean_block_gain=mean,
                    log_e_value=log_e, log_certification_threshold=cutoff,
                    status=status,
                ))
    refits = tuple(SharedValidationRefit(
        refit_id=rid,
        certified_success=all(c.status == "robust_positive" for c in by_refit[ri]),
        cells=tuple(by_refit[ri]),
    ) for ri, rid in enumerate(ids))
    K = sum(r.certified_success for r in refits)
    return SharedValidationAudit(
        schema_version=0, method_version=METHOD_VERSION,
        qualification_status="experimental_unqualified", raw_api_primary_confirmatory=False,
        training_process_id=pid, training_process_manifest_sha256=psha,
        inference_target="Future frozen-process refit has positive validation-block-uniform population gain in every required group x contrast",
        refit_ids=ids, refit_count=R, group_count=len(group_order),
        component_test_alpha=a, validation_markov_delta=d, process_alpha=ap,
        overall_confidence_alpha=d+ap,
        maximum_bad_refit_false_certification_fraction=a/d,
        gain_lower_bound=low, gain_upper_bound=high, gain_tolerance=tau,
        betting_fractions=BET_FRACTIONS,
        shared_validation_blocks_used=True, inner_validation_iut_used=True,
        block_uniform_population_target=True,
        validation_iid_blocks_verified=False, training_process_iid_verified=False,
        bounded_score_protocol_verified=False, model_to_score_provenance_verified=False,
        certified_success_count=K,
        conditional_certificate_cp_lower=certificate_probability_cp_lower(K, R, alpha=ap),
        true_future_refit_success_probability_lower=shared_validation_success_probability_lower(
            K, R, component_test_alpha=a, validation_delta=d, process_alpha=ap
        ),
        maximum_possible_lower_bound=shared_validation_success_probability_lower(
            R, R, component_test_alpha=a, validation_delta=d, process_alpha=ap
        ),
        unconditional_certificate_count_binomial_claimed=False,
        existing_results_reclassified=False,
        refits=refits,
    )


def shared_validation_design_frontier(
    refits: int,
    *,
    probability_target: float = 0.8,
    component_test_alpha: float = COMPONENT_TEST_ALPHA,
    validation_delta: float = VALIDATION_MARKOV_DELTA,
    process_alpha: float = PROCESS_ALPHA,
    validation_groups: int = 2,
    independent_blocks_per_group: int = 12,
) -> dict[str, object]:
    """Mathematical feasibility only, not power from marginal certificate rates."""
    R = _integer(refits, "refits", 1)
    G = _integer(validation_groups, "validation_groups", 2)
    B = _integer(independent_blocks_per_group, "independent_blocks_per_group", 2)
    q = _prob(probability_target, "probability_target")
    def bound(k: int) -> float:
        return shared_validation_success_probability_lower(
            k, R, component_test_alpha=component_test_alpha,
            validation_delta=validation_delta, process_alpha=process_alpha
        )
    K = next((k for k in range(R+1) if bound(k) > q), None)
    return {
        "refit_count": R, "probability_target": q,
        "minimum_certificates": K, "feasible_even_if_all_certify": K is not None,
        "maximum_lower_bound": bound(R),
        "minimum_distinct_shared_validation_blocks": B*G,
        "refit_by_block_score_evaluations": R*B*G,
        "unconditional_binomial_power_inferred": False,
        "prospective_qualification_passed": False,
    }
