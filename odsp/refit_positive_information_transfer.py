"""Directional information-transfer certification across upstream refits.

The directional bootstrap-t engine controls validation-sample uncertainty *within*
a fitted refit.  Upstream refits are then treated as an explicit empirical
sensitivity ensemble rather than as IID draws from a refit population.

A transfer step is refit-robust only when every supplied refit has a
``robust_generalizing`` one-sided validation result for that step.  This keeps the
one-sided confidence statement attached to validation sampling while making the
upstream-model uncertainty rule deterministic and fail-closed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
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


@dataclass(frozen=True)
class RefitPositiveStepSensitivity:
    lower_level: str
    upper_level: str
    added_information: tuple[str, ...]
    per_refit_categories: tuple[str, ...]
    robust_positive_refit_count: int
    not_robust_positive_refit_count: int
    unavailable_refit_count: int
    refit_consensus_category: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["added_information"] = list(self.added_information)
        payload["per_refit_categories"] = list(self.per_refit_categories)
        return payload


@dataclass(frozen=True)
class RefitPositiveInformationTransferSensitivity:
    score_name: str
    levels: tuple[str, ...]
    information_filtration_validated: bool
    refit_count: int
    refit_ids: tuple[str, ...]
    reference_refit_id: str
    minimum_refits: int
    minimum_refits_satisfied: bool
    validation_familywise_lower_confidence_level: float
    validation_bootstrap_draws: int
    validation_seed: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    per_refit_certified_transfer_ceilings: tuple[str, ...]
    reference_refit_certified_transfer_ceiling: str
    refit_consensus_certified_transfer_ceiling: str
    refit_ceiling_stability: str
    all_refits_must_support_each_step: bool
    refit_ensemble_probability_sample_assumed: bool
    population_refit_confidence_claimed: bool
    validation_confidence_is_conditional_on_each_refit: bool
    upstream_refit_uncertainty_included_as_empirical_sensitivity: bool
    reference_refit_can_override_consensus_failure: bool
    total_gain_can_override_failed_step: bool
    steps: tuple[RefitPositiveStepSensitivity, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "score_name": self.score_name,
            "levels": list(self.levels),
            "information_filtration_validated": self.information_filtration_validated,
            "refit_count": self.refit_count,
            "refit_ids": list(self.refit_ids),
            "reference_refit_id": self.reference_refit_id,
            "minimum_refits": self.minimum_refits,
            "minimum_refits_satisfied": self.minimum_refits_satisfied,
            "validation_familywise_lower_confidence_level": self.validation_familywise_lower_confidence_level,
            "validation_bootstrap_draws": self.validation_bootstrap_draws,
            "validation_seed": self.validation_seed,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "gain_tolerance": self.gain_tolerance,
            "per_refit_certified_transfer_ceilings": list(self.per_refit_certified_transfer_ceilings),
            "reference_refit_certified_transfer_ceiling": self.reference_refit_certified_transfer_ceiling,
            "refit_consensus_certified_transfer_ceiling": self.refit_consensus_certified_transfer_ceiling,
            "refit_ceiling_stability": self.refit_ceiling_stability,
            "all_refits_must_support_each_step": self.all_refits_must_support_each_step,
            "refit_ensemble_probability_sample_assumed": self.refit_ensemble_probability_sample_assumed,
            "population_refit_confidence_claimed": self.population_refit_confidence_claimed,
            "validation_confidence_is_conditional_on_each_refit": self.validation_confidence_is_conditional_on_each_refit,
            "upstream_refit_uncertainty_included_as_empirical_sensitivity": self.upstream_refit_uncertainty_included_as_empirical_sensitivity,
            "reference_refit_can_override_consensus_failure": self.reference_refit_can_override_consensus_failure,
            "total_gain_can_override_failed_step": self.total_gain_can_override_failed_step,
            "steps": [row.as_dict() for row in self.steps],
        }


def _consensus_category(categories: Sequence[str], *, minimum_refits_satisfied: bool) -> str:
    values = tuple(categories)
    if not minimum_refits_satisfied or not values:
        return "unavailable"
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if all(value == "robust_generalizing" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def _ceiling(level_names: tuple[str, ...], categories: Sequence[str]) -> str:
    ceiling = level_names[0]
    for index, category in enumerate(categories):
        if category != "robust_generalizing":
            break
        ceiling = level_names[index + 1]
    return ceiling


def certify_refit_positive_information_transfer(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object] | None = None,
    reference_refit_id: object | None = None,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260916,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> RefitPositiveInformationTransferSensitivity:
    """Audit directional transfer across an explicit upstream-refit ensemble.

    Each supplied refit is certified independently with the calibrated one-sided
    validation bootstrap-t method, using the same declared held-out rows, groups,
    blocks, weights and bootstrap seed.  The refit-aware ceiling then advances
    only through steps that are ``robust_generalizing`` for *every* supplied
    refit.  Refit IDs are sorted before evaluation, so input order cannot alter
    the result.

    The confidence statement is conditional on each fitted refit.  Across-refit
    aggregation is an empirical sensitivity rule, not a confidence interval over
    a hypothetical population of refits.
    """

    if isinstance(minimum_refits, bool) or not isinstance(minimum_refits, int) or minimum_refits < 2:
        raise ValueError("minimum_refits must be an integer >= 2")

    rows, matrices = _score_matrices(levels)
    refit_count, n = matrices[0].shape
    group = _labels(groups, n, name="groups")
    block = _labels(blocks, n, name="blocks")
    weight = _weights(sample_weight, n)
    ids, order = _refit_ids(refit_ids, refit_count)
    matrices = tuple(matrix[order] for matrix in matrices)
    reference_id = ids[0] if reference_refit_id is None else str(reference_refit_id).strip()
    if reference_id not in ids:
        raise ValueError("reference_refit_id must identify one supplied refit")
    reference_index = ids.index(reference_id)

    step_defs: tuple[InformationTransferStep, ...] = validate_information_filtration(
        [InformationLevelScore(row.name, row.information, [0.0]) for row in rows]
    )
    level_names = tuple(row.name for row in rows)
    minimum_ok = refit_count >= minimum_refits

    certifications: list[PositiveInformationTransferCertification] = []
    per_refit_ceilings: list[str] = []
    per_step_categories: list[list[str]] = [[] for _ in step_defs]

    for refit_index in range(refit_count):
        local_levels = [
            InformationLevelScore(
                name=row.name,
                information=row.information,
                score=matrix[refit_index],
            )
            for row, matrix in zip(rows, matrices)
        ]
        certification = certify_positive_information_transfer_v2(
            local_levels,
            group,
            score_name=score_name,
            blocks=block,
            sample_weight=weight,
            familywise_lower_confidence_level=familywise_lower_confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )
        certifications.append(certification)
        per_refit_ceilings.append(certification.certified_transfer_ceiling)
        for step_index, contrast in enumerate(certification.one_sided_bootstrap_t_audit.contrasts):
            per_step_categories[step_index].append(contrast.category)

    step_rows: list[RefitPositiveStepSensitivity] = []
    consensus_categories: list[str] = []
    for step_index, step in enumerate(step_defs):
        categories = tuple(per_step_categories[step_index])
        consensus = _consensus_category(categories, minimum_refits_satisfied=minimum_ok)
        consensus_categories.append(consensus)
        step_rows.append(
            RefitPositiveStepSensitivity(
                lower_level=step.lower_level,
                upper_level=step.upper_level,
                added_information=step.added_information,
                per_refit_categories=categories,
                robust_positive_refit_count=categories.count("robust_generalizing"),
                not_robust_positive_refit_count=categories.count("not_robust_generalizing"),
                unavailable_refit_count=categories.count("unavailable"),
                refit_consensus_category=consensus,
            )
        )

    consensus_ceiling = _ceiling(level_names, consensus_categories)
    ceiling_stability = "stable" if len(set(per_refit_ceilings)) == 1 else "variable"

    return RefitPositiveInformationTransferSensitivity(
        score_name=str(score_name).strip(),
        levels=level_names,
        information_filtration_validated=True,
        refit_count=refit_count,
        refit_ids=ids,
        reference_refit_id=reference_id,
        minimum_refits=minimum_refits,
        minimum_refits_satisfied=minimum_ok,
        validation_familywise_lower_confidence_level=float(familywise_lower_confidence_level),
        validation_bootstrap_draws=int(bootstrap_draws),
        validation_seed=int(seed),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        gain_tolerance=float(gain_tolerance),
        per_refit_certified_transfer_ceilings=tuple(per_refit_ceilings),
        reference_refit_certified_transfer_ceiling=per_refit_ceilings[reference_index],
        refit_consensus_certified_transfer_ceiling=consensus_ceiling,
        refit_ceiling_stability=ceiling_stability,
        all_refits_must_support_each_step=True,
        refit_ensemble_probability_sample_assumed=False,
        population_refit_confidence_claimed=False,
        validation_confidence_is_conditional_on_each_refit=True,
        upstream_refit_uncertainty_included_as_empirical_sensitivity=True,
        reference_refit_can_override_consensus_failure=False,
        total_gain_can_override_failed_step=False,
        steps=tuple(step_rows),
    )
