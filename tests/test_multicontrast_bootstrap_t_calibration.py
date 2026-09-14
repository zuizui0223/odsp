from __future__ import annotations

import numpy as np
import pytest

from odsp.multicontrast_bootstrap_t_calibration import (
    GENERATOR_VERSION,
    _world,
    run_multicontrast_bootstrap_t_calibration,
)


def test_world_generator_is_seed_deterministic_without_matrix_factorization():
    first = _world(
        np.random.default_rng(12345),
        blocks=12,
        group_count=3,
        contrast_count=4,
        contrast_rho=0.5,
        distribution="normal",
    )
    second = _world(
        np.random.default_rng(12345),
        blocks=12,
        group_count=3,
        contrast_count=4,
        contrast_rho=0.5,
        distribution="normal",
    )
    assert np.array_equal(first, second)
    assert first.shape == (12, 3, 4)


def test_calibration_benchmark_is_reproducible_and_records_family_size():
    first = run_multicontrast_bootstrap_t_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
        group_count=3,
    )
    second = run_multicontrast_bootstrap_t_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
        group_count=3,
    )
    assert first.as_dict() == second.as_dict()
    assert first.generator_version == GENERATOR_VERSION
    assert len(first.scenarios) == 5
    assert {row.contrast_count for row in first.scenarios} == {2, 4}
    assert {row.blocks_per_group for row in first.scenarios} == {8, 20, 50}
    assert all(0.0 <= row.v2_two_sided_familywise_noncoverage_rate <= 1.0 for row in first.scenarios)


def test_calibration_rejects_invalid_design_arguments():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_multicontrast_bootstrap_t_calibration(simulations_per_scenario=99)
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_multicontrast_bootstrap_t_calibration(bootstrap_draws=499)
    with pytest.raises(ValueError, match="group_count"):
        run_multicontrast_bootstrap_t_calibration(group_count=1)
    with pytest.raises(ValueError, match="contrast_correlation"):
        run_multicontrast_bootstrap_t_calibration(contrast_correlation=1.0)
