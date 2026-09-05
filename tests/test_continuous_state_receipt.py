from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from odsp.continuous_state_benchmark import run_continuous_state_benchmark


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "CONTINUOUS_STATE_PREDICTION_VALIDATION_RECEIPT.json"


def test_continuous_state_validation_receipt_reproduces_frozen_benchmark():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    frozen = receipt["known_truth_benchmark"]
    result = run_continuous_state_benchmark(
        seed=frozen["seed"],
        replicates=frozen["replicate_count"],
        training_rows=frozen["training_rows"],
        heldout_rows=frozen["heldout_rows"],
    ).as_dict()

    assert result["passed"] is True
    assert result["stable_all_positive"] is True
    assert result["shifted_all_negative"] is True
    assert result["null_mean_gain_near_zero"] is True
    assert result["seed"] == frozen["seed"]
    assert result["replicate_count"] == frozen["replicate_count"]
    assert result["training_rows"] == frozen["training_rows"]
    assert result["heldout_rows"] == frozen["heldout_rows"]

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
            "mean_crps_improvement",
            "mean_rmse_improvement",
        ):
            np.testing.assert_allclose(
                observed[key], expected[key], rtol=0.0, atol=1e-10
            )

    np.testing.assert_allclose(
        result["affine_gain_invariance_error"],
        frozen["response_affine_gain_invariance_error"],
        rtol=0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["interval_empirical_coverage"],
        frozen["interval_empirical_coverage"],
        rtol=0.0,
        atol=1e-12,
    )


def test_continuous_state_receipt_preserves_claim_boundaries():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["scientific_boundary"]
    assert boundary["continuous_state_automatically_defines_biological_niche_axis"] is False
    assert boundary["gaussian_reference_is_universal_biological_distribution"] is False
    assert boundary["positive_density_gain_implies_causality"] is False
    assert boundary["absolute_altitude_equals_height_above_ground"] is False
    assert boundary["observation_bias_removed"] is False
    assert boundary["circular_time_density_implemented"] is False
    assert boundary["multivariate_continuous_state_density_implemented"] is False
    assert boundary["n2_output_automatically_promoted_to_n3"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_terminal_categories_changed"] is False
