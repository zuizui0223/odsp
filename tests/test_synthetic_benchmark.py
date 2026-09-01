import pytest

from odsp.synthetic_benchmark import (
    benchmark_passes,
    habitat_capacity_pair,
    run_known_truth_synthetic_benchmark,
)


def test_known_truth_synthetic_benchmark_passes_all_frozen_checks():
    checks = run_known_truth_synthetic_benchmark()
    assert checks
    assert all(check.passed for check in checks)
    assert benchmark_passes() is True


def test_known_truth_benchmark_contains_all_required_families():
    families = {check.family for check in run_known_truth_synthetic_benchmark()}
    assert {
        "planar_sufficiency",
        "pure_vertical",
        "pure_temporal",
        "independent_zt",
        "coupled_zt",
        "vertical_partition_pair",
        "temporal_partition_pair",
        "joint_only_partition",
        "habitat_capacity",
    } <= families


def test_habitat_capacity_fixture_holds_xy_footprint_constant():
    simple, layered = habitat_capacity_pair(layered_vertical_states=5)
    assert simple.shape[:2] == layered.shape[:2]
    assert simple.shape[2] == 1
    assert layered.shape[2] == 5


def test_invalid_habitat_capacity_state_count_fails_closed():
    with pytest.raises(ValueError, match="vertical_states"):
        habitat_capacity_pair(layered_vertical_states=0)
