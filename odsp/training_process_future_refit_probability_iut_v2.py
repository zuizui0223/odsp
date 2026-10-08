"""Experimental future-refit success-probability v2: refit-level IUT.

This is a *new inferential candidate*, distinct from the failed v1 simultaneous
max-t route, the qualified v5 process-mean route and fixed-set intersections.

For each of R independently generated refits, certify success by an IUT over
group x ordered-contrast components. Each *component* uses a one-sided
validation-block t bound at alpha_validation/R. Because one refit is truly
unsuccessful whenever at least one component null is true, no additional
multiplicity adjustment is made among the AND components within that refit.
Union bound across R observed refits gives validation false-certification
probability <= alpha_validation, assuming each component test is valid.

On the event of no false certification, K_certified <= K_true and the exact
binomial Clopper-Pearson bound on K_certified is conservative for a future
iid training-process draw. The final overstatement bound is
alpha_validation + alpha_process.

The component t calibration is not guaranteed for arbitrary validation
distributions; this v2 remains experimental pending its OWN prospective
operating-characteristic qualification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .bootstrap_t import ratio_mean_and_cluster_se
from .information_transfer import (
    InformationLevelScore,
    InformationTransferStep,
    validate_information_filtration,
)
from .refit_information_transfer import (
    RefitInformationLevelScores,
    _labels,
    _refit_ids,
    _score_matrices,
    _weights,
)
from .training_process_positive_cv3max_iut import _student_t_ppf
from .training_process_positive_transfer import _process_identity
from .training_process_future_refit_success_probability import (
    FutureRefitSuccessCell,
    FutureRefitSuccessRefit,
    exact_binomial_success_probability_lower_bound,
)

METHOD_VERSION = "training_process_future_refit_probability_refit_iut_v2"
VALIDATION_ALPHA = 0.025
PROCESS_ALPHA = 0.025


@dataclass(frozen=True)
class RefitIUTProbabilityAudit:
    schema_version: int
    method_version: str
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_count: int
    refit_ids: tuple[str, ...]
    group_count: int
    contrast_count: int
    validation_alpha: float
    process_alpha: float
    overall_alpha: float
    validation_component_alpha_per_refit: float
    student_t_distribution: str
    refit_level_iut: bool
    validation_multiplicity_across_refits_only: bool
    validation_shared_across_refits: bool
    observed_training_refits_resampled: bool
    max_t_across_all_refit_cells_used: bool
    certified_success_count: int
    maximum_possible_probability_bound: float
    future_refit_success_probability_lower_bound: float
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    all_required_cells_estimable: bool
    raw_api_primary_confirmatory: bool
    fixed_set_intersection_used: bool
    process_mean_is_estimand: bool
    original_training_source_superpopulation_generalization_claimed: bool
    cells: tuple[FutureRefitSuccessCell, ...]
    per_refit: tuple[FutureRefitSuccessRefit, ...]

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["refit_ids"] = list(self.refit_ids)
        result["cells"] = [row.as_dict() for row in self.cells]
        result["per_refit"] = [row.as_dict() for row in self.per_refit]
        return result


@dataclass(frozen=True)
class RefitIUTInformationCertification:
    schema_version: int
    method_version: str
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    audit: RefitIUTProbabilityAudit

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "method_version": self.method_version,
            "score_name": self.score_name,
            "levels": list(self.levels),
            "steps": [step.as_dict() for step in self.steps],
            "audit": self.audit.as_dict(),
        }


def _integer(value: object, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    n = int(value)
    if n < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return n


def certify_future_refit_probability_refit_iut_v2(
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
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> RefitIUTProbabilityAudit:
    """Report a non-primary p_success lower bound under refit-level IUT tests."""

    process_id, process_sha = _process_identity(
        training_process_id, training_process_manifest_sha256
    )
    data = np.asarray(row_gain_by_refit, dtype=float)
    if data.ndim == 2:
        data = data[:, :, None]
    if data.ndim != 3 or 0 in data.shape:
        raise ValueError("row_gain_by_refit must be [refit,row,contrast]")
    if np.isnan(data).any() or np.isposinf(data).any():
        raise ValueError("row gains may be finite or -inf, not NaN or +inf")
    R, nrows, ncontrasts = data.shape
    ids, order = _refit_ids(refit_ids, R)
    data = data[order]
    if ncontrasts != 2:
        raise ValueError("v2 requires exactly two ordered contrasts")
    groups_arr = _labels(groups, nrows, name="groups")
    blocks_arr = _labels(blocks, nrows, name="blocks")
    weights = _weights(sample_weight, nrows)

    for val, name in ((validation_alpha, "validation_alpha"),(process_alpha,"process_alpha")):
        if not isinstance(val, (int, float)) or isinstance(val, bool) or not math.isfinite(float(val)) or not 0.0 < float(val) < 1.0:
            raise ValueError(f"{name} must lie in (0,1)")
    if validation_alpha + process_alpha > 0.05 + 1e-15:
        raise ValueError("v2 overall alpha budget must not exceed 0.05")
    minimum_refits = _integer(minimum_refits,"minimum_refits",8)
    minimum_blocks_per_group = _integer(minimum_blocks_per_group,"minimum_blocks_per_group",8)
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0.0:
        raise ValueError("gain_tolerance must be non-negative and finite")
    if contrast_names is None:
        names = ("contrast-000","contrast-001")
    else:
        names = tuple(str(x).strip() for x in contrast_names)
        if len(names)!=2 or any(not x for x in names) or names[0]==names[1]:
            raise ValueError("contrast_names must contain two unique nonempty strings")
    refit_alpha = float(validation_alpha)/float(R)
    groups_order = sorted(set(groups_arr.tolist()), key=lambda x:(type(x).__name__,repr(x)))
    records: list[FutureRefitSuccessCell] = []
    per_refit_positions: list[list[FutureRefitSuccessCell]] = [[] for _ in range(R)]

    enough_refits = R >= minimum_refits
    for group in groups_order:
        mask = groups_arr==group
        gw = weights[mask]
        gb = blocks_arr[mask]
        gain = data[:,mask,:]
        positive = gw>0
        if not np.any(positive):
            raise ValueError("validation group has zero positive weight")
        block_order = sorted(set(gb[positive].tolist()), key=lambda x:(type(x).__name__,repr(x)))
        B = len(block_order)
        block_mass = np.empty(B,dtype=float)
        numer = np.zeros((B,R*ncontrasts),dtype=float)
        finite = np.all(np.isfinite(gain[:,positive,:]),axis=1)
        safe = np.where(np.isfinite(gain),gain,0.0)
        for bi, block in enumerate(block_order):
            in_block=(gb==block)&positive
            block_mass[bi]=float(np.sum(gw[in_block]))
            numer[bi,:]=np.sum(
                safe[:,in_block,:]*gw[in_block][None,:,None],
                axis=1,
            ).reshape(-1)
        if np.any(block_mass<=0):
            raise ValueError("positive-support blocks must have positive mass")
        means, ses = ratio_mean_and_cluster_se(numer, block_mass)
        means=means.reshape(R,ncontrasts)
        ses=ses.reshape(R,ncontrasts)
        tcrit = _student_t_ppf(1.0-refit_alpha,B-1) if B>=minimum_blocks_per_group and enough_refits else math.inf
        for ri in range(R):
            for ci in range(ncontrasts):
                estimable = bool(finite[ri,ci] and enough_refits and B>=minimum_blocks_per_group and ses[ri,ci]>1e-12)
                lo = float(means[ri,ci]-tcrit*ses[ri,ci]) if estimable else None
                cell = FutureRefitSuccessCell(
                    refit_id=ids[ri],
                    group=group,
                    contrast=names[ci],
                    row_count=int(np.count_nonzero(mask)),
                    block_count=B,
                    total_weight=float(np.sum(gw[positive])),
                    mean_gain=float(means[ri,ci]) if bool(finite[ri,ci]) else None,
                    studentizing_standard_error=float(ses[ri,ci]) if bool(finite[ri,ci]) else None,
                    lower_bound=lo,
                    status=("robust_positive" if lo is not None and lo>gain_tolerance else "not_robust_positive" if estimable else "unavailable"),
                    estimable=estimable,
                )
                records.append(cell)
                per_refit_positions[ri].append(cell)
    per_refit=[]
    successes=0
    for ri,refit_id in enumerate(ids):
        cells=per_refit_positions[ri]
        required=len(groups_order)*ncontrasts
        assert len(cells)==required
        certified=all(c.status=="robust_positive" for c in cells)
        successes+=int(certified)
        per_refit.append(FutureRefitSuccessRefit(
            refit_id=refit_id,
            certified_success=certified,
            all_required_cells_estimable=all(c.estimable for c in cells),
            robust_positive_cell_count=sum(c.status=="robust_positive" for c in cells),
            required_cell_count=required,
            minimum_lower_bound=min(float(c.lower_bound) for c in cells) if all(c.lower_bound is not None for c in cells) else None,
        ))
    return RefitIUTProbabilityAudit(
        schema_version=2,
        method_version=METHOD_VERSION,
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        inference_target="Probability that a future iid frozen-process refit has positive population gain in every required validation cell",
        refit_count=R,
        refit_ids=ids,
        group_count=len(groups_order),
        contrast_count=ncontrasts,
        validation_alpha=float(validation_alpha),
        process_alpha=float(process_alpha),
        overall_alpha=float(validation_alpha+process_alpha),
        validation_component_alpha_per_refit=refit_alpha,
        student_t_distribution="t_(validation_block_count_per_group-1)",
        refit_level_iut=True,
        validation_multiplicity_across_refits_only=True,
        validation_shared_across_refits=True,
        observed_training_refits_resampled=False,
        max_t_across_all_refit_cells_used=False,
        certified_success_count=successes,
        maximum_possible_probability_bound=exact_binomial_success_probability_lower_bound(R,R,alpha=process_alpha),
        future_refit_success_probability_lower_bound=exact_binomial_success_probability_lower_bound(successes,R,alpha=process_alpha),
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        all_required_cells_estimable=all(c.estimable for c in records),
        raw_api_primary_confirmatory=False,
        fixed_set_intersection_used=False,
        process_mean_is_estimand=False,
        original_training_source_superpopulation_generalization_claimed=False,
        cells=tuple(records),
        per_refit=tuple(per_refit),
    )


def certify_future_refit_probability_information_iut_v2(
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
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> RefitIUTInformationCertification:
    """Ordered-three-level information wrapper, still experimental."""

    if not str(score_name).strip():
        raise ValueError("score_name must be nonempty")
    rows, matrices = _score_matrices(levels)
    if len(rows)!=3:
        raise ValueError("v2 requires three ordered information levels")
    R,n = matrices[0].shape
    ids,order = _refit_ids(refit_ids,R)
    matrices=tuple(m[order] for m in matrices)
    w=_weights(sample_weight,n)
    for row,mat in zip(rows[:-1],matrices[:-1]):
        if not np.isfinite(mat[:,w>0]).all():
            raise ValueError(f"comparator {row.name} must be finite on positive-weight rows")
    steps=validate_information_filtration(
        [InformationLevelScore(row.name,row.information,[0.0]) for row in rows]
    )
    gains=np.stack([matrices[1]-matrices[0],matrices[2]-matrices[1]],axis=2)
    audit=certify_future_refit_probability_refit_iut_v2(
        gains,groups,blocks=blocks,refit_ids=ids,
        training_process_id=training_process_id,
        training_process_manifest_sha256=training_process_manifest_sha256,
        contrast_names=tuple(f"{step.lower_level}->{step.upper_level}" for step in steps),
        sample_weight=sample_weight,
        validation_alpha=validation_alpha,
        process_alpha=process_alpha,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )
    return RefitIUTInformationCertification(
        schema_version=2,
        method_version=METHOD_VERSION,
        score_name=str(score_name),
        levels=tuple(row.name for row in rows),
        steps=steps,
        audit=audit,
    )
