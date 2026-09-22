"""Directional one-sided certification for qualified independent information lattices.

The prospective wrapper accepts exactly two or three scientifically unordered
information blocks. Complete two- and three-block lattices contain four and
twelve directed edges, respectively, and map onto prospectively qualified
independent-group one-sided bootstrap-t family sizes.

Four-block (32-edge) and larger independent directional lattices remain
unqualified.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .information_lattice import (
    InformationBlock,
    InformationLatticeNodeScore,
    InformationLatticePointAudit,
    _edges,
    _path_count,
    _path_status,
    _validate_blocks,
    _validate_nodes,
    audit_information_lattice,
)
from .positive_transfer_bootstrap_t import (
    IndependentGroupPositiveTransferBootstrapTAudit,
    certify_independent_group_positive_transfer_v2,
)


@dataclass(frozen=True)
class PositiveInformationLatticeEdgeSummary:
    lower_blocks: tuple[str, ...]
    upper_blocks: tuple[str, ...]
    added_block: str
    category: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["lower_blocks"] = list(self.lower_blocks)
        payload["upper_blocks"] = list(self.upper_blocks)
        return payload


@dataclass(frozen=True)
class PositiveInformationLatticeBlockSummary:
    block: str
    edge_count: int
    directional_order_robust_category: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PositiveInformationLatticeCertification:
    point_audit: InformationLatticePointAudit
    one_sided_bootstrap_t_audit: IndependentGroupPositiveTransferBootstrapTAudit
    edges: tuple[PositiveInformationLatticeEdgeSummary, ...]
    block_summaries: tuple[PositiveInformationLatticeBlockSummary, ...]
    edge_count: int
    total_admissible_path_count: int
    robust_full_transfer_path_count: int
    robust_full_transfer_path_fraction: float
    certified_path_status: str
    all_edges_robust_generalizing: bool
    alternative: str
    validation_group_independence_assumed: bool
    calibrated_family_size_edge_count: int
    qualification_inherited_from_four_contrast_panel: bool
    qualification_inherited_from_twelve_contrast_panel: bool
    total_gain_can_override_failed_edge: bool
    best_path_can_override_failed_edge: bool
    shapley_can_override_edge_failure: bool
    upstream_refit_uncertainty_included: bool
    untouched_external_validation_included: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "point_audit": self.point_audit.as_dict(),
            "one_sided_bootstrap_t_audit": self.one_sided_bootstrap_t_audit.as_dict(),
            "edges": [row.as_dict() for row in self.edges],
            "block_summaries": [row.as_dict() for row in self.block_summaries],
            "edge_count": self.edge_count,
            "total_admissible_path_count": self.total_admissible_path_count,
            "robust_full_transfer_path_count": self.robust_full_transfer_path_count,
            "robust_full_transfer_path_fraction": self.robust_full_transfer_path_fraction,
            "certified_path_status": self.certified_path_status,
            "all_edges_robust_generalizing": self.all_edges_robust_generalizing,
            "alternative": self.alternative,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "calibrated_family_size_edge_count": self.calibrated_family_size_edge_count,
            "qualification_inherited_from_four_contrast_panel": self.qualification_inherited_from_four_contrast_panel,
            "qualification_inherited_from_twelve_contrast_panel": self.qualification_inherited_from_twelve_contrast_panel,
            "total_gain_can_override_failed_edge": self.total_gain_can_override_failed_edge,
            "best_path_can_override_failed_edge": self.best_path_can_override_failed_edge,
            "shapley_can_override_edge_failure": self.shapley_can_override_edge_failure,
            "upstream_refit_uncertainty_included": self.upstream_refit_uncertainty_included,
            "untouched_external_validation_included": self.untouched_external_validation_included,
        }


def _edge_name(lower: tuple[str, ...], upper: tuple[str, ...]) -> str:
    left = "+".join(lower) if lower else "base"
    right = "+".join(upper)
    return f"{left}->{right}"


def _block_category(categories: Sequence[str]) -> str:
    values = tuple(categories)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_generalizing" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def certify_positive_information_lattice_v2(
    nodes: Sequence[InformationLatticeNodeScore],
    information_blocks: Sequence[InformationBlock],
    groups: Sequence[object],
    *,
    base_information: Sequence[str] = (),
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260915,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> PositiveInformationLatticeCertification:
    """Certify every edge of a qualified 2- or 3-block independent lattice."""

    block_rows = _validate_blocks(information_blocks)
    if len(block_rows) not in {2, 3}:
        raise ValueError(
            "independent directional lattice is qualified for exactly 2 or 3 information blocks "
            "(4 or 12 directed edges); 4-block / 32-edge and larger families remain unqualified"
        )
    block_order = tuple(row.name for row in block_rows)
    score_by_subset, _ = _validate_nodes(nodes, block_order)
    edge_defs = _edges(block_order)
    expected_edge_count = 4 if len(block_order) == 2 else 12
    if len(edge_defs) != expected_edge_count:
        raise AssertionError(
            f"a complete {len(block_order)}-block lattice must contain exactly "
            f"{expected_edge_count} directed edges"
        )

    point = audit_information_lattice(
        nodes,
        block_rows,
        groups,
        base_information=base_information,
        sample_weight=sample_weight,
        gain_tolerance=gain_tolerance,
    )
    row_gain = np.column_stack(
        [score_by_subset[upper] - score_by_subset[lower] for lower, upper, _ in edge_defs]
    )
    names = tuple(_edge_name(lower, upper) for lower, upper, _ in edge_defs)
    audit = certify_independent_group_positive_transfer_v2(
        row_gain,
        groups,
        blocks=blocks,
        contrast_names=names,
        sample_weight=sample_weight,
        familywise_lower_confidence_level=familywise_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )
    category_by_name = {row.contrast: row.category for row in audit.contrasts}
    edges = tuple(
        PositiveInformationLatticeEdgeSummary(
            lower_blocks=lower,
            upper_blocks=upper,
            added_block=added,
            category=category_by_name[_edge_name(lower, upper)],
        )
        for lower, upper, added in edge_defs
    )
    block_summaries = tuple(
        PositiveInformationLatticeBlockSummary(
            block=block_name,
            edge_count=sum(1 for _, _, added in edge_defs if added == block_name),
            directional_order_robust_category=_block_category(
                [
                    category_by_name[_edge_name(lower, upper)]
                    for lower, upper, added in edge_defs
                    if added == block_name
                ]
            ),
        )
        for block_name in block_order
    )
    successful = {
        (lower, added)
        for lower, upper, added in edge_defs
        if category_by_name[_edge_name(lower, upper)] == "robust_generalizing"
    }
    total_paths = math.factorial(len(block_order))
    robust_paths = _path_count(block_order, successful)
    return PositiveInformationLatticeCertification(
        point_audit=point,
        one_sided_bootstrap_t_audit=audit,
        edges=edges,
        block_summaries=block_summaries,
        edge_count=len(edge_defs),
        total_admissible_path_count=total_paths,
        robust_full_transfer_path_count=robust_paths,
        robust_full_transfer_path_fraction=float(robust_paths / total_paths),
        certified_path_status=_path_status(robust_paths, total_paths),
        all_edges_robust_generalizing=bool(robust_paths == total_paths),
        alternative="greater",
        validation_group_independence_assumed=True,
        calibrated_family_size_edge_count=len(edge_defs),
        qualification_inherited_from_four_contrast_panel=bool(len(edge_defs) == 4),
        qualification_inherited_from_twelve_contrast_panel=bool(len(edge_defs) == 12),
        total_gain_can_override_failed_edge=False,
        best_path_can_override_failed_edge=False,
        shapley_can_override_edge_failure=False,
        upstream_refit_uncertainty_included=False,
        untouched_external_validation_included=False,
    )
