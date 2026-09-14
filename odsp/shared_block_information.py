"""Shared-block certification wrappers for ODSP information-transfer methods."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .information_lattice import (
    InformationBlock,
    InformationLatticeNodeScore,
    InformationLatticePointAudit,
    _block_certified_category,
    _edges,
    _path_count,
    _path_status,
    _validate_blocks,
    _validate_nodes,
    audit_information_lattice,
)
from .information_transfer import (
    InformationLevelScore,
    InformationTransferResult,
    decompose_information_transfer,
    validate_information_filtration,
)
from .shared_block_certification import (
    SharedBlockGainCertification,
    certify_shared_block_gains,
)


@dataclass(frozen=True)
class SharedBlockInformationTransferCertification:
    score_name: str
    filtration_validated: bool
    point_result: InformationTransferResult
    shared_block_certification: SharedBlockGainCertification
    point_transfer_ceiling: str
    certified_transfer_ceiling: str
    validation_group_independence_assumed: bool
    exact_shared_block_support_validated: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "score_name": self.score_name,
            "filtration_validated": self.filtration_validated,
            "point_result": self.point_result.as_dict(),
            "shared_block_certification": self.shared_block_certification.as_dict(),
            "point_transfer_ceiling": self.point_transfer_ceiling,
            "certified_transfer_ceiling": self.certified_transfer_ceiling,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "exact_shared_block_support_validated": self.exact_shared_block_support_validated,
        }


@dataclass(frozen=True)
class SharedBlockLatticeEdgeSummary:
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
class SharedBlockLatticeBlockSummary:
    block: str
    edge_count: int
    order_robust_category: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SharedBlockInformationLatticeCertification:
    point_audit: InformationLatticePointAudit
    shared_block_certification: SharedBlockGainCertification
    edges: tuple[SharedBlockLatticeEdgeSummary, ...]
    block_summaries: tuple[SharedBlockLatticeBlockSummary, ...]
    total_admissible_path_count: int
    robust_full_transfer_path_count: int
    robust_full_transfer_path_fraction: float
    certified_path_status: str
    validation_group_independence_assumed: bool
    exact_shared_block_support_validated: bool
    best_path_can_override_failed_edge: bool
    shapley_can_override_edge_failure: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "point_audit": self.point_audit.as_dict(),
            "shared_block_certification": self.shared_block_certification.as_dict(),
            "edges": [row.as_dict() for row in self.edges],
            "block_summaries": [row.as_dict() for row in self.block_summaries],
            "total_admissible_path_count": self.total_admissible_path_count,
            "robust_full_transfer_path_count": self.robust_full_transfer_path_count,
            "robust_full_transfer_path_fraction": self.robust_full_transfer_path_fraction,
            "certified_path_status": self.certified_path_status,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "exact_shared_block_support_validated": self.exact_shared_block_support_validated,
            "best_path_can_override_failed_edge": self.best_path_can_override_failed_edge,
            "shapley_can_override_edge_failure": self.shapley_can_override_edge_failure,
        }


def _ceiling(levels: tuple[str, ...], categories: Sequence[str]) -> str:
    ceiling = levels[0]
    for index, category in enumerate(categories):
        if category != "robust_generalizing":
            break
        ceiling = levels[index + 1]
    return ceiling


def certify_shared_block_information_transfer(
    levels: Sequence[InformationLevelScore],
    groups: Sequence[object],
    shared_blocks: Sequence[object],
    *,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260914,
    minimum_shared_blocks: int = 8,
    gain_tolerance: float = 0.0,
) -> SharedBlockInformationTransferCertification:
    """Certify a nested information filtration with paired blocks across groups."""

    rows = tuple(levels)
    steps = validate_information_filtration(rows)
    point = decompose_information_transfer(
        rows,
        groups,
        score_name=score_name,
        sample_weight=sample_weight,
        gain_tolerance=gain_tolerance,
    )
    scores = tuple(np.asarray(row.score, dtype=float) for row in rows)
    row_gain = np.column_stack(
        [scores[index + 1] - scores[index] for index in range(len(steps))]
    )
    names = tuple(
        f"{step.lower_level}->{step.upper_level}" for step in steps
    )
    shared = certify_shared_block_gains(
        row_gain,
        groups,
        shared_blocks,
        contrast_names=names,
        sample_weight=sample_weight,
        familywise_confidence_level=familywise_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_shared_blocks=minimum_shared_blocks,
        gain_tolerance=gain_tolerance,
    )
    categories = tuple(row.category for row in shared.contrasts)
    levels_names = tuple(row.name for row in rows)
    return SharedBlockInformationTransferCertification(
        score_name=point.score_name,
        filtration_validated=True,
        point_result=point,
        shared_block_certification=shared,
        point_transfer_ceiling=point.predictive_result.all_group_point_transfer_ceiling,
        certified_transfer_ceiling=_ceiling(levels_names, categories),
        validation_group_independence_assumed=False,
        exact_shared_block_support_validated=True,
    )


def _edge_name(lower: tuple[str, ...], added: str) -> str:
    left = "+".join(lower) if lower else "base"
    return f"{left}->{added}"


def certify_shared_block_information_lattice(
    nodes: Sequence[InformationLatticeNodeScore],
    information_blocks: Sequence[InformationBlock],
    groups: Sequence[object],
    shared_blocks: Sequence[object],
    *,
    base_information: Sequence[str] = (),
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260914,
    minimum_shared_blocks: int = 8,
    gain_tolerance: float = 0.0,
) -> SharedBlockInformationLatticeCertification:
    """Certify a complete information lattice with paired blocks across groups."""

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
        [
            score_by_subset[upper] - score_by_subset[lower]
            for lower, upper, _ in edge_defs
        ]
    )
    names = tuple(_edge_name(lower, added) for lower, _, added in edge_defs)
    shared = certify_shared_block_gains(
        row_gain,
        groups,
        shared_blocks,
        contrast_names=names,
        sample_weight=sample_weight,
        familywise_confidence_level=familywise_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_shared_blocks=minimum_shared_blocks,
        gain_tolerance=gain_tolerance,
    )
    category_by_name = {
        row.contrast: row.category for row in shared.contrasts
    }
    edges = tuple(
        SharedBlockLatticeEdgeSummary(
            lower_blocks=lower,
            upper_blocks=upper,
            added_block=added,
            category=category_by_name[_edge_name(lower, added)],
        )
        for lower, upper, added in edge_defs
    )
    block_summaries = tuple(
        SharedBlockLatticeBlockSummary(
            block=block,
            edge_count=sum(1 for _, _, added in edge_defs if added == block),
            order_robust_category=_block_certified_category(
                [
                    category_by_name[_edge_name(lower, added)]
                    for lower, _, added in edge_defs
                    if added == block
                ]
            ),
        )
        for block in block_order
    )
    successful = {
        (lower, added)
        for lower, _, added in edge_defs
        if category_by_name[_edge_name(lower, added)] == "robust_generalizing"
    }
    total_paths = math.factorial(len(block_order))
    robust_paths = _path_count(block_order, successful)
    return SharedBlockInformationLatticeCertification(
        point_audit=point,
        shared_block_certification=shared,
        edges=edges,
        block_summaries=block_summaries,
        total_admissible_path_count=total_paths,
        robust_full_transfer_path_count=robust_paths,
        robust_full_transfer_path_fraction=float(robust_paths / total_paths),
        certified_path_status=_path_status(robust_paths, total_paths),
        validation_group_independence_assumed=False,
        exact_shared_block_support_validated=True,
        best_path_can_override_failed_edge=False,
        shapley_can_override_edge_failure=False,
    )
