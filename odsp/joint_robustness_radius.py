"""Certified gamma radius for joint transfer robustness.

The audit asks how far the baseline joint transfer-sign conclusion survives when
both caller-declared block uncertainty and the bounded row-reweighting envelope are
expanded.  It repeatedly invokes the existing joint bias x uncertainty audit with
the same blocks, seed and bootstrap design.  The result is a sensitivity radius,
not a probability of correctness.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

from .joint_bias_uncertainty_robustness import (
    JointBiasUncertaintyAudit,
    audit_joint_bias_uncertainty_robustness,
)


@dataclass(frozen=True)
class JointRobustnessRadiusAudit:
    row_count: int
    group_count: int
    confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    search_upper_gamma: float
    binary_iterations: int
    point_transfer_category: str
    baseline_joint_category: str
    target_joint_category: str | None
    radius_status: str
    certified_gamma: float | None
    break_gamma: float | None
    boundary_interval_width: float | None
    radius_is_lower_bound_only: bool
    certified_maximum_multiplier_ratio: float | None
    baseline_minimum_worst_case_lower_bound: float | None
    baseline_maximum_best_case_upper_bound: float | None
    search_upper_joint_category: str | None
    limiting_group_ids: tuple[str, ...]
    automatic_bias_correction_performed: bool
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        payload=asdict(self)
        payload["limiting_group_ids"]=list(self.limiting_group_ids)
        return payload


def _audit(
    row_gain: Sequence[float],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    base_weight: Sequence[float] | None,
    gamma: float,
    confidence_level: float,
    bootstrap_draws: int,
    seed: int,
    minimum_blocks_per_group: int,
    gain_tolerance: float,
) -> JointBiasUncertaintyAudit:
    return audit_joint_bias_uncertainty_robustness(
        row_gain,
        groups,
        blocks,
        base_weight=base_weight,
        gamma=gamma,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )


def audit_joint_robustness_radius(
    row_gain: Sequence[float],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    base_weight: Sequence[float] | None=None,
    confidence_level: float=0.95,
    bootstrap_draws: int=1000,
    seed: int=20260906,
    minimum_blocks_per_group: int=8,
    gain_tolerance: float=0.0,
    search_upper_gamma: float=10.0,
    binary_iterations: int=50,
) -> JointRobustnessRadiusAudit:
    """Return the certified gamma range for the baseline joint transfer category."""

    upper=float(search_upper_gamma)
    if not math.isfinite(upper) or upper<=1.0:
        raise ValueError("search_upper_gamma must be finite and > 1")
    if not isinstance(binary_iterations,int) or binary_iterations<20:
        raise ValueError("binary_iterations must be an integer >= 20")

    baseline=_audit(
        row_gain,groups,blocks,base_weight=base_weight,gamma=1.0,
        confidence_level=confidence_level,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,gain_tolerance=gain_tolerance,
    )
    common=dict(
        row_count=baseline.row_count,
        group_count=baseline.group_count,
        confidence_level=float(confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        seed=int(seed),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        search_upper_gamma=upper,
        binary_iterations=int(binary_iterations),
        point_transfer_category=baseline.point_transfer_category,
        baseline_joint_category=baseline.joint_robust_category,
        baseline_minimum_worst_case_lower_bound=baseline.minimum_worst_case_lower_bound,
        baseline_maximum_best_case_upper_bound=baseline.maximum_best_case_upper_bound,
        automatic_bias_correction_performed=False,
        aggregate_confidence_score_emitted=False,
    )

    if baseline.joint_robust_category=="unavailable":
        return JointRobustnessRadiusAudit(
            **common,
            target_joint_category=None,
            radius_status="unavailable",
            certified_gamma=None,
            break_gamma=None,
            boundary_interval_width=None,
            radius_is_lower_bound_only=False,
            certified_maximum_multiplier_ratio=None,
            search_upper_joint_category=None,
            limiting_group_ids=tuple(row.group_id for row in baseline.groups if not row.estimable),
        )

    eligible={"joint_robust_generalizing","joint_robust_non_generalizing"}
    if baseline.joint_robust_category not in eligible:
        return JointRobustnessRadiusAudit(
            **common,
            target_joint_category=None,
            radius_status="not_certified_at_baseline",
            certified_gamma=None,
            break_gamma=None,
            boundary_interval_width=None,
            radius_is_lower_bound_only=False,
            certified_maximum_multiplier_ratio=None,
            search_upper_joint_category=None,
            limiting_group_ids=tuple(
                row.group_id for row in baseline.groups
                if row.status not in {"joint_robust_positive","joint_robust_nonpositive"}
            ),
        )

    target=baseline.joint_robust_category
    upper_audit=_audit(
        row_gain,groups,blocks,base_weight=base_weight,gamma=upper,
        confidence_level=confidence_level,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,gain_tolerance=gain_tolerance,
    )
    if upper_audit.joint_robust_category==target:
        return JointRobustnessRadiusAudit(
            **common,
            target_joint_category=target,
            radius_status="robust_through_search_upper",
            certified_gamma=upper,
            break_gamma=None,
            boundary_interval_width=None,
            radius_is_lower_bound_only=True,
            certified_maximum_multiplier_ratio=float(upper*upper),
            search_upper_joint_category=upper_audit.joint_robust_category,
            limiting_group_ids=(),
        )

    lo=1.0
    hi=upper
    hi_audit=upper_audit
    for _ in range(binary_iterations):
        mid=(lo+hi)/2.0
        mid_audit=_audit(
            row_gain,groups,blocks,base_weight=base_weight,gamma=mid,
            confidence_level=confidence_level,bootstrap_draws=bootstrap_draws,seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,gain_tolerance=gain_tolerance,
        )
        if mid_audit.joint_robust_category==target:
            lo=mid
        else:
            hi=mid
            hi_audit=mid_audit

    wanted=(
        "joint_robust_positive"
        if target=="joint_robust_generalizing"
        else "joint_robust_nonpositive"
    )
    limiting=tuple(row.group_id for row in hi_audit.groups if row.status!=wanted)
    return JointRobustnessRadiusAudit(
        **common,
        target_joint_category=target,
        radius_status="finite_radius",
        certified_gamma=float(lo),
        break_gamma=float(hi),
        boundary_interval_width=float(hi-lo),
        radius_is_lower_bound_only=False,
        certified_maximum_multiplier_ratio=float(lo*lo),
        search_upper_joint_category=upper_audit.joint_robust_category,
        limiting_group_ids=limiting,
    )
