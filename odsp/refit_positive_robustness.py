"""Directional transfer robustness across a fixed supplied refit set.

This module deliberately does not treat upstream refits as an independent random
sample.  Each supplied refit is evaluated separately with an already-qualified
one-sided validation-sample bootstrap-t procedure.  A transfer step is declared
robust across refits only when every supplied refit robustly generalizes at that
step.

Statistically this is an intersection-union construction over a fixed refit set:
the global alternative is the intersection of the per-refit positive-transfer
alternatives.  Because the global claim requires every component refit test to
reject, no additional multiplicity correction is needed on the refit axis for
the fixed-set claim.  This does not justify generalization to an unsampled
population of possible refits, algorithms or training sets.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .information_transfer import InformationLevelScore, InformationTransferStep, validate_information_filtration
from .information_transfer_positive_v2 import (
    PositiveInformationTransferCertification,
    certify_positive_information_transfer_v2,
)
from .refit_information_transfer import (
    RefitInformationLevelScores,
    _labels,
    _refit_ids,
    _score_matrices,
    _weights,
)
from .shared_block_positive_information import (
    SharedBlockPositiveInformationTransferCertification,
    certify_shared_block_positive_information_transfer_v2,
)


@dataclass(frozen=True)
class RefitPositiveTransferAudit:
    refit_id: str
    certified_transfer_ceiling: str
    point_transfer_ceiling: str
    step_categories: tuple[str, ...]
    all_cells_estimable: bool
    bootstrap_t_critical_value: float | None
    certification: PositiveInformationTransferCertification | SharedBlockPositiveInformationTransferCertification

    def as_dict(self) -> dict[str, object]:
        return {
            "refit_id": self.refit_id,
            "certified_transfer_ceiling": self.certified_transfer_ceiling,
            "point_transfer_ceiling": self.point_transfer_ceiling,
            "step_categories": list(self.step_categories),
            "all_cells_estimable": self.all_cells_estimable,
            "bootstrap_t_critical_value": self.bootstrap_t_critical_value,
            "certification": self.certification.as_dict(),
        }


@dataclass(frozen=True)
class AllRefitStepRobustness:
    lower_level: str
    upper_level: str
    added_information: tuple[str, ...]
    refit_categories: tuple[str, ...]
    robust_refit_count: int
    not_robust_refit_count: int
    unavailable_refit_count: int
    category: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["added_information"] = list(self.added_information)
        payload["refit_categories"] = list(self.refit_categories)
        return payload


@dataclass(frozen=True)
class AllRefitPositiveTransferCertification:
    schema_version: int
    design: str
    score_name: str
    levels: tuple[str, ...]
    information_filtration_validated: bool
    refit_count: int
    refit_ids: tuple[str, ...]
    minimum_refits: int
    robustness_evaluable: bool
    familywise_lower_confidence_level: float
    validation_familywise_alpha: float
    bootstrap_draws_per_refit: int
    seed: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    alternative: str
    all_refit_certified_transfer_ceiling: str
    refit_certified_transfer_ceilings: tuple[str, ...]
    refit_ceiling_stability: str
    intersection_union_rule_used: bool
    all_supplied_refits_must_pass: bool
    additional_refit_axis_multiplicity_correction_applied: bool
    refit_independence_assumed: bool
    refit_sampling_distribution_assumed: bool
    refit_population_generalization_claimed: bool
    same_validation_bootstrap_seed_across_refits: bool
    reference_refit_can_override_failure: bool
    refit_average_can_override_failure: bool
    step_robustness: tuple[AllRefitStepRobustness, ...]
    per_refit: tuple[RefitPositiveTransferAudit, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "design": self.design,
            "score_name": self.score_name,
            "levels": list(self.levels),
            "information_filtration_validated": self.information_filtration_validated,
            "refit_count": self.refit_count,
            "refit_ids": list(self.refit_ids),
            "minimum_refits": self.minimum_refits,
            "robustness_evaluable": self.robustness_evaluable,
            "familywise_lower_confidence_level": self.familywise_lower_confidence_level,
            "validation_familywise_alpha": self.validation_familywise_alpha,
            "bootstrap_draws_per_refit": self.bootstrap_draws_per_refit,
            "seed": self.seed,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "gain_tolerance": self.gain_tolerance,
            "alternative": self.alternative,
            "all_refit_certified_transfer_ceiling": self.all_refit_certified_transfer_ceiling,
            "refit_certified_transfer_ceilings": list(self.refit_certified_transfer_ceilings),
            "refit_ceiling_stability": self.refit_ceiling_stability,
            "intersection_union_rule_used": self.intersection_union_rule_used,
            "all_supplied_refits_must_pass": self.all_supplied_refits_must_pass,
            "additional_refit_axis_multiplicity_correction_applied": self.additional_refit_axis_multiplicity_correction_applied,
            "refit_independence_assumed": self.refit_independence_assumed,
            "refit_sampling_distribution_assumed": self.refit_sampling_distribution_assumed,
            "refit_population_generalization_claimed": self.refit_population_generalization_claimed,
            "same_validation_bootstrap_seed_across_refits": self.same_validation_bootstrap_seed_across_refits,
            "reference_refit_can_override_failure": self.reference_refit_can_override_failure,
            "refit_average_can_override_failure": self.refit_average_can_override_failure,
            "step_robustness": [row.as_dict() for row in self.step_robustness],
            "per_refit": [row.as_dict() for row in self.per_refit],
        }


def _integer(value: int, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    value = int(value)
    if value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _step_category(categories: Sequence[str], *, evaluable: bool) -> str:
    values = tuple(categories)
    if not evaluable or any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_generalizing" for value in values):
        return "robust_across_refits"
    return "not_robust_across_refits"


def _ceiling(levels: tuple[str, ...], categories: Sequence[str]) -> str:
    ceiling = levels[0]
    for index, category in enumerate(categories):
        if category != "robust_across_refits":
            break
        ceiling = levels[index + 1]
    return ceiling


def _prepare(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    refit_ids: Sequence[object] | None,
    sample_weight: Sequence[float] | None,
    score_name: str,
    familywise_lower_confidence_level: float,
    bootstrap_draws: int,
    seed: int,
    minimum_refits: int,
    minimum_blocks_per_group: int,
    gain_tolerance: float,
):
    name = str(score_name).strip()
    if not name:
        raise ValueError("score_name must be non-empty")
    rows, matrices = _score_matrices(levels)
    refit_count, n = matrices[0].shape
    ids, order = _refit_ids(refit_ids, refit_count)
    matrices = tuple(matrix[order] for matrix in matrices)
    group = _labels(groups, n, name="groups")
    weight = _weights(sample_weight, n)
    minimum_refits = _integer(minimum_refits, name="minimum_refits", minimum=2)
    bootstrap_draws = _integer(bootstrap_draws, name="bootstrap_draws", minimum=500)
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group, name="minimum_blocks_per_group", minimum=2
    )
    seed = _integer(seed, name="seed", minimum=0)
    if not math.isfinite(familywise_lower_confidence_level) or not 0 < familywise_lower_confidence_level < 1:
        raise ValueError(
            "familywise_lower_confidence_level must lie strictly between zero and one"
        )
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    positive = weight > 0
    for row, matrix in zip(rows[:-1], matrices[:-1]):
        if not np.isfinite(matrix[:, positive]).all():
            raise ValueError(
                f"comparator level {row.name!r} must be finite on every positive-weight row for every refit"
            )

    steps = validate_information_filtration(
        [
            InformationLevelScore(row.name, row.information, [0.0])
            for row in rows
        ]
    )
    return (
        name,
        rows,
        matrices,
        ids,
        group,
        weight,
        steps,
        minimum_refits,
        bootstrap_draws,
        minimum_blocks_per_group,
        seed,
    )


def _aggregate(
    *,
    design: str,
    score_name: str,
    rows: Sequence[RefitInformationLevelScores],
    ids: tuple[str, ...],
    steps: tuple[InformationTransferStep, ...],
    minimum_refits: int,
    familywise_lower_confidence_level: float,
    bootstrap_draws: int,
    seed: int,
    minimum_blocks_per_group: int,
    gain_tolerance: float,
    audits: Sequence[RefitPositiveTransferAudit],
) -> AllRefitPositiveTransferCertification:
    audits = tuple(audits)
    evaluable = len(audits) >= minimum_refits
    step_rows: list[AllRefitStepRobustness] = []
    global_categories: list[str] = []
    for index, step in enumerate(steps):
        categories = tuple(audit.step_categories[index] for audit in audits)
        category = _step_category(categories, evaluable=evaluable)
        global_categories.append(category)
        step_rows.append(
            AllRefitStepRobustness(
                lower_level=step.lower_level,
                upper_level=step.upper_level,
                added_information=step.added_information,
                refit_categories=categories,
                robust_refit_count=categories.count("robust_generalizing"),
                not_robust_refit_count=categories.count("not_robust_generalizing"),
                unavailable_refit_count=categories.count("unavailable"),
                category=category,
            )
        )
    level_names = tuple(row.name for row in rows)
    ceilings = tuple(audit.certified_transfer_ceiling for audit in audits)
    return AllRefitPositiveTransferCertification(
        schema_version=1,
        design=design,
        score_name=score_name,
        levels=level_names,
        information_filtration_validated=True,
        refit_count=len(audits),
        refit_ids=ids,
        minimum_refits=minimum_refits,
        robustness_evaluable=evaluable,
        familywise_lower_confidence_level=float(familywise_lower_confidence_level),
        validation_familywise_alpha=float(1.0 - familywise_lower_confidence_level),
        bootstrap_draws_per_refit=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        alternative="greater",
        all_refit_certified_transfer_ceiling=(
            _ceiling(level_names, global_categories) if evaluable else level_names[0]
        ),
        refit_certified_transfer_ceilings=ceilings,
        refit_ceiling_stability=("stable" if len(set(ceilings)) <= 1 else "refit_sensitive"),
        intersection_union_rule_used=True,
        all_supplied_refits_must_pass=True,
        additional_refit_axis_multiplicity_correction_applied=False,
        refit_independence_assumed=False,
        refit_sampling_distribution_assumed=False,
        refit_population_generalization_claimed=False,
        same_validation_bootstrap_seed_across_refits=True,
        reference_refit_can_override_failure=False,
        refit_average_can_override_failure=False,
        step_robustness=tuple(step_rows),
        per_refit=audits,
    )


def certify_all_refit_positive_information_transfer_v2(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object] | None = None,
    refit_ids: Sequence[object] | None = None,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260915,
    minimum_refits: int = 2,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> AllRefitPositiveTransferCertification:
    """Require directional transfer certification in every supplied refit."""

    (
        name,
        rows,
        matrices,
        ids,
        group,
        weight,
        steps,
        minimum_refits,
        bootstrap_draws,
        minimum_blocks_per_group,
        seed,
    ) = _prepare(
        levels,
        groups,
        refit_ids=refit_ids,
        sample_weight=sample_weight,
        score_name=score_name,
        familywise_lower_confidence_level=familywise_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    audits: list[RefitPositiveTransferAudit] = []
    for refit_index, refit_id in enumerate(ids):
        local_levels = tuple(
            InformationLevelScore(
                row.name,
                row.information,
                matrices[level_index][refit_index],
            )
            for level_index, row in enumerate(rows)
        )
        result = certify_positive_information_transfer_v2(
            local_levels,
            group,
            score_name=name,
            blocks=blocks,
            sample_weight=weight,
            familywise_lower_confidence_level=familywise_lower_confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )
        audit = result.one_sided_bootstrap_t_audit
        audits.append(
            RefitPositiveTransferAudit(
                refit_id=refit_id,
                certified_transfer_ceiling=result.certified_transfer_ceiling,
                point_transfer_ceiling=result.point_result.predictive_result.all_group_point_transfer_ceiling,
                step_categories=tuple(row.category for row in audit.contrasts),
                all_cells_estimable=audit.all_cells_estimable,
                bootstrap_t_critical_value=audit.bootstrap_t_critical_value,
                certification=result,
            )
        )

    return _aggregate(
        design="independent_groups",
        score_name=name,
        rows=rows,
        ids=ids,
        steps=steps,
        minimum_refits=minimum_refits,
        familywise_lower_confidence_level=familywise_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
        audits=audits,
    )


def certify_all_refit_shared_block_positive_information_transfer_v2(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    shared_blocks: Sequence[object],
    *,
    refit_ids: Sequence[object] | None = None,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260915,
    minimum_refits: int = 2,
    minimum_shared_blocks: int = 8,
    gain_tolerance: float = 0.0,
) -> AllRefitPositiveTransferCertification:
    """Require directional paired transfer certification in every supplied refit."""

    (
        name,
        rows,
        matrices,
        ids,
        group,
        weight,
        steps,
        minimum_refits,
        bootstrap_draws,
        minimum_shared_blocks,
        seed,
    ) = _prepare(
        levels,
        groups,
        refit_ids=refit_ids,
        sample_weight=sample_weight,
        score_name=score_name,
        familywise_lower_confidence_level=familywise_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_shared_blocks,
        gain_tolerance=gain_tolerance,
    )

    audits: list[RefitPositiveTransferAudit] = []
    for refit_index, refit_id in enumerate(ids):
        local_levels = tuple(
            InformationLevelScore(
                row.name,
                row.information,
                matrices[level_index][refit_index],
            )
            for level_index, row in enumerate(rows)
        )
        result = certify_shared_block_positive_information_transfer_v2(
            local_levels,
            group,
            shared_blocks,
            score_name=name,
            sample_weight=weight,
            familywise_lower_confidence_level=familywise_lower_confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_shared_blocks=minimum_shared_blocks,
            gain_tolerance=gain_tolerance,
        )
        audit = result.paired_positive_certification
        audits.append(
            RefitPositiveTransferAudit(
                refit_id=refit_id,
                certified_transfer_ceiling=result.certified_transfer_ceiling,
                point_transfer_ceiling=result.point_transfer_ceiling,
                step_categories=tuple(row.category for row in audit.contrasts),
                all_cells_estimable=audit.all_cells_estimable,
                bootstrap_t_critical_value=audit.bootstrap_t_critical_value,
                certification=result,
            )
        )

    return _aggregate(
        design="shared_blocks",
        score_name=name,
        rows=rows,
        ids=ids,
        steps=steps,
        minimum_refits=minimum_refits,
        familywise_lower_confidence_level=familywise_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_shared_blocks,
        gain_tolerance=gain_tolerance,
        audits=audits,
    )
