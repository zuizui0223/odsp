"""Directional positive-transfer ceiling using one-sided bootstrap-t lower bounds.

This wrapper preserves the strict information filtration and non-skippable ceiling
logic.  It differs from :mod:`odsp.information_transfer_v2` only in the
predeclared directional inferential target: the confirmatory question is whether
every independent group has a gain strictly above the declared tolerance.

The two-sided v2 route remains available when negative departures are also part
of the simultaneous inferential target.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .information_transfer import (
    InformationLevelScore,
    InformationTransferResult,
    InformationTransferStep,
    decompose_information_transfer,
    validate_information_filtration,
)
from .positive_transfer_bootstrap_t import (
    IndependentGroupPositiveTransferBootstrapTAudit,
    certify_independent_group_positive_transfer_v2,
)


@dataclass(frozen=True)
class PositiveInformationTransferCertification:
    score_name: str
    filtration_validated: bool
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    point_result: InformationTransferResult
    one_sided_bootstrap_t_audit: IndependentGroupPositiveTransferBootstrapTAudit
    certified_transfer_ceiling: str
    validation_sample_uncertainty_method: str
    alternative: str
    upstream_refit_uncertainty_included: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "score_name": self.score_name,
            "filtration_validated": self.filtration_validated,
            "levels": list(self.levels),
            "steps": [row.as_dict() for row in self.steps],
            "point_result": self.point_result.as_dict(),
            "one_sided_bootstrap_t_audit": self.one_sided_bootstrap_t_audit.as_dict(),
            "certified_transfer_ceiling": self.certified_transfer_ceiling,
            "validation_sample_uncertainty_method": self.validation_sample_uncertainty_method,
            "alternative": self.alternative,
            "upstream_refit_uncertainty_included": self.upstream_refit_uncertainty_included,
        }


def certify_positive_information_transfer_v2(
    levels: Sequence[InformationLevelScore],
    groups: Sequence[object],
    *,
    score_name: str = "log",
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260915,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> PositiveInformationTransferCertification:
    """Certify a strict filtration for the directional claim ``gain > tolerance``."""

    rows = tuple(levels)
    steps = validate_information_filtration(rows)
    point = decompose_information_transfer(
        rows,
        groups,
        score_name=score_name,
        sample_weight=sample_weight,
        gain_tolerance=gain_tolerance,
    )
    score_arrays = tuple(np.asarray(row.score, dtype=float) for row in rows)
    row_gain = np.column_stack(
        [score_arrays[index + 1] - score_arrays[index] for index in range(len(steps))]
    )
    contrast_names = tuple(
        f"{step.lower_level}->{step.upper_level}" for step in steps
    )
    audit = certify_independent_group_positive_transfer_v2(
        row_gain,
        groups,
        blocks=blocks,
        contrast_names=contrast_names,
        sample_weight=sample_weight,
        familywise_lower_confidence_level=familywise_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    ceiling = rows[0].name
    for index, summary in enumerate(audit.contrasts):
        if summary.category != "robust_generalizing":
            break
        ceiling = rows[index + 1].name

    return PositiveInformationTransferCertification(
        score_name=str(score_name).strip(),
        filtration_validated=True,
        levels=tuple(row.name for row in rows),
        steps=steps,
        point_result=point,
        one_sided_bootstrap_t_audit=audit,
        certified_transfer_ceiling=ceiling,
        validation_sample_uncertainty_method=(
            "one_sided_replicate_studentized_cluster_ratio_max_t_v2"
        ),
        alternative="greater",
        upstream_refit_uncertainty_included=False,
    )
