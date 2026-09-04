from __future__ import annotations

import math

from odsp.generality_benchmark import run_n2_generality_benchmark


def test_default_generality_benchmark_passes_all_proof_obligations():
    result = run_n2_generality_benchmark()

    assert result.seed == 20260904
    assert result.randomized_case_count == 128
    assert result.check_count >= 1800
    assert result.passed_count == result.check_count
    assert result.failed_count == 0
    assert result.passed is True
    assert math.isfinite(result.maximum_absolute_error)
    assert result.maximum_absolute_error <= 2e-9


def test_generality_benchmark_covers_required_property_families():
    result = run_n2_generality_benchmark(randomized_cases=8)
    properties = set(result.properties)

    assert {
        "same_distribution_identity",
        "information_bounds",
        "positive_mass_scaling",
        "axis_permutation_equivariance",
        "state_label_permutation",
        "omitted_nuisance_refinement",
        "conditional_independence_composition",
        "independent_group_mass_invariance",
        "independent_group_count",
    } <= properties


def test_generality_benchmark_is_deterministic_for_fixed_seed():
    first = run_n2_generality_benchmark(seed=917, randomized_cases=6).as_dict()
    second = run_n2_generality_benchmark(seed=917, randomized_cases=6).as_dict()
    assert first == second


def test_generality_benchmark_changes_cases_when_seed_changes():
    first = run_n2_generality_benchmark(seed=917, randomized_cases=3)
    second = run_n2_generality_benchmark(seed=918, randomized_cases=3)

    assert first.passed is True
    assert second.passed is True
    assert first.checks != second.checks
