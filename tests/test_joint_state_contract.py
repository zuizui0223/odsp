from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_joint_height_time_contract_keeps_context_and_coupling_distinct():
    contract = json.loads(
        (ROOT / "JOINT_HEIGHT_TIME_PREDICTION_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["primary_target"] == "p(z,t|X) = p(t|X) p(z|X,t)"
    assert "log p_train(z,t|X)" in contract["primary_contextual_joint_score"]
    assert "log p_train(z|X,t)" in contract["directional_coupling_score"]
    assert contract["independence"]["joint_gain_classified_separately_from_coupling_gain"] is True
    assert contract["independence"]["pooled_mean_may_rescue_conflicting_group"] is False

    benchmark = contract["known_truth_benchmark"]
    assert benchmark["seed"] == 20260905
    assert benchmark["replicates"] == 128
    assert benchmark["training_rows"] == 800
    assert benchmark["heldout_rows"] == 1600
    assert len(benchmark["families"]) == 5

    boundary = contract["semantic_boundary"]
    assert boundary["joint_prediction_proves_joint_niche_causality"] is False
    assert boundary["directional_coupling_gain_is_symmetric_dependence_measure"] is False
    assert boundary["directional_coupling_gain_implies_behavioral_mechanism"] is False
    assert boundary["absolute_altitude_equals_height_above_ground"] is False
    assert boundary["clock_time_equals_true_activity_time"] is False
    assert boundary["joint_density_removes_observation_or_detection_bias"] is False

    frozen = contract["frozen_v4_preservation"]
    assert all(value is False for value in frozen.values())
