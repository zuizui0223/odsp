from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from odsp.circular_state_benchmark import run_circular_state_benchmark


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "CIRCULAR_STATE_PREDICTION_VALIDATION_RECEIPT.json"


def test_circular_state_validation_receipt_reproduces_frozen_benchmark():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    frozen = receipt["known_truth_benchmark"]
    result = run_circular_state_benchmark(
        seed=frozen["seed"],
        replicates=frozen["replicate_count"],
        training_rows=frozen["training_rows"],
        heldout_rows=frozen["heldout_rows"],
        period=frozen["period"],
    ).as_dict()

    assert result["passed"] is True
    assert result["stable_all_positive"] is True
    assert result["shifted_all_negative"] is True
    assert result["null_mean_gain_near_zero"] is True

    by_family = {row["family"]: row for row in result["families"]}
    for family in (
        "stable_generalizing",
        "unorganized",
        "shifted_non_generalizing",
    ):
        expected = frozen[family]
        observed = by_family[family]
        for key in (
            "mean_log_density_gain",
            "minimum_log_density_gain",
            "maximum_log_density_gain",
            "positive_gain_fraction",
            "negative_gain_fraction",
            "mean_circular_mae_improvement",
        ):
            np.testing.assert_allclose(
                observed[key], expected[key], rtol=0.0, atol=1e-10
            )

    np.testing.assert_allclose(
        result["phase_origin_gain_invariance_error"],
        frozen["phase_origin_gain_invariance_error"],
        rtol=0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["period_unit_gain_invariance_error"],
        frozen["period_unit_gain_invariance_error"],
        rtol=0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["interval_empirical_coverage"],
        frozen["interval_empirical_coverage"],
        rtol=0.0,
        atol=1e-12,
    )


def test_circular_state_receipt_preserves_semantic_boundaries():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["scientific_boundary"]
    assert boundary["observation_clock_time_equals_true_activity_time"] is False
    assert boundary["local_clock_time_equals_solar_time"] is False
    assert boundary["von_mises_reference_is_universal_activity_distribution"] is False
    assert boundary["positive_density_gain_implies_temporal_displacement_or_competition"] is False
    assert boundary["detection_bias_removed"] is False
    assert boundary["joint_height_time_density_implemented"] is False
    assert boundary["n2_output_automatically_promoted_to_n3"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_terminal_categories_changed"] is False
