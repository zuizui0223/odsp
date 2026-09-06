from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_joint_robustness_radius_contract_is_fail_closed():
    contract=json.loads((ROOT/"JOINT_ROBUSTNESS_RADIUS_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-joint-robustness-radius-v1"
    definition=contract["definition"]
    assert definition["certified_gamma_is_last_passing_lower_bound"] is True
    assert definition["break_gamma_is_first_failing_upper_bound"] is True
    rule=contract["decision_rule"]
    assert rule["baseline_unavailable_gives_radius_status"]=="unavailable"
    assert rule["baseline_not_joint_robust_gives_radius_status"]=="not_certified_at_baseline"
    assert rule["gamma_is_inferred_from_data"] is False
    assert rule["automatic_bias_correction_performed"] is False
    assert rule["aggregate_confidence_score_emitted"] is False
    boundary=contract["claim_boundary"]
    assert boundary["radius_is_probability_of_correctness"] is False
    assert boundary["radius_proves_no_observation_bias"] is False
    assert boundary["radius_repairs_bad_block_definition"] is False
