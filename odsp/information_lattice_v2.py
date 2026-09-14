"""Prospective genuine bootstrap-t certification for complete information lattices.

The complete-lattice point estimand is unchanged.  Every directed subset edge is
placed into one global independent-group x edge validation family and certified
with the version-2 replicate-studentized cluster bootstrap-t engine.  Shapley
summaries remain descriptive point averages and cannot override edge failures.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .information_lattice import (
    InformationBlock,
    InformationLatticeNodeScore,
    InformationLatticePointAudit,
    LatticeBlockCertificationSummary,
    _block_certified_category,
    _edges,
    _path_count,
    _path_status,
    _validate_blocks,
    _validate_nodes,
    audit_information_lattice,
)
from .multicontrast_bootstrap_t import (
    ContrastBootstrapTSummary,
    IndependentGroupContrastBootstrapTAudit,
    certify_independent_group_contrasts_v2,
)


@dataclass(frozen=True)
class InformationLatticeV2EdgeSummary:
    lower_blocks: tuple[str, ...]
    upper_blocks: tuple[str, ...]
    added_block: str
    bootstrap_t_summary: ContrastBootstrapTSummary

    def as_dict(self) -> dict[str, object]:
        return {
            "lower_blocks": list(self.lower_blocks),
            "upper_blocks": list(self.upper_blocks),
            "added_block": self.added_block,
            "bootstrap_t_summary": self.bootstrap_t_summary.as_dict(),
        }


@dataclass(frozen=True)
class InformationLatticeV2Certification:
    point_audit: InformationLatticePointAudit
    bootstrap_t_audit: IndependentGroupContrastBootstrapTAudit
    edges: tuple[InformationLatticeV2EdgeSummary, ...]
    block_summaries: tuple[LatticeBlockCertificationSummary, ...]
    total_admissible_path_count: int
    robust_full_transfer_path_count: int
    robust_full_transfer_path_fraction: float
    certified_path_status: str
    all_edges_robust_generalizing: bool
    total_gain_can_override_failed_edge: bool
    shapley_can_override_edge_failure: bool
    validation_sample_uncertainty_method: str
    upstream_refit_uncertainty_included: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "point_audit": self.point_audit.as_dict(),
            "bootstrap_t_audit": self.bootstrap_t_audit.as_dict(),
            "edges": [row.as_dict() for row in self.edges],
            "block_summaries": [row.as_dict() for row in self.block_summaries],
            "total_admissible_path_count": self.total_admissible_path_count,
            "robust_full_transfer_path_count": self.robust_full_transfer_path_count,
            "robust_full_transfer_path_fraction": self.robust_full_transfer_path_fraction,
            "certified_path_status": self.certified_path_status,
            "all_edges_robust_generalizing": self.all_edges_robust_generalizing,
            "total_gain_can_override_failed_edge": self.total_gain_can_override_failed_edge,
            "shapley_can_override_edge_failure": self.shapley_can_override_edge_failure,
            "validation_sample_uncertainty_method": self.validation_sample_uncertainty_method,
            "upstream_refit_uncertainty_included": self.upstream_refit_uncertainty_included,
        }


def certify_information_lattice_v2(
    nodes: Sequence[InformationLatticeNodeScore],
    information_blocks: Sequence[InformationBlock],
    groups: Sequence[object],
    *,
    base_information: Sequence[str] = (),
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260914,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> InformationLatticeV2Certification:
    """Certify every complete-lattice edge with genuine bootstrap-t intervals."""

    point = audit_information_lattice(
        nodes,
        information_blocks,
        groups,
        base_information=base_information,
        sample_weight=sample_weight,
        gain_tolerance=gain_tolerance,
    )
    block_rows = _validate_blocks(information_blocks)
    block_order = tuple(row.name for row in block_rows)
    score_by_subset, _ = _validate_nodes(nodes, block_order)
    edge_defs = _edges(block_order)
    row_gain = np.column_stack(
        [score_by_subset[upper] - score_by_subset[lower] for lower, upper, _ in edge_defs]
    )
    contrast_names = tuple(
        f"{'+'.join(lower) if lower else 'base'}->{'+'.join(upper)}"
        for lower, upper, _ in edge_defs
    )
    audit = certify_independent_group_contrasts_v2(
        row_gain,
        groups,
        blocks=blocks,
        contrast_names=contrast_names,
        sample_weight=sample_weight,
        familywise_confidence_level=familywise_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    edge_rows: list[InformationLatticeV2EdgeSummary] = []
    category_by_edge: dict[tuple[tuple[str, ...], str], str] = {}
    for edge_def, summary in zip(edge_defs, audit.contrasts):
        lower, upper, added = edge_def
        category_by_edge[(lower, added)] = summary.category
        edge_rows.append(
            InformationLatticeV2EdgeSummary(
                lower_blocks=lower,
                upper_blocks=upper,
                added_block=added,
                bootstrap_t_summary=summary,
            )
        )

    block_summaries = tuple(
        LatticeBlockCertificationSummary(
            block=block,
            edge_count=sum(1 for _, _, added in edge_defs if added == block),
            order_robust_category=_block_certified_category(
                [
                    category_by_edge[(lower, added)]
                    for lower, _, added in edge_defs
                    if added == block
                ]
            ),
        )
        for block in block_order
    )
    successful = {
        key
        for key, category in category_by_edge.items()
        if category == "robust_generalizing"
    }
    total_paths = int(np.math.factorial(len(block_order))) if hasattr(np, "math") else 0
    # NumPy 2 no longer exposes np.math; retain an explicit standard-library path.
    if total_paths == 0:
        import math
        total_paths = math.factorial(len(block_order))
    robust_paths = _path_count(block_order, successful)

    return InformationLatticeV2Certification(
        point_audit=point,
        bootstrap_t_audit=audit,
        edges=tuple(edge_rows),
        block_summaries=block_summaries,
        total_admissible_path_count=total_paths,
        robust_full_transfer_path_count=robust_paths,
        robust_full_transfer_path_fraction=float(robust_paths / total_paths),
        certified_path_status=_path_status(robust_paths, total_paths),
        all_edges_robust_generalizing=bool(robust_paths == total_paths),
        total_gain_can_override_failed_edge=False,
        shapley_can_override_edge_failure=False,
        validation_sample_uncertainty_method=(
            "replicate_studentized_cluster_ratio_max_t_v2"
        ),
        upstream_refit_uncertainty_included=False,
    )
