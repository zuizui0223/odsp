from __future__ import annotations

import pytest

pytest.importorskip("sklearn")

from odsp.prediction_trust_benchmark import run_prediction_trust_benchmark


def test_prediction_trust_benchmark_passes_all_frozen_obligations():
    result = run_prediction_trust_benchmark(seed=20260905)
    assert result.passed is True
    assert len(result.checks) == 6
    assert all(check.passed for check in result.checks)
    assert 0.89 <= result.conformal_exchangeable_coverage <= 0.92
    assert result.conformal_shifted_coverage < result.conformal_exchangeable_coverage
    assert result.novelty_shifted_strict_fraction >= 0.95
    assert result.novelty_shifted_median_ratio > result.novelty_in_domain_median_ratio
    assert result.novelty_affine_max_abs_ratio_error <= 1e-10
    assert result.individual_gain_category == "mixed"
    assert result.species_gain_category == "generalizing"
    assert result.fine_level_failure_preserved is True
