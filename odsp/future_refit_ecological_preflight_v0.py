"""Outcome-blind structural preflight for a future ecological shared-validation run.

A structurally admissible roster NEVER implies independent and identically
distributed validation blocks, genuinely iid training-process refits,
prospective non-access, or a qualified statistical result. The preflight
checks only materializable identities and support denominators.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence
import math

import numpy as np


@dataclass(frozen=True)
class EcologicalValidationRosterPreflight:
    schema_version: int
    structural_status: str
    identity_namespace: str
    physical_unit_kind: str
    training_validation_physical_unit_overlap_checked: bool
    within_group_physical_unit_fragmentation_checked: bool
    physical_unit_sampling_independence_verified: bool
    refit_count: int
    group_count: int
    contrast_count: int
    validation_row_count: int
    validation_positive_weight_row_count: int
    validation_block_count_by_group: tuple[tuple[str, int], ...]
    minimum_blocks_per_group: int
    training_source_frame_disjoint_checked: bool
    identity_namespace_provenance_verified: bool
    row_ids_unique_checked: bool
    group_block_counts_checked: bool
    validation_sampling_iid_verified: bool
    score_bounds_process_wide_verified: bool
    model_to_score_provenance_verified: bool
    training_process_iid_verified: bool
    model_selection_is_validation_blind_verified: bool
    pre_outcome_freeze_verified: bool
    route_primary_qualified: bool
    historical_ecological_results_reclassified: bool

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["validation_block_count_by_group"] = [
            {"group": g, "block_count": b}
            for g, b in self.validation_block_count_by_group
        ]
        return result


def _unique(values: Sequence[object], name: str, *, required_count: int = 1) -> tuple[str, ...]:
    if isinstance(values, str):
        raise ValueError(f"{name} must be a sequence, not a string")
    if any(v is None or isinstance(v, (bool, np.bool_)) for v in values):
        raise ValueError(f"{name} must contain nonmissing identity values")
    vals = tuple(str(v).strip() for v in values)
    if len(vals) < required_count or any(not v for v in vals) or len(set(vals)) != len(vals):
        raise ValueError(f"{name} must contain unique nonempty IDs")
    return vals


def preflight_shared_validation_ecological_roster(
    validation_row_ids: Sequence[object],
    validation_groups: Sequence[object],
    validation_blocks: Sequence[object],
    training_source_row_ids: Sequence[object],
    *,
    refit_ids: Sequence[object],
    identity_namespace: str,
    training_source_unit_ids: Sequence[object],
    validation_unit_ids: Sequence[object],
    physical_unit_kind: str,
    sample_weight: Sequence[float] | None = None,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    ordered_level_names: Sequence[str] = ("marginal","identity","identity-context"),
) -> EcologicalValidationRosterPreflight:
    """Fail closed on structural overlap; leave all substantive proof flags false.

    The entire original source frame AND its physical sampling units are
    compared, not a subset in one bootstrap refit. A physical unit repeated
    across multiple validation blocks within a group is forbidden.
    Shared block names across validation GROUPS are allowed (IUT can be
    dependent across groups); only within-group distinct block counts matter.
    """
    if not isinstance(identity_namespace, str) or not identity_namespace.strip():
        raise ValueError("identity_namespace must be nonempty")
    if not isinstance(physical_unit_kind, str) or not physical_unit_kind.strip():
        raise ValueError("physical_unit_kind must be nonempty")
    if type(minimum_refits) is not int or minimum_refits < 8:
        raise ValueError("minimum_refits must be integer >=8")
    if type(minimum_blocks_per_group) is not int or minimum_blocks_per_group < 8:
        raise ValueError("minimum_blocks_per_group must be integer >=8")
    if len(ordered_level_names) != 3:
        raise ValueError("exactly three ordered prediction levels are required")
    names = _unique(ordered_level_names, "ordered_level_names", required_count=3)
    refits = _unique(refit_ids, "refit_ids", required_count=minimum_refits)
    src = _unique(training_source_row_ids, "training_source_row_ids")
    val = _unique(validation_row_ids, "validation_row_ids")
    if set(src) & set(val):
        raise ValueError("entire frozen training source frame overlaps validation rows")
    # Distinct event/row IDs do not prove separation of sampling units.
    # Physical unit IDs must be supplied for BOTH entire source and V.
    if len(training_source_unit_ids) != len(src) or len(validation_unit_ids) != len(val):
        raise ValueError("physical unit metadata must align with entire source and validation row frames")
    if any(v is None for v in training_source_unit_ids) or any(v is None for v in validation_unit_ids):
        raise ValueError("physical unit IDs must not be missing")
    src_units = tuple(str(v).strip() for v in training_source_unit_ids)
    val_units = tuple(str(v).strip() for v in validation_unit_ids)
    if not all(src_units) or not all(val_units):
        raise ValueError("physical unit IDs must be nonempty")
    if set(src_units) & set(val_units):
        raise ValueError("training and validation share a physical sampling unit despite distinct row IDs")

    n = len(val)
    if len(validation_groups) != n or len(validation_blocks) != n:
        raise ValueError("group/block metadata must align with validation row IDs")
    gs = tuple(str(x).strip() for x in validation_groups)
    bs = tuple(str(x).strip() for x in validation_blocks)
    if not all(gs) or not all(bs):
        raise ValueError("group and block IDs must be nonempty")
    if sample_weight is None:
        weights = np.ones(n,dtype=float)
    else:
        weights = np.asarray(sample_weight,dtype=float)
        if weights.shape != (n,) or not np.isfinite(weights).all() or np.any(weights < 0):
            raise ValueError("sample_weight must be finite nonnegative per validation row")
    if weights.sum() <= 0:
        raise ValueError("validation roster has no positive-weight support")
    groups = tuple(sorted(set(gs)))
    if len(groups) < 2:
        raise ValueError("at least two validation groups required")
    block_counts = []
    for g in groups:
        # A site, tagged individual, or other declared physical unit must
        # NOT be split into pseudo-independent validation blocks within g.
        unit_to_block: dict[str, str] = {}
        for i in range(n):
            if gs[i] == g and weights[i] > 0:
                previous = unit_to_block.setdefault(val_units[i], bs[i])
                if previous != bs[i]:
                    raise ValueError(
                        "one physical unit was split across distinct validation blocks"
                    )
        blocks = {
            bs[i]
            for i in range(n)
            if gs[i] == g and weights[i] > 0
        }
        if len(blocks) < minimum_blocks_per_group:
            raise ValueError(f"group {g!r} has too few positive-weight independent-block IDs")
        block_counts.append((g,len(blocks)))
    return EcologicalValidationRosterPreflight(
        schema_version=0,
        structural_status="STRUCTURALLY_ADMISSIBLE_UNVERIFIED_SAMPLING",
        identity_namespace=identity_namespace.strip(),
        physical_unit_kind=physical_unit_kind.strip(),
        training_validation_physical_unit_overlap_checked=True,
        within_group_physical_unit_fragmentation_checked=True,
        physical_unit_sampling_independence_verified=False,
        refit_count=len(refits),
        group_count=len(groups),
        contrast_count=2,
        validation_row_count=n,
        validation_positive_weight_row_count=int(np.count_nonzero(weights > 0)),
        validation_block_count_by_group=tuple(block_counts),
        minimum_blocks_per_group=minimum_blocks_per_group,
        training_source_frame_disjoint_checked=True,
        identity_namespace_provenance_verified=False,
        row_ids_unique_checked=True,
        group_block_counts_checked=True,
        validation_sampling_iid_verified=False,
        score_bounds_process_wide_verified=False,
        model_to_score_provenance_verified=False,
        training_process_iid_verified=False,
        model_selection_is_validation_blind_verified=False,
        pre_outcome_freeze_verified=False,
        route_primary_qualified=False,
        historical_ecological_results_reclassified=False,
    )
