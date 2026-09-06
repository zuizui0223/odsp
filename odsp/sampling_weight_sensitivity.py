"""Sensitivity of held-out transfer conclusions to caller-supplied weighting schemes.

ODSP does not infer a correct observation or detection model here.  Instead, the
caller supplies multiple plausible non-negative weighting scenarios on the same
validation rows.  Each scenario is audited with the existing block-aware transfer
uncertainty procedure and the scenario-specific conclusions are retained.
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
class WeightScenarioTransferResult:
    name: str
    mean_gain: float
    point_transfer_category: str
    robust_transfer_category: str
    robust_admissible: bool
    minimum_group_lower_bound: float | None
    maximum_group_upper_bound: float | None
    overall_effective_sample_size: float
    minimum_group_effective_sample_size: float
    audit: BlockAwareTransferAudit

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "mean_gain": self.mean_gain,
            "point_transfer_category": self.point_transfer_category,
            "robust_transfer_category": self.robust_transfer_category,
            "robust_admissible": self.robust_admissible,
            "minimum_group_lower_bound": self.minimum_group_lower_bound,
            "maximum_group_upper_bound": self.maximum_group_upper_bound,
            "overall_effective_sample_size": self.overall_effective_sample_size,
            "minimum_group_effective_sample_size": self.minimum_group_effective_sample_size,
            "audit": self.audit.as_dict(),
        }


@dataclass(frozen=True)
class SamplingWeightSensitivityAudit:
    scenario_count: int
    scenario_names: tuple[str, ...]
    sensitivity_category: str
    robust_category_set: tuple[str, ...]
    point_category_set: tuple[str, ...]
    any_robust_category_change: bool
    any_point_category_change: bool
    minimum_scenario_mean_gain: float
    maximum_scenario_mean_gain: float
    group_status_flip_count: int
    automatic_bias_correction_performed: bool
    aggregate_confidence_score_emitted: bool
    scenarios: tuple[WeightScenarioTransferResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_count": self.scenario_count,
            "scenario_names": list(self.scenario_names),
            "sensitivity_category": self.sensitivity_category,
            "robust_category_set": list(self.robust_category_set),
            "point_category_set": list(self.point_category_set),
            "any_robust_category_change": self.any_robust_category_change,
            "any_point_category_change": self.any_point_category_change,
            "minimum_scenario_mean_gain": self.minimum_scenario_mean_gain,
            "maximum_scenario_mean_gain": self.maximum_scenario_mean_gain,
            "group_status_flip_count": self.group_status_flip_count,
            "automatic_bias_correction_performed": self.automatic_bias_correction_performed,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "scenarios": [row.as_dict() for row in self.scenarios],
        }


def _validate_weight_scenarios(
    scenarios: Mapping[str, Sequence[float]], n: int
) -> tuple[tuple[str, np.ndarray], ...]:
    if len(scenarios) < 2:
        raise ValueError("weight_scenarios must contain at least two named scenarios")
    rows: list[tuple[str, np.ndarray]] = []
    for name, values in scenarios.items():
        label = str(name).strip()
        if not label:
            raise ValueError("weight scenario names must be non-empty")
        weight = np.asarray(values, dtype=float)
        if weight.shape != (n,):
            raise ValueError("every weight scenario must contain one value per row")
        if not np.isfinite(weight).all() or np.any(weight < 0) or not np.any(weight > 0):
            raise ValueError("weight scenarios must be finite, non-negative and positive in total")
        rows.append((label, weight))
    if len({name for name, _ in rows}) != len(rows):
        raise ValueError("weight scenario names must be unique")
    return tuple(rows)


def _kish_ess(weight: np.ndarray) -> float:
    numerator = float(np.sum(weight)) ** 2
    denominator = float(np.sum(weight ** 2))
    return float(numerator / denominator) if denominator > 0 else 0.0


def _minimum_group_ess(weight: np.ndarray, groups: tuple[str, ...]) -> float:
    arr = np.asarray(groups, dtype=object)
    values = []
    for group in tuple(dict.fromkeys(groups)):
        values.append(_kish_ess(weight[arr == group]))
    return float(min(values))


def audit_sampling_weight_sensitivity(
    row_gain: Sequence[float],
    groups: Sequence[object],
    weight_scenarios: Mapping[str, Sequence[float]],
    *,
    blocks: Sequence[object] | None = None,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 2000,
    seed: int = 20260906,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> SamplingWeightSensitivityAudit:
    gain = np.asarray(row_gain, dtype=float)
    if gain.ndim != 1 or gain.size == 0 or not np.isfinite(gain).all():
        raise ValueError("row_gain must be a non-empty finite one-dimensional vector")
    n = int(gain.size)
    if len(groups) != n:
        raise ValueError("groups must contain one value per row")
    group_labels = tuple(str(value).strip() for value in groups)
    if any(not value for value in group_labels):
        raise ValueError("group labels must be non-empty")
    if blocks is not None and len(blocks) != n:
        raise ValueError("blocks must contain one value per row")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    scenario_rows = _validate_weight_scenarios(weight_scenarios, n)
    results: list[WeightScenarioTransferResult] = []
    group_statuses: dict[str, list[str]] = {}

    for name, weight in scenario_rows:
        audit = audit_block_aware_transfer_uncertainty(
            gain,
            group_labels,
            blocks=blocks,
            sample_weight=weight,
            confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )
        lower = [row.lower_bound for row in audit.groups if row.lower_bound is not None]
        upper = [row.upper_bound for row in audit.groups if row.upper_bound is not None]
        for row in audit.groups:
            group_statuses.setdefault(row.group_id, []).append(row.status)
        results.append(
            WeightScenarioTransferResult(
                name=name,
                mean_gain=float(audit.mean_gain),
                point_transfer_category=audit.point_transfer_category,
                robust_transfer_category=audit.robust_transfer_category,
                robust_admissible=audit.robust_admissible,
                minimum_group_lower_bound=(float(min(lower)) if len(lower) == len(audit.groups) else None),
                maximum_group_upper_bound=(float(max(upper)) if len(upper) == len(audit.groups) else None),
                overall_effective_sample_size=_kish_ess(weight),
                minimum_group_effective_sample_size=_minimum_group_ess(weight, group_labels),
                audit=audit,
            )
        )

    robust_categories = tuple(sorted({row.robust_transfer_category for row in results}))
    point_categories = tuple(sorted({row.point_transfer_category for row in results}))
    if robust_categories == ("robust_generalizing",):
        sensitivity_category = "weight_robust_generalizing"
    elif robust_categories == ("robust_non_generalizing",):
        sensitivity_category = "weight_robust_non_generalizing"
    elif robust_categories == ("unavailable",):
        sensitivity_category = "stable_unavailable"
    elif len(robust_categories) == 1:
        sensitivity_category = f"stable_{robust_categories[0]}"
    else:
        sensitivity_category = "weight_sensitive"

    flip_count = sum(len(set(statuses)) > 1 for statuses in group_statuses.values())
    means = [row.mean_gain for row in results]
    return SamplingWeightSensitivityAudit(
        scenario_count=len(results),
        scenario_names=tuple(row.name for row in results),
        sensitivity_category=sensitivity_category,
        robust_category_set=robust_categories,
        point_category_set=point_categories,
        any_robust_category_change=len(robust_categories) > 1,
        any_point_category_change=len(point_categories) > 1,
        minimum_scenario_mean_gain=float(min(means)),
        maximum_scenario_mean_gain=float(max(means)),
        group_status_flip_count=int(flip_count),
        automatic_bias_correction_performed=False,
        aggregate_confidence_score_emitted=False,
        scenarios=tuple(results),
    )
