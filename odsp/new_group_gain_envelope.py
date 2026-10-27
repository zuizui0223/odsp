"""One-sided new-individual transfer-gain envelopes with group-level ranks.

The sampling unit is one *independently evaluated group gain*, not GPS fixes,
camera detections, or temporal blocks inside that group. Under exchangeability
of calibration group gains with a new group's gain for a frozen predictor and
comparator, the order-statistic lower bound has finite-sample marginal coverage.

An archived cross-validation score roster is not automatically exchangeable
with a future deployed predictor. Such data remain descriptive, including the
closed BOP_RODENT archive. This module never changes a terminal decision.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


_SOURCE_DESIGNS = frozenset(
    {"fixed_predictor_groups", "historical_crossfit_descriptive"}
)


@dataclass(frozen=True)
class NewGroupGainEnvelope:
    """A rank lower bound on the *mean gain of one new independent group*."""

    calibration_group_ids: tuple[str, ...]
    calibration_group_count: int
    miscoverage: float
    nominal_coverage: float
    finite_sample_rank: int
    conservative_coverage_if_exchangeable: float
    lower_gain_bound: float
    bound_is_vacuous: bool
    gain_threshold: float
    observed_positive_group_count: int
    source_design: str
    inference_status: str

    def as_dict(self) -> dict[str, object]:
        """Export without individual/group identifiers or invalid JSON infinities."""
        return {
            "calibration_group_count": self.calibration_group_count,
            "miscoverage": self.miscoverage,
            "nominal_coverage": self.nominal_coverage,
            "finite_sample_rank": self.finite_sample_rank,
            "conservative_coverage_if_exchangeable": self.conservative_coverage_if_exchangeable,
            "lower_gain_bound": (
                None if self.bound_is_vacuous else self.lower_gain_bound
            ),
            "bound_is_vacuous": self.bound_is_vacuous,
            "gain_threshold": self.gain_threshold,
            "observed_positive_group_count": self.observed_positive_group_count,
            "bound_above_threshold": bool(
                not self.bound_is_vacuous
                and self.lower_gain_bound > self.gain_threshold
            ),
            "source_design": self.source_design,
            "inference_status": self.inference_status,
            "exchangeability_verified_by_software": False,
            "target": "one_future_independent_group_mean_heldout_score_gain",
            "not_a_mean_gain_confidence_interval": True,
            "not_simultaneous_all_groups_certification": True,
        }

    def covers_new_group(self, group_id: str, group_gain: float) -> bool:
        """Compare one separately evaluated group; never recycle calibration IDs."""
        if not isinstance(group_id, str) or not group_id.strip():
            raise ValueError("new group_id must be a non-empty string")
        if group_id.strip() in self.calibration_group_ids:
            raise ValueError("new group_id overlaps the calibration group roster")
        if isinstance(group_gain, bool):
            raise ValueError("new group_gain must be a finite numeric score")
        try:
            gain = float(group_gain)
        except (TypeError, ValueError) as exc:
            raise ValueError("new group_gain must be a finite numeric score") from exc
        if not math.isfinite(gain):
            raise ValueError("new group_gain must be finite")
        return bool(gain >= self.lower_gain_bound)


def fit_new_group_gain_lower_envelope(
    group_gains: Sequence[float],
    group_ids: Sequence[str],
    *,
    miscoverage: float = 0.10,
    gain_threshold: float = 0.0,
    source_design: str = "historical_crossfit_descriptive",
) -> NewGroupGainEnvelope:
    """Fit a one-sided, group-rank lower prediction bound.

    With n calibration group scores and alpha miscoverage, set
    k = floor((n + 1) * alpha). The lower bound is the k-th *smallest*
    calibration group gain, or -infinity if k=0. If calibration and future
    group gains are exchangeable, coverage is at least (n+1-k)/(n+1).

    Requires *one scalar already-held-out gain per independent group*, all
    scored with the same prespecified score orientation and comparator.
    No event-weighted or per-fix fitting is accepted. The software can reject
    repeated group IDs but cannot independently certify biological sampling,
    score exchangeability, absence of leakage or model-freeze chronology.

    The "historical_crossfit_descriptive" mode is explicitly NOT a coverage
    certificate for future deployment; e.g. frozen BOP cross-fitted gains
    were obtained from different group-specific training folds.
    """
    try:
        alpha = float(miscoverage)
        threshold = float(gain_threshold)
    except (TypeError, ValueError) as exc:
        raise ValueError("miscoverage and gain_threshold must be numeric") from exc
    if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("miscoverage must be strictly between zero and one")
    if not math.isfinite(threshold):
        raise ValueError("gain_threshold must be finite")
    if source_design not in _SOURCE_DESIGNS:
        raise ValueError("source_design must declare a supported evidence role")

    try:
        values = tuple(group_gains)
        raw_ids = tuple(group_ids)
    except TypeError as exc:
        raise ValueError("group_gains and group_ids must be sequences") from exc
    if not values or len(values) != len(raw_ids):
        raise ValueError("supply one independent group ID per group gain")
    ids: list[str] = []
    gains: list[float] = []
    for identity, raw_gain in zip(raw_ids, values):
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError("each group ID must be a non-empty string")
        ids.append(identity.strip())
        if isinstance(raw_gain, bool):
            raise ValueError("group gains must be finite numeric scalars")
        try:
            gain = float(raw_gain)
        except (ValueError, TypeError) as exc:
            raise ValueError("group gains must be finite numeric scalars") from exc
        if not math.isfinite(gain):
            raise ValueError("group gains must be finite")
        gains.append(gain)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate group IDs: group scores cannot be replicated")
    n = len(gains)
    rank = math.floor((n + 1) * alpha)
    lower = float("-inf") if rank == 0 else sorted(gains)[rank - 1]
    coverage = (n + 1 - rank) / (n + 1)
    status = (
        "conditional_rank_guarantee_only_if_group_scores_exchangeable"
        if source_design == "fixed_predictor_groups"
        else "descriptive_only_crossfit_future_exchangeability_not_established"
    )
    return NewGroupGainEnvelope(
        calibration_group_ids=tuple(ids),
        calibration_group_count=n,
        miscoverage=alpha,
        nominal_coverage=1.0 - alpha,
        finite_sample_rank=rank,
        conservative_coverage_if_exchangeable=coverage,
        lower_gain_bound=lower,
        bound_is_vacuous=(rank == 0),
        gain_threshold=threshold,
        observed_positive_group_count=sum(x > threshold for x in gains),
        source_design=source_design,
        inference_status=status,
    )
