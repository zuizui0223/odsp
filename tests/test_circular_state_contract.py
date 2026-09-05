from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_circular_state_contract_freezes_periodic_prediction_boundaries():
    contract = json.loads(
        (ROOT / "CIRCULAR_STATE_PREDICTION_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["primary_target"] == "p(t|X) for one circular state t with an explicitly declared period"
    assert contract["default_example"]["period"] == 24.0
    assert contract["known_truth_benchmark"]["replicates"] == 128
    assert contract["known_truth_benchmark"]["seed"] == 20260905
    assert contract["independence"]["all_positive_required_for_generalizing"] is True
    assert contract["independence"]["pooled_mean_may_rescue_conflicting_group"] is False

    boundary = contract["semantic_boundary"]
    assert boundary["observation_clock_time_equals_true_activity_time"] is False
    assert boundary["local_clock_time_equals_solar_time"] is False
    assert boundary["von_mises_reference_is_universal_activity_distribution"] is False
    assert boundary["positive_density_gain_implies_temporal_displacement_or_competition"] is False
    assert boundary["circular_density_removes_detection_bias"] is False

    frozen = contract["frozen_v4_preservation"]
    assert all(value is False for value in frozen.values())
