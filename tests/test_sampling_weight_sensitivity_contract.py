from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_sampling_weight_contract_forbids_auto_bias_correction():
    contract=json.loads((ROOT/"SAMPLING_WEIGHT_SENSITIVITY_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-sampling-weight-sensitivity-v1"
    rule=contract["decision_rule"]
    assert rule["weight_robust_generalizing_requires_every_scenario_robust_generalizing"] is True
    assert rule["one_weight_scenario_can_override_another"] is False
    assert rule["automatic_bias_correction_performed"] is False
    assert rule["aggregate_confidence_score_emitted"] is False
    ceiling=contract["claim_boundary"]
    assert ceiling["weight_sensitivity_identifies_true_sampling_process"] is False
    assert ceiling["stable_result_proves_no_observation_bias"] is False
    assert ceiling["weighting_replaces_detection_model"] is False
