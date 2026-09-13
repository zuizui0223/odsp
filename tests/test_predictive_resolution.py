from __future__ import annotations

import math

import pytest

from odsp.predictive_resolution import decompose_predictive_resolution
from odsp.predictive_resolution_benchmark import run_predictive_resolution_benchmark


def test_score_ladder_telescopes_with_arbitrary_upstream_scores():
    result = decompose_predictive_resolution(
        (
            ("pooled", [-1.0, -2.0, -1.5, -2.5]),
            ("species", [-0.8, -1.7, -1.2, -2.0]),
            ("full", [-0.6, -1.5, -1.0, -1.8]),
        ),
        ["a", "a", "b", "b"],
        sample_weight=[1.0, 1.0, 2.0, 1.0],
    )

    assert result.levels == ("pooled", "species", "full")
    assert result.total_gain_category == "generalizing"
    assert result.increment_categories == (
        ("pooled", "species", "generalizing"),
        ("species", "full", "generalizing"),
    )
    assert len(result.groups) == 2
    for group in result.groups:
        assert group.additivity_error == pytest.approx(0.0, abs=1e-15)
        assert group.total_gain == pytest.approx(
            sum(step.mean_gain for step in group.increments), abs=1e-15
        )


def test_nonlog_proper_score_orientation_is_supported():
    # Negative Brier score: larger is better.  The decomposition only requires
    # commensurate row-wise scores, not a particular learner or state geometry.
    result = decompose_predictive_resolution(
        (
            ("pooled", [-0.25, -0.25, -0.25, -0.25]),
            ("species", [-0.16, -0.16, -0.20, -0.20]),
            ("full", [-0.09, -0.12, -0.16, -0.18]),
        ),
        ["g1", "g1", "g2", "g2"],
    )
    assert result.total_gain_category == "generalizing"
    assert all(abs(row.additivity_error) < 1e-15 for row in result.groups)


def test_intermediate_support_failure_is_fail_closed_but_final_failure_is_scored():
    with pytest.raises(ValueError, match="comparator level 'species' must be finite"):
        decompose_predictive_resolution(
            (
                ("pooled", [-1.0, -1.0]),
                ("species", [-1.0, -math.inf]),
                ("full", [-0.8, -0.8]),
            ),
            ["a", "a"],
        )

    result = decompose_predictive_resolution(
        (
            ("pooled", [-1.0, -1.0]),
            ("species", [-0.9, -0.9]),
            ("full", [-0.8, -math.inf]),
        ),
        ["a", "a"],
    )
    assert result.groups[0].total_gain == -math.inf
    assert result.groups[0].increments[-1].mean_gain == -math.inf
    assert result.groups[0].additivity_error == 0.0
    assert result.total_gain_category == "non_generalizing"


def test_zero_weight_rows_do_not_create_false_support_failures():
    result = decompose_predictive_resolution(
        (
            ("pooled", [-1.0, -1.0]),
            ("species", [-0.8, -math.inf]),
            ("full", [-0.7, -math.inf]),
        ),
        ["a", "a"],
        sample_weight=[1.0, 0.0],
    )
    assert result.groups[0].positive_weight_row_count == 1
    assert result.groups[0].total_gain == pytest.approx(0.3)


def test_known_truth_oracle_and_misspecification_identities():
    benchmark = run_predictive_resolution_benchmark()

    assert benchmark.oracle_species_information == pytest.approx(
        0.14321854481691187, abs=1e-12
    )
    assert benchmark.oracle_context_information == pytest.approx(
        0.014032432883159807, abs=1e-12
    )
    assert benchmark.misspecified_full_kl_penalty == pytest.approx(
        0.07190509252064392, abs=1e-12
    )
    assert benchmark.misspecified_species_increment == pytest.approx(
        benchmark.oracle_species_information, abs=1e-12
    )
    assert benchmark.misspecified_context_increment == pytest.approx(
        -0.057872659637484114, abs=1e-12
    )
    assert benchmark.misspecified_total_gain == pytest.approx(
        0.08534588517942776, abs=1e-12
    )
    assert benchmark.oracle_additivity_error < 1e-14
    assert benchmark.misspecified_additivity_error < 1e-14
    assert benchmark.oracle_information_identity_error < 1e-14
    assert benchmark.misspecification_identity_error < 1e-14
    assert benchmark.total_positive_context_negative_recovered is True
