"""Sensitivity of transfer uncertainty to caller-declared block definitions.

The same held-out row gains, group labels and sample weights are evaluated under
multiple plausible block definitions.  Each definition is passed unchanged to the
existing block-aware transfer-uncertainty audit.  ODSP reports whether the robust
transfer conclusion is stable across those definitions; it does not infer which
block definition is biologically correct.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .block_aware_transfer_uncertainty import (
    BlockAwareTransferAudit,
    audit_block_aware_transfer_uncertainty,
)


@dataclass(frozen=True)
class BlockDefinitionTransferResult:
    name: str
    robust_transfer_category: str
    robust_admissible: bool
    point_transfer_category: str
    minimum_group_lower_bound: float | None
    maximum_group_upper_bound: float | None
    minimum_group_block_count: int
    maximum_group_block_count: int
    audit: BlockAwareTransferAudit

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "robust_transfer_category": self.robust_transfer_category,
            "robust_admissible": self.robust_admissible,
            "point_transfer_category": self.point_transfer_category,
            "minimum_group_lower_bound": self.minimum_group_lower_bound,
            "maximum_group_upper_bound": self.maximum_group_upper_bound,
            "minimum_group_block_count": self.minimum_group_block_count,
            "maximum_group_block_count": self.maximum_group_block_count,
            "audit": self.audit.as_dict(),
        }


@dataclass(frozen=True)
class BlockDefinitionSensitivityAudit:
    row_count: int
    group_count: int
    definition_count: int
    definition_names: tuple[str, ...]
    confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    sensitivity_category: str
    robust_category_set: tuple[str, ...]
    point_category_set: tuple[str, ...]
    any_robust_category_change: bool
    group_status_flip_count: int
    minimum_observed_lower_bound: float | None
    maximum_observed_upper_bound: float | None
    minimum_definition_group_block_count: int
    maximum_definition_group_block_count: int
    no_automatic_block_definition_selection: bool
    aggregate_confidence_score_emitted: bool
    definitions: tuple[BlockDefinitionTransferResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "row_count": self.row_count,
            "group_count": self.group_count,
            "definition_count": self.definition_count,
            "definition_names": list(self.definition_names),
            "confidence_level": self.confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "seed": self.seed,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "sensitivity_category": self.sensitivity_category,
            "robust_category_set": list(self.robust_category_set),
            "point_category_set": list(self.point_category_set),
            "any_robust_category_change": self.any_robust_category_change,
            "group_status_flip_count": self.group_status_flip_count,
            "minimum_observed_lower_bound": self.minimum_observed_lower_bound,
            "maximum_observed_upper_bound": self.maximum_observed_upper_bound,
            "minimum_definition_group_block_count": self.minimum_definition_group_block_count,
            "maximum_definition_group_block_count": self.maximum_definition_group_block_count,
            "no_automatic_block_definition_selection": self.no_automatic_block_definition_selection,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "definitions": [row.as_dict() for row in self.definitions],
        }


def _validate_gain(row_gain: Sequence[float]) -> np.ndarray:
    gain = np.asarray(row_gain, dtype=float)
    if gain.ndim != 1 or gain.size == 0 or not np.isfinite(gain).all():
        raise ValueError("row_gain must be a non-empty finite one-dimensional vector")
    return gain


def _validate_named_definitions(
    block_definitions: Mapping[str, Sequence[object]], n: int
) -> tuple[tuple[str, tuple[object, ...]], ...]:
    if len(block_definitions) < 2:
        raise ValueError("block_definitions must contain at least two named definitions")
    rows: list[tuple[str, tuple[object, ...]]] = []
    for name, values in block_definitions.items():
        label = str(name).strip()
        if not label:
            raise ValueError("block-definition names must be non-empty")
        if len(values) != n:
            raise ValueError("every block definition must contain one value per row")
        blocks = tuple(values)
        if any(not str(value).strip() for value in blocks):
            raise ValueError("block-definition labels must be non-empty")
        rows.append((label, blocks))
    if len({name for name, _ in rows}) != len(rows):
        raise ValueError("block-definition names must be unique")
    return tuple(rows)


def _definition_result(name: str, audit: BlockAwareTransferAudit) -> BlockDefinitionTransferResult:
    lower = [row.lower_bound for row in audit.groups if row.lower_bound is not None]
    upper = [row.upper_bound for row in audit.groups if row.upper_bound is not None]
    block_counts = [row.block_count for row in audit.groups]
    return BlockDefinitionTransferResult(
        name=name,
        robust_transfer_category=audit.robust_transfer_category,
        robust_admissible=audit.robust_admissible,
        point_transfer_category=audit.point_transfer_category,
        minimum_group_lower_bound=(
            float(min(lower)) if len(lower) == len(audit.groups) else None
        ),
        maximum_group_upper_bound=(
            float(max(upper)) if len(upper) == len(audit.groups) else None
        ),
        minimum_group_block_count=int(min(block_counts)),
        maximum_group_block_count=int(max(block_counts)),
        audit=audit,
    )


def audit_block_definition_sensitivity(
    row_gain: Sequence[float],
    groups: Sequence[object],
    block_definitions: Mapping[str, Sequence[object]],
    *,
    sample_weight: Sequence[float] | None = None,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 2000,
    seed: int = 20260906,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> BlockDefinitionSensitivityAudit:
    """Audit transfer robustness across multiple plausible block definitions."""

    gain = _validate_gain(row_gain)
    n = int(gain.size)
    if len(groups) != n:
        raise ValueError("groups must contain one value per row")
    if not math.isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")
    definitions = _validate_named_definitions(block_definitions, n)

    results: list[BlockDefinitionTransferResult] = []
    statuses_by_group: dict[str, list[str]] = {}
    for name, blocks in definitions:
        audit = audit_block_aware_transfer_uncertainty(
            gain,
            groups,
            blocks=blocks,
            sample_weight=sample_weight,
            confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )
        result = _definition_result(name, audit)
        results.append(result)
        for row in audit.groups:
            statuses_by_group.setdefault(row.group_id, []).append(row.status)

    robust_categories = tuple(sorted({row.robust_transfer_category for row in results}))
    point_categories = tuple(sorted({row.point_transfer_category for row in results}))
    if robust_categories == ("robust_generalizing",):
        sensitivity_category = "block_definition_robust_generalizing"
    elif robust_categories == ("robust_non_generalizing",):
        sensitivity_category = "block_definition_robust_non_generalizing"
    elif robust_categories == ("unavailable",):
        sensitivity_category = "stable_unavailable"
    elif len(robust_categories) == 1:
        sensitivity_category = f"stable_{robust_categories[0]}"
    else:
        sensitivity_category = "block_definition_sensitive"

    finite_lower = [
        row.minimum_group_lower_bound
        for row in results
        if row.minimum_group_lower_bound is not None
    ]
    finite_upper = [
        row.maximum_group_upper_bound
        for row in results
        if row.maximum_group_upper_bound is not None
    ]
    block_counts = [row.minimum_group_block_count for row in results]
    max_block_counts = [row.maximum_group_block_count for row in results]
    flip_count = sum(len(set(statuses)) > 1 for statuses in statuses_by_group.values())

    return BlockDefinitionSensitivityAudit(
        row_count=n,
        group_count=results[0].audit.group_count,
        definition_count=len(results),
        definition_names=tuple(row.name for row in results),
        confidence_level=float(confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        seed=int(seed),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        sensitivity_category=sensitivity_category,
        robust_category_set=robust_categories,
        point_category_set=point_categories,
        any_robust_category_change=len(robust_categories) > 1,
        group_status_flip_count=int(flip_count),
        minimum_observed_lower_bound=(float(min(finite_lower)) if finite_lower else None),
        maximum_observed_upper_bound=(float(max(finite_upper)) if finite_upper else None),
        minimum_definition_group_block_count=int(min(block_counts)),
        maximum_definition_group_block_count=int(max(max_block_counts)),
        no_automatic_block_definition_selection=True,
        aggregate_confidence_score_emitted=False,
        definitions=tuple(results),
    )
