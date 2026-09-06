from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_bias_robust_selection_contract_keeps_gates_separate():
    contract=json.loads((ROOT/"BIAS_ROBUST_MODEL_SELECTION_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-bias-robust-model-selection-v4"
    rule=contract["decision_rule"]
    assert rule["all_group_coverage_within_tolerance_required"] is True
    assert rule["joint_bias_uncertainty_robustness_required"] is True
    assert rule["point_trust_can_override_joint_failure"] is False
    assert rule["aggregate_confidence_score_emitted"] is False
    boundary=contract["claim_boundary"]
    assert boundary["selection_identifies_true_biological_mechanism"] is False
    assert boundary["joint_robustness_proves_no_observation_bias"] is False
    assert boundary["gamma_is_inferred_from_data"] is False
