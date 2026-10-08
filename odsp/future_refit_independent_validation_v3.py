"""Experimental v3: future-refit success probability with iid validation replicates.

This route deliberately does NOT use the shared-validation population design of
v1/v2. Each process refit must be paired with a fresh, iid validation draw
independent of every other refit's validation draw. Distinct block identifiers
can be checked here; iid sampling and train/validation independence cannot.

An IUT of one-sided validation tests at level a gives, for any truly
unsuccessful refit, P(certificate | refit) <= a. Write p for the probability
that a future frozen-process refit is truly successful in all required cells,
and theta for the marginal probability of obtaining a certificate from an iid
(refit, validation) pair. Then theta <= p + (1 - p) * a.

With iid pairs, K ~ Binomial(R, theta). An exact CP lower bound L on theta
therefore yields max(0, (L - a)/(1 - a)) as a (1 - process_alpha)
lower confidence bound for p. Unlike v1/v2, this does not spend a validation
familywise error budget across all R refits. The test level a is a
misclassification upper bound, NOT a second confidence-tail allowance.

The validation component Student-t test is only approximately calibrated
without additional assumptions. This is a non-primary experimental candidate:
the raw API does not verify iid draws, prospectivity or component-test size.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .bootstrap_t import ratio_mean_and_cluster_se
from .refit_information_transfer import _labels, _refit_ids, _weights
from .training_process_positive_cv3max_iut import _student_t_ppf
from .training_process_positive_transfer import _process_identity

METHOD_VERSION = "future_refit_independent_validation_v3"
TEST_ALPHA = 0.05
PROCESS_ALPHA = 0.05


def _strict_integer(value: object, *, name: str, minimum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    number = int(value)
    if number < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return number


def _alpha(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{name} must be a finite number in (0, 0.5)")
    number = float(value)
    if not math.isfinite(number) or not 0.0 < number < 0.5:
        raise ValueError(f"{name} must be a finite number in (0, 0.5)")
    return number


def _binomial_tail(k: int, n: int, p: float) -> float:
    """Numerically stable P[Binomial(n,p) >= k], including large n."""
    if k == 0:
        return 1.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    log_p = math.log(p)
    log_q = math.log1p(-p)
    base = math.lgamma(n + 1.0)
    terms = [
        base - math.lgamma(j + 1.0) - math.lgamma(n - j + 1.0)
        + j * log_p + (n - j) * log_q
        for j in range(k, n + 1)
    ]
    ceiling = max(terms)
    return min(1.0, math.exp(ceiling + math.log(sum(math.exp(t - ceiling) for t in terms))))


def exact_iid_certificate_lower_bound(
    certificates: int,
    refits: int,
    *,
    process_alpha: float = PROCESS_ALPHA,
) -> float:
    """Exact one-sided binomial lower bound for iid certificate probability."""
    n = _strict_integer(refits, name="refits", minimum=1)
    k = _strict_integer(certificates, name="certificates", minimum=0)
    if k > n:
        raise ValueError("certificates cannot exceed refits")
    alpha = _alpha(process_alpha, "process_alpha")
    if k == 0:
        return 0.0
    if k == n:
        return alpha ** (1.0 / n)
    lo, hi = 0.0, k / n
    for _ in range(90):
        mid = (lo + hi) / 2.0
        if _binomial_tail(k, n, mid) < alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def corrected_future_refit_lower_bound(
    certificates: int,
    refits: int,
    *,
    test_alpha: float = TEST_ALPHA,
    process_alpha: float = PROCESS_ALPHA,
) -> float:
    """Partial-identification bound correcting possible false certification."""
    a = _alpha(test_alpha, "test_alpha")
    lo = exact_iid_certificate_lower_bound(
        certificates, refits, process_alpha=process_alpha
    )
    return max(0.0, (lo - a) / (1.0 - a))


@dataclass(frozen=True)
class IndependentValidationV3Cell:
    refit_id: str
    group: object
    contrast: str
    block_count: int
    mean_gain: float | None
    standard_error: float | None
    t_critical: float | None
    lower_bound: float | None
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IndependentValidationV3Refit:
    refit_id: str
    certified_success: bool
    cells: tuple[IndependentValidationV3Cell, ...]

    def as_dict(self) -> dict[str, object]:
        return {"refit_id": self.refit_id,
                "certified_success": self.certified_success,
                "cells": [c.as_dict() for c in self.cells]}


@dataclass(frozen=True)
class IndependentValidationV3Audit:
    schema_version: int
    method_version: str
    qualification_status: str
    raw_api_primary_confirmatory: bool
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_ids: tuple[str, ...]
    refit_count: int
    validation_group_count: int
    contrast_count: int
    validation_test_alpha_per_refit: float
    process_confidence_alpha: float
    confidence_alpha_is_sum_of_test_and_process_alphas: bool
    globally_disjoint_validation_block_ids_checked: bool
    independent_iid_validation_draws_verified: bool
    frozen_process_iid_generation_verified: bool
    holdout_independence_verified: bool
    certified_success_count: int
    certificate_probability_lower_bound: float
    future_refit_success_probability_lower_bound: float
    maximum_possible_future_refit_bound: float
    gain_tolerance: float
    exploratory_probability_target: float
    exceeds_exploratory_target: bool
    fixed_set_results_reclassified: bool
    v5_process_mean_results_reclassified: bool
    v1_v2_results_reclassified: bool
    refits: tuple[IndependentValidationV3Refit, ...]

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["refit_ids"] = list(self.refit_ids)
        value["refits"] = [r.as_dict() for r in self.refits]
        return value


def evaluate_independent_validation_future_refit_v3(
    row_gains_by_refit: Sequence[np.ndarray | Sequence[Sequence[float]]],
    groups_by_refit: Sequence[Sequence[object]],
    validation_block_ids_by_refit: Sequence[Sequence[object]],
    *,
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    weights_by_refit: Sequence[Sequence[float] | None] | None = None,
    contrast_names: Sequence[str] = ("coarse-vs-marginal", "fine-vs-coarse"),
    test_alpha: float = TEST_ALPHA,
    process_alpha: float = PROCESS_ALPHA,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
    exploratory_probability_target: float = 0.8,
) -> IndependentValidationV3Audit:
    """Experimental IUT plus false-certification-adjusted CP bound.

    The caller must provide one genuinely independent validation sample per
    refit. Globally distinct IDs are necessary but do not prove this property.
    No provided score array qualifies an untouched external/provenance claim.
    """

    process_id, process_sha = _process_identity(
        training_process_id, training_process_manifest_sha256
    )
    R = len(row_gains_by_refit)
    minimum_refits = _strict_integer(minimum_refits, name="minimum_refits", minimum=8)
    minimum_blocks_per_group = _strict_integer(
        minimum_blocks_per_group, name="minimum_blocks_per_group", minimum=8
    )
    if R < minimum_refits:
        raise ValueError("insufficient refits for experimental v3 design")
    if len(groups_by_refit) != R or len(validation_block_ids_by_refit) != R:
        raise ValueError("refit, group and validation-block arrays must align")
    if weights_by_refit is not None and len(weights_by_refit) != R:
        raise ValueError("weights_by_refit must match refit count")
    a = _alpha(test_alpha, "test_alpha")
    cp_alpha = _alpha(process_alpha, "process_alpha")
    q = float(exploratory_probability_target)
    if not math.isfinite(q) or not 0.0 < q < 1.0:
        raise ValueError("exploratory_probability_target must lie in (0, 1)")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0.0:
        raise ValueError("gain_tolerance must be finite and nonnegative")
    contrasts = tuple(str(c).strip() for c in contrast_names)
    if len(contrasts) != 2 or any(not s for s in contrasts) or len(set(contrasts)) != 2:
        raise ValueError("v3 requires two unique non-empty ordered contrasts")
    ordered_ids, ordering = _refit_ids(refit_ids, R)

    seen_global_blocks: dict[str, str] = {}
    expected_groups: tuple[object, ...] | None = None
    rows: list[IndependentValidationV3Refit] = []
    for refit_id, index in zip(ordered_ids, ordering.tolist()):
        data = np.asarray(row_gains_by_refit[index], dtype=float)
        if data.ndim != 2 or data.shape[0] == 0 or data.shape[1] != 2:
            raise ValueError("each refit's gains must have shape [rows, 2]")
        if np.isnan(data).any() or np.isposinf(data).any():
            raise ValueError("row gains must not include NaN or positive infinity")
        n = data.shape[0]
        groups = _labels(groups_by_refit[index], n, name="groups")
        blocks = _labels(validation_block_ids_by_refit[index], n, name="validation blocks")
        weights = _weights(
            None if weights_by_refit is None else weights_by_refit[index], n
        )
        present_groups = tuple(sorted(set(groups.tolist()), key=lambda v: (type(v).__name__, repr(v))))
        if len(present_groups) < 2:
            raise ValueError("v3 needs at least two validation groups")
        if expected_groups is None:
            expected_groups = present_groups
        elif present_groups != expected_groups:
            raise ValueError("all refits must use the same target validation groups")

        for block in set(blocks[weights > 0].tolist()):
            key = str(block).strip()
            if not key:
                raise ValueError("block IDs must be nonempty")
            if key in seen_global_blocks and seen_global_blocks[key] != refit_id:
                raise ValueError(
                    "validation block IDs overlap across refits; v3 requires independent draws"
                )
            seen_global_blocks[key] = refit_id

        cells: list[IndependentValidationV3Cell] = []
        for group in present_groups:
            mask = groups == group
            positive = (weights > 0) & mask
            if not np.any(positive):
                raise ValueError("every target group needs positive validation weight")
            unique_blocks = sorted(set(blocks[positive].tolist()), key=lambda v: (type(v).__name__, repr(v)))
            B = len(unique_blocks)
            block_mass = np.empty(B, dtype=float)
            block_numerator = np.zeros((B, 2), dtype=float)
            finite = np.all(np.isfinite(data[positive]), axis=0)
            safe = np.where(np.isfinite(data), data, 0.0)
            for bi, b in enumerate(unique_blocks):
                bm = positive & (blocks == b)
                block_mass[bi] = float(weights[bm].sum())
                block_numerator[bi, :] = (
                    safe[bm, :] * weights[bm, None]
                ).sum(axis=0)
            means, ses = ratio_mean_and_cluster_se(block_numerator, block_mass) if B >= 2 else (
                np.full(2, math.nan), np.full(2, math.nan)
            )
            tcrit = _student_t_ppf(1.0 - a, B - 1) if B >= minimum_blocks_per_group else None
            for c in range(2):
                estimable = (
                    tcrit is not None and bool(finite[c])
                    and math.isfinite(float(ses[c])) and float(ses[c]) > 1e-12
                )
                lower = float(means[c] - float(tcrit) * ses[c]) if estimable else None
                cells.append(IndependentValidationV3Cell(
                    refit_id=refit_id,
                    group=group,
                    contrast=contrasts[c],
                    block_count=B,
                    mean_gain=float(means[c]) if bool(finite[c]) and math.isfinite(float(means[c])) else None,
                    standard_error=float(ses[c]) if bool(finite[c]) and math.isfinite(float(ses[c])) else None,
                    t_critical=float(tcrit) if tcrit is not None else None,
                    lower_bound=lower,
                    status=("robust_positive" if lower is not None and lower > gain_tolerance else
                            "not_robust_positive" if estimable else "unavailable"),
                ))
        certified = all(c.status == "robust_positive" for c in cells)
        rows.append(IndependentValidationV3Refit(refit_id, certified, tuple(cells)))
    K = sum(r.certified_success for r in rows)
    certificate_lo = exact_iid_certificate_lower_bound(K, R, process_alpha=cp_alpha)
    future_lo = corrected_future_refit_lower_bound(
        K, R, test_alpha=a, process_alpha=cp_alpha
    )
    return IndependentValidationV3Audit(
        schema_version=3,
        method_version=METHOD_VERSION,
        qualification_status="experimental_unqualified",
        raw_api_primary_confirmatory=False,
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        inference_target="iid frozen-process future refit all-cell true-positive-gain probability",
        refit_ids=ordered_ids,
        refit_count=R,
        validation_group_count=len(expected_groups or ()),
        contrast_count=2,
        validation_test_alpha_per_refit=a,
        process_confidence_alpha=cp_alpha,
        confidence_alpha_is_sum_of_test_and_process_alphas=False,
        globally_disjoint_validation_block_ids_checked=True,
        independent_iid_validation_draws_verified=False,
        frozen_process_iid_generation_verified=False,
        holdout_independence_verified=False,
        certified_success_count=K,
        certificate_probability_lower_bound=certificate_lo,
        future_refit_success_probability_lower_bound=future_lo,
        maximum_possible_future_refit_bound=corrected_future_refit_lower_bound(
            R, R, test_alpha=a, process_alpha=cp_alpha
        ),
        gain_tolerance=float(gain_tolerance),
        exploratory_probability_target=q,
        exceeds_exploratory_target=future_lo > q,
        fixed_set_results_reclassified=False,
        v5_process_mean_results_reclassified=False,
        v1_v2_results_reclassified=False,
        refits=tuple(rows),
    )



def iid_certificate_design_frontier(
    refits: int,
    *,
    probability_target: float = 0.8,
    desired_decision_power: float = 0.8,
    test_alpha: float = TEST_ALPHA,
    process_alpha: float = PROCESS_ALPHA,
    validation_groups: int = 2,
    independent_blocks_per_group: int = 8,
) -> dict[str, float | int | bool | None]:
    """Exact *planning* frontier; not empirical certification or calibration.

    Given q, R, and a target P(L_p > q), find the required number of
    certificates K and the smallest iid certificate probability theta that
    would reach the desired decision power. It cannot guarantee that the
    scientific validation tests achieve theta or are correctly calibrated.
    """
    n = _strict_integer(refits, name="refits", minimum=1)
    g = _strict_integer(validation_groups, name="validation_groups", minimum=2)
    b = _strict_integer(independent_blocks_per_group, name="independent_blocks_per_group", minimum=2)
    a = _alpha(test_alpha, "test_alpha")
    cp_alpha = _alpha(process_alpha, "process_alpha")
    q = float(probability_target)
    power = float(desired_decision_power)
    if not math.isfinite(q) or not 0.0 < q < 1.0:
        raise ValueError("probability_target must be in (0,1)")
    if not math.isfinite(power) or not 0.0 < power < 1.0:
        raise ValueError("desired_decision_power must be in (0,1)")
    target_k: int | None = None
    for k in range(1, n + 1):
        if corrected_future_refit_lower_bound(
            k, n, test_alpha=a, process_alpha=cp_alpha
        ) > q:
            target_k = k
            break
    min_theta: float | None = None
    if target_k is not None:
        lo, hi = 0.0, 1.0
        for _ in range(90):
            mid = (lo + hi) / 2.0
            if _binomial_tail(target_k, n, mid) < power:
                lo = mid
            else:
                hi = mid
        min_theta = (lo + hi) / 2.0
    return {
        "refit_count": n,
        "probability_target": q,
        "desired_decision_power": power,
        "feasible_even_if_all_certify": target_k is not None,
        "minimum_certificates": target_k,
        "minimum_iid_certificate_probability_for_target_power": min_theta,
        "maximum_corrected_lower_bound": corrected_future_refit_lower_bound(
            n, n, test_alpha=a, process_alpha=cp_alpha
        ),
        "minimum_independent_validation_blocks": n * g * b,
        "component_test_size_assumption_verified": False,
        "iid_validation_sampling_verified": False,
        "prospective_qualification_passed": False,
    }
