"""A fixed-threshold exact binomial test for positive animal-gain content.

This opt-in test is separate from a marginal rank prediction bound. Its
frequentist guarantee requires IID group-gain indicators within one
prespecified target population for a fixed upstream predictor/reference.
Integrity checks cannot establish that assumption, or freeze chronology.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from typing import Mapping

from .fixed_group_gain_protocol import (
    FrozenGainCalibration, FrozenGroupForecastPlan, calibrate_fixed_group_gain,
)


IID_ASSUMPTION = "iid_group_gains_within_prespecified_stratum"


def _probability(value: object, name: str) -> Fraction:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a probability strictly between zero and one")
    try:
        result = Fraction(str(value))
    except (ValueError, TypeError, ZeroDivisionError) as error:
        raise ValueError(f"{name} must be a finite rational probability") from error
    if not 0 < result < 1:
        raise ValueError(f"{name} must be strictly between zero and one")
    return result


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _upper_float(value: Fraction) -> float:
    """Display conservatively; the decision never uses this approximation."""
    rounded = float(value)
    return math.nextafter(rounded, math.inf) if Fraction.from_float(rounded) < value else rounded


def _binomial_lower_tail(n: int, x: int, positive_fraction: Fraction) -> Fraction:
    """P(X<=x), X~Binomial(n,1-positive_fraction), using exact recurrence."""
    if x == n:
        return Fraction(1)
    term = positive_fraction ** n
    total = term
    for j in range(x):
        term *= Fraction(n - j, j + 1) * (1 - positive_fraction) / positive_fraction
        total += term
    return total


@dataclass(frozen=True)
class FrozenGroupGainContentPlan:
    forecast_plan_sha256: str
    stratum: str
    minimum_positive_fraction: Fraction
    confidence_level: Fraction
    gain_threshold: float
    sampling_assumption: str
    calibration_group_count: int
    validation_group_count: int
    digest: str

    def canonical(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "forecast_plan_sha256": self.forecast_plan_sha256,
            "stratum": self.stratum,
            "minimum_positive_fraction": str(self.minimum_positive_fraction),
            "confidence_level": str(self.confidence_level),
            "gain_threshold": self.gain_threshold,
            "sampling_assumption": self.sampling_assumption,
            "calibration_group_count": self.calibration_group_count,
            "validation_group_count": self.validation_group_count,
            "method": "fixed_threshold_one_sided_exact_binomial",
            "nonpositive_event": "group_gain_less_than_or_equal_to_threshold",
            "sample_size_policy": "fixed_before_outcomes_no_optional_stopping",
        }

    @property
    def count_allows_support(self) -> bool:
        return self.minimum_positive_fraction ** self.calibration_group_count <= 1 - self.confidence_level

    def as_public_dict(self) -> dict[str, object]:
        return {
            **self.canonical(),
            "content_plan_sha256": self.digest,
            "status": "COUNT_FEASIBLE_ONLY" if self.count_allows_support else "HOLD_INSUFFICIENT_GROUPS_FOR_CONTENT_CLAIM",
            "count_allows_support": self.count_allows_support,
            "best_case_p_value_upper_bound": _upper_float(self.minimum_positive_fraction ** self.calibration_group_count),
            "outcomes_accessed_by_freeze": False,
            "sampling_independence_verified_by_software": False,
            "chronology_verified_by_software": False,
            "simultaneous_strata_claim": False,
        }


@dataclass(frozen=True)
class GroupGainContentAssessment:
    content_plan: FrozenGroupGainContentPlan
    calibration: FrozenGainCalibration
    nonpositive_group_count: int
    exact_p_value: Fraction

    @property
    def calibration_group_count(self) -> int:
        return self.content_plan.calibration_group_count

    @property
    def positive_group_count(self) -> int:
        return self.calibration_group_count - self.nonpositive_group_count

    @property
    def supported(self) -> bool:
        return self.exact_p_value <= 1 - self.content_plan.confidence_level

    def as_public_dict(self) -> dict[str, object]:
        return {
            **self.content_plan.as_public_dict(),
            "status": "SUPPORTED_IF_IID_ASSUMPTION_HOLDS" if self.supported else "NOT_SUPPORTED",
            "calibration_sha256": self.calibration.calibration_sha256,
            "positive_group_count": self.positive_group_count,
            "nonpositive_group_count": self.nonpositive_group_count,
            "p_value_upper_bound": _upper_float(self.exact_p_value),
            "decision_uses_exact_rational_p_value": True,
            "supported_under_declared_iid_sampling": self.supported,
            "null_hypothesis": "population_positive_fraction_at_most_minimum_positive_fraction",
            "confidence_is_repeated_sample_error_control_not_posterior": True,
            "not_conditional_on_realized_calibration_or_feature_roster": True,
            "not_a_rank_prediction_bound": True,
            "validation_outcomes_accessed": False,
            "historical_bop_terminal_changed": False,
        }


def freeze_group_gain_content_plan(
    forecast_plan: FrozenGroupForecastPlan,
    *,
    stratum: str,
    sampling_assumption: str,
    model_artifact: bytes,
    reference_artifact: bytes,
    minimum_positive_fraction: object = "0.9",
    confidence_level: object = "0.95",
    gain_threshold: object = 0.0,
) -> FrozenGroupGainContentPlan:
    """Fix a single-stratum content test BEFORE calibration outcomes.

    The sampling statement must be justified externally; an unchanged model,
    distinct identifiers and frozen forecasts do not verify IID sampling.
    Selecting the stratum, threshold, sample size or confidence after outcomes,
    or repeating this test until it passes, invalidates the stated error bound.
    The reserved validation group belongs to the surrounding ODSP protocol;
    it is not mathematically required by the binomial test itself.
    """
    if not isinstance(forecast_plan, FrozenGroupForecastPlan):
        raise ValueError("forecast_plan must be a FrozenGroupForecastPlan")
    forecast_plan.assert_unchanged(model_artifact=model_artifact, reference_artifact=reference_artifact)
    if not isinstance(stratum, str) or not stratum or stratum != stratum.strip():
        raise ValueError("stratum must be a nonempty stripped string")
    if sampling_assumption != IID_ASSUMPTION:
        raise ValueError(f"sampling_assumption must explicitly declare {IID_ASSUMPTION}")
    c = _probability(minimum_positive_fraction, "minimum_positive_fraction")
    confidence = _probability(confidence_level, "confidence_level")
    if isinstance(gain_threshold, bool):
        raise ValueError("gain_threshold must be finite and numeric")
    try:
        threshold = float(gain_threshold)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("gain_threshold must be finite and numeric") from error
    if not math.isfinite(threshold):
        raise ValueError("gain_threshold must be finite")
    n = len({r.group_id for r in forecast_plan.calibration_rows if r.stratum == stratum})
    n_validation = len({r.group_id for r in forecast_plan.validation_rows if r.stratum == stratum})
    if not n or not n_validation:
        raise ValueError("selected stratum requires calibration and reserved validation groups")
    policy = FrozenGroupGainContentPlan(
        forecast_plan_sha256=forecast_plan.digest, stratum=stratum,
        minimum_positive_fraction=c, confidence_level=confidence,
        gain_threshold=threshold, sampling_assumption=sampling_assumption,
        calibration_group_count=n, validation_group_count=n_validation, digest="",
    )
    object.__setattr__(policy, "digest", _digest(policy.canonical()))
    return policy


def assess_group_gain_content(
    content_plan: FrozenGroupGainContentPlan,
    forecast_plan: FrozenGroupForecastPlan,
    calibration_outcomes: Mapping[str, str],
    *,
    model_artifact: bytes,
    reference_artifact: bytes,
) -> GroupGainContentAssessment:
    """Score calibration only, then test fixed-threshold population content.

    Scores are recomputed by the existing frozen-forecast calibrator, never
    accepted as caller-supplied scalar gains. The returned calibration can be
    used unchanged by validate_fixed_group_gain on the reserved validation
    outcomes. For managed model-to-forecast provenance, replay the upstream
    managed source/artifact chain before this lower-level operation as usual.
    """
    if not isinstance(content_plan, FrozenGroupGainContentPlan):
        raise ValueError("content_plan must be a FrozenGroupGainContentPlan")
    if _digest(content_plan.canonical()) != content_plan.digest:
        raise ValueError("content policy contents changed after freeze")
    if not isinstance(forecast_plan, FrozenGroupForecastPlan):
        raise ValueError("forecast_plan must be a FrozenGroupForecastPlan")
    if content_plan.forecast_plan_sha256 != forecast_plan.digest:
        raise ValueError("content policy belongs to a different frozen forecast plan")
    rebuilt = freeze_group_gain_content_plan(
        forecast_plan, stratum=content_plan.stratum,
        sampling_assumption=content_plan.sampling_assumption,
        model_artifact=model_artifact, reference_artifact=reference_artifact,
        minimum_positive_fraction=content_plan.minimum_positive_fraction,
        confidence_level=content_plan.confidence_level,
        gain_threshold=content_plan.gain_threshold,
    )
    if rebuilt.digest != content_plan.digest:
        raise ValueError("content policy disagrees with frozen forecast counts or settings")
    if not content_plan.count_allows_support:
        raise ValueError("insufficient calibration groups for the declared content/confidence claim")
    calibration = calibrate_fixed_group_gain(
        forecast_plan, calibration_outcomes,
        model_artifact=model_artifact, reference_artifact=reference_artifact,
    )
    gains = [r.weighted_mean_gain for r in calibration.gains if r.stratum == content_plan.stratum]
    if len(gains) != content_plan.calibration_group_count or any(not math.isfinite(g) for g in gains):
        raise ValueError("calibration requires the declared count of finite group gains")
    failures = sum(g <= content_plan.gain_threshold for g in gains)
    tail = _binomial_lower_tail(len(gains), failures, content_plan.minimum_positive_fraction)
    return GroupGainContentAssessment(content_plan, calibration, failures, tail)
