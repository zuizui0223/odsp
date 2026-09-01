import numpy as np
import pytest

from odsp.concealed_recovery import (
    DEFAULT_RANDOM_SEED,
    DEFAULT_SAMPLE_SIZE,
    estimate_thickness_from_counts,
    run_concealed_recovery_benchmark,
    sample_state_counts,
)
from odsp.synthetic_benchmark import independent_vertical_temporal


def test_concealed_recovery_benchmark_passes_frozen_tolerances():
    result = run_concealed_recovery_benchmark()
    assert result.sample_size == DEFAULT_SAMPLE_SIZE
    assert result.random_seed == DEFAULT_RANDOM_SEED
    assert result.checks
    assert result.passed is True
    assert all(check.passed for check in result.checks)


def test_concealed_estimator_receives_counts_not_truth_object():
    truth = independent_vertical_temporal(vertical_states=2, temporal_states=3)
    counts = sample_state_counts(
        truth,
        n_observations=20_000,
        random_state=123,
    )
    assert counts.shape == truth.shape
    assert counts.sum() == pytest.approx(20_000)
    assert np.issubdtype(counts.dtype, np.floating)

    estimate = estimate_thickness_from_counts(
        counts,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    assert estimate.effective_vertical_states == pytest.approx(2.0, abs=0.08)
    assert estimate.effective_temporal_states == pytest.approx(3.0, abs=0.08)
    assert estimate.effective_joint_vertical_temporal_states == pytest.approx(
        6.0, abs=0.08
    )


def test_sampling_is_deterministic_for_frozen_seed():
    truth = np.ones((2, 2, 2, 2), dtype=float)
    a = sample_state_counts(truth, n_observations=1000, random_state=42)
    b = sample_state_counts(truth, n_observations=1000, random_state=42)
    assert np.array_equal(a, b)


def test_sampling_fails_closed_on_invalid_truth_or_sample_size():
    with pytest.raises(ValueError, match="non-negative"):
        sample_state_counts(
            np.array([[1.0, -1.0]]), n_observations=10, random_state=1
        )
    with pytest.raises(ValueError, match="positive mass"):
        sample_state_counts(
            np.zeros((2, 2), dtype=float), n_observations=10, random_state=1
        )
    with pytest.raises(ValueError, match="n_observations"):
        sample_state_counts(
            np.ones((2, 2), dtype=float), n_observations=0, random_state=1
        )
