"""Fixed-set all-refit robustness for calibrated paired directional lattices.

Each supplied upstream refit is evaluated separately with the paired one-sided
familywise bootstrap-t lattice procedure.  The across-refit claim is then an
intersection-union statement over the fixed supplied refit set: an edge is
robust across refits only when every supplied refit robustly generalizes on that
same edge.

Global paths are recomputed from the intersection of robust edges.  Therefore,
different refits having different successful paths cannot be combined into a
synthetic cross-refit path.  No refit independence or refit-population sampling
model is assumed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .information_lattice import (
    InformationBlock,
    InformationLatticeNodeScore,
    _edges,
    _path_count,
    _path_status,
    _validate_blocks,
)
from .predictive_resolution import _validate_groups, _validate_weights
from .refit_information_lattice import (
    RefitInformationLatticeNodeScores,
    _refit_ids,
    _validate_refit_nodes,
)
from .shared_block_positive_information import (
    SharedBlockPositiveInformationLatticeCertification,
    certify_shared_block_positive_information_lattice_v2,
)


@dataclass(frozen=True)
class RefitPositiveLatticeAudit:
    refit_id: str
    edge_categories: tuple[str, ...]
    robust_full_transfer_path_count: int
    certified_path_status: str
    all_cells_estimable: bool
    bootstrap_t_critical_value: float | None
    certification: SharedBlockPositiveInformationLatticeCertification

    def as_dict(self) -> dict[str, object]:
        return {
            "refit_id": self.refit_id,
            "edge_categories": list(self.edge_categories),
            "robust_full_transfer_path_count": self.robust_full_transfer_path_count,
            "certified_path_status": self.certified_path_status,
            "all_cells_estimable": self.all_cells_estimable,
            "bootstrap_t_critical_value": self.bootstrap_t_critical_value,
            "certification": self.certification.as_dict(),
        }


@dataclass(frozen=True)
class AllRefitPositiveLatticeEdgeRobustness:
    lower_blocks: tuple[str, ...]
    upper_blocks: tuple[str, ...]
    added_block: str
    refit_categories: tuple[str, ...]
    robust_refit_count: int
    not_robust_refit_count: int
    unavailable_refit_count: int
    category: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["lower_blocks"] = list(self.lower_blocks)
        payload["upper_blocks"] = list(self.upper_blocks)
        payload["refit_categories"] = list(self.refit_categories)
        return payload


@dataclass(frozen=True)
class AllRefitPositiveLatticeBlockRobustness:
    block: str
    edge_count: int
    category: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AllRefitPairedPositiveLatticeCertification:
    schema_version: int
    design: str
    information_block_count: int
    edge_count: int
    calibrated_family_size_edge_count: int
    refit_count: int
    refit_ids: tuple[str, ...]
    minimum_refits: int
    robustness_evaluable: bool
    familywise_lower_confidence_level: float
    bootstrap_draws_per_refit: int
    seed: int
    minimum_shared_blocks: int
    gain_tolerance: float
    alternative: str
    total_admissible_path_count: int
    all_refit_robust_full_transfer_path_count: int
    all_refit_robust_full_transfer_path_fraction: float
    all_refit_certified_path_status: str
    refit_certified_path_statuses: tuple[str, ...]
    refit_robust_full_transfer_path_counts: tuple[int, ...]
    refit_path_stability: str
    intersection_union_rule_used: bool
    all_supplied_refits_must_pass_same_edge: bool
    different_refit_paths_can_be_combined: bool
    additional_refit_axis_multiplicity_correction_applied: bool
    refit_independence_assumed: bool
    refit_sampling_distribution_assumed: bool
    refit_population_generalization_claimed: bool
    same_validation_bootstrap_seed_across_refits: bool
    validation_group_independence_assumed: bool
    exact_shared_block_support_required: bool
    shared_block_exchangeability_assumed: bool
    best_path_can_override_failed_edge: bool
    shapley_can_override_edge_failure: bool
    edges: tuple[AllRefitPositiveLatticeEdgeRobustness, ...]
    block_summaries: tuple[AllRefitPositiveLatticeBlockRobustness, ...]
    per_refit: tuple[RefitPositiveLatticeAudit, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "design": self.design,
            "information_block_count": self.information_block_count,
            "edge_count": self.edge_count,
            "calibrated_family_size_edge_count": self.calibrated_family_size_edge_count,
            "refit_count": self.refit_count,
            "refit_ids": list(self.refit_ids),
            "minimum_refits": self.minimum_refits,
            "robustness_evaluable": self.robustness_evaluable,
            "familywise_lower_confidence_level": self.familywise_lower_confidence_level,
            "bootstrap_draws_per_refit": self.bootstrap_draws_per_refit,
            "seed": self.seed,
            "minimum_shared_blocks": self.minimum_shared_blocks,
            "gain_tolerance": self.gain_tolerance,
            "alternative": self.alternative,
            "total_admissible_path_count": self.total_admissible_path_count,
            "all_refit_robust_full_transfer_path_count": self.all_refit_robust_full_transfer_path_count,
            "all_refit_robust_full_transfer_path_fraction": self.all_refit_robust_full_transfer_path_fraction,
            "all_refit_certified_path_status": self.all_refit_certified_path_status,
            "refit_certified_path_statuses": list(self.refit_certified_path_statuses),
            "refit_robust_full_transfer_path_counts": list(self.refit_robust_full_transfer_path_counts),
            "refit_path_stability": self.refit_path_stability,
            "intersection_union_rule_used": self.intersection_union_rule_used,
            "all_supplied_refits_must_pass_same_edge": self.all_supplied_refits_must_pass_same_edge,
            "different_refit_paths_can_be_combined": self.different_refit_paths_can_be_combined,
            "additional_refit_axis_multiplicity_correction_applied": self.additional_refit_axis_multiplicity_correction_applied,
            "refit_independence_assumed": self.refit_independence_assumed,
            "refit_sampling_distribution_assumed": self.refit_sampling_distribution_assumed,
            "refit_population_generalization_claimed": self.refit_population_generalization_claimed,
            "same_validation_bootstrap_seed_across_refits": self.same_validation_bootstrap_seed_across_refits,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "exact_shared_block_support_required": self.exact_shared_block_support_required,
            "shared_block_exchangeability_assumed": self.shared_block_exchangeability_assumed,
            "best_path_can_override_failed_edge": self.best_path_can_override_failed_edge,
            "shapley_can_override_edge_failure": self.shapley_can_override_edge_failure,
            "edges": [row.as_dict() for row in self.edges],
            "block_summaries": [row.as_dict() for row in self.block_summaries],
            "per_refit": [row.as_dict() for row in self.per_refit],
        }


def _integer(value: int, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    value = int(value)
    if value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _global_edge_category(categories: Sequence[str], *, evaluable: bool) -> str:
    values = tuple(categories)
    if not evaluable or any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_generalizing" for value in values):
        return "robust_across_refits"
    return "not_robust_across_refits"


def _global_block_category(categories: Sequence[str], *, evaluable: bool) -> str:
    values = tuple(categories)
    if not evaluable or any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_across_refits" for value in values):
        return "robust_across_refits"
    return "not_robust_across_refits"


def certify_all_refit_shared_block_positive_information_lattice_v2(
    nodes: Sequence[RefitInformationLatticeNodeScores],
    information_blocks: Sequence[InformationBlock],
    groups: Sequence[object],
    shared_blocks: Sequence[object],
    *,
    base_information: Sequence[str] = (),
    refit_ids: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260916,
    minimum_refits: int = 2,
    minimum_shared_blocks: int = 8,
    gain_tolerance: float = 0.0,
) -> AllRefitPairedPositiveLatticeCertification:
    """Require the same paired directional lattice edges in every supplied refit.

    Only complete lattices with two or three added information blocks are
    accepted.  These correspond to 4-edge and 12-edge simultaneous families,
    the family sizes prospectively calibrated for the paired directional route.
    """

    block_rows = _validate_blocks(information_blocks)
    block_order = tuple(row.name for row in block_rows)
    information_block_count = len(block_order)
    if information_block_count not in {2, 3}:
        raise ValueError(
            "all-refit paired directional lattice is qualified only for 2 or 3 "
            "information blocks (4 or 12 directed edges)"
        )
    base = tuple(str(value).strip() for value in base_information)
    if any(not value for value in base) or len(set(base)) != len(base):
        raise ValueError("base_information must contain unique non-empty labels")
    block_variables = {value for row in block_rows for value in row.variables}
    overlap = set(base) & block_variables
    if overlap:
        raise ValueError(
            "base_information must be disjoint from added information blocks; "
            f"overlap={tuple(sorted(overlap))!r}"
        )

    score_by_subset, refit_count, n = _validate_refit_nodes(nodes, block_order)
    ids, order = _refit_ids(refit_ids, refit_count)
    score_by_subset = {
        subset: matrix[order] for subset, matrix in score_by_subset.items()
    }
    group = _validate_groups(groups, n)
    weight = _validate_weights(sample_weight, n)
    shared_block = np.asarray(list(shared_blocks), dtype=object)
    if shared_block.shape != (n,):
        raise ValueError("shared_blocks must contain one value per held-out row")
    for value in shared_block.tolist():
        if value is None:
            raise ValueError("shared-block labels may not be missing")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("shared-block labels must be hashable") from exc

    minimum_refits = _integer(minimum_refits, name="minimum_refits", minimum=2)
    bootstrap_draws = _integer(bootstrap_draws, name="bootstrap_draws", minimum=500)
    minimum_shared_blocks = _integer(
        minimum_shared_blocks, name="minimum_shared_blocks", minimum=2
    )
    seed = _integer(seed, name="seed", minimum=0)
    if (
        not math.isfinite(familywise_lower_confidence_level)
        or not 0 < familywise_lower_confidence_level < 1
    ):
        raise ValueError(
            "familywise_lower_confidence_level must lie strictly between zero and one"
        )
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    positive = weight > 0
    full_subset = block_order
    for subset, matrix in score_by_subset.items():
        if subset != full_subset and not np.isfinite(matrix[:, positive]).all():
            raise ValueError(
                f"comparator lattice node {subset!r} must be finite on every "
                "positive-weight row for every refit"
            )

    edge_defs = _edges(block_order)
    edge_count = len(edge_defs)
    expected_edge_count = information_block_count * 2 ** (information_block_count - 1)
    if edge_count != expected_edge_count:
        raise AssertionError("complete lattice edge count is inconsistent")

    audits: list[RefitPositiveLatticeAudit] = []
    per_edge_categories: list[list[str]] = [[] for _ in edge_defs]
    for refit_index, refit_id in enumerate(ids):
        local_nodes = tuple(
            InformationLatticeNodeScore(
                blocks=subset,
                score=matrix[refit_index],
            )
            for subset, matrix in score_by_subset.items()
        )
        result = certify_shared_block_positive_information_lattice_v2(
            local_nodes,
            block_rows,
            group,
            shared_block,
            base_information=base,
            sample_weight=weight,
            familywise_lower_confidence_level=familywise_lower_confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_shared_blocks=minimum_shared_blocks,
            gain_tolerance=gain_tolerance,
        )
        categories = tuple(edge.category for edge in result.edges)
        if len(categories) != edge_count:
            raise AssertionError("paired lattice edge count changed across refits")
        for edge_index, category in enumerate(categories):
            per_edge_categories[edge_index].append(category)
        audits.append(
            RefitPositiveLatticeAudit(
                refit_id=refit_id,
                edge_categories=categories,
                robust_full_transfer_path_count=result.robust_full_transfer_path_count,
                certified_path_status=result.certified_path_status,
                all_cells_estimable=result.paired_positive_certification.all_cells_estimable,
                bootstrap_t_critical_value=result.paired_positive_certification.bootstrap_t_critical_value,
                certification=result,
            )
        )

    evaluable = refit_count >= minimum_refits
    edge_rows: list[AllRefitPositiveLatticeEdgeRobustness] = []
    global_categories: dict[tuple[tuple[str, ...], str], str] = {}
    for edge_index, (lower, upper, added) in enumerate(edge_defs):
        categories = tuple(per_edge_categories[edge_index])
        category = _global_edge_category(categories, evaluable=evaluable)
        global_categories[(lower, added)] = category
        edge_rows.append(
            AllRefitPositiveLatticeEdgeRobustness(
                lower_blocks=lower,
                upper_blocks=upper,
                added_block=added,
                refit_categories=categories,
                robust_refit_count=categories.count("robust_generalizing"),
                not_robust_refit_count=categories.count("not_robust_generalizing"),
                unavailable_refit_count=categories.count("unavailable"),
                category=category,
            )
        )

    block_summaries = tuple(
        AllRefitPositiveLatticeBlockRobustness(
            block=block_name,
            edge_count=sum(1 for _, _, added in edge_defs if added == block_name),
            category=_global_block_category(
                [
                    global_categories[(lower, added)]
                    for lower, _, added in edge_defs
                    if added == block_name
                ],
                evaluable=evaluable,
            ),
        )
        for block_name in block_order
    )

    successful = {
        (lower, added)
        for lower, _, added in edge_defs
        if global_categories[(lower, added)] == "robust_across_refits"
    }
    total_paths = math.factorial(information_block_count)
    robust_paths = _path_count(block_order, successful) if evaluable else 0
    path_status = _path_status(robust_paths, total_paths) if evaluable else "unavailable"
    refit_statuses = tuple(audit.certified_path_status for audit in audits)
    refit_counts = tuple(audit.robust_full_transfer_path_count for audit in audits)

    return AllRefitPairedPositiveLatticeCertification(
        schema_version=1,
        design="shared_blocks",
        information_block_count=information_block_count,
        edge_count=edge_count,
        calibrated_family_size_edge_count=expected_edge_count,
        refit_count=refit_count,
        refit_ids=ids,
        minimum_refits=minimum_refits,
        robustness_evaluable=evaluable,
        familywise_lower_confidence_level=float(familywise_lower_confidence_level),
        bootstrap_draws_per_refit=bootstrap_draws,
        seed=seed,
        minimum_shared_blocks=minimum_shared_blocks,
        gain_tolerance=float(gain_tolerance),
        alternative="greater",
        total_admissible_path_count=total_paths,
        all_refit_robust_full_transfer_path_count=robust_paths,
        all_refit_robust_full_transfer_path_fraction=float(robust_paths / total_paths),
        all_refit_certified_path_status=path_status,
        refit_certified_path_statuses=refit_statuses,
        refit_robust_full_transfer_path_counts=refit_counts,
        refit_path_stability=("stable" if len(set(refit_statuses)) <= 1 else "refit_sensitive"),
        intersection_union_rule_used=True,
        all_supplied_refits_must_pass_same_edge=True,
        different_refit_paths_can_be_combined=False,
        additional_refit_axis_multiplicity_correction_applied=False,
        refit_independence_assumed=False,
        refit_sampling_distribution_assumed=False,
        refit_population_generalization_claimed=False,
        same_validation_bootstrap_seed_across_refits=True,
        validation_group_independence_assumed=False,
        exact_shared_block_support_required=True,
        shared_block_exchangeability_assumed=True,
        best_path_can_override_failed_edge=False,
        shapley_can_override_edge_failure=False,
        edges=tuple(edge_rows),
        block_summaries=block_summaries,
        per_refit=tuple(audits),
    )
