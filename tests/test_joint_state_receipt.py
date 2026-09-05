from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from odsp.joint_state_benchmark import run_joint_state_benchmark


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "JOINT_HEIGHT_TIME_PREDICTION_VALIDATION_RECEIPT.json"


def test_joint_state_validation_receipt_reproduces_frozen_benchmark():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    frozen = receipt["known_truth_benchmark"]
    result = run_joint_state_benchmark(
        seed=frozen["seed"],
        replicates=frozen["replicate_count"],
        training_rows=frozen["training_rows"],
        heldout_rows=frozen["heldout_rows"],
        period=frozen["period"],
    ).as_dict()

    assert result["passed"] is True
    assert result["stable_joint_all_positive"] is True
    assert result["stable_coupling_all_positive"] is True
    assert result["context_null_joint_mean_near_zero"] is True
    assert result["uncoupled_coupling_mean_near_zero"] is True
    assert result["context_shift_joint_all_negative"] is True
    assert result["coupling_shift_coupling_all_negative"] is True

    by_family = {row["family"]: row for row in result["families"]}
    for family in (
        "stable_context_and_coupling",
        "context_unorganized_but_coupled",
        "contextual_but_uncoupled",
        "context_shifted",
        "coupling_shifted",
    ):
        expected = frozen[family]
        observed = by_family[family]
        for key in (
            "mean_joint_gain",
            "minimum_joint_gain",
            "maximum_joint_gain",
            "positive_joint_gain_fraction",
            "negative_joint_gain_fraction",
            "mean_coupling_gain",
            "minimum_coupling_gain",
            "maximum_coupling_gain",
            "positive_coupling_gain_fraction",
            "negative_coupling_gain_fraction",
        ):
            np.testing.assert_allclose(
                observed[key], expected[key], rtol=0.0, atol=1e-10
            )

    for observed_key, expected_key in (
        ("phase_origin_joint_gain_error", "phase_origin_joint_gain_error"),
        ("phase_origin_coupling_gain_error", "phase_origin_coupling_gain_error"),
        ("period_unit_joint_gain_error", "period_unit_joint_gain_error"),
        ("period_unit_coupling_gain_error", "period_unit_coupling_gain_error"),
        ("height_unit_joint_gain_error", "height_unit_joint_gain_error"),
        ("height_unit_coupling_gain_error", "height_unit_coupling_gain_error"),
    ):
        np.testing.assert_allclose(
            result[observed_key], frozen[expected_key], rtol=0.0, atol=1e-12
        )


def test_joint_state_receipt_preserves_claim_boundaries():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["scientific_boundary"]
    assert boundary["joint_prediction_proves_joint_niche_causality"] is False
    assert boundary["directional_coupling_gain_is_symmetric_dependence_measure"] is False
    assert boundary["directional_coupling_gain_implies_behavioral_mechanism"] is False
    assert boundary["absolute_altitude_equals_height_above_ground"] is False
    assert boundary["clock_time_equals_true_activity_time"] is False
    assert boundary["joint_density_removes_observation_or_detection_bias"] is False
    assert boundary["n2_output_automatically_promoted_to_n3"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_terminal_categories_changed"] is False
