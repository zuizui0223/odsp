"""Known-truth benchmark for ODSP prediction trust diagnostics."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .generalization_profile import generalization_profile_from_probability_field
from .prediction_novelty import fit_environmental_novelty_model
from .prediction_uncertainty import fit_state_conformal_calibrator


@dataclass(frozen=True)
class PredictionTrustCheck:
    name: str
    passed: bool
    value: float | str | bool
    criterion: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionTrustBenchmarkResult:
    seed: int
    checks: tuple[PredictionTrustCheck, ...]
    conformal_exchangeable_coverage: float
    conformal_target_coverage: float
    conformal_shifted_coverage: float
    conformal_mean_set_size: float
    novelty_in_domain_median_ratio: float
    novelty_shifted_median_ratio: float
    novelty_shifted_strict_fraction: float
    novelty_affine_max_abs_ratio_error: float
    individual_gain_category: str
    species_gain_category: str
    fine_level_failure_preserved: bool

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
            "conformal_exchangeable_coverage": self.conformal_exchangeable_coverage,
            "conformal_target_coverage": self.conformal_target_coverage,
            "conformal_shifted_coverage": self.conformal_shifted_coverage,
            "conformal_mean_set_size": self.conformal_mean_set_size,
            "novelty_in_domain_median_ratio": self.novelty_in_domain_median_ratio,
            "novelty_shifted_median_ratio": self.novelty_shifted_median_ratio,
            "novelty_shifted_strict_fraction": self.novelty_shifted_strict_fraction,
            "novelty_affine_max_abs_ratio_error": self.novelty_affine_max_abs_ratio_error,
            "individual_gain_category": self.individual_gain_category,
            "species_gain_category": self.species_gain_category,
            "fine_level_failure_preserved": self.fine_level_failure_preserved,
        }


def _probabilities(rng: np.random.Generator, n: int) -> np.ndarray:
    raw = rng.gamma(shape=np.array([1.5, 2.5, 4.0]), scale=1.0, size=(n, 3))
    return raw / raw.sum(axis=1, keepdims=True)


def _draw_labels(rng: np.random.Generator, probability: np.ndarray) -> np.ndarray:
    cumulative = np.cumsum(probability, axis=1)
    draws = rng.random(probability.shape[0])
    return np.sum(draws[:, None] > cumulative, axis=1)


def run_prediction_trust_benchmark(seed: int = 20260905) -> PredictionTrustBenchmarkResult:
    rng = np.random.default_rng(seed)

    calibration_probability = _probabilities(rng, 6000)
    calibration_y = _draw_labels(rng, calibration_probability)
    test_probability = _probabilities(rng, 30000)
    test_y = _draw_labels(rng, test_probability)
    conformal = fit_state_conformal_calibrator(
        calibration_probability,
        calibration_y,
        classes=(0, 1, 2),
        miscoverage=0.1,
    )
    exchangeable = conformal.evaluate(test_probability, test_y)
    shifted_y = np.argmin(test_probability, axis=1)
    shifted = conformal.evaluate(test_probability, shifted_y)

    train = rng.normal(size=(1200, 4))
    query = rng.normal(size=(600, 4))
    shifted_query = rng.normal(loc=6.0, scale=0.35, size=(300, 4))
    novelty = fit_environmental_novelty_model(train, reference_quantile=0.95)
    query_summary = novelty.summarize(query)
    shifted_summary = novelty.summarize(shifted_query)
    in_ratios = np.asarray([item.novelty_ratio for item in query_summary])
    shift_ratios = np.asarray([item.novelty_ratio for item in shifted_summary])
    strict_fraction = float(
        np.mean([item.category == "strict_extrapolation" for item in shifted_summary])
    )

    affine_scale = np.array([2.5, 0.3, 8.0, 1.7])
    affine_offset = np.array([10.0, -7.0, 2.0, 3.0])
    novelty_affine = fit_environmental_novelty_model(
        train * affine_scale + affine_offset,
        reference_quantile=0.95,
    )
    affine_summary = novelty_affine.summarize(query * affine_scale + affine_offset)
    affine_error = float(
        np.max(
            np.abs(
                in_ratios
                - np.asarray([item.novelty_ratio for item in affine_summary], dtype=float)
            )
        )
    )
    affine_categories_equal = [item.category for item in query_summary] == [
        item.category for item in affine_summary
    ]

    true_probability = np.array([0.80, 0.82, 0.75, 0.78, 0.90, 0.88, 0.45, 0.46])
    profile_probability = np.column_stack([true_probability, 1.0 - true_probability])
    profile = generalization_profile_from_probability_field(
        profile_probability,
        ["used"] * 8,
        classes=("used", "other"),
        marginal_probability=np.array([0.5, 0.5]),
        groupings={
            "individual": ["i1", "i1", "i2", "i2", "i3", "i3", "i4", "i4"],
            "species": ["spA", "spA", "spA", "spA", "spB", "spB", "spB", "spB"],
        },
    )
    individual, species = profile.levels
    fine_preserved = (
        individual.gain_category == "mixed"
        and species.gain_category == "generalizing"
        and profile.fine_level_failures_may_not_be_overridden
    )

    in_median = float(np.median(in_ratios))
    shifted_median = float(np.median(shift_ratios))
    checks = (
        PredictionTrustCheck(
            "exchangeable_conformal_coverage",
            0.89 <= exchangeable.empirical_coverage <= 0.92,
            float(exchangeable.empirical_coverage),
            "0.89 <= empirical coverage <= 0.92 for nominal 0.90",
        ),
        PredictionTrustCheck(
            "shifted_conformal_failure_visible",
            shifted.empirical_coverage < exchangeable.empirical_coverage - 0.20,
            float(shifted.empirical_coverage),
            "shifted coverage at least 0.20 below exchangeable coverage",
        ),
        PredictionTrustCheck(
            "shifted_environment_strict_extrapolation",
            strict_fraction >= 0.95,
            strict_fraction,
            "at least 95% of strongly shifted rows are strict extrapolation",
        ),
        PredictionTrustCheck(
            "shifted_environment_more_novel",
            shifted_median > max(2.0, 2.0 * in_median),
            shifted_median,
            "shifted median novelty ratio exceeds max(2, 2x in-domain median)",
        ),
        PredictionTrustCheck(
            "novelty_affine_invariance",
            affine_error <= 1e-10 and affine_categories_equal,
            affine_error,
            "max ratio error <= 1e-10 and categories unchanged",
        ),
        PredictionTrustCheck(
            "fine_level_failure_not_overridden",
            fine_preserved,
            fine_preserved,
            "individual=mixed, species=generalizing, no override flag remains true",
        ),
    )

    return PredictionTrustBenchmarkResult(
        seed=int(seed),
        checks=checks,
        conformal_exchangeable_coverage=float(exchangeable.empirical_coverage),
        conformal_target_coverage=float(exchangeable.target_coverage),
        conformal_shifted_coverage=float(shifted.empirical_coverage),
        conformal_mean_set_size=float(exchangeable.mean_set_size),
        novelty_in_domain_median_ratio=in_median,
        novelty_shifted_median_ratio=shifted_median,
        novelty_shifted_strict_fraction=strict_fraction,
        novelty_affine_max_abs_ratio_error=affine_error,
        individual_gain_category=individual.gain_category,
        species_gain_category=species.gain_category,
        fine_level_failure_preserved=fine_preserved,
    )
