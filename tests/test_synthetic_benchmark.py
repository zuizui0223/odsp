import pytest

from odsp.synthetic_benchmark import (
    benchmark_passes,
    habitat_capacity_pair,
    run_known_truth_synthetic_benchmark,
    shifted_organization_transferability_pair,
    stable_organization_transferability_pair,
    thick_unorganized_transferability_pair,
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
        "thick_unorganized_transferability",
        "stable_organization_transferability",
        "shifted_organization_transferability",
    } <= families


def test_habitat_capacity_fixture_holds_xy_footprint_constant():
    simple, layered = habitat_capacity_pair(layered_vertical_states=5)
    assert simple.shape[:2] == layered.shape[:2]
    assert simple.shape[2] == 1
    assert layered.shape[2] == 5


def test_transferability_fixtures_preserve_model_shape_and_separate_cases():
    thick_model, thick_heldout = thick_unorganized_transferability_pair()
    stable_model, stable_heldout = stable_organization_transferability_pair()
    shifted_model, shifted_heldout = shifted_organization_transferability_pair()

    assert thick_model.shape == thick_heldout.shape == (2, 1, 4)
    assert stable_model.shape == stable_heldout.shape == (2, 1, 2)
    assert shifted_model.shape == shifted_heldout.shape == (2, 1, 2)
    assert (stable_model == stable_heldout).all()
    assert not (shifted_model == shifted_heldout).all()


def test_invalid_habitat_capacity_state_count_fails_closed():
    with pytest.raises(ValueError, match="vertical_states"):
        habitat_capacity_pair(layered_vertical_states=0)
